from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.security import get_current_user, verify_document_access
from app.models.entities import User, Document, Clause, ClauseCategory
from app.schemas.clauses import ClauseResponse
from app.services.analysis import analyze_document

router = APIRouter(tags=["clauses"])


@router.get("/documents/{document_id}/clauses", response_model=List[ClauseResponse])
def get_document_clauses(
    document_id: str,
    category: Optional[str] = Query(None, description="Filter by clause category"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve categorized clauses for a document with plain-language summaries and citations."""
    doc = verify_document_access(document_id, current_user.id, db)

    # If clauses have not been analyzed yet, run analysis pipeline
    if not doc.clauses:
        analyze_document(document_id, db)

    query = db.query(Clause).filter(Clause.document_id == document_id)

    if category:
        try:
            cat_enum = ClauseCategory(category.lower())
            query = query.filter(Clause.category == cat_enum)
        except ValueError:
            pass

    clauses = query.order_by(Clause.page_number.asc()).all()

    return [
        ClauseResponse(
            id=c.id,
            document_id=c.document_id,
            clause_number=c.clause_number,
            heading=c.heading,
            category=c.category.value if hasattr(c.category, "value") else str(c.category),
            summary=c.summary,
            quote=c.quote,
            page_number=c.page_number,
        )
        for c in clauses
    ]
