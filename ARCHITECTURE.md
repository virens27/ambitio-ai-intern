# System Architecture

## Overview

This system is a four-stage pipeline designed to ingest messy legal documents,
extract structured information, generate grounded drafts, and improve over time
from operator feedback.

---

## Stage 1: Document Processing

**File:** `src/document_processing/extractor.py`

**Flow:**
PDF File → PyMuPDF (fast digital extraction)
→ pdfplumber (if PyMuPDF yields < 100 chars)
→ pytesseract OCR (if pdfplumber still yields < 100 chars)
→ Text cleaning (whitespace, non-ASCII removal)
→ Chunking (500 words, 50 word overlap)
→ Structured output dict

**Key decisions:**
- Three-layer fallback ensures both digital and scanned PDFs are handled
- Overlapping chunks preserve context across chunk boundaries
- Output is a structured dict with raw_text, word_count, and chunks list

---

## Stage 2: Grounded Retrieval

**File:** `src/retrieval/retriever.py`

**Flow:**
Text chunks → SentenceTransformer (all-MiniLM-L6-v2) → Embeddings
Embeddings → FAISS IndexFlatL2 → Searchable index
Query → Query embedding → FAISS search → Top-K chunks
Top-K chunks → Relevance scored, ranked results
Results → Formatted evidence block for LLM prompt

**Key decisions:**
- all-MiniLM-L6-v2 is lightweight (80MB) and fast with strong semantic quality
- FAISS IndexFlatL2 gives exact nearest-neighbor search for small-medium corpora
- Relevance score = 1/(1+distance) makes scores human-readable (0 to 1)
- Evidence block includes chunk rank and score so output is fully inspectable

---

## Stage 3: Draft Generation

**File:** `src/drafting/generator.py`

**Flow:**
Evidence block + doc name + style rules
→ Structured prompt (with grounding instructions)
→ Groq API (LLaMA-3.3-70b-versatile)
→ Raw draft text
→ Returned with prompt and metadata

**Key decisions:**
- temperature=0.2 keeps output factual and deterministic
- System prompt explicitly forbids hallucination
- Style rules injected into prompt header so they influence the entire output
- Draft format: Overview, Key Parties, Key Dates, Critical Facts, Flags & Concerns

---

## Stage 4: Improvement from Operator Edits

**File:** `src/improvement/editor.py`

**Flow:**
Original draft + Edited draft
→ Groq prompt (diff analysis)
→ Extracted rule list (JSON array)
→ Merged with existing rules (deduplication)
→ Saved to edit_memory.json
→ Loaded on next pipeline run
→ Injected into generation prompt

**Key decisions:**
- LLM-based rule extraction captures semantic intent, not just text diffs
- Rules are stored as plain English strings for transparency and debuggability
- Deduplication prevents rule bloat over many edit cycles
- edit_memory.json is human-readable so operators can inspect/edit rules manually

---

## Data Flow Diagram
[PDF] ──► [Extractor] ──► [Chunks]
│
▼
[FAISS Index]
│
[Query] ──► [Retrieved Chunks]
│
▼
[Groq LLM] ◄── [Style Rules]
│
▼
[Draft Output]
│
[Operator Edits]
│
▼
[Rule Extractor]
│
▼
[edit_memory.json]
│
└──► [Next Draft Generation]

---

## Component Dependencies
main.py
├── src.document_processing.extractor
├── src.retrieval.retriever
├── src.drafting.generator
├── src.improvement.editor
└── src.config

---

## Scalability Considerations

- **FAISS** can scale to millions of vectors with IndexIVFFlat for larger corpora
- **Chunking** parameters (size, overlap) are configurable in `src/config.py`
- **Edit memory** can be migrated to a database (PostgreSQL, MongoDB) for multi-user scenarios
- **Groq API** can be swapped for any OpenAI-compatible endpoint via one config change