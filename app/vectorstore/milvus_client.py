"""Milvus vector database integration with HNSW indexing and metadata filtering."""

from typing import Any, Dict, List, Optional

from langchain_core.documents import Document
from pymilvus import (
    Collection,
    CollectionSchema,
    DataType,
    FieldSchema,
    connections,
    utility,
)
from pymilvus.exceptions import MilvusException
from tenacity import retry, stop_after_attempt, wait_fixed

from app.core.config import settings
from app.core.exceptions import VectorStoreError
from app.core.logging import get_logger

logger = get_logger(__name__)


class MilvusVectorStore:
    """Enterprise Milvus layer for EV troubleshooting embeddings."""

    def __init__(self):
        self.collection_name = settings.milvus_collection
        self.dim = settings.embedding_dimension
        self._collection: Optional[Collection] = None
        self._connected = False

    def connect(self) -> None:
        if self._connected:
            return
        try:
            connections.connect(
                alias="default",
                host=settings.milvus_host,
                port=str(settings.milvus_port),
            )
            self._connected = True
            self._ensure_collection()
            logger.info("milvus_connected", host=settings.milvus_host)
        except Exception as exc:
            raise VectorStoreError(
                "Failed to connect to Milvus",
                {"host": settings.milvus_host, "error": str(exc)},
            ) from exc

    def _schema(self) -> CollectionSchema:
        fields = [
            FieldSchema(name="id", dtype=DataType.VARCHAR, is_primary=True, max_length=64),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=self.dim),
            FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535),
            FieldSchema(name="document_id", dtype=DataType.VARCHAR, max_length=64),
            FieldSchema(name="source_file", dtype=DataType.VARCHAR, max_length=512),
            FieldSchema(name="vehicle_model", dtype=DataType.VARCHAR, max_length=128),
            FieldSchema(name="firmware_version", dtype=DataType.VARCHAR, max_length=64),
            FieldSchema(name="charging_type", dtype=DataType.VARCHAR, max_length=64),
            FieldSchema(name="diagnostic_category", dtype=DataType.VARCHAR, max_length=128),
            FieldSchema(name="chunk_index", dtype=DataType.INT64),
        ]
        return CollectionSchema(fields=fields, description="EV troubleshooting knowledge")

    def _ensure_collection(self) -> None:
        if utility.has_collection(self.collection_name):
            self._collection = Collection(self.collection_name)
            self._collection.load()
            return

        schema = self._schema()
        self._collection = Collection(name=self.collection_name, schema=schema)
        index_params = {
            "index_type": settings.milvus_index_type,
            "metric_type": settings.milvus_metric_type,
            "params": {"M": 16, "efConstruction": 200},
        }
        self._collection.create_index(field_name="embedding", index_params=index_params)
        self._collection.load()
        logger.info("milvus_collection_created", name=self.collection_name)

    @property
    def collection(self) -> Collection:
        if not self._connected:
            self.connect()
        assert self._collection is not None
        return self._collection

    def health_check(self) -> str:
        try:
            self.connect()
            return "healthy"
        except Exception:
            return "unavailable"

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
    def insert_chunks(self, chunks: List[Document], embeddings: List[List[float]]) -> int:
        self.connect()
        entities = []
        for chunk, emb in zip(chunks, embeddings):
            meta = chunk.metadata
            entities.append(
                {
                    "id": str(meta.get("chunk_id", meta.get("id", ""))),
                    "embedding": emb,
                    "text": chunk.page_content[:65000],
                    "document_id": str(meta.get("document_id", "")),
                    "source_file": str(meta.get("source_file", "")),
                    "vehicle_model": str(meta.get("vehicle_model", "") or ""),
                    "firmware_version": str(meta.get("firmware_version", "") or ""),
                    "charging_type": str(meta.get("charging_type", "") or ""),
                    "diagnostic_category": str(meta.get("diagnostic_category", "") or ""),
                    "chunk_index": int(meta.get("chunk_index", 0)),
                }
            )

        try:
            self.collection.insert(entities)
            self.collection.flush()
        except MilvusException as exc:
            raise VectorStoreError("Milvus insert failed", {"error": str(exc)}) from exc

        return len(chunks)

    def _build_filter_expr(self, metadata_filter: Optional[Dict[str, Any]]) -> Optional[str]:
        if not metadata_filter:
            return None
        clauses = []
        field_map = {
            "vehicle_model": "vehicle_model",
            "firmware_version": "firmware_version",
            "charging_type": "charging_type",
            "diagnostic_category": "diagnostic_category",
            "document_source": "source_file",
        }
        for key, field in field_map.items():
            value = metadata_filter.get(key)
            if value:
                clauses.append(f'{field} == "{value}"')
        return " and ".join(clauses) if clauses else None

    def search(
        self,
        query_embedding: List[float],
        top_k: int = 10,
        metadata_filter: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        self.connect()
        expr = self._build_filter_expr(metadata_filter)
        search_params = {"metric_type": settings.milvus_metric_type, "params": {"ef": 128}}

        try:
            results = self.collection.search(
                data=[query_embedding],
                anns_field="embedding",
                param=search_params,
                limit=top_k,
                expr=expr,
                output_fields=[
                    "text",
                    "document_id",
                    "source_file",
                    "vehicle_model",
                    "firmware_version",
                    "charging_type",
                    "diagnostic_category",
                    "chunk_index",
                ],
            )
        except MilvusException as exc:
            raise VectorStoreError("Milvus search failed", {"error": str(exc)}) from exc

        hits: List[Dict[str, Any]] = []
        for hit in results[0]:
            entity = hit.entity
            hits.append(
                {
                    "chunk_id": hit.id,
                    "text": entity.get("text"),
                    "score": float(hit.distance),
                    "document_id": entity.get("document_id"),
                    "source_file": entity.get("source_file"),
                    "metadata": {
                        "vehicle_model": entity.get("vehicle_model"),
                        "firmware_version": entity.get("firmware_version"),
                        "charging_type": entity.get("charging_type"),
                        "diagnostic_category": entity.get("diagnostic_category"),
                        "chunk_index": entity.get("chunk_index"),
                    },
                }
            )
        return hits

    def list_documents(self) -> List[Dict[str, Any]]:
        """Return distinct indexed documents (approximate via query)."""
        self.connect()
        try:
            rows = self.collection.query(
                expr="document_id != ''",
                output_fields=["document_id", "source_file", "diagnostic_category"],
                limit=16384,
            )
        except MilvusException:
            return []

        seen: Dict[str, Dict[str, Any]] = {}
        for row in rows:
            doc_id = row.get("document_id")
            if doc_id and doc_id not in seen:
                seen[doc_id] = {
                    "document_id": doc_id,
                    "source_file": row.get("source_file", ""),
                    "diagnostic_category": row.get("diagnostic_category"),
                    "chunk_count": 1,
                }
            elif doc_id:
                seen[doc_id]["chunk_count"] += 1
        return list(seen.values())
