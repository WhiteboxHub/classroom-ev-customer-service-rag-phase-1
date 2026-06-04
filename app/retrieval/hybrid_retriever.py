"""Hybrid retrieval: semantic + BM25 fusion with LangChain Ensemble pattern."""

from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.core.logging import get_logger
from app.retrieval.bm25_retriever import BM25Index
from app.retrieval.query_processor import QueryProcessor
from app.retrieval.semantic_retriever import SemanticRetriever

logger = get_logger(__name__)


class HybridRetriever:
    """Combines semantic and keyword retrieval with reciprocal rank fusion."""

    def __init__(
        self,
        semantic: Optional[SemanticRetriever] = None,
        bm25_index: Optional[BM25Index] = None,
        query_processor: Optional[QueryProcessor] = None,
    ):
        self.semantic = semantic or SemanticRetriever()
        self.bm25_index = bm25_index or BM25Index()
        self.query_processor = query_processor or QueryProcessor()

    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        metadata_filter: Optional[Dict[str, Any]] = None,
        use_hybrid: bool = True,
    ) -> List[Dict[str, Any]]:
        top_k = top_k or settings.hybrid_top_k
        cleaned, _ = self.query_processor.process(query)

        if not use_hybrid:
            return self.semantic.retrieve(cleaned, top_k=top_k, metadata_filter=metadata_filter)

        semantic_hits = self.semantic.retrieve(
            cleaned, top_k=settings.semantic_top_k, metadata_filter=metadata_filter
        )
        keyword_hits = self.bm25_index.search(cleaned, top_k=settings.bm25_top_k)
        for hit in keyword_hits:
            hit["retrieval_type"] = "bm25"
            # Normalize BM25 scores to 0-1 range
            max_score = max((h["score"] for h in keyword_hits), default=1.0) or 1.0
            hit["score"] = hit["score"] / max_score

        fused = self._reciprocal_rank_fusion(semantic_hits, keyword_hits)
        return fused[:top_k]

    def _reciprocal_rank_fusion(
        self,
        semantic_hits: List[Dict[str, Any]],
        keyword_hits: List[Dict[str, Any]],
        k: int = 60,
    ) -> List[Dict[str, Any]]:
        """RRF fusion used in study guide result fusion (5.15.5)."""
        scores: Dict[str, float] = {}
        store: Dict[str, Dict[str, Any]] = {}

        for rank, hit in enumerate(semantic_hits):
            cid = hit["chunk_id"]
            scores[cid] = scores.get(cid, 0) + 1.0 / (k + rank + 1)
            store[cid] = hit

        for rank, hit in enumerate(keyword_hits):
            cid = hit["chunk_id"]
            scores[cid] = scores.get(cid, 0) + 1.0 / (k + rank + 1)
            if cid not in store:
                store[cid] = hit

        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        results: List[Dict[str, Any]] = []
        for cid, rrf_score in ranked:
            item = dict(store[cid])
            item["score"] = rrf_score
            item["retrieval_type"] = "hybrid"
            results.append(item)

        logger.info(
            "hybrid_fusion_complete",
            semantic=len(semantic_hits),
            keyword=len(keyword_hits),
            fused=len(results),
        )
        return results
