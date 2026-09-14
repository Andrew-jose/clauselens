from datetime import datetime
from typing import List, Optional, Any
from pydantic import BaseModel, ConfigDict


class ChunkResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    page_number: int
    clause_id: Optional[str] = None
    section_heading: Optional[str] = None
    text: str
    token_count: int


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    filename: str
    mime_type: str
    page_count: int
    status: str
    summary: Optional[str] = None
    created_at: datetime


class DocumentDetailResponse(DocumentResponse):
    key_terms: Optional[List[str]] = None
    chunks_count: int = 0
    clauses_count: int = 0
    findings_count: int = 0


class DocumentStatusResponse(BaseModel):
    status: str
    page_count: int
    chunks_count: int
    message: Optional[str] = None
