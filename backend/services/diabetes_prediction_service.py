import os
import joblib
import numpy as np
from app.core.logs import logger

# Get absolute path to app directory
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

MODEL_PATH = os.path.join(
    BASE_DIR,
    "models",
    "diabetes",
    "model.pkl"
)

SCALER_PATH = os.path.join(
    BASE_DIR,
    "models",
    "diabetes",
    "scaler.pkl"
)

# Load model and scaler
model = joblib.load(MODEL_PATH)
scaler = joblib.load(SCALER_PATH)


def predict_diabetes(data):
    try:
        logger.info("Received diabetes prediction request")

        # Arrange features in SAME order as training
        features = np.array([[
            data.pregnancies,
            data.glucose,
            data.blood_pressure,
            data.skin_thickness,
            data.insulin,
            data.bmi,
            data.diabetes_pedigree_function,
            data.age
        ]])

        # Apply scaling
        features_scaled = scaler.transform(features)

        # Predict probability
        probability = model.predict_proba(features_scaled)[0][1]

        logger.info(f"Prediction successful | Probability={probability}")

        return {
            "probability": round(float(probability), 2),
            "risk_level": "High" if probability >= 0.6 else "Low"
        }

    except Exception as e:
        logger.error(f"Diabetes prediction failed: {str(e)}")
        raise
