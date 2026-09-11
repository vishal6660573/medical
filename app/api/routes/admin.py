from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.auth.dependencies import get_current_user, get_current_doctor, get_current_admin
from app.core.exceptions import NotFoundException, ForbiddenException
from app.core.logs import logger
from app.database.database import get_db
from app.database.models import User, UserRole

router = APIRouter(prefix="/admin", tags=["Admin"])


class UserOut(BaseModel):
    id: int
    full_name: str
    email: str
    role: str
    is_active: bool

    class Config:
        from_attributes = True


class UpdateStatusRequest(BaseModel):
    is_active: bool


# ── List all users ──
@router.get("/users", response_model=list[UserOut])
def list_users(
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    return db.query(User).order_by(User.created_at.desc()).all()


# ── Toggle user active/inactive ──
@router.patch("/users/{user_id}/status", response_model=UserOut)
def update_user_status(
    user_id: int,
    body: UpdateStatusRequest,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    if user_id == current_user.id:
        raise ForbiddenException("Cannot deactivate your own account")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise NotFoundException(f"User {user_id} not found")
    user.is_active = body.is_active
    db.commit()
    db.refresh(user)
    logger.info(f"Admin {current_user.id} set user {user_id} active={body.is_active}")
    return user


# ── Get full patient profile (doctor or admin) ──
@router.get("/patients/{patient_id}/full")
def get_full_patient_profile(
    patient_id: int,
    current_user: User = Depends(get_current_doctor),
    db: Session = Depends(get_db)
):
    from app.database.models import Patient, Visit, Medication, PredictionResult

    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise NotFoundException(f"Patient {patient_id} not found")

    visits = db.query(Visit).filter(Visit.patient_id == patient_id).order_by(Visit.visit_date.desc()).all()
    meds = db.query(Medication).filter(Medication.patient_id == patient_id).order_by(Medication.prescribed_at.desc()).all()
    preds = db.query(PredictionResult).filter(PredictionResult.patient_id == patient_id).order_by(PredictionResult.created_at.desc()).all()

    return {
        "profile": {
            "id": patient.id,
            "user_id": patient.user_id,
            "full_name": patient.user.full_name,
            "email": patient.user.email,
            "date_of_birth": patient.date_of_birth,
            "gender": patient.gender,
            "blood_group": patient.blood_group,
            "phone": patient.phone,
            "address": patient.address,
            "emergency_contact": patient.emergency_contact,
            "allergies": patient.allergies,
        },
        "visits": [
            {
                "id": v.id,
                "visit_date": str(v.visit_date),
                "chief_complaint": v.chief_complaint,
                "diagnosis": v.diagnosis,
                "notes": v.notes,
                "follow_up_date": v.follow_up_date,
                "doctor_name": v.doctor.user.full_name if v.doctor else None,
            }
            for v in visits
        ],
        "medications": [
            {
                "id": m.id,
                "name": m.name,
                "dosage": m.dosage,
                "frequency": m.frequency,
                "duration": m.duration,
                "prescribed_by": m.prescribed_by,
                "is_active": m.is_active,
                "notes": m.notes,
                "prescribed_at": str(m.prescribed_at),
            }
            for m in meds
        ],
        "predictions": [
            {
                "id": p.id,
                "prediction_type": p.prediction_type,
                "probability": p.probability,
                "risk_level": p.risk_level,
                "created_at": str(p.created_at),
            }
            for p in preds
        ],
    }
