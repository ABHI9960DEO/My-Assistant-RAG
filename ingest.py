"""
ingest.py - Build the searchable index from your documents.

Pass one or more file paths to index specific files:
    uv run ingest.py /path/to/profile.md
    uv run ingest.py about.md skills.md projects.md

With no arguments it falls back to every .md / .txt file in ./knowledge/:
    uv run ingest.py
"""
import sys
from pathlib import Path

import numpy as np

import rag

KNOWLEDGE_DIR = Path("knowledge")


def main() -> None:
    client = rag.get_client()

    # Use paths from the command line, or fall back to the knowledge/ folder.
    if len(sys.argv) > 1:
        files = [Path(p) for p in sys.argv[1:]]
        for f in files:
            if not f.exists():
                raise SystemExit(f"File not found: {f}")
            if f.suffix.lower() not in {".md", ".txt"}:
                raise SystemExit(f"Only .md and .txt files are supported: {f}")
    else:
        files = [
            f for f in sorted(KNOWLEDGE_DIR.glob("**/*"))
            if f.is_file() and f.suffix.lower() in {".md", ".txt"}
        ]
        if not files:
            raise SystemExit(f"No .md or .txt files found in ./{KNOWLEDGE_DIR}/")

    # Split each file into chunks.
    chunks: list[str] = []
    sources: list[str] = []
    for f in files:
        text = f.read_text(encoding="utf-8")
        for chunk in rag.chunk_text(text):
            chunks.append(chunk)
            sources.append(f.name)
    print(f"Read {len(files)} file(s) -> {len(chunks)} chunk(s).")

    # Embed every chunk via Gemini.
    print("Embedding chunks...")
    vectors = rag.embed_texts(client, chunks, task_type="RETRIEVAL_DOCUMENT")
    matrix = np.vstack(vectors)
    print(f"Done. Each chunk is a vector of {matrix.shape[1]} numbers.")

    # Save everything to one file.
    np.savez(
        rag.INDEX_FILE,
        vectors=matrix,
        chunks=np.array(chunks, dtype=object),
        sources=np.array(sources, dtype=object),
    )
    print(f"Index saved to {rag.INDEX_FILE}.")
    print("Next step:  uv run uvicorn server:app --reload")


if __name__ == "__main__":
    main()
