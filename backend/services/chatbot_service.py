from typing import Optional, List, Dict, Any, Tuple
import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logs import logger
from app.rag.embeddings import get_embedding_service
from app.rag.vector_store import get_vector_store

SYSTEM_PROMPT = """You are MediBot, an empathetic, highly knowledgeable AI clinical assistant integrated into the MediSense Smart Healthcare Platform.

Your role:
- Help patients understand their symptoms, medications, lab values, and general wellness.
- Assist clinicians with quick reference summaries, guideline recommendations, and differential considerations.
- Ground your medical advice in trusted medical literature and clinical guidelines.

Strict Clinical & Ethical Safety Rules:
1. ALWAYS state clearly that you provide informational guidance, not a definitive medical diagnosis.
2. NEVER prescribe prescription dosages or recommend changes to a doctor's prescribed regimen.
3. RED FLAG EMERGENCIES: If the user describes sudden crushing chest pain, difficulty breathing, FAST stroke signs (facial droop, arm weakness, slurred speech), or severe anaphylaxis, IMMEDIATELY urge them to call emergency services (108 in India / 911 in North America) or visit the nearest emergency department.
4. PERSONALIZED CARE: If confidential patient context is provided, consider their allergies and medications when discussing contraindications.
5. EVIDENCE-BASED: When relevant clinical guidelines are provided in the medical context, use them accurately and cite the guidelines (e.g. ADA, ACC/AHA, ATS).
6. Format responses clearly with bullet points and bold section highlights for readability."""


def _build_prompt(
    message: str,
    history: list,
    patient_context: Optional[dict],
    retrieved_chunks: Optional[List[dict]] = None
) -> str:
    parts = [SYSTEM_PROMPT, ""]

    # 1. Patient Context (from PostgreSQL User/Patient/Medication DB - strictly separated)
    if patient_context:
        ctx_parts = []
        if patient_context.get("full_name"):
            ctx_parts.append(f"Patient Name: {patient_context['full_name']}")
        if patient_context.get("gender"):
            ctx_parts.append(f"Gender: {patient_context['gender']}")
        if patient_context.get("blood_group"):
            ctx_parts.append(f"Blood Group: {patient_context['blood_group']}")
        if patient_context.get("allergies"):
            ctx_parts.append(f"Known Allergies: {patient_context['allergies']}")
        if patient_context.get("active_medications"):
            ctx_parts.append(f"Active Prescriptions: {patient_context['active_medications']}")

        if ctx_parts:
            parts.append("[CONFIDENTIAL PATIENT CONTEXT]")
            parts.append(" | ".join(ctx_parts))
            parts.append("Note: Consider allergies and active prescriptions when discussing medication safety.")
            parts.append("")

    # 2. Retrieved Medical Literature / Clinical Guidelines (from RAG Vector Store)
    if retrieved_chunks:
        parts.append("[TRUSTED MEDICAL KNOWLEDGE BASE (RETRIEVED GUIDELINES)]")
        for i, chunk in enumerate(retrieved_chunks, start=1):
            title = chunk.get("document_title", "Medical Guideline")
            section = chunk.get("section", "Reference")
            content = chunk.get("content", "").strip()
            parts.append(f"--- Document Source {i}: {title} | Section: {section} ---")
            parts.append(content)
            parts.append("")
        parts.append("Instruction: Use the trusted medical knowledge above to provide clinically accurate explanations.")
        parts.append("")

    # 3. Conversation History
    if history:
        parts.append("[CONVERSATION HISTORY]")
        for msg in history:
            role = "Patient/Doctor" if msg.get("role") == "user" else "MediBot"
            parts.append(f"{role}: {msg.get('content', '')}")
        parts.append("")

    # 4. Current User Query
    parts.append("[CURRENT INQUIRY]")
    parts.append(f"User: {message}")
    parts.append("")
    parts.append("MediBot:")

    return "\n".join(parts)


async def chat_with_medibot(
    message: str,
    history: list,
    patient_context: Optional[dict] = None,
    db: Optional[Session] = None
) -> Tuple[str, List[Dict[str, Any]]]:
    """
    RAG-Augmented Medical Chatbot:
    1. Embeds user query
    2. Retrieves top-k relevant medical guideline chunks
    3. Blends patient context + medical context + history
    4. Queries Ollama (Llama 3.2)
    5. Returns answer and source citations
    """
    retrieved_chunks: List[Dict[str, Any]] = []
    sources: List[Dict[str, Any]] = []

    # 1. RAG Retrieval
    if getattr(settings, "RAG_ENABLED", True) and db is not None:
        try:
            embedding_service = get_embedding_service()
            query_embedding = await embedding_service.aembed_text(message)
            vector_store = get_vector_store()
            retrieved_chunks = vector_store.search_similar(
                db=db,
                query_embedding=query_embedding,
                top_k=getattr(settings, "RAG_TOP_K", 3),
                min_score=0.08
            )

            # Extract distinct citations
            seen_sources = set()
            for chk in retrieved_chunks:
                key = (chk.get("document_title"), chk.get("section"))
                if key not in seen_sources:
                    seen_sources.add(key)
                    sources.append({
                        "document_title": chk.get("document_title"),
                        "section": chk.get("section"),
                        "source_file": chk.get("source_file"),
                        "score": chk.get("score"),
                        "snippet": chk.get("snippet")
                    })
        except Exception as e:
            logger.warning(f"RAG retrieval skipped due to error: {e}")

    # 2. Build Augmented Prompt
    prompt = _build_prompt(message, history, patient_context, retrieved_chunks)

    # 3. Call Ollama LLM
    try:
        url = f"{settings.OLLAMA_BASE_URL.rstrip('/')}/api/generate"
        payload = {
            "model": settings.OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
        }
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            reply = data.get("response", "").strip()

        logger.info(f"MediBot responded | model={settings.OLLAMA_MODEL} | sources_used={len(sources)}")
        return reply, sources

    except Exception as e:
        logger.error(f"MediBot generation error: {str(e)}")
        raise
