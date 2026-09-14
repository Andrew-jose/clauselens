import uuid
import pytest
from app.services.validator import (
    normalize_text,
    compute_fuzzy_overlap,
    verify_citation_quote,
    validate_citations_against_db,
)
from app.services.verifier import strip_fabricated_citations, run_self_check_verifier
from app.models.entities import Chunk, AuditEvent, User, Document, GroundedStatus
from app.db.session import SessionLocal, init_db


@pytest.fixture(scope="module")
def db_session():
    init_db()
    db = SessionLocal()
    yield db
    db.close()


def test_normalize_text():
    raw = "  Tenant   shall pay   “$2,400.00” — on the 1st!  \n"
    norm = normalize_text(raw)
    assert norm == 'tenant shall pay "$2,400.00" - on the 1st!'


def test_exact_and_fuzzy_citation_verification():
    chunk_text = (
        "In the event Tenant elects to terminate this Agreement prior to the expiration of the full term, "
        "Tenant shall provide sixty (60) days' written notice and pay an early termination fee equivalent to "
        "two (2) months' rent ($4,800.00)."
    )

    # 1. Exact quote
    exact_quote = "Tenant shall provide sixty (60) days' written notice"
    is_valid, score = verify_citation_quote(exact_quote, chunk_text)
    assert is_valid is True
    assert score >= 0.95

    # 2. Quote with whitespace/punctuation variation (simulating OCR noise)
    noisy_quote = "Tenant  shall provide  sixty (60) days written notice"
    is_valid_noisy, score_noisy = verify_citation_quote(noisy_quote, chunk_text)
    assert is_valid_noisy is True
    assert score_noisy >= 0.90

    # 3. Completely fabricated quote (must fail!)
    fake_quote = "Tenant may terminate immediately without any penalty or notice period."
    is_valid_fake, score_fake = verify_citation_quote(fake_quote, chunk_text)
    assert is_valid_fake is False
    assert score_fake < 0.50


def test_validate_citations_against_db(db_session):
    # Setup test doc and chunk
    unique_email = f"test_validator_{uuid.uuid4().hex[:8]}@clauselens.ai"
    user = User(id=str(uuid.uuid4()), email=unique_email, password_hash="test")
    doc = Document(id=str(uuid.uuid4()), user_id=user.id, filename="test.pdf", mime_type="application/pdf")
    chunk = Chunk(
        id=str(uuid.uuid4()),
        document_id=doc.id,
        page_number=1,
        clause_id="9(a)",
        text="Tenant shall provide sixty (60) days' written notice and pay an early termination fee.",
    )
    db_session.add_all([user, doc, chunk])
    db_session.commit()

    # Case A: Authentic citation
    cits_valid = [{"chunk_id": chunk.id, "page": 1, "clause_id": "9(a)", "quote": "sixty (60) days' written notice"}]
    verified, failed, status = validate_citations_against_db(cits_valid, db_session, user.id, doc.id)
    assert len(verified) == 1
    assert len(failed) == 0
    assert status == GroundedStatus.GROUNDED_HIGH.value

    # Case B: Fabricated citation
    cits_invalid = [{"chunk_id": chunk.id, "page": 1, "clause_id": "9(a)", "quote": "landlord pays moving expenses"}]
    verified_bad, failed_bad, status_bad = validate_citations_against_db(cits_invalid, db_session, user.id, doc.id)
    assert len(verified_bad) == 0
    assert len(failed_bad) == 1
    assert status_bad == GroundedStatus.NOT_FOUND_IN_DOCUMENT.value

    # Verify audit event logged for failure
    audit = db_session.query(AuditEvent).filter(
        AuditEvent.user_id == user.id,
        AuditEvent.event_type == "validation_failure"
    ).first()
    assert audit is not None
    assert audit.metadata_json["failed_count"] == 1


def test_strip_fabricated_legal_citations():
    text_with_statutes = (
        "Under Cal. Civ. Code § 1950.5 and Smith v. Landlord, the security deposit must be returned within 21 days."
    )
    cleaned = strip_fabricated_citations(text_with_statutes)
    assert "§" not in cleaned
    assert "v." not in cleaned
    assert "Cal. Civ. Code" not in cleaned


def test_self_check_verifier():
    citations = [{"quote": "Tenant shall provide sixty (60) days' written notice"}]
    context = "Clause 8: Tenant shall provide sixty (60) days' written notice."

    # Grounded answer
    grounded_answer = "You are required to give sixty (60) days' written notice."
    is_grounded, unsupported = run_self_check_verifier(grounded_answer, citations, context)
    assert is_grounded is True
    assert len(unsupported) == 0

    # Answer containing completely foreign/unsupported claim
    unsupported_answer = "You are entitled to a full refund and free parking per municipal law."
    is_grounded_bad, unsupported_bad = run_self_check_verifier(unsupported_answer, citations, context)
    assert is_grounded_bad is False
    assert len(unsupported_bad) >= 1
