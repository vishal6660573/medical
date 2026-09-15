import os
import sys
from pathlib import Path

# Ensure backend directory is in sys.path
BASE_BACKEND = Path(__file__).resolve().parent.parent
if str(BASE_BACKEND) not in sys.path:
    sys.path.insert(0, str(BASE_BACKEND))

import json
import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.database import Base
from app.database.models import User, Patient, Visit, Medication, PredictionResult, UserRole, Gender, BloodGroup
from services.query_router import classify_query, QueryType
from services.patient_rag_service import get_patient_rag_service, PatientRAGService
from services.wikipedia_service import WikipediaService, WikipediaResult, get_wikipedia_service
from services.ollama_service import OllamaService, get_ollama_service
from services.chatbot_service import chat_with_medibot, ChatbotResult


@pytest.fixture
def in_memory_db():
    """Create an isolated in-memory SQLite database for testing."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def sample_data(in_memory_db):
    """Seed sample data for Patient A and Patient B to test multi-tenant separation."""
    db = in_memory_db

    # Patient A
    user_a = User(
        full_name="Alice Johnson",
        email="alice@example.com",
        hashed_password="hashedpasswordA",
        role=UserRole.patient,
        is_active=True
    )
    db.add(user_a)
    db.flush()

    patient_a = Patient(
        user_id=user_a.id,
        date_of_birth="1985-05-12",
        gender=Gender.female,
        blood_group=BloodGroup.A_POS,
        allergies="Penicillin",
    )
    db.add(patient_a)
    db.flush()

    # Patient A Medication: Metformin 500mg
    med_a = Medication(
        patient_id=patient_a.id,
        name="Metformin",
        dosage="500mg",
        frequency="twice daily",
        duration="ongoing",
        prescribed_by="Dr. Gregory House",
        is_active=True,
        notes="For Type 2 Diabetes management"
    )
    db.add(med_a)

    # Patient A Visit
    visit_a = Visit(
        patient_id=patient_a.id,
        chief_complaint="Routine diabetes checkup",
        diagnosis="Type 2 Diabetes mellitus",
        notes="Blood glucose monitored regularly. HbA1c target 6.5%.",
        follow_up_date="2026-10-01"
    )
    db.add(visit_a)

    # Patient A Lab/Prediction (HbA1c = 6.8%, Glucose = 142)
    pred_a = PredictionResult(
        patient_id=patient_a.id,
        prediction_type="diabetes",
        probability=0.74,
        risk_level="High",
        input_data=json.dumps({"Glucose": 142, "HbA1c": 6.8, "BloodPressure": 120, "BMI": 27.4}),
        result_summary=json.dumps({"disease": "diabetes", "recommendation": "Maintain diet and take Metformin as directed."})
    )
    db.add(pred_a)

    # ─────────────────────────────────────────────────────────────
    # Patient B
    # ─────────────────────────────────────────────────────────────
    user_b = User(
        full_name="Bob Smith",
        email="bob@example.com",
        hashed_password="hashedpasswordB",
        role=UserRole.patient,
        is_active=True
    )
    db.add(user_b)
    db.flush()

    patient_b = Patient(
        user_id=user_b.id,
        date_of_birth="1978-11-20",
        gender=Gender.male,
        blood_group=BloodGroup.O_POS,
        allergies="Sulfa drugs",
    )
    db.add(patient_b)
    db.flush()

    # Patient B Medication: Lisinopril 10mg & Atorvastatin 20mg
    med_b1 = Medication(
        patient_id=patient_b.id,
        name="Lisinopril",
        dosage="10mg",
        frequency="daily",
        duration="ongoing",
        prescribed_by="Dr. Allison Cameron",
        is_active=True,
        notes="For hypertension"
    )
    med_b2 = Medication(
        patient_id=patient_b.id,
        name="Atorvastatin",
        dosage="20mg",
        frequency="at bedtime",
        duration="ongoing",
        prescribed_by="Dr. Allison Cameron",
        is_active=True,
        notes="For hyperlipidemia"
    )
    db.add_all([med_b1, med_b2])

    # Patient B Prediction (Heart disease risk)
    pred_b = PredictionResult(
        patient_id=patient_b.id,
        prediction_type="heart",
        probability=0.82,
        risk_level="High",
        input_data=json.dumps({"age": 48, "cholesterol": 240, "trestbps": 145}),
        result_summary=json.dumps({"disease": "heart disease", "recommendation": "Low sodium diet and lipid management."})
    )
    db.add(pred_b)

    db.commit()
    return {
        "user_a": user_a,
        "patient_a": patient_a,
        "user_b": user_b,
        "patient_b": patient_b
    }


# ─────────────────────────────────────────────────────────────
# Test 1: General query -> GENERAL -> Ollama -> No patient retrieval
# ─────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_1_general_medical_query_diabetes_symptoms(in_memory_db, sample_data):
    """
    Question: 'What are the symptoms of diabetes?'
    Expected: GENERAL -> Ollama -> no patient-history retrieval
    """
    question = "What are the symptoms of diabetes?"
    classification = classify_query(question)
    assert classification.query_type == QueryType.GENERAL

    user_a = sample_data["user_a"]

    with patch.object(OllamaService, "generate", new_callable=AsyncMock) as mock_generate, \
         patch.object(PatientRAGService, "retrieve_patient_context") as mock_patient_rag:

        mock_generate.return_value = (
            "Common symptoms of diabetes include increased thirst (polydipsia), "
            "frequent urination (polyuria), unintended weight loss, and fatigue."
        )

        res = await chat_with_medibot(
            message=question,
            history=[],
            current_user=user_a,
            db=in_memory_db
        )

        assert res.query_type == "GENERAL"
        assert res.source == "ollama"
        assert "increased thirst" in res.reply
        # Ensure patient RAG service was NEVER called for this general medical inquiry
        mock_patient_rag.assert_not_called()


# ─────────────────────────────────────────────────────────────
# Test 2: Patient-specific query -> PATIENT_SPECIFIC -> Patient RAG -> Ollama
# ─────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_2_patient_specific_medications(in_memory_db, sample_data):
    """
    Question: 'What medications am I taking?'
    Expected: PATIENT_SPECIFIC -> patient RAG -> Ollama
    """
    question = "What medications am I currently taking?"
    classification = classify_query(question)
    assert classification.query_type == QueryType.PATIENT_SPECIFIC

    user_a = sample_data["user_a"]

    with patch.object(OllamaService, "generate", new_callable=AsyncMock) as mock_generate:
        mock_generate.return_value = (
            "According to your available medical records, you are currently prescribed Metformin 500mg (twice daily)."
        )

        res = await chat_with_medibot(
            message=question,
            history=[],
            current_user=user_a,
            db=in_memory_db
        )

        assert res.query_type == "PATIENT_SPECIFIC"
        assert res.source == "patient_rag+ollama"
        assert "Metformin" in res.reply
        assert len(res.sources) > 0

        # Verify the prompt sent to Ollama contained Patient A's Metformin
        call_args = mock_generate.call_args[0][0]
        assert "Metformin" in call_args
        assert "Alice Johnson" in call_args
        # Verify it did NOT contain Patient B's Lisinopril
        assert "Lisinopril" not in call_args


# ─────────────────────────────────────────────────────────────
# Test 3: Patient-specific query -> HbA1c records
# ─────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_3_patient_specific_hba1c(in_memory_db, sample_data):
    """
    Question: 'What was my previous HbA1c?'
    Expected: PATIENT_SPECIFIC -> patient RAG -> Ollama
    """
    question = "What was my previous HbA1c?"
    classification = classify_query(question)
    assert classification.query_type == QueryType.PATIENT_SPECIFIC

    user_a = sample_data["user_a"]

    with patch.object(OllamaService, "generate", new_callable=AsyncMock) as mock_generate:
        mock_generate.return_value = (
            "According to your latest diabetes report, your recorded HbA1c was 6.8% with blood glucose of 142 mg/dL."
        )

        res = await chat_with_medibot(
            message=question,
            history=[],
            current_user=user_a,
            db=in_memory_db
        )

        assert res.query_type == "PATIENT_SPECIFIC"
        assert res.source == "patient_rag+ollama"
        assert "6.8%" in res.reply

        call_args = mock_generate.call_args[0][0]
        assert "HbA1c: 6.8" in call_args


# ─────────────────────────────────────────────────────────────
# Test 4: General query -> 'What is pneumonia?'
# ─────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_4_general_query_pneumonia(in_memory_db, sample_data):
    """
    Question: 'What is pneumonia?'
    Expected: GENERAL -> Ollama
    """
    question = "What is pneumonia?"
    classification = classify_query(question)
    assert classification.query_type == QueryType.GENERAL

    user_b = sample_data["user_b"]

    with patch.object(OllamaService, "generate", new_callable=AsyncMock) as mock_generate, \
         patch.object(PatientRAGService, "retrieve_patient_context") as mock_patient_rag:

        mock_generate.return_value = (
            "Pneumonia is an inflammatory infection affecting the air sacs (alveoli) in one or both lungs, "
            "commonly caused by bacteria, viruses, or fungi."
        )

        res = await chat_with_medibot(
            message=question,
            history=[],
            current_user=user_b,
            db=in_memory_db
        )

        assert res.query_type == "GENERAL"
        assert res.source == "ollama"
        assert "alveoli" in res.reply
        mock_patient_rag.assert_not_called()


# ─────────────────────────────────────────────────────────────
# Test 5: General query where Ollama indicates insufficient info -> Wikipedia Fallback
# ─────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_5_general_query_wikipedia_fallback(in_memory_db, sample_data):
    """
    General query where Ollama indicates insufficient information.
    Expected: GENERAL -> Ollama -> Wikipedia fallback -> Ollama with Wikipedia context -> final response
    """
    question = "Tell me about Takotsubo cardiomyopathy."
    classification = classify_query(question)
    assert classification.query_type == QueryType.GENERAL

    user_a = sample_data["user_a"]

    # First Ollama call returns insufficient info signal; second call uses Wikipedia context
    ollama_mock_replies = [
        "I do not have enough information to answer this question accurately.",
        "Takotsubo cardiomyopathy, also known as broken heart syndrome, is a temporary heart condition often triggered by severe emotional or physical stress."
    ]

    wiki_result = WikipediaResult(
        title="Takotsubo cardiomyopathy",
        extract="Takotsubo cardiomyopathy is a type of non-ischemic cardiomyopathy in which there is a sudden temporary weakening of the muscular portion of the heart.",
        url="https://en.wikipedia.org/wiki/Takotsubo_cardiomyopathy"
    )

    with patch.object(OllamaService, "generate", side_effect=ollama_mock_replies) as mock_generate, \
         patch.object(WikipediaService, "search_and_summarize", new_callable=AsyncMock) as mock_wiki:

        mock_wiki.return_value = wiki_result

        res = await chat_with_medibot(
            message=question,
            history=[],
            current_user=user_a,
            db=in_memory_db
        )

        assert res.query_type == "GENERAL"
        assert res.source == "ollama+wikipedia"
        assert "broken heart syndrome" in res.reply
        assert len(res.sources) == 1
        assert "Wikipedia: Takotsubo cardiomyopathy" in res.sources[0]["document_title"]

        # Ensure Wikipedia search was triggered
        mock_wiki.assert_called_once_with(question)
        # Ensure Ollama was called twice (first raw, second with Wikipedia context)
        assert mock_generate.call_count == 2
        second_prompt = mock_generate.call_args_list[1][0][0]
        assert "EXTERNAL WIKIPEDIA REFERENCE: Takotsubo cardiomyopathy" in second_prompt


# ─────────────────────────────────────────────────────────────
# Test 6: Patient-specific question where no relevant patient record exists
# ─────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_6_patient_specific_no_records(in_memory_db):
    """
    Patient-specific question for a patient with no previous records/tests.
    Expected: PATIENT_SPECIFIC -> safe 'not found in available records' response without hallucination.
    """
    db = in_memory_db
    # Create empty patient with no visits, meds, or lab tests
    empty_user = User(
        full_name="New Patient",
        email="newpatient@example.com",
        hashed_password="hash",
        role=UserRole.patient,
        is_active=True
    )
    db.add(empty_user)
    db.flush()

    empty_patient = Patient(
        user_id=empty_user.id,
        date_of_birth=None,
        gender=None,
        blood_group=None,
        allergies=None
    )
    db.add(empty_patient)
    db.commit()

    question = "What medications was I prescribed previously?"
    classification = classify_query(question)
    assert classification.query_type == QueryType.PATIENT_SPECIFIC

    with patch.object(OllamaService, "generate", new_callable=AsyncMock) as mock_generate:
        mock_generate.return_value = (
            "I couldn't find any medication records for you in your available medical history."
        )

        res = await chat_with_medibot(
            message=question,
            history=[],
            current_user=empty_user,
            db=db
        )

        assert res.query_type == "PATIENT_SPECIFIC"
        assert res.source == "patient_rag+ollama"
        assert "couldn't find" in res.reply.lower() or "not found" in res.reply.lower()

        call_args = mock_generate.call_args[0][0]
        # Verify that prompt indicates no records found
        assert "No medical records" in call_args or "None recorded" in call_args


# ─────────────────────────────────────────────────────────────
# Test 7: Strict multi-tenant isolation — Patient A cannot retrieve Patient B's records
# ─────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_7_patient_isolation_security(in_memory_db, sample_data):
    """
    Verify Patient A can NEVER retrieve Patient B's records and vice-versa.
    """
    user_a = sample_data["user_a"]
    user_b = sample_data["user_b"]
    patient_a = sample_data["patient_a"]
    patient_b = sample_data["patient_b"]

    patient_rag = get_patient_rag_service()

    # Retrieve context for Patient A
    rag_a = patient_rag.retrieve_patient_context(patient_id=patient_a.id, db=in_memory_db)
    # Retrieve context for Patient B
    rag_b = patient_rag.retrieve_patient_context(patient_id=patient_b.id, db=in_memory_db)

    # 1. Patient A context must contain Metformin and Type 2 Diabetes, NEVER Lisinopril or Atorvastatin
    assert "Metformin" in rag_a.context_text
    assert "Type 2 Diabetes" in rag_a.context_text
    assert "Lisinopril" not in rag_a.context_text
    assert "Atorvastatin" not in rag_a.context_text
    assert "Bob Smith" not in rag_a.context_text

    # 2. Patient B context must contain Lisinopril and Atorvastatin, NEVER Metformin
    assert "Lisinopril" in rag_b.context_text
    assert "Atorvastatin" in rag_b.context_text
    assert "Metformin" not in rag_b.context_text
    assert "Alice Johnson" not in rag_b.context_text


# ─────────────────────────────────────────────────────────────
# Test 8: Wikipedia Service Network Failure Graceful Fallback
# ─────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_8_wikipedia_service_error_handling(in_memory_db, sample_data):
    """
    If Wikipedia search fails or raises network error, fallback gracefully to initial Ollama reply.
    """
    question = "What is Epstein-Barr virus?"
    user_a = sample_data["user_a"]

    initial_reply = "I do not have enough information to provide full details on this topic."

    with patch.object(OllamaService, "generate", new_callable=AsyncMock) as mock_generate, \
         patch.object(WikipediaService, "search_and_summarize", new_callable=AsyncMock) as mock_wiki:

        mock_generate.return_value = initial_reply
        # Wikipedia service returns None due to network failure / error
        mock_wiki.return_value = None

        res = await chat_with_medibot(
            message=question,
            history=[],
            current_user=user_a,
            db=in_memory_db
        )

        assert res.query_type == "GENERAL"
        # Should gracefully return the original response with source="ollama"
        assert res.source == "ollama"
        assert res.reply == initial_reply


# ─────────────────────────────────────────────────────────────
# Test 9: Query Router classification accuracy on diverse inputs
# ─────────────────────────────────────────────────────────────
def test_9_query_router_comprehensive():
    """
    Test accuracy of router across various patient-specific and general prompts.
    """
    patient_queries = [
        "What medications am I currently taking?",
        "What was my previous HbA1c?",
        "What diseases have I been diagnosed with?",
        "Show me my previous medical history.",
        "What did my previous report say?",
        "Do I have any allergies recorded in my file?",
        "What was prescribed to me on my last visit?",
        "Tell me about my test results.",
        "According to my records, what is my blood group?",
    ]

    for q in patient_queries:
        res = classify_query(q)
        assert res.query_type == QueryType.PATIENT_SPECIFIC, f"Failed on query: '{q}' -> got {res.query_type}"

    general_queries = [
        "What are the symptoms of diabetes?",
        "What is hypertension?",
        "What causes pneumonia?",
        "What is the difference between Type 1 and Type 2 diabetes?",
        "How does insulin lower blood glucose?",
        "What is asthma?",
        "Explain coronary artery disease.",
    ]

    for q in general_queries:
        res = classify_query(q)
        assert res.query_type == QueryType.GENERAL, f"Failed on query: '{q}' -> got {res.query_type}"
