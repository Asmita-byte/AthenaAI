<div align="center">

# ◉ Athena AI

### Multimodal Document Intelligence Platform

*Ask anything about your documents — get grounded answers with citations*

[

![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python&logoColor=white)

](https://python.org)
[

![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi&logoColor=white)

](https://fastapi.tiangolo.com)
[

![Celery](https://img.shields.io/badge/Celery-5.4-37814A?style=flat-square&logo=celery&logoColor=white)

](https://docs.celeryq.dev)
[

![Qdrant](https://img.shields.io/badge/Qdrant-Vector_DB-DC143C?style=flat-square)

](https://qdrant.tech)
[

![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)

](LICENSE)
[

![Tests](https://img.shields.io/badge/Tests-36_passed-22c55e?style=flat-square)

](tests/)

[Live Demo](#) · [API Docs](http://localhost:8000/docs) · [Architecture](#architecture)

</div>

---

## The Problem

Most RAG systems fail in the real world. They chunk text, embed it, retrieve it — and completely ignore the tables, charts, figures, and images that often contain the most critical information in a document.

Upload an annual report and ask *"What are the key financial risks?"* — a text-only RAG system searches through paragraphs. But the risk summary might be in a **table on page 12**. The revenue breakdown might be in a **chart on page 8**. A text-only system misses all of it.

Athena AI solves this.

---

## The Solution

A production-grade **Multimodal Agentic RAG** platform that:

- Parses **every modality** — text, tables, charts, figures, images — from PDF, DOCX, PPTX, XLSX, CSV, TXT
- Embeds **text and images** into separate vector spaces using sentence-transformers + CLIP
- Retrieves using **hybrid search** — dense semantic + BM25 keyword, fused via RRF and reranked by a cross-encoder
- Uses an **agentic query planner** that dynamically selects retrieval tools based on query intent
- Returns **grounded answers with exact citations** — page number, table index, figure reference, source file
- Supports **multi-document reasoning** — compare, contrast, verify across documents simultaneously
- Enforces **per-user data isolation** with JWT authentication

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│              Athena AI Frontend (HTML/JS)            │
│     Login · Upload · Chat · Citations · History      │
└─────────────────────┬───────────────────────────────┘
                      │ HTTPS + JWT
                      ▼
┌─────────────────────────────────────────────────────┐
│              FastAPI Backend (Python 3.11)           │
│   /auth  /upload  /query  /status  /health           │
└──────┬──────────────────────────┬───────────────────┘
       │                          │
       ▼                          ▼
┌─────────────┐        ┌──────────────────────────────┐
│ Celery +    │        │        Query Pipeline         │
│ Redis Queue │        │                              │
│             │        │  Query → Planner Agent       │
│ • Parse     │        │    → Tool Selection          │
│ • Chunk     │        │    → Hybrid Retrieval        │
│ • Embed     │        │    → RRF Fusion              │
│ • Caption   │        │    → Cross-Encoder Rerank    │
│ • KG Build  │        │    → LLM Generation (Groq)  │
└──────┬──────┘        │    → Citation Attachment      │
       │               └──────────────────────────────┘
       ▼
┌─────────────────────────────────────────────────────┐
│                  Ingestion Pipeline                  │
│                                                     │
│  File → Validator → Format Router                   │
│    ↓         ↓          ↓          ↓               │
│  PDF       DOCX       PPTX      XLSX/CSV/TXT        │
│    └─────────┴──────────┴──────────┘               │
│                    ↓                                │
│         Text · Tables · Images/Figures             │
│                    ↓                                │
│    Text Embedder · Table Embedder · CLIP           │
│                    ↓                                │
│              Qdrant Vector DB                       │
└─────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────┐
│                   Storage Layer                      │
│   SQLite · Local FS · Qdrant · Redis Cache          │
└─────────────────────────────────────────────────────┘
```

---

## Why Hybrid Retrieval?

```
User Query
    │
    ├── Dense Retrieval    "revenue" ≈ "income" ≈ "earnings"
    │   (Qdrant ANN)       Semantic similarity, handles paraphrasing
    │
    ├── Sparse Retrieval   "Q3 2023 SEC filing revenue" exact match
    │   (BM25)             Keyword precision, handles rare terms
    │
    ├── RRF Fusion         Combines both ranked lists mathematically
    │   (k=60)             No weight tuning needed, robust by design
    │
    └── Cross-Encoder      Re-scores every chunk against the query
        Reranker            Most accurate, used as final precision filter
```

Dense retrieval has high recall. BM25 has high keyword precision. The cross-encoder has the highest accuracy but is too slow to run on thousands of chunks. Each stage feeds the next — trading speed for precision as the candidate pool shrinks.

---

## Tech Stack

| Layer | Technology | Why |
|---|---|---|
| Backend API | FastAPI + Uvicorn | Async, production-grade, auto-docs |
| Authentication | JWT + bcrypt | Stateless, secure, industry standard |
| Task Queue | Celery + Redis | Fault-tolerant, horizontally scalable |
| Vector DB | Qdrant | OSS, payload filtering, CPU-capable |
| Text Embeddings | all-MiniLM-L6-v2 | Fast, free, 384-dim, strong quality |
| Image Embeddings | CLIP ViT-B/32 | Cross-modal retrieval, OSS |
| Reranker | ms-marco-MiniLM-L-6-v2 | Free, accurate cross-encoder |
| LLM | Groq llama-3.3-70b | Free tier, extremely fast inference |
| LLM Fallback | Gemini 1.5 Flash | Free tier, generous limits |
| Vision LLM | Qwen2-VL-7B | OSS, runs locally |
| Metadata DB | SQLite + SQLAlchemy async | Zero config, production swap-ready |
| Frontend | Vanilla HTML/CSS/JS | Zero dependencies, instant load |

---

## Evaluation Framework

| Metric | Tool | What It Measures |
|---|---|---|
| Faithfulness | Custom + Ragas | Is the answer grounded in retrieved context? |
| Answer Relevancy | Custom + Ragas | Does the answer address the question? |
| Context Recall | DeepEval | Did retrieval surface the right chunks? |
| Context Utilization | Custom | Were retrieved chunks actually used? |
| Hallucination Rate | DeepEval | How often does the LLM fabricate? |

---

## Project Structure

```
athena-ai/
│
├── backend/                  # FastAPI application
│   ├── api/                  # Route handlers (auth, upload, query, status)
│   ├── models/               # SQLAlchemy ORM models
│   ├── schemas/              # Pydantic request/response schemas
│   ├── services/             # Business logic layer
│   └── core/                 # Config, logging, security, exceptions
│
├── ingestion/                # Document processing pipeline
│   ├── parsers/              # PDF, DOCX, PPTX, XLSX, TXT parsers
│   ├── chunkers/             # Text, table, image chunkers
│   ├── extractors/           # Table, image, metadata extraction
│   └── captioners/           # VLM-based image/chart captioning
│
├── embeddings/               # Text + image embedding pipelines
├── retrieval/                # Dense, sparse, RRF fusion, reranking
├── agents/                   # Agentic query planner + retrieval tools
├── generation/               # LLM answer generation + citations
├── knowledge_graph/          # Cross-document entity graph (NetworkX)
├── vectorstore/              # Qdrant client + bulk indexing
├── workers/                  # Celery background task definitions
├── evaluation/               # Ragas + DeepEval evaluation pipelines
├── observability/            # Latency tracking + metrics collection
├── tests/                    # 36 tests — unit, integration, e2e
├── index.html                # Frontend — zero-dependency chat UI
├── docker-compose.yml        # Full stack local deployment
├── Dockerfile.api            # FastAPI container
├── Dockerfile.worker         # Celery worker container
└── .github/workflows/        # CI/CD — lint, test, build validation
```

---

## Quick Start

```bash
# 1. Clone
git clone https://github.com/Asmita-byte/AthenaAI.git
cd athena-ai

# 2. Environment
conda create -n multimodal_env python=3.11 -y
conda activate multimodal_env
pip install -r requirements.txt

# 3. Configure
cp .env.example .env
# Add: GROQ_API_KEY, GEMINI_API_KEY, JWT_SECRET_KEY

# 4. Start services
docker run -d -p 6379:6379 redis:alpine
docker run -d -p 6333:6333 qdrant/qdrant

# 5. Start backend
celery -A workers.celery_app worker --loglevel=info --pool=solo
uvicorn backend.main:app --reload

# 6. Open frontend
# Open index.html in browser → signup → upload → ask
```

---

## Key Engineering Decisions

**Why Qdrant over Pinecone/Weaviate?**
Runs entirely locally — no API costs, no data leaving your machine. Persistent storage with a single config change for production. Supports payload filtering for per-user document isolation.

**Why separate text and image collections?**
Text embeddings (384-dim) and CLIP embeddings (512-dim) live in different vector spaces. Mixing them would require dimension alignment and hurt retrieval quality for both modalities.

**Why SQLite over PostgreSQL?**
Zero configuration for local development. The SQLAlchemy async layer means swapping to PostgreSQL in production requires changing exactly one environment variable.

**Why Celery over FastAPI BackgroundTasks?**
FastAPI BackgroundTasks die if the server restarts. Celery tasks survive restarts, support retries, and scale horizontally — critical for a document processing pipeline that can take minutes per file.

**Why JWT over session-based auth?**
Stateless — no session store needed. Works across multiple API instances. Standard for REST APIs and mobile clients.

---

## Test Coverage

```bash
pytest tests/ -v

# Results: 36 passed in < 40s
# Unit:        24 tests — parsers, chunkers, embedders, retrieval
# Integration:  8 tests — ingestion pipeline, API endpoints
# E2E:          4 tests — full upload → process → query flow
```

---

## What This Demonstrates

**ML Engineering** — Embedding pipelines, vector search, reranking, multimodal fusion, evaluation metrics

**GenAI Engineering** — RAG architecture, agentic systems, prompt engineering, hallucination measurement

**Backend Engineering** — Async FastAPI, SQLAlchemy, Celery, Redis, JWT auth, REST API design

**System Design** — Scalable ingestion pipeline, caching strategy, per-user isolation, multi-tenant readiness

**Production Thinking** — Observability, fault tolerance, security, Docker deployment, CI/CD

---

## Resume Bullets

```
• Built production-grade Multimodal RAG platform processing PDF/DOCX/PPTX/XLSX
  with hybrid retrieval (dense + BM25 + RRF fusion + cross-encoder reranking)

• Implemented agentic query planner dynamically routing queries across text,
  table, figure, and chart retrieval tools using sentence-transformers + CLIP

• Designed async document ingestion pipeline with Celery + Redis supporting
  parallel processing of text, tables, and images with VLM captioning

• Achieved 36/36 test coverage across unit, integration, and E2E test suites
  with CI/CD pipeline via GitHub Actions

• Deployed on Azure with JWT authentication and per-user data isolation
```

---

## License

MIT — feel free to use, modify, and build upon this work.

---

<div align="center">
Built with ◉ by Asmita Sharma
</div>