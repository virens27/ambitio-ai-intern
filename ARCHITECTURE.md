# System Architecture

## Overview

A five-layer pipeline that ingests messy legal documents, extracts structured
information, retrieves grounded evidence, generates cited draft summaries,
improves over time from operator feedback, and exposes everything via a web UI.

---

## Stage 1: Document Processing

**File:** `src/document_processing/extractor.py`

**Flow:**
```
PDF File → PyMuPDF (fast digital extraction)
         → pdfplumber (if PyMuPDF yields < 100 chars)
         → Tesseract OCR (if pdfplumber still yields < 100 chars)
         → Text cleaning (whitespace, non-ASCII removal)
         → Chunking (500 words, 50 word overlap)
         → Structured output dict
```

**Key decisions:**
- Three-layer fallback ensures both digital and scanned PDFs are handled
- Tesseract OCR configured via `src/config.py` for Windows path compatibility
- Overlapping chunks preserve context across chunk boundaries
- Output is a structured dict with raw_text, word_count, and chunks list

**Tested on:**
| Document | Method Used | Words Extracted |
|----------|-------------|-----------------|
| sample_inputs.pdf | PyMuPDF | 2,136 |
| fraud_investigation_memo.pdf | PyMuPDF | 660 |
| employment_dispute.pdf | PyMuPDF | 3,105 |
| property_dispute_notice.pdf | Tesseract OCR | 10,805 |

---

## Stage 2: Grounded Retrieval

**File:** `src/retrieval/retriever.py`

**Flow:**
```
Text chunks → SentenceTransformer (all-MiniLM-L6-v2) → Embeddings
Embeddings → FAISS IndexFlatL2 → Searchable index
Query → Query embedding → FAISS search → Top-K chunks
Top-K chunks → Evidence IDs assigned (E1, E2, E3...)
Results → Relevance scored, ranked results
Results → Formatted evidence block for LLM prompt
```

**Key decisions:**
- all-MiniLM-L6-v2 is lightweight (80MB) and fast with strong semantic quality
- FAISS IndexFlatL2 gives exact nearest-neighbor search for small-medium corpora
- Relevance score = 1/(1+distance) makes scores human-readable (0 to 1)
- Each chunk assigned a unique Evidence ID (E1, E2...) for citation tracking
- Evidence block includes chunk ID, rank, and score — fully inspectable

---

## Stage 3: Draft Generation

**File:** `src/drafting/generator.py`

**Flow:**
```
Evidence block (with E1, E2 IDs) + doc name + style rules
    → Structured prompt (with grounding + citation instructions)
    → Groq API (LLaMA-3.3-70b-versatile)
    → Draft with inline citations per section
    → Returned with prompt and metadata
```

**Citation format:**
```
**Overview** [Sources: E1, E2, E3]
The case involves...

**Key Parties** [Sources: E1, E4]
- Plaintiff: ...
```

**Key decisions:**
- temperature=0.2 keeps output factual and deterministic
- System prompt explicitly forbids hallucination
- Style rules injected into prompt header so they influence the entire output
- LLM instructed to cite Evidence IDs after every section heading
- Draft format: Overview, Key Parties, Key Dates, Critical Facts, Flags & Concerns

---

## Stage 4: Improvement from Operator Edits

**File:** `src/improvement/editor.py`

**Flow:**
```
Original draft + Edited draft
    → Groq prompt (diff analysis)
    → Extracted rule list (JSON array)
    → Merged with existing rules (deduplication)
    → Saved to edit_memory.json
    → Loaded on next pipeline run
    → Injected into generation prompt
```

**Key decisions:**
- LLM-based rule extraction captures semantic intent, not just text diffs
- Rules are stored as plain English strings for transparency and debuggability
- Deduplication prevents rule bloat over many edit cycles
- edit_memory.json is human-readable so operators can inspect/edit rules manually

**Example learned rules:**
```json
{
  "style_rules": [
    "Always verify monetary amounts against relevant exhibits",
    "Explicitly flag any missing documentation, such as notarization",
    "Include a dedicated section for flags and concerns in the case summary",
    "Use a standard format for listing key parties and their roles",
    "Include all relevant source citations for each section"
  ]
}
```

---

## Stage 5: Web UI & API

**Files:** `api.py`, `templates/index.html`

**API Endpoints:**
```
GET  /          → Serves the web UI
POST /process   → Accepts PDF upload, runs full pipeline, returns JSON
POST /improve   → Accepts edited draft, extracts rules, updates memory
GET  /rules     → Returns all learned style rules
```

**UI Components:**
```
Header          → Ambitio branding
Pipeline Steps  → 01 → 02 → 03 → 04 (lights up as each stage completes)
Upload Card     → PDF drag/click upload with file validation
Stats Card      → Words extracted, chunks created, rules applied
Draft Card      → View Draft tab (formatted with citations)
                  Edit & Improve tab (editable textarea + submit)
Evidence Card   → E1-E5 with relevance scores and text previews
Rules Card      → All learned style rules from edit_memory.json
```

**Key decisions:**
- FastAPI chosen for simplicity and compatibility with existing Python codebase
- Single HTML file UI — no build step, no framework overhead
- SVG icons used instead of emojis for professional appearance
- Draft rendered with proper HTML formatting (section headers in red, citations in blue)
- In-memory draft store for improvement loop (suitable for single-user local use)

---

## Full Data Flow Diagram

```
[PDF Upload]
     │
     ▼
[Extractor] ──PyMuPDF──► text
     │       ──pdfplumber► text (fallback)
     │       ──Tesseract──► text (fallback)
     │
     ▼
[Chunks: 500 words, 50 overlap]
     │
     ▼
[SentenceTransformer] ──► [Embeddings]
                                │
                           [FAISS Index]
                                │
                    [Query] ──► [Top-K Chunks]
                                      │
                              [Evidence IDs: E1..E5]
                                      │
                                      ▼
                        [Groq LLM] ◄── [Style Rules]
                             │
                             ▼
                    [Cited Draft Output]
                    **Section** [Sources: E1, E2]
                             │
                    [Operator Reviews]
                             │
                    [Edited Draft]
                             │
                    [Rule Extractor (Groq)]
                             │
                    [edit_memory.json]
                             │
                             └──► [Next Draft Generation]
```

---

## Component Dependencies

```
api.py / main.py
├── src.document_processing.extractor   # Stage 1
├── src.retrieval.retriever             # Stage 2
├── src.drafting.generator              # Stage 3
├── src.improvement.editor              # Stage 4
└── src.config                         # Central config + Tesseract path
```

---

## Scalability Considerations

- **FAISS** can scale to millions of vectors with IndexIVFFlat for larger corpora
- **Chunking** parameters (size, overlap) are configurable in `src/config.py`
- **Edit memory** can be migrated to a database (PostgreSQL, MongoDB) for multi-user scenarios
- **Groq API** can be swapped for any OpenAI-compatible endpoint via one config change
- **UI** can be extended with user authentication and document history
- **OCR** can be upgraded to cloud-based OCR (AWS Textract, Google Vision) for higher accuracy on noisy scans