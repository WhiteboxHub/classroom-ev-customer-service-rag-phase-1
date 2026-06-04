# EV RAG Platform — API Reference

## Base URL
```
http://localhost:8000/api/v1
```

---

## Endpoints

### Chat

#### `POST /api/v1/chat`
Send a natural language query and receive a grounded answer with source citations.

**Request Body:**
```json
{
    "query": "What does DTC P0A80 mean and how do I fix it?",
    "session_id": "optional-uuid",
    "top_k": 5,
    "use_hybrid": true,
    "use_rerank": true
}
```

**Response:**
```json
{
    "answer": "DTC P0A80 indicates 'Replace Hybrid/EV Battery Pack'... [Source 1]",
    "sources": [
        {
            "text": "DTC P0A80 is set when SoH drops below 70%...",
            "source_file": "dtc_catalog.md",
            "score": 0.92,
            "metadata": {
                "diagnostic_category": "battery",
                "dtc_code": "P0A80",
                "firmware_version": "4.1.0"
            }
        }
    ],
    "latency_ms": 1250.3,
    "grounded": true,
    "retrieval_mode": "hybrid_reranked"
}
```

---

### Retrieval

#### `POST /api/v1/retrieve`
Retrieve ranked source chunks without LLM generation.

**Request Body:**
```json
{
    "query": "battery thermal warning procedure",
    "top_k": 5,
    "metadata_filter": {
        "diagnostic_category": "battery",
        "vehicle_platform": "EV-3000"
    }
}
```

**Response:**
```json
{
    "sources": [...],
    "latency_ms": 320.5,
    "retrieval_mode": "hybrid_reranked",
    "total_candidates": 20
}
```

---

### Ingestion

#### `POST /api/v1/ingest/upload`
Upload a PDF or Markdown file for ingestion.

**Request:** `multipart/form-data`
- `file`: PDF or MD file (max 100MB)

**Response:**
```json
{
    "document_id": "doc_abc123",
    "source_file": "battery_guide.pdf",
    "chunks_indexed": 45,
    "metadata": {
        "diagnostic_category": "battery",
        "dtc_codes_found": ["P0A80", "P0A1F"]
    }
}
```

#### `POST /api/v1/ingest/path`
Ingest documents from a local filesystem path.

**Request Body:**
```json
{
    "source_path": "data/battery_manuals",
    "metadata_overrides": {
        "vehicle_platform": "EV-3000"
    }
}
```

---

### Health & Metrics

#### `GET /api/v1/health`
System health check.

**Response:**
```json
{
    "status": "healthy",
    "components": {
        "api": "healthy",
        "milvus": "healthy",
        "redis": "healthy",
        "postgres": "healthy"
    },
    "version": "1.0.0",
    "uptime_seconds": 86400
}
```

#### `GET /api/v1/metrics`
Operational metrics snapshot.

**Response:**
```json
{
    "uptime_seconds": 86400,
    "counters": {
        "retrieval_requests_total": 1523,
        "generation_requests_total": 1200,
        "cache_hits_query": 890,
        "cache_misses_query": 633,
        "ingestion_chunks_total": 456,
        "errors_total": 3
    },
    "histograms": {
        "retrieval_latency_seconds": {
            "count": 1523,
            "avg": 0.45,
            "p50": 0.38,
            "p95": 1.20,
            "p99": 2.10
        }
    }
}
```

---

### Admin

#### `GET /api/v1/documents`
List all indexed documents.

#### `DELETE /api/v1/documents/{document_id}`
Delete a document and its vectors.

#### `GET /api/v1/collections/stats`
Milvus collection statistics.

---

## Async Worker API (Celery Tasks)

These tasks are dispatched via Celery and execute asynchronously:

| Task Name | Queue | Description |
|-----------|-------|-------------|
| `ev_rag.ingest_document` | ingestion | Ingest a single document |
| `ev_rag.ingest_directory` | ingestion | Batch ingest a directory |
| `ev_rag.ingest_s3_category` | ingestion | Ingest from S3 bucket prefix |
| `ev_rag.backfill_embeddings` | embedding | Re-embed document chunks |
| `ev_rag.warm_embedding_cache` | embedding | Pre-compute frequent query embeddings |
| `ev_rag.sync_vector_metadata` | sync | Milvus ↔ Postgres sync |
| `ev_rag.purge_stale_vectors` | sync | Remove orphaned vectors |

---

## Error Responses

All errors follow a consistent format:

```json
{
    "detail": "Descriptive error message",
    "error_code": "RETRIEVAL_THRESHOLD_NOT_MET",
    "timestamp": "2024-01-15T12:00:00Z"
}
```

| Status | Error Code | Description |
|--------|-----------|-------------|
| 400 | `INVALID_QUERY` | Query is empty or malformed |
| 404 | `DOCUMENT_NOT_FOUND` | Document ID does not exist |
| 422 | `INGESTION_FAILED` | File could not be parsed |
| 500 | `VECTOR_STORE_ERROR` | Milvus connection or query failure |
| 503 | `SERVICE_UNAVAILABLE` | Downstream dependency unhealthy |

---

## Metadata Filtering

The retrieve and chat endpoints support metadata filtering:

```json
{
    "metadata_filter": {
        "diagnostic_category": "battery",
        "vehicle_platform": "EV-3000",
        "firmware_version": "4.2.1",
        "dtc_code": "P0A80",
        "charging_type": "CCS",
        "tenant_id": "ev_technicians"
    }
}
```

All filter fields are optional. Multiple fields are combined with AND logic.
