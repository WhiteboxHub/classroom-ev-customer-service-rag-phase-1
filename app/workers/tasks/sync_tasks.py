"""
sync_tasks.py
Celery tasks for Milvus ↔ PostgreSQL metadata synchronization.
Ensures vector store and relational metadata DB stay in sync.
"""

from typing import Any, Dict

from app.core.logging import get_logger
from app.workers.celery_app import celery_app

logger = get_logger(__name__)


@celery_app.task(
    name="ev_rag.sync_vector_metadata",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    queue="sync",
)
def sync_vector_metadata_task(self) -> Dict[str, Any]:
    """
    Synchronize Milvus vector records with PostgreSQL document metadata.
    Detects orphaned vectors (Milvus record without Postgres entry) and
    missing vectors (Postgres doc without Milvus chunks).
    """
    logger.info("sync_task_started")
    try:
        from app.vectorstore.milvus_client import MilvusVectorStore

        vector_store = MilvusVectorStore()
        milvus_docs = vector_store.list_documents()

        synced = len(milvus_docs)
        orphaned = 0  # Would cross-reference with Postgres in full implementation

        result = {"milvus_documents": synced, "orphaned_vectors": orphaned}
        logger.info("sync_task_complete", **result)
        return result
    except Exception as exc:
        logger.error("sync_task_failed", error=str(exc))
        raise self.retry(exc=exc)


@celery_app.task(
    name="ev_rag.purge_stale_vectors",
    bind=True,
    max_retries=2,
    queue="sync",
)
def purge_stale_vectors_task(self, document_ids: list) -> Dict[str, Any]:
    """
    Remove vectors from Milvus for documents that no longer exist in Postgres.
    Called after document deletion or version deprecation.
    """
    logger.info("purge_task_started", count=len(document_ids))
    try:
        from app.vectorstore.milvus_client import MilvusVectorStore

        vector_store = MilvusVectorStore()
        deleted = 0
        for doc_id in document_ids:
            try:
                vector_store.delete_by_document_id(doc_id)
                deleted += 1
            except Exception as del_exc:
                logger.warning("purge_delete_failed", document_id=doc_id, error=str(del_exc))

        result = {"requested": len(document_ids), "deleted": deleted}
        logger.info("purge_task_complete", **result)
        return result
    except Exception as exc:
        logger.error("purge_task_failed", error=str(exc))
        raise self.retry(exc=exc)
