import io
import os
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_security_headers_present_on_responses():
    """Defensive HTTP security headers must be attached to all responses."""
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.headers.get("X-Content-Type-Options") == "nosniff"
    assert resp.headers.get("X-Frame-Options") == "DENY"
    assert "strict-origin" in resp.headers.get("Referrer-Policy", "")


def test_root_endpoint():
    """Root endpoint must provide welcoming metadata and docs URLs."""
    resp = client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert "Welcome to ClauseLens API" in data["message"]
    assert "docs_url" in data
    assert "health_url" in data


def test_input_validation_registration_bounds():
    """Registration must enforce email and password length limits."""
    # Email too long (> 255 chars)
    long_email = "a" * 250 + "@example.com"
    resp = client.post("/api/auth/register", json={"email": long_email, "password": "Password123!"})
    assert resp.status_code == 422

    # Password too long (> 128 chars)
    long_pwd = "P" * 130 + "!"
    resp2 = client.post("/api/auth/register", json={"email": "valid@example.com", "password": long_pwd})
    assert resp2.status_code == 422

    # Password too short (< 6 chars)
    short_pwd = "123"
    resp3 = client.post("/api/auth/register", json={"email": "valid2@example.com", "password": short_pwd})
    assert resp3.status_code == 422


def test_input_validation_situation_bounds():
    """Situation context text must enforce bounds (3 to 5000 chars)."""
    # Context too short (< 3 chars)
    resp = client.post(
        "/api/documents/00000000-0000-0000-0000-000000000001/situation",
        json={"context_text": "hi"},
    )
    assert resp.status_code == 422

    # Context too long (> 5000 chars)
    oversized_context = "I need help with my lease. " * 300
    resp2 = client.post(
        "/api/documents/00000000-0000-0000-0000-000000000001/situation",
        json={"context_text": oversized_context},
    )
    assert resp2.status_code == 422


def test_input_validation_qa_bounds():
    """Q&A question text must enforce bounds (2 to 1000 chars)."""
    # Question too short (< 2 chars)
    resp = client.post(
        "/api/documents/00000000-0000-0000-0000-000000000001/ask",
        json={"question": "?"},
    )
    assert resp.status_code == 422

    # Question too long (> 1000 chars)
    oversized_question = "What is the policy on " + ("pets " * 250) + "?"
    resp2 = client.post(
        "/api/documents/00000000-0000-0000-0000-000000000001/ask",
        json={"question": oversized_question},
    )
    assert resp2.status_code == 422


def test_invalid_json_body_returns_422():
    """Malformed JSON bodies must return 422 Unprocessable Entity."""
    resp = client.post(
        "/api/auth/login",
        content="not valid json",
        headers={"Content-Type": "application/json"},
    )
    assert resp.status_code == 422


def test_nonexistent_route_returns_404():
    """Requests to unmapped endpoints must return 404."""
    resp = client.get("/api/nonexistent_endpoint")
    assert resp.status_code == 404
