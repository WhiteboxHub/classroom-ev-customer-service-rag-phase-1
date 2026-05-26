"""Environment-based configuration for the EV RAG platform."""

from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # OpenAI
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini", alias="OPENAI_MODEL")
    openai_temperature: float = Field(default=0.1, alias="OPENAI_TEMPERATURE")

    # Milvus
    milvus_host: str = Field(default="localhost", alias="MILVUS_HOST")
    milvus_port: int = Field(default=19530, alias="MILVUS_PORT")
    milvus_collection: str = Field(default="ev_troubleshooting", alias="MILVUS_COLLECTION")
    milvus_index_type: str = Field(default="HNSW", alias="MILVUS_INDEX_TYPE")
    milvus_metric_type: str = Field(default="COSINE", alias="MILVUS_METRIC_TYPE")

    # Redis
    redis_host: str = Field(default="localhost", alias="REDIS_HOST")
    redis_port: int = Field(default=6379, alias="REDIS_PORT")
    redis_db: int = Field(default=0, alias="REDIS_DB")
    redis_password: str = Field(default="", alias="REDIS_PASSWORD")
    cache_ttl_seconds: int = Field(default=3600, alias="CACHE_TTL_SECONDS")
    cache_enabled: bool = Field(default=True, alias="CACHE_ENABLED")

    # Embeddings
    embedding_model: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2", alias="EMBEDDING_MODEL"
    )
    embedding_dimension: int = Field(default=384, alias="EMBEDDING_DIMENSION")
    reranker_model: str = Field(
        default="cross-encoder/ms-marco-MiniLM-L-6-v2", alias="RERANKER_MODEL"
    )

    # Chunking
    chunk_size: int = Field(default=800, alias="CHUNK_SIZE")
    chunk_overlap: int = Field(default=150, alias="CHUNK_OVERLAP")

    # Retrieval
    semantic_top_k: int = Field(default=10, alias="SEMANTIC_TOP_K")
    bm25_top_k: int = Field(default=10, alias="BM25_TOP_K")
    hybrid_top_k: int = Field(default=8, alias="HYBRID_TOP_K")
    rerank_top_k: int = Field(default=5, alias="RERANK_TOP_K")
    retrieval_score_threshold: float = Field(default=0.35, alias="RETRIEVAL_SCORE_THRESHOLD")

    # API
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    api_prefix: str = Field(default="/api/v1", alias="API_PREFIX")
    cors_origins: str = Field(default="*", alias="CORS_ORIGINS")

    # Paths
    data_dir: Path = Field(default=Path("./data"), alias="DATA_DIR")
    upload_dir: Path = Field(default=Path("./data/uploads"), alias="UPLOAD_DIR")
    bm25_index_path: Path = Field(default=Path("./data/bm25_index.json"), alias="BM25_INDEX_PATH")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    @property
    def cors_origin_list(self) -> List[str]:
        if self.cors_origins.strip() == "*":
            return ["*"]
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    def ensure_dirs(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.bm25_index_path.parent.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    s = Settings()
    s.ensure_dirs()
    return s


settings = get_settings()
