# ==============================================================
# EV RAG Platform — Makefile
# Operational shortcuts for the enterprise EV RAG platform
# ==============================================================

.PHONY: up down down-clean logs test ingest eval warm-cache sync-vectors \
        build push shell worker-logs flower health

# ── Stack Management ──────────────────────────────────────────
up:
	docker compose -f docker-compose.yml up -d --build

up-ops:
	docker compose -f docker-compose.yml -f docker-compose.ops.yml up -d --build

down:
	docker compose -f docker-compose.yml -f docker-compose.ops.yml down

down-clean:
	docker compose -f docker-compose.yml -f docker-compose.ops.yml down -v --remove-orphans

logs:
	docker compose -f docker-compose.yml -f docker-compose.ops.yml logs -f

api-logs:
	docker compose logs -f api

worker-logs:
	docker compose logs -f worker-ingestion worker-embedding

# ── Health Checks ─────────────────────────────────────────────
health:
	curl -s http://localhost:8000/api/v1/health | python -m json.tool

metrics:
	curl -s http://localhost:8000/api/v1/metrics | python -m json.tool

# ── Development ───────────────────────────────────────────────
dev:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 --log-level debug

dev-infra:
	docker compose up -d milvus redis postgres etcd minio

# ── Testing ───────────────────────────────────────────────────
test:
	docker compose exec api pytest tests/ -v --tb=short

test-local:
	pytest tests/ -v --tb=short

# ── Data Ingestion ────────────────────────────────────────────
ingest:
	python scripts/ingest_samples.py

ingest-all:
	curl -X POST http://localhost:8000/api/v1/ingest/path \
		-H "Content-Type: application/json" \
		-d '{"source_path": "data"}'

ingest-battery:
	curl -X POST http://localhost:8000/api/v1/ingest/path \
		-H "Content-Type: application/json" \
		-d '{"source_path": "data/battery_manuals"}'

ingest-dtc:
	curl -X POST http://localhost:8000/api/v1/ingest/path \
		-H "Content-Type: application/json" \
		-d '{"source_path": "data/dtc_codes"}'

ingest-firmware:
	curl -X POST http://localhost:8000/api/v1/ingest/path \
		-H "Content-Type: application/json" \
		-d '{"source_path": "data/firmware_updates"}'

# ── Operational Scripts ───────────────────────────────────────
warm-cache:
	python scripts/cache_warmup.py

data-quality:
	python scripts/data_quality_checks.py

sync-vectors:
	python scripts/reindex_documents.py

purge-stale:
	python scripts/purge_stale_vectors.py

backfill:
	python scripts/backfill_embeddings.py

# ── Evaluation ────────────────────────────────────────────────
eval:
	python evaluation/runners/ragas_runner.py

# ── Worker Management ─────────────────────────────────────────
flower:
	@echo "Celery Flower UI: http://localhost:5555"

worker-status:
	docker compose exec worker-ingestion celery -A app.workers.celery_app inspect active

# ── Build & Deploy ────────────────────────────────────────────
build:
	docker build -t xyz-ev-corp/ev-rag-backend:latest .
	docker build -t xyz-ev-corp/ev-rag-worker:latest -f infrastructure/docker/Dockerfile.worker .

push:
	docker push xyz-ev-corp/ev-rag-backend:latest
	docker push xyz-ev-corp/ev-rag-worker:latest

helm-deploy:
	helm upgrade --install ev-rag-platform infrastructure/helm/ev-rag-chart/ \
		--namespace ev-rag \
		--create-namespace \
		--values infrastructure/helm/ev-rag-chart/values.yaml

helm-lint:
	helm lint infrastructure/helm/ev-rag-chart/

# ── Quick Chat Test ───────────────────────────────────────────
chat:
	curl -X POST http://localhost:8000/api/v1/chat \
		-H "Content-Type: application/json" \
		-d '{"query": "What does DTC P0A80 mean and how do I fix it?"}'

retrieve:
	curl -X POST http://localhost:8000/api/v1/retrieve \
		-H "Content-Type: application/json" \
		-d '{"query": "battery thermal warning", "top_k": 3}'
