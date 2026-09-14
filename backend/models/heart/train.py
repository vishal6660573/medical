import os
from pathlib import Path
import pandas as pd
import numpy as np
import joblib
from sklearn.model_selection import train_test_split, StratifiedKFold, GridSearchCV
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score,
    f1_score, roc_auc_score, classification_report
)

def find_dataset() -> Path:
    candidates = [
        Path(__file__).resolve().parent.parent.parent.parent / "data" / "heart.csv",
        Path(__file__).resolve().parent.parent.parent / "data" / "heart.csv",
        Path("data/heart.csv"),
        Path("../../data/heart.csv"),
    ]
    for p in candidates:
        if p.exists():
            return p
    raise FileNotFoundError("heart.csv not found in candidate paths")

def main():
    print("=" * 65)
    print("Heart Disease Prediction Pipeline — Training & Hyperparameter Tuning")
    print("=" * 65)

    data_path = find_dataset()
    print(f"Loading dataset from: {data_path}")
    data = pd.read_csv(data_path)

    # 1. Cleaning & Preprocessing
    if "id" in data.columns:
        data = data.drop(columns=["id"])
    if "dataset" in data.columns:
        data = data.drop(columns=["dataset"])

    # Convert target to binary (0 = no disease, >=1 = disease present)
    data["num"] = data["num"].apply(lambda x: 1 if x > 0 else 0)

    # Encode categorical columns
    categorical_cols = data.select_dtypes(include=["object", "bool"]).columns
    for col in categorical_cols:
        data[col] = data[col].astype("category").cat.codes

    # Handle missing values via column medians
    data = data.fillna(data.median())

    X = data.drop("num", axis=1)
    y = data["num"]

    # 2. Stratified Train / Test Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    # 3. Baseline Random Forest
    baseline_rf = RandomForestClassifier(n_estimators=100, random_state=42)
    baseline_rf.fit(X_train, y_train)
    y_pred_base = baseline_rf.predict(X_test)
    y_prob_base = baseline_rf.predict_proba(X_test)[:, 1]

    base_acc = accuracy_score(y_test, y_pred_base)
    base_auc = roc_auc_score(y_test, y_prob_base)
    print(f"\n[Baseline Random Forest] Test Accuracy: {base_acc:.4f} | ROC-AUC: {base_auc:.4f}")

    # 4. Hyperparameter Tuning via GridSearchCV
    print("\n[Hyperparameter Tuning] Running GridSearchCV on Random Forest & Gradient Boosting...")

    rf_param_grid = {
        "n_estimators": [100, 200],
        "max_depth": [4, 6, 8, None],
        "min_samples_split": [2, 5],
        "min_samples_leaf": [1, 2],
        "max_features": ["sqrt", "log2"]
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

    gb_param_grid = {
        "n_estimators": [100, 150],
        "learning_rate": [0.05, 0.1],
        "max_depth": [3, 4]
    }
    grid_gb = GridSearchCV(
        GradientBoostingClassifier(random_state=42),
        param_grid=gb_param_grid,
        cv=skf,
        scoring="roc_auc",
        n_jobs=-1
    )
    grid_gb.fit(X_train, y_train)
    best_gb = grid_gb.best_estimator_

    print(f"  Best RF Params: {grid_rf.best_params_} (CV ROC-AUC: {grid_rf.best_score_:.4f})")
    print(f"  Best GB Params: {grid_gb.best_params_} (CV ROC-AUC: {grid_gb.best_score_:.4f})")

    # Select best candidate
    if grid_rf.best_score_ >= grid_gb.best_score_:
        best_model = best_rf
        best_name = "Random Forest"
    else:
        best_model = best_gb
        best_name = "Gradient Boosting"

    # Evaluate Best Model on Untouched Test Set
    y_pred_tuned = best_model.predict(X_test)
    y_prob_tuned = best_model.predict_proba(X_test)[:, 1]

    tuned_acc = accuracy_score(y_test, y_pred_tuned)
    tuned_prec = precision_score(y_test, y_pred_tuned)
    tuned_rec = recall_score(y_test, y_pred_tuned)
    tuned_f1 = f1_score(y_test, y_pred_tuned)
    tuned_auc = roc_auc_score(y_test, y_prob_tuned)

    print("\n" + "=" * 45)
    print(f"FINAL MODEL EVALUATION (Tuned {best_name}):")
    print("=" * 45)
    print(f"Accuracy:  {tuned_acc:.4f} (Baseline: {base_acc:.4f})")
    print(f"Precision: {tuned_prec:.4f}")
    print(f"Recall:    {tuned_rec:.4f}")
    print(f"F1 Score:  {tuned_f1:.4f}")
    print(f"ROC-AUC:   {tuned_auc:.4f} (Baseline: {base_auc:.4f})")
    print("\nClassification Report:\n", classification_report(y_test, y_pred_tuned))

    # Save artifacts in backend/models/heart
    save_dir = Path(__file__).resolve().parent
    model_save_path = save_dir / "model.pkl"

    joblib.dump(best_model, model_save_path)
    print(f"\nSaved tuned {best_name} model to: {model_save_path}")

if __name__ == "__main__":
    main()
