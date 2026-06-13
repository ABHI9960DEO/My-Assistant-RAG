# My Assistant RAG

A personal AI assistant powered by Retrieval-Augmented Generation (RAG). Point it at your own profile or resume, and it answers client questions about your services, experience, and how to hire you — using only what you wrote, nothing made up.

Built with **Gemini 2.5 Flash** (answers) + **gemini-embedding-001** (vectors), **FastAPI** backend, and a **React + Vite** frontend.

## How it works

```
your profile.md  →  split into chunks  →  embed each chunk  →  knowledge_index.npz
                                                                        │
client's question  →  embed question  →  find closest chunks  ◄─────────┘
                                                │
                              chunks + question → Gemini → answer
```

## Project structure

```
├── rag.py                  # shared helpers: client, chunking, embedding, similarity
├── ingest.py               # builds the vector index from your markdown file
├── agent.py                # CLI chat agent (terminal use)
├── server.py               # FastAPI backend — exposes /ask and /info
├── abhishek_profile.md     # profile used as the knowledge source
├── profile_template.md     # blank template to copy and fill in
├── knowledge/              # legacy sample docs (coffee demo)
├── frontend/               # React + Vite chat UI
│   ├── src/App.jsx
│   ├── src/App.css
│   └── vite.config.js
├── pyproject.toml          # Python dependencies (managed by uv)
├── .env                    # API keys — never commit this
└── knowledge_index.npz     # generated index — never commit this
```

## Prerequisites

- [Python 3.11+](https://www.python.org/downloads/)
- [uv](https://docs.astral.sh/uv/getting-started/installation/) — fast Python package manager
- [Node.js 18+](https://nodejs.org/)
- A [Gemini API key](https://aistudio.google.com/apikey) (free tier works)

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/ABHI9960DEO/My-Assistant-RAG.git
cd My-Assistant-RAG
```

### 2. Install Python dependencies

```bash
uv sync
```

### 3. Install frontend dependencies

```bash
cd frontend
npm install
cd ..
```

### 4. Create your `.env` file

```bash
cp .env.example .env   # or create it manually
```

Add the following to `.env`:

```
GEMINI_API_KEY=your_key_here
ASSISTANT_NAME=Your Name
```

Get your free API key at https://aistudio.google.com/apikey

### 5. Create your profile

Copy the template and fill it in:

```bash
cp profile_template.md my_profile.md
# edit my_profile.md with your details
```

Or point it at an existing markdown file anywhere on your machine.

### 6. Build the index

```bash
uv run ingest.py my_profile.md
```

You should see output like:

```
Read 1 file(s) -> 7 chunk(s).
Embedding chunks...
Done. Each chunk is a vector of 3072 numbers.
Index saved to knowledge_index.npz.
```

### 7. Start the servers

**Terminal 1 — backend:**

```bash
uv run uvicorn server:app --reload --port 8001
```

**Terminal 2 — frontend:**

```bash
cd frontend
npx vite --port 5173
```

Open **http://localhost:5173** in your browser.

## Updating your profile

Edit your markdown file, then re-run ingest — no server restart needed if using `--reload`:

```bash
uv run ingest.py my_profile.md
```

## CLI usage (no UI)

```bash
# Interactive chat in the terminal
uv run agent.py

# Single question
uv run agent.py "what services do you offer?"
```

## Configuration

| Setting | Where | Default |
|---|---|---|
| `GEMINI_API_KEY` | `.env` | — |
| `ASSISTANT_NAME` | `.env` | `AI Assistant` |
| Chat model | `rag.py` → `CHAT_MODEL` | `gemini-2.5-flash` |
| Embed model | `rag.py` → `EMBED_MODEL` | `gemini-embedding-001` |
| Chunks returned per query | `server.py` → `TOP_K` | `3` |
| Max chunk size | `rag.py` → `chunk_text(max_chars)` | `800` chars |

## Security

- `.env` is git-ignored — never commit your API key
- `knowledge_index.npz` is git-ignored — regenerate it locally after cloning
- If your key is ever exposed, regenerate it at https://aistudio.google.com/apikey
