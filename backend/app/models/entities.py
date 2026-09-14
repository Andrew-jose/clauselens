import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    String,
    Integer,
    Boolean,
    Text,
    DateTime,
    ForeignKey,
    Enum as SAEnum,
    JSON,
)
from sqlalchemy.orm import relationship
from app.db.session import Base
import enum


def generate_uuid() -> str:
    return str(uuid.uuid4())


def utc_now():
    return datetime.now(timezone.utc)


class ClauseCategory(str, enum.Enum):
    RENT_FEES = "rent_fees"
    TERM_RENEWAL = "term_renewal"
    TERMINATION_PENALTIES = "termination_penalties"
    REPAIRS_HABITABILITY = "repairs_habitability"
    ACCESS_PRIVACY = "access_privacy"
    DEPOSIT = "deposit"
    RESTRICTIONS = "restrictions"
    OTHER = "other"


class SeverityLevel(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class FindingType(str, enum.Enum):
    RISK = "risk"
    OBLIGATION = "obligation"
    INCONSISTENCY = "inconsistency"


class GroundedStatus(str, enum.Enum):
    GROUNDED_HIGH = "grounded_high"
    GROUNDED_LOW = "grounded_low"
    NOT_FOUND_IN_DOCUMENT = "not_found_in_document"
    GENERAL_INFO = "general_info"


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    documents = relationship("Document", back_populates="user", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")


class Document(Base):
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    mime_type = Column(String(100), nullable=False)
    page_count = Column(Integer, default=0)
    status = Column(String(50), default="uploading")  # uploading, processing, ready, failed
    summary = Column(Text, nullable=True)
    key_terms = Column(JSON, nullable=True)
    retention_expiry = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    user = relationship("User", back_populates="documents")
    pages = relationship("DocumentPage", back_populates="document", cascade="all, delete-orphan")
    chunks = relationship("Chunk", back_populates="document", cascade="all, delete-orphan")
    clauses = relationship("Clause", back_populates="document", cascade="all, delete-orphan")
    findings = relationship("Finding", back_populates="document", cascade="all, delete-orphan")
    action_plans = relationship("ActionPlan", back_populates="document", cascade="all, delete-orphan")
    questions = relationship("Question", back_populates="document", cascade="all, delete-orphan")


class DocumentPage(Base):
    __tablename__ = "document_pages"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    document_id = Column(String(36), ForeignKey("documents.id"), nullable=False, index=True)
    page_number = Column(Integer, nullable=False)
    raw_text = Column(Text, nullable=False)
    char_count = Column(Integer, default=0)

    document = relationship("Document", back_populates="pages")


class Chunk(Base):
    __tablename__ = "chunks"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    document_id = Column(String(36), ForeignKey("documents.id"), nullable=False, index=True)
    page_number = Column(Integer, nullable=False)
    clause_id = Column(String(100), nullable=True)
    section_heading = Column(String(255), nullable=True)
    text = Column(Text, nullable=False)
    start_char = Column(Integer, default=0)
    end_char = Column(Integer, default=0)
    token_count = Column(Integer, default=0)
    vector_ref = Column(String(100), nullable=True)  # ChromaDB ID

    document = relationship("Document", back_populates="chunks")


class Clause(Base):
    __tablename__ = "clauses"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    document_id = Column(String(36), ForeignKey("documents.id"), nullable=False, index=True)
    clause_number = Column(String(50), nullable=True)
    heading = Column(String(255), nullable=True)
    category = Column(SAEnum(ClauseCategory), default=ClauseCategory.OTHER, nullable=False)
    summary = Column(Text, nullable=True)
    quote = Column(Text, nullable=True)
    page_number = Column(Integer, default=1)

    document = relationship("Document", back_populates="clauses")
    findings = relationship("Finding", back_populates="clause", cascade="all, delete-orphan")


class Finding(Base):
    __tablename__ = "findings"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    document_id = Column(String(36), ForeignKey("documents.id"), nullable=False, index=True)
    clause_id = Column(String(36), ForeignKey("clauses.id"), nullable=True)
    type = Column(SAEnum(FindingType), default=FindingType.RISK, nullable=False)
    severity = Column(SAEnum(SeverityLevel), default=SeverityLevel.MEDIUM, nullable=False)
    title = Column(String(255), nullable=False)
    plain_explanation = Column(Text, nullable=False)
    page_number = Column(Integer, default=1)
    quote = Column(Text, nullable=True)
    verified = Column(Boolean, default=False)

    document = relationship("Document", back_populates="findings")
    clause = relationship("Clause", back_populates="findings")


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    document_id = Column(String(36), ForeignKey("documents.id"), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")


class Message(Base):
    __tablename__ = "messages"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    conversation_id = Column(String(36), ForeignKey("conversations.id"), nullable=False, index=True)
    role = Column(String(50), nullable=False)  # user, assistant
    content = Column(Text, nullable=False)
    status = Column(SAEnum(GroundedStatus), default=GroundedStatus.GROUNDED_HIGH, nullable=False)
    confidence_note = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    conversation = relationship("Conversation", back_populates="messages")
    citations = relationship("MessageCitation", back_populates="message", cascade="all, delete-orphan")


class MessageCitation(Base):
    __tablename__ = "message_citations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    message_id = Column(String(36), ForeignKey("messages.id"), nullable=False, index=True)
    chunk_id = Column(String(36), nullable=True)
    page = Column(Integer, nullable=False)
    clause_id = Column(String(100), nullable=True)
    quote = Column(Text, nullable=False)
    verified = Column(Boolean, default=False)

    message = relationship("Message", back_populates="citations")


class ComparisonSession(Base):
    __tablename__ = "comparison_sessions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    document_a_id = Column(String(36), ForeignKey("documents.id"), nullable=False)
    document_b_id = Column(String(36), ForeignKey("documents.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    findings = relationship("ComparisonFinding", back_populates="session", cascade="all, delete-orphan")


class ComparisonFinding(Base):
    __tablename__ = "comparison_findings"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    comparison_session_id = Column(String(36), ForeignKey("comparison_sessions.id"), nullable=False, index=True)
    category = Column(String(100), nullable=False)
    delta_description = Column(Text, nullable=False)
    favors = Column(String(50), default="unclear")  # tenant, landlord, neutral, unclear
    severity = Column(SAEnum(SeverityLevel), default=SeverityLevel.LOW, nullable=False)
    doc_a_citation = Column(JSON, nullable=True)
    doc_b_citation = Column(JSON, nullable=True)

    session = relationship("ComparisonSession", back_populates="findings")


class Question(Base):
    __tablename__ = "questions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    document_id = Column(String(36), ForeignKey("documents.id"), nullable=False, index=True)
    finding_id = Column(String(36), ForeignKey("findings.id"), nullable=True)
    topic = Column(String(100), nullable=False)
    question_text = Column(Text, nullable=False)
    priority = Column(SAEnum(SeverityLevel), default=SeverityLevel.MEDIUM, nullable=False)

    document = relationship("Document", back_populates="questions")


class ActionPlan(Base):
    __tablename__ = "action_plans"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    document_id = Column(String(36), ForeignKey("documents.id"), nullable=False, index=True)
    situation_context_text = Column(Text, nullable=False)
    situation_type = Column(String(100), nullable=False)
    urgency = Column(SAEnum(SeverityLevel), default=SeverityLevel.LOW, nullable=False)
    steps = Column(JSON, nullable=False)  # list of {order, action, rationale, citation}
    generated_at = Column(DateTime(timezone=True), default=utc_now)

    document = relationship("Document", back_populates="action_plans")


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), nullable=True, index=True)
    event_type = Column(String(50), nullable=False)  # login, upload, delete, export, ai_call, validation_failure
    metadata_json = Column(JSON, nullable=True)
    ip_hash = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)
