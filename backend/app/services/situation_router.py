import json
import logging
import re
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session

from app.config import settings
from app.models.entities import (
    Document,
    Finding,
    Chunk,
    Clause,
    ActionPlan,
    Question,
    SeverityLevel,
    AuditEvent,
    utc_now,
)
from app.services.gemini_client import generate_structured_json
from app.services.prompts.situation import (
    SITUATION_SYSTEM_PROMPT,
    ACTION_PLAN_SYSTEM_PROMPT,
    LAWYER_QUESTION_SYSTEM_PROMPT,
    format_situation_prompt,
    format_action_plan_prompt,
    format_lawyer_questions_prompt,
)
from app.services.validator import verify_citation_quote
from app.services.verifier import strip_fabricated_citations

logger = logging.getLogger(__name__)

VALID_SITUATION_TYPES = {
    "pre_signing_review",
    "active_dispute",
    "termination",
    "renewal_negotiation",
    "general_curiosity",
}

VALID_URGENCIES = {"low", "medium", "high"}


def classify_situation_offline(context_text: str) -> Dict[str, Any]:
    """
    Deterministic rule-based situation classifier for offline/test mode.
    Classifies tenant's plain language situation into fixed taxonomy + urgency.
    """
    text_lower = context_text.lower()

    # 0. General Curiosity (when explicitly stated and not urgent)
    curiosity_signals = ["curious", "curiosity", "just wondering", "general question"]
    if any(sig in text_lower for sig in curiosity_signals) and not any(urgent in text_lower for urgent in ["broken", "threat", "dispute", "court", "mold", "relocat", "break lease"]):
        return {
            "situation_type": "general_curiosity",
            "urgency": "low",
            "relevant_categories": ["rent_fees", "restrictions"],
        }

    # 1. Active Dispute
    dispute_signals = [
        "dispute", "broken", "heat", "withhold", "court", "threat",
        "refusing", "landlord won't", "mold", "infestation", "leak",
        "pest", "unsafe", "violation", "sue", "lawyer", "evict",
        "uninhabitable", "harass"
    ]
    if any(sig in text_lower for sig in dispute_signals):
        high_signals = ["court", "threat", "heat", "mold", "unsafe", "evict", "uninhabitable"]
        urgency = "high" if any(h in text_lower for h in high_signals) else "medium"
        return {
            "situation_type": "active_dispute",
            "urgency": urgency,
            "relevant_categories": ["repairs_habitability", "access_privacy", "restrictions"],
        }

    # 2. Termination / Move Out
    termination_signals = [
        "leave early", "relocate", "relocating", "break", "break lease",
        "moving out", "end lease", "move out", "sublet", "terminate",
        "job transfer", "moving", "leaving"
    ]
    if any(sig in text_lower for sig in termination_signals):
        urgency = "high" if ("immediate" in text_lower or "urgent" in text_lower or "2 days" in text_lower) else "medium"
        return {
            "situation_type": "termination",
            "urgency": urgency,
            "relevant_categories": ["termination_penalties", "term_renewal", "deposit"],
        }

    # 3. Renewal Negotiation
    renewal_signals = [
        "renewal", "increase", "rent hike", "negotiate", "renew",
        "higher rent", "offering", "new term", "renewal offer"
    ]
    if any(sig in text_lower for sig in renewal_signals):
        return {
            "situation_type": "renewal_negotiation",
            "urgency": "medium",
            "relevant_categories": ["rent_fees", "term_renewal"],
        }

    # 4. Pre-Signing Review
    pre_signing_signals = [
        "before i sign", "signing", "prospective", "about to sign",
        "new lease", "review before", "just got a lease", "check this lease",
        "considering", "look over"
    ]
    if any(sig in text_lower for sig in pre_signing_signals):
        return {
            "situation_type": "pre_signing_review",
            "urgency": "low",
            "relevant_categories": ["rent_fees", "deposit", "restrictions", "termination_penalties"],
        }

    # 5. General Curiosity default
    return {
        "situation_type": "general_curiosity",
        "urgency": "low",
        "relevant_categories": ["rent_fees", "restrictions"],
    }


def classify_situation(context_text: str) -> Dict[str, Any]:
    """
    Classify tenant context into exactly one situation type, urgency, and relevant categories.
    Uses Gemini Flash if configured, else deterministic offline fallback.
    """
    if settings.GEMINI_API_KEY and settings.GEMINI_API_KEY != "your_gemini_api_key_here":
        try:
            user_prompt = format_situation_prompt(context_text)
            parsed = generate_structured_json(
                system_prompt=SITUATION_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                model_name=settings.GEMINI_FLASH_MODEL,
                temperature=0.0,
            )
            sit_type = parsed.get("situation_type", "general_curiosity").lower().strip()
            urgency = parsed.get("urgency", "low").lower().strip()
            categories = parsed.get("relevant_categories", [])

            if sit_type not in VALID_SITUATION_TYPES:
                sit_type = "general_curiosity"
            if urgency not in VALID_URGENCIES:
                urgency = "low"
            if not isinstance(categories, list):
                categories = []

            return {
                "situation_type": sit_type,
                "urgency": urgency,
                "relevant_categories": categories[:4],
            }
        except Exception as e:
            logger.warning(f"Gemini situation classification failed: {e}. Falling back to offline classifier.")

    return classify_situation_offline(context_text)


def generate_action_plan(
    document_id: str,
    situation: Dict[str, Any],
    db: Session,
    user_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Generate an ordered, concrete action plan tailored to tenant's situation and findings.
    Enforces strict code-level citation validation on every step and escalation for high urgency.
    """
    findings = db.query(Finding).filter(Finding.document_id == document_id).all()
    findings_data = [
        {
            "id": f.id,
            "title": f.title,
            "severity": f.severity.value if hasattr(f.severity, "value") else str(f.severity),
            "explanation": f.plain_explanation,
            "quote": f.quote,
            "page": f.page_number,
        }
        for f in findings
    ]

    situation_type = situation.get("situation_type", "general_curiosity")
    urgency = situation.get("urgency", "low")
    context_text = situation.get("context_text", "")

    candidate_steps = []

    # Attempt Gemini generation if key is present
    if settings.GEMINI_API_KEY and settings.GEMINI_API_KEY != "your_gemini_api_key_here":
        try:
            user_prompt = format_action_plan_prompt(situation, findings_data)
            parsed = generate_structured_json(
                system_prompt=ACTION_PLAN_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                model_name=settings.GEMINI_FLASH_MODEL,
                temperature=0.1,
            )
            candidate_steps = parsed.get("steps", [])
        except Exception as e:
            logger.warning(f"Gemini action plan generation failed: {e}. Using deterministic action plan.")

    # Deterministic offline fallback if Gemini not used or failed
    if not candidate_steps:
        candidate_steps = _generate_offline_action_steps(situation_type, urgency, findings_data, db, document_id)

    # Validate citations and enforce non-negotiable legal safety rules
    verified_steps = []
    doc_chunks = db.query(Chunk).filter(Chunk.document_id == document_id).all()

    for step in candidate_steps:
        order = step.get("order", len(verified_steps) + 1)
        action = strip_fabricated_citations(step.get("action", ""))
        rationale = strip_fabricated_citations(step.get("rationale", ""))
        cit = step.get("citation")

        verified_cit = None
        if cit and isinstance(cit, dict) and cit.get("quote"):
            quote = cit.get("quote", "").strip()
            # Verify quote against chunk texts
            is_valid = False
            for chunk in doc_chunks:
                match, score = verify_citation_quote(quote, chunk.text)
                if match:
                    is_valid = True
                    verified_cit = {
                        "page": chunk.page_number,
                        "clause_id": chunk.clause_id or cit.get("clause_id"),
                        "quote": quote,
                    }
                    break

            if not is_valid:
                # Log audit failure and drop invalid citation
                audit = AuditEvent(
                    user_id=user_id,
                    event_type="validation_failure",
                    metadata_json={
                        "document_id": document_id,
                        "step_order": order,
                        "invalid_quote": quote,
                        "reason": "Action plan step citation quote not found in stored document chunks",
                    },
                )
                db.add(audit)
                db.commit()
                verified_cit = None

        verified_steps.append({
            "order": order,
            "action": action,
            "rationale": rationale,
            "citation": verified_cit,
        })

    # High urgency / dispute escalation requirement (§13.7 & §8)
    # If active dispute or high urgency, ensure final step recommends professional consult
    if situation_type == "active_dispute" or urgency == "high":
        has_consult_step = any(
            "lawyer" in s["action"].lower() or "legal" in s["action"].lower() or "tenant" in s["action"].lower()
            for s in verified_steps
        )
        if not has_consult_step or len(verified_steps) == 0:
            verified_steps.append({
                "order": len(verified_steps) + 1,
                "action": "Consult a qualified local tenant attorney or housing rights legal clinic.",
                "rationale": "Because this situation involves an active dispute or urgent exposure, professional guidance is essential to preserve your legal rights and avoid unintended lease forfeiture.",
                "citation": None,
            })

    # Save or update ActionPlan in DB
    existing_plan = db.query(ActionPlan).filter(ActionPlan.document_id == document_id).first()
    severity_enum = SeverityLevel[urgency.upper()] if urgency.upper() in SeverityLevel.__members__ else SeverityLevel.LOW

    if existing_plan:
        existing_plan.situation_context_text = context_text
        existing_plan.situation_type = situation_type
        existing_plan.urgency = severity_enum
        existing_plan.steps = verified_steps
        existing_plan.generated_at = utc_now()
        plan_record = existing_plan
    else:
        plan_record = ActionPlan(
            document_id=document_id,
            situation_context_text=context_text,
            situation_type=situation_type,
            urgency=severity_enum,
            steps=verified_steps,
        )
        db.add(plan_record)

    db.commit()
    db.refresh(plan_record)

    return {
        "id": plan_record.id,
        "document_id": document_id,
        "situation_context_text": context_text,
        "situation_type": situation_type,
        "urgency": urgency,
        "steps": verified_steps,
        "generated_at": plan_record.generated_at,
    }


def _generate_offline_action_steps(
    situation_type: str,
    urgency: str,
    findings: List[Dict[str, Any]],
    db: Session,
    document_id: str,
) -> List[Dict[str, Any]]:
    """Helper to construct deterministic grounded action steps for test/offline environments."""
    steps = []
    # Try finding relevant clauses to cite
    term_chunk = db.query(Chunk).filter(
        Chunk.document_id == document_id,
        Chunk.clause_id.in_(["3", "Clause 3", "9(a)", "Clause 9(a)", "9", "4"])
    ).first()

    if situation_type == "termination":
        cit = None
        if term_chunk:
            cit = {"page": term_chunk.page_number, "clause_id": term_chunk.clause_id, "quote": term_chunk.text[:80]}
        steps.append({
            "order": 1,
            "action": "Review the required written notice window before serving move-out intent.",
            "rationale": "Failure to provide timely written notice in the prescribed format may trigger automatic month-to-month renewal or penalty charges.",
            "citation": cit,
        })
        steps.append({
            "order": 2,
            "action": "Document the condition of the rental unit and request a joint pre-moveout inspection.",
            "rationale": "A documented move-out walkthrough protects your security deposit against unauthorized deductions.",
            "citation": None,
        })
        steps.append({
            "order": 3,
            "action": "Request formal written confirmation of account balance and release of obligations upon surrendering keys.",
            "rationale": "Clear documentation prevents unexpected claims for subsequent rental periods.",
            "citation": None,
        })
    elif situation_type == "active_dispute":
        steps.append({
            "order": 1,
            "action": "Create a contemporaneous written timeline with photos and correspondence of all unaddressed issues.",
            "rationale": "Documentary evidence is essential for establishing landlord non-compliance or failure to repair.",
            "citation": None,
        })
        steps.append({
            "order": 2,
            "action": "Send formal written notice to the landlord citing the specific repair or habitability deficiencies.",
            "rationale": "Most lease agreements require written notice and a defined cure period before tenant remedies take effect.",
            "citation": None,
        })
        steps.append({
            "order": 3,
            "action": "Consult a qualified tenant-rights organization or legal aid attorney before withholding rent or terminating early.",
            "rationale": "Unilateral withholding without adhering to jurisdictional notice statutes can risk eviction proceedings.",
            "citation": None,
        })
    elif situation_type == "renewal_negotiation":
        steps.append({
            "order": 1,
            "action": "Compare the proposed renewal rate and terms against your current lease terms.",
            "rationale": "Verify that all changes to rent, security deposit, and utilities are clearly documented.",
            "citation": None,
        })
        steps.append({
            "order": 2,
            "action": "Request written clarification on any revised fees, penalty additions, or restriction modifications.",
            "rationale": "Ambiguities should be resolved and confirmed in writing prior to signing the renewal addendum.",
            "citation": None,
        })
    else:  # pre_signing_review or general_curiosity
        steps.append({
            "order": 1,
            "action": "Read and verify key lease terms including rent due dates, security deposit conditions, and termination clauses.",
            "rationale": "Ensures you are aware of all financial obligations and notice deadlines before legally committing.",
            "citation": None,
        })
        steps.append({
            "order": 2,
            "action": "Request written amendments for any verbal representations made by the leasing agent.",
            "rationale": "Lease agreements typically include integration clauses stating that oral promises are non-binding.",
            "citation": None,
        })

    return steps


def generate_lawyer_questions(
    document_id: str,
    situation: Optional[Dict[str, Any]],
    db: Session,
) -> List[Dict[str, Any]]:
    """
    Generate topic-grouped, non-generic questions for tenant legal consultation (§13.8).
    Strictly guards against fabricated statute/case law citations.
    """
    findings = db.query(Finding).filter(Finding.document_id == document_id).all()
    findings_data = [
        {
            "id": f.id,
            "title": f.title,
            "severity": f.severity.value if hasattr(f.severity, "value") else str(f.severity),
            "explanation": f.plain_explanation,
            "quote": f.quote,
            "page": f.page_number,
        }
        for f in findings
    ]

    candidate_questions = []

    if settings.GEMINI_API_KEY and settings.GEMINI_API_KEY != "your_gemini_api_key_here":
        try:
            user_prompt = format_lawyer_questions_prompt(findings_data, situation)
            parsed = generate_structured_json(
                system_prompt=LAWYER_QUESTION_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                model_name=settings.GEMINI_FLASH_MODEL,
                temperature=0.1,
            )
            candidate_questions = parsed.get("questions", [])
        except Exception as e:
            logger.warning(f"Gemini lawyer question generation failed: {e}. Using deterministic questions.")

    if not candidate_questions:
        candidate_questions = _generate_offline_lawyer_questions(findings_data, situation)

    # Process questions: enforce regex guard against fabricated legal citations
    cleaned_questions = []
    # Clear existing questions for this document
    db.query(Question).filter(Question.document_id == document_id).delete()

    for q in candidate_questions:
        topic = strip_fabricated_citations(q.get("topic", "General Lease Terms"))
        raw_q_text = q.get("question", "")
        question_text = strip_fabricated_citations(raw_q_text)
        priority_str = q.get("priority", "medium").lower()
        if priority_str not in VALID_URGENCIES:
            priority_str = "medium"

        source_fid = q.get("source_finding_id")
        # Validate source_fid exists
        if source_fid:
            f_exists = any(f["id"] == source_fid for f in findings_data)
            if not f_exists:
                source_fid = None

        priority_enum = SeverityLevel[priority_str.upper()] if priority_str.upper() in SeverityLevel.__members__ else SeverityLevel.MEDIUM

        q_record = Question(
            document_id=document_id,
            finding_id=source_fid,
            topic=topic,
            question_text=question_text,
            priority=priority_enum,
        )
        db.add(q_record)
        cleaned_questions.append({
            "topic": topic,
            "question": question_text,
            "priority": priority_str,
            "source_finding_id": source_fid,
        })

    db.commit()
    return cleaned_questions


def _generate_offline_lawyer_questions(
    findings: List[Dict[str, Any]],
    situation: Optional[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Helper to generate targeted lawyer questions based on findings and situation."""
    questions = []

    # 1. Questions from high-severity findings
    for f in findings:
        severity = str(f.get("severity", "")).lower()
        title = f.get("title", "")
        fid = f.get("id")

        if severity == "high":
            if "early termination" in title.lower() or "penalty" in title.lower():
                questions.append({
                    "topic": "Early Termination & Liquidated Damages",
                    "question": "Is the lease clause imposing multiple months of liquidated damages penalty enforceable, or does the landlord have an affirmative duty to mitigate damages under local tenancy law?",
                    "priority": "high",
                    "source_finding_id": fid,
                })
            elif "repair" in title.lower() or "habitability" in title.lower():
                questions.append({
                    "topic": "Habitability & Landlord Repair Obligations",
                    "question": "Does the clause attempting to shift maintenance responsibilities or waive tenant habitability rights conflict with municipal housing codes?",
                    "priority": "high",
                    "source_finding_id": fid,
                })
            elif "access" in title.lower() or "entry" in title.lower():
                questions.append({
                    "topic": "Tenant Privacy & Notice of Entry",
                    "question": "Can the landlord legally enter the premises without 24 hours advance written notice, or is this provision void under local privacy laws?",
                    "priority": "high",
                    "source_finding_id": fid,
                })
            else:
                questions.append({
                    "topic": "High-Risk Lease Provisions",
                    "question": f"How does the lease clause regarding '{title}' impact my legal rights and financial liability in this jurisdiction?",
                    "priority": "high",
                    "source_finding_id": fid,
                })

    # 2. Add situation-specific questions if relevant
    sit_type = situation.get("situation_type") if situation else None
    if sit_type == "termination":
        questions.append({
            "topic": "Notice Window & Surrender of Possession",
            "question": "What is the legally compliant method and timeline to serve my notice of termination to avoid improper notice claims?",
            "priority": "medium",
            "source_finding_id": None,
        })
    elif sit_type == "active_dispute":
        questions.append({
            "topic": "Dispute Resolution & Evidence Documentation",
            "question": "What formal written demands or escrow steps should I take prior to initiating administrative complaints or withholding rent?",
            "priority": "high",
            "source_finding_id": None,
        })
    elif sit_type == "renewal_negotiation":
        questions.append({
            "topic": "Rent Increase Limitations",
            "question": "Are there local rent stabilization ordinances or notice period requirements governing the proposed renewal increase?",
            "priority": "medium",
            "source_finding_id": None,
        })

    # Default fallback question if no findings
    if not questions:
        questions.append({
            "topic": "General Lease Review",
            "question": "Are there any provisions in this agreement that waive statutory tenant protections or impose non-standard liabilities?",
            "priority": "medium",
            "source_finding_id": None,
        })

    return questions
