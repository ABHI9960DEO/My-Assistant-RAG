"""
server.py - FastAPI backend exposing the RAG pipeline and image editing as a REST API.

Set ASSISTANT_NAME in your .env file to personalise the UI.

Start with:  uv run uvicorn server:app --reload --port 8001
"""
import os

import numpy as np
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.messages import AIMessage, HumanMessage
from pydantic import BaseModel

import images
import rag

# One history object per browser session, keyed by session_id.
_histories: dict[str, InMemoryChatMessageHistory] = {}

app = FastAPI()

_frontend_url = os.environ.get("FRONTEND_URL", "")
_origins = (
    [_frontend_url, "http://localhost:5173", "http://localhost:5174"]
    if _frontend_url
    else ["*"]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
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
    session_id: str = "default"


@app.get("/info")
def info():
    return {"name": _name}


@app.post("/ask")
def ask(body: Question):
    history = _histories.setdefault(body.session_id, InMemoryChatMessageHistory())

    q_vec = rag.embed_texts(_client, [body.question], task_type="RETRIEVAL_QUERY")[0]
    scores = [rag.cosine_similarity(q_vec, v) for v in _vectors]
    top = np.argsort(scores)[::-1][:TOP_K]
    retrieved = [(_chunks[i], _sources[i], float(scores[i])) for i in top]

    context = "\n\n".join(f"[Source: {src}]\n{text}" for text, src, _ in retrieved)

    # Include the last 6 messages (3 turns) so the model remembers recent context.
    history_text = ""
    if history.messages:
        lines = []
        for msg in history.messages[-6:]:
            role = "Human" if isinstance(msg, HumanMessage) else "Assistant"
            lines.append(f"{role}: {msg.content}")
        history_text = "CONVERSATION HISTORY:\n" + "\n".join(lines) + "\n\n"

    prompt = (
        f"You are a helpful assistant representing {_name}. "
        "Answer the QUESTION using ONLY the CONTEXT below. "
        "If the context does not contain the answer, say you don't know "
        "based on the provided documents — do not make anything up.\n\n"
        f"CONTEXT:\n{context}\n\n"
        f"{history_text}"
        f"QUESTION: {body.question}\n\n"
        "ANSWER:"
    )
    response = _client.models.generate_content(model=rag.CHAT_MODEL, contents=prompt)
    answer = response.text

    # Save this turn to memory.
    history.add_message(HumanMessage(content=body.question))
    history.add_message(AIMessage(content=answer))

    return {
        "answer": answer,
        "sources": [
            {"file": src, "score": round(score, 2)}
            for _, src, score in retrieved
        ],
    }


@app.post("/edit-image")
async def edit_image_endpoint(prompt: str = Form(...), image: UploadFile = File(...)):
    """Edit an uploaded image with a text instruction, via Replicate (FLUX Kontext)."""
    image_bytes = await image.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="No image was uploaded.")
    try:
        edited = images.edit_image(image_bytes, prompt, image.content_type or "image/png")
    except Exception as e:
        # Surface a readable message to the frontend instead of a raw 500 error.
        raise HTTPException(status_code=502, detail=f"Image editing failed: {e}")
    return Response(content=edited, media_type="image/png")
