import json
import os
from src.document_processing.extractor import extract_text
from src.retrieval.retriever import build_index, retrieve, format_evidence
from src.drafting.generator import generate_draft
from src.improvement.editor import process_operator_edit, load_edit_memory
from src.config import SAMPLE_INPUTS_DIR, SAMPLE_OUTPUTS_DIR


def run_pipeline(pdf_path: str):
    """Run the full pipeline on a PDF document."""

    print("\n" + "="*60)
    print("STAGE 1: DOCUMENT PROCESSING")
    print("="*60)
    extracted = extract_text(pdf_path)
    print(f"Extracted {extracted['word_count']} words, {len(extracted['chunks'])} chunks")

    print("\n" + "="*60)
    print("STAGE 2: GROUNDED RETRIEVAL")
    print("="*60)
    index, embeddings = build_index(extracted["chunks"])
    query = "key parties, dates, events, facts, legal issues, concerns"
    retrieved = retrieve(query, extracted["chunks"], index, top_k=5)
    evidence = format_evidence(retrieved)
    print(f"Evidence block ready ({len(evidence)} chars)")

    print("\n" + "="*60)
    print("STAGE 3: DRAFT GENERATION")
    print("="*60)
    style_rules = load_edit_memory()
    if style_rules:
        print(f"Applying {len(style_rules)} learned style rules...")
    result = generate_draft(evidence, extracted["file_name"], style_rules)

    print("\n--- GENERATED DRAFT ---")
    print(result["draft"])

    # Save output
    os.makedirs(SAMPLE_OUTPUTS_DIR, exist_ok=True)
    output_path = os.path.join(SAMPLE_OUTPUTS_DIR, "draft_output.json")
    with open(output_path, "w") as f:
        json.dump({
            "doc_name": extracted["file_name"],
            "word_count": extracted["word_count"],
            "retrieved_evidence": retrieved,
            "draft": result["draft"],
            "style_rules_applied": style_rules
        }, f, indent=2)
    print(f"\n[Main] Output saved to {output_path}")
    return result["draft"]


def run_improvement(original_draft: str, edited_draft: str):
    """Run the improvement loop with operator edits."""
    print("\n" + "="*60)
    print("STAGE 4: IMPROVEMENT FROM OPERATOR EDITS")
    print("="*60)
    rules = process_operator_edit(original_draft, edited_draft)
    print("\nUpdated style rules:")
    for i, rule in enumerate(rules, 1):
        print(f"  {i}. {rule}")
    return rules


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python main.py <pdf_path>              # Run full pipeline")
        print("  python main.py improve                 # Run improvement loop demo")
        sys.exit(1)

    if sys.argv[1] == "improve":
        # Demo improvement loop with simulated edits
        original = open("sample_outputs/draft_output.json").read()
        original_draft = json.loads(original)["draft"]
        edited_draft = original_draft + "\n\nFLAG: Missing notarization on page 3. All monetary amounts must be verified against exhibit A."
        run_improvement(original_draft, edited_draft)
    else:
        run_pipeline(sys.argv[1])