import fitz  # PyMuPDF
import pdfplumber
import pytesseract
from PIL import Image
import io
import re
from pathlib import Path


def clean_text(text: str) -> str:
    """Clean extracted text by removing noise."""
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)
    text = text.strip()
    return text


def extract_with_pymupdf(pdf_path: str) -> str:
    """Extract text using PyMuPDF (fast, good for digital PDFs)."""
    doc = fitz.open(pdf_path)
    full_text = []
    for page in doc:
        text = page.get_text()
        if text.strip():
            full_text.append(text)
    doc.close()
    return "\n".join(full_text)


def extract_with_pdfplumber(pdf_path: str) -> str:
    """Extract text using pdfplumber (better for tables/structured PDFs)."""
    full_text = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                full_text.append(text)
    return "\n".join(full_text)


def extract_with_ocr(pdf_path: str) -> str:
    """Extract text using OCR for scanned/image-based PDFs."""
    doc = fitz.open(pdf_path)
    full_text = []
    for page in doc:
        pix = page.get_pixmap(dpi=300)
        img_data = pix.tobytes("png")
        image = Image.open(io.BytesIO(img_data))
        text = pytesseract.image_to_string(image)
        if text.strip():
            full_text.append(text)
    doc.close()
    return "\n".join(full_text)


def extract_text(pdf_path: str) -> dict:
    """
    Main extraction function. Tries PyMuPDF first,
    falls back to pdfplumber, then OCR if needed.
    """
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {pdf_path}")

    print(f"[Extractor] Processing: {path.name}")

    # Try PyMuPDF first
    text = extract_with_pymupdf(pdf_path)

    # If too little text, try pdfplumber
    if len(text.strip()) < 100:
        print("[Extractor] PyMuPDF got little text, trying pdfplumber...")
        text = extract_with_pdfplumber(pdf_path)

    # If still too little, fall back to OCR
    if len(text.strip()) < 100:
        print("[Extractor] Falling back to OCR...")
        text = extract_with_ocr(pdf_path)

    cleaned = clean_text(text)

    # Structure the output
    result = {
        "file_name": path.name,
        "file_path": str(path),
        "raw_text": cleaned,
        "word_count": len(cleaned.split()),
        "char_count": len(cleaned),
        "chunks": chunk_text(cleaned)
    }

    print(f"[Extractor] Done. Words extracted: {result['word_count']}")
    return result


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list:
    """Split text into overlapping chunks for retrieval."""
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        chunks.append({
            "chunk_id": len(chunks),
            "text": chunk,
            "start_word": start,
            "end_word": min(end, len(words))
        })
        start += chunk_size - overlap
    return chunks