"""
ragas_runner.py
RAGAS evaluation runner for the EV RAG Platform.
Evaluates: faithfulness, answer_relevancy, context_recall, context_precision.
Aligns with EV Study Guide Section 5.22 — RAG Evaluation Framework.
"""

import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.core.logging import get_logger

logger = get_logger(__name__)

GOLDEN_SET_PATH = Path(__file__).parent.parent / "datasets" / "ev_golden_set.json"
RESULTS_DIR = Path(__file__).parent.parent / "results"


class EVRAGASRunner:
    """
    RAGAS evaluation runner for the EV RAG platform.
    Evaluates retrieval quality and generation faithfulness using
    the EV golden dataset across all diagnostic categories.
    """

    def __init__(
        self,
        api_url: str = "http://localhost:8000",
        golden_set_path: Optional[Path] = None,
    ):
        self.api_url = api_url
        self.golden_set_path = golden_set_path or GOLDEN_SET_PATH
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    def load_golden_set(self) -> List[Dict[str, Any]]:
        """Load the EV golden evaluation dataset."""
        with open(self.golden_set_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        logger.info("golden_set_loaded", count=len(data))
        return data

    def run_retrieval(
        self, query: str, top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Call the EV RAG API retrieval endpoint."""
        try:
            import httpx
            response = httpx.post(
                f"{self.api_url}/api/v1/retrieve",
                json={"query": query, "top_k": top_k},
                timeout=30,
            )
            response.raise_for_status()
            return response.json().get("sources", [])
        except Exception as exc:
            logger.error("ragas_retrieval_failed", query=query[:60], error=str(exc))
            return []

    def run_chat(
        self, query: str
    ) -> Dict[str, Any]:
        """Call the EV RAG API chat endpoint."""
        try:
            import httpx
            response = httpx.post(
                f"{self.api_url}/api/v1/chat",
                json={"query": query},
                timeout=60,
            )
            response.raise_for_status()
            return response.json()
        except Exception as exc:
            logger.error("ragas_chat_failed", query=query[:60], error=str(exc))
            return {"answer": "", "sources": []}

    def compute_ragas_metrics(
        self,
        queries: List[str],
        answers: List[str],
        contexts: List[List[str]],
        ground_truths: List[str],
    ) -> Dict[str, float]:
        """Compute RAGAS metrics using the ragas library."""
        try:
            from ragas import evaluate
            from ragas.metrics import faithfulness, answer_relevancy, context_recall, context_precision
            from datasets import Dataset

            eval_dataset = Dataset.from_dict({
                "question": queries,
                "answer": answers,
                "contexts": contexts,
                "ground_truth": ground_truths,
            })

            result = evaluate(
                eval_dataset,
                metrics=[faithfulness, answer_relevancy, context_recall, context_precision],
            )

            return {
                "faithfulness": round(float(result["faithfulness"]), 4),
                "answer_relevancy": round(float(result["answer_relevancy"]), 4),
                "context_recall": round(float(result["context_recall"]), 4),
                "context_precision": round(float(result["context_precision"]), 4),
            }

        except ImportError:
            logger.warning("ragas_not_installed", hint="pip install ragas datasets")
            return self._compute_simple_metrics(queries, answers, ground_truths)

    def _compute_simple_metrics(
        self,
        queries: List[str],
        answers: List[str],
        ground_truths: List[str],
    ) -> Dict[str, float]:
        """Fallback simple metrics when ragas library is unavailable."""
        scores = []
        for answer, truth in zip(answers, ground_truths):
            truth_words = set(truth.lower().split())
            answer_words = set(answer.lower().split())
            overlap = len(truth_words & answer_words) / max(len(truth_words), 1)
            scores.append(overlap)
        avg_score = sum(scores) / max(len(scores), 1)
        return {
            "faithfulness": avg_score,
            "answer_relevancy": avg_score,
            "context_recall": avg_score,
            "context_precision": avg_score,
            "method": "simple_overlap",
        }

    def run_full_evaluation(self) -> Dict[str, Any]:
        """Run a full RAGAS evaluation over the EV golden dataset."""
        golden_set = self.load_golden_set()

        queries, answers, contexts, ground_truths = [], [], [], []
        per_query_results = []

        for item in golden_set:
            query = item["query"]
            ground_truth = item["ground_truth"]

            start = time.perf_counter()
            chat_result = self.run_chat(query)
            latency_ms = (time.perf_counter() - start) * 1000

            answer = chat_result.get("answer", "")
            retrieved_sources = chat_result.get("sources", [])
            context_texts = [s.get("text", "") for s in retrieved_sources[:5]]

            queries.append(query)
            answers.append(answer)
            contexts.append(context_texts)
            ground_truths.append(ground_truth)

            per_query_results.append({
                "id": item.get("id"),
                "query": query,
                "category": item.get("category"),
                "difficulty": item.get("difficulty"),
                "answer": answer,
                "latency_ms": round(latency_ms, 2),
                "sources_retrieved": len(retrieved_sources),
                "grounded": chat_result.get("grounded", False),
            })

        ragas_metrics = self.compute_ragas_metrics(queries, answers, contexts, ground_truths)

        results = {
            "evaluation_timestamp": datetime.utcnow().isoformat(),
            "total_queries": len(golden_set),
            "ragas_metrics": ragas_metrics,
            "per_query_results": per_query_results,
            "avg_latency_ms": sum(r["latency_ms"] for r in per_query_results) / max(len(per_query_results), 1),
            "grounded_rate": sum(1 for r in per_query_results if r["grounded"]) / max(len(per_query_results), 1),
        }

        # Save results
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        results_file = RESULTS_DIR / f"ev_ragas_eval_{timestamp}.json"
        with open(results_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)

        logger.info(
            "ragas_evaluation_complete",
            total=len(golden_set),
            faithfulness=ragas_metrics.get("faithfulness"),
            avg_latency_ms=round(results["avg_latency_ms"], 2),
        )

        return results


def run_evaluation():
    """Entry point for RAGAS evaluation."""
    print("Starting EV RAG RAGAS evaluation...")
    runner = EVRAGASRunner()
    results = runner.run_full_evaluation()
    print(f"Evaluation complete. Faithfulness: {results['ragas_metrics'].get('faithfulness', 'N/A')}")
    print(f"Results saved to evaluation/results/")
    return results


if __name__ == "__main__":
    run_evaluation()
