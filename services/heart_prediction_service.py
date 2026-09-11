import os
import joblib
import numpy as np
from app.core.logs import logger

# Get absolute path to project root
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

MODEL_PATH = os.path.join(
    BASE_DIR,
    "models",
    "heart",
    "model.pkl"
)

# Load trained model
model = joblib.load(MODEL_PATH)

def predict_heart_disease(data):
    """
    Predict heart disease risk using Random Forest model
    """

    try:
        logger.info("Heart disease prediction request received")

        # Convert input data to numpy array (same order as training)
        features = np.array([[
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
        ]])

        # Predict probability
        probability = model.predict_proba(features)[0][1]

        logger.info(f"Heart disease prediction successful | Probability={probability}")

        return {
            "probability": round(float(probability), 2),
            "risk_level": "High" if probability >= 0.6 else "Low"
        }

    except Exception as e:
        logger.error(f"Heart disease prediction failed: {str(e)}")
        raise
