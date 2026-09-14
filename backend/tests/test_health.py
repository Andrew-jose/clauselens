from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "ClauseLens" in data["message"]


def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "ClauseLens"
    assert "version" in data


def test_gemini_health_unconfigured():
    response = client.get("/api/health/gemini")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["ok", "unconfigured"]
    assert "flash_model" in data or "model" in data
