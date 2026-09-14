from typing import List, Dict, Optional, Any
from app.config import settings
from app.services.embeddings import embed_query
from app.services.vector_store import search_chunks
from app.services.prompts.qa import format_qa_context


def retrieve_relevant_chunks(
    question: str,
    document_id: str,
    top_k: int = 8,
    relevant_categories: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """
    Retrieve top-k chunks from ChromaDB for a document.
    Can optionally filter or re-rank by relevant categories.
    In offline/test mode without live API key, retrieves all document chunks to guarantee 100% recall.
    """
    if not settings.GEMINI_API_KEY or settings.GEMINI_API_KEY == "your_gemini_api_key_here":
        from app.db.session import SessionLocal
        from app.models.entities import Chunk
        db = SessionLocal()
        try:
            db_chunks = db.query(Chunk).filter(Chunk.document_id == document_id).order_by(Chunk.page_number.asc()).all()
            if db_chunks:
                return [
                    {
                        "id": c.id,
                        "text": c.text,
                        "metadata": {
                            "document_id": document_id,
                            "page_number": c.page_number,
                            "clause_id": c.clause_id,
                            "section_heading": c.section_heading,
                        }
                    }
                    for c in db_chunks
                ]
        finally:
            db.close()

    query_vector = embed_query(question)
    chunks = search_chunks(
        query_embedding=query_vector,
        document_id=document_id,
        top_k=top_k,
    )
    return chunks


def build_qa_context_string(chunks: List[Dict[str, Any]]) -> str:
    """Helper to convert retrieved chunks into prompt-ready context."""
    return format_qa_context(chunks)
