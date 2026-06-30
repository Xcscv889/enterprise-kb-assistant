# Enterprise Knowledge Base AI Assistant

An intelligent enterprise document Q&A system built on the **RAG (Retrieval-Augmented Generation)** architecture. Upload corporate documents (PDF/Word/TXT/Markdown), and the system automatically parses, vectorizes, and enables natural language querying — powered by DeepSeek LLM for accurate, context-grounded answers.

[中文文档](README.md)

---

## Core Capabilities

- **Multi-format document parsing**: PDF, DOCX, TXT, Markdown → intelligent chunking → vector indexing
- **Semantic retrieval**: Precise content recall based on embedding similarity
- **Streaming generation**: Token-by-token SSE responses via DeepSeek LLM
- **Dual memory system**: Short-term conversation context + long-term knowledge synthesis
- **Zero GPU**: Local ONNX Runtime embedding inference — CPU-only, no PyTorch needed

---

## Quick Start

### Local Development

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Edit .env: set DEEPSEEK_API_KEY=sk-xxxx

# 3. Run
python main.py

# 4. Open browser
# http://localhost:8000
```

### 🐳 Docker (Recommended for Production)

```bash
# 1. Configure environment
cp .env.example .env
# Edit .env: set DEEPSEEK_API_KEY and optionally APP_API_KEY

# 2. Build & start
docker compose up -d --build

# 3. Check logs
docker compose logs -f

# 4. Open browser
# http://localhost:8000
```

The embedding model (~100MB) is pre-downloaded during image build — no cold-start wait on first run.

---

## ☁️ Cloud Deployment

### Server Requirements

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| CPU | 2 cores | 4 cores |
| Memory | 4 GB | 8 GB |
| Disk | 20 GB | 40 GB SSD |
| OS | Ubuntu 22.04 / Debian 12 | Ubuntu 22.04 |
| Bandwidth | 1 Mbps | 5 Mbps |

> The embedding model uses ~200MB in memory. ChromaDB queries need additional RAM. 4GB is the bare minimum.

### Deployment Steps

```bash
# 1. SSH into server
ssh root@<server-ip>

# 2. Install Docker (if not already installed)
curl -fsSL https://get.docker.com | bash

# 3. Upload project
#    Option A: git clone <repo-url>
#    Option B: scp -r enterprise-kb-assistant/ root@<IP>:/opt/

cd /opt/enterprise-kb-assistant

# 4. Configure API keys
cp .env.example .env
vim .env   # Set DEEPSEEK_API_KEY=sk-xxxx

# 5. Build & start container
docker compose up -d --build

# 6. Verify
docker compose logs -f

# 7. Open firewall port
#    Alibaba Cloud: Security Group → Inbound → TCP 8000
#    Tencent Cloud: Firewall → Add Rule → TCP 8000
#    AWS/GCP: Security Group → Inbound → TCP 8000

# 8. Access in browser
# http://<server-ip>:8000
```

### Operations Cheat Sheet

```bash
docker compose ps              # Check status
docker compose logs -f         # Live logs
docker compose restart         # Restart
docker compose down            # Stop
git pull && docker compose up -d --build   # Update & redeploy
tar -czf backup-$(date +%Y%m%d).tar.gz chroma_data/ uploads/   # Backup
```

### Data Persistence

- `chroma_data/`: Vector DB — **survives restarts**
- `uploads/`: Raw documents — **survives restarts**
- Conversation memory: stored in ChromaDB alongside document vectors
- Both directories are bind-mounted to the host, decoupled from container lifecycle

---

## API Key Protection

Set `APP_API_KEY` in `.env` to protect `/api/*` endpoints. All API requests must then include the header:

```
X-API-Key: your-secret-key
```

Leave `APP_API_KEY` empty to skip validation (local development mode). The health check endpoint (`/api/health`) and static files are always open.

---

## Tech Stack

| Component | Technology | Notes |
|-----------|-----------|-------|
| Web Framework | FastAPI + Uvicorn | Async HTTP server |
| LLM | DeepSeek (OpenAI-compatible) | Streaming chat completion |
| Embedding | BAAI/bge-small-zh-v1.5 | Local ONNX Runtime, CPU-only |
| Vector DB | ChromaDB | Persistent document vectors |
| Parsing | PyMuPDF + python-docx | PDF/DOCX/TXT/Markdown |

---

## Features

### 📄 Document Management
- Upload **PDF / DOCX / TXT / Markdown**
- Auto text extraction & smart chunking (800 chars/chunk, 150 char overlap)
- Vector indexing with list & delete support

### 🤖 RAG Q&A
- **5-stage RAG pipeline**: Query embedding → Memory retrieval → Document retrieval → Context assembly → Streaming generation
- SSE (Server-Sent Events) for token-by-token responses
- Graceful fallback to chat mode when no documents match

### 🧠 Dual Memory
- **Short-term**: Last 20 conversation turns, 1-hour TTL
- **Long-term**: Auto-synthesized every 5 turns, persisted to ChromaDB, cross-session recall

### ⚡ Local Embedding
- **fastembed (ONNX Runtime)** for local model inference
- No PyTorch or GPU required — runs efficiently on CPU

### 🌐 Web UI
- Clean chat interface with multi-session management
- Drag-and-drop document upload
- Real-time source attribution display

---

## Project Structure

```
enterprise-kb-assistant/
├── main.py                 # FastAPI application entry
├── config.py               # Centralized config (.env loaded)
├── requirements.txt        # Python dependencies
├── Dockerfile              # Docker image build
├── docker-compose.yml      # Docker Compose configuration
├── .dockerignore           # Docker build exclusions
├── app/
│   ├── api/                # API routes
│   │   ├── auth.py         # API Key middleware
│   │   ├── chat.py         # Chat endpoint (SSE streaming)
│   │   ├── documents.py    # Document upload/list/delete
│   │   ├── memory.py       # Memory inspect/clear
│   │   └── health.py       # Health check
│   ├── core/               # Core components
│   │   ├── llm_client.py   # DeepSeek LLM client
│   │   ├── embedding.py    # Embedding model service
│   │   ├── chunker.py      # Document chunker
│   │   └── prompts.py      # Prompt templates
│   ├── rag/                # RAG pipeline
│   │   ├── pipeline.py     # Pipeline orchestrator
│   │   ├── retriever.py    # Document retriever
│   │   └── store.py        # ChromaDB vector store
│   ├── memory/             # Memory system
│   │   ├── conversation.py # Short-term conversation memory
│   │   └── long_term.py    # Long-term memory synthesis
│   ├── parsing/            # Document parsers
│   │   ├── parser_registry.py
│   │   ├── pdf_parser.py
│   │   ├── docx_parser.py
│   │   ├── txt_parser.py
│   │   └── markdown_parser.py
│   └── models/             # Data models
│       └── schemas.py
├── static/                 # Frontend static files
│   ├── index.html
│   ├── css/style.css
│   └── js/
│       ├── app.js
│       ├── chat.js
│       └── upload.js
├── uploads/                # Uploaded file staging
└── chroma_data/            # ChromaDB persistence
```
