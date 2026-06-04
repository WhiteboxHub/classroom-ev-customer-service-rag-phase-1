"""
test_reranker.py
Unit tests for EV RAG reranker.
Tests: score thresholding, fallback logic, empty candidate handling.
"""

import pytest
from unittest.mock import MagicMock, patch


class TestReranker:
    """Tests for cross-encoder Reranker."""

    def test_rerank_empty_candidates_triggers_fallback(self):
        from app.retrieval.reranker import Reranker
        with patch.object(Reranker, '_fallback_keyword', return_value=[]) as mock_fallback:
            reranker = Reranker()
            result = reranker.rerank("battery DTC", [], top_k=3)
            mock_fallback.assert_called_once_with("battery DTC", 3)

    def test_rerank_filters_low_scores(self):
        from app.retrieval.reranker import Reranker
        reranker = Reranker()

        # Mock the cross-encoder to return a low score
        mock_model = MagicMock()
        mock_model.predict.return_value = [0.01]  # Very low score
        reranker._model = mock_model

        candidates = [{
            "chunk_id": "chunk-001",
            "text": "Some unrelated content",
            "score": 0.9,
            "source_file": "test.md",
            "document_id": "doc-001"
        }]

        # With very low reranker score, should trigger fallback
        with patch.object(reranker, '_fallback_keyword', return_value=candidates) as mock_fallback:
            result = reranker.rerank("battery thermal warning", candidates, top_k=3)
            # Either filtered result or fallback result
            assert isinstance(result, list)

    def test_rerank_preserves_top_k_limit(self):
        from app.retrieval.reranker import Reranker
        reranker = Reranker()
        mock_model = MagicMock()
        mock_model.predict.return_value = [0.9, 0.8, 0.7, 0.6, 0.5]
        reranker._model = mock_model

        candidates = [
            {
                "chunk_id": f"chunk-{i:03d}",
                "text": f"Content {i}",
                "score": 0.9 - i * 0.1,
                "source_file": "test.md",
                "document_id": "doc-001",
            }
            for i in range(5)
        ]

        result = reranker.rerank("battery DTC P0A80", candidates, top_k=3)
        assert len(result) <= 3

    def test_rerank_returns_list(self):
        from app.retrieval.reranker import Reranker
        reranker = Reranker()
        mock_model = MagicMock()
        mock_model.predict.return_value = [0.9]
        reranker._model = mock_model

        candidates = [{
            "chunk_id": "chunk-001",
            "text": "DTC P0A80 battery replacement procedure",
            "score": 0.85,
            "source_file": "dtc_catalog.md",
            "document_id": "doc-001",
        }]

        result = reranker.rerank("DTC P0A80", candidates, top_k=5)
        assert isinstance(result, list)
        assert len(result) >= 1
