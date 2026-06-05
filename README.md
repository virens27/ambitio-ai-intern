# Ambitio AI Intern Assessment
## Document Understanding, Grounded Drafting, and Improvement from Edits

A production-ready pipeline that ingests messy legal-style documents, extracts structured information, retrieves grounded evidence, generates legal draft summaries, and improves over time from operator edits.

---

## Architecture Overview
PDF Input
↓
[Stage 1] Document Processing (PyMuPDF → pdfplumber → OCR fallback)
↓
[Stage 2] Grounded Retrieval (SentenceTransformers + FAISS)
↓
[Stage 3] Draft Generation (Groq LLaMA-3.3-70b)
↓
[Stage 4] Improvement Loop (Edit diff → Rule extraction → Memory)
↓
JSON Output + Updated Style Rules

---

## Features

- **Messy document handling** — tries PyMuPDF first, falls back to pdfplumber, then OCR
- **Grounded retrieval** — FAISS vector search ensures output is anchored to source evidence
- **Inspectable evidence** — every draft section is traceable to retrieved chunks
- **Real improvement loop** — operator edits are analyzed by LLM to extract reusable style rules
- **Persistent memory** — rules saved in `edit_memory.json` and applied to all future drafts

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

### 4. Set up environment variables
Create a `.env` file in the root directory:
GROQ_API_KEY=your_groq_api_key_here
Get a free API key at [console.groq.com](https://console.groq.com)

---

## Usage

### Run the full pipeline
```bash
python main.py sample_inputs/sample_inputs.pdf
```

### Run the improvement loop (after running pipeline at least once)
```bash
python main.py improve
```

### Run pipeline again to see improvement applied
```bash
python main.py sample_inputs/sample_inputs.pdf
```

---

## Sample Input & Output

**Input:** `sample_inputs/sample_inputs.pdf`
A 10-page legal complaint — *Margie Lou Welch v. Makemson* — filed in the Superior Court of Alaska, involving fiduciary duty breach and fraudulent use of an access device.

**Output:** `sample_outputs/draft_output.json`
A structured case fact summary with:
- Overview
- Key Parties
- Key Dates & Events
- Critical Facts
- Flags & Concerns

---

## Assumptions & Tradeoffs

| Decision | Reasoning |
|---|---|
| PyMuPDF → pdfplumber → OCR fallback chain | Handles both digital and scanned PDFs gracefully |
| FAISS with all-MiniLM-L6-v2 embeddings | Fast, lightweight, no API cost for retrieval |
| Groq LLaMA-3.3-70b for generation | Free, fast, high quality |
| LLM-based rule extraction from edits | More semantic than regex diffing — captures intent |
| JSON edit memory store | Simple, inspectable, no database needed for this scope |
| temperature=0.2 for generation | Keeps output factual and consistent |

---

## Evaluation

| Stage | What was tested |
|---|---|
| Document Processing | Extracted 2136 words from 10-page legal PDF correctly |
| Retrieval | All 5 chunks retrieved with relevance scores |
| Draft Generation | Structured output grounded in source, no hallucinations |
| Improvement Loop | 3 rules extracted and applied in subsequent run |

---

## Project Structure
ambitio-ai-intern/
├── src/
│   ├── document_processing/
│   │   └── extractor.py       # OCR + text extraction
│   ├── retrieval/
│   │   └── retriever.py       # FAISS vector search
│   ├── drafting/
│   │   └── generator.py       # Groq draft generation
│   ├── improvement/
│   │   └── editor.py          # Operator edit learning
│   └── config.py              # Central configuration
├── sample_inputs/             # Input PDF documents
├── sample_outputs/            # Generated drafts (JSON)
├── main.py                    # Pipeline entry point
├── edit_memory.json           # Persistent style rules
├── requirements.txt
└── .env                       # API keys (not committed)

