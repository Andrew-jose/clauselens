import os
import io
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.db.session import init_db, SessionLocal
from app.models.entities import AuditEvent, Document

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    init_db()


@pytest.fixture
def sample_pdf_bytes():
    fixture_path = os.path.join(os.path.dirname(__file__), "..", "fixtures", "sample_lease.pdf")
    with open(fixture_path, "rb") as f:
        return f.read()


def test_auth_registration_and_login_flow():
    unique_suffix = str(uuid.uuid4())[:8]
    email = f"user_{unique_suffix}@example.com"
    password = "SecurePassword123!"

    # 1. Register
    reg_resp = client.post(
        "/api/auth/register",
        json={"email": email, "password": password},
    )
    assert reg_resp.status_code == 201
    reg_data = reg_resp.json()
    assert "access_token" in reg_data
    assert reg_data["user"]["email"] == email

    # 2. Duplicate registration should return 400
    dup_resp = client.post(
        "/api/auth/register",
        json={"email": email, "password": password},
    )
    assert dup_resp.status_code == 400
    assert "already exists" in dup_resp.json()["detail"]

    # 3. Short password validation (< 6 chars)
    short_resp = client.post(
        "/api/auth/register",
        json={"email": f"short_{unique_suffix}@example.com", "password": "123"},
    )
    assert short_resp.status_code == 422

    # 4. Login with correct password
    login_resp = client.post(
        "/api/auth/login",
        json={"email": email, "password": password},
    )
    assert login_resp.status_code == 200
    login_data = login_resp.json()
    token = login_data["access_token"]
    assert token is not None

    # 5. Login with incorrect password returns 401
    bad_login = client.post(
        "/api/auth/login",
        json={"email": email, "password": "WrongPassword!"},
    )
    assert bad_login.status_code == 401

    # 6. Check /api/auth/me with valid Bearer token
    me_resp = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == email

    # 7. Check /api/auth/me without token returns 401
    unauth_resp = client.get("/api/auth/me")
    assert unauth_resp.status_code == 401

    # 8. Check /api/auth/me with malformed/tampered token returns 401
    bad_token_resp = client.get(
        "/api/auth/me",
        headers={"Authorization": "Bearer invalid.jwt.token"},
    )
    assert bad_token_resp.status_code == 401


def test_tenancy_isolation_and_cross_user_rejection(sample_pdf_bytes):
    """
    Assert that User B cannot access, read, ask, export, or delete User A's documents (returns 403 Forbidden).
    """
    uid_a = str(uuid.uuid4())[:8]
    email_a = f"tenant_a_{uid_a}@example.com"
    reg_a = client.post("/api/auth/register", json={"email": email_a, "password": "PasswordA123!"})
    token_a = reg_a.json()["access_token"]

    uid_b = str(uuid.uuid4())[:8]
    email_b = f"tenant_b_{uid_b}@example.com"
    reg_b = client.post("/api/auth/register", json={"email": email_b, "password": "PasswordB123!"})
    token_b = reg_b.json()["access_token"]

    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # User A uploads a document
    upload_resp = client.post(
        "/api/documents",
        headers=headers_a,
        files={"file": ("lease_a.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf")},
    )
    assert upload_resp.status_code == 201
    doc_a_id = upload_resp.json()["id"]

    # User A can access their own document
    assert client.get(f"/api/documents/{doc_a_id}", headers=headers_a).status_code == 200

    # User B attempts to access Document A -> 403 Forbidden on all routes
    assert client.get(f"/api/documents/{doc_a_id}", headers=headers_b).status_code == 403
    assert client.get(f"/api/documents/{doc_a_id}/status", headers=headers_b).status_code == 403
    assert client.get(f"/api/documents/{doc_a_id}/chunks", headers=headers_b).status_code == 403
    assert client.get(f"/api/documents/{doc_a_id}/clauses", headers=headers_b).status_code == 403
    assert client.get(f"/api/documents/{doc_a_id}/findings", headers=headers_b).status_code == 403
    assert client.post(f"/api/documents/{doc_a_id}/analyze", headers=headers_b).status_code == 403
    assert client.post(
        f"/api/documents/{doc_a_id}/ask",
        headers=headers_b,
        json={"question": "What is the rent?"},
    ).status_code == 403
    assert client.post(
        f"/api/documents/{doc_a_id}/situation",
        headers=headers_b,
        json={"context_text": "Moving out"},
    ).status_code == 403
    assert client.get(f"/api/documents/{doc_a_id}/action-plan", headers=headers_b).status_code == 403
    assert client.get(f"/api/documents/{doc_a_id}/lawyer-questions", headers=headers_b).status_code == 403
    assert client.get(f"/api/documents/{doc_a_id}/export", headers=headers_b).status_code == 403
    assert client.delete(f"/api/documents/{doc_a_id}", headers=headers_b).status_code == 403

    # User B uploads their own Document B
    upload_b = client.post(
        "/api/documents",
        headers=headers_b,
        files={"file": ("lease_b.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf")},
    )
    assert upload_b.status_code == 201
    doc_b_id = upload_b.json()["id"]

    # User B attempts to compare Document A (owned by User A) with Document B -> 403 Forbidden
    compare_resp = client.post(
        "/api/compare",
        headers=headers_b,
        json={"document_a_id": doc_a_id, "document_b_id": doc_b_id},
    )
    assert compare_resp.status_code == 403

    # Non-existent document returns 404
    non_existent_id = str(uuid.uuid4())
    assert client.get(f"/api/documents/{non_existent_id}", headers=headers_a).status_code == 404

    # User A successfully cleans up Document A
    del_resp = client.delete(f"/api/documents/{doc_a_id}", headers=headers_a)
    assert del_resp.status_code == 204


def test_malicious_executable_upload_rejection():
    """
    Test that a Windows executable (.exe) or malicious file renamed to .pdf
    is rejected via magic-byte inspection (HTTP 415).
    """
    exe_header_content = b"MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\xff\xff\x00\x00This is an executable payload"
    resp = client.post(
        "/api/documents",
        files={"file": ("exploit.pdf", io.BytesIO(exe_header_content), "application/pdf")},
    )
    assert resp.status_code == 415
    assert "Unsupported or invalid file format" in resp.json()["detail"]


def test_oversized_file_upload_rejection():
    """
    Test that files exceeding MAX_UPLOAD_SIZE_BYTES (15 MB) are rejected with HTTP 413.
    """
    # 16 MB payload
    oversized_bytes = b"%PDF-1.5\n" + (b"0" * (16 * 1024 * 1024))
    resp = client.post(
        "/api/documents",
        files={"file": ("oversized.pdf", io.BytesIO(oversized_bytes), "application/pdf")},
    )
    assert resp.status_code == 413
    assert "File exceeds maximum allowed size" in resp.json()["detail"]


def test_audit_logging_recorded(sample_pdf_bytes):
    """
    Verify that key user operations (register, login, upload, delete) create persistent AuditEvent records.
    """
    uid = str(uuid.uuid4())[:8]
    email = f"audited_user_{uid}@example.com"
    reg = client.post("/api/auth/register", json={"email": email, "password": "AuditPassword123!"})
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Upload
    upload = client.post(
        "/api/documents",
        headers=headers,
        files={"file": ("audit_lease.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf")},
    )
    doc_id = upload.json()["id"]

    # Delete
    client.delete(f"/api/documents/{doc_id}", headers=headers)

    # Check DB for audit events
    db: Session = SessionLocal()
    try:
        events = db.query(AuditEvent).filter(AuditEvent.user_id == reg.json()["user"]["id"]).all()
        event_types = [e.event_type for e in events]
        assert "auth_register" in event_types
        assert "upload" in event_types
        assert "delete" in event_types
    finally:
        db.close()


def test_rate_limiting_triggers_429():
    """
    Verify slowapi rate-limiting blocks rapid requests with HTTP 429.
    """
    from app.core.rate_limit import limiter
    limiter.enabled = True
    try:
        statuses = []
        for i in range(15):
            resp = client.post(
                "/api/auth/register",
                json={"email": f"ratelimit_{i}_{uuid.uuid4().hex[:6]}@example.com", "password": "Password123!"},
            )
            statuses.append(resp.status_code)

        assert 429 in statuses
    finally:
        limiter.enabled = False


def test_cors_preflight_and_origin_policy():
    """
    T3: Verify CORS preflight OPTIONS request returns expected headers and respects origin policy.
    """
    # Allowed origin preflight
    headers = {
        "Origin": "http://localhost:5173",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "Authorization, Content-Type",
    }
    resp = client.options("/api/documents", headers=headers)
    assert resp.status_code == 200
    assert resp.headers.get("access-control-allow-origin") == "http://localhost:5173"
    allowed_methods = resp.headers.get("access-control-allow-methods", "")
    assert "POST" in allowed_methods

    # Disallowed origin
    bad_headers = {
        "Origin": "http://untrusted-attacker-site.com",
        "Access-Control-Request-Method": "POST",
    }
    bad_resp = client.options("/api/documents", headers=bad_headers)
    assert bad_resp.headers.get("access-control-allow-origin") != "http://untrusted-attacker-site.com"



