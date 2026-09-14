from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class CitationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    chunk_id: Optional[str] = None
    page: int
    clause_id: Optional[str] = None
    quote: str
    verified: bool = False
    match_score: Optional[float] = None


class AskRequest(BaseModel):
    question: str = Field(..., min_length=2, max_length=1000)
    conversation_id: Optional[str] = None


class AskResponse(BaseModel):
    answer: str
    status: str  # grounded_high, grounded_low, not_found_in_document, general_info
    citations: List[CitationResponse] = []
    confidence_note: Optional[str] = None
    conversation_id: str


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    role: str
    content: str
    status: str
    citations: List[CitationResponse] = []
    created_at: datetime


class ConversationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    document_id: Optional[str] = None
    messages: List[MessageResponse] = []
    created_at: datetime
