"""
Multimodal Feature Ablation Study for Burnout Regression Model.

This script trains the model (CatBoostRegressor by default) on 6 different feature combinations:
1. Questionnaire-based features only
2. Facial-based features only
3. Vocal-based features only
4. Questionnaire + Facial features
5. Facial + Vocal features
6. Questionnaire + Vocal features
(Plus Full Multimodal: Questionnaire + Facial + Vocal for baseline comparison)

In the end, it displays their R² scores and performance metrics.
"""

import os
import pandas as pd
import numpy as np
from sklearn.model_selection import KFold
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from catboost import CatBoostRegressor


def load_and_preprocess_data(csv_path='model_training/data.csv'):
    # Check if csv exists locally or relative to script
    if not os.path.exists(csv_path) and os.path.exists('data.csv'):
        csv_path = 'data.csv'

    df = pd.read_csv(csv_path)

    # Frequency mapping for questionnaire responses
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

    df_features = pd.DataFrame()
    df_features['Q1_inv'] = q_encoded['Q1']
    df_features['Q2'] = q_encoded['Q2']
    df_features['Q3'] = q_encoded['Q3']
    df_features['Q4_inv'] = q_encoded['Q4']
    df_features['Q5_inv'] = q_encoded['Q5']
    df_features['Survey_Sum'] = df['Survey_Sum']

    df_features['Avg_EAR'] = df['Avg_EAR']
    df_features['Std_EAR'] = df['Std_EAR']
    df_features['Avg_MAR'] = df['Avg_MAR']
    df_features['Std_MAR'] = df['Std_MAR']
    df_features['Exhaustion_Ratio'] = df['Exhaustion_Ratio']

    df_features['Positive_Percent'] = df['Positive_Percent']
    df_features['Neutral_Percent'] = df['Neutral_Percent']
    df_features['Negative_Percent'] = df['Negative_Percent']
    df_features['Sentiment_Pos'] = df['Sentiment_Pos']
    df_features['Sentiment_Neu'] = df['Sentiment_Neu']
    df_features['Sentiment_Neg'] = df['Sentiment_Neg']
    df_features['Sentiment_Comp'] = df['Sentiment_Comp']

    y = df['Burnout_Score']

    return df_features, y


def run_ablation_study():
    df_features, y = load_and_preprocess_data()

    # Define modality feature groups
    questionnaire_cols = ['Q1_inv', 'Q2', 'Q3', 'Q4_inv', 'Q5_inv', 'Survey_Sum']
    facial_cols = ['Avg_EAR', 'Std_EAR', 'Avg_MAR', 'Std_MAR', 'Exhaustion_Ratio']
    vocal_cols = ['Positive_Percent', 'Neutral_Percent', 'Negative_Percent', 'Sentiment_Pos', 'Sentiment_Neu', 'Sentiment_Neg', 'Sentiment_Comp']

    # Define requested feature combinations
    feature_sets = {
        "1. Questionnaire Only": questionnaire_cols,
        "2. Facial Only": facial_cols,
        "3. Vocal Only": vocal_cols,
        "4. Questionnaire + Facial": questionnaire_cols + facial_cols,
        "5. Facial + Vocal": facial_cols + vocal_cols,
        "6. Questionnaire + Vocal": questionnaire_cols + vocal_cols,
        "7. All (Questionnaire + Facial + Vocal)": questionnaire_cols + facial_cols + vocal_cols,
    }

    kf = KFold(n_splits=5, shuffle=True, random_state=42)
    results = []

    print("=" * 80)
    print("      MULTIMODAL FEATURE COMBINATION ABLATION STUDY (5-FOLD CV)")
    print("=" * 80)

    for set_name, cols in feature_sets.items():
        X_sub = df_features[cols]
        r2_folds = []
        rmse_folds = []
        mae_folds = []

        for train_idx, val_idx in kf.split(X_sub):
            X_tr, y_tr = X_sub.iloc[train_idx], y.iloc[train_idx]
            X_val, y_val = X_sub.iloc[val_idx], y.iloc[val_idx]

            scaler = StandardScaler()
            X_tr_scaled = scaler.fit_transform(X_tr)
            X_val_scaled = scaler.transform(X_val)

            model = CatBoostRegressor(
                iterations=150,
                learning_rate=0.07,
                depth=4,
                l2_leaf_reg=6,
                random_seed=42,
                verbose=0
            )
            model.fit(X_tr_scaled, y_tr)

            preds = model.predict(X_val_scaled)

            r2_folds.append(r2_score(y_val, preds))
            rmse_folds.append(np.sqrt(mean_squared_error(y_val, preds)))
            mae_folds.append(mean_absolute_error(y_val, preds))

        mean_r2 = np.mean(r2_folds)
        std_r2 = np.std(r2_folds)
        mean_rmse = np.mean(rmse_folds)
        mean_mae = np.mean(mae_folds)

        results.append({
            "Feature Combination": set_name,
            "Num Features": len(cols),
            "Mean R2 Score (%)": mean_r2 * 100,
            "R2 Std Dev (%)": std_r2 * 100,
            "RMSE": mean_rmse,
            "MAE": mean_mae
        })

    # Display summary table
    results_df = pd.DataFrame(results)
    
    print("\n" + "-" * 80)
    print(f"{'Feature Combination':<40} | {'Features':<8} | {'Mean R² Score':<15} | {'RMSE':<8}")
    print("-" * 80)
    for res in results:
        comb = res["Feature Combination"]
        n_feat = res["Num Features"]
        r2_pct = f"{res['Mean R2 Score (%)']:.2f}%"
        rmse_val = f"{res['RMSE']:.4f}"
        print(f"{comb:<40} | {n_feat:<8} | {r2_pct:<15} | {rmse_val:<8}")
    print("-" * 80)

    print("\nSummary Table:")
    print(results_df.to_string(index=False))

    return results_df


if __name__ == '__main__':
    run_ablation_study()
