import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
from typing import List, Dict


# Load the embedding model once
model = SentenceTransformer("all-MiniLM-L6-v2")


def build_index(chunks: List[Dict]) -> tuple:
    """
    Build a FAISS index from text chunks.
    Returns the index and the list of embeddings.
    """
    print(f"[Retriever] Building index over {len(chunks)} chunks...")
    texts = [chunk["text"] for chunk in chunks]
    embeddings = model.encode(texts, show_progress_bar=False)
    embeddings = np.array(embeddings).astype("float32")

    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)

    print(f"[Retriever] Index built. Dimension: {dimension}")
    return index, embeddings


def retrieve(query: str, chunks: List[Dict], index, top_k: int = 5) -> List[Dict]:
    """
    Retrieve top_k most relevant chunks for a given query.
    Returns chunks with their relevance scores.
    """
    print(f"[Retriever] Retrieving top {top_k} chunks for query...")
    query_embedding = model.encode([query]).astype("float32")
    distances, indices = index.search(query_embedding, top_k)

    results = []
    for rank, (dist, idx) in enumerate(zip(distances[0], indices[0])):
        if idx < len(chunks):
            chunk = chunks[idx].copy()
            chunk["relevance_score"] = float(1 / (1 + dist))
            chunk["rank"] = rank + 1
            results.append(chunk)

    print(f"[Retriever] Retrieved {len(results)} chunks.")
    return results


def format_evidence(retrieved_chunks: List[Dict]) -> str:
    """
    Format retrieved chunks into a readable evidence block
    to pass into the LLM prompt.
    """
    evidence_parts = []
    for chunk in retrieved_chunks:
        evidence_parts.append(
            f"[Evidence {chunk['rank']} | Score: {chunk['relevance_score']:.3f}]\n"
            f"{chunk['text']}"
        )
    return "\n\n".join(evidence_parts)