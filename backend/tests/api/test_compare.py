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
def doc_a_and_b_ids():
    fixtures_dir = os.path.join(os.path.dirname(__file__), "..", "fixtures")
    p1 = os.path.join(fixtures_dir, "sample_lease.pdf")
    p2 = os.path.join(fixtures_dir, "sample_lease_renewal.pdf")

    with open(p1, "rb") as f1, open(p2, "rb") as f2:
        resp1 = client.post(
            "/api/documents",
            files={"file": ("sample_lease.pdf", f1, "application/pdf")},
        )
        resp2 = client.post(
            "/api/documents",
            files={"file": ("sample_lease_renewal.pdf", f2, "application/pdf")},
        )

    assert resp1.status_code == 201
    assert resp2.status_code == 201

    doc_a_id = resp1.json()["id"]
    doc_b_id = resp2.json()["id"]

    yield doc_a_id, doc_b_id

    # Clean up
    client.delete(f"/api/documents/{doc_a_id}")
    client.delete(f"/api/documents/{doc_b_id}")


def test_compare_leases_delta_table(doc_a_and_b_ids):
    doc_a_id, doc_b_id = doc_a_and_b_ids

    resp = client.post(
        "/api/compare",
        json={"document_a_id": doc_a_id, "document_b_id": doc_b_id},
    )
    assert resp.status_code == 201
    data = resp.json()

    assert data["document_a_id"] == doc_a_id
    assert data["document_b_id"] == doc_b_id
    assert data["deltas_count"] >= 2
    assert len(data["findings"]) >= 2

    findings = data["findings"]

    # 1. Early termination finding check
    term_finding = next((f for f in findings if f["category"] == "termination_penalties" and f["severity"] == "high"), None)
    if not term_finding:
        term_finding = next((f for f in findings if f["category"] == "termination_penalties"), None)
    assert term_finding is not None
    assert term_finding["severity"] == "high"
    assert term_finding["favors"] in ["landlord", "unclear"]
    assert "three (3) months" in term_finding["delta_description"] or "penalty" in term_finding["delta_description"].lower()

    # Verify both citations
    cit_a = term_finding["doc_a_citation"]
    cit_b = term_finding["doc_b_citation"]
    assert cit_a is not None
    assert cit_b is not None
    assert cit_a["verified"] is True
    assert cit_b["verified"] is True
    assert "two" in cit_a["quote"].lower() or "4,800" in cit_a["quote"]
    assert "three" in cit_b["quote"].lower() or "7,950" in cit_b["quote"]

    # 2. Rent finding check
    rent_finding = next((f for f in findings if f["category"] == "rent_fees"), None)
    assert rent_finding is not None
    assert rent_finding["severity"] in ["medium", "low"]
    assert "2,650" in rent_finding["delta_description"] or "increase" in rent_finding["delta_description"].lower()
    assert rent_finding["doc_a_citation"]["verified"] is True
    assert rent_finding["doc_b_citation"]["verified"] is True

    # 3. Verify GET comparison session
    session_id = data["id"]
    get_resp = client.get(f"/api/compare/{session_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == session_id
    assert get_resp.json()["deltas_count"] == data["deltas_count"]
