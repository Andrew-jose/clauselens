from typing import List, Dict, Optional, Any
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
    """
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
