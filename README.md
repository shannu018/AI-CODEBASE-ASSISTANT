# AI Codebase Assistant

An intelligent, RAG-powered assistant for large-scale codebase comprehension using **Google Gemini** + ChromaDB.

## Features

- 📁 **Upload entire codebases** (drag & drop folders)
- 🧠 **Semantic Search** via Gemini embeddings + ChromaDB
- 💬 **Natural Language Chat** with memory across turns
- 🔍 **Code Analysis** – explain, impact analysis, test generation
- ⚡ **Real-time indexing progress** with background threads
- 🎨 **Glassmorphism dark UI**

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.10+, Flask |
| AI / LLM | Google Gemini 1.5 Flash |
| Embeddings | Gemini text-embedding-004 (768-dim) |
| Vector DB | ChromaDB (cosine similarity) |
| Frontend | HTML5, CSS3, Vanilla JS |

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

Get your Gemini API key at: https://aistudio.google.com/app/apikey

### 3. Run

```bash
python app.py
```

Open http://localhost:5000

## Usage Flow

1. **Upload** – drag your project folder onto the sidebar
2. **Index** – click "Index Codebase" (parses → chunks → embeds → stores)
3. **Chat** – ask anything about your code

## Project Structure

```
├── app.py                    # Flask entry point
├── services/
│   ├── parser.py             # Multi-language file parser
│   ├── chunker.py            # Semantic code chunker (sliding window)
│   ├── embeddings.py         # Gemini text-embedding-004
│   ├── vectordb.py           # ChromaDB integration
│   ├── rag.py                # RAG pipeline (retrieve + generate)
│   └── memory.py             # Session conversation memory
├── routes/
│   ├── upload.py             # POST /api/upload
│   ├── index_route.py        # POST /api/index, GET /api/index/status/:id
│   ├── chat.py               # POST /api/chat  ← FIXED (now uses Gemini)
│   └── analyze.py            # POST /api/analyze/{explain,impact,tests}
├── static/
│   ├── index.html
│   ├── css/styles.css
│   └── js/app.js
└── requirements.txt
```

## API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/upload` | POST | Upload files (multipart) |
| `/api/index` | POST | Start indexing job |
| `/api/index/status/:id` | GET | Poll indexing progress |
| `/api/index/stats` | GET | ChromaDB stats |
| `/api/chat` | POST | Chat with RAG |
| `/api/chat/sessions` | GET | List sessions |
| `/api/analyze/explain` | POST | Explain code |
| `/api/analyze/impact` | POST | Impact analysis |
| `/api/analyze/tests` | POST | Generate tests |

## What Was Fixed

- ❌ README/requirements said OpenAI → ✅ Changed to **Google Gemini**
- ❌ Missing `routes/` and `services/` files → ✅ All files created
- ❌ Chatbot had no RAG implementation → ✅ Full RAG pipeline implemented
- ❌ No session memory → ✅ In-memory session management added
