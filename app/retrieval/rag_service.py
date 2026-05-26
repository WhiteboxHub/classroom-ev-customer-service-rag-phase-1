"""Central RAG orchestration service tying retrieval, cache, and generation."""

import time
from typing import Any, Dict, List, Optional, Tuple

from app.api.schemas.responses import ChatMessage, SourceChunk
from app.cache.redis_cache import RedisCache
from app.core.config import settings
from app.core.logging import get_logger
from app.generation.rag_chain import EVRAGChain
from app.memory.conversation_memory import ConversationMemoryManager
from app.observability.metrics import metrics_collector
from app.retrieval.hybrid_retriever import HybridRetriever
from app.retrieval.reranker import Reranker
from app.utils.helpers import generate_id, utc_now_iso

logger = get_logger(__name__)


class RAGService:
    """Enterprise orchestration layer for retrieval and grounded generation."""

    def __init__(
        self,
        hybrid_retriever: Optional[HybridRetriever] = None,
        reranker: Optional[Reranker] = None,
        rag_chain: Optional[EVRAGChain] = None,
        cache: Optional[RedisCache] = None,
        memory: Optional[ConversationMemoryManager] = None,
    ):
        self.hybrid_retriever = hybrid_retriever or HybridRetriever()
        self.reranker = reranker or Reranker()
        self.rag_chain = rag_chain or EVRAGChain(memory_manager=memory)
        self.cache = cache or RedisCache()
        self.memory = memory or ConversationMemoryManager()

    def _to_source_chunks(self, hits: List[Dict[str, Any]]) -> List[SourceChunk]:
        return [
            SourceChunk(
                chunk_id=str(h.get("chunk_id", "")),
                text=h.get("text", ""),
                score=float(h.get("score", 0)),
                source_file=h.get("source_file", ""),
                document_id=h.get("document_id", ""),
                metadata=h.get("metadata", {}),
            )
            for h in hits
        ]

    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        use_hybrid: bool = True,
        use_rerank: bool = True,
        metadata_filter: Optional[Dict[str, Any]] = None,
    ) -> Tuple[List[SourceChunk], float, str]:
        cache_key = f"{query}|{top_k}|{use_hybrid}|{use_rerank}|{metadata_filter}"
        cached = self.cache.get("retrieval", cache_key)
        if cached:
            return (
                [SourceChunk(**s) for s in cached["sources"]],
                cached["latency_ms"],
                cached["mode"],
            )

        start = time.perf_counter()
        with metrics_collector.track("retrieval"):
            hits = self.hybrid_retriever.retrieve(
                query,
                top_k=top_k,
                metadata_filter=metadata_filter,
                use_hybrid=use_hybrid,
            )
            if use_rerank and hits:
                hits = self.reranker.rerank(query, hits, top_k=top_k or settings.rerank_top_k)

        latency_ms = (time.perf_counter() - start) * 1000
        mode = "hybrid+rerank" if use_hybrid and use_rerank else "semantic"
        sources = self._to_source_chunks(hits)

        self.cache.set(
            "retrieval",
            cache_key,
            {"sources": [s.model_dump() for s in sources], "latency_ms": latency_ms, "mode": mode},
        )
        return sources, latency_ms, mode

    def chat(
        self,
        query: str,
        session_id: Optional[str] = None,
        top_k: Optional[int] = None,
        use_hybrid: bool = True,
        use_rerank: bool = True,
        metadata_filter: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        session_id = self.memory.get_or_create_session(session_id)

        response_cache_key = f"{session_id}|{query}|{top_k}|{use_hybrid}"
        cached = self.cache.get("chat", response_cache_key)
        if cached:
            return cached

        sources, retrieval_latency_ms, retrieval_mode = self.retrieve(
            query,
            top_k=top_k,
            use_hybrid=use_hybrid,
            use_rerank=use_rerank,
            metadata_filter=metadata_filter,
        )
        hits_dict = [s.model_dump() for s in sources]

        start = time.perf_counter()
        with metrics_collector.track("generation"):
            answer, citations, grounded = self.rag_chain.generate(
                query, hits_dict, session_id=session_id
            )
        gen_latency = (time.perf_counter() - start) * 1000

        result = {
            "session_id": session_id,
            "answer": answer,
            "sources": hits_dict,
            "citations": citations,
            "latency_ms": retrieval_latency_ms + gen_latency,
            "retrieval_latency_ms": retrieval_latency_ms,
            "generation_latency_ms": gen_latency,
            "retrieval_mode": retrieval_mode,
            "grounded": grounded,
            "history": self.memory.get_messages(session_id),
            "timestamp": utc_now_iso(),
        }

        self.cache.set("chat", response_cache_key, result, ttl=settings.cache_ttl_seconds)
        return result
