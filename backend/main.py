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
import tempfile

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# --- Global Configuration ---
RUN_DURATION = 20  # Max duration for video analysis
EMOTION_BUCKETS = {
    'positive': ['happy'],
    'neutral': ['neutral'],
    'negative': ['angry', 'sad', 'fear', 'disgust', 'surprise']
}
sentiment_analyzer = SentimentIntensityAnalyzer()

# Lazy loading face_mesh to prevent Docker initialization crashes
face_mesh = mp.solutions.face_mesh.FaceMesh(
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
try:
    scaler = joblib.load('scaler.joblib')
    model = joblib.load('model.joblib')
except FileNotFoundError:
    print("WARNING: Model files (scaler.joblib, model.joblib) not found in current directory. Prediction will fail.")
    scaler = None
    model = None
except Exception as e:
    print(f"Error loading model files: {e}")
    scaler = None
    model = None

# --- Core Functions ---

def calculate_ear(eye_points, landmarks):
    try:
        v1 = math.dist(landmarks[eye_points[1]], landmarks[eye_points[5]])
        v2 = math.dist(landmarks[eye_points[2]], landmarks[eye_points[4]])
        h = math.dist(landmarks[eye_points[0]], landmarks[eye_points[3]])
        return (v1 + v2) / (2.0 * h) if h > 0 else 0.0
    except:
        return 0.0

def calculate_mar(landmarks):
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
                pass
        
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
        return (0.30, 0.02, 0.15, 0.01), (0, 100, 0) # Fallback to standard biological defaults on frame drops

    avg_ear = np.mean(ear_values)
    std_ear = np.std(ear_values)
    avg_mar = np.mean(mar_values)
    std_mar = np.std(mar_values)

    total_emotions = sum(emotion_bucket_counts.values())
    pos_perc = (emotion_bucket_counts['positive'] / total_emotions) * 100 if total_emotions > 0 else 0.0
    neu_perc = (emotion_bucket_counts['neutral'] / total_emotions) * 100 if total_emotions > 0 else 100.0
    neg_perc = (emotion_bucket_counts['negative'] / total_emotions) * 100 if total_emotions > 0 else 0.0

    return (avg_ear, std_ear, avg_mar, std_mar), (pos_perc, neu_perc, neg_perc)


def analyze_audio_file(audio_path: str):
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
        return text, sentiment_str, "N/A"
    except Exception:
        return "", "Pos: 0.00, Neu: 1.00, Neg: 0.00, Comp: 0.00", "N/A"

def preprocess_input(raw_dict, scaler):
    q_encoded = [answer_mapping.get(ans, -1) for ans in raw_dict["Questionnaire Answers"]]
    if -1 in q_encoded: raise ValueError("Unknown answer detected in questionnaire answers.")

    # Align new questionnaire answers with the pre-trained CatBoost model:
    # Model features were trained expecting:
    #   - Q1: clarity (higher = healthy / lower burnout) -> new Q1 is exhaustion (higher = worse), so we invert Q1.
    #   - Q2 & Q3: disconnect & fatigue (higher = worse) -> same direction, no inversion.
    #   - Q4 & Q5: lack of motivation & irritation (higher = worse) -> new Q4 & Q5 are pride & outcomes (higher = healthy), so we invert Q4 and Q5.
    q_encoded[0] = 4 - q_encoded[0]
    q_encoded[3] = 4 - q_encoded[3]
    q_encoded[4] = 4 - q_encoded[4]

    # Safely unpack average and standard deviations
    EAR_avg, EAR_std = map(float, raw_dict["EAR"].split(" ± "))
    MAR_avg, MAR_std = map(float, raw_dict["MAR"].split(" ± "))

    emotions = raw_dict["Emotions"]
    pos_emotion = float(emotions["Positive %"].rstrip('%'))
    neu_emotion = float(emotions["Neutral %"].rstrip('%'))
    neg_emotion = float(emotions["Negative %"].rstrip('%'))

    sentiment_str = raw_dict["Sentiment"]
    sentiment_vals = re.findall(r'[-+]?\d*\.\d+|\d+', sentiment_str)
    sentiment_vals = list(map(float, sentiment_vals))
    if len(sentiment_vals) != 4: raise ValueError("Sentiment string format unexpected.")
    sent_pos, sent_neu, sent_neg, sent_comp = sentiment_vals

    # Compute engineered features Survey_Sum and Exhaustion_Ratio
    survey_sum = (4 - q_encoded[0]) + q_encoded[1] + q_encoded[2] + q_encoded[3] + q_encoded[4]
    exhaustion_ratio = MAR_avg / (EAR_avg + 1e-5)

    # Construct the array with full high-accuracy statistical parameters (18 features total)
    features = q_encoded + [
        EAR_avg, EAR_std,  
        MAR_avg, MAR_std,  
        pos_emotion, neu_emotion, neg_emotion,
        sent_pos, sent_neu, sent_neg, sent_comp,
        survey_sum, exhaustion_ratio
    ]

    X = np.array(features).reshape(1, -1)
    X_scaled = scaler.transform(X)
    return X_scaled

def predict_burnout(raw_dict):
    if not scaler or not model:
        raise RuntimeError("Model files not loaded. Cannot predict.")
    X_processed = preprocess_input(raw_dict, scaler)
    pred = model.predict(X_processed)
    # CatBoostRegressor returns prediction as an array/float value
    score = float(pred[0]) if isinstance(pred, np.ndarray) else float(pred)
    # Clip the score to the valid range [0.0, 4.0]
    return max(0.0, min(4.0, score))

def get_suggestion_text(burnout_score: float) -> str:
    rounded_score = round(burnout_score)
    if rounded_score <= 0:
        return "Your burnout score is Low (0-20). You're feeling good and active. Maintain healthy work-life habits, practice gratitude journaling, and promote regular physical activity."
    elif rounded_score == 1:
        return "Your burnout score is Mild (20-40). You're under a little stress. Use the Pomodoro Technique, try Box Breathing, and schedule 'disconnect' periods."
    elif rounded_score == 2:
        return "Your burnout score is Moderate (40-60). You're starting to feel physical and emotional exhaustion. Implement a Digital Detox and focus on good sleep hygiene."
    elif rounded_score == 3:
        return "Your burnout score is High (60-80). Your burnout symptoms are persistent. Take mandatory time off and consider seeking professional advice."
    else:
        return "Your burnout score is Severe (80-100). You feel completely burned out. Immediate professional help is needed. Prioritize your health over work. Work can wait."


# --- FastAPI Implementation ---
app = FastAPI(title="Burnout Regression API")

# Enable Cross-Origin requests so your Vercel site can call it
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PredictionResponse(BaseModel):
    burnout_score: float
    suggestion: str
    debug_data: dict

@app.get("/health")
async def health_check():
    """
    Lightweight endpoint for uptime monitoring to keep the container awake.
    """
    return {"status": "healthy", "timestamp": time.time()}

@app.post("/predict", response_model=PredictionResponse)
async def get_prediction(
    video_file: UploadFile = File(..., description="Video file for facial and emotion analysis."),
    audio_file: UploadFile = File(..., description="Audio file for voice and sentiment analysis."),
    answer_1: str = Form(..., description="Answer to Question 1"),
    answer_2: str = Form(..., description="Answer to Question 2"),
    answer_3: str = Form(..., description="Answer to Question 3"),
    answer_4: str = Form(..., description="Answer to Question 4"),
    answer_5: str = Form(..., description="Answer to Question 5"),
):
    q_answers = [answer_1, answer_2, answer_3, answer_4, answer_5]
    
    # Write video data out securely to container disk mounts
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_video:
        video_content = await video_file.read()
        tmp_video.write(video_content)
        video_path = tmp_video.name
    
    # Write audio data out securely to container disk mounts
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_audio:
        audio_content = await audio_file.read()
        tmp_audio.write(audio_content)
        audio_path = tmp_audio.name

    try:
        face_stats, emotion_stats = analyze_video_file(video_path)
        text, sentiment_str, pitch_display = analyze_audio_file(audio_path)

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
            "Subtypes": []
        }

        burnout_score = predict_burnout(raw_dict)
        suggestion_text = get_suggestion_text(burnout_score)

        return PredictionResponse(
            burnout_score=burnout_score,
            suggestion=suggestion_text,
            debug_data=raw_dict
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")
        
    finally:
        # Prevent disk out-of-space crash cycles inside docker container instances
        if os.path.exists(video_path):
            os.unlink(video_path)
        if os.path.exists(audio_path):
            os.unlink(audio_path)