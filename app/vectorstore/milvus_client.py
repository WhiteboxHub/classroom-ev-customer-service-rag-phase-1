"""
milvus_client.py
Enterprise Milvus vector database integration for the EV RAG Platform.
Features: HNSW indexing, metadata filtering, tenant isolation,
vehicle platform partitioning, DTC-aware schema, delete/sync operations.
Aligns with EV Study Guide Section 5.10 — Vector Store Architecture.
"""

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
    """
    Enterprise Milvus vector store for EV troubleshooting embeddings.
    Supports: HNSW indexing, metadata filtering, DTC/firmware/platform fields,
    tenant isolation, partition-based retrieval, document deletion, sync operations.
    """

    def __init__(self):
        self.collection_name = settings.milvus_collection
        self.dim = settings.embedding_dimension
        self._collection: Optional[Collection] = None
        self._connected = False

    # ──────────────────────────────────────────────────────────
    # Connection Management
    # ──────────────────────────────────────────────────────────

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
        """EV-specific Milvus collection schema with full metadata fields."""
        fields = [
            # Primary key
            FieldSchema(name="id", dtype=DataType.VARCHAR, is_primary=True, max_length=64),
            # Vector embedding
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=self.dim),
            # Core text
            FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535),
            # Document identification
            FieldSchema(name="document_id", dtype=DataType.VARCHAR, max_length=64),
            FieldSchema(name="source_file", dtype=DataType.VARCHAR, max_length=512),
            # EV domain metadata
            FieldSchema(name="vehicle_model", dtype=DataType.VARCHAR, max_length=128),
            FieldSchema(name="vehicle_platform", dtype=DataType.VARCHAR, max_length=64),
            FieldSchema(name="firmware_version", dtype=DataType.VARCHAR, max_length=64),
            FieldSchema(name="charging_type", dtype=DataType.VARCHAR, max_length=64),
            FieldSchema(name="charging_standard", dtype=DataType.VARCHAR, max_length=64),
            FieldSchema(name="diagnostic_category", dtype=DataType.VARCHAR, max_length=128),
            FieldSchema(name="dtc_code", dtype=DataType.VARCHAR, max_length=32),
            # Multi-tenancy
            FieldSchema(name="tenant_id", dtype=DataType.VARCHAR, max_length=64),
            # Structural metadata
            FieldSchema(name="section_hierarchy", dtype=DataType.VARCHAR, max_length=512),
            FieldSchema(name="page_number", dtype=DataType.INT64),
            FieldSchema(name="chunk_index", dtype=DataType.INT64),
            # Version tracking
            FieldSchema(name="doc_version", dtype=DataType.VARCHAR, max_length=32),
        ]
        return CollectionSchema(
            fields=fields,
            description="EV troubleshooting knowledge base — service manuals, DTCs, firmware, charging",
        )

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

    # ──────────────────────────────────────────────────────────
    # Write Operations
    # ──────────────────────────────────────────────────────────

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
    def insert_chunks(self, chunks: List[Document], embeddings: List[List[float]]) -> int:
        """Insert chunks with embeddings into Milvus."""
        self.connect()
        entities = []
        for chunk, emb in zip(chunks, embeddings):
            meta = chunk.metadata
            entities.append({
                "id": str(meta.get("chunk_id", meta.get("id", ""))),
                "embedding": emb,
                "text": chunk.page_content[:65000],
                "document_id": str(meta.get("document_id", "")),
                "source_file": str(meta.get("source_file", ""))[:512],
                "vehicle_model": str(meta.get("vehicle_model", "") or "")[:128],
                "vehicle_platform": str(meta.get("vehicle_platform", "") or "")[:64],
                "firmware_version": str(meta.get("firmware_version", "") or "")[:64],
                "charging_type": str(meta.get("charging_type", "") or "")[:64],
                "charging_standard": str(meta.get("charging_standard", "") or "")[:64],
                "diagnostic_category": str(meta.get("diagnostic_category", "") or "")[:128],
                "dtc_code": str(meta.get("dtc_code", "") or "")[:32],
                "tenant_id": str(meta.get("tenant_id", settings.default_tenant))[:64],
                "section_hierarchy": str(meta.get("section_hierarchy", "") or "")[:512],
                "page_number": int(meta.get("page_number", 0)),
                "chunk_index": int(meta.get("chunk_index", 0)),
                "doc_version": str(meta.get("doc_version", "") or "")[:32],
            })

        try:
            self.collection.insert(entities)
            self.collection.flush()
        except MilvusException as exc:
            raise VectorStoreError("Milvus insert failed", {"error": str(exc)}) from exc

        return len(chunks)

    # ──────────────────────────────────────────────────────────
    # Delete Operations
    # ──────────────────────────────────────────────────────────

    def delete_by_document_id(self, document_id: str) -> int:
        """Delete all chunks for a given document from Milvus."""
        self.connect()
        try:
            expr = f'document_id == "{document_id}"'
            result = self.collection.delete(expr)
            self.collection.flush()
            deleted = result.delete_count if hasattr(result, "delete_count") else 0
            logger.info("milvus_delete_by_doc", document_id=document_id, deleted=deleted)
            return deleted
        except MilvusException as exc:
            raise VectorStoreError(
                "Milvus delete failed", {"document_id": document_id, "error": str(exc)}
            ) from exc

    def delete_by_firmware_version(self, firmware_version: str) -> int:
        """Delete all chunks for a deprecated firmware version."""
        self.connect()
        try:
            expr = f'firmware_version == "{firmware_version}"'
            result = self.collection.delete(expr)
            self.collection.flush()
            deleted = result.delete_count if hasattr(result, "delete_count") else 0
            logger.info("milvus_delete_by_firmware", firmware_version=firmware_version, deleted=deleted)
            return deleted
        except MilvusException as exc:
            raise VectorStoreError("Milvus delete failed", {"error": str(exc)}) from exc

    # ──────────────────────────────────────────────────────────
    # Update Operations
    # ──────────────────────────────────────────────────────────

    def update_embeddings(self, document_id: str, new_embeddings: List[List[float]]) -> None:
        """
        Update embeddings for a document by delete + re-insert pattern.
        Called by backfill_embeddings script and embedding worker.
        """
        chunks = self.get_chunks_by_document_id(document_id)
        if not chunks or len(chunks) != len(new_embeddings):
            logger.warning(
                "update_embeddings_mismatch",
                document_id=document_id,
                chunks=len(chunks),
                embeddings=len(new_embeddings),
            )
            return

        self.delete_by_document_id(document_id)
        docs = [
            Document(page_content=c["text"], metadata=c.get("metadata", {}))
            for c in chunks
        ]
        self.insert_chunks(docs, new_embeddings)
        logger.info("update_embeddings_complete", document_id=document_id)

    # ──────────────────────────────────────────────────────────
    # Search Operations
    # ──────────────────────────────────────────────────────────

    def _build_filter_expr(self, metadata_filter: Optional[Dict[str, Any]]) -> Optional[str]:
        if not metadata_filter:
            return None
        clauses = []
        field_map = {
            "vehicle_model": "vehicle_model",
            "vehicle_platform": "vehicle_platform",
            "firmware_version": "firmware_version",
            "charging_type": "charging_type",
            "charging_standard": "charging_standard",
            "diagnostic_category": "diagnostic_category",
            "dtc_code": "dtc_code",
            "tenant_id": "tenant_id",
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
        tenant_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Semantic vector search with optional metadata filtering and tenant isolation."""
        self.connect()

        if tenant_id and settings.multi_tenant_enabled:
            if metadata_filter is None:
                metadata_filter = {}
            metadata_filter["tenant_id"] = tenant_id

        expr = self._build_filter_expr(metadata_filter)
        search_params = {"metric_type": settings.milvus_metric_type, "params": {"ef": 128}}

        output_fields = [
            "text", "document_id", "source_file",
            "vehicle_model", "vehicle_platform", "firmware_version",
            "charging_type", "charging_standard", "diagnostic_category",
            "dtc_code", "tenant_id", "chunk_index", "page_number",
            "section_hierarchy", "doc_version",
        ]

        try:
            results = self.collection.search(
                data=[query_embedding],
                anns_field="embedding",
                param=search_params,
                limit=top_k,
                expr=expr,
                output_fields=output_fields,
            )
        except MilvusException as exc:
            raise VectorStoreError("Milvus search failed", {"error": str(exc)}) from exc

        hits: List[Dict[str, Any]] = []
        for hit in results[0]:
            entity = hit.entity
            hits.append({
                "chunk_id": hit.id,
                "text": entity.get("text"),
                "score": float(hit.distance),
                "document_id": entity.get("document_id"),
                "source_file": entity.get("source_file"),
                "metadata": {
                    "vehicle_model": entity.get("vehicle_model"),
                    "vehicle_platform": entity.get("vehicle_platform"),
                    "firmware_version": entity.get("firmware_version"),
                    "charging_type": entity.get("charging_type"),
                    "charging_standard": entity.get("charging_standard"),
                    "diagnostic_category": entity.get("diagnostic_category"),
                    "dtc_code": entity.get("dtc_code"),
                    "tenant_id": entity.get("tenant_id"),
                    "chunk_index": entity.get("chunk_index"),
                    "page_number": entity.get("page_number"),
                    "section_hierarchy": entity.get("section_hierarchy"),
                    "doc_version": entity.get("doc_version"),
                },
            })
        return hits

    # ──────────────────────────────────────────────────────────
    # Query Operations
    # ──────────────────────────────────────────────────────────

    def get_chunks_by_document_id(self, document_id: str) -> List[Dict[str, Any]]:
        """Retrieve all chunks for a document by document_id."""
        self.connect()
        try:
            rows = self.collection.query(
                expr=f'document_id == "{document_id}"',
                output_fields=["id", "text", "chunk_index", "source_file"],
                limit=16384,
            )
            return [
                {
                    "chunk_id": r.get("id"),
                    "text": r.get("text", ""),
                    "chunk_index": r.get("chunk_index", 0),
                    "source_file": r.get("source_file", ""),
                    "metadata": {"document_id": document_id},
                }
                for r in rows
            ]
        except MilvusException:
            return []

    def list_documents(self) -> List[Dict[str, Any]]:
        """Return distinct indexed documents (grouped by document_id)."""
        self.connect()
        try:
            rows = self.collection.query(
                expr="document_id != ''",
                output_fields=["document_id", "source_file", "diagnostic_category", "firmware_version"],
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
                    "firmware_version": row.get("firmware_version"),
                    "chunk_count": 1,
                }
            elif doc_id:
                seen[doc_id]["chunk_count"] += 1
        return list(seen.values())

    def sync_metadata(self) -> Dict[str, Any]:
        """Return metadata summary for Milvus-Postgres sync validation."""
        self.connect()
        docs = self.list_documents()
        total_chunks = sum(d.get("chunk_count", 0) for d in docs)
        return {
            "total_documents": len(docs),
            "total_chunks": total_chunks,
            "collection": self.collection_name,
            "dimension": self.dim,
        }
