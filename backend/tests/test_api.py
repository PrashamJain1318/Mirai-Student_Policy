"""
API Endpoint tests using FastAPI TestClient (Phase 7).
"""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from backend import app
from app.rag_chain import PolicyAnswer


@pytest.fixture
def client():
    return TestClient(app)


def test_get_root(client):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Autonomous MirAI Student Policy Advisor API"
    assert data["status"] == "online"


def test_get_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "handbook_file_present" in data
    assert "vector_store_initialized" in data


def test_chat_uninitialized_returns_503(client):
    with patch("backend.vector_store_manager.is_initialized", return_value=False):
        response = client.post("/chat", json={"question": "What is the attendance policy?"})
        assert response.status_code == 503
        data = response.json()
        assert "not initialized" in data["detail"].lower()


def test_chat_validation_too_short(client):
    response = client.post("/chat", json={"question": "hi"})
    assert response.status_code == 422  # Pydantic validation error


def test_chat_successful_response(client):
    with patch("backend.vector_store_manager.is_initialized", return_value=True):
        mock_answer = PolicyAnswer(
            answer="According to Page 5, attendance requires 75%.",
            sources=[{
                "document": "Mirai_SoT_Policy_Handbook_2026.pdf",
                "page": 5,
                "excerpt": "75% attendance rule",
                "chunk_id": "c1",
            }],
            sub_queries=["attendance", "attendance percentage"],
            abstained=False,
        )
        with patch("backend.advisor_chain.answer_question", return_value=mock_answer):
            response = client.post("/chat", json={"question": "What is the attendance rule?"})
            assert response.status_code == 200
            data = response.json()
            assert data["answer"] == "According to Page 5, attendance requires 75%."
            assert len(data["sources"]) == 1
            assert data["sources"][0]["page"] == 5
            assert data["abstained"] is False


def test_ingest_empty_file_fails(client):
    response = client.post(
        "/ingest",
        files={"file": ("empty.pdf", b"", "application/pdf")},
    )
    assert response.status_code == 400
