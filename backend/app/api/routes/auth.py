from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr

from app.auth.hashing import hash_password, verify_password
from app.auth.jwt_handler import create_access_token
from app.auth.dependencies import get_current_user
from app.core.exceptions import ConflictException, CredentialsException
from app.core.logs import logger
from app.database.database import get_db
from app.database.models import User, UserRole, Patient, Doctor

router = APIRouter(prefix="/auth", tags=["Auth"])


# ─────────────────────────────────────────────
# Pydantic schemas (auth-specific, kept here)
# ─────────────────────────────────────────────

class RegisterRequest(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    role: UserRole = UserRole.patient


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    user_id: int
    full_name: str


class UserOut(BaseModel):
    id: int
    full_name: str
    email: str
    role: str
    is_active: bool

    class Config:
        from_attributes = True


# ─────────────────────────────────────────────
# Register
# ─────────────────────────────────────────────

@router.post("/register", response_model=UserOut, status_code=201)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    # Check duplicate email
    existing = db.query(User).filter(User.email == body.email).first()
    if existing:
        raise ConflictException("Email already registered")

    user = User(
        full_name=body.full_name,
        email=body.email,
        hashed_password=hash_password(body.password),
        role=body.role,
    )
    db.add(user)
    db.flush()  # get user.id before commit

    # Auto-create profile based on role
    if body.role == UserRole.patient:
        db.add(Patient(user_id=user.id))
    elif body.role == UserRole.doctor:
        db.add(Doctor(user_id=user.id))

    db.commit()
    db.refresh(user)
    logger.info(f"New user registered: {user.email} | role={user.role}")
    return user


# ─────────────────────────────────────────────
# Login
# ─────────────────────────────────────────────

@router.post("/login", response_model=TokenResponse)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise CredentialsException("Incorrect email or password")

    if not user.is_active:
        raise CredentialsException("Account is disabled")

    token = create_access_token({"sub": str(user.id), "role": user.role})
    logger.info(f"User logged in: {user.email}")

    return TokenResponse(
        access_token=token,
        role=user.role,
        user_id=user.id,
        full_name=user.full_name
    )


# ─────────────────────────────────────────────
# Me — get current logged-in user
# ─────────────────────────────────────────────

@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user
