from datetime import datetime
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, ConfigDict


class CompareRequest(BaseModel):
    document_a_id: str
    document_b_id: str


class ComparisonFindingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    category: str
    delta_description: str
    favors: str  # tenant, landlord, neutral, unclear
    severity: str  # low, medium, high
    doc_a_citation: Optional[Dict[str, Any]] = None
    doc_b_citation: Optional[Dict[str, Any]] = None


class ComparisonSessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    document_a_id: str
    document_b_id: str
    created_at: datetime
    deltas_count: int = 0
    findings: List[ComparisonFindingResponse] = []
