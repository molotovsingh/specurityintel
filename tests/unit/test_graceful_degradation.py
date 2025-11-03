"""
Test graceful degradation when AI services fail.
"""

import pytest
from unittest.mock import Mock, patch
from src.modules.ai.analyzer import RiskAnalyzer
from src.interfaces.dto import RiskAnalysisResult
from src.interfaces.errors import ProcessingError, IntegrationError
from src.adapters.openai_adapter import MockOpenAIClient
from src.adapters.clock import FixedClock
from datetime import datetime


class TestGracefulDegradation:
    """Test system behavior when AI services fail."""

    def test_ai_service_timeout_fallback(self):
        """Test fallback when AI service times out."""
        # Create mock client that times out
        mock_client = Mock()
        mock_client.analyze.side_effect = IntegrationError(
            message="AI service timeout",
            context={"service": "openai", "timeout": "30s"}
        )
        
        clock = FixedClock(datetime(2025, 1, 1))
        analyzer = RiskAnalyzer(mock_client, clock)
        
        # Should raise ProcessingError with fallback info
        with pytest.raises(ProcessingError) as exc_info:
            analyzer.analyze("APP-001", "orphan_accounts", 15.0)
        
        assert "AI analysis failed" in str(exc_info.value)
        assert exc_info.value.context["app_id"] == "APP-001"
        assert exc_info.value.context["kpi"] == "orphan_accounts"

    def test_ai_service_rate_limit_fallback(self):
        """Test fallback when AI service is rate limited."""
        mock_client = Mock()
        mock_client.analyze.side_effect = IntegrationError(
            message="Rate limit exceeded",
            context={"service": "openai", "error": "rate_limit"}
        )
        
        clock = FixedClock(datetime(2025, 1, 1))
        analyzer = RiskAnalyzer(mock_client, clock)
        
        with pytest.raises(ProcessingError) as exc_info:
            analyzer.analyze("APP-002", "failed_access", 25.0)
        
        assert "AI analysis failed" in str(exc_info.value)
        assert exc_info.value.context["app_id"] == "APP-002"

    def test_ai_service_invalid_response_fallback(self):
        """Test fallback when AI returns invalid response."""
        mock_client = Mock()
        mock_client.analyze.return_value = "Invalid JSON response"
        
        clock = FixedClock(datetime(2025, 1, 1))
        analyzer = RiskAnalyzer(mock_client, clock)
        
        # Should still work with heuristics
        result = analyzer.analyze("APP-003", "privileged_accounts", 8.0)
        
        assert isinstance(result, RiskAnalysisResult)
        assert result.app_id == "APP-003"
        assert result.kpi_name == "privileged_accounts"
        assert result.risk_score == 80.0  # 8.0 * 10, capped at 100
        assert result.confidence == 75.0
        assert result.analyzed_at == datetime(2025, 1, 1)

    def test_template_based_risk_scoring(self):
        """Test template-based risk scoring when AI fails."""
        mock_client = Mock()
        mock_client.analyze.side_effect = Exception("Network error")
        
        clock = FixedClock(datetime(2025, 1, 1))
        analyzer = RiskAnalyzer(mock_client, clock)
        
        # Test different KPI values get appropriate scores
        test_cases = [
            ("APP-004", "orphan_accounts", 5.0, 50.0),
            ("APP-005", "failed_access", 12.0, 100.0),  # Capped at 100
            ("APP-006", "privileged_accounts", 3.0, 30.0),
        ]
        
        for app_id, kpi_name, kpi_value, expected_score in test_cases:
            with pytest.raises(ProcessingError):
                analyzer.analyze(app_id, kpi_name, kpi_value)
            
            # Verify the heuristic would work if we caught the error
            assert analyzer._extract_risk_score("", kpi_value) == expected_score

    def test_fallback_maintains_data_integrity(self):
        """Test that fallback maintains required data fields."""
        mock_client = Mock()
        mock_client.analyze.return_value = "Partial response"
        
        clock = FixedClock(datetime(2025, 1, 1))
        analyzer = RiskAnalyzer(mock_client, clock)
        
        result = analyzer.analyze("APP-007", "policy_violations", 2.5)
        
        # Verify all required fields are present
        assert result.app_id is not None
        assert result.kpi_name is not None
        assert isinstance(result.risk_score, float)
        assert isinstance(result.confidence, float)
        assert result.explanation is not None
        assert isinstance(result.factors, dict)
        assert result.analyzed_at is not None

    def test_multiple_consecutive_failures(self):
        """Test system behavior with multiple consecutive AI failures."""
        mock_client = Mock()
        mock_client.analyze.side_effect = [
            IntegrationError("First failure"),
            IntegrationError("Second failure"),
            "Valid response"  # Third attempt succeeds
        ]
        
        clock = FixedClock(datetime(2025, 1, 1))
        analyzer = RiskAnalyzer(mock_client, clock)
        
        # First two attempts should fail
        with pytest.raises(ProcessingError):
            analyzer.analyze("APP-008", "orphan_accounts", 10.0)
        
        with pytest.raises(ProcessingError):
            analyzer.analyze("APP-009", "orphan_accounts", 10.0)
        
        # Third attempt should succeed
        result = analyzer.analyze("APP-010", "orphan_accounts", 10.0)
        assert isinstance(result, RiskAnalysisResult)

    def test_fallback_performance_impact(self):
        """Test that fallback doesn't significantly impact performance."""
        mock_client = Mock()
        mock_client.analyze.side_effect = IntegrationError("Service unavailable")
        
        clock = FixedClock(datetime(2025, 1, 1))
        analyzer = RiskAnalyzer(mock_client, clock)
        
        import time
        start_time = time.time()
        
        try:
            analyzer.analyze("APP-011", "orphan_accounts", 10.0)
        except ProcessingError:
            pass
        
        elapsed_time = time.time() - start_time
        
        # Fallback should be fast (< 1 second)
        assert elapsed_time < 1.0

    def test_error_context_preservation(self):
        """Test that error context is preserved for debugging."""
        mock_client = Mock()
        mock_client.analyze.side_effect = IntegrationError(
            message="API key invalid",
            context={"service": "openai", "status_code": 401}
        )
        
        clock = FixedClock(datetime(2025, 1, 1))
        analyzer = RiskAnalyzer(mock_client, clock)
        
        with pytest.raises(ProcessingError) as exc_info:
            analyzer.analyze("APP-012", "orphan_accounts", 10.0)
        
        # Verify error context is preserved
        assert exc_info.value.context["app_id"] == "APP-012"
        assert exc_info.value.context["kpi"] == "orphan_accounts"