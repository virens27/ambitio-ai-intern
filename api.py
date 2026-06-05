from fastapi import FastAPI, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
import shutil
import os
import json

from src.document_processing.extractor import extract_text
from src.retrieval.retriever import build_index, retrieve, format_evidence
from src.drafting.generator import generate_draft
from src.improvement.editor import process_operator_edit, load_edit_memory
from src.config import SAMPLE_OUTPUTS_DIR

app = FastAPI(title="Ambitio Legal Document Pipeline")

# Store last draft in memory for improvement loop
last_draft_store = {}

os.makedirs("uploads", exist_ok=True)
os.makedirs(SAMPLE_OUTPUTS_DIR, exist_ok=True)


@app.get("/", response_class=HTMLResponse)
async def home():
    with open("templates/index.html", "r", encoding="utf-8") as f:
        return f.read()


@app.post("/process")
async def process_document(file: UploadFile = File(...)):
    try:
        # Save uploaded file
        file_path = f"uploads/{file.filename}"
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        # Stage 1: Extract
        extracted = extract_text(file_path)

        # Stage 2: Retrieve
        index, embeddings = build_index(extracted["chunks"])
        query = "key parties, dates, events, facts, legal issues, concerns"
        retrieved = retrieve(query, extracted["chunks"], index, top_k=5)
        evidence = format_evidence(retrieved)

        # Stage 3: Generate
        style_rules = load_edit_memory()
        result = generate_draft(evidence, extracted["file_name"], style_rules)

        # Store for improvement loop
        last_draft_store["draft"] = result["draft"]
        last_draft_store["doc_name"] = extracted["file_name"]

        # Save output
        output = {
            "doc_name": extracted["file_name"],
            "word_count": extracted["word_count"],
            "num_chunks": len(extracted["chunks"]),
            "retrieved_evidence": retrieved,
            "draft": result["draft"],
            "style_rules_applied": style_rules
        }

        output_path = os.path.join(SAMPLE_OUTPUTS_DIR, "draft_output.json")
        with open(output_path, "w") as f:
            json.dump(output, f, indent=2)

        return JSONResponse({
            "success": True,
            "doc_name": extracted["file_name"],
            "word_count": extracted["word_count"],
            "num_chunks": len(extracted["chunks"]),
            "draft": result["draft"],
            "style_rules_applied": style_rules,
            "evidence": [
                {
                    "id": c["evidence_id"],
                    "score": round(c["relevance_score"], 3),
                    "text": c["text"][:300] + "..."
                }
                for c in retrieved
            ]
        })

    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


@app.post("/improve")
async def improve_draft(edited_draft: str = Form(...)):
    try:
        if "draft" not in last_draft_store:
            return JSONResponse({
                "success": False,
                "error": "No draft found. Please process a document first."
            }, status_code=400)

        original_draft = last_draft_store["draft"]
        rules = process_operator_edit(original_draft, edited_draft)

        return JSONResponse({
            "success": True,
            "rules_extracted": rules,
            "total_rules": len(rules)
        })

    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


@app.get("/rules")
async def get_rules():
    rules = load_edit_memory()
    return JSONResponse({"rules": rules, "total": len(rules)})