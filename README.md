# First Agentic AI — a tiny RAG agent

A small, beginner-friendly **Retrieval-Augmented Generation (RAG)** agent built
with the Gemini API. Ask it questions and it answers using *your* documents
instead of just what the model memorized during training.

## How it works

```
your documents  ─►  split into chunks  ─►  embed each chunk  ─►  knowledge_index.npz
                                                                        │
your question  ─►  embed question  ─►  find most similar chunks  ◄──────┘
                                                │
                                  give chunks + question to Gemini  ─►  answer
```

1. **Ingest** (`ingest.py`): reads every file in `knowledge/`, splits them into
   chunks, and turns each chunk into an *embedding* (a list of 3072 numbers that
   captures its meaning). These are saved to `knowledge_index.npz`.
2. **Retrieve + answer** (`agent.py`): embeds your question, finds the chunks
   whose meaning is closest (by cosine similarity), and asks Gemini to answer
   using only those chunks.

## Files

| File                  | What it does                                              |
| --------------------- | --------------------------------------------------------- |
| `knowledge/`          | Your documents (`.md` / `.txt`). Edit these!              |
| `rag.py`              | Shared helpers: client, chunking, embedding, similarity.  |
| `ingest.py`           | Builds the searchable index from `knowledge/`.            |
| `agent.py`            | The chat agent that retrieves and answers.                |
| `check_setup.py`      | Verifies your API key and lists available models.         |
| `.env`                | Holds your `GEMINI_API_KEY` (never commit this).          |
| `knowledge_index.npz` | The generated index (rebuilt by `ingest.py`).             |

## Usage

```powershell
# 1. (once) confirm your key works
uv run check_setup.py

# 2. build the index from the documents in knowledge/
uv run ingest.py

# 3a. chat interactively
uv run agent.py

# 3b. or ask a single question
uv run agent.py "which coffee is best for espresso?"
```

## Make it your own

1. Delete the sample files in `knowledge/` and drop in your own `.md` or `.txt`
   files (notes, documentation, a FAQ, anything).
2. Re-run `uv run ingest.py` to rebuild the index.
3. Run `uv run agent.py` and ask away.

That's the whole loop: **change documents → re-ingest → ask.**

## Settings you can tweak

- `rag.py` → `CHAT_MODEL` / `EMBED_MODEL`: which Gemini models to use.
- `rag.py` → `chunk_text(max_chars=800)`: bigger chunks = more context per piece,
  smaller chunks = more precise retrieval.
- `agent.py` → `TOP_K = 3`: how many chunks to feed the model as context.

## Security

Your API key lives in `.env`, which is git-ignored. Never paste it into code,
screenshots, or chats. If it is ever exposed, regenerate it at
https://aistudio.google.com/apikey.
