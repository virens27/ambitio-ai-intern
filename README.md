# Ambitio AI Intern Assessment
## Document Understanding, Grounded Drafting, and Improvement from Edits

A production-ready pipeline that ingests messy legal-style documents, extracts structured information, retrieves grounded evidence, generates cited legal draft summaries, and improves over time from operator edits — with a full web UI.

---

## Architecture Overview

| Stage | Component | Technology |
|-------|-----------|------------|
| Stage 1 | Document Processing | PyMuPDF → pdfplumber → Tesseract OCR fallback |
| Stage 2 | Grounded Retrieval | SentenceTransformers + FAISS |
| Stage 3 | Draft Generation | Groq LLaMA-3.3-70b + Evidence Citations |
| Stage 4 | Improvement Loop | Edit diff → Rule extraction → Memory |
| UI/API | Web Interface | FastAPI + HTML/CSS/JS |

### Pipeline Flow

```
┌─────────────────────────────────────────────────────────┐
│                      INPUT: PDF File                    │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│           STAGE 1: Document Processing                  │
│   PyMuPDF → pdfplumber → Tesseract OCR (fallback chain) │
│   Output: cleaned text + overlapping chunks             │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│           STAGE 2: Grounded Retrieval                   │
│   SentenceTransformers → FAISS index → Top-K chunks     │
│   Output: ranked evidence (E1, E2...) with scores       │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│           STAGE 3: Draft Generation                     │
│   Evidence + Style Rules → Groq LLaMA-3.3-70b           │
│   Output: cited draft [Sources: E1, E2] per section     │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│           STAGE 4: Improvement Loop                     │
│   Operator edits → LLM rule extraction → Memory         │
│   Output: updated edit_memory.json for future drafts    │
└─────────────────────────────────────────────────────────┘
```

---

## Features

- **Messy document handling** — tries PyMuPDF first, falls back to pdfplumber, then Tesseract OCR
- **Grounded retrieval** — FAISS vector search ensures output is anchored to source evidence
- **Inspectable evidence citations** — every draft section cites exactly which evidence chunks (E1, E2...) supported it
- **Real improvement loop** — operator edits analyzed by LLM to extract reusable style rules
- **Persistent memory** — rules saved in `edit_memory.json` and applied to all future drafts
- **Web UI** — clean FastAPI interface for document upload, draft viewing, evidence inspection, and operator editing

---

## Setup Instructions

### 1. Clone the repository
```bash
git clone https://github.com/virens27/ambitio-ai-intern.git
cd ambitio-ai-intern
```

### 2. Create and activate virtual environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Install Tesseract OCR (for scanned/image-based PDFs)
- **Windows:** Download and install from https://github.com/UB-Mannheim/tesseract/wiki
- **Mac:** `brew install tesseract`
- **Linux:** `sudo apt install tesseract-ocr`

### 5. Set up environment variables
Create a `.env` file in the root directory:
```
GROQ_API_KEY=your_groq_api_key_here
```
Get a free API key at [console.groq.com](https://console.groq.com)

---

## Usage

### Option A — Web UI (Recommended)
```bash
uvicorn api:app --reload
```
Then open `http://localhost:8000` in your browser.

### Option B — Command Line

Run the full pipeline:
```bash
python main.py sample_inputs/sample_inputs.pdf
```

Run the improvement loop:
```bash
python main.py improve
```

Run pipeline again to see improvement applied:
```bash
python main.py sample_inputs/sample_inputs.pdf
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Web UI |
| POST | `/process` | Upload PDF and run full pipeline |
| POST | `/improve` | Submit operator edit and extract rules |
| GET | `/rules` | Get all learned style rules |

---

## Sample Input & Output

**Tested on 4 different documents:**

| Document | Type | Words | Chunks | Method Used |
|----------|------|-------|--------|-------------|
| `sample_inputs.pdf` | Alaska legal complaint (Welch v. Makemson) | 2,136 | 5 | PyMuPDF |
| `fraud_investigation_memo.pdf` | Internal fraud investigation memo | 660 | 2 | PyMuPDF |
| `employment_dispute.pdf` | Employment discrimination complaint | 3,105 | 7 | PyMuPDF |
| `property_dispute_notice.pdf` | Property/employment dispute (Avendaño v. Uber) | 10,805 | 25 | Tesseract OCR |

**Output:** `sample_outputs/draft_output.json`
A structured case fact summary with Overview, Key Parties, Key Dates & Events, Critical Facts, and Flags & Concerns — each section citing supporting evidence chunks.

**Sample citation format:**
```
**Overview** [Sources: E1, E2, E3]
The case involves...

**Key Parties** [Sources: E1, E4]
- Plaintiff: ...
```

---

## Assumptions & Tradeoffs

| Decision | Reasoning |
|----------|-----------|
| PyMuPDF → pdfplumber → Tesseract OCR fallback | Handles digital, structured, and scanned PDFs gracefully |
| FAISS with all-MiniLM-L6-v2 embeddings | Fast, lightweight, no API cost for retrieval |
| Groq LLaMA-3.3-70b for generation | Free, fast, high quality |
| Evidence IDs (E1, E2...) in prompt and output | Makes grounding fully inspectable per section |
| LLM-based rule extraction from edits | More semantic than regex diffing — captures intent |
| JSON edit memory store | Simple, inspectable, no database needed for this scope |
| temperature=0.2 for generation | Keeps output factual and consistent |
| FastAPI + single HTML file UI | Lightweight, no build step, easy to run locally |

---

## Evaluation

| Stage | What was tested | Result |
|-------|----------------|--------|
| Document Processing | 4 PDFs including scanned image-based PDF | All processed successfully |
| OCR Fallback | property_dispute_notice.pdf (image-based) | 10,805 words extracted via Tesseract |
| Retrieval | Top-5 chunks retrieved per document | All returned with relevance scores |
| Evidence Citations | [Sources: E1, E2] on every section | Fully inspectable grounding |
| Draft Generation | Grounded summaries across 4 documents | No hallucinations, fully structured |
| Improvement Loop | Rules extracted from operator edits | Applied successfully in subsequent runs |
| Web UI | Full pipeline via browser | Upload, view draft, edit, improve — all working |

---

## Project Structure

```
ambitio-ai-intern/
├── src/
│   ├── document_processing/
│   │   └── extractor.py        # OCR + text extraction (3-layer fallback)
│   ├── retrieval/
│   │   └── retriever.py        # FAISS vector search + evidence IDs
│   ├── drafting/
│   │   └── generator.py        # Groq draft generation with citations
│   ├── improvement/
│   │   └── editor.py           # Operator edit learning
│   └── config.py               # Central configuration + Tesseract path
├── templates/
│   └── index.html              # Web UI
├── sample_inputs/              # Input PDF documents (4 files)
├── sample_outputs/             # Generated drafts (JSON)
├── api.py                      # FastAPI backend
├── main.py                     # CLI pipeline entry point
├── edit_memory.json            # Persistent style rules
├── ARCHITECTURE.md             # System architecture details
├── requirements.txt
└── .env                        # API keys (not committed)
```