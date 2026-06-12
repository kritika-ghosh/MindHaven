import cv2
import math
import mediapipe as mp
import numpy as np
import time
from deepface import DeepFace
import speech_recognition as sr
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from collections import defaultdict
import joblib
import re
import os
import io

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
import tempfile

# --- Global Configuration (from original code) ---
RUN_DURATION = 20  # Max duration for video analysis
EMOTION_BUCKETS = {
    'positive': ['happy'],
    'neutral': ['neutral'],
    'negative': ['angry', 'sad', 'fear', 'disgust', 'surprise']
}
sentiment_analyzer = SentimentIntensityAnalyzer()
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    max_num_faces=1, refine_landmarks=True, min_detection_confidence=0.7, min_tracking_confidence=0.7
)
LEFT_EYE = [362, 385, 387, 263, 373, 380]
RIGHT_EYE = [33, 160, 158, 133, 153, 144]
INNER_MOUTH = [78, 191, 80, 81, 82, 13, 312, 311, 310, 415, 95, 88, 178, 87, 14, 317, 402, 318, 324]
answer_mapping = {
    "Never": 0, "Rarely": 1, "Sometimes": 2, "Often": 3, "Always": 4,
    "I enjoy my work. I have no symptoms of burnout": 0,
    "Occasionally I am under stress, and I don’t always have as much energy as I once did, but I don’t feel burned out": 1,
    "I am definitely burning out and have one or more symptoms of burnout, such as physical and emotional exhaustion": 2,
    "The symptoms of burnout that I’m experiencing won’t go away. I think about frustration at work a lot": 3,
    "I feel completely burned out and often wonder if I can go on. I am at the point where I may need some changes or may need to seek some sort of help": 4,
}

# --- Model Loading ---
# Load scaler and model (assuming they are in the same directory)
try:
    scaler = joblib.load('scaler.joblib')
    model = joblib.load('model.joblib')
except FileNotFoundError:
    print("WARNING: Model files (scaler.joblib, model.joblib) not found. Prediction will fail.")
    scaler = None
    model = None
except Exception as e:
    print(f"Error loading model files: {e}")
    scaler = None
    model = None

# --- Core Functions (Refactored for FastAPI) ---

def calculate_ear(eye_points, landmarks):
    """Calculate Eye Aspect Ratio"""
    try:
        v1 = math.dist(landmarks[eye_points[1]], landmarks[eye_points[5]])
        v2 = math.dist(landmarks[eye_points[2]], landmarks[eye_points[4]])
        h = math.dist(landmarks[eye_points[0]], landmarks[eye_points[3]])
        return (v1 + v2) / (2.0 * h) if h > 0 else 0.0
    except:
        return 0.0

def calculate_mar(landmarks):
    """Calculate Mouth Aspect Ratio using inner mouth points"""
    try:
        points = [landmarks[i] for i in INNER_MOUTH]
        if len(points) < 2: return 0.0
        y_coords = [p[1] for p in points]
        mouth_height = max(y_coords) - min(y_coords)
        
        if len(landmarks) > 60:
            mouth_width = math.dist(landmarks[61], landmarks[291])  # Left to right mouth corner
        else:
            mouth_width = math.dist(points[0], points[6]) if len(points) > 6 else 1.0
        
        return mouth_height / mouth_width if mouth_width > 0 else 0.0
    except:
        return 0.0

def _get_emotion_bucket(emotion):
    for bucket, emotions_list in EMOTION_BUCKETS.items():
        if emotion in emotions_list:
            return bucket
    return "unknown"

def analyze_video_file(video_path: str):
    """Processes a video file to get face and emotion metrics."""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise HTTPException(status_code=400, detail="Could not open video file.")

    ear_values = []
    mar_values = []
    emotion_bucket_counts = defaultdict(int)
    
    start_time = time.time()
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret or (time.time() - start_time) > RUN_DURATION:
            break

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(rgb_frame)

        if results.multi_face_landmarks:
            try:
                face_landmarks = results.multi_face_landmarks[0]
                h, w, _ = frame.shape
                landmarks = [(int(p.x * w), int(p.y * h)) for p in face_landmarks.landmark]

                left_ear = calculate_ear(LEFT_EYE, landmarks)
                right_ear = calculate_ear(RIGHT_EYE, landmarks)
                ear = (left_ear + right_ear) / 2.0
                mar = calculate_mar(landmarks)

                ear_values.append(ear)
                mar_values.append(mar)
            except Exception as e:
                # print(f"Landmark error: {e}")
                pass # Skip frame if landmark processing fails
        
        # Emotion analysis (every few frames to speed up)
        if int(cap.get(cv2.CAP_PROP_POS_FRAMES)) % 10 == 0:
            try:
                results_emotion = DeepFace.analyze(
                    frame, actions=['emotion'],
                    detector_backend='mtcnn', enforce_detection=False, silent=True
                )
                if results_emotion:
                    dominant_emotion = results_emotion[0].get('dominant_emotion', 'neutral')
                    bucket = _get_emotion_bucket(dominant_emotion)
                    emotion_bucket_counts[bucket] += 1
            except Exception:
                pass

    cap.release()

    if not ear_values or not mar_values:
        return (0, 0, 0, 0), (0, 0, 0) # Default/failure return

    avg_ear = np.mean(ear_values)
    std_ear = np.std(ear_values)
    avg_mar = np.mean(mar_values)
    std_mar = np.std(mar_values)

    total_emotions = sum(emotion_bucket_counts.values())
    pos_perc = (emotion_bucket_counts['positive'] / total_emotions) * 100 if total_emotions > 0 else 0.0
    neu_perc = (emotion_bucket_counts['neutral'] / total_emotions) * 100 if total_emotions > 0 else 0.0
    neg_perc = (emotion_bucket_counts['negative'] / total_emotions) * 100 if total_emotions > 0 else 0.0

    face_stats = (avg_ear, std_ear, avg_mar, std_mar)
    emotion_stats = (pos_perc, neu_perc, neg_perc)

    return face_stats, emotion_stats


def analyze_audio_file(audio_path: str):
    """Processes an audio file for speech recognition and sentiment analysis."""
    r = sr.Recognizer()
    try:
        with sr.AudioFile(audio_path) as source:
            audio_sr = r.record(source)
        try:
            text = r.recognize_google(audio_sr)
        except (sr.UnknownValueError, sr.RequestError):
            text = ""
        
        sentiment = sentiment_analyzer.polarity_scores(text) if text else {"pos": 0, "neu": 1, "neg": 0, "compound": 0}
        sentiment_str = (
            f"Pos: {sentiment['pos']:.2f}, Neu: {sentiment['neu']:.2f}, "
            f"Neg: {sentiment['neg']:.2f}, Comp: {sentiment['compound']:.2f}"
        )
        return text, sentiment_str, "N/A" # text, sentiment_str, pitch_display
    except Exception:
        return "", "Pos: 0.00, Neu: 1.00, Neg: 0.00, Comp: 0.00", "N/A"

def preprocess_input(raw_dict, scaler):
    """Preprocesses the aggregated results for model input."""
    q_encoded = [answer_mapping.get(ans, -1) for ans in raw_dict["Questionnaire Answers"]]
    if -1 in q_encoded: raise ValueError("Unknown answer detected in questionnaire answers.")

    # Parse EAR and MAR (only average, ignore std)
    EAR_avg = float(raw_dict["EAR"].split(" ± ")[0])
    MAR_avg = float(raw_dict["MAR"].split(" ± ")[0])

    # Parse emotions percentages
    emotions = raw_dict["Emotions"]
    pos_emotion = float(emotions["Positive %"].rstrip('%'))
    neu_emotion = float(emotions["Neutral %"].rstrip('%'))
    neg_emotion = float(emotions["Negative %"].rstrip('%'))

    # Parse sentiment scores
    sentiment_str = raw_dict["Sentiment"]
    sentiment_vals = re.findall(r'[-+]?\d*\.\d+|\d+', sentiment_str)
    sentiment_vals = list(map(float, sentiment_vals))
    if len(sentiment_vals) != 4: raise ValueError("Sentiment string format unexpected.")
    sent_pos, sent_neu, sent_neg, sent_comp = sentiment_vals

    # Build input feature vector (Must match the training data order!)
    # Q1-Q5, Avg_EAR, Std_EAR, Avg_MAR, Std_MAR, Pos_Emo, Neu_Emo, Neg_Emo, Sent_Pos, Sent_Neu, Sent_Neg, Sent_Comp
    # NOTE: We use placeholders (0) for Std_EAR and Std_MAR as the original Gradio app didn't use them in the final feature list but they appear in the original preprocessing
    features = q_encoded + [
        EAR_avg, 0,  
        MAR_avg, 0,  
        pos_emotion, neu_emotion, neg_emotion,
        sent_pos, sent_neu, sent_neg, sent_comp
    ]

    X = np.array(features).reshape(1, -1)
    X_scaled = scaler.transform(X)
    return X_scaled

def predict_burnout(raw_dict):
    """Runs the prediction model."""
    if not scaler or not model:
        raise RuntimeError("Model files not loaded. Cannot predict.")

    X_processed = preprocess_input(raw_dict, scaler)
    pred = model.predict(X_processed)
    output_score = float(pred[0])
    return output_score

def get_suggestion_text(burnout_score: float) -> str:
    """Generates the suggestion text based on the predicted score."""
    if burnout_score == 0.0:
        return (
            "Your burnout score is **Low** (0-20). You're feeling good and active. "
            "Maintain healthy work-life habits, practice gratitude journaling, and promote regular physical activity."
        )
    elif burnout_score == 1.0:
        return (
            "Your burnout score is **Mild** (20-40). You're under a little stress. "
            "Use the Pomodoro Technique, try Box Breathing (4s in, 4s hold, 4s out, 4s hold), and schedule 'disconnect' periods."
        )
    elif burnout_score == 2.0:
        return (
            "Your burnout score is **Moderate** (40-60). You're starting to feel physical and emotional exhaustion. "
            "Implement a Digital Detox, prioritize 20-30 minutes of aerobic exercise 3 times a week, and focus on good sleep hygiene (7-9 hours)."
        )
    elif burnout_score == 3.0:
        return (
            "Your burnout score is **High** (60-80). Your burnout symptoms are persistent. "
            "Take mandatory time off, consider a Mindfulness-Based Stress Reduction (MBSR) course, and seek professional help (EAP or therapist)."
        )
    else:
        return (
            "Your burnout score is **Severe** (80-100). You feel completely burned out. **Immediate professional help is needed.** "
            "Access Crisis Resources (e.g., call 988), consult a doctor immediately, and prioritize your health over work. Work can wait."
        )


# --- FastAPI Implementation ---
app = FastAPI(title="Burnout Prediction API")

class PredictionResponse(BaseModel):
    burnout_score: float
    suggestion: str
    debug_data: dict

@app.post("/predict", response_model=PredictionResponse)
async def get_prediction(
    video_file: UploadFile = File(..., description="Video file for facial and emotion analysis (max 20s will be analyzed)."),
    audio_file: UploadFile = File(..., description="Audio file for voice and sentiment analysis."),
    answer_1: str = Form(..., description="Answer to Question 1"),
    answer_2: str = Form(..., description="Answer to Question 2"),
    answer_3: str = Form(..., description="Answer to Question 3"),
    answer_4: str = Form(..., description="Answer to Question 4"),
    answer_5: str = Form(..., description="Answer to Question 5"),
):
    """
    Analyzes questionnaire answers, video, and audio to predict a burnout score and provide suggestions.

    Expects five string answers (Form data), a video file, and an audio file (UploadFile).
    """
    
    # 1. Process Files and Questionnaire
    q_answers = [answer_1, answer_2, answer_3, answer_4, answer_5]
    
    # Save video file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_video:
        video_content = await video_file.read()
        tmp_video.write(video_content)
        video_path = tmp_video.name
    
    # Save audio file temporarily
    # NOTE: Gradio's audio output is often WAV, so we use that suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_audio:
        audio_content = await audio_file.read()
        tmp_audio.write(audio_content)
        audio_path = tmp_audio.name

    try:
        # Video/Face/Emotion Analysis
        face_stats, emotion_stats = analyze_video_file(video_path)
        
        # Audio/Voice/Sentiment Analysis
        text, sentiment_str, pitch_display = analyze_audio_file(audio_path)

        # 2. Aggregate Results (simulating the Gradio `aggregate_results` output)
        avg_ear, std_ear, avg_mar, std_mar = face_stats
        pos_perc, neu_perc, neg_perc = emotion_stats
        
        raw_dict = {
            "Questionnaire Answers": q_answers,
            "EAR": f"{avg_ear:.2f} ± {std_ear:.2f}",
            "MAR": f"{avg_mar:.2f} ± {std_mar:.2f}",
            "Emotions": {
                "Positive %": f"{pos_perc:.1f}%",
                "Neutral %": f"{neu_perc:.1f}%",
                "Negative %": f"{neg_perc:.1f}%"
            },
            "Voice Transcript": text,
            "Sentiment": sentiment_str,
            "Pitch": pitch_display,
            "Subtypes": [] # Subtype tracking is complex/optional, set to empty for API
        }

        # 3. Prediction
        burnout_score = predict_burnout(raw_dict)
        suggestion_text = get_suggestion_text(burnout_score)

        # 4. Return Response
        return PredictionResponse(
            burnout_score=burnout_score,
            suggestion=suggestion_text,
            debug_data=raw_dict
        )

    except Exception as e:
        # Clean up temporary files on error
        os.unlink(video_path)
        os.unlink(audio_path)
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")
    
    finally:
        # Clean up temporary files
        if os.path.exists(video_path):
            os.unlink(video_path)
        if os.path.exists(audio_path):
            os.unlink(audio_path)

# Example of how to run the FastAPI app (requires 'uvicorn'):
# Save the code above as main.py and run:
# uvicorn main:app --reload

# For testing, you would typically use a tool like cURL or a Python 'requests' script 
# to send a multipart/form-data request containing the files and the form data.