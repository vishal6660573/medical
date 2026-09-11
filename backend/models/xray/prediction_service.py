import os
import numpy as np
import json
from PIL import Image
from app.core.logs import logger

BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH  = os.path.join(BASE_DIR, "model.h5")
LABELS_PATH = os.path.join(BASE_DIR, "labels.json")
IMG_SIZE    = 224

# TF 2.15 + Keras 2.15 — use tf.keras directly
# The .h5 model was trained with Keras 2.x so this is the only compatible loader
import tensorflow as tf
model = tf.keras.models.load_model(MODEL_PATH)

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
        class_id   = int(np.argmax(preds))
        confidence = float(preds[class_id])
        disease    = labels[class_id]
        logger.info(f"X-ray prediction: {disease} | Confidence: {confidence:.2f}")
        return {
            "disease":     disease,
            "confidence":  round(confidence, 2),
            "probability": round(confidence, 2),
            "risk_level":  "Low" if disease == "NORMAL" else "High",
        }
    except Exception as e:
        logger.error(f"X-ray prediction failed: {str(e)}")
        raise
