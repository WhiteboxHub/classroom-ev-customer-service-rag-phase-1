# EV RAG Platform – Phase 1

Enterprise-grade **Retrieval-Augmented Generation** system for EV troubleshooting, aligned with the EV RAG Phase-1 study guide architecture.

## Capabilities

- Enterprise document ingestion (PDF, Markdown, text)
- PDF parsing, preprocessing, metadata enrichment, semantic chunking
- Sentence Transformer **MiniLM** embeddings
- **Milvus** vector store (HNSW, cosine similarity, metadata filters)
- **Semantic + BM25 hybrid retrieval** with reciprocal rank fusion
- **Cross-encoder reranking** with keyword fallback
- **OpenAI GPT** grounded generation (RetrievalQA-style orchestration)
- Multi-turn **conversation memory**
- **Redis** caching (embeddings, retrieval, chat responses)
- **FastAPI** REST APIs with logging middleware and latency tracking
- **Streamlit** troubleshooting chat UI with source citations
- **Docker Compose** deployment (Milvus, Redis, API, UI)

## Project structure

```
rag-ev-phase-1/
├── app/
│   ├── api/              # FastAPI routes, schemas, middleware
│   ├── cache/            # Redis caching
│   ├── core/             # Config, logging, exceptions
│   ├── embeddings/       # MiniLM embedding service
│   ├── generation/       # Prompts, LLM, RAG chain
│   ├── ingestion/        # Parse → preprocess → chunk → index
│   ├── memory/           # Conversation memory
│   ├── observability/    # Metrics & tracing callbacks
│   ├── retrieval/        # Semantic, BM25, hybrid, rerank, RAG service
│   ├── utils/
│   └── vectorstore/      # Milvus client
├── data/sample_ev_docs/  # Sample EV troubleshooting corpus
├── streamlit_app/        # Enterprise chat UI
├── scripts/              # CLI utilities
├── docs/API.md           # API reference
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

## Quick start (Docker – recommended)

1. **Copy environment file**
   ```bash
   cd rag-ev-phase-1
   copy .env.example .env
   ```
   Set `OPENAI_API_KEY` in `.env`.

2. **Start infrastructure and services**
   ```bash
   docker compose up -d --build
   ```
   Wait until Milvus and API are healthy (~1–2 minutes on first run).

3. **Ingest sample EV dataset**
   ```bash
   curl -X POST http://localhost:8000/api/v1/ingest/path -H "Content-Type: application/json" -d "{\"source_path\": \"sample_ev_docs\"}"
   ```

4. **Open applications**
   - API docs: http://localhost:8000/docs
   - Streamlit UI: http://localhost:8501

5. **Example chat request**
   ```bash
   curl -X POST http://localhost:8000/api/v1/chat -H "Content-Type: application/json" -d "{\"query\": \"Vehicle not charging after OTA 4.2.1\"}"
   ```

## Local development (without Docker)

### Prerequisites

- Python 3.11+
- Running **Milvus** (standalone) on `localhost:19530`
- Running **Redis** on `localhost:6379`
- OpenAI API key

### Setup

```bash
cd rag-ev-phase-1
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Start Milvus/Redis via Docker if needed:
```bash
docker compose up -d milvus redis etcd minio
```

Run API:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Ingest samples:
```bash
python scripts/ingest_samples.py
```

Run Streamlit:
```bash
set STREAMLIT_API_URL=http://localhost:8000
streamlit run streamlit_app/app.py
```

## API overview

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/health` | GET | Health check (Milvus, Redis) |
| `/api/v1/metrics` | GET | Latency metrics |
| `/api/v1/ingest/upload` | POST | Upload & ingest document |
| `/api/v1/ingest/path` | POST | Ingest file or directory |
| `/api/v1/ingest/documents` | GET | List indexed documents |
| `/api/v1/retrieve` | POST | Hybrid retrieval only |
| `/api/v1/chat` | POST | Grounded multi-turn chat |

See [docs/API.md](docs/API.md) for request/response schemas.

## Sample dataset

Included under `data/sample_ev_docs/`:

- Charging failure after OTA
- Battery DTC P0A80
- DC fast charging (CCS) guide
- Firmware OTA recovery
- Infotainment blank screen procedure

## Architecture workflow

1. **Ingestion** – PDF/text → clean → metadata → chunk → embed → Milvus + BM25 index  
2. **Query** – clean → intent metadata → instruction-formatted embedding  
3. **Retrieval** – Milvus semantic + BM25 → RRF fusion → cross-encoder rerank  
4. **Generation** – strict grounding prompt → OpenAI GPT → citations  
5. **Cache** – Redis for retrieval/chat; invalidated on new ingestion  

## Configuration

All settings are environment-driven (see `.env.example`). Key variables:

- `OPENAI_API_KEY`, `OPENAI_MODEL`
- `MILVUS_HOST`, `MILVUS_PORT`, `MILVUS_COLLECTION`
- `REDIS_HOST`, `CACHE_TTL_SECONDS`
- `EMBEDDING_MODEL` (default: `sentence-transformers/all-MiniLM-L6-v2`)
- `CHUNK_SIZE`, `CHUNK_OVERLAP`, `RERANK_TOP_K`

## License

Internal enterprise prototype – XYZ EV Corp Phase-1 RAG platform.
