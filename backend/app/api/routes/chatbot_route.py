from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.auth.dependencies import get_current_user, get_current_doctor
from app.core.logs import logger
from app.database.database import get_db
from app.database.models import User, Patient, Medication, UserRole
from app.rag.ingest import ingest_medical_documents
from app.rag.vector_store import get_vector_store
from services.chatbot_service import chat_with_medibot

router = APIRouter(prefix="/chatbot", tags=["Medical Chatbot"])


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    history: List[Message] = []
    include_patient_context: bool = True


class SourceItem(BaseModel):
    document_title: Optional[str] = None
    section: Optional[str] = None
    source_file: Optional[str] = None
    score: Optional[float] = None
    snippet: Optional[str] = None
    url: Optional[str] = None


class ChatResponse(BaseModel):
    reply: str
    role: str = "assistant"
    sources: List[SourceItem] = []
    query_type: Optional[str] = None
    source: Optional[str] = None


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
        "patient_id": patient.id,
        "full_name": user.full_name,
        "gender": patient.gender.value if patient.gender else None,
        "blood_group": patient.blood_group.value if patient.blood_group else None,
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
        logger.info(f"Chatbot | user={current_user.id} | history={len(history)} | msg_len={len(body.message)}")

        result = await chat_with_medibot(
            message=body.message,
            history=history,
            patient_context=patient_context,
            current_user=current_user,
            db=db
        )
        return ChatResponse(
            reply=result.reply,
            role="assistant",
            sources=result.sources,
            query_type=result.query_type,
            source=result.source
        )

    except Exception as e:
        err_str = str(e)
        logger.error(f"Chatbot error: {err_str}")
        is_quota = "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "quota" in err_str.lower()
        if is_quota:
            raise HTTPException(status_code=429, detail="rate_limit")
        raise HTTPException(status_code=503, detail=f"Ollama or Chatbot error: {err_str}")


@router.post("/ingest")
def trigger_ingest(
    clear_existing: bool = True,
    current_user: User = Depends(get_current_user)
):
    """Admin/authenticated trigger to load or refresh medical RAG knowledge base."""
    result = ingest_medical_documents(clear_existing=clear_existing)
    return result


@router.get("/rag-stats")
def get_rag_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get count of indexed chunks and documents in knowledge base."""
    store = get_vector_store()
    return store.get_stats(db)
