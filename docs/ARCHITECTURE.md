# EV RAG Platform — System Architecture

## Overview

The EV RAG Platform is a production-grade Retrieval Augmented Generation system built for XYZ EV Corp's field technician support operations. It provides grounded, citation-backed answers to EV troubleshooting queries by searching across service manuals, DTC catalogs, firmware changelogs, and charging infrastructure documentation.

---

## Architecture Layers

### 1. API Gateway Layer
- **Nginx** reverse proxy at port 80
- Rate limiting: 60 req/min for API, 10 req/min for ingestion
- Routes `/api/` → FastAPI backend, `/` → Streamlit UI
- WebSocket upgrade support for Streamlit
- 100MB max upload for PDF ingestion

### 2. Application Layer
- **FastAPI** backend with async request handling
- **Streamlit** chat UI for technician interaction
- **Open-WebUI** pipeline adapter for alternative frontend

### 3. RAG Pipeline

```
Query → QueryProcessor → EmbeddingService → HybridRetriever → Reranker → ThresholdGuard → LLM → SafetyFilter → Response
                                                 ↑                                              ↑
                                          Milvus + BM25                                   Hallucination Guard
```

#### Retrieval Flow
1. **Query Processing**: Cleaning, DTC extraction, query expansion
2. **Embedding**: `sentence-transformers/all-MiniLM-L6-v2` (384 dim)
3. **Hybrid Search**: Milvus semantic search + BM25 lexical search
4. **Reciprocal Rank Fusion**: Score fusion with configurable weights
5. **Cross-Encoder Reranking**: `cross-encoder/ms-marco-MiniLM-L-6-v2`
6. **Threshold Guard**: Minimum confidence enforcement with fallback
7. **Generation**: OpenAI `gpt-4o-mini` with grounded system prompt
8. **Safety Filter**: HV disclaimer injection, dangerous query blocking
9. **Hallucination Guard**: Source citation validation

### 4. Ingestion Pipeline

```
Source → Loader → Preprocessor → MetadataExtractor → Chunker → EmbeddingService → Milvus + BM25Index
```

#### Document Connectors
| Connector | Source | Protocol |
|-----------|--------|----------|
| PDFDocumentLoader | Local PDF files | PyPDF |
| HTMLDocumentLoader | Web pages / local HTML | BeautifulSoup |
| S3DocumentLoader | AWS S3 buckets | boto3 |
| ConfluenceLoader | Atlassian Confluence | REST API |
| SharePointLoader | Microsoft SharePoint | Graph API |
| WikiLoader | MediaWiki instances | MediaWiki API |

#### Chunking Strategy
- EV-domain-aware separators: `\n## `, `\n### `, `\nStep `
- Chunk size: 800 tokens, overlap: 150 tokens
- Table-aware splitting preserves diagnostic tables
- Section hierarchy tracked in metadata

### 5. Data Layer

| Store | Purpose | Technology |
|-------|---------|------------|
| Vector Store | Embedding search | Milvus (HNSW, COSINE, 384 dim) |
| Cache | Query/embedding cache | Redis 7 (512MB, LRU eviction) |
| Metadata DB | Document lifecycle, DTC catalog, sessions | PostgreSQL 15 |
| Message Broker | Celery task queue | Redis (DB 1) |

### 6. Async Worker Layer
- **Celery** with Redis broker
- Queues: `ingestion`, `embedding`, `sync`
- Tasks: document ingestion, embedding backfill, vector sync, stale purge
- Retry with exponential backoff

### 7. Observability Layer
| Tool | Purpose |
|------|---------|
| Prometheus | Metrics scraping (latency, tokens, cache, errors) |
| Grafana | Dashboard visualization |
| OpenTelemetry Collector | Distributed tracing |
| Jaeger | Trace visualization |
| Langfuse | LLM-specific observability |
| Celery Flower | Worker monitoring UI |
| In-memory Metrics | Lightweight `/metrics` endpoint fallback |

---

## Milvus Collection Schema

The `ev_troubleshooting` collection uses a 17-field schema:

| Field | Type | Purpose |
|-------|------|---------|
| `id` | VARCHAR(64) | Primary key (chunk ID) |
| `embedding` | FLOAT_VECTOR(384) | Semantic embedding |
| `text` | VARCHAR(65535) | Chunk content |
| `document_id` | VARCHAR(64) | Parent document reference |
| `source_file` | VARCHAR(512) | Original filename |
| `vehicle_model` | VARCHAR(128) | EV model (EV-3000, EV-5000) |
| `vehicle_platform` | VARCHAR(64) | Platform identifier |
| `firmware_version` | VARCHAR(64) | Applicable firmware version |
| `charging_type` | VARCHAR(64) | CCS, AC L2, CHAdeMO |
| `charging_standard` | VARCHAR(64) | ISO 15118, DIN 70121 |
| `diagnostic_category` | VARCHAR(128) | battery, charging, firmware, etc. |
| `dtc_code` | VARCHAR(32) | Extracted DTC code (P0A80, U0100) |
| `tenant_id` | VARCHAR(64) | Multi-tenant isolation key |
| `section_hierarchy` | VARCHAR(512) | Document section path |
| `page_number` | INT64 | Source page number |
| `chunk_index` | INT64 | Sequential chunk position |
| `doc_version` | VARCHAR(32) | Document version tracking |

**Index**: HNSW (M=16, efConstruction=200, COSINE metric)

---

## PostgreSQL Schema

7 tables for metadata lifecycle management:

- **tenants**: Multi-tenant access control with JSONB config
- **documents**: Document lifecycle tracking (active → deprecated → deleted)
- **document_versions**: Version lineage with change summaries
- **dtc_catalog**: DTC reference with severity, resolution steps, related DTCs
- **firmware_catalog**: Firmware versions with changelogs, known issues, fixed DTCs
- **retrieval_sessions**: Query analytics (latency, scores, grounding status)
- **chat_history**: Persistent conversation memory per session

---

## Guardrails Architecture

```
                    ┌──────────────────┐
                    │  ThresholdGuard  │ ← Before generation
                    │  (min confidence)│
                    └────────┬─────────┘
                             │ passes
                    ┌────────▼─────────┐
                    │  LLM Generation  │
                    └────────┬─────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
    ┌─────────▼──────┐ ┌────▼──────┐ ┌─────▼──────────┐
    │ Hallucination   │ │  Safety   │ │   HV Safety    │
    │ Guard           │ │  Filter   │ │   Disclaimer   │
    │ (source check)  │ │ (blocked) │ │   Injection    │
    └─────────────────┘ └───────────┘ └────────────────┘
```

---

## Tenant Isolation

| Tenant | Access Level | HV Procedures | Document Categories |
|--------|-------------|---------------|-------------------|
| `ev_technicians` | Full | ✅ Yes | All categories |
| `ev_support_tier1` | Standard | ❌ No | DTCs, charging, OTA |
| `ev_fleet_ops` | Standard | ❌ No | Firmware, OTA, charging |
| `ev_engineers` | Admin | ✅ Yes | All categories |
