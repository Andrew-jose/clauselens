from datetime import datetime
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, ConfigDict, field_validator


class CompareRequest(BaseModel):
    document_a_id: str
    document_b_id: str

    @field_validator("document_b_id")
    @classmethod
    def validate_distinct_documents(cls, v: str, info) -> str:
        if "document_a_id" in info.data and v == info.data["document_a_id"]:
            raise ValueError("Cannot compare a document with itself. Please select two distinct lease documents.")
        return v


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
