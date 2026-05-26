# EV RAG API Documentation

Base URL: `http://localhost:8000/api/v1`

Interactive docs: `http://localhost:8000/docs`

## Health

### `GET /health`
Returns service, Milvus, and Redis status.

### `GET /metrics`
Returns average retrieval/generation latency summaries.

## Ingestion

### `POST /ingest/upload`
Multipart upload of PDF/MD/TXT with optional metadata form fields:
- `vehicle_model`, `firmware_version`, `charging_type`, `diagnostic_category`

### `POST /ingest/path`
```json
{
  "source_path": "sample_ev_docs",
  "vehicle_model": "XYZ Model E",
  "diagnostic_category": "charging"
}
```

### `GET /ingest/documents`
Lists indexed documents from Milvus.

## Retrieval

### `POST /retrieve`
```json
{
  "query": "car not charging after OTA update",
  "top_k": 5,
  "use_hybrid": true,
  "use_rerank": true,
  "metadata_filter": {
    "diagnostic_category": "charging"
  }
}
```

Response includes `sources[]` with chunk text, scores, and metadata.

## Chat

### `POST /chat`
```json
{
  "query": "What is the procedure for DTC P0A80?",
  "session_id": "optional-session-id",
  "use_hybrid": true,
  "use_rerank": true,
  "include_sources": true
}
```

Response fields:
- `answer` – grounded troubleshooting guidance
- `citations` – traceable source references
- `sources` – retrieved chunks
- `history` – multi-turn conversation
- `grounded` – whether answer is grounded in retrieved context
- `latency_ms` – end-to-end latency

## Headers
Responses include:
- `X-Request-ID`
- `X-Process-Time-Ms`
