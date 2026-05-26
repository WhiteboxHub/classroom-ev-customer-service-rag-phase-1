"""FastAPI dependency injection for shared services."""

from functools import lru_cache

from app.cache.redis_cache import RedisCache
from app.ingestion.pipeline import IngestionPipeline
from app.retrieval.rag_service import RAGService
from app.vectorstore.milvus_client import MilvusVectorStore


@lru_cache(maxsize=1)
def get_vector_store() -> MilvusVectorStore:
    store = MilvusVectorStore()
    store.connect()
    return store


@lru_cache(maxsize=1)
def get_ingestion_pipeline() -> IngestionPipeline:
    return IngestionPipeline(vector_store=get_vector_store())


@lru_cache(maxsize=1)
def get_rag_service() -> RAGService:
    return RAGService()


@lru_cache(maxsize=1)
def get_cache() -> RedisCache:
    return RedisCache()
