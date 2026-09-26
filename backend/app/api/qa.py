import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from app.config import settings
from app.db.session import get_db
from app.core.security import get_current_user, verify_document_access
from app.core.rate_limit import limiter
from app.models.entities import (
    User,
    Document,
    Conversation,
    Message,
    MessageCitation,
    GroundedStatus,
)
from app.schemas.qa import (
    AskRequest,
    AskResponse,
    CitationResponse,
    ConversationResponse,
    MessageResponse,
)
from app.services.retriever import retrieve_relevant_chunks, build_qa_context_string
from app.services.prompts.qa import QA_SYSTEM_PROMPT, QA_USER_PROMPT_TEMPLATE, sanitize_prompt_input
from app.services.gemini_client import generate_structured_json
from app.services.validator import validate_citations_against_db
from app.services.verifier import run_self_check_verifier, strip_fabricated_citations

router = APIRouter(tags=["qa"])


@router.post("/documents/{document_id}/ask", response_model=AskResponse)
@limiter.limit(settings.RATE_LIMIT_PER_MINUTE)
async def ask_document(
    request: Request,
    document_id: str,
    payload: AskRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Evidence-grounded Q&A endpoint.
    Retrieves top chunks, queries Gemini with structured output, validates
    citations in code against stored chunk text, and verifies groundedness.
    """
    doc = verify_document_access(document_id, current_user.id, db)

    # 1. Retrieve or initialize conversation
    conv_id = payload.conversation_id
    conversation = None
    if conv_id:
        conversation = db.query(Conversation).filter(Conversation.id == conv_id, Conversation.user_id == current_user.id).first()

    if not conversation:
        conv_id = str(uuid.uuid4())
        conversation = Conversation(
            id=conv_id,
            user_id=current_user.id,
            document_id=document_id,
        )
        db.add(conversation)
        db.commit()

    # 2. Record user query
    user_msg = Message(
        id=str(uuid.uuid4()),
        conversation_id=conv_id,
        role="user",
        content=payload.question,
        status=GroundedStatus.GENERAL_INFO,
    )
    db.add(user_msg)
    db.commit()

    # 3. Retrieve relevant chunks from ChromaDB (reusing request db session)
    retrieved_chunks = retrieve_relevant_chunks(payload.question, document_id, top_k=6, db=db)
    context_str = build_qa_context_string(retrieved_chunks)

    # 4. Prompt Gemini with structured output & prompt isolation delimiters
    sanitized_question = sanitize_prompt_input(payload.question)
    user_prompt = QA_USER_PROMPT_TEMPLATE.format(
        retrieved_chunks=context_str,
        user_question=sanitized_question,
    )

    ai_output = generate_structured_json(
        system_prompt=QA_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        model_name=settings.GEMINI_FLASH_MODEL,
    )

    raw_answer = ai_output.get("answer", "")
    raw_citations = ai_output.get("citations", [])
    raw_status = ai_output.get("status", GroundedStatus.NOT_FOUND_IN_DOCUMENT.value)
    confidence_note = ai_output.get("confidence_note", "")

    # Security: Strip any prohibited fabricated statute/case citations
    cleaned_answer = strip_fabricated_citations(raw_answer)

    # 5. Independent Code-Level Citation Validator (§7.3)
    verified_citations, failed_citations, recommended_status = validate_citations_against_db(
        citations=raw_citations,
        db=db,
        user_id=current_user.id,
        document_id=document_id,
    )

    # 6. Second-Pass Self-Check Verifier (§7.6)
    final_status = recommended_status
    if verified_citations and recommended_status == GroundedStatus.GROUNDED_HIGH.value:
        is_grounded, unsupported_sentences = run_self_check_verifier(
            answer=cleaned_answer,
            citations=verified_citations,
            retrieved_chunks_text=context_str,
        )
        if not is_grounded:
            # Fallback if unanchored claims are present
            final_status = GroundedStatus.GROUNDED_LOW.value

    # If no citations passed, strictly prevent grounded status
    if not verified_citations:
        final_status = GroundedStatus.NOT_FOUND_IN_DOCUMENT.value
        if "doesn't appear to address" not in cleaned_answer:
            cleaned_answer = f"This document doesn't appear to address this question. Consider checking your local tenant-rights statute or speaking with a lawyer, since this affects your rights."

    # 7. Record assistant message and citations
    assistant_msg_id = str(uuid.uuid4())
    assistant_msg = Message(
        id=assistant_msg_id,
        conversation_id=conv_id,
        role="assistant",
        content=cleaned_answer,
        status=final_status,
        confidence_note=confidence_note,
    )
    db.add(assistant_msg)

    saved_citations = []
    for cit in verified_citations:
        cit_record = MessageCitation(
            id=str(uuid.uuid4()),
            message_id=assistant_msg_id,
            chunk_id=cit.get("chunk_id"),
            page=cit.get("page", 1),
            clause_id=cit.get("clause_id"),
            quote=cit.get("quote"),
            verified=True,
        )
        db.add(cit_record)
        saved_citations.append(CitationResponse(
            chunk_id=cit.get("chunk_id"),
            page=cit.get("page", 1),
            clause_id=cit.get("clause_id"),
            quote=cit.get("quote"),
            verified=True,
            match_score=cit.get("match_score", 1.0),
        ))

    db.commit()

    return AskResponse(
        answer=cleaned_answer,
        status=final_status,
        citations=saved_citations,
        confidence_note=confidence_note,
        conversation_id=conv_id,
    )


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
def get_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve full conversation history."""
    conv = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id,
    ).first()

    if not conv:
        other_conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if other_conv:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access forbidden: you do not have permission to view this conversation.",
            )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")

    messages_out = []
    for m in conv.messages:
        cits_out = [
            CitationResponse(
                chunk_id=c.chunk_id,
                page=c.page,
                clause_id=c.clause_id,
                quote=c.quote,
                verified=c.verified,
            )
            for c in m.citations
        ]
        messages_out.append(MessageResponse(
            id=m.id,
            role=m.role,
            content=m.content,
            status=m.status.value if hasattr(m.status, "value") else str(m.status),
            citations=cits_out,
            created_at=m.created_at,
        ))

    return ConversationResponse(
        id=conv.id,
        document_id=conv.document_id,
        messages=messages_out,
        created_at=conv.created_at,
    )
