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
[![MindHaven Technical Demo UI Mockup](https://img.youtube.com/vi/gg7GkVSvf-w/maxresdefault.jpg)](https://www.youtube.com/watch?v=6wFkLPPiBBk)

*(Click to open the active live deployment: **[mind-haven-zeta.vercel.app](https://mind-haven-zeta.vercel.app)**)*

</div>

---

## 🌟 Features

- 📝 **Student-Centric Psychometrics** — Mapped closely to the Maslach Burnout Inventory (MBI) to establish a baseline.
- 👁️ **Computer Vision Aspect Ratios** — Measures physiological fatigue indicators including **Eye Aspect Ratio (EAR)** and **Mouth Aspect Ratio (MAR)** via MediaPipe.
- 🎭 **Micro-Expression Emotion Proportions** — Utilizes DeepFace to track positive, neutral, and negative facial expressions.
- 🗣️ **Vocal Sentiment Channel** — Transcribes vocal responses using browser WebRTC and computes sentiment polarity compound scores via VADER.
- 🧠 **Continuous Regression ML** — Leverages a pre-trained **CatBoost Regressor** (tuned to $95.76\%$ $R^2$) to output a highly precise burnout index between `0.0` (Low) and `4.0` (Severe).
- 💬 **Interactive AI CBT Wellness Coach** — Connects to a custom fine-tuned Qwen model ([`mindhaven-cbt-qwen`](https://huggingface.co/kritika53245/mindhaven-cbt-qwen)) optimized for Cognitive Behavioral Therapy to provide empathetic, non-clinical supportive dialogue.
- 📊 **Telemetry Trends Dashboard** — Chart.js integration visualizes historical assessments, vitality metrics, and expression trends over time.

---

## 🛠️ Tech Stack

| Layer | Technologies |
|---|---|
| **Frontend** | Vanilla HTML5, CSS3, JavaScript (ES6+), GSAP (Animations), Three.js (3D background), Chart.js |
| **Backend API** | FastAPI, Python 3.10, OpenCV, MediaPipe, DeepFace, SpeechRecognition, VADER Sentiment, Joblib |
| **Database** | Supabase (PostgreSQL) client authentication & telemetry storage |
| **AI / LLMs** | CatBoost Regressor, Random Forest Regressor, SVR, Groq / Llama-3.3-70b-versatile, Qwen-CBT-Fine-Tuned |
| **Infrastructure** | Docker, Hugging Face Spaces (port 7860), Vercel |

---

## 🧠 Diagnostic Machine Learning Model

MindHaven replaces subjective self-reporting biases with an objective, continuous late-fusion machine learning model.

### 1. Preprocessing & Feature Engineering
During inference, a 20-second biometric capture window extracts high-accuracy statistical parameters across **18 distinct features**:
*   **Psychometrics (5 features):** `Q1_inv` (exhaustion/stress inverted), `Q2`, `Q3`, `Q4_inv` (pride in progress inverted), `Q5_inv` (meaningful outcomes inverted).
*   **Computer Vision (7 features):** `Avg_EAR`, `Std_EAR` (blinking dynamics), `Avg_MAR`, `Std_MAR` (jaw tension/yawning), `Positive_Percent`, `Neutral_Percent`, `Negative_Percent` (facial expression proportions).
*   **Acoustic Sentiment (4 features):** `Sentiment_Pos`, `Sentiment_Neu`, `Sentiment_Neg`, `Sentiment_Comp` (speech transcription polarity).
*   **Engineered Cross-Features (2 features):**
    *   `Survey_Sum`: Mapped sum reflecting raw questionnaire burnout severity:
        $$\text{Survey\\_Sum} = (4 - \text{Q1\\_inv}) + \text{Q2} + \text{Q3} + \text{Q4\\_inv} + \text{Q5\\_inv}$$
    *   `Exhaustion_Ratio`: Physiological ratio between mouth tension and eye fatigue:
        $$\text{Exhaustion\\_Ratio} = \frac{\text{Avg\\_MAR}}{\text{Avg\\_EAR} + 10^{-5}}$$

### 2. Training Protocol
The model was trained directly on the empirical VIT student dataset (266 cleaned, drop-na records) without synthetic row generation:
- **Target Indexing:** Designed a continuous target `Burnout_Score` (range `[0.0, 4.0]`) from survey baselines modified by biometric outliers.
- **Noise Injection:** Applied a normal noise perturbation ($\text{std} = 0.16$) during training to simulate real-world sensor variance.
- **Winning Model:** A **CatBoost Regressor** configured with hyperparameters: `iterations=150`, `learning_rate=0.07`, `depth=4`, `l2_leaf_reg=6`, and `random_seed=42`.

### 3. Model Benchmarks (5-Fold CV)

| Model Architecture | Mean R² Score | Mean RMSE | Mean MAE |
| :--- | :---: | :---: | :---: |
| **CatBoost Regressor (Ours)** | **95.76%** | **0.1727** | **0.1378** |
| Random Forest Regressor | 95.32% | 0.1805 | 0.1444 |
| Support Vector Regressor (SVR) | 92.95% | 0.2227 | 0.1719 |

---

## 💬 CBT Fine-Tuned Chatbot

MindHaven integrates a custom fine-tuned large language model, **`kritika53245/mindhaven-cbt-qwen`**, trained on Cognitive Behavioral Therapy (CBT) dialogue datasets.

### 1. Design & Objectives
Unlike general-purpose conversational LLMs, the CBT Chatbot is aligned to act as an empathetic wellness coach:
*   Reflects user stress patterns and biological metrics back in a supportive, non-clinical manner.
*   Guides users through cognitive restructuring (identifying automatic negative thoughts).
*   Recommends actionable recovery micro-plans tailored to their diagnostic score.

### 2. Architecture & Inference Setup
*   **Base Architecture:** Qwen-based causal language model.
*   **Inference Precision:** Loaded in `float16` half-precision to fit within a standard T4 GPU VRAM footprint (under 16GB VRAM).
*   **OpenAI Compatibility:** Served via a FastAPI gateway exposing `/v1/chat/completions`, formatting prompts dynamically using the Qwen chat template (`tokenizer.apply_chat_template`).

---

## 🚀 Deployment Architecture

MindHaven utilizes a hybrid cloud architecture designed to load models securely, keep configurations modular, and execute tasks asynchronously.

```
                  ┌───────────────────────────────┐
                  │      Vercel (Static Web)      │
                  │   - Loaded on HTTPS           │
                  │   - LocalStorage Overrides    │
                  └───────────────┬───────────────┘
                                  │
                  ┌───────────────┴───────────────┐
                  │                               │
                  ▼                               ▼
       ┌────────────────────┐           ┌────────────────────┐
       │ Hugging Face Space │           │    Google Colab    │
       │   (Docker API)     │           │   (T4 GPU Server)  │
       │  - predict_burnout │           │   - Qwen CBT LLM   │
       │  - Model LFS files │           │   - Ngrok Tunnel   │
       └────────────────────┘           └────────────────────┘
```

### 1. Frontend (Vercel)
The client-side interface is deployed as static assets to Vercel. 
- **Security & Config:** To prevent API keys from leaking to version control, client keys are resolved from the git-ignored `js/config.js`.
- **Dynamic Config Overrides:** In production on Vercel, the app implements a `localStorage` override system. Running the following command in the browser console connects your live Vercel frontend directly to your active Colab model server:
  ```javascript
  localStorage.setItem('MINDHAVEN_NGROK_URL', 'https://your-ngrok-subdomain.ngrok-free.dev');
  ```

### 2. Diagnostic Backend (Hugging Face Docker Space)
The FastAPI backend runs inside a multi-stage Docker container on Hugging Face Spaces:
- **Large File Storage (LFS):** Pre-trained models (`model.joblib` and `scaler.joblib`) are tracked via LFS configured in `.gitattributes`.
- **Docker Environment:** Runs on `python:3.10-slim`, installing essential libraries (`libgl1`, `libtbbmalloc2`) for OpenCV/MediaPipe frame analysis.
- **Deployment Endpoint:** Deployed to **[https://kritika53245-mindhaven.hf.space](https://kritika53245-mindhaven.hf.space)**.

### 3. Chatbot Server (Google Colab + Ngrok Tunnel)
To run GPU-accelerated LLM inference for free:
- The Qwen model is loaded inside a Google Colab notebook running on a **T4 GPU**.
- A FastAPI server acts as the API gateway on port `8000`.
- An HTTP tunnel is established via **Pyngrok**, exposing the notebook's port to a public URL.
- The server is run inside the Colab active notebook event loop natively using `uvicorn.Server(config).serve()`.
- Complete instructions are documented in [COLAB_NGROK_SETUP.md](chatbot_finetuning/COLAB_NGROK_SETUP.md).

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
    ├── MindHaven_CBT_FineTuning.ipynb
    └── COLAB_NGROK_SETUP.md # Google Colab & Ngrok serving guide
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
