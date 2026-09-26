import re
from typing import List, Dict, Optional, Any


# Regex detecting lease clause boundaries such as:
# "1. RENT", "Section 3. Security Deposit", "ARTICLE IV: TERMINATION", "Clause 9(a) Notice"
CLAUSE_HEADING_PATTERN = re.compile(
    r'(?m)^(?:\s*(?:SECTION|ARTICLE|CLAUSE|PARAGRAPH)\s+([0-9A-Z\.\(\)]+)|\s*([0-9]{1,2}(?:\.[0-9A-Za-z\(\)]+)*))\s*[:\.\-—]?\s*([^\n]*)',
    re.IGNORECASE
)


def fallback_sliding_window_chunking(
    text: str,
    page_number: int,
    clause_id: Optional[str] = None,
    heading: Optional[str] = None,
    chunk_size_words: int = 450,
    overlap_words: int = 75,
) -> List[Dict[str, Any]]:
    """Splits text into sliding window chunks when no structure or very long text."""
    words = text.split()
    if not words:
        return []

    chunks = []
    start_idx = 0
    step = max(1, chunk_size_words - overlap_words)

    while start_idx < len(words):
        end_idx = min(start_idx + chunk_size_words, len(words))
        chunk_words = words[start_idx:end_idx]
        chunk_text = " ".join(chunk_words)

        chunks.append({
            "page_number": page_number,
            "clause_id": clause_id,
            "section_heading": heading,
            "text": chunk_text,
            "token_count": len(chunk_words),
            "start_char": 0,
            "end_char": len(chunk_text),
        })

        if end_idx >= len(words):
            break
        start_idx += step

    return chunks


def chunk_document_pages(pages_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Structure-aware chunker that identifies numbered clauses and sections
    tied to page numbers, with token fallback for unstructured content.
    """
    all_chunks = []

    for page in pages_data:
        page_num = page["page_number"]
        raw_text = page["raw_text"]

        # Find all clause headings in this page
        matches = list(CLAUSE_HEADING_PATTERN.finditer(raw_text))

        if not matches:
            # Fallback for page with no clear clause headings
            page_chunks = fallback_sliding_window_chunking(
                text=raw_text,
                page_number=page_num,
                clause_id=f"p{page_num}",
                heading=f"Page {page_num}",
            )
            all_chunks.extend(page_chunks)
            continue

        # Split text by matches
        for i, match in enumerate(matches):
            clause_num = match.group(1) or match.group(2)
            heading_title = (match.group(3) or "").strip()
            full_heading = f"{clause_num} {heading_title}".strip() if heading_title else clause_num

            start_pos = match.start()
            end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(raw_text)
            clause_body = raw_text[start_pos:end_pos].strip()

            words_count = len(clause_body.split())

            # If clause is excessively long (> 600 words), sub-chunk it
            if words_count > 600:
                sub_chunks = fallback_sliding_window_chunking(
                    text=clause_body,
                    page_number=page_num,
                    clause_id=clause_num,
                    heading=full_heading,
                )
                all_chunks.extend(sub_chunks)
            else:
                all_chunks.append({
                    "page_number": page_num,
                    "clause_id": clause_num,
                    "section_heading": full_heading,
                    "text": clause_body,
                    "token_count": words_count,
                    "start_char": start_pos,
                    "end_char": end_pos,
                })

    # Ensure at least 1 chunk exists even if file is empty
    if not all_chunks and pages_data:
        all_chunks.append({
            "page_number": 1,
            "clause_id": "1",
            "section_heading": "Document Content",
            "text": pages_data[0]["raw_text"] or "Empty Document",
            "token_count": 1,
            "start_char": 0,
            "end_char": len(pages_data[0]["raw_text"] or ""),
        })

    return all_chunks
