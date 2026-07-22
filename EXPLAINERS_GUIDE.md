# MindHaven Explainability & Predictive Engine Guide

This document explains the technical details, mathematical alignment, and data pipelines for the **Burnout Predictive Engine**, **SHAP Explainability Engine**, and **Longitudinal Risk Trajectory** features implemented in MindHaven.

---

## 1. The Burnout Predictive Engine

The MindHaven backend uses a **CatBoost Regression Model** trained to assess occupational burnout risk based on multi-modal biometrics and questionnaire inputs.

### The Input Feature Vector (18 Features)
Every time a user completes an assessment, the system compiles a multi-modal feature vector of **18 values** that is standardized using a pre-trained `StandardScaler`:

| # | Feature Code Name | Category | Source / Description |
|---|-------------------|----------|---------------------|
| 1 | `q1` | Survey | Frequency of feeling emotionally drained from work |
| 2 | `q2` | Survey | Frequency of feeling used up at the end of the work day |
| 3 | `q3` | Survey | Frequency of feeling fatigued when getting up to face work |
| 4 | `q4` | Survey | Frequency of feeling working all day is a strain |
| 5 | `q5` | Survey | Frequency of feeling burned out from work |
| 6 | `ear_mean` | Biometrics | Mean Eye Aspect Ratio (indicator of blink frequency and fatigue) |
| 7 | `ear_std` | Biometrics | Standard deviation of Eye Aspect Ratio (indicator of blink volatility) |
| 8 | `mar_mean` | Biometrics | Mean Mouth Aspect Ratio (indicator of jaw clenching and tension) |
| 9 | `mar_std` | Biometrics | Standard deviation of Mouth Aspect Ratio (jaw movement volatility) |
| 10| `pos_pct` | Biometrics | Percentage of facial frames reflecting positive emotions |
| 11| `neu_pct` | Biometrics | Percentage of facial frames reflecting neutral composure |
| 12| `neg_pct` | Biometrics | Percentage of facial frames reflecting negative emotions |
| 13| `num_words` | Voice & Tone | Total word count in speech transcript (indicators of cognitive speed) |
| 14| `sentiment_pos` | Voice & Tone | Positivity score from text sentiment analysis |
| 15| `sentiment_neu` | Voice & Tone | Neutrality score from text sentiment analysis |
| 16| `sentiment_neg` | Voice & Tone | Negativity score from text sentiment analysis |
| 17| `sentiment_compound`| Voice & Tone | Overall compound sentiment valence (runs from -1.0 to +1.0) |
| 18| `vocal_pitch` | Voice & Tone | Average vocal frequency in Hz (indicator of vocal cord tension) |

### Pre-processing & Normalization
1. **Ordinal questionnaire encoding**: Answers like "Rarely" or "Often" are mapped to numeric values (`0` to `4`).
2. **Text sentiment extraction**: Speech transcripts are evaluated using `vaderSentiment` to extract positive/negative ratios.
3. **Scaling**: Questionnaire and biometric values are scaled independently using `scaler_q.joblib` and `scaler_b.joblib`.
4. **Scoring**: Predictions from the Questionnaire and Biometrics sub-models are combined using the `model_meta.joblib` blending model.

### Late Fusion Architecture

#### Why We Implemented Late Fusion (The Problem)
In the initial single-model (early fusion) setup, all features (subjective survey answers and objective biometrics) were fed into a single regressor. Because the synthetic training target score was mathematically dominated by the questionnaire sum, the machine learning model suffered from **feature dominance**. The model learned to almost entirely ignore the facial and vocal biometrics when survey answers were present, sometimes even leading to inverted logic (e.g. predicting a higher burnout score for positive biometrics than negative ones). To restore the objective validation power of biometrics and prevent surveys from completely overriding them, we moved to a Late Fusion architecture.

#### What Late Fusion Is (The Solution)
**Late Fusion (Decision-Level Fusion)** is an architectural pattern in multimodal machine learning where separate independent models are trained on each individual input modality first, and their individual predictions are subsequently combined (fused) by a meta-model. 

In MindHaven, the prediction pipeline consists of:
1. **Survey Sub-model ($P_Q$)**: A CatBoost model (`model_q.joblib`) trained solely on the 6 questionnaire-based features to predict a baseline burnout score.
2. **Biometrics Sub-model ($P_B$)**: A CatBoost model (`model_b.joblib`) trained solely on the 12 facial and vocal biometrics to predict a physical/affective burnout indicator.
3. **Blending Meta-model ($P_{\text{final}}$)**: A Linear Regression meta-model (`model_meta.joblib`) that blends the two sub-model predictions using optimized weights:
   $$P_{\text{final}} = w_Q \cdot P_Q + w_B \cdot P_B + \text{intercept}$$
   *(Currently, $w_Q = 0.865$, $w_B = 0.237$, and $\text{intercept} = -0.193$)*

This ensures that shifts in a user's physical and vocal state directly and reliably affect the final burnout score (adjusting it by up to $\pm 10\%$), even if their self-reported survey answers remain identical.

---

## 2. The SHAP Explainability Engine

A common problem in clinical AI is the "black box" effect—users are presented with a score but do not understand why they received it. **SHAP (Shapley Additive Explanations)** bridges this trust gap by explaining the mathematical contribution of each feature to the final score.

### The Game Theory Formula
SHAP values are based on cooperative game theory. Each feature behaves like a "player" in a game, and the final prediction score is the "payout". The Shapley value is the average marginal contribution of a feature across all possible feature combinations.

For a specific prediction $f(X)$:
$$f(X) = \phi_0 + \sum_{i=1}^{M} \phi_i$$

Where:
* $f(X)$ is the final **Burnout Score** (e.g., `1.96`).
* $\phi_0$ is the **Base Value** (the average burnout score across the training set, which is exactly **`1.89`**).
* $\phi_i$ is the **SHAP contribution** of feature $i$.
* $M$ is the number of features (`18`).

### Stress Drivers vs. Wellness Buffers
* **Stress Drivers ($\phi_i > 0$)**: Features that pulled the user's score **higher** (represented in **coral red**).
  * *Example*: Higher jaw clenching (`mar_mean`) adds `+0.24` to the score.
* **Wellness Buffers ($\phi_i < 0$)**: Features that pulled the user's score **lower** (represented in **sage green**).
  * *Example*: High positive emotions (`pos_pct`) subtracts `-0.18` from the score.

### Zero-Dependency Tree SHAP
To deploy in zero-cost, lightweight environments (like Hugging Face Spaces or slim Docker images), we bypass heavy C++ libraries like the Python `shap` package. Instead, we call **CatBoost's native Tree SHAP** method on both sub-models independently, and scale their relative contributions using the meta-model's coefficients.

For each sub-model, we get the feature contributions and base values:
```python
# Native fast SHAP calculation for Questionnaire Sub-model
shap_vals_q = model_q.get_feature_importance(data=Pool(X_q_scaled), type="ShapValues")[0]

# Native fast SHAP calculation for Biometrics Sub-model
shap_vals_b = model_b.get_feature_importance(data=Pool(X_b_scaled), type="ShapValues")[0]
```

We then blend their contributions linearly using the meta-model weights ($w_Q$ and $w_B$):
* **Final Base Value**: $\phi_{0,\text{final}} = w_Q \cdot \phi_{0,Q} + w_B \cdot \phi_{0,B} + \text{intercept}$
* **Questionnaire Feature $i$ Contribution**: $\phi_{i,\text{final}} = w_Q \cdot \phi_{i,Q}$
* **Biometrics Feature $j$ Contribution**: $\phi_{j,\text{final}} = w_B \cdot \phi_{j,B}$

This returns the final contributions mapped directly to `FEATURE_METADATA` for the frontend.

---

## 3. Longitudinal Risk Trajectory

Instead of looking at a single point in time, the Longitudinal Risk Trajectory evaluates the trend of stress across multiple sessions.

### Trend Delta Calculation
Let $S_{latest}$ be the latest burnout score, and $S_{prev}$ be the score of the previous session. We calculate the delta difference:
$$\Delta = S_{latest} - S_{prev}$$

The system evaluates $\Delta$ using the following thresholds:
1. **Rising Risk ↗ ($\Delta > +0.15$)**: Burnout indicators are escalating. The UI shows a coral badge and warning prompts.
2. **Declining Risk ↘ ($\Delta < -0.15$)**: Stress is decreasing. The UI displays a sage green badge celebrating positive progress.
3. **Stable Trend → ($-0.15 \le \Delta \le +0.15$)**: Composure remains stable.

### Shaded Severity Bands
In `dashboard.html`, the progression line chart overlays the user's scores on top of color-coded horizontal bands to show their trajectory relative to clinical categories:
* **Severe (3.0 - 4.0)**: Red background area.
* **Moderate (1.5 - 3.0)**: Yellow background area.
* **Low/Mild (0.0 - 1.5)**: Green background area.
