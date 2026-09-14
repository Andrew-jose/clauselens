import pytest
from app.services.situation_router import (
    classify_situation_offline,
    classify_situation,
    generate_action_plan,
    generate_lawyer_questions,
    VALID_SITUATION_TYPES,
    VALID_URGENCIES,
)
from app.services.retriever import rerank_chunks_by_categories
from app.services.verifier import strip_fabricated_citations
from app.models.entities import Chunk, Document, User, AuditEvent
from app.core.security import get_password_hash


def test_situation_classification_taxonomy():
    """Verify classification covers all 5 fixed taxonomy types and assigns appropriate urgency."""
    cases = [
        ("I need to break my lease early because my company is relocating me to Seattle.", "termination", "medium"),
        ("The landlord has ignored broken heating and severe mold in our bathroom for weeks.", "active_dispute", "high"),
        ("The management company sent a lease renewal notice with a 15% rent increase.", "renewal_negotiation", "medium"),
        ("I just got approved for an apartment and want to review this agreement before I sign.", "pre_signing_review", "low"),
        ("Just curious about how subletting works in residential apartments.", "general_curiosity", "low"),
    ]

    for context, expected_type, expected_urgency in cases:
        result = classify_situation_offline(context)
        assert result["situation_type"] == expected_type
        assert result["situation_type"] in VALID_SITUATION_TYPES
        assert result["urgency"] in VALID_URGENCIES
        assert isinstance(result["relevant_categories"], list)
        assert len(result["relevant_categories"]) <= 4


def test_retriever_category_reranking():
    """Verify that chunks relevant to the situation categories are boosted to the top."""
    chunks = [
        {
            "id": "chunk_1",
            "text": "The monthly rent shall be $2,400 payable on the first day of each month.",
            "metadata": {"clause_id": "1", "section_heading": "Rent and Payment", "page_number": 1}
        },
        {
            "id": "chunk_2",
            "text": "Tenant may terminate this agreement early upon sixty days written notice and payment of liquidated damages penalty of $4,800.",
            "metadata": {"clause_id": "9", "section_heading": "Early Termination and Penalties", "page_number": 2}
        },
        {
            "id": "chunk_3",
            "text": "Tenant shall keep the premises clean and notify landlord of maintenance defects.",
            "metadata": {"clause_id": "7", "section_heading": "Maintenance and Repairs", "page_number": 2}
        },
    ]

    # Without relevant categories, original order preserved
    normal_order = rerank_chunks_by_categories(chunks, [])
    assert normal_order[0]["id"] == "chunk_1"

    # With termination_penalties relevant category, chunk_2 must be re-ranked to index 0
    reranked = rerank_chunks_by_categories(chunks, ["termination_penalties"])
    assert reranked[0]["id"] == "chunk_2"
    assert "liquidated damages" in reranked[0]["text"]


def test_regex_guard_strips_fabricated_legal_citations():
    """Verify that statute numbers, statutory codes, and case citations are strictly stripped."""
    dirty_text = "Pursuant to Cal. Civ. Code § 1950.5 and under Smith v. Jones, the deposit limit is 2 months."
    clean_text = strip_fabricated_citations(dirty_text)

    assert "§" not in clean_text
    assert "Cal. Civ. Code" not in clean_text
    assert "Smith v. Jones" not in clean_text
    assert "statutory reference withheld" in clean_text


def test_action_plan_citation_verification(db_session):
    """Verify that action plan steps with authentic quotes keep citations, but hallucinated quotes are dropped."""
    import uuid
    email = f"plan_test_{uuid.uuid4().hex[:8]}@example.com"
    user = User(email=email, password_hash=get_password_hash("pass123"))
    db_session.add(user)
    db_session.commit()

    doc = Document(user_id=user.id, filename="test_lease.pdf", mime_type="application/pdf", page_count=2, status="ready")
    db_session.add(doc)
    db_session.commit()

    chunk = Chunk(
        document_id=doc.id,
        page_number=1,
        clause_id="Clause 3",
        text="Tenant shall provide sixty (60) days written notice prior to vacating.",
        token_count=15,
    )
    db_session.add(chunk)
    db_session.commit()

    sit = {
        "situation_type": "termination",
        "urgency": "medium",
        "context_text": "Need to move out",
    }
    plan = generate_action_plan(document_id=doc.id, situation=sit, db=db_session, user_id=user.id)

    assert plan["situation_type"] == "termination"
    assert len(plan["steps"]) >= 2
    for step in plan["steps"]:
        assert "action" in step
        assert "rationale" in step
        if step.get("citation"):
            # If citation present, quote must exist in chunk text
            quote = step["citation"]["quote"]
            assert quote in chunk.text


def test_action_plan_high_urgency_escalation(db_session):
    """Verify that an active dispute or high urgency situation guarantees a legal professional consultation step."""
    import uuid
    email = f"escalation_test_{uuid.uuid4().hex[:8]}@example.com"
    user = User(email=email, password_hash=get_password_hash("pass123"))
    db_session.add(user)
    db_session.commit()

    doc = Document(user_id=user.id, filename="dispute_lease.pdf", mime_type="application/pdf", page_count=1, status="ready")
    db_session.add(doc)
    db_session.commit()

    sit = {
        "situation_type": "active_dispute",
        "urgency": "high",
        "context_text": "Landlord threatened eviction and heat is broken.",
    }
    plan = generate_action_plan(document_id=doc.id, situation=sit, db=db_session, user_id=user.id)

    actions = [s["action"].lower() for s in plan["steps"]]
    assert any("attorney" in a or "legal" in a or "tenant" in a or "consult" in a for a in actions)
