from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.security import get_current_user
from app.models.entities import User, Document, Finding, Clause, SeverityLevel, ClauseCategory
from app.schemas.clauses import FindingResponse
from app.services.analysis import analyze_document

router = APIRouter(tags=["findings"])


@router.get("/documents/{document_id}/findings", response_model=List[FindingResponse])
def get_document_findings(
    document_id: str,
    severity: Optional[str] = Query(None, description="Filter by severity: low, medium, high"),
    category: Optional[str] = Query(None, description="Filter by clause category"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve risk and obligation findings with severity ratings and verified quotes."""
    doc = db.query(Document).filter(Document.id == document_id, Document.user_id == current_user.id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    if not doc.findings:
        analyze_document(document_id, db)

    query = db.query(Finding).filter(Finding.document_id == document_id)

    if severity:
        try:
            sev_enum = SeverityLevel(severity.lower())
            query = query.filter(Finding.severity == sev_enum)
        except ValueError:
            pass

    if category:
        try:
            cat_enum = ClauseCategory(category.lower())
            query = query.join(Clause).filter(Clause.category == cat_enum)
        except ValueError:
            pass

    findings = query.all()

    return [
        FindingResponse(
            id=f.id,
            document_id=f.document_id,
            clause_id=f.clause_id,
            type=f.type.value if hasattr(f.type, "value") else str(f.type),
            severity=f.severity.value if hasattr(f.severity, "value") else str(f.severity),
            title=f.title,
            plain_explanation=f.plain_explanation,
            page_number=f.page_number,
            quote=f.quote,
            verified=f.verified,
        )
        for f in findings
    ]


@router.post("/documents/{document_id}/analyze")
def trigger_document_analysis(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Trigger or refresh full document analysis (summary, clauses, risks)."""
    doc = db.query(Document).filter(Document.id == document_id, Document.user_id == current_user.id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    result = analyze_document(document_id, db)
    return {
        "document_id": document_id,
        "status": "ready",
        **result,
    }
