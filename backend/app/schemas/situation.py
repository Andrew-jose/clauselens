from typing import List, Optional, Any, Dict
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from app.schemas.clauses import ClauseCitation


class SituationRequest(BaseModel):
    context_text: str = Field(..., min_length=3, description="Tenant's free-text situation context")


class SituationResponse(BaseModel):
    situation_type: str = Field(..., description="pre_signing_review, active_dispute, termination, renewal_negotiation, general_curiosity")
    urgency: str = Field(..., description="low, medium, high")
    relevant_categories: List[str] = Field(default_factory=list, description="Up to 4 relevant clause categories")


class ActionStep(BaseModel):
    order: int
    action: str
    rationale: str
    citation: Optional[ClauseCitation] = None


class ActionPlanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[str] = None
    document_id: str
    situation_context_text: Optional[str] = None
    situation_type: Optional[str] = None
    urgency: Optional[str] = None
    steps: List[ActionStep] = Field(default_factory=list)
    generated_at: Optional[datetime] = None


class LawyerQuestion(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[str] = None
    topic: str
    question: str
    priority: str = Field("medium", description="low, medium, high")
    source_finding_id: Optional[str] = None


class LawyerQuestionsResponse(BaseModel):
    document_id: str
    questions: List[LawyerQuestion] = Field(default_factory=list)
