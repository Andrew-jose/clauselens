import io
import os
from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


@pytest.fixture
def sample_pdf_bytes():
    fixture_path = os.path.join(os.path.dirname(__file__), "..", "fixtures", "sample_lease.pdf")
    with open(fixture_path, "rb") as f:
        return f.read()


@pytest.fixture
def ready_document_id(sample_pdf_bytes):
    resp = client.post(
        "/api/documents",
        files={"file": ("resilience_lease.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf")},
    )
    assert resp.status_code == 201
    return resp.json()["id"]


def test_gemini_failure_during_qa_returns_safe_fallback(ready_document_id):
    """When Gemini API fails or times out during Q&A, system returns safe grounded fallback."""
    with patch("app.services.gemini_client.generate_structured_json") as mock_gemini:
        mock_gemini.side_effect = Exception("503 Service Unavailable: Gemini API rate limit reached")

        resp = client.post(
            f"/api/documents/{ready_document_id}/ask",
            json={"question": "What happens if rent is late?"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "answer" in data
        assert data["status"] in ["grounded_high", "grounded_low", "not_found_in_document", "general_info"]
        assert isinstance(data["citations"], list)


def test_gemini_failure_during_analysis_uses_deterministic_fallback(ready_document_id):
    """When Gemini fails during summarization/extraction, fallback pipeline generates verified data."""
    with patch("app.services.gemini_client.generate_structured_json") as mock_gemini:
        mock_gemini.side_effect = Exception("500 Internal Error from upstream LLM provider")

        resp = client.post(f"/api/documents/{ready_document_id}/analyze")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ready"
        assert data["clauses_count"] > 0
        assert data["findings_count"] > 0


def test_gemini_failure_during_comparison_uses_deterministic_fallback(ready_document_id, sample_pdf_bytes):
    """When Gemini Pro fails during comparison synthesis, deterministic pairwise comparison takes over."""
    # Upload second document
    resp2 = client.post(
        "/api/documents",
        files={"file": ("second_lease.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf")},
    )
    assert resp2.status_code == 201
    doc2_id = resp2.json()["id"]

    with patch("app.services.gemini_client.generate_structured_json") as mock_gemini:
        mock_gemini.side_effect = Exception("Gemini comparison synthesis timeout")

        comp_resp = client.post(
            "/api/compare",
            json={"document_a_id": ready_document_id, "document_b_id": doc2_id},
        )
        assert comp_resp.status_code == 201
        comp_data = comp_resp.json()
        assert comp_data["document_a_id"] == ready_document_id
        assert comp_data["document_b_id"] == doc2_id
        assert "findings" in comp_data


def test_chromadb_query_failure_falls_back_to_database_chunks(ready_document_id):
    """When ChromaDB vector query fails or is empty, retriever seamlessly falls back to SQLite chunks."""
    with patch("app.services.vector_store.search_chunks") as mock_vector_search:
        mock_vector_search.side_effect = Exception("ChromaDB socket closed")

        resp = client.post(
            f"/api/documents/{ready_document_id}/ask",
            json={"question": "What is the security deposit amount?"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "answer" in data


def test_chromadb_delete_failure_still_deletes_database_record(ready_document_id):
    """ChromaDB vector deletion errors do not abort document deletion from relational database."""
    with patch("app.services.vector_store.delete_document_vectors") as mock_delete:
        mock_delete.side_effect = Exception("ChromaDB index corrupted")

        del_resp = client.delete(f"/api/documents/{ready_document_id}")
        assert del_resp.status_code == 204

        # Document is deleted from SQLite
        get_resp = client.get(f"/api/documents/{ready_document_id}")
        assert get_resp.status_code == 404


def test_compare_document_with_itself_rejected():
    """Comparing a document against itself must return 400 or 422 Bad Request."""
    dummy_id = "00000000-0000-0000-0000-000000000001"
    resp = client.post(
        "/api/compare",
        json={"document_a_id": dummy_id, "document_b_id": dummy_id},
    )
    assert resp.status_code in [400, 422]
    assert "distinct" in str(resp.json()).lower() or "itself" in str(resp.json()).lower()


def test_compare_nonexistent_document_returns_404():
    """Comparing non-existent documents must return 404 Not Found."""
    resp = client.post(
        "/api/compare",
        json={
            "document_a_id": "00000000-0000-0000-0000-000000000001",
            "document_b_id": "00000000-0000-0000-0000-000000000002",
        },
    )
    assert resp.status_code == 404
