import os
try:
    import pymupdf as fitz
except ImportError:
    import fitz
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import init_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    init_db()


@pytest.fixture
def sample_doc_id():
    fixtures_dir = os.path.join(os.path.dirname(__file__), "..", "fixtures")
    p = os.path.join(fixtures_dir, "sample_lease.pdf")

    with open(p, "rb") as f:
        resp = client.post(
            "/api/documents",
            files={"file": ("sample_lease.pdf", f, "application/pdf")},
        )
    assert resp.status_code == 201
    doc_id = resp.json()["id"]

    yield doc_id

    # Clean up
    client.delete(f"/api/documents/{doc_id}")


def test_situation_submission(sample_doc_id):
    """Test submitting tenant situation context returns classified type and relevant categories."""
    payload = {
        "context_text": "I might need to leave early because of a job transfer in 3 months."
    }
    resp = client.post(f"/api/documents/{sample_doc_id}/situation", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    assert data["situation_type"] == "termination"
    assert data["urgency"] in ["medium", "high"]
    assert isinstance(data["relevant_categories"], list)
    assert "termination_penalties" in data["relevant_categories"] or "term_renewal" in data["relevant_categories"]


def test_action_plan_generation_and_retrieval(sample_doc_id):
    """Test retrieving and generating situation-tailored action plan."""
    # First submit situation
    client.post(
        f"/api/documents/{sample_doc_id}/situation",
        json={"context_text": "I need to break my lease early."}
    )

    resp = client.get(f"/api/documents/{sample_doc_id}/action-plan")
    assert resp.status_code == 200
    data = resp.json()

    assert data["document_id"] == sample_doc_id
    assert data["situation_type"] == "termination"
    assert len(data["steps"]) >= 2

    for step in data["steps"]:
        assert step["order"] > 0
        assert len(step["action"]) > 5
        assert len(step["rationale"]) > 5
        # Ensure no hallucinated statute citations
        assert "§" not in step["action"]
        assert "Civ. Code" not in step["action"]


def test_lawyer_questions_endpoint(sample_doc_id):
    """Test retrieving topic-grouped lawyer consultation questions."""
    resp = client.get(f"/api/documents/{sample_doc_id}/lawyer-questions")
    assert resp.status_code == 200
    data = resp.json()

    assert data["document_id"] == sample_doc_id
    assert len(data["questions"]) >= 1

    for q in data["questions"]:
        assert len(q["topic"]) > 0
        assert len(q["question"]) > 10
        assert q["priority"] in ["low", "medium", "high"]
        # Non-negotiable: check no fabricated statute/case citations
        assert "§" not in q["question"]
        assert "Civ. Code" not in q["question"]
        assert " v. " not in q["question"]


def test_export_lawyer_prep_pdf(sample_doc_id):
    """Test exporting branded lawyer-consultation PDF packet and verify its structure."""
    # Ensure a situation is submitted so the situation banner renders
    client.post(
        f"/api/documents/{sample_doc_id}/situation",
        json={"context_text": "I need to terminate early due to job relocation."}
    )

    resp = client.get(f"/api/documents/{sample_doc_id}/export")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/pdf"
    assert "attachment; filename=" in resp.headers.get("content-disposition", "")

    content = resp.content
    assert content.startswith(b"%PDF-")
    assert len(content) > 1000

    # Parse and inspect generated PDF using PyMuPDF
    pdf_doc = fitz.open(stream=content, filetype="pdf")
    assert pdf_doc.page_count >= 1

    full_text = ""
    for page in pdf_doc:
        full_text += page.get_text()

    assert "ClauseLens" in full_text
    assert "Lawyer Consultation Preparation Packet" in full_text
    assert "Prioritized Risk Radar" in full_text
    assert "Action Plan Checklist" in full_text
    assert "ClauseLens provides information, not legal advice" in full_text
