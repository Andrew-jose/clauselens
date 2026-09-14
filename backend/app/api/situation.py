import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.security import get_current_user, verify_document_access
from app.models.entities import User, Document, ActionPlan, Question, AuditEvent
from app.schemas.situation import (
    SituationRequest,
    SituationResponse,
    ActionPlanResponse,
    ActionStep,
    LawyerQuestionsResponse,
    LawyerQuestion,
)
from app.schemas.clauses import ClauseCitation
from app.services.analysis import analyze_document
from app.services.situation_router import (
    classify_situation,
    generate_action_plan,
    generate_lawyer_questions,
)
from app.services.exporter import generate_lawyer_prep_pdf

router = APIRouter(tags=["situation"])


@router.post("/documents/{document_id}/situation", response_model=SituationResponse)
def submit_situation(
    document_id: str,
    payload: SituationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Submit tenant's free-text situation. Classifies the scenario into fixed taxonomy,
    assigns urgency, identifies relevant categories, and triggers situation-specific
    action plan and lawyer question updates.
    """
    doc = verify_document_access(document_id, current_user.id, db)

    # Ensure document has findings analyzed
    if not doc.findings:
        analyze_document(document_id, db)

    # 1. Classify situation
    classification = classify_situation(payload.context_text)
    classification_with_text = {
        **classification,
        "context_text": payload.context_text,
    }

    # 2. Generate updated Action Plan tailored to situation and findings
    generate_action_plan(
        document_id=document_id,
        situation=classification_with_text,
        db=db,
        user_id=current_user.id,
    )

    # 3. Generate updated Lawyer Questions tailored to situation and findings
    generate_lawyer_questions(
        document_id=document_id,
        situation=classification_with_text,
        db=db,
    )

    return SituationResponse(
        situation_type=classification["situation_type"],
        urgency=classification["urgency"],
        relevant_categories=classification["relevant_categories"],
    )


@router.get("/documents/{document_id}/action-plan", response_model=ActionPlanResponse)
def get_action_plan(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve the current ordered action plan for this document.
    Generates a default plan if one has not yet been requested.
    """
    doc = verify_document_access(document_id, current_user.id, db)

    if not doc.findings:
        analyze_document(document_id, db)

    plan = db.query(ActionPlan).filter(ActionPlan.document_id == document_id).first()
    if not plan:
        default_sit = {
            "situation_type": "pre_signing_review",
            "urgency": "low",
            "context_text": "General pre-signing lease review",
            "relevant_categories": ["rent_fees", "deposit", "restrictions"],
        }
        plan_dict = generate_action_plan(
            document_id=document_id,
            situation=default_sit,
            db=db,
            user_id=current_user.id,
        )
        steps_out = [
            ActionStep(
                order=s["order"],
                action=s["action"],
                rationale=s["rationale"],
                citation=ClauseCitation(**s["citation"]) if s.get("citation") else None,
            )
            for s in plan_dict["steps"]
        ]
        return ActionPlanResponse(
            id=plan_dict["id"],
            document_id=document_id,
            situation_context_text=plan_dict["situation_context_text"],
            situation_type=plan_dict["situation_type"],
            urgency=plan_dict["urgency"],
            steps=steps_out,
            generated_at=plan_dict["generated_at"],
        )

    urgency_str = plan.urgency.value if hasattr(plan.urgency, "value") else str(plan.urgency)
    raw_steps = plan.steps or []
    steps_out = [
        ActionStep(
            order=s.get("order", idx + 1),
            action=s.get("action", ""),
            rationale=s.get("rationale", ""),
            citation=ClauseCitation(**s["citation"]) if s.get("citation") else None,
        )
        for idx, s in enumerate(raw_steps)
    ]

    return ActionPlanResponse(
        id=plan.id,
        document_id=document_id,
        situation_context_text=plan.situation_context_text,
        situation_type=plan.situation_type,
        urgency=urgency_str,
        steps=steps_out,
        generated_at=plan.generated_at,
    )


@router.get("/documents/{document_id}/lawyer-questions", response_model=LawyerQuestionsResponse)
def get_lawyer_questions(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve topic-grouped consultation questions prepared for legal counsel.
    Generates questions if not yet created.
    """
    doc = verify_document_access(document_id, current_user.id, db)

    if not doc.findings:
        analyze_document(document_id, db)

    questions = db.query(Question).filter(Question.document_id == document_id).all()
    if not questions:
        plan = db.query(ActionPlan).filter(ActionPlan.document_id == document_id).first()
        sit = None
        if plan:
            sit = {
                "situation_type": plan.situation_type,
                "urgency": plan.urgency.value if hasattr(plan.urgency, "value") else str(plan.urgency),
            }
        raw_qs = generate_lawyer_questions(document_id, sit, db)
        questions = db.query(Question).filter(Question.document_id == document_id).all()

    return LawyerQuestionsResponse(
        document_id=document_id,
        questions=[
            LawyerQuestion(
                id=q.id,
                topic=q.topic,
                question=q.question_text,
                priority=q.priority.value if hasattr(q.priority, "value") else str(q.priority),
                source_finding_id=q.finding_id,
            )
            for q in questions
        ],
    )


@router.get("/documents/{document_id}/export")
def export_lawyer_packet_pdf(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Generate and stream a branded PDF lawyer-consultation preparation packet.
    """
    doc = verify_document_access(document_id, current_user.id, db)

    if not doc.findings:
        analyze_document(document_id, db)

    # Ensure questions and action plan exist
    if not doc.action_plans:
        default_sit = {
            "situation_type": "pre_signing_review",
            "urgency": "low",
            "context_text": "Standard Lease Review",
        }
        generate_action_plan(document_id, default_sit, db, current_user.id)

    if not doc.questions:
        generate_lawyer_questions(document_id, None, db)

    pdf_bytes = generate_lawyer_prep_pdf(document_id, db)

    filename = f"lawyer_prep_{doc.id[:8]}.pdf"

    # Log audit event for PDF export
    audit = AuditEvent(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        event_type="export",
        metadata_json={"document_id": document_id, "format": "pdf", "filename": filename},
    )
    db.add(audit)
    db.commit()

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-cache",
        },
    )
