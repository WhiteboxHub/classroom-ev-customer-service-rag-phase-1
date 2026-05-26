"""Cross-encoder reranking with confidence threshold and BM25 fallback."""

from functools import lru_cache
from typing import Any, Dict, List, Optional

from sentence_transformers import CrossEncoder

from app.core.config import settings
from app.core.logging import get_logger
from app.retrieval.bm25_retriever import BM25Index

logger = get_logger(__name__)


@lru_cache(maxsize=1)
def _get_cross_encoder() -> CrossEncoder:
    return CrossEncoder(settings.reranker_model)


class Reranker:
    """Rerank fused retrieval results before LLM generation."""

    def __init__(self, bm25_index: Optional[BM25Index] = None):
        self.bm25_index = bm25_index or BM25Index()
        self._model: Optional[CrossEncoder] = None

    @property
    def model(self) -> CrossEncoder:
        if self._model is None:
            self._model = _get_cross_encoder()
        return self._model

    def rerank(
        self,
        query: str,
        candidates: List[Dict[str, Any]],
        top_k: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        top_k = top_k or settings.rerank_top_k
        if not candidates:
            return self._fallback_keyword(query, top_k)

        pairs = [(query, c["text"]) for c in candidates]
        scores = self.model.predict(pairs)

        reranked: List[Dict[str, Any]] = []
        for candidate, score in zip(candidates, scores):
            item = dict(candidate)
            item["rerank_score"] = float(score)
            item["score"] = float(score)
            reranked.append(item)

        reranked.sort(key=lambda x: x["rerank_score"], reverse=True)
        filtered = [
            r
            for r in reranked
            if r["rerank_score"] >= settings.retrieval_score_threshold
        ]

        # Fallback when semantic confidence is low (study guide 5.16.2)
        if len(filtered) < 2:
            logger.warning("rerank_low_confidence_fallback", query=query[:60])
            fallback = self._fallback_keyword(query, top_k)
            seen = {r["chunk_id"] for r in filtered}
            for item in fallback:
                if item["chunk_id"] not in seen:
                    filtered.append(item)

        return filtered[:top_k]

    def _fallback_keyword(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        hits = self.bm25_index.search(query, top_k=top_k)
        for hit in hits:
            hit["retrieval_type"] = "bm25_fallback"
        return hits
