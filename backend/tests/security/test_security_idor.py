import io
import os
import uuid
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


@pytest.fixture
def sample_pdf_bytes():
    fixture_path = os.path.join(os.path.dirname(__file__), "..", "fixtures", "sample_lease.pdf")
    with open(fixture_path, "rb") as f:
        return f.read()


def register_and_get_token(email: str, password: str = "SecurePass123!") -> str:
    resp = client.post("/api/auth/register", json={"email": email, "password": password})
    assert resp.status_code == 201
    return resp.json()["access_token"]


def test_complete_idor_protection_across_all_document_endpoints(sample_pdf_bytes):
    """
    Exhaustive IDOR & Tenant Isolation Test:
    Ensures that User B cannot access, read, analyze, ask questions about,
    or delete any resource owned by User A.
    """
    user_a_email = f"tenant_a_{uuid.uuid4().hex[:6]}@example.com"
    user_b_email = f"tenant_b_{uuid.uuid4().hex[:6]}@example.com"

    token_a = register_and_get_token(user_a_email)
    token_b = register_and_get_token(user_b_email)

    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # 1. User A uploads Document A
    upload_resp = client.post(
        "/api/documents",
        headers=headers_a,
        files={"file": ("lease_a.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf")},
    )
    assert upload_resp.status_code == 201
    doc_a_id = upload_resp.json()["id"]

    # 2. User B document list does NOT contain Document A
    list_b = client.get("/api/documents", headers=headers_b)
    assert list_b.status_code == 200
    assert not any(d["id"] == doc_a_id for d in list_b.json())

    # 3. User B cannot access Document A metadata
    get_resp = client.get(f"/api/documents/{doc_a_id}", headers=headers_b)
    assert get_resp.status_code == 403

    # 4. User B cannot access Document A status
    status_resp = client.get(f"/api/documents/{doc_a_id}/status", headers=headers_b)
    assert status_resp.status_code == 403

    # 5. User B cannot access Document A chunks
    chunks_resp = client.get(f"/api/documents/{doc_a_id}/chunks", headers=headers_b)
    assert chunks_resp.status_code == 403

    # 6. User B cannot access Document A clauses
    clauses_resp = client.get(f"/api/documents/{doc_a_id}/clauses", headers=headers_b)
    assert clauses_resp.status_code == 403

    # 7. User B cannot access Document A findings
    findings_resp = client.get(f"/api/documents/{doc_a_id}/findings", headers=headers_b)
    assert findings_resp.status_code == 403

    # 8. User B cannot trigger analysis on Document A
    analyze_resp = client.post(f"/api/documents/{doc_a_id}/analyze", headers=headers_b)
    assert analyze_resp.status_code == 403

    # 9. User B cannot ask questions against Document A
    ask_resp = client.post(
        f"/api/documents/{doc_a_id}/ask",
        headers=headers_b,
        json={"question": "What is the monthly rent?"},
    )
    assert ask_resp.status_code == 403

    # 10. User B cannot submit a situation against Document A
    situation_resp = client.post(
        f"/api/documents/{doc_a_id}/situation",
        headers=headers_b,
        json={"context_text": "I lost my job and need to break my lease."},
    )
    assert situation_resp.status_code == 403

    # 11. User B cannot get action plan for Document A
    plan_resp = client.get(f"/api/documents/{doc_a_id}/action-plan", headers=headers_b)
    assert plan_resp.status_code == 403

    # 12. User B cannot get lawyer questions for Document A
    questions_resp = client.get(f"/api/documents/{doc_a_id}/lawyer-questions", headers=headers_b)
    assert questions_resp.status_code == 403

    # 13. User B cannot export PDF of Document A
    export_resp = client.get(f"/api/documents/{doc_a_id}/export", headers=headers_b)
    assert export_resp.status_code == 403

    # 14. User B uploads Document B, but cannot compare Document A and Document B
    upload_b = client.post(
        "/api/documents",
        headers=headers_b,
        files={"file": ("lease_b.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf")},
    )
    assert upload_b.status_code == 201
    doc_b_id = upload_b.json()["id"]

    compare_resp = client.post(
        "/api/compare",
        headers=headers_b,
        json={"document_a_id": doc_a_id, "document_b_id": doc_b_id},
    )
    assert compare_resp.status_code == 403

    # 15. User A runs a comparison between Doc A and another Doc A2 owned by User A
    upload_a2 = client.post(
        "/api/documents",
        headers=headers_a,
        files={"file": ("lease_a2.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf")},
    )
    assert upload_a2.status_code == 201
    doc_a2_id = upload_a2.json()["id"]

    compare_a = client.post(
        "/api/compare",
        headers=headers_a,
        json={"document_a_id": doc_a_id, "document_b_id": doc_a2_id},
    )
    assert compare_a.status_code == 201
    comp_session_id = compare_a.json()["id"]

    # User B cannot access User A's comparison session
    comp_get_b = client.get(f"/api/compare/{comp_session_id}", headers=headers_b)
    assert comp_get_b.status_code == 403

    # 16. User A starts a Q&A conversation
    ask_a = client.post(
        f"/api/documents/{doc_a_id}/ask",
        headers=headers_a,
        json={"question": "What is the penalty for early termination?"},
    )
    assert ask_a.status_code == 200
    conv_id = ask_a.json()["conversation_id"]

    # User B cannot access User A's conversation
    conv_get_b = client.get(f"/api/conversations/{conv_id}", headers=headers_b)
    assert conv_get_b.status_code == 403

    # 17. User B cannot delete Document A
    delete_b = client.delete(f"/api/documents/{doc_a_id}", headers=headers_b)
    assert delete_b.status_code == 403

    # Document A still exists and is accessible by User A
    get_a = client.get(f"/api/documents/{doc_a_id}", headers=headers_a)
    assert get_a.status_code == 200
