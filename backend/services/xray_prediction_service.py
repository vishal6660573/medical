import json
import os
from pathlib import Path
import numpy as np
from PIL import Image
import tensorflow as tf
from app.core.logs import logger

# Project root path resolution
PROJECT_ROOT = Path(__file__).resolve().parents[2]
MODEL_PATH = PROJECT_ROOT / "ml" / "artifacts" / "chest_xray" / "model.h5"
LABELS_PATH = PROJECT_ROOT / "ml" / "artifacts" / "chest_xray" / "labels.json"
IMG_SIZE = 224

# TF 2.15 + Keras 2.15 — use tf.keras directly
# The .h5 model was trained with Keras 2.x so this is the compatible loader
model = tf.keras.models.load_model(str(MODEL_PATH))

# Load class labels — reverse map {index: label}
with open(LABELS_PATH, "r") as f:
    class_indices = json.load(f)
labels = {v: k for k, v in class_indices.items()}


def preprocess_image(image: Image.Image) -> np.ndarray:
    image = image.resize((IMG_SIZE, IMG_SIZE)).convert("RGB")
    arr = np.array(image, dtype=np.float32) / 255.0
    return np.expand_dims(arr, axis=0)


def predict_xray(image: Image.Image) -> dict:
    try:
        logger.info("X-ray prediction request received")
        img = preprocess_image(image)
        preds = model.predict(img)[0]
        class_id = int(np.argmax(preds))
        confidence = float(preds[class_id])
        disease = labels[class_id]
        logger.info(f"X-ray prediction: {disease} | Confidence: {confidence:.2f}")
        return {
            "disease": disease,
            "confidence": round(confidence, 2),
            "probability": round(confidence, 2),
            "risk_level": "Low" if disease == "NORMAL" else "High",
        }
    except Exception as e:
        logger.error(f"X-ray prediction failed: {str(e)}")
        raise
