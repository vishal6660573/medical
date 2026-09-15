import re
from typing import Optional, List, Dict, Any
import httpx
from app.core.config import settings
from app.core.logs import logger


# System Prompts as specified by clinical guidelines & prompt design requirements
PATIENT_SPECIFIC_SYSTEM_PROMPT = """You are a healthcare assistant integrated into the MediSense Smart Healthcare Platform.
Answer the user's inquiry using only the provided patient-record context.
Strict Rules:
1. Do NOT invent or fabricate patient information, lab values, or medications.
2. If the requested information is not present in the provided context, clearly state that it is unavailable in the patient's records (e.g., "I couldn't find information regarding this in your available medical records.").
3. State clearly that you are providing informational guidance based on records, not a real-time medical diagnosis.
4. Keep the tone empathetic, concise, and professional."""


GENERAL_MEDICAL_SYSTEM_PROMPT = """You are a healthcare information assistant. Provide clear, accurate, and evidence-grounded general medical information.
Strict Rules:
1. Do not diagnose the user or claim that general information is a personal medical diagnosis.
2. If discussing symptoms or conditions, clearly recommend consulting a certified healthcare professional.
3. If red flag symptoms (e.g. sudden crushing chest pain, difficulty breathing, stroke symptoms) are described, urge immediate emergency medical care.
4. If you do not have sufficient information or knowledge to answer accurately, explicitly state that you do not have enough information."""


WIKIPEDIA_CONTEXT_SYSTEM_PROMPT = """You are a healthcare information assistant.
Use the supplied Wikipedia information as supporting context to answer the user's general medical inquiry.
Strict Rules:
1. Ground your explanation in the provided Wikipedia context. Do not fabricate facts that are not supported by the provided context.
2. If the information is insufficient, clearly state the limitation.
3. Do not diagnose the user or claim that general information is a personal diagnosis."""


INSUFFICIENT_RESPONSE_PATTERNS = [
    r"\bi\s+(do\s*not|don'?t)\s+(know|have\s+(enough\s+)?information|have\s+access)\b",
    r"\binsufficient\s+information\b",
    r"\b(cannot|can'?t|unable\s+to)\s+(answer|provide\s+(an\s+)?answer|find\s+information)\b",
    r"\bi\s+am\s+not\s+(sure|certain)\b",
    r"\bi'?m\s+not\s+(sure|certain)\b",
    r"\bno\s+information\s+(is\s+)?available\b",
    r"\bnot\s+enough\s+information\b",
    r"\boutside\s+my\s+knowledge\b",
    r"\bi\s+do\s+not\s+possess\b",
]


class OllamaService:
    """
    Service interfacing with local Ollama LLM instance with robust prompt templating and fallback detection.
    """

    def __init__(self, base_url: Optional[str] = None, model: Optional[str] = None):
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.model = model or getattr(settings, "OLLAMA_MODEL", "llama3.2")

    def build_patient_prompt(
        self,
        message: str,
        patient_context: str,
        history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """Build prompt for patient-specific medical record questions."""
        parts = [PATIENT_SPECIFIC_SYSTEM_PROMPT, ""]

        if patient_context.strip():
            parts.append("[AUTHENTICATED PATIENT MEDICAL RECORDS]")
            parts.append(patient_context.strip())
            parts.append("")
        else:
            parts.append("[AUTHENTICATED PATIENT MEDICAL RECORDS]")
            parts.append("No medical records or diagnostic reports found for this patient.")
            parts.append("")

        if history:
            parts.append("[CONVERSATION HISTORY]")
            for msg in history:
                role = "Patient" if msg.get("role") == "user" else "Assistant"
                parts.append(f"{role}: {msg.get('content', '')}")
            parts.append("")

        parts.append("[CURRENT QUESTION]")
        parts.append(f"User: {message}")
        parts.append("")
        parts.append("Assistant:")
        return "\n".join(parts)

    def build_general_prompt(
        self,
        message: str,
        history: Optional[List[Dict[str, str]]] = None,
        guidelines_chunks: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """Build prompt for general medical inquiries."""
        parts = [GENERAL_MEDICAL_SYSTEM_PROMPT, ""]

        if guidelines_chunks:
            parts.append("[CLINICAL GUIDELINES REFERENCE]")
            for i, chk in enumerate(guidelines_chunks, start=1):
                title = chk.get("document_title", "Guideline")
                sec = chk.get("section", "General")
                content = chk.get("content", "").strip()
                parts.append(f"Source {i}: {title} ({sec})\n{content}")
            parts.append("")

        if history:
            parts.append("[CONVERSATION HISTORY]")
            for msg in history:
                role = "User" if msg.get("role") == "user" else "Assistant"
                parts.append(f"{role}: {msg.get('content', '')}")
            parts.append("")

        parts.append("[CURRENT QUESTION]")
        parts.append(f"User: {message}")
        parts.append("")
        parts.append("Assistant:")
        return "\n".join(parts)

    def build_wikipedia_prompt(
        self,
        message: str,
        wikipedia_title: str,
        wikipedia_extract: str,
        history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """Build prompt for general medical queries augmented with Wikipedia reference context."""
        parts = [WIKIPEDIA_CONTEXT_SYSTEM_PROMPT, ""]

        parts.append(f"[EXTERNAL WIKIPEDIA REFERENCE: {wikipedia_title}]")
        parts.append(wikipedia_extract.strip())
        parts.append("")

        if history:
            parts.append("[CONVERSATION HISTORY]")
            for msg in history:
                role = "User" if msg.get("role") == "user" else "Assistant"
                parts.append(f"{role}: {msg.get('content', '')}")
            parts.append("")

        parts.append("[CURRENT QUESTION]")
        parts.append(f"User: {message}")
        parts.append("")
        parts.append("Assistant:")
        return "\n".join(parts)

    def is_insufficient_response(self, reply: str) -> bool:
        """
        Check if Ollama's response signals insufficient information or inability to answer.
        """
        if not reply or not reply.strip():
            return True

        text = reply.strip().lower()
        if len(text) < 25:
            # Very short replies like "I don't know" or "No info"
            return True

        for pat in INSUFFICIENT_RESPONSE_PATTERNS:
            if re.search(pat, text):
                logger.info(f"Detected insufficient knowledge signal in response: '{pat}'")
                return True

        return False

    async def generate(self, prompt: str, timeout: float = 120.0) -> str:
        """Send prompt to Ollama generation API and return generated text."""
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
        }

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.post(url, json=payload)
                resp.raise_for_status()
                data = resp.json()
                return data.get("response", "").strip()
        except httpx.ConnectError:
            logger.error(f"Ollama connection refused at {self.base_url}. Ensure 'ollama serve' is running.")
            raise
        except httpx.TimeoutException:
            logger.error(f"Ollama request timed out after {timeout}s.")
            raise
        except Exception as e:
            logger.error(f"Ollama generation error: {e}")
            raise


_ollama_instance: Optional[OllamaService] = None


def get_ollama_service() -> OllamaService:
    global _ollama_instance
    if _ollama_instance is None:
        _ollama_instance = OllamaService()
    return _ollama_instance
