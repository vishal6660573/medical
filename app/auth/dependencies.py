from typing import Optional
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.auth.jwt_handler import decode_access_token
from app.core.exceptions import CredentialsException, ForbiddenException
from app.database.database import get_db
from app.database.models import User, UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    payload = decode_access_token(token)
    if not payload:
        raise CredentialsException()

    user_id = payload.get("sub")
    if user_id is None:
        raise CredentialsException()

    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user or not user.is_active:
        raise CredentialsException("User not found or inactive")

    return user


def get_current_doctor(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in (UserRole.doctor, UserRole.admin):
        raise ForbiddenException("Only doctors can perform this action")
    return current_user


def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.admin:
        raise ForbiddenException("Only admins can perform this action")
    return current_user


def get_doctor_or_patient(current_user: User = Depends(get_current_user)) -> User:
    return current_user
