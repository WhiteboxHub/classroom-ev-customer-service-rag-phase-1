"""
embedding_tasks.py
Celery tasks for asynchronous embedding operations.
Handles: embedding backfill, cache warming, model hot-swap.
"""

from typing import Any, Dict, List

from app.core.logging import get_logger
from app.workers.celery_app import celery_app

logger = get_logger(__name__)


@celery_app.task(
    name="ev_rag.backfill_embeddings",
    bind=True,
    max_retries=3,
    default_retry_delay=30,
    queue="embedding",
)
def backfill_embeddings_task(self, document_ids: List[str]) -> Dict[str, Any]:
    """
    Re-embed chunks for documents that are missing vector representations.
    Triggered when: embedding model is upgraded, vectors are corrupted.
    """
    logger.info("backfill_task_started", count=len(document_ids))
    try:
        from app.embeddings.embedding_service import EmbeddingService
        from app.vectorstore.milvus_client import MilvusVectorStore

        embedding_service = EmbeddingService()
        vector_store = MilvusVectorStore()

        processed = 0
        for doc_id in document_ids:
            try:
                # Query existing chunks for this document
                chunks = vector_store.get_chunks_by_document_id(doc_id)
                if not chunks:
                    logger.warning("backfill_no_chunks", document_id=doc_id)
                    continue

                texts = [c["text"] for c in chunks]
                new_embeddings = embedding_service.embed_documents(texts)

                # Update vectors in Milvus
                vector_store.update_embeddings(doc_id, new_embeddings)
                processed += 1
                logger.info("backfill_chunk_done", document_id=doc_id)
            except Exception as chunk_exc:
                logger.warning("backfill_chunk_failed", document_id=doc_id, error=str(chunk_exc))

        result = {"requested": len(document_ids), "processed": processed}
        logger.info("backfill_task_complete", **result)
        return result
    except Exception as exc:
        logger.error("backfill_task_failed", error=str(exc))
        raise self.retry(exc=exc)


@celery_app.task(
    name="ev_rag.warm_embedding_cache",
    bind=True,
    queue="embedding",
)
def warm_embedding_cache_task(self, queries: List[str]) -> Dict[str, Any]:
    """
    Pre-compute and cache embeddings for high-frequency EV DTC queries.
    Reduces P99 latency for common troubleshooting queries.
    """
    logger.info("cache_warmup_task_started", queries=len(queries))
    try:
        from app.embeddings.embedding_service import EmbeddingService

        embedding_service = EmbeddingService()
        embeddings = embedding_service.embed_documents(queries)  # This caches them in Redis
        result = {"warmed": len(embeddings)}
        logger.info("cache_warmup_task_complete", **result)
        return result
    except Exception as exc:
        logger.error("cache_warmup_task_failed", error=str(exc))
        raise self.retry(exc=exc)
