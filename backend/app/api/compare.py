import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request, status

logger = logging.getLogger(__name__)
from sqlalchemy.orm import Session
from app.config import settings
from app.db.session import get_db
from app.core.security import get_current_user
from app.core.rate_limit import limiter
from app.models.entities import User, ComparisonSession, ComparisonFinding
from app.schemas.compare import (
    CompareRequest,
    ComparisonSessionResponse,
    ComparisonFindingResponse,
)
from app.services.comparator import compare_documents

router = APIRouter(prefix="/compare", tags=["compare"])


@router.post("", response_model=ComparisonSessionResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(settings.RATE_LIMIT_PER_MINUTE)
def start_comparison(
    request: Request,
    payload: CompareRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Start a side-by-side clause-level comparison between two leases.
    Synthesizes deltas, assesses tenant favorability, and validates citations on both documents.
    """
    if payload.document_a_id == payload.document_b_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot compare a document with itself. Please select two distinct lease documents.",
        )

    try:
        session = compare_documents(
            doc_a_id=payload.document_a_id,
            doc_b_id=payload.document_b_id,
            user_id=current_user.id,
            db=db,
        )
    except HTTPException:
        raise
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))
    except Exception as e:
        logger.error(f"Comparison failed for documents {payload.document_a_id} and {payload.document_b_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Comparison failed. Please verify that both documents are readable and try again.",
        )

    findings_out = [
        ComparisonFindingResponse(
            id=f.id,
            category=f.category,
            delta_description=f.delta_description,
            favors=f.favors,
            severity=f.severity.value if hasattr(f.severity, "value") else str(f.severity),
            doc_a_citation=f.doc_a_citation,
            doc_b_citation=f.doc_b_citation,
        )
        for f in session.findings
    ]

    return ComparisonSessionResponse(
        id=session.id,
        document_a_id=session.document_a_id,
        document_b_id=session.document_b_id,
        created_at=session.created_at,
        deltas_count=len(findings_out),
        findings=findings_out,
    )


@router.get("/{comparison_id}", response_model=ComparisonSessionResponse)
def get_comparison(
    comparison_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve comparison session results."""
    session = db.query(ComparisonSession).filter(
        ComparisonSession.id == comparison_id,
        ComparisonSession.user_id == current_user.id,
    ).first()

    if not session:
        other_session = db.query(ComparisonSession).filter(ComparisonSession.id == comparison_id).first()
        if other_session:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access forbidden: you do not have permission to view this comparison.",
            )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comparison session not found.")

    findings_out = [
        ComparisonFindingResponse(
            id=f.id,
            category=f.category,
            delta_description=f.delta_description,
            favors=f.favors,
            severity=f.severity.value if hasattr(f.severity, "value") else str(f.severity),
            doc_a_citation=f.doc_a_citation,
            doc_b_citation=f.doc_b_citation,
        )
        for f in session.findings
    ]

    return ComparisonSessionResponse(
        id=session.id,
        document_a_id=session.document_a_id,
        document_b_id=session.document_b_id,
        created_at=session.created_at,
        deltas_count=len(findings_out),
        findings=findings_out,
    )
