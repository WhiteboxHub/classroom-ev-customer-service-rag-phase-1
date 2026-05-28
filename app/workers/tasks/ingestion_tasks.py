"""
ingestion_tasks.py
Celery tasks for asynchronous EV document ingestion.
Handles: PDF ingestion, HTML crawl ingestion, S3 batch ingestion.
"""

import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.core.logging import get_logger
from app.workers.celery_app import celery_app

logger = get_logger(__name__)


@celery_app.task(
    name="ev_rag.ingest_document",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    queue="ingestion",
)
def ingest_document_task(
    self,
    file_path: str,
    metadata_overrides: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Async Celery task: ingest a single EV document from file path.
    Automatically retries on transient Milvus / network errors.
    """
    logger.info("ingestion_task_started", file=file_path, task_id=self.request.id)
    try:
        from app.ingestion.pipeline import IngestionPipeline

        pipeline = IngestionPipeline()
        result = pipeline.ingest_file(Path(file_path), metadata_overrides)
        logger.info("ingestion_task_complete", file=file_path, result=result)
        return result
    except Exception as exc:
        logger.error("ingestion_task_failed", file=file_path, error=str(exc))
        raise self.retry(exc=exc)


@celery_app.task(
    name="ev_rag.ingest_directory",
    bind=True,
    max_retries=2,
    default_retry_delay=120,
    queue="ingestion",
)
def ingest_directory_task(
    self,
    directory_path: str,
    metadata_overrides: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """
    Async Celery task: batch-ingest all EV documents in a directory.
    """
    logger.info("ingest_directory_task_started", directory=directory_path)
    try:
        from app.ingestion.pipeline import IngestionPipeline

        pipeline = IngestionPipeline()
        results = pipeline.ingest_directory(Path(directory_path), metadata_overrides)
        logger.info("ingest_directory_task_complete", directory=directory_path, count=len(results))
        return results
    except Exception as exc:
        logger.error("ingest_directory_task_failed", directory=directory_path, error=str(exc))
        raise self.retry(exc=exc)


@celery_app.task(
    name="ev_rag.ingest_s3_category",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    queue="ingestion",
)
def ingest_s3_category_task(self, category: str) -> Dict[str, Any]:
    """
    Async Celery task: ingest all EV docs from an S3 category bucket prefix.
    Categories: service_manuals, firmware_updates, dtc_codes, charging_docs, etc.
    """
    logger.info("s3_ingest_task_started", category=category)
    try:
        from app.ingestion.loaders.s3_loader import S3DocumentLoader
        from app.ingestion.pipeline import IngestionPipeline
        from app.ingestion.chunker import ChunkingPipeline
        from app.ingestion.metadata_extractor import MetadataExtractor
        from app.embeddings.embedding_service import EmbeddingService
        from app.vectorstore.milvus_client import MilvusVectorStore
        from app.retrieval.bm25_retriever import BM25Index
        from app.utils.helpers import generate_id

        loader = S3DocumentLoader()
        docs = loader.load_ev_category(category)

        extractor = MetadataExtractor()
        chunker = ChunkingPipeline()
        embedding_service = EmbeddingService()
        vector_store = MilvusVectorStore()
        bm25_index = BM25Index()

        total_chunks = 0
        for doc in docs:
            doc_id = generate_id("doc")
            enriched = extractor.enrich_documents([doc], {"document_id": doc_id, "s3_category": category})
            chunks = chunker.chunk_documents(enriched)
            texts = [c.page_content for c in chunks]
            embeddings = embedding_service.embed_documents(texts)
            vector_store.insert_chunks(chunks, embeddings)
            bm25_index.add_chunks(chunks)
            total_chunks += len(chunks)

        result = {"category": category, "documents": len(docs), "chunks": total_chunks}
        logger.info("s3_ingest_task_complete", **result)
        return result
    except Exception as exc:
        logger.error("s3_ingest_task_failed", category=category, error=str(exc))
        raise self.retry(exc=exc)
