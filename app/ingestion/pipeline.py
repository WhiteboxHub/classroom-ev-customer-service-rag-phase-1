"""Enterprise document ingestion pipeline orchestration."""

from pathlib import Path
from typing import Any, Dict, List, Optional

from langchain_community.document_loaders import TextLoader
from langchain_core.documents import Document

from app.core.config import settings
from app.core.exceptions import IngestionError
from app.core.logging import get_logger
from app.embeddings.embedding_service import EmbeddingService
from app.ingestion.chunker import ChunkingPipeline
from app.ingestion.metadata_extractor import MetadataExtractor
from app.ingestion.pdf_parser import PDFParser
from app.ingestion.preprocessor import DocumentPreprocessor
from app.retrieval.bm25_retriever import BM25Index
from app.utils.helpers import generate_id
from app.vectorstore.milvus_client import MilvusVectorStore

logger = get_logger(__name__)


class IngestionPipeline:
    """End-to-end ingestion: parse → preprocess → metadata → chunk → embed → index."""

    def __init__(
        self,
        vector_store: Optional[MilvusVectorStore] = None,
        embedding_service: Optional[EmbeddingService] = None,
        bm25_index: Optional[BM25Index] = None,
    ):
        self.pdf_parser = PDFParser()
        self.preprocessor = DocumentPreprocessor()
        self.metadata_extractor = MetadataExtractor()
        self.chunker = ChunkingPipeline()
        self.embedding_service = embedding_service or EmbeddingService()
        self.vector_store = vector_store or MilvusVectorStore()
        self.bm25_index = bm25_index or BM25Index()

    def ingest_file(
        self,
        file_path: Path,
        metadata_overrides: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        file_path = Path(file_path)
        suffix = file_path.suffix.lower()
        document_id = generate_id("doc")

        if suffix == ".pdf":
            raw_docs = self.pdf_parser.parse(file_path)
        elif suffix in {".txt", ".md"}:
            loader = TextLoader(str(file_path), encoding="utf-8")
            raw_docs = loader.load()
            for doc in raw_docs:
                doc.metadata["source_file"] = file_path.name
                doc.metadata["file_type"] = suffix.lstrip(".")
        else:
            raise IngestionError(f"Unsupported file type: {suffix}")

        cleaned = self.preprocessor.preprocess(raw_docs)
        if not cleaned:
            raise IngestionError("No usable content after preprocessing", {"file": str(file_path)})

        overrides = metadata_overrides or {}
        overrides.setdefault("document_id", document_id)
        enriched = self.metadata_extractor.enrich_documents(cleaned, overrides)
        chunks = self.chunker.chunk_documents(enriched)

        for chunk in chunks:
            chunk.metadata["document_id"] = document_id
            chunk.metadata["chunk_id"] = generate_id("chunk")

        texts = [c.page_content for c in chunks]
        embeddings = self.embedding_service.embed_documents(texts)
        self.vector_store.insert_chunks(chunks, embeddings)
        self.bm25_index.add_chunks(chunks)

        logger.info(
            "ingestion_complete",
            document_id=document_id,
            file=file_path.name,
            chunks=len(chunks),
        )
        return {
            "document_id": document_id,
            "source_file": file_path.name,
            "chunks_indexed": len(chunks),
        }

    def ingest_directory(
        self,
        directory: Path,
        metadata_overrides: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        directory = Path(directory)
        if not directory.exists():
            raise IngestionError(f"Directory not found: {directory}")

        results: List[Dict[str, Any]] = []
        patterns = ("*.pdf", "*.md", "*.txt")
        files: List[Path] = []
        for pattern in patterns:
            files.extend(directory.rglob(pattern))

        if not files:
            raise IngestionError(f"No ingestible files in {directory}")

        for file_path in sorted(files):
            results.append(self.ingest_file(file_path, metadata_overrides))

        return results

    def ingest_path(
        self,
        source_path: str,
        metadata_overrides: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        path = Path(source_path)
        if not path.is_absolute():
            path = settings.data_dir / path

        if path.is_dir():
            return self.ingest_directory(path, metadata_overrides)
        if path.is_file():
            return [self.ingest_file(path, metadata_overrides)]
        raise IngestionError(f"Path not found: {path}")
