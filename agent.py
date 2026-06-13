"""
agent.py - Your RAG agent.

Ask it a question. It will:
  1. embed your question,
  2. find the most relevant chunks from your documents,
  3. hand those chunks to Gemini as context, and
  4. answer using only what it found (and tell you its sources).

Chat interactively:        uv run agent.py
Ask a single question:     uv run agent.py "how do I earn a free drink?"
"""
import sys

import numpy as np

import rag

TOP_K = 3  # how many of the most relevant chunks to give the model


def load_index():
    """Load the vectors + text we saved during ingest."""
    try:
        data = np.load(rag.INDEX_FILE, allow_pickle=True)
    except FileNotFoundError:
        raise SystemExit("No index found. Run 'uv run ingest.py' first.")
    return data["vectors"], data["chunks"], data["sources"]


def retrieve(client, question, vectors, chunks, sources, k=TOP_K):
    """Find the k chunks whose meaning is closest to the question."""
    # Embed the question the SAME way we embedded the documents.
    q_vec = rag.embed_texts(client, [question], task_type="RETRIEVAL_QUERY")[0]
    # Score every chunk, then keep the highest-scoring k.
    scores = [rag.cosine_similarity(q_vec, v) for v in vectors]
    top = np.argsort(scores)[::-1][:k]
    return [(chunks[i], sources[i], scores[i]) for i in top]


def build_prompt(question, retrieved):
    """Glue the retrieved chunks and the question into one instruction."""
    context = "\n\n".join(f"[Source: {src}]\n{text}" for text, src, _ in retrieved)
    return (
        "You are a helpful assistant. Answer the QUESTION using ONLY the CONTEXT "
        "below. If the context does not contain the answer, say you don't know "
        "based on the provided documents - do not make anything up.\n\n"
        f"CONTEXT:\n{context}\n\n"
        f"QUESTION: {question}\n\n"
        "ANSWER:"
    )


def answer(client, question, index):
    vectors, chunks, sources = index
    retrieved = retrieve(client, question, vectors, chunks, sources)
    prompt = build_prompt(question, retrieved)
    response = client.models.generate_content(model=rag.CHAT_MODEL, contents=prompt)

    print(f"\nAgent: {response.text}\n")
    print("  (sources the answer was drawn from:)")
    for _, src, score in retrieved:
        print(f"    - {src}   similarity {score:.2f}")
    print()


def main() -> None:
    client = rag.get_client()
    index = load_index()
    chunk_count = len(index[1])

    # If a question was passed on the command line, answer it once and exit.
    if len(sys.argv) > 1:
        answer(client, " ".join(sys.argv[1:]), index)
        return

    # Otherwise, start an interactive chat.
    print(f"Loaded {chunk_count} chunks. Ask me about your documents.")
    print("(type 'quit' to exit)\n")
    while True:
        try:
            question = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye!")
            break
        if not question:
            continue
        if question.lower() in {"quit", "exit"}:
            print("Bye!")
            break
        answer(client, question, index)


if __name__ == "__main__":
    main()
