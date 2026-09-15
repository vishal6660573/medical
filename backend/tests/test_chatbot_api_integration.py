import os
import sys
from pathlib import Path

# Ensure backend directory is in sys.path
BASE_BACKEND = Path(__file__).resolve().parent.parent
if str(BASE_BACKEND) not in sys.path:
    sys.path.insert(0, str(BASE_BACKEND))

import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database.database import Base, get_db
from app.database.models import User, Patient, Medication, PredictionResult, UserRole, Gender, BloodGroup
from app.auth.jwt_handler import create_access_token
from services.wikipedia_service import WikipediaService, WikipediaResult
from services.ollama_service import OllamaService


@pytest.fixture
def api_test_db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSession()

    user = User(
        full_name="Sarah Connor",
        email="sarah@example.com",
        hashed_password="securepassword",
        role=UserRole.patient,
        is_active=True
    )
    db.add(user)
    db.flush()

    patient = Patient(
        user_id=user.id,
        date_of_birth="1990-03-15",
        gender=Gender.female,
        blood_group=BloodGroup.O_POS,
        allergies="Aspirin"
    )
    db.add(patient)
    db.flush()

    med = Medication(
        patient_id=patient.id,
        name="Amoxicillin",
        dosage="250mg",
        frequency="three times daily",
        duration="5 days",
        prescribed_by="Dr. Silberman",
        is_active=True
    )
    db.add(med)
    db.commit()

    try:
        yield db, user, patient
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(api_test_db):
    db, user, patient = api_test_db

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    test_client = TestClient(app)
    token = create_access_token(data={"sub": str(user.id), "role": user.role.value})
    test_client.headers["Authorization"] = f"Bearer {token}"
    yield test_client, user
    app.dependency_overrides.clear()


def test_api_chat_general_query(client):
    test_client, _ = client
    with patch.object(OllamaService, "generate", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = "Hypertension is high blood pressure exceeding 130/80 mmHg."

        resp = test_client.post(
            "/chatbot/chat",
            json={"message": "What is hypertension?", "history": []}
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["reply"] == "Hypertension is high blood pressure exceeding 130/80 mmHg."
        assert data["query_type"] == "GENERAL"
        assert data["source"] == "ollama"
        assert "sources" in data


def test_api_chat_patient_specific_query(client):
    test_client, user = client
    with patch.object(OllamaService, "generate", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = "According to your records, you are currently prescribed Amoxicillin 250mg."

        resp = test_client.post(
            "/chatbot/chat",
            json={"message": "What medications am I taking?", "history": []}
        )

        assert resp.status_code == 200
        data = resp.json()
        assert "Amoxicillin" in data["reply"]
        assert data["query_type"] == "PATIENT_SPECIFIC"
        assert data["source"] == "patient_rag+ollama"
        assert len(data["sources"]) > 0


def test_api_chat_wikipedia_fallback(client):
    test_client, _ = client
    ollama_responses = [
        "I do not know enough about this rare condition.",
        "Marfan syndrome is a genetic disorder that affects the body's connective tissue."
    ]
    wiki_res = WikipediaResult(
        title="Marfan syndrome",
        extract="Marfan syndrome is a multi-systemic genetic disorder that affects the connective tissue.",
        url="https://en.wikipedia.org/wiki/Marfan_syndrome"
    )

    with patch.object(OllamaService, "generate", side_effect=ollama_responses), \
         patch.object(WikipediaService, "search_and_summarize", new_callable=AsyncMock) as mock_wiki:

        mock_wiki.return_value = wiki_res

        resp = test_client.post(
            "/chatbot/chat",
            json={"message": "Explain Marfan syndrome.", "history": []}
        )

        assert resp.status_code == 200
        data = resp.json()
        assert "Marfan syndrome" in data["reply"]
        assert data["query_type"] == "GENERAL"
        assert data["source"] == "ollama+wikipedia"
        assert len(data["sources"]) == 1
        assert "Wikipedia" in data["sources"][0]["document_title"]


def test_api_chat_unauthenticated():
    unauth_client = TestClient(app)
    resp = unauth_client.post(
        "/chatbot/chat",
        json={"message": "What is hypertension?"}
    )
    assert resp.status_code == 401


def test_wikipedia_service_query_cleaning():
    service = WikipediaService()
    assert service._clean_query("What is diabetes?") == "diabetes"
    assert service._clean_query("What are the symptoms of pneumonia?") == "the symptoms of pneumonia"
    assert service._clean_query("Tell me about asthma!") == "asthma"
    assert service._clean_query("Explain hypertension...") == "hypertension"
