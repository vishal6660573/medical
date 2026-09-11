from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel
from datetime import datetime

from app.auth.dependencies import get_current_user, get_current_doctor
from app.core.exceptions import NotFoundException, ForbiddenException
from app.core.logs import logger
from app.database.database import get_db
from app.database.models import User, Patient, Visit, Medication, PredictionResult, UserRole, Gender, BloodGroup

router = APIRouter(prefix="/patients", tags=["Patients"])


# ─────────────────────────────────────────────
# Pydantic schemas
# ─────────────────────────────────────────────

class PatientProfileUpdate(BaseModel):
    date_of_birth: Optional[str] = None
    gender: Optional[Gender] = None
    blood_group: Optional[BloodGroup] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    emergency_contact: Optional[str] = None
    allergies: Optional[str] = None


class PatientOut(BaseModel):
    id: int
    user_id: int
    date_of_birth: Optional[str]
    gender: Optional[str]
    blood_group: Optional[str]
    phone: Optional[str]
    address: Optional[str]
    emergency_contact: Optional[str]
    allergies: Optional[str]
    full_name: str
    email: str

    class Config:
        from_attributes = True


class VisitCreate(BaseModel):
    chief_complaint: str
    diagnosis: Optional[str] = None
    notes: Optional[str] = None
    follow_up_date: Optional[str] = None


class VisitOut(BaseModel):
    id: int
    patient_id: int
    visit_date: Optional[datetime]
    chief_complaint: Optional[str]
    diagnosis: Optional[str]
    notes: Optional[str]
    follow_up_date: Optional[str]
    doctor_name: Optional[str] = None

    class Config:
        from_attributes = True


class MedicationCreate(BaseModel):
    name: str
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    duration: Optional[str] = None
    notes: Optional[str] = None
    visit_id: Optional[int] = None


class MedicationOut(BaseModel):
    id: int
    name: str
    dosage: Optional[str]
    frequency: Optional[str]
    duration: Optional[str]
    prescribed_by: Optional[str]
    is_active: bool
    notes: Optional[str]

    class Config:
        from_attributes = True


# ─────────────────────────────────────────────
# Helper
# ─────────────────────────────────────────────

def _get_patient_or_404(patient_id: int, db: Session) -> Patient:
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise NotFoundException(f"Patient {patient_id} not found")
    return patient


def _assert_access(patient: Patient, current_user: User):
    """Patient can only access their own records; doctors/admins can access all."""
    if current_user.role == UserRole.patient:
        if not patient.user_id == current_user.id:
            raise ForbiddenException("You can only view your own records")


# ─────────────────────────────────────────────
# GET /patients/me  — patient sees own profile
# ─────────────────────────────────────────────

@router.get("/me", response_model=PatientOut)
def get_my_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()
    if not patient:
        raise NotFoundException("Patient profile not found")
    return _enrich(patient)


# ─────────────────────────────────────────────
# PUT /patients/me  — patient updates own profile
# ─────────────────────────────────────────────

@router.put("/me", response_model=PatientOut)
def update_my_profile(
    body: PatientProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()
    if not patient:
        raise NotFoundException("Patient profile not found")

    for field, value in body.model_dump(exclude_none=True).items():
        setattr(patient, field, value)

    db.commit()
    db.refresh(patient)
    return _enrich(patient)


# ─────────────────────────────────────────────
# GET /patients/  — doctor/admin lists all patients
# ─────────────────────────────────────────────

@router.get("/", response_model=list[PatientOut])
def list_patients(
    current_user: User = Depends(get_current_doctor),
    db: Session = Depends(get_db)
):
    patients = db.query(Patient).all()
    return [_enrich(p) for p in patients]


# ─────────────────────────────────────────────
# GET /patients/{patient_id}  — doctor/patient views a profile
# ─────────────────────────────────────────────

@router.get("/{patient_id}", response_model=PatientOut)
def get_patient(
    patient_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    patient = _get_patient_or_404(patient_id, db)
    _assert_access(patient, current_user)
    return _enrich(patient)


# ─────────────────────────────────────────────
# VISITS
# ─────────────────────────────────────────────

@router.post("/{patient_id}/visits", response_model=VisitOut, status_code=201)
def add_visit(
    patient_id: int,
    body: VisitCreate,
    current_user: User = Depends(get_current_doctor),
    db: Session = Depends(get_db)
):
    patient = _get_patient_or_404(patient_id, db)

    doctor = current_user.doctor_profile
    visit = Visit(
        patient_id=patient.id,
        doctor_id=doctor.id if doctor else None,
        chief_complaint=body.chief_complaint,
        diagnosis=body.diagnosis,
        notes=body.notes,
        follow_up_date=body.follow_up_date
    )
    db.add(visit)
    db.commit()
    db.refresh(visit)
    logger.info(f"Visit added for patient {patient_id} by doctor {current_user.id}")
    return _enrich_visit(visit, current_user.full_name)


@router.get("/{patient_id}/visits", response_model=list[VisitOut])
def get_visits(
    patient_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    patient = _get_patient_or_404(patient_id, db)
    _assert_access(patient, current_user)
    visits = db.query(Visit).filter(Visit.patient_id == patient_id).order_by(Visit.visit_date.desc()).all()
    return [_enrich_visit(v, None) for v in visits]


# ─────────────────────────────────────────────
# MEDICATIONS
# ─────────────────────────────────────────────

@router.post("/{patient_id}/medications", response_model=MedicationOut, status_code=201)
def add_medication(
    patient_id: int,
    body: MedicationCreate,
    current_user: User = Depends(get_current_doctor),
    db: Session = Depends(get_db)
):
    patient = _get_patient_or_404(patient_id, db)
    med = Medication(
        patient_id=patient.id,
        visit_id=body.visit_id,
        name=body.name,
        dosage=body.dosage,
        frequency=body.frequency,
        duration=body.duration,
        prescribed_by=current_user.full_name,
        notes=body.notes
    )
    db.add(med)
    db.commit()
    db.refresh(med)
    return med


@router.get("/{patient_id}/medications", response_model=list[MedicationOut])
def get_medications(
    patient_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    patient = _get_patient_or_404(patient_id, db)
    _assert_access(patient, current_user)
    meds = db.query(Medication).filter(Medication.patient_id == patient_id).order_by(Medication.prescribed_at.desc()).all()
    return meds


# ─────────────────────────────────────────────
# PREDICTION HISTORY
# ─────────────────────────────────────────────

@router.get("/{patient_id}/predictions")
def get_prediction_history(
    patient_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    patient = _get_patient_or_404(patient_id, db)
    _assert_access(patient, current_user)
    results = db.query(PredictionResult).filter(
        PredictionResult.patient_id == patient_id
    ).order_by(PredictionResult.created_at.desc()).all()
    return results


# ─────────────────────────────────────────────
# Enrichment helpers
# ─────────────────────────────────────────────

def _enrich(patient: Patient) -> dict:
    data = {
        "id": patient.id,
        "user_id": patient.user_id,
        "date_of_birth": patient.date_of_birth,
        "gender": patient.gender,
        "blood_group": patient.blood_group,
        "phone": patient.phone,
        "address": patient.address,
        "emergency_contact": patient.emergency_contact,
        "allergies": patient.allergies,
        "full_name": patient.user.full_name if patient.user else "",
        "email": patient.user.email if patient.user else "",
    }
    return data


def _enrich_visit(visit: Visit, doctor_name: Optional[str]) -> dict:
    return {
        "id": visit.id,
        "patient_id": visit.patient_id,
        "visit_date": visit.visit_date,
        "chief_complaint": visit.chief_complaint,
        "diagnosis": visit.diagnosis,
        "notes": visit.notes,
        "follow_up_date": visit.follow_up_date,
        "doctor_name": doctor_name or (visit.doctor.user.full_name if visit.doctor else None)
    }
