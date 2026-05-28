"""
test_retrieval.py
Unit tests for the EV RAG retrieval pipeline.
Tests: hybrid retrieval, query processor, threshold enforcement.
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

    def test_multiple_sources_average(self):
        from app.guardrails.threshold_guard import ThresholdGuard
        guard = ThresholdGuard(score_threshold=0.3, min_sources=2)
        # Only 1 source but min_sources=2
        sources = [{"score": 0.9, "text": "great chunk"}]
        passes, reason, fallback = guard.validate(sources)
        assert not passes
        assert "insufficient_sources" in reason

    def test_passes_with_good_sources(self):
        from app.guardrails.threshold_guard import ThresholdGuard
        guard = ThresholdGuard(score_threshold=0.3, min_sources=1)
        sources = [
            {"score": 0.9, "text": "DTC P0A80 battery replacement"},
            {"score": 0.7, "text": "Battery SoH diagnostic procedure"},
        ]
        passes, reason, fallback = guard.validate(sources)
        assert passes
        assert reason == "passed"
        assert fallback is None


class TestHallucinationGuard:
    """Tests for the hallucination detection guard."""

    def test_no_sources_not_grounded(self):
        from app.guardrails.hallucination_guard import HallucinationGuard
        guard = HallucinationGuard()
        is_grounded, confidence, reason = guard.check("Some answer", [])
        assert not is_grounded
        assert reason == "no_retrieved_sources"

    def test_grounded_with_source_citations(self):
        from app.guardrails.hallucination_guard import HallucinationGuard
        guard = HallucinationGuard()
        answer = (
            "According to the documentation, DTC P0A80 indicates battery replacement "
            "is needed [Source 1]. The service manual states the SoH threshold is 70% [Source 2]."
        )
        sources = [
            {"text": "DTC P0A80 battery replacement"},
            {"text": "SoH threshold 70%"},
        ]
        is_grounded, confidence, reason = guard.check(answer, sources)
        assert is_grounded
        assert confidence > 0.0
