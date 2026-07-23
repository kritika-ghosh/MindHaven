# MindHaven Frontend Handover Guide

This guide provides a comprehensive technical overview of the **MindHaven** frontend application. Use this document to redesign the UI/UX without breaking core functionalities, data flows, or API integrations.

---

## 📁 1. Frontend File Structure & Map

* **`index.html`** (Landing Page)
  * Hero section, feature walkthroughs, and entry points.
  * Handles authentication choice: Supabase sign-in/sign-up redirect or **Guest Mode** (bypasses Supabase using local state).
* **`assess.html`** (Assessment Panel)
  * Collects 5 survey answers.
  * Records **Webcam Video** and **Microphone Audio** using browser `MediaRecorder`.
  * Sends multi-part Form Data to the Hugging Face backend `/predict` endpoint.
  * Redirects to `insights.html` upon completion.
* **`insights.html`** (Current Assessment Results & Therapy Chatbot)
  * Displays the calculated **Vitality Score** continuously.
  * Renders the **SHAP stress driver/wellness buffer chart**.
  * Shows the vocal transcript, sentiment valence, and AI therapist conversational chat box.
* **`dashboard.html`** (Longitudinal Dashboard)
  * Fetches historical assessments from Supabase.
  * Plots trendlines using Chart.js.
  * Displays detail modals for previous assessment records.
* **`js/utils.js`** (Core Javascript Core Helpers)
  * Supabase client initialization, auth guards (`requireAuth`), and longitudinal math models.
* **`js/config.js`** (Global Configuration)
  * Points to the Hugging Face Space endpoint and contains Groq API fallbacks.

---

## 🔌 2. Backend API Endpoint Details
The backend is hosted as a single unified container on Hugging Face:
**Base URL**: `https://kritika53245-mindhaven.hf.space`

### 1. Burnout Predictor (`POST /predict`)
* **Type**: Multi-part Form Data
* **Inputs**:
  * `video_file`: Binary file (WebM format)
  * `audio_file`: Binary file (WebM format)
  * `answer_1` to `answer_5`: Strings (e.g. `"Rarely"`, `"Often"`, `"Sometimes"`, etc.)
* **Response JSON Format**:
  ```json
  {
    "burnout_score": 1.1255,
    "suggestion": "Detailed therapeutic advice string...",
    "debug_data": {
      "Questionnaire Answers": ["Rarely", "Rarely", "Rarely", "Often", "Often"],
      "EAR": 0.14,
      "MAR": 0.22,
      "Emotions": { "Positive %": "17.2%", "Neutral %": "65.5%", "Negative %": "17.2%" },
      "Voice Transcript": "Transcript text...",
      "Sentiment": "Comp: -0.78"
    },
    "shap_base_value": 1.89,
    "shap_contributions": [
      {
        "name": "Avg_EAR",
        "display_name": "Eye Composure",
        "category": "biometric",
        "shap_value": 0.05,
        "effect": "worsening",
        "description": "Lower blink rates suggest fatigue..."
      }
    ]
  }
  ```

### 2. CBT Chatbot completions (`POST /v1/chat/completions`)
* **Type**: Application/JSON (OpenAI Compatible)
* **Body**:
  ```json
  {
    "messages": [
      { "role": "system", "content": "You are MindHaven, an empathetic therapist." },
      { "role": "user", "content": "I feel stressed." }
    ],
    "temperature": 0.7,
    "max_tokens": 512,
    "stream": true
  }
  ```
* **Streaming format**: Returns Server-Sent Events (SSE) data chunks (`data: {...}\n\n` followed by `data: [DONE]\n\n`).

---

## 💾 3. State Management & Storage Keys

* **`sessionStorage.getItem('mindhaven_guest')`**: `"true"` if using Guest mode.
* **`sessionStorage.getItem('burnout_prediction')`**: Holds the JSON string of the latest prediction response.
* **`sessionStorage.getItem('mindhaven_user')`**: Display name of the active user.

---

## 🗄️ 4. Supabase Database Schema
If not in Guest mode, assessments are stored in the `assessments` table:
* `id` (UUID, Primary Key)
* `user_id` (UUID, Foreign Key)
* `answers` (JSON array of strings)
* `burnout_score` (Float8)
* `vitality_score` (Int4, calculated by `burnoutToVitality`)
* `ear` (Float8)
* `mar` (Float8)
* `emo_pos`, `emo_neu`, `emo_neg` (Float8 percentages)
* `voice_transcript` (Text)
* `sentiment_compound` (Float8)
* `llm_insight` (Text)
* `created_at` (Timestampz)

---

## 🎛️ 5. Critical JavaScript Logic (DO NOT BREAK)

When redesigning the files, keep these core JS helper functions intact. They are imported from `js/utils.js`:

### 1. Continuous Vitality Conversion
Converts the backend's continuous $0.0 \to 4.0$ burnout score to a $100\% \to 0\%$ vitality percentage. It uses **linear interpolation** (lerp) to represent biometric variance visually on the UI:
```javascript
function burnoutToVitality(score) {
  var val = parseFloat(score);
  if (isNaN(val)) return 54;
  val = Math.max(0.0, Math.min(4.0, val));
  var anchors = [
    { x: 0.0, y: 92 }, { x: 1.0, y: 78 }, { x: 2.0, y: 54 }, { x: 3.0, y: 32 }, { x: 4.0, y: 12 }
  ];
  for (var i = 0; i < anchors.length - 1; i++) {
    var a = anchors[i], b = anchors[i+1];
    if (val >= a.x && val <= b.x) {
      var pct = (val - a.x) / (b.x - a.x);
      return Math.round(a.y + pct * (b.y - a.y));
    }
  }
  return 54;
}
```

### 2. SHAP Reconstruct fallback
If SHAP values are ever missing or mock data is needed, `ensureShapData(prediction)` dynamically compiles contributions based on the raw metrics so the Chart renderers do not crash:
```javascript
window.activeShapData = ensureShapData(data);
```

### 3. longitudinal Trend badge
Calculates progress delta between your last assessment and the previous one:
```javascript
const trajectory = calculateRiskTrajectory(historyRecords);
// Returns: { signal: "Improving/Stable/Worsening", delta: 0.12, label: "Stable Composure", ... }
```

---

## 🎨 6. Redesign Guidelines for Claude

1. **Keep DOM element IDs intact**: The Chart renders, text updates, and webcam indicators rely on exact element IDs (e.g. `vitality-score`, `vitality-label`, `vitality-desc`, `shap-bars-container`, `chat-messages`, etc.).
2. **Audio/Video Streamers**: In `assess.html`, the elements for video capture (`#webcam-preview`, `#recording-indicator`, `#progress-bar`) are tightly coupled with the webcam recording loop. Keep their functional event listeners.
3. **CORS Headers**: Ensure all fetch calls use the Hugging Face base URL (`https://kritika53245-mindhaven.hf.space`) and support CORS.
