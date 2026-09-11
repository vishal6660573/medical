from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.auth.dependencies import get_current_user
from app.core.logs import logger
from app.database.database import get_db
from app.database.models import User, Patient, Medication, UserRole
from services.chatbot_service import chat_with_medibot

router = APIRouter(prefix="/chatbot", tags=["Medical Chatbot"])


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    history: List[Message] = []
    include_patient_context: bool = True


class ChatResponse(BaseModel):
    reply: str
    role: str = "assistant"


def _get_patient_context(user: User, db: Session) -> Optional[dict]:
    if user.role != UserRole.patient:
        return None
    patient = db.query(Patient).filter(Patient.user_id == user.id).first()
    if not patient:
        return None
    active_meds = [m.name for m in db.query(Medication).filter(
        Medication.patient_id == patient.id,
        Medication.is_active == True
    ).all()]
    return {
        "full_name": user.full_name,
        "gender": patient.gender,
        "blood_group": patient.blood_group,
        "allergies": patient.allergies,
        "active_medications": ", ".join(active_meds) if active_meds else None,
    }


@router.post("/chat", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        patient_context = None
        if body.include_patient_context:
            patient_context = _get_patient_context(current_user, db)

        history = [{"role": m.role, "content": m.content} for m in body.history]
        logger.info(f"Chatbot | user={current_user.id} | history={len(history)} | msg={body.message[:60]}")

        reply = await chat_with_medibot(
            message=body.message,
            history=history,
            patient_context=patient_context
        )
        return ChatResponse(reply=reply)

    except Exception as e:
        err_str = str(e)
        logger.error(f"Chatbot error: {err_str}")
        is_quota = "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "quota" in err_str.lower()
        if is_quota:
            raise HTTPException(status_code=429, detail="rate_limit")
        raise HTTPException(status_code=503, detail="unavailable")
