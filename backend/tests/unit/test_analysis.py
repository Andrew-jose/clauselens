import uuid
import pytest
from app.models.entities import User, Document, Chunk, ClauseCategory, SeverityLevel
from app.services.analysis import map_category_string, analyze_document
from app.db.session import SessionLocal, init_db


@pytest.fixture(scope="module")
def db_session():
    init_db()
    db = SessionLocal()
    yield db
    db.close()


def test_map_category_string():
    assert map_category_string("rent") == ClauseCategory.RENT_FEES
    assert map_category_string("monthly rent & fees") == ClauseCategory.RENT_FEES
    assert map_category_string("term_renewal") == ClauseCategory.TERM_RENEWAL
    assert map_category_string("early termination") == ClauseCategory.TERMINATION_PENALTIES
    assert map_category_string("habitability repairs") == ClauseCategory.REPAIRS_HABITABILITY
    assert map_category_string("random unknown category") == ClauseCategory.OTHER


def test_analyze_document_unit(db_session):
    unique_email = f"test_analysis_{uuid.uuid4().hex[:8]}@clauselens.ai"
    user = User(id=str(uuid.uuid4()), email=unique_email, password_hash="test")
    doc = Document(id=str(uuid.uuid4()), user_id=user.id, filename="lease.pdf", mime_type="application/pdf")

    # Add sample chunks representing rent and termination
    c1 = Chunk(
        id=str(uuid.uuid4()),
        document_id=doc.id,
        page_number=1,
        clause_id="3",
        section_heading="Clause 3. Rent and Fees",
        text="Tenant agrees to pay monthly rent in the amount of $2,400.00 on the first day of each month.",
    )
    c2 = Chunk(
        id=str(uuid.uuid4()),
        document_id=doc.id,
        page_number=1,
        clause_id="9(a)",
        section_heading="Clause 9(a). Early Termination and Penalties",
        text="Tenant shall provide sixty (60) days' written notice and pay an early termination fee equivalent to two (2) months' rent ($4,800.00).",
    )
    db_session.add_all([user, doc, c1, c2])
    db_session.commit()

    # Run analysis
    result = analyze_document(doc.id, db_session)
    assert result["clauses_count"] >= 2
    assert result["findings_count"] >= 1
    assert "summary" in result
    assert len(result["key_terms"]) > 0

    # Verify clauses in DB
    clauses = doc.clauses
    assert len(clauses) >= 2
    categories = [c.category for c in clauses]
    assert ClauseCategory.RENT_FEES in categories
    assert ClauseCategory.TERMINATION_PENALTIES in categories

    # Verify findings in DB
    findings = doc.findings
    assert len(findings) >= 1
    high_risks = [f for f in findings if f.severity == SeverityLevel.HIGH]
    assert len(high_risks) >= 1
    assert "Early Termination" in high_risks[0].title
    assert high_risks[0].verified is True
