import easyocr
import numpy as np
from PIL import Image
import io
from pdf2image import convert_from_bytes
import os
from app.core.logs import logger

# Path to Poppler (Windows fallback or standard PATH in Linux/Docker)
DEFAULT_POPPLER_PATH = r"C:\poppler-25.12.0\Library\bin"
POPPLER_PATH = DEFAULT_POPPLER_PATH if os.path.exists(DEFAULT_POPPLER_PATH) else None

# Initialize OCR reader
reader = easyocr.Reader(['en'])

def extract_text_from_image(image: Image.Image):
    """
    Extract text from a PIL image using EasyOCR
    """
    img = np.array(image)
    results = reader.readtext(img)
    text = " ".join([res[1] for res in results])
    return text

def extract_text(file_bytes: bytes, filename: str):
    """
    Extract text from uploaded PDF or image file
    """
    try:
        logger.info("OCR extraction started")

        if filename.lower().endswith(".pdf"):
            # Convert PDF pages to images using Poppler
            images = convert_from_bytes(file_bytes, poppler_path=POPPLER_PATH)
            full_text = ""

            for img in images:
                full_text += extract_text_from_image(img) + " "

        else:
            # Image file (jpg/png)
            image = Image.open(io.BytesIO(file_bytes)).convert("RGB")
            full_text = extract_text_from_image(image)

        logger.info("OCR extraction completed successfully")
        return full_text

    except Exception as e:
        logger.error(f"OCR failed: {str(e)}")
        raise
