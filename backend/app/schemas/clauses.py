from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class ClauseCitation(BaseModel):
    page: int
    clause_id: Optional[str] = None
    quote: str


class ClauseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    document_id: str
    clause_number: Optional[str] = None
    heading: Optional[str] = None
    category: str
    summary: Optional[str] = None
    quote: Optional[str] = None
    page_number: int


class FindingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    document_id: str
    clause_id: Optional[str] = None
    type: str  # risk, obligation, inconsistency
    severity: str  # low, medium, high
    title: str
    plain_explanation: str
    page_number: int
    quote: Optional[str] = None
    verified: bool = False
