from sqlalchemy import (
    Column, Integer, String, Float, Boolean,
    DateTime, ForeignKey, Text, Enum as SAEnum
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.database.database import Base


# ─────────────────────────────────────────────
# Enums
# ─────────────────────────────────────────────

class UserRole(str, enum.Enum):
    patient = "patient"
    doctor  = "doctor"
    admin   = "admin"


class BloodGroup(str, enum.Enum):
    A_POS  = "A+"
    A_NEG  = "A-"
    B_POS  = "B+"
    B_NEG  = "B-"
    O_POS  = "O+"
    O_NEG  = "O-"
    AB_POS = "AB+"
    AB_NEG = "AB-"


class Gender(str, enum.Enum):
    male    = "male"
    female  = "female"
    other   = "other"


# ─────────────────────────────────────────────
# User — login credentials + role
# ─────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id            = Column(Integer, primary_key=True, index=True)
    full_name     = Column(String(100), nullable=False)
    email         = Column(String(150), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role          = Column(SAEnum(UserRole), default=UserRole.patient, nullable=False)
    is_active     = Column(Boolean, default=True)
    created_at    = Column(DateTime(timezone=True), server_default=func.now())
    updated_at    = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    patient_profile = relationship("Patient", back_populates="user", uselist=False)
    doctor_profile  = relationship("Doctor",  back_populates="user", uselist=False)


# ─────────────────────────────────────────────
# Doctor profile
# ─────────────────────────────────────────────

class Doctor(Base):
    __tablename__ = "doctors"

    id              = Column(Integer, primary_key=True, index=True)
    user_id         = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    specialization  = Column(String(100))
    license_number  = Column(String(50), unique=True)
    hospital        = Column(String(150))
    phone           = Column(String(20))
    created_at      = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user    = relationship("User",   back_populates="doctor_profile")
    visits  = relationship("Visit",  back_populates="doctor")


# ─────────────────────────────────────────────
# Patient profile
# ─────────────────────────────────────────────

class Patient(Base):
    __tablename__ = "patients"

    id           = Column(Integer, primary_key=True, index=True)
    user_id      = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    date_of_birth = Column(String(20))
    gender       = Column(SAEnum(Gender))
    blood_group  = Column(SAEnum(BloodGroup))
    phone        = Column(String(20))
    address      = Column(Text)
    emergency_contact = Column(String(100))
    allergies    = Column(Text)          # comma-separated or free text
    created_at   = Column(DateTime(timezone=True), server_default=func.now())
    updated_at   = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user         = relationship("User",              back_populates="patient_profile")
    visits       = relationship("Visit",             back_populates="patient")
    medications  = relationship("Medication",        back_populates="patient")
    predictions  = relationship("PredictionResult",  back_populates="patient")


# ─────────────────────────────────────────────
# Visit — each doctor consultation
# ─────────────────────────────────────────────

class Visit(Base):
    __tablename__ = "visits"

    id           = Column(Integer, primary_key=True, index=True)
    patient_id   = Column(Integer, ForeignKey("patients.id"), nullable=False)
    doctor_id    = Column(Integer, ForeignKey("doctors.id"), nullable=True)
    visit_date   = Column(DateTime(timezone=True), server_default=func.now())
    chief_complaint = Column(Text)       # reason for visit
    diagnosis    = Column(Text)
    notes        = Column(Text)
    follow_up_date = Column(String(20))

    # Relationships
    patient      = relationship("Patient",    back_populates="visits")
    doctor       = relationship("Doctor",     back_populates="visits")
    medications  = relationship("Medication", back_populates="visit")


# ─────────────────────────────────────────────
# Medication — prescribed per visit
# ─────────────────────────────────────────────

class Medication(Base):
    __tablename__ = "medications"

    id           = Column(Integer, primary_key=True, index=True)
    patient_id   = Column(Integer, ForeignKey("patients.id"), nullable=False)
    visit_id     = Column(Integer, ForeignKey("visits.id"), nullable=True)
    name         = Column(String(150), nullable=False)
    dosage       = Column(String(100))   # e.g. "500mg"
    frequency    = Column(String(100))   # e.g. "twice daily"
    duration     = Column(String(100))   # e.g. "7 days"
    prescribed_by = Column(String(100))
    prescribed_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active    = Column(Boolean, default=True)
    notes        = Column(Text)

    # Relationships
    patient      = relationship("Patient", back_populates="medications")
    visit        = relationship("Visit",   back_populates="medications")


# ─────────────────────────────────────────────
# PredictionResult — stores every ML prediction
# ─────────────────────────────────────────────

class PredictionResult(Base):
    __tablename__ = "prediction_results"

    id              = Column(Integer, primary_key=True, index=True)
    patient_id      = Column(Integer, ForeignKey("patients.id"), nullable=False)
    prediction_type = Column(String(50), nullable=False)  # "diabetes", "heart", "xray"
    probability     = Column(Float)
    risk_level      = Column(String(20))     # "High" / "Low"
    input_data      = Column(Text)           # JSON string of inputs used
    result_summary  = Column(Text)
    created_at      = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    patient         = relationship("Patient", back_populates="predictions")
