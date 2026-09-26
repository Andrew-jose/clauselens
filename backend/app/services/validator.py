import re
import difflib
from typing import Dict, List, Optional, Tuple, Any
from sqlalchemy.orm import Session
from app.models.entities import Chunk, AuditEvent, GroundedStatus


def normalize_text(text: str) -> str:
    """Normalize text by collapsing whitespace, stripping non-alphanumerics, and lowercasing."""
    if not text:
        return ""
    # Replace any whitespace sequence with single space
    cleaned = re.sub(r'\s+', ' ', text.strip().lower())
    # Normalize fancy quotes and dashes
    cleaned = cleaned.replace('“', '"').replace('”', '"').replace('’', "'").replace('‘', "'")
    cleaned = cleaned.replace('—', '-').replace('–', '-')
    return cleaned


def compute_fuzzy_overlap(quote: str, target: str) -> float:
    """
    Compute token/character overlap between quote and target text.
    Returns a score between 0.0 and 1.0.
    Uses token-set pre-filter to bypass expensive SequenceMatcher for non-matching chunks.
    """
    norm_quote = normalize_text(quote)
    norm_target = normalize_text(target)

    if not norm_quote:
        return 0.0

    # 1. Direct exact or normalized substring
    if norm_quote in norm_target:
        return 1.0

    # 2. Token set overlap if target is large: find best sliding window in target
    quote_tokens = norm_quote.split()
    target_tokens = norm_target.split()

    if not quote_tokens or not target_tokens:
        return 0.0

    # Fast pruning: if target doesn't even contain 70% of quote unique tokens, ratio cannot reach 0.90
    quote_token_set = set(quote_tokens)
    target_token_set = set(target_tokens)
    common_tokens = quote_token_set & target_token_set
    if len(common_tokens) / len(quote_token_set) < 0.70:
        return 0.0

    window_size = len(quote_tokens)
    max_ratio = 0.0

    # Sliding window search over target tokens
    # Window variation between len(quote_tokens)-2 and len(quote_tokens)+2
    for w in range(max(1, window_size - 3), min(len(target_tokens) + 1, window_size + 4)):
        for i in range(len(target_tokens) - w + 1):
            window_slice = " ".join(target_tokens[i:i + w])
            ratio = difflib.SequenceMatcher(None, norm_quote, window_slice).ratio()
            if ratio > max_ratio:
                max_ratio = ratio
                if max_ratio >= 0.98:
                    return 1.0

    return max_ratio


def verify_citation_quote(quote: str, chunk_text: str, threshold: float = 0.90) -> Tuple[bool, float]:
    """
    Verify if a citation's quote actually exists in the source chunk text.
    Requires at least 90% fuzzy match overlap to tolerate whitespace/OCR noise.
    """
    if not quote or not chunk_text:
        return False, 0.0

    overlap = compute_fuzzy_overlap(quote, chunk_text)
    is_valid = overlap >= threshold
    return is_valid, overlap


def validate_citations_against_db(
    citations: List[Dict[str, Any]],
    db: Session,
    user_id: Optional[str] = None,
    document_id: Optional[str] = None,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], str]:
    """
    Validates a list of candidate citations returned by the LLM.
    Returns:
        verified_citations: list of verified citations
        failed_citations: list of rejected/unsupported citations
        recommended_status: "grounded_high" | "grounded_low" | "not_found_in_document"
    """
    verified = []
    failed = []
    cached_doc_chunks = None

    for cit in citations:
        chunk_id = cit.get("chunk_id")
        quote = cit.get("quote", "").strip()

        # If no quote or no chunk_id, citation is invalid
        if not quote:
            failed.append({**cit, "reason": "Empty quote"})
            continue

        chunk = None
        if chunk_id:
            chunk = db.query(Chunk).filter(Chunk.id == chunk_id).first()

        # If chunk not found by chunk_id, attempt to match against document chunks (lazily cached)
        if not chunk and document_id:
            if cached_doc_chunks is None:
                cached_doc_chunks = db.query(Chunk).filter(Chunk.document_id == document_id).all()
            for cand_chunk in cached_doc_chunks:
                is_match, score = verify_citation_quote(quote, cand_chunk.text)
                if is_match:
                    chunk = cand_chunk
                    cit["chunk_id"] = chunk.id
                    cit["page"] = chunk.page_number
                    cit["clause_id"] = chunk.clause_id
                    break

        if not chunk:
            failed.append({**cit, "reason": "Chunk not found"})
            continue

        is_valid, score = verify_citation_quote(quote, chunk.text)
        if is_valid:
            verified.append({
                "chunk_id": chunk.id,
                "page": chunk.page_number,
                "clause_id": chunk.clause_id or cit.get("clause_id"),
                "quote": quote,
                "verified": True,
                "match_score": score,
            })
        else:
            failed.append({
                **cit,
                "reason": f"Quote failed verification (match score: {score:.2f} < 0.90)",
                "match_score": score,
            })

    # Log audit event for any validation failure
    if failed:
        audit = AuditEvent(
            user_id=user_id,
            event_type="validation_failure",
            metadata_json={
                "document_id": document_id,
                "failed_count": len(failed),
                "failures": failed,
            },
        )
        db.add(audit)
        db.commit()

    # Determine recommended status
    if verified and not failed:
        status = GroundedStatus.GROUNDED_HIGH.value
    elif verified and failed:
        status = GroundedStatus.GROUNDED_LOW.value
    else:
        status = GroundedStatus.NOT_FOUND_IN_DOCUMENT.value

    return verified, failed, status
