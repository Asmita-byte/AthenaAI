# AthenaAI - Multimodal Document Intelligence Platform

Most RAG systems fail in the real world. They chunk text, embed it, retrieve it — and completely ignore the tables, charts, figures, and images that often contain the most important information in a document.

This platform was built to solve that.

---

## The Problem

Imagine you upload an annual report and ask: *"What are the key financial risks?"*

A typical RAG system searches through text chunks. But the risk summary might be in a **table on page 12**. The revenue breakdown might be in a **chart on page 8**. The executive commentary might reference a **figure on page 23**.

A text-only RAG system misses all of it.

Add multiple documents into the mix — comparing two research papers, verifying a presentation's claims against a report — and the problem compounds further.

---

## The Solution

A production-grade **Multimodal Agentic RAG** system that:

- Parses **every modality** — text, tables, charts, figures, images — from PDF, DOCX, PPTX, XLSX, CSV, and TXT
- Embeds **text and images** into separate vector spaces (sentence-transformers + CLIP)
- Retrieves using **hybrid search** — dense semantic retrieval + BM25 keyword retrieval, fused and reranked
- Uses an **agentic query planner** that dynamically decides which retrieval tools to invoke based on the question
- Returns **grounded answers with exact citations** — page number, table index, figure reference, source file
- Supports **multi-document reasoning** — compare, contrast, verify, and detect contradictions across documents simultaneously

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Streamlit Frontend                 │
│        Upload · Chat · Citations · Evaluation        │
└─────────────────────┬───────────────────────────────┘
                      │ HTTP
                      ▼
┌─────────────────────────────────────────────────────┐
│                   FastAPI Backend                    │
│         /upload  /query  /status  /health            │
└──────┬──────────────────────────┬───────────────────┘
       │                          │
       ▼                          ▼
┌─────────────┐        ┌──────────────────────────────┐
│ Celery +    │        │        Query Pipeline         │
│ Redis Queue │        │                              │
│             │        │  Query → Planner Agent       │
│ • Parse     │        │    → Tool Selection          │
│ • Embed     │        │    → Hybrid Retrieval        │
│ • Caption   │        │    → RRF Fusion              │
│ • KG Build  │        │    → Cross-Encoder Rerank    │
└──────┬──────┘        │    → LLM Generation          │
       │               │    → Citation Attachment      │
       ▼               └──────────────────────────────┘
┌─────────────────────────────────────────────────────┐
│                  Ingestion Pipeline                  │
│                                                     │
│  File → Validator → Format Router                   │
│              │                                      │
│    ┌─────────┼──────────┬──────────┐               │
│    ▼         ▼          ▼          ▼               │
│  PDF       DOCX       PPTX      XLSX/CSV            │
│    └─────────┴──────────┴──────────┘               │
│                    │                                │
│         ┌──────────┼──────────┐                    │
│         ▼          ▼          ▼                    │
│    Text Chunks  Tables    Images/Figures            │
│         │          │          │                    │
│    Text Embed  Text Embed  CLIP Embed              │
│                         + VLM Caption              │
│                    │                               │
│              Qdrant Vector DB                       │
│         (text_chunks · image_chunks)               │
└─────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────┐
│                   Storage Layer                      │
│  SQLite · Local FS · Qdrant · Redis Cache           │
└─────────────────────────────────────────────────────┘
```

---

## Why Hybrid Retrieval?

Most systems stop at vector search. This platform goes further.

```
User Query
    │
    ├── Dense Retrieval    →  "revenue" matches "income", "earnings"
    │   (Qdrant ANN)          Semantic similarity, handles paraphrasing
    │
    ├── Sparse Retrieval   →  "Q3 2023 SEC filing revenue" exact match
    │   (BM25)                Keyword precision, handles rare terms
    │
    ├── RRF Fusion         →  Combines both ranked lists mathematically
    │   (Reciprocal Rank)     No weight tuning needed, robust by design
    │
    └── Cross-Encoder      →  Re-scores every chunk against the query
        Reranker               Most accurate, used as final precision filter
```

Dense retrieval has high recall. BM25 has high keyword precision. The cross-encoder has the highest accuracy but is too slow to run on thousands of chunks. Each stage feeds the next — trading speed for precision as the candidate pool shrinks.

---

## Agentic Query Planning

Not every question needs every retrieval tool. A question about revenue trends needs tables. A question about a diagram needs image retrieval. A comparison question needs multi-document context.

```
"Compare profit margins across both uploaded reports"
                    │
                    ▼
            Query Planner Agent
                    │
       ┌────────────┼────────────┐
       ▼            ▼            ▼
  Text Tool    Table Tool   Metadata Tool
       │            │            │
       └────────────┴────────────┘
                    │
            Evidence Aggregator
                    │
            LLM Answer Generator
                    │
            Citation Attacher
                    │
    "Report A shows 23% margin (Table 4, p.12)
     vs Report B's 18% margin (Table 2, p.8)"
```

The planner is LLM-powered. It reads the query, selects the appropriate tools, executes them in parallel where possible, and aggregates evidence before passing it to the generator.

---

## Tech Stack

| Layer | Technology | Why |
|---|---|---|
| Backend API | FastAPI + Uvicorn | Async, production-grade, auto-docs |
| Task Queue | Celery + Redis | Industry standard, fault-tolerant |
| Vector DB | Qdrant (local) | OSS, payload filtering, CPU-capable |
| Text Embeddings | all-MiniLM-L6-v2 | Fast, free, strong quality |
| Image Embeddings | CLIP ViT-B/32 | Cross-modal retrieval, OSS |
| Reranker | ms-marco-MiniLM-L-6-v2 | Free, accurate cross-encoder |
| LLM | Groq llama-3.3-70b | Free tier, extremely fast inference |
| LLM Fallback | Gemini 1.5 Flash | Free tier, generous limits |
| Vision LLM | Qwen2-VL-7B | OSS, runs locally |
| Metadata DB | SQLite + SQLAlchemy | Zero config, async, swap-ready |
| Frontend | Streamlit | Rapid UI, Python-native |
| Evaluation | Ragas + DeepEval | Industry standard RAG metrics |

---

## Evaluation Framework

Every answer is measurable. The platform tracks:

| Metric | What It Measures |
|---|---|
| Faithfulness | Is the answer grounded in the retrieved context? |
| Answer Relevancy | Does the answer actually address the question? |
| Context Recall | Did retrieval surface the right chunks? |
| Context Precision | Were the retrieved chunks actually useful? |
| Hallucination Rate | How often does the LLM fabricate information? |

---

## Project Structure

```
multimodal_doc_intelligence/
│
├── backend/                  # FastAPI app
│   ├── api/                  # Route handlers
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
├── retrieval/                # Dense, sparse, fusion, reranking
├── agents/                   # Query planner + retrieval tools
├── generation/               # LLM answer generation + citations
├── knowledge_graph/          # Cross-document entity graph
├── vectorstore/              # Qdrant client + indexing
├── workers/                  # Celery background tasks
├── evaluation/               # Ragas + DeepEval pipelines
├── observability/            # Latency tracking + metrics
├── frontend/                 # Streamlit UI
└── tests/                    # Unit, integration, e2e
```

---

## Getting Started

```bash
# Clone
git clone https://github.com/Asmita-byte/AthenaAI.git
cd AthenaAI

# Environment
conda create -n multimodal_env python=3.11 -y
conda activate multimodal_env
pip install -r requirements.txt

# Configure
cp .env.example .env
# Add your GROQ_API_KEY and GEMINI_API_KEY in .env

# Start Redis
docker run -d -p 6379:6379 redis:alpine

# Start Celery Worker
celery -A workers.celery_app worker --loglevel=info

# Start API
uvicorn backend.main:app --reload --port 8000

# Start Frontend
streamlit run frontend/app.py
```

---

## Key Engineering Decisions

**Why Qdrant over Pinecone/Weaviate?**
Runs entirely locally — no API costs, no data leaving your machine, persistent storage with a single config change for production deployment.

**Why separate text and image collections?**
Text embeddings (384-dim) and CLIP embeddings (512-dim) live in different vector spaces. Mixing them in one collection would require dimension alignment and hurt retrieval quality for both modalities.

**Why SQLite over PostgreSQL?**
Zero configuration for local development. The SQLAlchemy async layer means swapping to PostgreSQL in production requires changing exactly one environment variable.

**Why Celery over FastAPI BackgroundTasks?**
FastAPI BackgroundTasks die if the server restarts. Celery tasks survive restarts, support retries, and scale horizontally — critical for a document processing pipeline that can take minutes per file.

---

## What This Demonstrates

- **ML Engineering** — Embedding pipelines, vector search, reranking, multimodal fusion
- **GenAI Engineering** — RAG architecture, agentic systems, prompt engineering, evaluation
- **Backend Engineering** — Async FastAPI, SQLAlchemy, Celery, Redis, REST API design
- **System Design** — Scalable ingestion pipeline, caching strategy, multi-tenant readiness
- **Production Thinking** — Observability, fault tolerance, security, Docker deployment

---

## License

MIT