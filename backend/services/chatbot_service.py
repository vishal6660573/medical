from typing import Optional, List, Dict, Any, Tuple, NamedTuple
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logs import logger
from app.database.models import User, Patient, UserRole
from app.rag.embeddings import get_embedding_service
from app.rag.vector_store import get_vector_store
from services.query_router import classify_query, QueryType
from services.patient_rag_service import get_patient_rag_service
from services.wikipedia_service import get_wikipedia_service
from services.ollama_service import get_ollama_service


class ChatbotResult(NamedTuple):
    reply: str
    sources: List[Dict[str, Any]]
    query_type: str
    source: str


async def chat_with_medibot(
    message: str,
    history: Optional[List[Dict[str, str]]] = None,
    patient_context: Optional[dict] = None,
    current_user: Optional[User] = None,
    db: Optional[Session] = None
) -> ChatbotResult:
    """
    Intelligent Medical Chatbot Pipeline:
    
    Case 1: PATIENT_SPECIFIC
      -> Route: PATIENT_SPECIFIC
      -> Retrieve authenticated patient records via Patient RAG
      -> Generate answer strictly grounded in patient records via Ollama
      -> Return reply + sources + metadata (source: 'patient_rag+ollama')
      
    Case 2: GENERAL Medical Query
      -> Route: GENERAL
      -> Send question to Ollama (augmented with guidelines RAG if available)
      -> If confident/sufficient -> Return answer (source: 'ollama')
      
    Case 3: GENERAL Fallback with Wikipedia
      -> If Ollama indicates insufficient information / inability to answer:
      -> Query Wikipedia Service
      -> Pass retrieved Wikipedia context to Ollama
      -> Generate final synthesized response (source: 'ollama+wikipedia')
    """
    history = history or []
    ollama_service = get_ollama_service()

    # Step 1: Query Routing & Classification
    classification = classify_query(message)
    query_type_str = classification.query_type.value

    # ─────────────────────────────────────────────────────────────
    # CASE 1: PATIENT-SPECIFIC QUERY
    # ─────────────────────────────────────────────────────────────
    if classification.query_type == QueryType.PATIENT_SPECIFIC:
        patient_id = None
        patient_obj = None

        if current_user and db is not None:
            if current_user.role == UserRole.patient:
                patient_obj = db.query(Patient).filter(Patient.user_id == current_user.id).first()
                if patient_obj:
                    patient_id = patient_obj.id
            elif current_user.role in (UserRole.doctor, UserRole.admin):
                # Doctor inquiring - check if patient_context or direct patient is available
                if patient_context and patient_context.get("patient_id"):
                    patient_id = patient_context["patient_id"]
                else:
                    patient_obj = db.query(Patient).filter(Patient.user_id == current_user.id).first()
                    if patient_obj:
                        patient_id = patient_obj.id

        if not patient_id or db is None:
            # Authenticated user is not a patient or has no profile records
            reply = (
                "I could not find an active patient profile associated with your account "
                "to retrieve personal medical records."
            )
            return ChatbotResult(
                reply=reply,
                sources=[],
                query_type=query_type_str,
                source="patient_rag+ollama"
            )

        # Retrieve confidential patient records strictly for this patient_id
        patient_rag = get_patient_rag_service()
        rag_result = patient_rag.retrieve_patient_context(patient_id=patient_id, db=db, query=message)

        prompt = ollama_service.build_patient_prompt(
            message=message,
            patient_context=rag_result.context_text,
            history=history
        )

        try:
            raw_reply = await ollama_service.generate(prompt)
            reply = raw_reply.strip()
        except Exception as e:
            logger.error(f"Ollama generation failed during patient-specific query: {e}")
            raise

        return ChatbotResult(
            reply=reply,
            sources=rag_result.sources,
            query_type=query_type_str,
            source="patient_rag+ollama"
        )

    # ─────────────────────────────────────────────────────────────
    # CASE 2 & 3: GENERAL MEDICAL QUERY + WIKIPEDIA FALLBACK
    # ─────────────────────────────────────────────────────────────
    guidelines_chunks: List[Dict[str, Any]] = []
    sources: List[Dict[str, Any]] = []

    # Optional: Retrieve clinical guidelines from vector knowledge base
    if getattr(settings, "RAG_ENABLED", True) and db is not None:
        try:
            embedding_service = get_embedding_service()
            query_embedding = await embedding_service.aembed_text(message)
            vector_store = get_vector_store()
            guidelines_chunks = vector_store.search_similar(
                db=db,
                query_embedding=query_embedding,
                top_k=getattr(settings, "RAG_TOP_K", 3),
                min_score=0.08
            )

            seen = set()
            for chk in guidelines_chunks:
                key = (chk.get("document_title"), chk.get("section"))
                if key not in seen:
                    seen.add(key)
                    sources.append({
                        "document_title": chk.get("document_title"),
                        "section": chk.get("section"),
                        "source_file": chk.get("source_file"),
                        "score": chk.get("score"),
                        "snippet": chk.get("snippet")
                    })
        except Exception as e:
            logger.warning(f"Guidelines vector search skipped due to error: {e}")

    general_prompt = ollama_service.build_general_prompt(
        message=message,
        history=history,
        guidelines_chunks=guidelines_chunks
    )

    try:
        raw_reply = await ollama_service.generate(general_prompt)
        reply = raw_reply.strip()
    except Exception as e:
        logger.error(f"Ollama generation failed during general query: {e}")
        raise

    # Check whether Ollama response is insufficient / uncertain and requires external Wikipedia fallback
    is_insufficient = ollama_service.is_insufficient_response(reply)

    if is_insufficient:
        logger.info(f"Ollama response triggered Wikipedia fallback for query: '{message[:50]}'")
        wiki_service = get_wikipedia_service()
        wiki_result = await wiki_service.search_and_summarize(message)

        if wiki_result and wiki_result.extract:
            wiki_prompt = ollama_service.build_wikipedia_prompt(
                message=message,
                wikipedia_title=wiki_result.title,
                wikipedia_extract=wiki_result.extract,
                history=history
            )

            try:
                wiki_reply = await ollama_service.generate(wiki_prompt)
                if wiki_reply and wiki_reply.strip():
                    wiki_sources = [
                        {
                            "document_title": f"Wikipedia: {wiki_result.title}",
                            "section": "Article Summary",
                            "source_file": wiki_result.url,
                            "snippet": wiki_result.extract[:200] + ("..." if len(wiki_result.extract) > 200 else "")
                        }
                    ]
                    return ChatbotResult(
                        reply=wiki_reply.strip(),
                        sources=wiki_sources,
                        query_type=query_type_str,
                        source="ollama+wikipedia"
                    )
            except Exception as e:
                logger.warning(f"Ollama generation with Wikipedia context failed: {e}")

    # Return standard general medical response
    return ChatbotResult(
        reply=reply,
        sources=sources,
        query_type=query_type_str,
        source="ollama"
    )
