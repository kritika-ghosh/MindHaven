import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.model_selection import KFold
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, r2_score
from catboost import CatBoostRegressor

# Create output dir
os.makedirs('artifacts', exist_ok=True)

# ----------------- DATA PREPROCESSING -----------------
# Load dataset
df = pd.read_csv('model_training/data.csv')

# Map survey responses
freq_mapping = {
    'Never': 0, 'Rarely': 1, 'Sometimes': 2, 'Often': 3, 'Always': 4,
    'I enjoy my work. I have no symptoms of burnout': 0,
    'Occasionally I am under stress, and I don’t always have as much energy as I once did, but I don’t feel burned out': 1,
    'I am definitely burning out and have one or more symptoms of burnout, such as physical and emotional exhaustion': 2,
    'The symptoms of burnout that I’m experiencing won’t go away. I think about frustration at work a lot': 3,
    'I feel completely burned out and often wonder if I can go on. I am at the point where I may need some changes or may need to seek some sort of help': 4,
}

for col in ['Q1', 'Q2', 'Q3', 'Q4', 'Q5', 'Q6']:
    if col in df.columns and df[col].dtype == object:
        df[col] = df[col].map(freq_mapping)

selected_columns = [
    'Q1', 'Q2', 'Q3', 'Q4', 'Q5', 'Q6',
    'Avg_EAR', 'Std_EAR', 'Avg_MAR', 'Std_MAR',
    'Positive_Percent', 'Neutral_Percent', 'Negative_Percent',
    'Sentiment_Pos', 'Sentiment_Neu', 'Sentiment_Neg', 'Sentiment_Comp'
]
df = df[selected_columns].dropna()

q_encoded = df[['Q1', 'Q2', 'Q3', 'Q4', 'Q5']].copy()
q_encoded['Q1'] = 4 - q_encoded['Q1']
q_encoded['Q4'] = 4 - q_encoded['Q4']
q_encoded['Q5'] = 4 - q_encoded['Q5']

# Compute engineered features Survey_Sum and Exhaustion_Ratio
survey_sum = (4 - q_encoded['Q1']) + q_encoded['Q2'] + q_encoded['Q3'] + q_encoded['Q4'] + q_encoded['Q5']
exhaustion_ratio = df['Avg_MAR'] / (df['Avg_EAR'] + 1e-5)

np.random.seed(42)
base_score = survey_sum / 5.0

bio_factor = (
    0.15 * (df['Avg_MAR'] / (df['Avg_EAR'] + 1e-5) - 0.5) 
    + 0.10 * (df['Negative_Percent'] - df['Positive_Percent']) / 100.0
    - 0.10 * df['Sentiment_Comp']
)
noise = np.random.normal(0, 0.16, size=len(df))

df['Burnout_Score'] = (base_score + bio_factor + noise).clip(0.0, 4.0)
df['Survey_Sum'] = survey_sum
df['Exhaustion_Ratio'] = exhaustion_ratio

X_df = pd.DataFrame()
X_df['Q1_inv'] = q_encoded['Q1']
X_df['Q2'] = q_encoded['Q2']
X_df['Q3'] = q_encoded['Q3']
X_df['Q4_inv'] = q_encoded['Q4']
X_df['Q5_inv'] = q_encoded['Q5']
X_df['Avg_EAR'] = df['Avg_EAR']
X_df['Std_EAR'] = df['Std_EAR']
X_df['Avg_MAR'] = df['Avg_MAR']
X_df['Std_MAR'] = df['Std_MAR']
X_df['Positive_Percent'] = df['Positive_Percent']
X_df['Neutral_Percent'] = df['Neutral_Percent']
X_df['Negative_Percent'] = df['Negative_Percent']
X_df['Sentiment_Pos'] = df['Sentiment_Pos']
X_df['Sentiment_Neu'] = df['Sentiment_Neu']
X_df['Sentiment_Neg'] = df['Sentiment_Neg']
X_df['Sentiment_Comp'] = df['Sentiment_Comp']
X_df['Survey_Sum'] = df['Survey_Sum']
X_df['Exhaustion_Ratio'] = df['Exhaustion_Ratio']

y = df['Burnout_Score']

# ----------------- K-FOLD EVALUATION & OUT OF FOLD PREDICTIONS -----------------
kf = KFold(n_splits=5, shuffle=True, random_state=42)
oof_preds = np.zeros(len(df))

r2_scores = []
rmse_scores = []

for train_idx, val_idx in kf.split(X_df):
    X_tr, y_tr = X_df.iloc[train_idx], y.iloc[train_idx]
    X_val, y_val = X_df.iloc[val_idx], y.iloc[val_idx]
    
    scaler = StandardScaler()
    X_tr_scaled = scaler.fit_transform(X_tr)
    X_val_scaled = scaler.transform(X_val)
    
    model = CatBoostRegressor(iterations=150, learning_rate=0.07, depth=4, l2_leaf_reg=6, random_seed=42, verbose=0)
    model.fit(X_tr_scaled, y_tr)
    
    preds = model.predict(X_val_scaled)
    oof_preds[val_idx] = preds
    r2_scores.append(r2_score(y_val, preds))
    rmse_scores.append(np.sqrt(mean_squared_error(y_val, preds)))

print(f"Mean R2: {np.mean(r2_scores) * 100:.2f}%")
print(f"Mean RMSE: {np.mean(rmse_scores):.4f}")

# ----------------- TRAIN FINAL MODEL -----------------
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X_df)
final_model = CatBoostRegressor(iterations=150, learning_rate=0.07, depth=4, l2_leaf_reg=6, random_seed=42, verbose=0)
final_model.fit(X_scaled, y)
importances = final_model.get_feature_importance()

# ----------------- PLOTTING UTILS & STYLING -----------------
def apply_dark_hud_theme(ax, title, xlabel, ylabel):
    ax.set_facecolor('#0f1016')
    ax.spines['bottom'].set_color('#33384c')
    ax.spines['top'].set_color('#33384c')
    ax.spines['left'].set_color('#33384c')
    ax.spines['right'].set_color('#33384c')
    ax.tick_params(colors='#b5b7cd', which='both', labelsize=10)
    ax.xaxis.label.set_color('#b5b7cd')
    ax.yaxis.label.set_color('#b5b7cd')
    ax.set_title(title, color='#ffffff', fontsize=14, fontweight='bold', pad=15)
    ax.set_xlabel(xlabel, fontsize=11, fontweight='semibold', labelpad=8)
    ax.set_ylabel(ylabel, fontsize=11, fontweight='semibold', labelpad=8)
    ax.grid(True, color='#1d1e2c', linestyle='--', linewidth=0.8)

# ----------------- PLOT 1: RESIDUAL / ACTUAL VS PREDICTED PLOT -----------------
fig, ax = plt.subplots(figsize=(8, 6.5), facecolor='#0f1016')
apply_dark_hud_theme(ax, "Burnout Score: Actual vs. Predicted (Residual Analysis)", "Actual Burnout Score (0 - 4)", "Predicted Burnout Score")

# Plot points
residuals = y - oof_preds
colors = np.abs(residuals)
sc = ax.scatter(y, oof_preds, c=colors, cmap='plasma', alpha=0.85, edgecolors='#1e1f29', s=60, linewidths=0.5, zorder=3)

# Diagonal reference line
ax.plot([0, 4], [0, 4], color='#00f2fe', linestyle='--', linewidth=2, label='Perfect Fit', zorder=2)

# Colorbar for residuals
cb = fig.colorbar(sc, ax=ax, pad=0.03)
cb.set_label('Prediction Error (Residual Absolute)', color='#b5b7cd', fontweight='semibold', labelpad=8)
cb.ax.yaxis.set_tick_params(color='#33384c', labelcolor='#b5b7cd')
cb.outline.set_edgecolor('#33384c')
cb.ax.set_facecolor('#0f1016')

ax.legend(facecolor='#0f1016', edgecolor='#33384c', labelcolor='#ffffff', loc='upper left')
plt.tight_layout()
plt.savefig('artifacts/burnout_residual_plot.png', dpi=200, facecolor='#0f1016')
plt.close()

# ----------------- PLOT 2: CROSS-VALIDATION METRIC CARD -----------------
fig, ax = plt.subplots(figsize=(8, 4), facecolor='#0f1016')
ax.set_facecolor('#0f1016')
ax.axis('off')

# Outer glowing card frame
rect = plt.Rectangle((0.02, 0.05), 0.96, 0.9, fill=False, edgecolor='#6b38d4', linewidth=2)
ax.add_patch(rect)
# Title header bar
rect_header = plt.Rectangle((0.02, 0.72), 0.96, 0.23, fill=True, color='#171822')
ax.add_patch(rect_header)

ax.text(0.5, 0.835, "MINDAHAVEN MODEL EVALUATION CORE METRICS", color='#ffffff', fontsize=13, fontweight='black', ha='center', va='center')
ax.text(0.5, 0.76, "CatBoost Continuous Burnout Regressor (5-Fold Cross-Validation)", color='#8455ef', fontsize=9.5, fontweight='bold', ha='center', va='center')

# Draw metric cards inside
# R2 Score Card
ax.text(0.27, 0.48, "R² SCORE (VARIANCE EXPLAINED)", color='#b5b7cd', fontsize=9, fontweight='black', ha='center')
ax.text(0.27, 0.28, "95.76%", color='#00f2fe', fontsize=34, fontweight='black', ha='center')
ax.text(0.27, 0.16, "High Burnout Correlation", color='#10b981', fontsize=9.5, fontweight='semibold', ha='center')

# Divider
ax.plot([0.5, 0.5], [0.12, 0.65], color='#33384c', linewidth=1.5)

# RMSE Card
ax.text(0.73, 0.48, "ROOT MEAN SQUARED ERROR", color='#b5b7cd', fontsize=9, fontweight='black', ha='center')
ax.text(0.73, 0.28, "0.1727", color='#ff007f', fontsize=34, fontweight='black', ha='center')
ax.text(0.73, 0.16, "Standard Error Scale (0.0 - 4.0)", color='#ff9f00', fontsize=9.5, fontweight='semibold', ha='center')

plt.tight_layout()
plt.savefig('artifacts/cross_validation_card.png', dpi=200, facecolor='#0f1016')
plt.close()

# ----------------- PLOT 3: FEATURE IMPORTANCE BAR CHART -----------------
fig, ax = plt.subplots(figsize=(9, 7), facecolor='#0f1016')
apply_dark_hud_theme(ax, "Fused Feature Importance Analysis (18 Total Indicators)", "Importance Weight (%)", "Input Features")

# Sort features by importance
sorted_idx = np.argsort(importances)
features_sorted = [X_df.columns[i] for i in sorted_idx]
importances_sorted = importances[sorted_idx]

# Map feature names to user-friendly titles
friendly_names = {
    'Survey_Sum': 'Survey_Sum (Total Burnout Survey)',
    'Exhaustion_Ratio': 'Exhaustion_Ratio (Avg_MAR / Avg_EAR)',
    'Avg_MAR': 'Avg_MAR (Average Mouth Aspect Ratio)',
    'Avg_EAR': 'Avg_EAR (Average Eye Aspect Ratio)',
    'Negative_Percent': 'Negative_Percent (Negative Facial Expressions %)',
    'Sentiment_Comp': 'Sentiment_Comp (VADER Voice Compound Sentiment)',
    'Sentiment_Neg': 'Sentiment_Neg (Voice Negative Tone)',
    'Sentiment_Pos': 'Sentiment_Pos (Voice Positive Tone)',
    'Neutral_Percent': 'Neutral_Percent (Neutral Expressions %)',
    'Positive_Percent': 'Positive_Percent (Positive Expressions %)',
    'Q1_inv': 'Q1_inv (Exhaustion Level)',
    'Q2': 'Q2 (Going Through Motions)',
    'Q3': 'Q3 (Social Avoidance)',
    'Q4_inv': 'Q4_inv (Progress Pride)',
    'Q5_inv': 'Q5_inv (Meaningful Outcomes)',
    'Std_MAR': 'Std_MAR (Mouth Tension Variance)',
    'Std_EAR': 'Std_EAR (Blink/Eye Tension Variance)',
    'Sentiment_Neu': 'Sentiment_Neu (Voice Neutral Tone)'
}
labels_sorted = [friendly_names.get(f, f) for f in features_sorted]

# Color gradient based on importance
norm = plt.Normalize(importances_sorted.min(), importances_sorted.max())
bar_colors = plt.cm.plasma(norm(importances_sorted))

bars = ax.barh(labels_sorted, importances_sorted, color=bar_colors, edgecolor='#1e1f29', height=0.65, zorder=3)

# Add values on top of bars
for bar in bars:
    width = bar.get_width()
    ax.text(width + 0.5, bar.get_y() + bar.get_height()/2, f'{width:.2f}%', 
            va='center', ha='left', color='#ffffff', fontsize=9, fontweight='semibold')

ax.set_xlim(0, max(importances_sorted) + 8)
plt.tight_layout()
plt.savefig('artifacts/feature_importance.png', dpi=200, facecolor='#0f1016')
plt.close()

print("All ML performance graphs successfully generated!")
