import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = "llama-3.3-70b-versatile"

CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
TOP_K_CHUNKS = 5

EDIT_MEMORY_PATH = "edit_memory.json"
SAMPLE_INPUTS_DIR = "sample_inputs"
SAMPLE_OUTPUTS_DIR = "sample_outputs"

import pytesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'