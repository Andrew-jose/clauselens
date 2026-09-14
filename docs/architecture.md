# ClauseLens Architecture

## System Overview
ClauseLens is an evidence-first residential lease assistant designed to eliminate hallucinations by anchoring every tenant-facing claim to verified lease text.

### Architecture Layers
1. **Frontend (React + TypeScript + Vite + Tailwind CSS)**
   - Document-Native Workspace with central Document Viewer and permanent Evidence Rail.
   - Modules: Landing, Dashboard, Upload, Clause Explorer, Risk Radar, Ask Document, Compare, Situation Panel, Action Plan, Lawyer Prep.
   - Accessibility: WCAG AA, automated axe-core scanning.
2. **FastAPI Backend (Python)**
   - Routers: `auth`, `documents`, `clauses`, `findings`, `qa`, `compare`, `situation`, `actionplan`, `health`.
   - Security: Magic-byte upload validation, rate-limiting (`slowapi`), JWT tenant isolation.
3. **Evidence & Anti-Hallucination Pipeline**
   - PyMuPDF (fitz) + python-docx structure-aware chunker.
   - Primary embeddings: `gemini-embedding-001` with lazy local `sentence-transformers` fallback.
   - ChromaDB vector store (local embedded).
   - Independent Code-Level Citation Validator (§7.3): Verifies that candidate quotes exist in chunks (≥90% fuzzy overlap).
   - Second-Pass Self-Check Verifier (§7.6): Validates all sentences have verified citation anchors before returning answer.
   - Regex guards preventing fabricated statute citations or case names.
4. **Data Persistence**
   - SQLite (via SQLAlchemy) for metadata, audit logs, conversations, and clauses.

## Implementation Phases
- Phase 0: Scaffold & Foundation (FastAPI health, Vite skeleton, CI)
- Phase 1: Ingestion & Storage (PDF/DOCX parsing, chunking, ChromaDB, SQLite)
- Phase 2: Evidence-Grounded Q&A & Citation Validator
- Phase 3: Clause Extraction & Risk Radar
- Phase 4: Side-by-Side Lease Comparison
- Phase 5: Situation Router, Action Plan & Lawyer Prep (ReportLab PDF)
- Phase 6: Frontend Workspace & Accessibility CI (axe-core)
- Phase 7: Security, Auth & Rate Limiting
- Phase 8: Polish, Demo Scenarios & README
