import os
from pathlib import Path
import joblib
import pandas as pd
from app.core.logs import logger

PROJECT_ROOT = Path(__file__).resolve().parents[2]

MODEL_PATH = PROJECT_ROOT / "ml" / "artifacts" / "heart_disease" / "model.pkl"

# Load trained model
model = joblib.load(MODEL_PATH)

FEATURE_COLUMNS = [
    "age", "sex", "cp", "trestbps", "chol", "fbs",
    "restecg", "thalach", "exang", "oldpeak", "slope", "ca", "thal"
]

def predict_heart_disease(data):
    """
    Predict heart disease risk using tuned Random Forest model
    """
    try:
        logger.info("Heart disease prediction request received")

        df_input = pd.DataFrame([[
            data.age,
            data.sex,
            data.cp,
            data.trestbps,
            data.chol,
            data.fbs,
            data.restecg,
            data.thalach,
            data.exang,
            data.oldpeak,
            data.slope,
            data.ca,
            data.thal
        ]], columns=FEATURE_COLUMNS)

        # Predict probability
        probability = model.predict_proba(df_input)[0][1]

        logger.info(f"Heart disease prediction successful | Probability={probability:.4f}")

        return {
            "probability": round(float(probability), 2),
            "risk_level": "High" if probability >= 0.6 else "Low"
        }

    except Exception as e:
        logger.error(f"Heart disease prediction failed: {str(e)}")
        raise
