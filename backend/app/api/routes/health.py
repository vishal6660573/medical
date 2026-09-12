from fastapi import APIRouter, HTTPException, UploadFile, File, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from PIL import Image
import io

from app.core.logs import logger
from app.auth.dependencies import get_current_user
from app.database.database import get_db
from app.database.models import User, Patient, UserRole
from app.core.exceptions import NotFoundException, ForbiddenException

# Schemas
from schemas.patient import DiabetesInput
from schemas.heart import HeartInput

# ML Services
from services.diabetes_prediction_service import predict_diabetes
from services.heart_prediction_service import predict_heart_disease
from models.xray.prediction_service import predict_xray

# Phase 2 — DB save helper
from services.prediction_store import save_prediction

router = APIRouter(prefix="", tags=["Health & Prediction"])


# ─────────────────────────────────────────────
# Helper — resolve patient_id from request
# ─────────────────────────────────────────────

def _resolve_patient(
    patient_id: Optional[int],
    current_user: User,
    db: Session
) -> Optional[int]:
    """
    Doctors can pass any patient_id.
    Patients use their own profile automatically.
    Returns None if no patient profile found (prediction still runs, just not saved).
    """
    if current_user.role in (UserRole.doctor, UserRole.admin):
        if patient_id:
            patient = db.query(Patient).filter(Patient.id == patient_id).first()
            if not patient:
                raise NotFoundException(f"Patient {patient_id} not found")
            return patient.id
        return None  # doctor ran a test prediction without linking a patient

    # Patient role — always use own profile
    patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()
    return patient.id if patient else None


# ─────────────────────────────────────────────
# Health Check (public)
# ─────────────────────────────────────────────

@router.get("/health")
def health_check():
    logger.info("Health check endpoint accessed")
    return {"status": "healthy"}


# ─────────────────────────────────────────────
# Diabetes Prediction
# ─────────────────────────────────────────────

@router.post("/predict/diabetes")
def diabetes_prediction(
    data: DiabetesInput,
    patient_id: Optional[int] = Query(None, description="Patient ID to link result (doctors only)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        logger.info(f"Diabetes prediction request | user={current_user.id}")
        result = predict_diabetes(data)

        resolved_patient_id = _resolve_patient(patient_id, current_user, db)
        saved_id = None

        if resolved_patient_id:
            record = save_prediction(
                db=db,
                patient_id=resolved_patient_id,
                prediction_type="diabetes",
                result=result,
                input_data=data.model_dump()
            )
            saved_id = record.id

        return {
            **result,
            "saved": saved_id is not None,
            "prediction_record_id": saved_id,
            "patient_id": resolved_patient_id
        }

    except (NotFoundException, ForbiddenException):
        raise
    except Exception as e:
        logger.error(f"Diabetes prediction failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Diabetes prediction failed")


# ─────────────────────────────────────────────
# Heart Disease Prediction
# ─────────────────────────────────────────────

@router.post("/predict/heart")
def heart_prediction(
    data: HeartInput,
    patient_id: Optional[int] = Query(None, description="Patient ID to link result (doctors only)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        logger.info(f"Heart disease prediction request | user={current_user.id}")
        result = predict_heart_disease(data)

        resolved_patient_id = _resolve_patient(patient_id, current_user, db)
        saved_id = None

        if resolved_patient_id:
            record = save_prediction(
                db=db,
                patient_id=resolved_patient_id,
                prediction_type="heart",
                result=result,
                input_data=data.model_dump()
            )
            saved_id = record.id

        return {
            **result,
            "saved": saved_id is not None,
            "prediction_record_id": saved_id,
            "patient_id": resolved_patient_id
        }

    except (NotFoundException, ForbiddenException):
        raise
    except Exception as e:
        logger.error(f"Heart disease prediction failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Heart disease prediction failed")


# ─────────────────────────────────────────────
# Chest X-ray Prediction
# ─────────────────────────────────────────────

@router.post("/predict/xray")
async def xray_prediction(
    file: UploadFile = File(...),
    patient_id: Optional[int] = Query(None, description="Patient ID to link result (doctors only)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        image = Image.open(io.BytesIO(await file.read())).convert("RGB")
        result = predict_xray(image)

        resolved_patient_id = _resolve_patient(patient_id, current_user, db)
        saved_id = None

        if resolved_patient_id:
            record = save_prediction(
                db=db,
                patient_id=resolved_patient_id,
                prediction_type="xray",
                result=result,
                input_data={"filename": file.filename}
            )
            saved_id = record.id

        return {
            **result,
            "saved": saved_id is not None,
            "prediction_record_id": saved_id,
            "patient_id": resolved_patient_id
        }

    except (NotFoundException, ForbiddenException):
        raise
    except Exception as e:
        logger.error(f"X-ray prediction failed: {str(e)}")
        raise HTTPException(status_code=400, detail="Invalid X-ray image")
