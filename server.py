"""
server.py - FastAPI backend that exposes the RAG pipeline as a REST API.

Set ASSISTANT_NAME in your .env file to personalise the UI.

Start with:  uv run uvicorn server:app --reload
"""
import os

import numpy as np
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import rag

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],
    allow_methods=["*"],
    allow_headers=["*"],
)

TOP_K = 3

try:
    _data = np.load(rag.INDEX_FILE, allow_pickle=True)
    _vectors = _data["vectors"]
    _chunks = _data["chunks"]
    _sources = _data["sources"]
except FileNotFoundError:
    raise SystemExit("No index found. Run 'uv run ingest.py /path/to/your/profile.md' first.")

_client = rag.get_client()
_name = os.environ.get("ASSISTANT_NAME", "AI Assistant")


class Question(BaseModel):
    question: str


@app.get("/info")
def info():
    return {"name": _name}


@app.post("/ask")
def ask(body: Question):
    q_vec = rag.embed_texts(_client, [body.question], task_type="RETRIEVAL_QUERY")[0]
    scores = [rag.cosine_similarity(q_vec, v) for v in _vectors]
    top = np.argsort(scores)[::-1][:TOP_K]
    retrieved = [(_chunks[i], _sources[i], float(scores[i])) for i in top]

    context = "\n\n".join(f"[Source: {src}]\n{text}" for text, src, _ in retrieved)
    prompt = (
        f"You are a helpful assistant representing {_name}. "
        "Answer the QUESTION using ONLY the CONTEXT below. "
        "If the context does not contain the answer, say you don't know "
        "based on the provided documents — do not make anything up.\n\n"
        f"CONTEXT:\n{context}\n\n"
        f"QUESTION: {body.question}\n\n"
        "ANSWER:"
    )
    response = _client.models.generate_content(model=rag.CHAT_MODEL, contents=prompt)

    return {
        "answer": response.text,
        "sources": [
            {"file": src, "score": round(score, 2)}
            for _, src, score in retrieved
        ],
    }
