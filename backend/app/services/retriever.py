from typing import List, Dict, Optional, Any
from app.config import settings
from app.services.embeddings import embed_query
from app.services.vector_store import search_chunks
from app.services.prompts.qa import format_qa_context


CATEGORY_KEYWORDS = {
    "rent_fees": ["rent", "due date", "late fee", "payment", "utilities", "monthly rent"],
    "term_renewal": ["term", "commence", "expire", "renewal", "renew", "notice to vacate", "notice period"],
    "termination_penalties": ["early termination", "liquidated damages", "penalty", "break lease", "forfeit", "default", "breach"],
    "repairs_habitability": ["repair", "maintenance", "habitability", "condition", "damage", "mold", "pest", "heat"],
    "access_privacy": ["access", "entry", "inspection", "24 hours", "notice of entry", "privacy", "landlord entry"],
    "deposit": ["security deposit", "deposit", "itemized", "deductions", "refund", "holding"],
    "restrictions": ["pet", "sublet", "assignment", "guest", "noise", "smoking", "alteration"],
    "other": ["miscellaneous", "severability", "entire agreement", "governing law"],
}


def rerank_chunks_by_categories(
    chunks: List[Dict[str, Any]],
    relevant_categories: List[str],
    document_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Re-rank chunks dynamically based on the Situation Router's relevant categories.
    Chunks matching the relevant categories receive higher priority and move to the top.
    """
    if not relevant_categories or not chunks:
        return chunks

    matching_clause_ids = set()
    if document_id:
        try:
            from app.db.session import SessionLocal
            from app.models.entities import Clause
            db = SessionLocal()
            clauses = db.query(Clause).filter(
                Clause.document_id == document_id,
                Clause.category.in_(relevant_categories)
            ).all()
            for cl in clauses:
                if cl.clause_number:
                    matching_clause_ids.add(cl.clause_number.lower().strip())
                if cl.id:
                    matching_clause_ids.add(cl.id)
            db.close()
        except Exception:
            pass

    scored_chunks = []
    for idx, chunk in enumerate(chunks):
        score = 0
        metadata = chunk.get("metadata", {})
        c_id = str(metadata.get("clause_id") or "").lower().strip()
        text_lower = chunk.get("text", "").lower()
        heading_lower = str(metadata.get("section_heading") or "").lower()

        # Check direct clause match
        if c_id and c_id in matching_clause_ids:
            score += 20

        # Check category keywords
        for cat in relevant_categories:
            keywords = CATEGORY_KEYWORDS.get(cat, [])
            for kw in keywords:
                if kw in heading_lower:
                    score += 10
                elif kw in text_lower:
                    score += 3

        # Stability bonus based on initial retrieval rank
        initial_rank_penalty = idx * 0.1
        final_score = score - initial_rank_penalty
        scored_chunks.append((final_score, idx, chunk))

    # Sort descending by score
    scored_chunks.sort(key=lambda item: item[0], reverse=True)
    return [item[2] for item in scored_chunks]


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
                raw_chunks = [
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
                if relevant_categories:
                    return rerank_chunks_by_categories(raw_chunks, relevant_categories, document_id)
                return raw_chunks
        finally:
            db.close()

    query_vector = embed_query(question)
    chunks = search_chunks(
        query_embedding=query_vector,
        document_id=document_id,
        top_k=top_k,
    )

    if relevant_categories:
        chunks = rerank_chunks_by_categories(chunks, relevant_categories, document_id)

    return chunks


def build_qa_context_string(chunks: List[Dict[str, Any]]) -> str:
    """Helper to convert retrieved chunks into prompt-ready context."""
    return format_qa_context(chunks)
