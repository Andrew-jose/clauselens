import os
import pytest
from app.services.ingestion import extract_document_pages, validate_file_magic_bytes
from app.services.chunker import chunk_document_pages, fallback_sliding_window_chunking


@pytest.fixture
def sample_pdf_content():
    fixture_path = os.path.join(os.path.dirname(__file__), "..", "fixtures", "sample_lease.pdf")
    with open(fixture_path, "rb") as f:
        return f.read()


def test_validate_magic_bytes(sample_pdf_content):
    is_valid, mime = validate_file_magic_bytes(sample_pdf_content, "sample_lease.pdf")
    assert is_valid is True
    assert mime == "application/pdf"

    # Invalid fake PDF
    fake_content = b"This is not a real PDF file despite the extension"
    is_valid_fake, _ = validate_file_magic_bytes(fake_content, "fake.pdf")
    assert is_valid_fake is False


def test_extract_pdf_pages(sample_pdf_content):
    pages = extract_document_pages(sample_pdf_content, "sample_lease.pdf", "application/pdf")
    assert len(pages) >= 1
    assert pages[0]["page_number"] == 1
    assert "Priya Sharma" in pages[0]["raw_text"]
    assert "Clause 1." in pages[0]["raw_text"]


def test_structure_aware_chunker(sample_pdf_content):
    pages = extract_document_pages(sample_pdf_content, "sample_lease.pdf", "application/pdf")
    chunks = chunk_document_pages(pages)

    assert len(chunks) >= 5

    # Check for clause IDs extracted
    clause_ids = [c["clause_id"] for c in chunks if c["clause_id"]]
    assert any("1" in cid for cid in clause_ids)
    assert any("3" in cid for cid in clause_ids)
    assert any("9" in cid for cid in clause_ids)

    # Check that chunks contain actual text
    for chunk in chunks:
        assert len(chunk["text"]) > 10
        assert chunk["page_number"] >= 1
        assert chunk["token_count"] > 0


def test_fallback_sliding_window():
    unstructured_text = " ".join([f"Word{i}" for i in range(1000)])
    chunks = fallback_sliding_window_chunking(
        text=unstructured_text,
        page_number=2,
        chunk_size_words=200,
        overlap_words=50,
    )

    assert len(chunks) > 1
    assert chunks[0]["page_number"] == 2
    assert "Word0" in chunks[0]["text"]
