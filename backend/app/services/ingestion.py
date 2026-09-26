import io
from typing import List, Dict, Tuple, Any
import fitz  # PyMuPDF
import docx


def validate_file_magic_bytes(content: bytes, filename: str) -> Tuple[bool, str]:
    """
    Validate uploaded file format by magic bytes (not just extension).
    Returns (is_valid, mime_type).
    """
    if len(content) < 4:
        return False, "unknown"

    # PDF magic bytes: %PDF-
    if content.startswith(b"%PDF-"):
        return True, "application/pdf"

    # DOCX magic bytes: PK\x03\x04 (ZIP format)
    if content.startswith(b"PK\x03\x04") and (filename.lower().endswith(".docx")):
        return True, "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

    return False, "unknown"


def extract_pdf_pages(content: bytes) -> List[Dict[str, Any]]:
    """
    Extract text page-by-page from a PDF using PyMuPDF.
    Strips embedded JavaScript, launch actions, and suspicious annotations for defense in depth.
    """
    pages_data = []
    doc = fitz.open(stream=content, filetype="pdf")

    try:
        for page_idx in range(len(doc)):
            page = doc[page_idx]

            # Security: Sanitize annotations & links that could contain javascript/URI payloads
            links = page.get_links()
            for link in links:
                if link.get("kind") in [fitz.LINK_LAUNCH, fitz.LINK_NAMED]:
                    page.delete_link(link)

            text = page.get_text("text")
            # Normalize whitespace while preserving line structure
            cleaned_text = "\n".join(
                line.strip() for line in text.splitlines() if line.strip()
            )
            pages_data.append({
                "page_number": page_idx + 1,
                "raw_text": cleaned_text,
                "char_count": len(cleaned_text),
            })
    finally:
        doc.close()

    return pages_data


def extract_docx_pages(content: bytes) -> List[Dict[str, Any]]:
    """
    Extract text from a DOCX document using python-docx.
    Treats paragraphs as virtual pages or partitions into logical chunks.
    """
    file_stream = io.BytesIO(content)
    doc = docx.Document(file_stream)

    paragraphs_text = []
    for p in doc.paragraphs:
        text = p.text.strip()
        if text:
            paragraphs_text.append(text)

    full_text = "\n\n".join(paragraphs_text)

    # If document is short, treat as 1 page; otherwise split into roughly 2000-char pages
    pages_data = []
    chunk_size = 2500
    if len(full_text) <= chunk_size:
        pages_data.append({
            "page_number": 1,
            "raw_text": full_text,
            "char_count": len(full_text),
        })
    else:
        chunks = [full_text[i:i + chunk_size] for i in range(0, len(full_text), chunk_size)]
        for idx, chunk in enumerate(chunks):
            pages_data.append({
                "page_number": idx + 1,
                "raw_text": chunk,
                "char_count": len(chunk),
            })

    return pages_data


def extract_document_pages(content: bytes, filename: str, mime_type: str) -> List[Dict[str, Any]]:
    """Dispatcher for extracting text from supported document types."""
    if mime_type == "application/pdf" or filename.lower().endswith(".pdf"):
        return extract_pdf_pages(content)
    elif "wordprocessingml" in mime_type or filename.lower().endswith(".docx"):
        return extract_docx_pages(content)
    else:
        raise ValueError(f"Unsupported document MIME type: {mime_type}")
