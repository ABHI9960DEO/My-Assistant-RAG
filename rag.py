"""
rag.py - Shared helpers for our tiny Retrieval-Augmented Generation (RAG) system.

Both ingest.py and agent.py import this file, so the important pieces live here
in one place.
"""
import os

import numpy as np
from dotenv import load_dotenv
from google import genai
from google.genai import types

# --- Configuration: which Gemini models we use, and where we save the index ---
CHAT_MODEL = "gemini-2.5-flash"        # answers questions
EMBED_MODEL = "gemini-embedding-001"   # turns text into vectors
INDEX_FILE = "knowledge_index.npz"     # where the embedded documents are stored

# Read the GEMINI_API_KEY from the .env file into the environment.
load_dotenv()


def get_client() -> genai.Client:
    """Create the Gemini client using the API key from your .env file."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise SystemExit("No GEMINI_API_KEY found. Add it to your .env file.")
    return genai.Client(api_key=api_key)


def chunk_text(text: str, max_chars: int = 800) -> list[str]:
    """Split a document into smaller pieces ("chunks").

    Why? An embedding captures the meaning of a *focused* passage well, but the
    meaning gets blurry if a passage is too long. So we break documents up,
    keeping whole paragraphs together where we can.
    """
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: list[str] = []
    current = ""
    for para in paragraphs:
        # If adding this paragraph keeps us under the limit, append it.
        if len(current) + len(para) + 2 <= max_chars:
            current = (current + "\n\n" + para).strip()
        else:
            if current:
                chunks.append(current)
            # A single giant paragraph gets hard-split into max_chars pieces.
            if len(para) > max_chars:
                for i in range(0, len(para), max_chars):
                    chunks.append(para[i:i + max_chars])
                current = ""
            else:
                current = para
    if current:
        chunks.append(current)
    return chunks


def embed_texts(client: genai.Client, texts: list[str], task_type: str) -> list[np.ndarray]:
    """Turn a list of strings into a list of vectors (lists of numbers).

    task_type tells Gemini how the text will be used, which improves results:
      - "RETRIEVAL_DOCUMENT" when embedding documents we want to search
      - "RETRIEVAL_QUERY"    when embedding the user's question
    """
    result = client.models.embed_content(
        model=EMBED_MODEL,
        contents=texts,
        config=types.EmbedContentConfig(task_type=task_type),
    )
    return [np.array(e.values, dtype=np.float32) for e in result.embeddings]


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Measure how similar two vectors are in meaning.

    Returns a number from about -1 to 1, where 1 means "points the same way"
    (very similar meaning) and 0 means "unrelated".
    """
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))
