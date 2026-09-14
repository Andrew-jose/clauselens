import os
import sys
import uuid
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(backend_dir))

from app.db.session import init_db, SessionLocal
from app.core.security import DEMO_USER_EMAIL, get_password_hash
from app.models.entities import (
    User,
    Document,
    DocumentPage,
    Chunk,
    AuditEvent,
)
from app.services.ingestion import validate_file_magic_bytes, extract_document_pages
from app.services.chunker import chunk_document_pages
from app.services.embeddings import embed_texts
from app.services.vector_store import index_chunks
from app.services.analysis import analyze_document
from app.services.comparator import compare_documents
from app.services.situation_router import classify_situation, generate_action_plan, generate_lawyer_questions


def seed_document(file_path: str, filename: str, user_id: str, db) -> Document:
    """Ingests and indexes a fixture lease PDF into the database and ChromaDB."""
    existing_doc = db.query(Document).filter(Document.filename == filename, Document.user_id == user_id).first()
    if existing_doc:
        print(f"  [i] Document '{filename}' already exists (ID: {existing_doc.id[:8]}...). Skipping re-ingestion.")
        return existing_doc

    with open(file_path, "rb") as f:
        content = f.read()

    is_valid, detected_mime = validate_file_magic_bytes(content, filename)
    if not is_valid:
        raise ValueError(f"Invalid file format for {filename}")

    doc_id = str(uuid.uuid4())
    doc = Document(
        id=doc_id,
        user_id=user_id,
        filename=filename,
        mime_type=detected_mime,
        status="processing",
    )
    db.add(doc)
    db.commit()

    # 1. Page extraction
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

    # 3. Vector embedding
    chunk_texts = [c["text"] for c in raw_chunks]
    embeddings = embed_texts(chunk_texts, task_type="retrieval_document")

    # 4. Save chunks
    chunk_records = []
    for c in raw_chunks:
        chunk_id = str(uuid.uuid4())
        c["id"] = chunk_id
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

    # 5. ChromaDB index
    index_chunks(doc_id, chunk_records, embeddings)
    doc.status = "ready"

    # Audit event
    db.add(AuditEvent(
        id=str(uuid.uuid4()),
        user_id=user_id,
        event_type="upload",
        metadata_json={"document_id": doc_id, "filename": filename, "pages": doc.page_count, "chunks": len(raw_chunks)},
    ))
    db.commit()
    db.refresh(doc)
    print(f"  [+] Ingested '{filename}' (ID: {doc.id[:8]}..., Pages: {doc.page_count}, Chunks: {len(raw_chunks)})")
    return doc


def run_seed():
    print("==========================================================")
    print("   ClauseLens Hackathon Demo Seeder (Priya's Scenario)   ")
    print("==========================================================")

    init_db()
    db = SessionLocal()

    try:
        # 1. Guarantee demo user
        demo_user = db.query(User).filter(User.email == DEMO_USER_EMAIL).first()
        if not demo_user:
            demo_user = User(
                id=str(uuid.uuid4()),
                email=DEMO_USER_EMAIL,
                password_hash=get_password_hash("clauselens_demo_pass"),
            )
            db.add(demo_user)
            db.commit()
            db.refresh(demo_user)
            print(f"[+] Created demo tenant account: {demo_user.email}")
        else:
            print(f"[i] Using demo tenant account: {demo_user.email}")

        # 2. Ingest Lease 1: Current Lease
        fixtures_dir = backend_dir / "tests" / "fixtures"
        lease_a_path = str(fixtures_dir / "sample_lease.pdf")
        lease_b_path = str(fixtures_dir / "sample_lease_renewal.pdf")

        print("\n--- 1. Ingesting Leases ---")
        doc_a = seed_document(lease_a_path, "Current_Lease_2025.pdf", demo_user.id, db)
        doc_b = seed_document(lease_b_path, "Renewal_Offer_2026.pdf", demo_user.id, db)

        # 3. Analyze Leases
        print("\n--- 2. Extracting Clauses & Risk Radar Findings ---")
        if not doc_a.clauses:
            print("  Analyzing Current Lease...")
            analyze_document(doc_a.id, db)
        print(f"  [OK] Current Lease: {len(doc_a.clauses)} clauses, {len(doc_a.findings)} risk findings.")

        if not doc_b.clauses:
            print("  Analyzing Renewal Offer...")
            analyze_document(doc_b.id, db)
        print(f"  [OK] Renewal Offer: {len(doc_b.clauses)} clauses, {len(doc_b.findings)} risk findings.")

        # 4. Generate Side-by-Side Comparison
        print("\n--- 3. Generating Lease Comparison (Current vs. Renewal) ---")
        session = compare_documents(doc_a.id, doc_b.id, demo_user.id, db)
        print(f"  [OK] Comparison Session generated (ID: {session.id[:8]}..., {len(session.findings)} clause deltas detected).")

        # 5. Route Demo Situation (Priya's Scenario: §18)
        print("\n--- 4. Routing Demo Context (Priya's Relocation Scenario) ---")
        demo_situation_text = "I might need to leave early if my new job relocates me in 6 months."
        classification = classify_situation(demo_situation_text)
        sit_payload = {**classification, "context_text": demo_situation_text}

        print(f"  Classified Situation: '{classification['situation_type']}' (Urgency: {classification['urgency'].upper()})")
        print(f"  Prioritized Categories: {', '.join(classification.get('relevant_categories', []))}")

        # Generate Action Plan and Lawyer Questions
        action_plan = generate_action_plan(doc_b.id, sit_payload, db, demo_user.id)
        print(f"  [OK] Action Plan generated with {len(action_plan['steps'])} prioritized steps.")

        questions = generate_lawyer_questions(doc_b.id, sit_payload, db)
        print(f"  [OK] Lawyer consultation questions generated ({len(questions)} prioritized inquiries).")

        print("\n==========================================================")
        print("  [OK] Demo Seed Complete! Database is primed for live demo.")
        print("==========================================================")
        print(f"  Primary Lease ID: {doc_b.id}")
        print(f"  Comparison ID:    {session.id}")
        print(f"  Demo Scenario:    \"{demo_situation_text}\"")
        print("==========================================================\n")

    finally:
        db.close()


if __name__ == "__main__":
    run_seed()
