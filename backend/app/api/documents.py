import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request, status
from sqlalchemy.orm import Session
from app.config import settings
from app.db.session import get_db
from app.core.security import get_current_user
from app.core.rate_limit import limiter
from app.models.entities import (
    User,
    Document,
    DocumentPage,
    Chunk,
    AuditEvent,
)
from app.schemas.documents import (
    DocumentResponse,
    DocumentDetailResponse,
    DocumentStatusResponse,
    ChunkResponse,
)
from app.services.ingestion import validate_file_magic_bytes, extract_document_pages
from app.services.chunker import chunk_document_pages
from app.services.embeddings import embed_texts
from app.services.vector_store import index_chunks, delete_document_vectors

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(settings.UPLOAD_RATE_LIMIT_PER_MINUTE)
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Upload a residential lease (PDF or DOCX).
    Validates MIME type by magic bytes and enforces size limits (max 15 MB).
    Extracts pages, generates structure-aware chunks, and indexes into ChromaDB.
    """
    filename = file.filename or "lease_document"

    # Read content
    content = await file.read()
    file_size = len(content)

    if file_size > settings.MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)} MB.",
        )

    # Magic byte validation
    is_valid, detected_mime = validate_file_magic_bytes(content, filename)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Unsupported or invalid file format. Only legitimate PDF and DOCX files are accepted.",
        )

    doc_id = str(uuid.uuid4())
    doc = Document(
        id=doc_id,
        user_id=current_user.id,
        filename=filename,
        mime_type=detected_mime,
        status="processing",
    )
    db.add(doc)
    db.commit()

    try:
        # 1. Page extraction with sanitization
        pages_data = extract_document_pages(content, filename, detected_mime)
        doc.page_count = len(pages_data)

        for p in pages_data:
            page_record = DocumentPage(
                id=str(uuid.uuid4()),
                document_id=doc_id,
                page_number=p["page_number"],
                raw_text=p["raw_text"],
                char_count=p["char_count"],
            )
            db.add(page_record)

        # 2. Structure-aware chunking
        raw_chunks = chunk_document_pages(pages_data)

        # 3. Embedding generation
        chunk_texts = [c["text"] for c in raw_chunks]
        embeddings = embed_texts(chunk_texts, task_type="retrieval_document")

        # 4. Save Chunk models to SQLite
        chunk_records = []
        for i, c in enumerate(raw_chunks):
            chunk_id = str(uuid.uuid4())
            c["id"] = chunk_id  # for Chroma index
            chunk_record = Chunk(
                id=chunk_id,
                document_id=doc_id,
                page_number=c["page_number"],
                clause_id=c["clause_id"],
                section_heading=c["section_heading"],
                text=c["text"],
                start_char=c["start_char"],
                end_char=c["end_char"],
                token_count=c["token_count"],
                vector_ref=chunk_id,
            )
            db.add(chunk_record)
            chunk_records.append(c)

        # 5. Index into ChromaDB
        index_chunks(doc_id, chunk_records, embeddings)

        doc.status = "ready"

        # Log audit event
        audit = AuditEvent(
            id=str(uuid.uuid4()),
            user_id=current_user.id,
            event_type="upload",
            metadata_json={"document_id": doc_id, "filename": filename, "pages": doc.page_count, "chunks": len(raw_chunks)},
        )
        db.add(audit)
        db.commit()
        db.refresh(doc)
        return doc

    except Exception as e:
        doc.status = "failed"
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process document: {str(e)}",
        )


@router.get("", response_model=List[DocumentResponse])
def list_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all documents owned by the current user."""
    return db.query(Document).filter(Document.user_id == current_user.id).order_by(Document.created_at.desc()).all()


@router.get("/{document_id}", response_model=DocumentDetailResponse)
def get_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get document details with counts."""
    doc = db.query(Document).filter(Document.id == document_id, Document.user_id == current_user.id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    chunks_count = db.query(Chunk).filter(Chunk.document_id == document_id).count()
    return DocumentDetailResponse(
        id=doc.id,
        filename=doc.filename,
        mime_type=doc.mime_type,
        page_count=doc.page_count,
        status=doc.status,
        summary=doc.summary,
        created_at=doc.created_at,
        key_terms=doc.key_terms or [],
        chunks_count=chunks_count,
        clauses_count=len(doc.clauses),
        findings_count=len(doc.findings),
    )


@router.get("/{document_id}/status", response_model=DocumentStatusResponse)
def get_document_status(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Poll document processing status."""
    doc = db.query(Document).filter(Document.id == document_id, Document.user_id == current_user.id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    chunks_count = db.query(Chunk).filter(Chunk.document_id == document_id).count()
    return DocumentStatusResponse(
        status=doc.status,
        page_count=doc.page_count,
        chunks_count=chunks_count,
        message="Document ready for evidence analysis." if doc.status == "ready" else "Processing...",
    )


@router.get("/{document_id}/chunks", response_model=List[ChunkResponse])
def get_document_chunks(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve all chunks for a document."""
    doc = db.query(Document).filter(Document.id == document_id, Document.user_id == current_user.id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    return db.query(Chunk).filter(Chunk.document_id == document_id).order_by(Chunk.page_number.asc()).all()


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a document, its database records, and ChromaDB vector embeddings."""
    doc = db.query(Document).filter(Document.id == document_id, Document.user_id == current_user.id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    # Remove ChromaDB vectors
    delete_document_vectors(document_id)

    # Log audit event
    audit = AuditEvent(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        event_type="delete",
        metadata_json={"document_id": document_id, "filename": doc.filename},
    )
    db.add(audit)

    # Delete Document from DB (cascades to pages, chunks, clauses, findings)
    db.delete(doc)
    db.commit()
    return None
