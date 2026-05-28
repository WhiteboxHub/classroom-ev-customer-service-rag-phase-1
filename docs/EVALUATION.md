# EV RAG Platform — Evaluation Guide

## Overview

The EV RAG Platform uses RAGAS (Retrieval Augmented Generation Assessment) to systematically evaluate retrieval quality and generation faithfulness across the EV troubleshooting domain.

---

## Golden Dataset

**Location:** `evaluation/datasets/ev_golden_set.json`

The golden evaluation dataset contains 10 expert-curated EV troubleshooting queries spanning all diagnostic categories:

| ID | Category | Difficulty | Query Topic |
|----|----------|-----------|-------------|
| ev_q001 | Battery | Medium | DTC P0A80 meaning and resolution |
| ev_q002 | Firmware | Hard | Charging failure after OTA 4.2.1 |
| ev_q003 | Charging | Easy | CCS DC fast charging procedure |
| ev_q004 | Battery | Hard | BMS_TEMP_HIGH thermal warning safety |
| ev_q005 | Firmware | Hard | OTA_INSTALL_FAIL_3 recovery |
| ev_q006 | Diagnostics | Medium | DTC U0100 CAN bus fault |
| ev_q007 | Service | Hard | Manual Service Disconnect (MSD) |
| ev_q008 | Firmware | Medium | ATMA v2 thermal management firmware |
| ev_q009 | Charging | Medium | AC Level 2 pilot signal errors |
| ev_q010 | Battery | Medium | State of Health (SoH) diagnostic |

Each entry includes:
- `query`: Natural language question
- `ground_truth`: Expert-written reference answer
- `contexts`: Expected source documents
- `category`: Diagnostic domain
- `difficulty`: easy / medium / hard

---

## RAGAS Metrics

| Metric | What It Measures | Target |
|--------|-----------------|--------|
| **Faithfulness** | Is the answer factually consistent with retrieved context? | > 0.80 |
| **Answer Relevancy** | Does the answer address the user's question? | > 0.85 |
| **Context Recall** | Are the correct source documents retrieved? | > 0.75 |
| **Context Precision** | Are retrieved documents relevant (not noisy)? | > 0.70 |

---

## Running Evaluation

### Full RAGAS Evaluation
```bash
# Using Makefile
make eval

# Direct execution
python evaluation/runners/ragas_runner.py
```

### What It Does
1. Loads the 10-query golden dataset
2. Sends each query to the EV RAG API (`/api/v1/chat`)
3. Records answer, sources, latency, grounding status
4. Computes RAGAS metrics (or simple overlap fallback)
5. Saves timestamped JSON results to `evaluation/results/`

### Output
Results are saved to `evaluation/results/ev_ragas_eval_YYYYMMDD_HHMMSS.json`:

```json
{
    "evaluation_timestamp": "2024-01-15T12:00:00",
    "total_queries": 10,
    "ragas_metrics": {
        "faithfulness": 0.87,
        "answer_relevancy": 0.91,
        "context_recall": 0.82,
        "context_precision": 0.78
    },
    "avg_latency_ms": 1450.3,
    "grounded_rate": 0.90,
    "per_query_results": [...]
}
```

---

## Fallback Metrics

When the `ragas` library is not installed, the runner automatically falls back to a simple word-overlap metric:

```
overlap = |ground_truth_words ∩ answer_words| / |ground_truth_words|
```

This provides a rough quality signal without requiring the full RAGAS dependency chain.

---

## Interpreting Results

### Good Performance
- Faithfulness > 0.80 — Answers are grounded in retrieved context
- Context Recall > 0.75 — Correct documents are being retrieved
- Avg Latency < 2000ms — Acceptable for interactive use

### Areas for Improvement
- Low Faithfulness — Check hallucination guard sensitivity, review system prompt
- Low Context Recall — Consider adding more domain documents, tuning chunking
- Low Context Precision — Tune retrieval threshold, improve metadata filtering
- High Latency — Enable Redis caching, reduce top_k, warm cache for frequent queries

---

## Adding New Evaluation Queries

To expand the golden dataset, add entries to `evaluation/datasets/ev_golden_set.json`:

```json
{
    "id": "ev_q011",
    "query": "Your new EV troubleshooting question",
    "ground_truth": "Expert reference answer with specific technical details",
    "contexts": ["expected_source_document.md"],
    "category": "battery|charging|firmware|diagnostics|service",
    "difficulty": "easy|medium|hard"
}
```

Guidelines for ground truth:
- Include specific DTC codes, firmware versions, and voltage values
- Reference exact procedure steps from source documents
- Be precise about safety requirements (HV procedures, PPE)
- Include resolution actions, not just descriptions

---

## Continuous Evaluation

For automated quality monitoring, schedule evaluation runs:

```bash
# Run evaluation every 6 hours via cron
0 */6 * * * cd /app && python evaluation/runners/ragas_runner.py
```

Monitor trends in `evaluation/results/` over time to detect quality regressions after:
- New document ingestion
- Chunking strategy changes
- Embedding model upgrades
- System prompt modifications
