<div align="center">

# 🧠 MindHaven

### *Objective continuous student burnout diagnostics powered by psychometric, computer vision, and acoustic AI multi-modal late-fusion.*

<br/>

[![Python](https://img.shields.io/badge/Python-3.10-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![HTML5](https://img.shields.io/badge/HTML5-supported-E34F26?style=flat-square&logo=html5&logoColor=white)](https://html.spec.whatwg.org/)
[![Three.js](https://img.shields.io/badge/Three.js-r128-black?style=flat-square&logo=three.js&logoColor=white)](https://threejs.org/)
[![Supabase](https://img.shields.io/badge/Supabase-database-3ecf8e?style=flat-square&logo=supabase&logoColor=white)](https://supabase.com/)
[![Docker](https://img.shields.io/badge/Docker-ready-2496ED?style=flat-square&logo=docker&logoColor=white)](https://www.docker.com/)
[![Vercel](https://img.shields.io/badge/Vercel-deployed-000000?style=flat-square&logo=vercel&logoColor=white)](https://vercel.com/)
[![Hugging Face](https://img.shields.io/badge/Hugging%20Face-Spaces-FFD21E?style=flat-square&logo=huggingface&logoColor=black)](https://huggingface.co/spaces)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

</div>

---

## 📸 Demo & Interfaces

<div align="center">

[![MindHaven Technical Demo UI Mockup](https://img.youtube.com/vi/gg7GkVSvf-w/maxresdefault.jpg)](https://mind-haven-zeta.vercel.app)

*(Click to open the active live deployment: **[mind-haven-zeta.vercel.app](https://mind-haven-zeta.vercel.app)**)*

</div>

---

## 🌟 Features

- 📝 **Student-Centric Psychometrics** — Mapped closely to the Maslach Burnout Inventory (MBI) to establish a baseline.
- 👁️ **Computer Vision Aspect Ratios** — Measures physiological fatigue indicators including **Eye Aspect Ratio (EAR)** and **Mouth Aspect Ratio (MAR)** via MediaPipe.
- 🎭 **Micro-Expression Emotion Proportions** — Utilizes DeepFace to track positive, neutral, and negative facial expressions.
- 🗣️ **Vocal Sentiment Channel** — Transcribes vocal responses using browser WebRTC and computes sentiment polarity compound scores via VADER.
- 🧠 **Continuous Regression ML** — Leverages a pre-trained **CatBoost Regressor** (tuned to $95.76\%$ $R^2$) to output a highly precise burnout index between `0.0` (Low) and `4.0` (Severe).
- 💬 **Interactive AI Wellness Coach** — Integrates Groq (Llama-3.3-70b-versatile) to provide personalized, warm, and highly actionable recovery plans.
- 📊 **Telemetry Trends Dashboard** — Chart.js integration visualizes historical assessments, vitality metrics, and expression trends over time.

---

## 🛠️ Tech Stack

| Layer | Technologies |
|---|---|
| **Frontend** | Vanilla HTML5, CSS3, JavaScript (ES6+), GSAP (Animations), Three.js (3D background), Chart.js |
| **Backend API** | FastAPI, Python 3.10, OpenCV, MediaPipe, DeepFace, SpeechRecognition, VADER Sentiment, Joblib |
| **Database** | Supabase (PostgreSQL) client authentication & telemetry storage |
| **AI / LLMs** | CatBoost Regressor, Random Forest Regressor, SVR, Groq / Llama-3.3-70b-versatile (Wellness Coach) |
| **Infrastructure** | Docker, Hugging Face Spaces (port 7860), Vercel |

---

## 🚀 Pipeline & Methodology

The late-fusion diagnostic pipeline executes five sequential phases, resolving objective biological state markers:

```
📝  Phase 1 · Psychometric Baseline
      ↓  User submits responses to 5 student-centric questionnaire statements
👁️  Phase 2 · Biometric Tracking
      ↓  Camera capture maps facial landmarks (EAR/MAR) and records emotion proportions
🗣️  Phase 3 · Sentiment Acoustics
      ↓  Audio capture transcribes user response and computes compound sentiment polarity
🧠  Phase 4 · Diagnostics & Inference
      ↓  FastAPI feeds 18 features into scaled CatBoost Regressor to predict burnout score
💬  Phase 5 · Recovery Plan
         Llama-3.3 generates empathetic wellness reports and recovery micro-plans
```

### 🤖 Mathematical Modeling

*   **Eye Aspect Ratio (EAR)**: Computes eye fatigue and blink duration:

$$\text{EAR} = \frac{||\text{P}_2 - \text{P}_6|| + ||\text{P}_3 - \text{P}_5||}{2 ||\text{P}_1 - \text{P}_4||}$$

*   **Mouth Aspect Ratio (MAR)**: Computes mouth openness and yawning frequencies:

$$\text{MAR} = \frac{\text{Inner Mouth Height}}{\text{Inner Mouth Width}}$$

---

## 📊 Model Evaluation & Benchmarks

All models were evaluated under strict 5-Fold Cross-Validation on the empirical VIT student dataset, predicting a continuous target to capture fine-grained transitions in fatigue:

| Metric | Support Vector Regressor (SVR) | Random Forest Regressor | CatBoost Regressor (Ours) |
| :--- | :---: | :---: | :---: |
| **Mean R² Score** | 92.95% | 95.32% | **95.76%** |
| **Mean RMSE** | 0.2227 | 0.1805 | **0.1727** |
| **Mean MAE** | 0.1719 | 0.1444 | **0.1378** |

---

## 📁 Project Structure

```
MindHaven/
├── frontend/               # Client-Side Application
│   ├── css/                # Custom CSS styling stylesheets
│   ├── js/                 # JavaScript scripts
│   │   ├── 3d-elements.js  # Three.js 3D background elements
│   │   ├── config.js       # Git-ignored local configuration overrides
│   │   ├── theme.js        # Light/dark UI mode toggling
│   │   └── utils.js        # Shared database hooks and default configurations
│   ├── index.html          # Wellness home page portal
│   ├── auth.html           # Authentication portal
│   ├── assess.html         # Multimodal capture interface
│   ├── insights.html       # AI Coach advisor panel
│   ├── dashboard.html      # Recovery tracking dashboard
│   ├── breathe.html        # Interactive breathing recovery exercises
│   └── about.html          # Scientific methodology
├── backend/                # Production Hugging Face Container API
│   ├── Dockerfile          # HF Docker deployment definition
│   ├── main.py             # FastAPI regression inference service
│   ├── model.joblib        # Pre-trained CatBoostRegressor model
│   ├── scaler.joblib       # Standard Scaler artifact
│   ├── requirements.txt    # Production dependencies
│   ├── README.md           # Hugging Face Space configuration metadata
│   └── .gitattributes      # Git LFS tracking configuration
├── model_training/         # Notebooks and empirical data
│   ├── data.csv            # Empirically collected VIT student burnout data
│   ├── Model_Training_Regression.ipynb # Fully-executed training pipeline
│   └── regression_output/  # Serialized model export directory
└── chatbot_finetuning/     # Cognitive Behavioral Therapy Fine-Tuning
    └── MindHaven_CBT_FineTuning.ipynb
```

---

## 🔌 API Reference

Base URL: `https://kritika53245-mindhaven.hf.space` (production) or `http://localhost:7860` (local)

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/predict` | Accept video, audio, and questionnaire responses; returns burnout score and details |
| `GET` | `/health` | Lightweight status check for keep-alive monitoring |

### `POST /predict`

**Form data (multipart/form-data)**

| Field | Type | Required | Description |
|---|---|---|---|
| `video_file` | `file` | ✅ | MP4 camera video clip (15-20 seconds) |
| `audio_file` | `file` | ✅ | WAV audio clip with vocal response |
| `answer_1` to `answer_5` | `string` | ✅ | Survey response options (`Never` to `Always`) |

**Response**

```json
{
  "burnout_score": 2.5412,
  "suggestion": "Your burnout score is Moderate (40-60). You're starting to feel physical and emotional exhaustion...",
  "debug_data": {
    "Questionnaire Answers": ["Sometimes", "Often", "Sometimes", "Often", "Sometimes"],
    "EAR": "0.24 ± 0.03",
    "MAR": "0.16 ± 0.02",
    "Emotions": { "Positive %": "10.5%", "Neutral %": "62.4%", "Negative %": "27.1%" },
    "Voice Transcript": "I am feeling quite tired lately...",
    "Sentiment": "Pos: 0.12, Neu: 0.65, Neg: 0.23, Comp: -0.21"
  }
}
```

---

## 🛠️ Local Setup & Configuration

### Prerequisites
- Python 3.10+
- Node.js (or simple HTTP server launcher)
- Custom keys for Supabase database access (configured in `js/utils.js`)

### 🐍 Python Backend (FastAPI)

```bash
cd backend

# Create and activate environment
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

# Install requirements
pip install -r requirements.txt

# Start local server
uvicorn main:app --host 0.0.0.0 --port 7860 --reload
```

---

### ⚛️ Frontend UI (Vercel Ready)

```bash
cd frontend

# Run local server
python -m http.server 8000
```
Open [http://localhost:8000](http://localhost:8000) in your browser.

To customize your API endpoint or add Groq wellness coach keys, create a `js/config.js` file:
```javascript
// frontend/js/config.js
window.MINDHAVEN_CONFIG = {
  GROQ_KEY: "gsk_your_private_groq_key_here",
  API_URL: "http://localhost:7860/predict" // Override to local backend
};
```

---

## 🚢 Deployment

### Backend (Hugging Face Spaces)
The backend folder is optimized for Dockerized Space deployments:
- Space builds automatically using the production multi-stage [`backend/Dockerfile`](backend/Dockerfile).
- Exposed on standard Hugging Face port `7860`.

### Frontend (Vercel)
The static web application is deployed via:
```bash
cd frontend
npx vercel --prod
```

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome!

1. Fork the repository.
2. Create your feature branch (`git checkout -b feat/amazing-feature`).
3. Commit your changes using [Conventional Commits](https://www.conventionalcommits.org/).
4. Push to the branch and open a Pull Request.

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

<div align="center">

Made with ❤️ by **[Kritika Ghosh](https://github.com/kritika-ghosh)**

</div>
