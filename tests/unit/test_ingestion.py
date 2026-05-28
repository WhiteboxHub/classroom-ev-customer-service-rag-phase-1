"""
test_ingestion.py
Unit tests for the EV RAG ingestion pipeline.
Tests: PDF parsing, metadata extraction, chunking, preprocessor.
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from langchain_core.documents import Document


class TestDocumentPreprocessor:
    """Tests for DocumentPreprocessor."""

    def test_preprocess_removes_short_docs(self):
        from app.ingestion.preprocessor import DocumentPreprocessor
        preprocessor = DocumentPreprocessor()
        docs = [Document(page_content="Hi", metadata={})]
        result = preprocessor.preprocess(docs)
        assert result == []

    def test_preprocess_preserves_long_docs(self):
        from app.ingestion.preprocessor import DocumentPreprocessor
        preprocessor = DocumentPreprocessor()
        text = "EV battery diagnostic procedure. " * 20
        docs = [Document(page_content=text, metadata={"source_file": "test.md"})]
        result = preprocessor.preprocess(docs)
        assert len(result) == 1
        assert len(result[0].page_content) > 100


class TestMetadataExtractor:
    """Tests for EV metadata extraction."""

    def test_extract_dtc_code(self):
        from app.ingestion.metadata_extractor import MetadataExtractor
        extractor = MetadataExtractor()
        text = "DTC P0A80 indicates battery pack replacement is needed."
        meta = extractor.extract_from_text(text)
        assert meta.get("dtc_code") == "P0A80"

    def test_extract_firmware_version(self):
        from app.ingestion.metadata_extractor import MetadataExtractor
        extractor = MetadataExtractor()
        text = "Firmware 4.2.1 introduced improved thermal management."
        meta = extractor.extract_from_text(text)
        assert "4.2.1" in str(meta.get("firmware_version", ""))

    def test_extract_charging_type_ccs(self):
        from app.ingestion.metadata_extractor import MetadataExtractor
        extractor = MetadataExtractor()
        text = "CCS fast charging procedure for EV-3000."
        meta = extractor.extract_from_text(text)
        assert meta.get("charging_type") is not None

    def test_extract_category_from_filename_battery(self):
        from app.ingestion.metadata_extractor import MetadataExtractor
        extractor = MetadataExtractor()
        meta = extractor.extract_from_filename("battery_thermal_guide.md")
        assert meta.get("diagnostic_category") == "battery"

    def test_extract_category_from_filename_firmware(self):
        from app.ingestion.metadata_extractor import MetadataExtractor
        extractor = MetadataExtractor()
        meta = extractor.extract_from_filename("firmware_4_2_1_changelog.md")
        assert meta.get("diagnostic_category") == "firmware"

    def test_extract_category_from_filename_charging(self):
        from app.ingestion.metadata_extractor import MetadataExtractor
        extractor = MetadataExtractor()
        meta = extractor.extract_from_filename("ccs_charging_guide.md")
        assert meta.get("diagnostic_category") == "charging"


class TestChunkingPipeline:
    """Tests for ChunkingPipeline."""

    def test_chunking_preserves_metadata(self):
        from app.ingestion.chunker import ChunkingPipeline
        chunker = ChunkingPipeline()
        text = "Battery diagnostic procedure. " * 100  # Long enough to produce multiple chunks
        doc = Document(page_content=text, metadata={"source_file": "test.md", "document_id": "doc-001"})
        chunks = chunker.chunk_documents([doc])
        assert len(chunks) >= 1
        for chunk in chunks:
            assert chunk.metadata.get("source_file") == "test.md"
            assert "chunk_index" in chunk.metadata

    def test_chunking_assigns_sequential_index(self):
        from app.ingestion.chunker import ChunkingPipeline
        chunker = ChunkingPipeline()
        text = "EV battery diagnostic. " * 200
        doc = Document(page_content=text, metadata={"source_file": "test.md"})
        chunks = chunker.chunk_documents([doc])
        indices = [c.metadata["chunk_index"] for c in chunks]
        assert indices == list(range(len(chunks)))


class TestGuardrails:
    """Tests for the EV RAG guardrails."""

    def test_threshold_guard_no_sources(self):
        from app.guardrails.threshold_guard import ThresholdGuard
        guard = ThresholdGuard()
        passes, reason, fallback = guard.validate([])
        assert not passes
        assert reason == "no_sources"
        assert fallback is not None

    def test_threshold_guard_low_score(self):
        from app.guardrails.threshold_guard import ThresholdGuard
        guard = ThresholdGuard(score_threshold=0.5)
        sources = [{"score": 0.1, "text": "Some content"}]
        passes, reason, fallback = guard.validate(sources)
        assert not passes
        assert "low_confidence" in reason

    def test_threshold_guard_passes(self):
        from app.guardrails.threshold_guard import ThresholdGuard
        guard = ThresholdGuard(score_threshold=0.3)
        sources = [{"score": 0.8, "text": "Battery DTC P0A80 diagnostic content"}]
        passes, reason, fallback = guard.validate(sources)
        assert passes
        assert fallback is None

    def test_safety_filter_hv_disclaimer(self):
        from app.guardrails.safety_filter import SafetyFilter
        safety = SafetyFilter()
        answer = "To replace the battery pack, disconnect the high-voltage cables and remove the battery."
        filtered_answer, is_safe, action = safety.apply("how to replace battery", answer)
        assert is_safe
        assert "WARNING" in filtered_answer or "HIGH-VOLTAGE" in filtered_answer
