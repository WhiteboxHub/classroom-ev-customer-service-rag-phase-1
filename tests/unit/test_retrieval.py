"""
test_retrieval.py
Unit tests for the EV RAG retrieval pipeline.
Tests: hybrid retrieval, reranker, query processor.
"""

import pytest
from unittest.mock import MagicMock, patch


class TestQueryProcessor:
    """Tests for QueryProcessor."""

    def test_clean_query(self):
        from app.retrieval.query_processor import QueryProcessor
        qp = QueryProcessor()
        cleaned = qp.clean_query("  What does DTC P0A80 mean?  ")
        assert cleaned == "What does DTC P0A80 mean?"

    def test_query_not_empty(self):
        from app.retrieval.query_processor import QueryProcessor
        qp = QueryProcessor()
        with pytest.raises(Exception):
            qp.clean_query("   ")


class TestThresholdGuardIntegration:
    """Integration tests for retrieval threshold enforcement."""

    def test_fallback_response_content(self):
        from app.guardrails.threshold_guard import ThresholdGuard, FALLBACK_RESPONSE
        guard = ThresholdGuard(score_threshold=0.9)
        sources = [{"score": 0.1, "text": "low quality chunk"}]
        passes, reason, fallback = guard.validate(sources)
        assert not passes
        assert "Recommended actions" in fallback
        assert "DTC codes" in fallback or "firmware" in fallback or "service manuals" in fallback.lower()
