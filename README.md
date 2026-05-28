# Classroom EV Customer Service RAG - Phase 1

**XYZ EV Corp — Enterprise EV Troubleshooting Agent**

This project implements Phase 1 of the Retrieval Augmented Generation (RAG) system for XYZ EV Corp's field technician support platform. It is designed to assist EV service technicians, customer support agents, and fleet operators by providing accurate, context-aware answers derived from internal EV documentation.

---

## 💡 The Idea

EV field technicians and support agents struggle to find the right diagnostic information quickly across disconnected service manuals, DTC catalogs, firmware changelogs, and charging infrastructure docs. This project unifies these sources into a single, enterprise-grade RAG pipeline.

**Phase 1 Goals:**
*   **Ingestion**: Process PDFs, Markdown, HTML, S3, Confluence, SharePoint, and Wiki docs into a vector store.
*   **Retrieval**: Hybrid search (Semantic + BM25) with cross-encoder reranking.
*   **Generation**: LLM-based grounded answer synthesis with source citations.
*   **Guardrails**: Hallucination prevention, HV safety disclaimers, confidence thresholds.
*   **Interface**: Streamlit chat UI + Open-WebUI pipeline for technician interaction.

---

## 🏗 Design & Architecture

The system follows a microservices architecture orchestrated via Docker Compose.

```mermaid
graph TD
    User[EV Technician] -->|HTTP/80| Gateway[NGINX Gateway]
    Gateway -->|/| StreamlitUI[Streamlit Chat UI]
    Gateway -->|/api| Backend[FastAPI Backend]

    StreamlitUI -->|Internal API| Backend

    Backend -->|Read/Write| DB[(PostgreSQL)]
    Backend -->|Cache/Queue| Redis[(Redis)]
    Backend -->|Vectors| Milvus[(Milvus)]

    Backend -->|Async Tasks| Celery[Celery Workers]
    Celery -->|Broker| Redis

    subgraph Ingestion Connectors
        PDF[PDF Loader]
        S3[S3 Loader]
        Confluence[Confluence]
        SharePoint[SharePoint]
        Wiki[Wiki Loader]
    end

    Celery --> Ingestion Connectors

    subgraph Guardrails
        HG[Hallucination Guard]
        SF[Safety Filter]
        TG[Threshold Guard]
    end

    Backend --> Guardrails

    subgraph Observability
        Prometheus -->|Scrape| Backend
        Grafana -->|Query| Prometheus
        OTel[OTel Collector] -->|Traces| Jaeger
        Langfuse -->|LLM Traces| Backend
    end
```

### Components

*   **API Gateway (Nginx)**: Entry point for all traffic. Rate limiting, routing, WebSocket support.
*   **Frontend (Streamlit / Open-WebUI)**: Chat interface for EV troubleshooting interactions.
*   **Backend (FastAPI)**: Core RAG logic for ingestion, retrieval, reranking, and generation.
    *   **Services**: Modularized logic — ingestion pipeline, hybrid retriever, RAG orchestrator.
    *   **Workers**: Celery async tasks — document ingestion, embedding backfill, vector sync.
    *   **Guardrails**: Hallucination guard, HV safety filter, confidence threshold enforcement.
    *   **API**: RESTful endpoints for chat, retrieval, ingestion, health, metrics, admin.
*   **Data Layer**:
    *   **PostgreSQL**: Relational metadata (documents, DTC catalog, firmware catalog, tenants, sessions).
    *   **Redis**: Query cache, embedding cache, and Celery message broker.
    *   **Milvus**: High-performance vector database with HNSW indexing and EV-specific schema.

---

## 📂 Folder Structure

How to navigate the codebase:

```text
.
├── app/                        # Core Application
│   ├── api/                    # FastAPI routes (chat, ingest, admin, health)
│   ├── core/                   # Config, logging, exceptions
│   ├── cache/                  # Redis cache layer
│   ├── embeddings/             # Embedding service (sentence-transformers)
│   ├── ingestion/              # Ingestion pipeline
│   │   ├── loaders/            # Document connectors (PDF, HTML, S3, Confluence, SharePoint, Wiki)
│   │   ├── chunker.py          # EV-domain-aware chunking
│   │   ├── metadata_extractor.py # DTC, firmware, charging metadata extraction
│   │   ├── preprocessor.py     # Document preprocessing & cleaning
│   │   └── pipeline.py         # Orchestrated ingestion flow
│   ├── retrieval/              # Retrieval pipeline
│   │   ├── hybrid_retriever.py # Semantic + BM25 fusion
│   │   ├── reranker.py         # Cross-encoder reranking
│   │   ├── bm25_retriever.py   # BM25 sparse retrieval
│   │   ├── query_processor.py  # Query cleaning & expansion
│   │   └── rag_service.py      # End-to-end RAG orchestrator
│   ├── vectorstore/            # Milvus vector store client
│   ├── guardrails/             # Hallucination guard, safety filter, threshold guard
│   ├── workers/                # Celery async workers (ingestion, embedding, sync)
│   └── observability/          # Langfuse, OpenTelemetry, Prometheus, in-memory metrics
├── data/                       # EV Domain Knowledge Base (7 categories)
│   ├── battery_manuals/        # Battery diagnostics, SoH, thermal management
│   ├── charging_docs/          # CCS DC, AC Level 2, EVSE troubleshooting
│   ├── dtc_codes/              # Diagnostic Trouble Code catalog
│   ├── firmware_updates/       # Firmware changelogs (4.1.0, 4.2.1)
│   ├── service_manuals/        # HV service procedures, CAN bus troubleshooting
│   ├── technician_notes/       # Field technician lessons learned
│   └── ota_release_notes/      # Customer-facing OTA release notes
├── evaluation/                 # RAGAS Evaluation Framework
│   ├── datasets/               # Golden evaluation dataset (10 EV queries)
│   └── runners/                # RAGAS evaluation runner
├── init_data/                  # Database & Schema Seeds
│   ├── milvus/                 # Milvus collection schema (17-field EV schema)
│   ├── postgres/               # PostgreSQL schema + DTC/tenant seed data
│   └── prompts/                # Role-based system prompt templates
├── infrastructure/             # Infrastructure as Code
│   ├── helm/                   # Helm chart (Chart.yaml, values.yaml)
│   ├── terraform/              # AWS Terraform (EKS, RDS, S3, ElastiCache)
│   ├── argocd/                 # ArgoCD GitOps application manifest
│   └── docker/                 # Production Dockerfiles (backend, worker)
├── observability/              # Ops Observability Configs
│   ├── prometheus/             # Prometheus scrape config
│   ├── otel/                   # OpenTelemetry Collector config
│   └── grafana/                # Grafana datasource provisioning
├── gateway/                    # Nginx API Gateway config
├── open-webui/                 # Open-WebUI pipeline adapter
├── resources/                  # Model registry, prompt registry, tenant config, logging
├── scripts/                    # Operational scripts
│   ├── backfill_embeddings.py  # Re-embed after model upgrade
│   ├── cache_warmup.py         # Pre-warm cache for high-frequency DTC queries
│   ├── data_quality_checks.py  # Validate corpus metadata & chunk quality
│   ├── purge_stale_vectors.py  # Remove orphaned Milvus vectors
│   └── reindex_documents.py    # Full re-ingestion after schema changes
├── tests/                      # Test suite
│   └── unit/                   # Unit tests (ingestion, retrieval, reranker)
├── streamlit_app/              # Streamlit chat interface
├── docker-compose.yml          # Main application stack
├── docker-compose.ops.yml      # Observability stack (Prometheus, Grafana, Jaeger, Flower)
├── Makefile                    # Developer & operator shortcuts
├── .env.example                # Environment configuration template
└── README.md                   # This file
```

---

## 🚀 How to Run

### Prerequisites
*   Docker & Docker Compose
*   Make (optional)
*   OpenAI API Key

### 1. Configuration
Copy the template and fill in your secrets (OpenAI API Key, database creds).
```bash
cp .env.example .env
# Edit .env with your OPENAI_API_KEY
```

### 2. Start the Stack
This spins up the Gateway, Backend, Streamlit UI, Databases, Workers, and Observability tools.
```bash
# Application stack only
make up

# Full stack with observability (Prometheus, Grafana, Jaeger, Flower)
make up-ops

# OR manually
docker compose -f docker-compose.yml -f docker-compose.ops.yml up -d --build
```

### 3. Ingest EV Documentation
Load the sample EV knowledge base into the vector store.
```bash
make ingest-all
# OR ingest specific categories
make ingest-battery
make ingest-dtc
make ingest-firmware
```

### 4. Access
*   **Streamlit Chat UI**: [http://localhost:8501](http://localhost:8501)
*   **API Gateway**: [http://localhost:8080](http://localhost:8080)
*   **API Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
*   **Grafana Dashboards**: [http://localhost:3001](http://localhost:3001)
*   **Celery Flower**: [http://localhost:5555](http://localhost:5555)
*   **Jaeger Traces**: [http://localhost:16686](http://localhost:16686)

---

## 📖 How to Use

### For Developers
1.  **Ingestion**: `POST /api/v1/ingest/path` — Trigger document processing from a file path.
2.  **Chat**: `POST /api/v1/chat` — Send a query and get a grounded answer with citations.
3.  **Retrieve**: `POST /api/v1/retrieve` — Get ranked source chunks without generation.
4.  **Health**: `GET /api/v1/health` — Check system health (API, Milvus, Redis).
5.  **Metrics**: `GET /api/v1/metrics` — View retrieval latency, token usage, cache stats.

### For Technicians
1.  Open the Streamlit Chat UI at [http://localhost:8501](http://localhost:8501).
2.  Ask questions about DTCs, battery diagnostics, charging issues, or firmware updates.
3.  Responses include source citations and HV safety warnings where applicable.

### Quick Test
```bash
# Ask about a DTC code
make chat
# Retrieve sources for a query
make retrieve
```

---

## 🧪 How to Test

### Automated Tests
Run the pytest suite:
```bash
make test-local
# OR inside Docker
make test
```

### Evaluation
Run RAGAS metrics against the 10-query EV golden dataset:
```bash
make eval
# OR
python evaluation/runners/ragas_runner.py
```

### Data Quality
Validate corpus metadata completeness and chunk distribution:
```bash
python scripts/data_quality_checks.py
```

---

## 🚢 How to Deploy

### Docker Compose (Single Node)
The provided `docker-compose.yml` is production-ready for single-node deployments. Ensure `.env` is secure and `LOG_LEVEL` is set to `WARNING` in production.

### Kubernetes (Helm)
For scaling, use the charts in the `infrastructure/helm/` directory.
1.  Build images and push to registry:
    ```bash
    make build && make push
    ```
2.  Update `values.yaml` with image tags and secrets.
3.  Deploy via Helm:
    ```bash
    make helm-deploy
    ```

### GitOps (ArgoCD)
For continuous deployment, apply the ArgoCD application manifest:
```bash
kubectl apply -f infrastructure/argocd/application.yaml
```

---

## 🛠 Maintenance

*   **Reindexing**: `python scripts/reindex_documents.py`
*   **Cache Warmup**: `python scripts/cache_warmup.py`
*   **Embedding Backfill**: `python scripts/backfill_embeddings.py`
*   **Purge Stale Vectors**: `python scripts/purge_stale_vectors.py --list`
*   **Data Quality**: `python scripts/data_quality_checks.py`
*   **Worker Status**: `make worker-status`
*   **Postgres Backup**: `docker compose exec postgres pg_dump -U evrag evragdb > backup.sql`

---

## 📊 EV Domain Coverage

| Category | Documents | Key Topics |
|----------|-----------|------------|
| Battery Manuals | 3 | SoH diagnostics, thermal management, DTC P0A80, cell voltage spread |
| Charging Docs | 2 | CCS DC fast charging, AC Level 2 troubleshooting, J1772 pilot signals |
| DTC Codes | 1 | Full catalog: P0A80, P1E00, P1E10, P0A94, P0A1F, U0100, B2AAA |
| Firmware Updates | 2 | Firmware 4.1.0 (ATMA v2), 4.2.1 (CCS fix, OTA reliability) |
| Service Manuals | 2 | HV service procedures, MSD, CAN bus troubleshooting |
| Technician Notes | 1 | Field lessons learned, MSD common mistakes |
| OTA Release Notes | 1 | Customer-facing 4.2.1 update notes |

---

## 🔒 Safety & Guardrails

*   **Hallucination Guard**: Detects responses not grounded in retrieved context.
*   **HV Safety Filter**: Auto-injects high-voltage safety disclaimers for battery/charging procedures.
*   **Dangerous Query Blocker**: Blocks queries requesting BMS bypass, safety override, etc.
*   **Threshold Guard**: Returns structured fallback when retrieval confidence is below threshold.
*   **Tenant Isolation**: Role-based access control (technicians, support, fleet ops, engineers).
