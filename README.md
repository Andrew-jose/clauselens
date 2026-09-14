# ClauseLens 🔍
### *Every claim, traced to the clause it came from.*
**An Evidence-First Lease & Tenancy Assistant for the GenAI Legal Accessibility Challenge**

[![CI Status](https://github.com/clauselens/clauselens/actions/workflows/ci.yml/badge.svg)](https://github.com/clauselens/clauselens/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-3776AB.svg?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React 19](https://img.shields.io/badge/React-19-61DAFB.svg?logo=react&logoColor=black)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.7+-3178C6.svg?logo=typescript&logoColor=white)](https://typescriptlang.org)
[![Gemini 3.x](https://img.shields.io/badge/AI-Google%20Gemini-4285F4.svg?logo=google&logoColor=white)](https://aistudio.google.com)
[![WCAG 2.1 AA](https://img.shields.io/badge/Accessibility-WCAG%202.1%20AA%20(axe--core)-008080.svg)](https://www.w3.org/WAI/WCAG21/AA/)
[![Repository Size](https://img.shields.io/badge/Repo%20Size-%3C%201%20MB-success.svg)]()

---

## 1. Persona & Vertical Rationale

### The Chosen Persona: The Residential Tenant
Residential tenancy represents one of the most asymmetric legal relationships in modern life. When moving into a home, tenants are handed 10-to-25 page legal documents drafted by institutional landlords and property attorneys, packed with dense indemnities, liquidated damages, waiver of jury trial, automatic renewal traps, and strict notice forfeiture rules.

Tenants routinely face:
1. **Severe Information Asymmetry:** Signing under urgent moving deadlines without access to counsel.
2. **High Financial & Housing Stakes:** Forfeited deposits, surprise fees, and crippling early-termination penalties (often 2 to 4 months of rent).
3. **Dangerous Generic AI Chatbots:** Standard consumer LLMs hallucinate "standard rules" or answer from generic statutory knowledge that contradicts the specific lease in hand. A hallucinated answer in tenancy is not an inconvenience—it causes eviction or financial ruin.

### Why Tenant Won Over Other Verticals
| Persona | Real-world impact | Demonstrability | Feasibility | Verdict |
|---|---|---|---|---|
| **Residential Tenant** | **Very High** (Universal, asymmetric power, high financial stakes) | **Exceptional** (Every judge understands a lease in seconds) | **High** (Well-structured document family, reliable clause extraction) | **Chosen Champion** |
| Employment Offer / NDA | High | Moderate | Medium (Diverse structures, variable clauses) | Runner-up |
| Small Business Commercial | High | Low (Difficult in 4 minutes) | Low (Multi-faceted contracts, cross-statute) | Scope risk |
| Student / Freelancer | Medium | Moderate | Medium (Narrow financial focus) | Weak stakes |

---

## 2. The Core Differentiator: Anti-Hallucination Citation Validator

> **Non-Negotiable Product Rule (§7.3 of Blueprint):**
> *Every AI-generated claim about a user's uploaded document MUST carry a citation (document, page, clause_id, exact quote), and every citation MUST be verified in code before being shown to the user as "grounded." Unsupported claims are structurally blocked.*

```
                               ┌────────────────────────┐
                               │ User Prompt / Analysis │
                               └───────────┬────────────┘
                                           ▼
┌──────────────────┐           ┌────────────────────────┐
│ PyMuPDF Chunker  │──────────►│ ChromaDB Vector Store  │
│  & SQLite Store  │           └───────────┬────────────┘
└─────────┬────────┘                       │ Top-k Chunks (k=6)
          │                                ▼
          │                    ┌────────────────────────┐
          │                    │  Gemini Flash / Pro    │
          │                    │  Structured Extraction │
          │                    └───────────┬────────────┘
          │                                │ Raw Citations & Quotes
          │                                ▼
          │                    ┌────────────────────────┐
          └───────────────────►│   CITATION VALIDATOR   │◄── Code-Enforced
                               │  Fuzzy Token Match ≥90% │    Verification
                               └───────────┬────────────┘
                                           │
                      ┌────────────────────┴────────────────────┐
                      ▼                                         ▼
            [ Verified in Code ]                     [ Validation Failed ]
         🟢 Grounded (High/Medium)                  ⚪ Not in Document / Inferential
         Quote highlighted in document              Audited, quote stripped, user alerted
```

### How Grounding is Enforced in Code
1. **Fuzzy Token Overlap ($\ge 90\%$):** Rather than fragile exact substring matching (which fails due to OCR artifacts or whitespace normalization), the validator tokenizes the quote and chunk text, checks token sequence boundaries, and calculates a Levenshtein similarity ratio ($\ge 0.90$).
2. **Second-Pass Self-Check Verifier:** Prompts Gemini Flash to verify whether its plain-language answer is strictly supported by the extracted quotes.
3. **Statute Hallucination Guard:** A regex boundary guard (`§`, `Civ. Code`, `v.`, `Cal. Civ.`) rejects any fabricated statutory or case-law citations unless verified against document text.
4. **Audit Logging:** Every validation failure is recorded in the SQLite `AuditEvent` table for security monitoring.

---

## 3. Architecture & Tech Stack

```
┌────────────────────────────────────────────────────────────────────────┐
│                   BROWSER (React 19 + TypeScript + Vite)               │
│  Document Viewer · Evidence Rail · Risk Radar · Situation Router       │
│  Lease Comparator · Grounded Q&A · Lawyer Prep PDF Exporter            │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ REST API + Bearer JWT
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                     BACKEND (FastAPI + Python 3.11+)                   │
│  routers/ (auth, documents, qa, clauses, findings, compare, situation) │
│  services/ (validator, verifier, retriever, comparator, exporter)      │
│  core/ (security, tenancy isolation, slowapi rate limiting)            │
└──────────────┬────────────────────┬────────────────────┬───────────────┘
               ▼                    ▼                    ▼
┌──────────────────────┐ ┌──────────────────────┐ ┌──────────────────────┐
│  SQLite (SQLAlchemy) │ │ ChromaDB (Vector DB) │ │ Google Gemini API    │
│  15 Structured Models│ │ Embedded Local Store │ │ Flash (Extract/Q&A)  │
│  Audit Events & Log  │ │ Cosine Embeddings    │ │ Pro (Compare/Synth)  │
└──────────────────────┘ └──────────────────────┘ └──────────────────────┘
```

### Full Tech Stack (No Substitutions)
- **Frontend:** React 19, TypeScript, Vite, Tailwind CSS, Lucide Icons, HeadlessUI.
- **Backend:** Python 3.11+, FastAPI, SQLAlchemy, Pydantic v2, SlowAPI rate-limiting.
- **AI Models:**
  - **Gemini Flash (`gemini-3.8-flash`):** Primary workhorse for high-volume extraction, clause categorization, and grounded Q&A.
  - **Gemini Pro (`gemini-3.8-flash` free-tier / `gemini-3.x-pro`):** Deep comparative reasoning and action-plan narrative.
  - **Embedding Model (`gemini-embedding-001`):** High-precision vector indexing with offline fallback.
- **Storage:** SQLite metadata database + Embedded ChromaDB vector store.
- **Document Parsing:** PyMuPDF (`fitz`) with structure-aware chunking and JS stripping.
- **Export Engine:** ReportLab for branded legal consultation prep packets.

---

## 4. Key Assumptions & Scope Boundaries

- **Input Formats:** Digital PDF and DOCX documents with selectable text layers. (Scanned image PDFs requiring OCR are out of MVP scope).
- **Domain Scope:** Residential tenancy leases (1–25 pages). The architecture generalizes to employment offers or commercial leases, but is specialized for tenants for the competition.
- **Legal Role:** ClauseLens provides information triage, clause translation, and consult preparation—**never unauthorized practice of law (UPL)**. Visible responsible AI disclaimers are persistently rendered.

---

## 5. Live Demo Script: Priya's 4-Minute Walkthrough (§18)

**Scenario:** Priya is deciding whether to sign a renewal offer on her apartment or prepare to break her lease in 6 months due to an unexpected job relocation.

| Step | Action | What Judges Notice |
|---|---|---|
| **1. Seed & Ingest** | Run `python backend/app/scripts/seed_demo.py` or drag-and-drop `Current_Lease_2025.pdf` and `Renewal_Offer_2026.pdf`. | Visible processing pipeline; instant chunking and vector indexing. |
| **2. Analysis Dashboard** | Dashboard opens with executive summary, key terms, and Risk Radar already populated. | High-density structured view, not an intimidating blank chat box. |
| **3. Risk Radar & Evidence Rail** | Click on the **High Severity** finding: *Early Termination Penalty Increased*. | Document pane jumps to Page 2, Clause 9, highlighting the exact text: `three (3) months' rent ($7,950.00)`. Real page, real text. |
| **4. Situation Router** | Enter context: *"I might need to leave early if my new job relocates me in 6 months."* | The Situation Router dynamically classifies context to **Termination (Medium Urgency)** and reprioritizes the Action Plan live. |
| **5. Evidence-Grounded Q&A** | Ask: *"What is my penalty if I leave early?"* → Grounded answer with citation chip.<br>Ask out-of-scope: *"Is 60 days notice legal in California?"* | Grounded answer cites Clause 9. Out-of-scope question triggers explicit **⚪ Not found in document** status with hedge—proving the system knows what it doesn't know. |
| **6. Side-by-Side Comparison** | Click **Compare Leases** tab. | Clause-level diff table flags monthly rent increase ($2,400 → $2,650) and penalty increase ($4,800 → $7,950) with dual citation anchors. |
| **7. Lawyer-Prep Packet** | Click **Download PDF Packet**. | Streams a clean, branded PDF containing an executive summary, high-severity findings, and prioritized consultation questions ready for an attorney. |

---

## 6. Judge Differentiation Matrix

| Category | What ClauseLens Does | Live Demonstration Proof |
|---|---|---|
| **Smart & Dynamic Assistant** | Situation Router re-ranks retrieval, adjusts urgency, and prioritizes action steps based on free-text tenant input. | Type a situation and watch the Risk Panel and Action Plan reorder instantly. |
| **Anti-Hallucination Guarantee** | Code-level $\ge 90\%$ fuzzy overlap verification blocks ungrounded AI claims before they reach the UI. | Ask an out-of-scope legal question; see the system explicitly declare "Not found in document". |
| **Comparative Reasoning** | Synthesizes deltas across two versions of a contract, assessing tenant favorability. | Compare Current vs. Renewal lease with dual citation chips. |
| **Real-World Usability** | Generates an attorney-ready, topic-grouped consultation PDF packet. | 1-click PDF download with branded styling and cited clauses. |
| **Security & Privacy** | Per-user document isolation (403 on cross-tenant access), magic-byte executable rejection, slowapi rate limiting. | Security test suite passing with 39 tests in CI. |
| **Accessibility Excellence** | Icon + text + color on all statuses, full keyboard navigation, automated `axe-core` CI scan. | 0 critical/serious WCAG AA violations across all core screens. |

---

## 7. Setup & Execution Instructions

### Prerequisites
- Python 3.11 or 3.12
- Node.js 18+ and npm
- (Optional) Docker & Docker Compose

### Quickstart: 1-Command Local Execution

```bash
# 1. Clone the repository
git clone https://github.com/clauselens/clauselens.git
cd clauselens

# 2. Configure environment
cp .env.example .env
# (Optional) Add your GEMINI_API_KEY in .env

# 3. Setup Backend
python -m venv backend/.venv
.\backend\.venv\Scripts\activate  # On Windows (or source backend/.venv/bin/activate on Linux/Mac)
pip install -e ./backend

# 4. Prime the Demo Data (Priya's Scenario)
python backend/app/scripts/seed_demo.py

# 5. Start Backend Server (runs on port 8008)
uvicorn app.main:app --host 127.0.0.1 --port 8008

# 6. Start Frontend Server (in a new terminal)
cd frontend
npm install
npm run dev
```

Visit **`http://localhost:5173`** in your browser.

---

### Running Automated Test Suites

```bash
# 1. Run full backend pytest suite (39 tests: unit, API, citation validator, security)
pytest backend/tests/ -v

# 2. Run automated axe-core accessibility scan (WCAG 2.1 AA)
cd frontend
npm run test:a11y

# 3. Build frontend production bundle
npm run build
```

---

### Docker & Cloud Deployment

```bash
# Full-stack local demo with Docker Compose
docker compose up --build

# Build Cloud Run container
docker build -t gcr.io/your-project/clauselens-api:latest .
```

---

## 8. Responsible AI & Legal Safety Notice

ClauseLens is an educational and document-triage assistant designed to improve legal literacy. **It does not provide legal advice, does not form an attorney-client relationship, and is not a substitute for licensed legal counsel.** Every document analysis is grounded strictly in the provided text and encourages professional consultation for disputes.
