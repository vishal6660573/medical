import re
import enum
from typing import Optional
from pydantic import BaseModel
from app.core.logs import logger


class QueryType(str, enum.Enum):
    PATIENT_SPECIFIC = "PATIENT_SPECIFIC"
    GENERAL = "GENERAL"


class QueryClassification(BaseModel):
    query_type: QueryType
    confidence: float
    reason: str


# Explicit patterns for patient health record queries
PATIENT_SPECIFIC_PATTERNS = [
    # 1. First-person possessive + medical records / tests / vitals / history
    r"\bmy\s+(medication|medications|meds|medicine|medicines|prescription|prescriptions|dose|dosage|pills)\b",
    r"\bmy\s+(hba1c|glucose|blood\s*sugar|sugar\s*level|blood\s*pressure|bp|cholesterol|vitals|bmi|pulse|heart\s*rate)\b",
    r"\bmy\s+(diagnosis|diagnoses|condition|disease|diseases|illness|disorder|health|medical\s*history|records|record|charts|profile)\b",
    r"\bmy\s+(report|reports|test|tests|test\s*results|lab|labs|lab\s*results|xray|x-ray|scan|mri|ct|findings)\b",
    r"\bmy\s+(doctor|dr|physician|visit|visits|consultation|appointment|follow-up|notes)\b",
    r"\bmy\s+(allergy|allergies|blood\s*group|dob|date\s*of\s*birth|age)\b",

    # 2. Direct first-person record questions
    r"\bwhat\s+(medication|medications|medicine|medicines|drugs?|prescriptions?)\s+(am\s+i|was\s+i|have\s+i|do\s+i)\b",
    r"\bwhat\s+(am\s+i|was\s+i|have\s+i\s+been)\s+(currently\s+|previously\s+)?(prescribed|taking|given|diagnosed\s+with|on)\b",
    r"\bwhat\s+diseases?\s+(have\s+i|was\s+i|am\s+i)\s+(been\s+)?diagnosed\s+with\b",
    r"\bwhat\s+(is|was|are|were)\s+my\s+",
    r"\bshow\s+(me\s+)?(my\s+)?(previous\s+|past\s+)?(medical\s+history|records?|reports?|medications?|prescriptions?)\b",
    r"\btell\s+me\s+(about\s+)?my\s+",
    r"\bdo\s+i\s+have\s+(any\s+)?(allergies|medications|history|records)\b",
    r"\bam\s+i\s+(prescribed|taking|allergic)\b",
    r"\bprescribed\s+(to|for)\s+me\b",
    r"\baccording\s+to\s+my\s+(records|history|file|charts|profile|reports?)\b",
    r"\bin\s+my\s+(records|history|file|charts|profile|reports?|file)\b",
    r"\bdid\s+my\s+(doctor|report|test|results?)\s+say\b",
    r"\bwhat\s+did\s+my\s+(previous\s+|last\s+)?(report|records?|test|doctor)\s+say\b",
]

# Explicit patterns for purely general medical knowledge
GENERAL_MEDICAL_PATTERNS = [
    r"^what\s+(is|are|causes|can\s+cause)\s+([a-z0-9\s\-]+)\??$",
    r"^what\s+are\s+the\s+(symptoms|causes|treatments|risks|side\s*effects|types)\s+of\s+",
    r"^what\s+is\s+the\s+difference\s+between\s+",
    r"^(how|why)\s+(does|do|is|are|can)\s+",
    r"^(explain|describe|define)\s+",
    r"^can\s+([a-z0-9\s\-]+)\s+cause\s+",
    r"^tell\s+me\s+about\s+(diabetes|hypertension|pneumonia|asthma|covid|heart\s*disease|stroke|cancer|[a-z]+)\??$",
]


def classify_query(message: str) -> QueryClassification:
    """
    Classify incoming query into PATIENT_SPECIFIC or GENERAL.
    Uses pattern matching and intent analysis with safe default to GENERAL.
    """
    if not message or not message.strip():
        return QueryClassification(
            query_type=QueryType.GENERAL,
            confidence=1.0,
            reason="Empty query defaulted to GENERAL"
        )

    clean_msg = message.strip().lower()

    # 1. Check for explicit Patient Specific patterns
    for pattern in PATIENT_SPECIFIC_PATTERNS:
        if re.search(pattern, clean_msg):
            logger.info(f"Query routed to PATIENT_SPECIFIC (matched pattern: {pattern})")
            return QueryClassification(
                query_type=QueryType.PATIENT_SPECIFIC,
                confidence=0.95,
                reason=f"Matched patient record query pattern: {pattern}"
            )

    # 2. Check for general medical phrasing
    for pattern in GENERAL_MEDICAL_PATTERNS:
        if re.search(pattern, clean_msg):
            # Double check that it does not contain first-person self-references
            if not re.search(r"\b(my|mine|me|i\s+am|i'm|am\s+i|was\s+i)\b", clean_msg):
                logger.info(f"Query routed to GENERAL (matched general pattern: {pattern})")
                return QueryClassification(
                    query_type=QueryType.GENERAL,
                    confidence=0.90,
                    reason=f"Matched general medical knowledge pattern: {pattern}"
                )

    # 3. Keyword co-occurrence checks for patient record context
    first_person = bool(re.search(r"\b(my|me|mine|myself|i|i'm|i've|i'd|am\s+i|was\s+i|have\s+i|did\s+i)\b", clean_msg))
    medical_record_terms = bool(re.search(
        r"\b(medication|medications|meds|medicine|medicines|prescription|prescriptions|prescribed|taking|"
        r"hba1c|glucose|blood\s*sugar|bp|blood\s*pressure|cholesterol|vitals|"
        r"diagnosis|diagnoses|diagnosed|report|reports|test\s*results?|results?|doctor|visit|visits|"
        r"history|medical\s*history|records?|allergies|allergy|allergic|xray|x-ray)\b",
        clean_msg
    ))

    if first_person and medical_record_terms:
        logger.info("Query routed to PATIENT_SPECIFIC (first-person + record terms)")
        return QueryClassification(
            query_type=QueryType.PATIENT_SPECIFIC,
            confidence=0.88,
            reason="Detected first-person pronouns co-occurring with medical record terms"
        )

    # 4. Safe default: GENERAL to protect patient confidentiality and avoid unnecessary database queries
    logger.info("Query defaulted to GENERAL")
    return QueryClassification(
        query_type=QueryType.GENERAL,
        confidence=0.75,
        reason="Defaulted to GENERAL (no patient-specific indicators detected)"
    )
