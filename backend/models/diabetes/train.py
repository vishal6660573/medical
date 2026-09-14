import os
from pathlib import Path
import pandas as pd
import numpy as np
import joblib
from sklearn.model_selection import train_test_split, StratifiedKFold, GridSearchCV
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score,
    f1_score, roc_auc_score, classification_report
)

def find_dataset() -> Path:
    candidates = [
        Path(__file__).resolve().parent.parent.parent.parent / "data" / "diabetes.csv",
        Path(__file__).resolve().parent.parent.parent / "data" / "diabetes.csv",
        Path("data/diabetes.csv"),
        Path("../../data/diabetes.csv"),
    ]
    for p in candidates:
        if p.exists():
            return p
    raise FileNotFoundError("diabetes.csv not found in candidate paths")

def main():
    print("=" * 65)
    print("Diabetes Risk Prediction Pipeline — Training & Hyperparameter Tuning")
    print("=" * 65)

    data_path = find_dataset()
    print(f"Loading dataset from: {data_path}")
    data = pd.read_csv(data_path)

    X = data.drop("Outcome", axis=1)
    y = data["Outcome"]

    # Preprocessing: Replace biological impossible zeros with median
    cols_with_zero = ["Glucose", "BloodPressure", "SkinThickness", "Insulin", "BMI"]
    for col in cols_with_zero:
        median_val = X[col][X[col] != 0].median()
        X[col] = X[col].replace(0, median_val)

    # Train / Test split with stratification
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # Fit Scaler on training data only
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    # 1. Baseline Logistic Regression
    baseline_lr = LogisticRegression(random_state=42, max_iter=1000)
    baseline_lr.fit(X_train_scaled, y_train)
    y_pred_base = baseline_lr.predict(X_test_scaled)
    y_prob_base = baseline_lr.predict_proba(X_test_scaled)[:, 1]

    base_acc = accuracy_score(y_test, y_pred_base)
    base_auc = roc_auc_score(y_test, y_prob_base)
    print(f"\n[Baseline Logistic Regression] Test Accuracy: {base_acc:.4f} | ROC-AUC: {base_auc:.4f}")

    # 2. Hyperparameter Tuning via GridSearchCV
    print("\n[Hyperparameter Tuning] Running GridSearchCV on Logistic Regression & Random Forest...")
    
    # Grid for Logistic Regression
    lr_param_grid = {
        "C": [0.01, 0.05, 0.1, 0.5, 1.0, 5.0, 10.0],
        "penalty": ["l2"],
        "solver": ["lbfgs", "liblinear"]
    }
    grid_lr = GridSearchCV(
        LogisticRegression(random_state=42, max_iter=1000),
        param_grid=lr_param_grid,
        cv=skf,
        scoring="roc_auc",
        n_jobs=-1
    )
    grid_lr.fit(X_train_scaled, y_train)
    best_lr = grid_lr.best_estimator_

    # Grid for Random Forest
    rf_param_grid = {
        "n_estimators": [100, 200],
        "max_depth": [4, 6, 8, None],
        "min_samples_split": [2, 5],
        "min_samples_leaf": [1, 2]
    }
    grid_rf = GridSearchCV(
        RandomForestClassifier(random_state=42),
        param_grid=rf_param_grid,
        cv=skf,
        scoring="roc_auc",
        n_jobs=-1
    )
    grid_rf.fit(X_train, y_train)
    best_rf = grid_rf.best_estimator_

    print(f"  Best LR Params: {grid_lr.best_params_} (CV ROC-AUC: {grid_lr.best_score_:.4f})")
    print(f"  Best RF Params: {grid_rf.best_params_} (CV ROC-AUC: {grid_rf.best_score_:.4f})")

    # Evaluate Tuned LR on Untouched Test Set
    y_pred_tuned = best_lr.predict(X_test_scaled)
    y_prob_tuned = best_lr.predict_proba(X_test_scaled)[:, 1]

    tuned_acc = accuracy_score(y_test, y_pred_tuned)
    tuned_prec = precision_score(y_test, y_pred_tuned)
    tuned_rec = recall_score(y_test, y_pred_tuned)
    tuned_f1 = f1_score(y_test, y_pred_tuned)
    tuned_auc = roc_auc_score(y_test, y_prob_tuned)

    print("\n" + "=" * 45)
    print("FINAL MODEL EVALUATION (Tuned Logistic Regression):")
    print("=" * 45)
    print(f"Accuracy:  {tuned_acc:.4f} (Baseline: {base_acc:.4f})")
    print(f"Precision: {tuned_prec:.4f}")
    print(f"Recall:    {tuned_rec:.4f}")
    print(f"F1 Score:  {tuned_f1:.4f}")
    print(f"ROC-AUC:   {tuned_auc:.4f} (Baseline: {base_auc:.4f})")
    print("\nClassification Report:\n", classification_report(y_test, y_pred_tuned))

    # Save artifacts in backend/models/diabetes
    save_dir = Path(__file__).resolve().parent
    model_save_path = save_dir / "model.pkl"
    scaler_save_path = save_dir / "scaler.pkl"

    joblib.dump(best_lr, model_save_path)
    joblib.dump(scaler, scaler_save_path)
    print(f"\nSaved tuned model to:  {model_save_path}")
    print(f"Saved fitted scaler to: {scaler_save_path}")

if __name__ == "__main__":
    main()
