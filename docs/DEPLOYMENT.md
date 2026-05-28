# EV RAG Platform — Deployment Guide

## Deployment Options

| Method | Use Case | Scaling |
|--------|----------|---------|
| Docker Compose | Dev, staging, single-node prod | Vertical only |
| Kubernetes (Helm) | Production multi-node | Horizontal auto-scaling |
| ArgoCD | GitOps continuous deployment | Automated sync |

---

## 1. Docker Compose Deployment

### Prerequisites
- Docker Engine 24.0+
- Docker Compose v2.20+
- 8GB+ RAM recommended
- OpenAI API Key

### Quick Start
```bash
# 1. Clone and configure
cp .env.example .env
# Edit .env: set OPENAI_API_KEY

# 2. Start application stack
make up

# 3. Start observability stack (optional)
make up-ops

# 4. Ingest EV documentation
make ingest-all

# 5. Verify
make health
```

### Service Ports

| Service | Port | URL |
|---------|------|-----|
| Nginx Gateway | 8080 | http://localhost:8080 |
| FastAPI Backend | 8000 | http://localhost:8000 |
| Streamlit UI | 8501 | http://localhost:8501 |
| Milvus | 19530 | — |
| Redis | 6379 | — |
| PostgreSQL | 5432 | — |
| Prometheus | 9090 | http://localhost:9090 |
| Grafana | 3001 | http://localhost:3001 |
| Jaeger | 16686 | http://localhost:16686 |
| Celery Flower | 5555 | http://localhost:5555 |

### Production Hardening
1. Set `LOG_LEVEL=WARNING` in `.env`
2. Remove port exposures for internal services (Milvus, Redis, Postgres)
3. Set strong `POSTGRES_PASSWORD` and `REDIS_PASSWORD`
4. Enable `LANGFUSE_ENABLED=true` for LLM observability
5. Set `CORS_ORIGINS` to specific domains (not `*`)

---

## 2. Kubernetes Deployment (Helm)

### Prerequisites
- Kubernetes 1.28+
- Helm 3.12+
- kubectl configured
- Container registry access

### Build & Push Images
```bash
# Build production images
make build

# Push to registry
make push
```

### Deploy with Helm
```bash
# Lint chart
make helm-lint

# Install / upgrade
make helm-deploy

# Or manually:
helm upgrade --install ev-rag-platform infrastructure/helm/ev-rag-chart/ \
    --namespace ev-rag \
    --create-namespace \
    --values infrastructure/helm/ev-rag-chart/values.yaml \
    --set secrets.openaiApiKey=$OPENAI_API_KEY
```

### Key Helm Values

| Parameter | Default | Description |
|-----------|---------|-------------|
| `replicaCount` | 2 | API pod replicas |
| `workers.ingestion.replicas` | 2 | Ingestion worker replicas |
| `workers.embedding.replicas` | 1 | Embedding worker replicas |
| `autoscaling.enabled` | true | HPA auto-scaling |
| `autoscaling.maxReplicas` | 10 | Max API replicas |
| `resources.api.limits.memory` | 4Gi | API memory limit |
| `resources.worker.limits.memory` | 8Gi | Worker memory limit |

---

## 3. ArgoCD GitOps Deployment

### Apply ArgoCD Application
```bash
kubectl apply -f infrastructure/argocd/application.yaml
```

### Sync Policy
- **Automated pruning**: Removes resources no longer in Git
- **Self-healing**: Reverts manual changes to match Git state
- **Create namespace**: Auto-creates `ev-rag` namespace

### Promotion Flow
```
feature branch → PR → main branch → ArgoCD auto-sync → production
```

---

## 4. AWS Infrastructure (Terraform)

### Resources Provisioned
- **EKS Cluster**: Kubernetes 1.28 with managed node groups
- **RDS PostgreSQL**: 15.4, multi-AZ (prod), encrypted, automated backups
- **ElastiCache Redis**: Redis 7.0 for caching and Celery broker
- **S3 Bucket**: Versioned, AES256-encrypted for EV documentation storage

### Deploy Infrastructure
```bash
cd infrastructure/terraform

# Initialize
terraform init

# Plan
terraform plan -var="db_password=YOUR_SECURE_PASSWORD"

# Apply
terraform apply -var="db_password=YOUR_SECURE_PASSWORD"
```

### Environment Variables
| Variable | Default | Description |
|----------|---------|-------------|
| `aws_region` | us-east-1 | AWS region |
| `environment` | prod | dev / staging / prod |
| `db_instance_class` | db.t3.medium | RDS instance size |
| `redis_node_type` | cache.t3.medium | ElastiCache node size |

---

## Monitoring & Alerts

### Health Check
```bash
curl http://localhost:8000/api/v1/health
```

### Key Metrics to Monitor
- `ev_rag_retrieval_latency_seconds` — P95 should be < 2s
- `ev_rag_generation_latency_seconds` — P95 should be < 10s
- `ev_rag_cache_hits_total` vs `ev_rag_cache_misses_total` — Hit rate > 60%
- `ev_rag_hallucination_blocked_total` — Should be < 5% of requests
- `ev_rag_ingestion_errors_total` — Should be 0 in steady state

### Grafana Access
- URL: http://localhost:3001
- Default credentials: `admin` / `ev_rag_admin`
