# AGENTS.md — ClauseLens

## Non-negotiable product rule
Every AI-generated claim about a user's uploaded document MUST carry a
citation (document, page, clause_id, exact quote), and every citation MUST
be verified in code (substring/fuzzy match against the actual stored chunk
text) before being shown to the user as "grounded." Never relax this to
ship a feature faster.

## Stack (do not substitute)
- Frontend: React + TypeScript + Vite + Tailwind CSS
- Backend: Python + FastAPI, SQLAlchemy, Pydantic v2
- Vector store: ChromaDB (embedded, persisted to a local directory)
- Metadata DB: SQLite (SQLAlchemy), Postgres-compatible schema
- AI: Gemini API — Flash-tier model for extraction/Q&A, Pro-tier model
  only for comparison synthesis and action-plan narrative. Verify the
  exact current model IDs in Google AI Studio before hardcoding them.
- PDF/DOCX parsing: PyMuPDF (fitz) for PDFs, python-docx for Word files

## Hard constraints
- Repository must stay under 10 MB. Never commit node_modules, venv,
  __pycache__, *.db, chroma_data/, .env, or sample PDFs over ~200KB.
- Single git branch only. Commit incrementally with clear messages.
- Never commit an API key or secret. Read them from environment
  variables only (.env.example may list variable names, never values).
- Never fabricate legal citations, statute numbers, or case names in any
  AI output field, anywhere in the app.

## Working style
- Follow the phase order in `docs/architecture.md` (Phase 0 → Phase 8).
  Do not skip ahead to frontend polish before the Q&A + citation
  validator (Phase 2) is working and tested.
- Write pytest tests alongside each backend phase, not at the end.
- After each phase, run the test suite and report results before
  moving on.
- Use the browser tool to visually verify any UI change with a
  screenshot before marking a frontend task done.
