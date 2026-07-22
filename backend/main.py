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
from catboost import Pool
import os
import io
import tempfile
import warnings

# Ignore user warnings for scaler inputs
warnings.filterwarnings('ignore', category=UserWarning)

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
    scaler_q = joblib.load('scaler_q.joblib')
    scaler_b = joblib.load('scaler_b.joblib')
    model_q = joblib.load('model_q.joblib')
    model_b = joblib.load('model_b.joblib')
    model_meta = joblib.load('model_meta.joblib')
except FileNotFoundError:
    print("WARNING: Model files (scaler_q, scaler_b, model_q, model_b, model_meta) not found in current directory. Prediction will fail.")
    scaler_q = None
    scaler_b = None
    model_q = None
    model_b = None
    model_meta = None
except Exception as e:
    print(f"Error loading late fusion model files: {e}")
    scaler_q = None
    scaler_b = None
    model_q = None
    model_b = None
    model_meta = None

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

def preprocess_input(raw_dict):
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

    # Q features: 'Q1_inv', 'Q2', 'Q3', 'Q4_inv', 'Q5_inv', 'Survey_Sum'
    q_features = q_encoded + [survey_sum]

    # Bio features: 'Avg_EAR', 'Std_EAR', 'Avg_MAR', 'Std_MAR', 'Exhaustion_Ratio',
    #               'Positive_Percent', 'Neutral_Percent', 'Negative_Percent',
    #               'Sentiment_Pos', 'Sentiment_Neu', 'Sentiment_Neg', 'Sentiment_Comp'
    bio_features = [
        EAR_avg, EAR_std,  
        MAR_avg, MAR_std,  
        exhaustion_ratio,
        pos_emotion, neu_emotion, neg_emotion,
        sent_pos, sent_neu, sent_neg, sent_comp
    ]

    return q_features, bio_features

def predict_burnout(raw_dict):
    if not scaler_q or not scaler_b or not model_q or not model_b or not model_meta:
        raise RuntimeError("Model files not loaded. Cannot predict.")
    q_features, bio_features = preprocess_input(raw_dict)
    
    X_q = np.array(q_features).reshape(1, -1)
    X_b = np.array(bio_features).reshape(1, -1)

    X_q_scaled = scaler_q.transform(X_q)
    X_b_scaled = scaler_b.transform(X_b)

    pred_q = model_q.predict(X_q_scaled)
    pred_b = model_b.predict(X_b_scaled)

    val_q = float(pred_q[0]) if isinstance(pred_q, np.ndarray) else float(pred_q)
    val_b = float(pred_b[0]) if isinstance(pred_b, np.ndarray) else float(pred_b)

    X_meta = np.column_stack((val_q, val_b))
    pred_fused = model_meta.predict(X_meta)
    
    score = float(pred_fused[0]) if isinstance(pred_fused, np.ndarray) else float(pred_fused)
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


FEATURE_METADATA = [
    {
        "name": "Q1_inv",
        "display_name": "Energy Levels & Vitality",
        "category": "Self-Reported",
        "desc_worsening": "Lower self-reported energy levels contributed to a higher stress rating.",
        "desc_protective": "High self-reported energy levels helped keep your stress rating lower."
    },
    {
        "name": "Q2",
        "display_name": "Cognitive Disconnect",
        "category": "Self-Reported",
        "desc_worsening": "Feeling like you are going through the motions increased your stress score.",
        "desc_protective": "Feeling engaged and connected in your daily activities helped lower your stress score."
    },
    {
        "name": "Q3",
        "display_name": "Physical & Emotional Fatigue",
        "category": "Self-Reported",
        "desc_worsening": "Self-reported physical and emotional exhaustion increased your stress score.",
        "desc_protective": "Minimal self-reported fatigue acted as a buffer to keep your stress score low."
    },
    {
        "name": "Q4_inv",
        "display_name": "Satisfaction with Progress",
        "category": "Self-Reported",
        "desc_worsening": "Lower satisfaction with daily progress increased your burnout risk.",
        "desc_protective": "A strong sense of pride in your progress helped lower your burnout risk."
    },
    {
        "name": "Q5_inv",
        "display_name": "Sense of Accomplishment",
        "category": "Self-Reported",
        "desc_worsening": "A reduced sense of achieving meaningful outcomes contributed to your stress level.",
        "desc_protective": "A strong sense of accomplishment helped reduce your overall stress level."
    },
    {
        "name": "Avg_EAR",
        "display_name": "Eye Openness (Focus/Tension)",
        "category": "Biometrics",
        "desc_worsening": "Narrowed eye openness (low EAR) indicated physiological fatigue, increasing your score.",
        "desc_protective": "Open, relaxed eyes (high EAR) indicated alertness, keeping your score lower."
    },
    {
        "name": "Std_EAR",
        "display_name": "Blink Variation (Alertness)",
        "category": "Biometrics",
        "desc_worsening": "Higher variation in eye blinks suggested irregular focus or fatigue.",
        "desc_protective": "Stable eye blink patterns indicated consistent focus and calm alertness."
    },
    {
        "name": "Avg_MAR",
        "display_name": "Mouth Tension (Expressiveness)",
        "category": "Biometrics",
        "desc_worsening": "Elevated mouth tension or movement suggested high physiological strain.",
        "desc_protective": "Relaxed mouth tension indicated positive composure, lowering your score."
    },
    {
        "name": "Std_MAR",
        "display_name": "Mouth Dynamics (Strain)",
        "category": "Biometrics",
        "desc_worsening": "Irregular mouth movements or tension spikes suggested stress response expression.",
        "desc_protective": "Stable mouth movement dynamics suggested emotional stability and ease."
    },
    {
        "name": "Positive_Percent",
        "display_name": "Positive Facial Expression",
        "category": "Biometrics",
        "desc_worsening": "Low frequency of positive facial expressions contributed to a higher stress index.",
        "desc_protective": "Frequent smiles and positive expressions acted as a strong protective wellness factor."
    },
    {
        "name": "Neutral_Percent",
        "display_name": "Facial Composure & Calm",
        "category": "Biometrics",
        "desc_worsening": "A low percentage of calm/neutral facial states increased your stress index.",
        "desc_protective": "A high percentage of calm, neutral facial composure helped lower your score."
    },
    {
        "name": "Negative_Percent",
        "display_name": "Negative Facial Tension",
        "category": "Biometrics",
        "desc_worsening": "Frequent micro-expressions of negative tension or worry increased your score.",
        "desc_protective": "Minimal facial indicators of negative tension helped keep your score low."
    },
    {
        "name": "Sentiment_Pos",
        "display_name": "Vocal Optimism",
        "category": "Voice & Tone",
        "desc_worsening": "Lower levels of positive sentiment in your speech increased your score.",
        "desc_protective": "Higher levels of positive sentiment in your speech helped lower your score."
    },
    {
        "name": "Sentiment_Neu",
        "display_name": "Vocal Composure",
        "category": "Voice & Tone",
        "desc_worsening": "Lower vocal neutrality suggested heightened emotional strain in your tone.",
        "desc_protective": "Balanced, neutral vocal delivery indicated composure, reducing your score."
    },
    {
        "name": "Sentiment_Neg",
        "display_name": "Vocal Frustration",
        "category": "Voice & Tone",
        "desc_worsening": "Underlying negative sentiment in your voice tone increased your score.",
        "desc_protective": "Absent vocal frustration or negative tone helped lower your score."
    },
    {
        "name": "Sentiment_Comp",
        "display_name": "Overall Tone Positivity",
        "category": "Voice & Tone",
        "desc_worsening": "Negative compound sentiment in your speech tone increased your score.",
        "desc_protective": "Positive compound sentiment in your speech tone helped keep your score low."
    },
    {
        "name": "Survey_Sum",
        "display_name": "Self-Reported Stress Sum",
        "category": "Self-Reported",
        "desc_worsening": "Your high self-reported stress sum is the primary driver of this score.",
        "desc_protective": "Your low self-reported stress sum is a key contributor to your low score."
    },
    {
        "name": "Exhaustion_Ratio",
        "display_name": "Mouth-to-Eye Tension Ratio",
        "category": "Biometrics",
        "desc_worsening": "An elevated mouth-to-eye tension ratio indicated physiological fatigue.",
        "desc_protective": "A low mouth-to-eye tension ratio suggested good physical energy and relaxation."
    }
]

# --- FastAPI Implementation ---
app = FastAPI(title="Burnout Regression API")

from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    print(f"FastAPI Validation Error: {exc.errors()} | Body: {exc.body}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": str(exc.body)},
    )

# Enable Cross-Origin requests so your Vercel site can call it
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ShapContribution(BaseModel):
    name: str
    display_name: str
    category: str
    shap_value: float
    effect: str
    description: str

class PredictionResponse(BaseModel):
    burnout_score: float
    suggestion: str
    debug_data: dict
    shap_base_value: float
    shap_contributions: list[ShapContribution]

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

        # Compute SHAP values
        shap_base_value = 0.0
        contributions = []
        if scaler_q and scaler_b and model_q and model_b and model_meta:
            try:
                q_features, bio_features = preprocess_input(raw_dict)
                X_q = np.array(q_features).reshape(1, -1)
                X_b = np.array(bio_features).reshape(1, -1)
                X_q_scaled = scaler_q.transform(X_q)
                X_b_scaled = scaler_b.transform(X_b)

                # Compute shap values for both submodels
                pool_q = Pool(data=X_q_scaled)
                shap_vals_q = model_q.get_feature_importance(data=pool_q, type="ShapValues")[0]
                
                pool_b = Pool(data=X_b_scaled)
                shap_vals_b = model_b.get_feature_importance(data=pool_b, type="ShapValues")[0]

                # Extract meta weights and intercept
                w_q = float(model_meta.coef_[0])
                w_b = float(model_meta.coef_[1])
                intercept = float(model_meta.intercept_)

                base_q = float(shap_vals_q[-1])
                base_b = float(shap_vals_b[-1])
                shap_base_value = w_q * base_q + w_b * base_b + intercept

                # Feature mappings to indices in the sub-models
                q_map = {
                    "Q1_inv": 0, "Q2": 1, "Q3": 2, "Q4_inv": 3, "Q5_inv": 4, "Survey_Sum": 5
                }
                b_map = {
                    "Avg_EAR": 0, "Std_EAR": 1, "Avg_MAR": 2, "Std_MAR": 3, "Exhaustion_Ratio": 4,
                    "Positive_Percent": 5, "Neutral_Percent": 6, "Negative_Percent": 7,
                    "Sentiment_Pos": 8, "Sentiment_Neu": 9, "Sentiment_Neg": 10, "Sentiment_Comp": 11
                }

                for meta in FEATURE_METADATA:
                    name = meta["name"]
                    if name in q_map:
                        idx = q_map[name]
                        shap_val = w_q * float(shap_vals_q[idx])
                    elif name in b_map:
                        idx = b_map[name]
                        shap_val = w_b * float(shap_vals_b[idx])
                    else:
                        shap_val = 0.0

                    effect = "worsening" if shap_val > 0 else "protective"
                    desc = meta["desc_worsening"] if shap_val > 0 else meta["desc_protective"]
                    contributions.append(ShapContribution(
                        name=name,
                        display_name=meta["display_name"],
                        category=meta["category"],
                        shap_value=shap_val,
                        effect=effect,
                        description=desc
                    ))
            except Exception as shap_err:
                print(f"SHAP calculation failed in predict endpoint: {shap_err}")

        return PredictionResponse(
            burnout_score=burnout_score,
            suggestion=suggestion_text,
            debug_data=raw_dict,
            shap_base_value=shap_base_value,
            shap_contributions=contributions
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")
        
    finally:
        # Prevent disk out-of-space crash cycles inside docker container instances
        if os.path.exists(video_path):
            os.unlink(video_path)
        if os.path.exists(audio_path):
            os.unlink(audio_path)
