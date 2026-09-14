import os
import io
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import init_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    init_db()


@pytest.fixture
def sample_pdf_bytes():
    fixture_path = os.path.join(os.path.dirname(__file__), "..", "fixtures", "sample_lease.pdf")
    with open(fixture_path, "rb") as f:
        return f.read()


@pytest.fixture
def uploaded_doc_id(sample_pdf_bytes):
    resp = client.post(
        "/api/documents",
        files={"file": ("sample_lease.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf")},
    )
    assert resp.status_code == 201
    doc_id = resp.json()["id"]
    yield doc_id
    client.delete(f"/api/documents/{doc_id}")


def test_get_clauses_endpoint(uploaded_doc_id):
    resp = client.get(f"/api/documents/{uploaded_doc_id}/clauses")
    assert resp.status_code == 200
    clauses = resp.json()
    assert len(clauses) >= 5

    # Verify fields
    first = clauses[0]
    assert "id" in first
    assert "category" in first
    assert "summary" in first
    assert "quote" in first
    assert first["page_number"] >= 1

    # Filter by category
    rent_resp = client.get(f"/api/documents/{uploaded_doc_id}/clauses?category=rent_fees")
    assert rent_resp.status_code == 200
    rent_clauses = rent_resp.json()
    assert len(rent_clauses) >= 1
    assert all(c["category"] == "rent_fees" for c in rent_clauses)


def test_get_findings_endpoint(uploaded_doc_id):
    resp = client.get(f"/api/documents/{uploaded_doc_id}/findings")
    assert resp.status_code == 200
    findings = resp.json()
    assert len(findings) >= 1

    # Verify finding properties
    for f in findings:
        assert f["severity"] in ["low", "medium", "high"]
        assert f["type"] in ["risk", "obligation", "inconsistency"]
        assert len(f["title"]) > 3
        assert len(f["plain_explanation"]) > 10
        assert f["verified"] is True
        assert len(f["quote"]) > 0

    # Filter by high severity
    high_resp = client.get(f"/api/documents/{uploaded_doc_id}/findings?severity=high")
    assert high_resp.status_code == 200
    high_findings = high_resp.json()
    assert len(high_findings) >= 1
    assert all(f["severity"] == "high" for f in high_findings)
    assert any("Termination" in f["title"] or "Early" in f["title"] for f in high_findings)


def test_post_analyze_endpoint(uploaded_doc_id):
    resp = client.post(f"/api/documents/{uploaded_doc_id}/analyze")
    assert resp.status_code == 200
    data = resp.json()
    assert data["document_id"] == uploaded_doc_id
    assert data["status"] == "ready"
    assert data["clauses_count"] >= 5
    assert data["findings_count"] >= 1
    assert "summary" in data
