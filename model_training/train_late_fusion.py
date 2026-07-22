"""
Late Fusion Model for Burnout Prediction.

This script implements a late fusion architecture:
1. Sub-model Q: Trained only on Questionnaire features.
2. Sub-model B: Trained only on Biometric (Facial + Vocal) features.
3. Meta-Model: Combined predictions using a Linear Regression meta-model (Stacking).

We evaluate the system using 5-Fold Cross-Validation, reporting R2 and RMSE,
and test the model on two custom experimental inputs to verify that biometrics
successfully shift the score when questionnaire responses are held constant.
"""

import os
import pandas as pd
import numpy as np
import joblib
import warnings
from sklearn.model_selection import KFold
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score
from catboost import CatBoostRegressor

# Ignore user warnings for feature names
warnings.filterwarnings('ignore', category=UserWarning)

# Load and preprocess data (same logic as main backend and ablation studies)
def load_and_preprocess_data(csv_path='model_training/data.csv'):
    if not os.path.exists(csv_path) and os.path.exists('data.csv'):
        csv_path = 'data.csv'

    df = pd.read_csv(csv_path)

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

    # Feature definitions
    X_df = pd.DataFrame()
    X_df['Q1_inv'] = q_encoded['Q1']
    X_df['Q2'] = q_encoded['Q2']
    X_df['Q3'] = q_encoded['Q3']
    X_df['Q4_inv'] = q_encoded['Q4']
    X_df['Q5_inv'] = q_encoded['Q5']
    X_df['Survey_Sum'] = df['Survey_Sum']

    X_df['Avg_EAR'] = df['Avg_EAR']
    X_df['Std_EAR'] = df['Std_EAR']
    X_df['Avg_MAR'] = df['Avg_MAR']
    X_df['Std_MAR'] = df['Std_MAR']
    X_df['Exhaustion_Ratio'] = df['Exhaustion_Ratio']

    X_df['Positive_Percent'] = df['Positive_Percent']
    X_df['Neutral_Percent'] = df['Neutral_Percent']
    X_df['Negative_Percent'] = df['Negative_Percent']
    X_df['Sentiment_Pos'] = df['Sentiment_Pos']
    X_df['Sentiment_Neu'] = df['Sentiment_Neu']
    X_df['Sentiment_Neg'] = df['Sentiment_Neg']
    X_df['Sentiment_Comp'] = df['Sentiment_Comp']

    y = df['Burnout_Score']
    return X_df, y

def train_and_eval_late_fusion():
    X_df, y = load_and_preprocess_data()

    # Column definitions
    q_cols = ['Q1_inv', 'Q2', 'Q3', 'Q4_inv', 'Q5_inv', 'Survey_Sum']
    b_cols = [
        'Avg_EAR', 'Std_EAR', 'Avg_MAR', 'Std_MAR', 'Exhaustion_Ratio',
        'Positive_Percent', 'Neutral_Percent', 'Negative_Percent',
        'Sentiment_Pos', 'Sentiment_Neu', 'Sentiment_Neg', 'Sentiment_Comp'
    ]

    kf = KFold(n_splits=5, shuffle=True, random_state=42)
    
    # Store out-of-fold predictions
    oof_preds_q = np.zeros(len(X_df))
    oof_preds_b = np.zeros(len(X_df))
    oof_preds_fused = np.zeros(len(X_df))

    # We will hold all evaluation metrics per fold
    rmse_q_folds = []
    rmse_b_folds = []
    rmse_fused_folds = []
    
    r2_q_folds = []
    r2_b_folds = []
    r2_fused_folds = []

    for train_idx, val_idx in kf.split(X_df):
        # Split Data
        X_train, y_train = X_df.iloc[train_idx], y.iloc[train_idx]
        X_val, y_val = X_df.iloc[val_idx], y.iloc[val_idx]

        # Scalers
        scaler_q = StandardScaler()
        scaler_b = StandardScaler()

        X_tr_q_scaled = scaler_q.fit_transform(X_train[q_cols])
        X_val_q_scaled = scaler_q.transform(X_val[q_cols])

        X_tr_b_scaled = scaler_b.fit_transform(X_train[b_cols])
        X_val_b_scaled = scaler_b.transform(X_val[b_cols])

        # Sub-models
        model_q = CatBoostRegressor(iterations=150, learning_rate=0.07, depth=4, l2_leaf_reg=6, random_seed=42, verbose=0)
        model_b = CatBoostRegressor(iterations=150, learning_rate=0.07, depth=4, l2_leaf_reg=6, random_seed=42, verbose=0)

        # Fit Sub-models
        model_q.fit(X_tr_q_scaled, y_train)
        model_b.fit(X_tr_b_scaled, y_train)

        # OOF Predictions on Validation set
        preds_q = model_q.predict(X_val_q_scaled)
        preds_b = model_b.predict(X_val_b_scaled)
        
        oof_preds_q[val_idx] = preds_q
        oof_preds_b[val_idx] = preds_b

        # Train a meta-regressor on the training set OOF predictions to blend them
        train_preds_q = model_q.predict(X_tr_q_scaled)
        train_preds_b = model_b.predict(X_tr_b_scaled)
        X_meta_tr = np.column_stack((train_preds_q, train_preds_b))
        
        meta_model = LinearRegression(fit_intercept=True)
        meta_model.fit(X_meta_tr, y_train)

        # Predict validation set
        X_meta_val = np.column_stack((preds_q, preds_b))
        preds_fused = meta_model.predict(X_meta_val)
        oof_preds_fused[val_idx] = preds_fused

        # Calculate fold metrics
        rmse_q_folds.append(np.sqrt(mean_squared_error(y_val, preds_q)))
        rmse_b_folds.append(np.sqrt(mean_squared_error(y_val, preds_b)))
        rmse_fused_folds.append(np.sqrt(mean_squared_error(y_val, preds_fused)))

        r2_q_folds.append(r2_score(y_val, preds_q))
        r2_b_folds.append(r2_score(y_val, preds_b))
        r2_fused_folds.append(r2_score(y_val, preds_fused))

    print("=" * 80)
    print("                      LATE FUSION MODEL CV METRICS")
    print("=" * 80)
    print(f"Sub-model Q (Questionnaire Only)  | Mean R2: {np.mean(r2_q_folds)*100:.2f}% | Mean RMSE: {np.mean(rmse_q_folds):.4f}")
    print(f"Sub-model B (Biometrics Only)     | Mean R2: {np.mean(r2_b_folds)*100:.2f}% | Mean RMSE: {np.mean(rmse_b_folds):.4f}")
    print(f"Late Fusion Model (Fused Blended) | Mean R2: {np.mean(r2_fused_folds)*100:.2f}% | Mean RMSE: {np.mean(rmse_fused_folds):.4f}")
    print("=" * 80)

    # Train final production models on full dataset
    scaler_q_full = StandardScaler()
    scaler_b_full = StandardScaler()
    
    X_q_full_scaled = scaler_q_full.fit_transform(X_df[q_cols])
    X_b_full_scaled = scaler_b_full.fit_transform(X_df[b_cols])

    # Convert scaled outputs back to DataFrame to preserve feature names for scikit-learn
    X_q_full_scaled_df = pd.DataFrame(X_q_full_scaled, columns=q_cols)
    X_b_full_scaled_df = pd.DataFrame(X_b_full_scaled, columns=b_cols)

    final_model_q = CatBoostRegressor(iterations=150, learning_rate=0.07, depth=4, l2_leaf_reg=6, random_seed=42, verbose=0)
    final_model_b = CatBoostRegressor(iterations=150, learning_rate=0.07, depth=4, l2_leaf_reg=6, random_seed=42, verbose=0)

    final_model_q.fit(X_q_full_scaled_df, y)
    final_model_b.fit(X_b_full_scaled_df, y)

    # Blend meta-model on full predictions
    full_preds_q = final_model_q.predict(X_q_full_scaled_df)
    full_preds_b = final_model_b.predict(X_b_full_scaled_df)
    X_meta_full = np.column_stack((full_preds_q, full_preds_b))
    
    final_meta = LinearRegression(fit_intercept=True)
    final_meta.fit(X_meta_full, y)
    
    print(f"Meta-model weights: Q_weight = {final_meta.coef_[0]:.3f}, B_weight = {final_meta.coef_[1]:.3f}, Intercept = {final_meta.intercept_:.3f}")

    # Save to backend/ and model_training/regression_output/
    backend_dir = 'backend' if os.path.exists('backend') else '../backend'
    reg_output_dir = 'model_training/regression_output' if os.path.exists('model_training/regression_output') else 'regression_output'

    for out_dir in [backend_dir, reg_output_dir]:
        if os.path.exists(out_dir):
            joblib.dump(final_model_q, os.path.join(out_dir, 'model_q.joblib'))
            joblib.dump(final_model_b, os.path.join(out_dir, 'model_b.joblib'))
            joblib.dump(final_meta, os.path.join(out_dir, 'model_meta.joblib'))
            joblib.dump(scaler_q_full, os.path.join(out_dir, 'scaler_q.joblib'))
            joblib.dump(scaler_b_full, os.path.join(out_dir, 'scaler_b.joblib'))
            print(f"Saved late fusion models & scalers to: {out_dir}")

    return final_model_q, final_model_b, final_meta, scaler_q_full, scaler_b_full, q_cols, b_cols

def test_on_experiments(model_q, model_b, meta, scaler_q, scaler_b, q_cols, b_cols):
    # Questionnaire answers: Constant moderate answers ("Sometimes")
    q_vals = [2, 2, 2, 2, 2, 10.0] 

    # EXP 1: Very positive facial + vocal
    exp1_bio = [
        0.31, 0.02, # Avg_EAR, Std_EAR
        0.02, 0.01, # Avg_MAR, Std_MAR
        0.02 / (0.31 + 1e-5), # Exhaustion_Ratio
        85.0, 15.0, 0.0, # Positive_Percent, Neutral_Percent, Negative_Percent
        0.80, 0.20, 0.00, 0.90 # Sentiment_Pos, Sentiment_Neu, Sentiment_Neg, Sentiment_Comp
    ]

    # EXP 2: Very negative facial + vocal
    exp2_bio = [
        0.24, 0.04, # Avg_EAR, Std_EAR
        0.08, 0.03, # Avg_MAR, Std_MAR
        0.08 / (0.24 + 1e-5), # Exhaustion_Ratio
        0.0, 30.0, 70.0, # Positive_Percent, Neutral_Percent, Negative_Percent
        0.00, 0.30, 0.70, -0.75 # Sentiment_Pos, Sentiment_Neu, Sentiment_Neg, Sentiment_Comp
    ]

    # Scale inputs using DataFrames with feature names to suppress warnings
    exp1_q_df = pd.DataFrame([q_vals], columns=q_cols)
    exp2_q_df = pd.DataFrame([q_vals], columns=q_cols)
    exp1_b_df = pd.DataFrame([exp1_bio], columns=b_cols)
    exp2_b_df = pd.DataFrame([exp2_bio], columns=b_cols)

    exp1_q_scaled = pd.DataFrame(scaler_q.transform(exp1_q_df), columns=q_cols)
    exp2_q_scaled = pd.DataFrame(scaler_q.transform(exp2_q_df), columns=q_cols)
    exp1_b_scaled = pd.DataFrame(scaler_b.transform(exp1_b_df), columns=b_cols)
    exp2_b_scaled = pd.DataFrame(scaler_b.transform(exp2_b_df), columns=b_cols)

    # Sub-model predictions
    pred_q_exp1 = model_q.predict(exp1_q_scaled)[0]
    pred_q_exp2 = model_q.predict(exp2_q_scaled)[0]

    pred_b_exp1 = model_b.predict(exp1_b_scaled)[0]
    pred_b_exp2 = model_b.predict(exp2_b_scaled)[0]

    # Late Fusion Predictions
    fused_exp1 = meta.predict(np.column_stack((pred_q_exp1, pred_b_exp1)))[0]
    fused_exp2 = meta.predict(np.column_stack((pred_q_exp2, pred_b_exp2)))[0]

    fused_exp1_bounded = max(0.0, min(4.0, fused_exp1))
    fused_exp2_bounded = max(0.0, min(4.0, fused_exp2))

    print("\n" + "=" * 80)
    print("                      EXPERIMENTAL EVALUATION RESULTS")
    print("=" * 80)
    print(f"Setup: Both experiments use identical Questionnaire responses ('Sometimes' on all questions).")
    print(f"Target Scale: 0.0 (No Burnout) to 4.0 (Severe Burnout)\n")

    print(f"Experiment 1 (Positive Biometrics):")
    print(f"  -> Survey Sub-model Prediction: {pred_q_exp1:.4f}")
    print(f"  -> Biometric Sub-model Prediction: {pred_b_exp1:.4f}")
    print(f"  -> Final Fused Prediction (Late Fusion): {fused_exp1_bounded:.4f}")
    print()

    print(f"Experiment 2 (Negative Biometrics):")
    print(f"  -> Survey Sub-model Prediction: {pred_q_exp2:.4f}")
    print(f"  -> Biometric Sub-model Prediction: {pred_b_exp2:.4f}")
    print(f"  -> Final Fused Prediction (Late Fusion): {fused_exp2_bounded:.4f}")
    print("=" * 80)

    # Demonstrate how the single model would have predicted
    try:
        # Resolve path to single model output
        single_scaler_path = 'model_training/regression_output/scaler.joblib'
        single_model_path = 'model_training/regression_output/model.joblib'
        if not os.path.exists(single_scaler_path):
            single_scaler_path = 'regression_output/scaler.joblib'
            single_model_path = 'regression_output/model.joblib'

        single_scaler = joblib.load(single_scaler_path)
        single_model = joblib.load(single_model_path)
        
        # Combine Q and B features
        feat1 = q_vals + exp1_bio
        feat2 = q_vals + exp2_bio
        
        single_pred1 = single_model.predict(single_scaler.transform(np.array(feat1).reshape(1, -1)))[0]
        single_pred2 = single_model.predict(single_scaler.transform(np.array(feat2).reshape(1, -1)))[0]
        
        print("\n" + "=" * 80)
        print("                  COMPARISON WITH PREVIOUS SINGLE-MODEL")
        print("=" * 80)
        print(f"Experiment 1 (Positive) -> Single Model prediction: {max(0.0, min(4.0, single_pred1)):.4f}")
        print(f"Experiment 2 (Negative) -> Single Model prediction: {max(0.0, min(4.0, single_pred2)):.4f}")
        print(f"Difference in Single Model: {abs(single_pred1 - single_pred2):.4f}")
        print(f"Difference in Late Fusion:  {abs(fused_exp1_bounded - fused_exp2_bounded):.4f}")
        print("=" * 80)
    except Exception as e:
        print(f"Could not load single model comparison: {e}")

if __name__ == '__main__':
    mq, mb, meta, sq, sb, q_cols, b_cols = train_and_eval_late_fusion()
    test_on_experiments(mq, mb, meta, sq, sb, q_cols, b_cols)

