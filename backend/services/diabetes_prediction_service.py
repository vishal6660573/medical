import os
from pathlib import Path
import joblib
import pandas as pd
from app.core.logs import logger

BASE_DIR = Path(__file__).resolve().parent.parent

MODEL_PATH = BASE_DIR / "models" / "diabetes" / "model.pkl"
SCALER_PATH = BASE_DIR / "models" / "diabetes" / "scaler.pkl"

# Load trained artifacts
model = joblib.load(MODEL_PATH)
scaler = joblib.load(SCALER_PATH)

FEATURE_COLUMNS = [
    "Pregnancies",
    "Glucose",
    "BloodPressure",
    "SkinThickness",
    "Insulin",
    "BMI",
    "DiabetesPedigreeFunction",
    "Age"
]

def predict_diabetes(data):
    try:
        logger.info("Received diabetes prediction request")

        df_input = pd.DataFrame([[
            data.pregnancies,
            data.glucose,
            data.blood_pressure,
            data.skin_thickness,
            data.insulin,
            data.bmi,
            data.diabetes_pedigree_function,
            data.age
        ]], columns=FEATURE_COLUMNS)

        # Apply scaling
        features_scaled = scaler.transform(df_input)

        # Predict probability
        probability = model.predict_proba(features_scaled)[0][1]

        logger.info(f"Prediction successful | Probability={probability:.4f}")

        return {
            "probability": round(float(probability), 2),
            "risk_level": "High" if probability >= 0.6 else "Low"
        }

    except Exception as e:
        logger.error(f"Diabetes prediction failed: {str(e)}")
        raise
