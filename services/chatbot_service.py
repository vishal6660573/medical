from typing import Optional
import google.generativeai as genai
from app.core.config import settings
from app.core.logs import logger

genai.configure(api_key=settings.GEMINI_API_KEY)

GEMINI_MODEL = "gemini-2.0-flash"

SYSTEM_PROMPT = """You are MediBot, a knowledgeable and compassionate AI medical assistant integrated into the MediSense Smart Healthcare Platform.

Your role:
- Help patients understand their symptoms, medications, and general health queries
- Assist doctors with quick clinical references, drug information, and differential considerations
- Provide clear, accurate, and empathetic health information

Rules you must strictly follow:
1. ALWAYS recommend consulting a qualified doctor for diagnosis or treatment decisions
2. NEVER prescribe medications or provide specific dosages as medical advice
3. If someone describes a medical emergency (chest pain, difficulty breathing, stroke symptoms etc.), immediately tell them to call emergency services (108 in India / 911 in US)
4. Be empathetic and supportive — many users may be anxious about their health
5. Keep responses concise but complete — use bullet points for clarity when listing symptoms or steps
6. If patient context is provided, use it to personalize responses
7. Do not make up symptoms, drug names, or statistics — if unsure, say so

You are not a replacement for professional medical care. Always make this clear when relevant."""


def _build_prompt(message: str, history: list, patient_context: Optional[dict]) -> str:
    parts = [SYSTEM_PROMPT, ""]

    if patient_context:
        ctx_parts = []
        if patient_context.get("full_name"):         ctx_parts.append(f"Patient: {patient_context['full_name']}")
        if patient_context.get("gender"):             ctx_parts.append(f"Gender: {patient_context['gender']}")
        if patient_context.get("blood_group"):        ctx_parts.append(f"Blood group: {patient_context['blood_group']}")
        if patient_context.get("allergies"):          ctx_parts.append(f"Known allergies: {patient_context['allergies']}")
        if patient_context.get("active_medications"): ctx_parts.append(f"Current medications: {patient_context['active_medications']}")
        if ctx_parts:
            parts.append("[PATIENT CONTEXT]")
            parts.append(", ".join(ctx_parts))
            parts.append("")

    if history:
        parts.append("[CONVERSATION HISTORY]")
        for msg in history:
            role = "Patient/Doctor" if msg["role"] == "user" else "MediBot"
            parts.append(f"{role}: {msg['content']}")
        parts.append("")

    parts.append("[CURRENT MESSAGE]")
    parts.append(f"Patient/Doctor: {message}")
    parts.append("")
    parts.append("MediBot:")

    return "\n".join(parts)


async def chat_with_medibot(
    message: str,
    history: list,
    patient_context: Optional[dict] = None,
) -> str:
    prompt = _build_prompt(message, history, patient_context)
    try:
        model = genai.GenerativeModel(GEMINI_MODEL)
        response = await model.generate_content_async(prompt)
        reply = response.text.strip()
        logger.info(f"MediBot responded | model={GEMINI_MODEL} | history_len={len(history)}")
        return reply
    except Exception as e:
        logger.error(f"MediBot error: {str(e)}")
        raise
