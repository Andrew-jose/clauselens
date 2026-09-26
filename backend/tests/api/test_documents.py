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


def test_upload_valid_lease_pdf(sample_pdf_bytes):
    response = client.post(
        "/api/documents",
        files={"file": ("sample_lease.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf")},
    )
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["filename"] == "sample_lease.pdf"
    assert data["status"] == "ready"
    assert data["page_count"] >= 1

    doc_id = data["id"]

    # Verify status polling
    status_resp = client.get(f"/api/documents/{doc_id}/status")
    assert status_resp.status_code == 200
    status_data = status_resp.json()
    assert status_data["status"] == "ready"
    assert status_data["chunks_count"] >= 5

    # Verify detail
    detail_resp = client.get(f"/api/documents/{doc_id}")
    assert detail_resp.status_code == 200
    detail_data = detail_resp.json()
    assert detail_data["id"] == doc_id
    assert detail_data["chunks_count"] >= 5

    # Verify chunks endpoint
    chunks_resp = client.get(f"/api/documents/{doc_id}/chunks")
    assert chunks_resp.status_code == 200
    chunks_list = chunks_resp.json()
    assert len(chunks_list) >= 5

    # Verify deletion
    del_resp = client.delete(f"/api/documents/{doc_id}")
    assert del_resp.status_code == 204

    # Verify 404 after deletion
    get_after = client.get(f"/api/documents/{doc_id}")
    assert get_after.status_code == 404


def test_upload_invalid_magic_bytes():
    fake_content = b"Not a real PDF despite header"
    response = client.post(
        "/api/documents",
        files={"file": ("malicious.pdf", io.BytesIO(fake_content), "application/pdf")},
    )
    assert response.status_code == 415
    assert "Unsupported or invalid file format" in response.json()["detail"]


def test_list_documents(sample_pdf_bytes):
    # Upload one document
    upload_resp = client.post(
        "/api/documents",
        files={"file": ("sample_lease.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf")},
    )
    assert upload_resp.status_code == 201
    doc_id = upload_resp.json()["id"]

    list_resp = client.get("/api/documents")
    assert list_resp.status_code == 200
    docs = list_resp.json()
    assert len(docs) >= 1
    assert any(d["id"] == doc_id for d in docs)

    # Clean up
    client.delete(f"/api/documents/{doc_id}")


def test_upload_empty_whitespace_pdf():
    """T1: Verify uploading a valid PDF with zero text / only whitespace succeeds gracefully."""
    import fitz
    doc = fitz.open()
    doc.new_page()  # creates blank page
    pdf_bytes = doc.tobytes()
    doc.close()

    resp = client.post(
        "/api/documents",
        files={"file": ("empty_lease.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "ready"
    assert data["page_count"] == 1
    doc_id = data["id"]

    # Verify chunks are created safely
    chunks_resp = client.get(f"/api/documents/{doc_id}/chunks")
    assert chunks_resp.status_code == 200
    assert len(chunks_resp.json()) >= 1

    # Cleanup
    client.delete(f"/api/documents/{doc_id}")


def test_duplicate_document_upload(sample_pdf_bytes):
    """T2: Verify concurrent/duplicate uploads of the same file are isolated with distinct IDs."""
    resp1 = client.post(
        "/api/documents",
        files={"file": ("sample_lease.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf")},
    )
    assert resp1.status_code == 201
    doc1_id = resp1.json()["id"]

    resp2 = client.post(
        "/api/documents",
        files={"file": ("sample_lease.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf")},
    )
    assert resp2.status_code == 201
    doc2_id = resp2.json()["id"]

    # Both documents should exist independently
    assert doc1_id != doc2_id

    # Verify both can be retrieved
    assert client.get(f"/api/documents/{doc1_id}").status_code == 200
    assert client.get(f"/api/documents/{doc2_id}").status_code == 200

    # Cleanup
    client.delete(f"/api/documents/{doc1_id}")
    client.delete(f"/api/documents/{doc2_id}")
