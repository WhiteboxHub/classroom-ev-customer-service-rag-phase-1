"""Semantic retrieval via Milvus + Sentence Transformer MiniLM."""

from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.core.logging import get_logger
from app.embeddings.embedding_service import EmbeddingService
from app.retrieval.query_processor import QueryProcessor
from app.vectorstore.milvus_client import MilvusVectorStore

logger = get_logger(__name__)


class SemanticRetriever:
    """Milvus-backed semantic similarity retrieval with metadata filtering."""

    def __init__(
        self,
        vector_store: Optional[MilvusVectorStore] = None,
        embedding_service: Optional[EmbeddingService] = None,
        query_processor: Optional[QueryProcessor] = None,
    ):
        self.vector_store = vector_store or MilvusVectorStore()
        self.embedding_service = embedding_service or EmbeddingService()
        self.query_processor = query_processor or QueryProcessor()

    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        metadata_filter: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        top_k = top_k or settings.semantic_top_k
        cleaned, intent_meta = self.query_processor.process(query)
        merged_filter = dict(metadata_filter or {})
        if intent_meta.get("diagnostic_category") and "diagnostic_category" not in merged_filter:
            merged_filter.setdefault("diagnostic_category", intent_meta["diagnostic_category"])

        instruction_query = self.query_processor.format_retrieval_instruction(cleaned)
        embedding = self.embedding_service.embed_query(instruction_query)
        hits = self.vector_store.search(embedding, top_k=top_k, metadata_filter=merged_filter)

        # Convert Milvus cosine distance to similarity score (higher = better)
        for hit in hits:
            hit["score"] = self._distance_to_similarity(hit["score"])
            hit["retrieval_type"] = "semantic"

        logger.info("semantic_retrieval_complete", hits=len(hits), query=cleaned[:80])
        return hits

    @staticmethod
    def _distance_to_similarity(distance: float) -> float:
        # Cosine distance in Milvus: 0 = identical; map to similarity
        return max(0.0, min(1.0, 1.0 - distance))
