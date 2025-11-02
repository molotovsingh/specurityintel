"""
Unit tests for Data Transfer Objects (DTOs).

Validates Pydantic model validation and serialization.
"""

import pytest
from datetime import datetime
from src.interfaces.dto import (
    Severity, KPIRecord, RiskAnalysisResult, Violation, Alert, AuditEvent
)
from src.interfaces.errors import ValidationError


class TestSeverity:
    """Test Severity enum."""

    def test_severity_values(self):
        assert Severity.LOW.value == "LOW"
        assert Severity.MEDIUM.value == "MEDIUM"
        assert Severity.HIGH.value == "HIGH"
        assert Severity.CRITICAL.value == "CRITICAL"


class TestKPIRecord:
    """Test KPIRecord DTO."""

    def test_valid_kpi_record(self):
        kpi = KPIRecord(
            app_id="APP-123",
            kpi_name="orphan_accounts",
            value=5.0,
            computed_at=datetime.now()
        )
        assert kpi.app_id == "APP-123"
        assert kpi.kpi_name == "orphan_accounts"
        assert kpi.value == 5.0

    def test_kpi_record_immutable(self):
        kpi = KPIRecord(
            app_id="APP-123",
            kpi_name="orphan_accounts",
            value=5.0,
            computed_at=datetime.now()
        )
        with pytest.raises(Exception):
            kpi.value = 10.0

    def test_kpi_serialization(self):
        kpi = KPIRecord(
            app_id="APP-123",
            kpi_name="orphan_accounts",
            value=5.0,
            computed_at=datetime(2025, 11, 2, 9, 0, 0)
        )
        json_str = kpi.model_dump_json()
        assert "APP-123" in json_str
        assert "orphan_accounts" in json_str


class TestRiskAnalysisResult:
    """Test RiskAnalysisResult DTO."""

    def test_valid_risk_analysis(self):
        result = RiskAnalysisResult(
            app_id="APP-123",
            kpi_name="orphan_accounts",
            risk_score=75.0,
            confidence=85.0,
            explanation="Found 5 orphan accounts",
            factors={"account_count": 5.0},
            analyzed_at=datetime.now()
        )
        assert result.risk_score == 75.0
        assert result.confidence == 85.0

    def test_risk_score_range_validation(self):
        with pytest.raises(Exception):
            RiskAnalysisResult(
                app_id="APP-123",
                kpi_name="orphan_accounts",
                risk_score=150.0,  # Invalid: >100
                confidence=85.0,
                explanation="Test",
                factors={},
                analyzed_at=datetime.now()
            )

    def test_empty_explanation_rejected(self):
        with pytest.raises(Exception):
            RiskAnalysisResult(
                app_id="APP-123",
                kpi_name="orphan_accounts",
                risk_score=75.0,
                confidence=85.0,
                explanation="",  # Invalid: empty
                factors={},
                analyzed_at=datetime.now()
            )


class TestViolation:
    """Test Violation DTO."""

    def test_valid_violation(self):
        violation = Violation(
            violation_id="VIO-123",
            app_id="APP-123",
            rule_id="threshold_orphan",
            severity=Severity.HIGH,
            kpi_values={"orphan_accounts": 5.0},
            threshold_breached={"high": 5, "critical": 10},
            evidence={"reason": "Threshold exceeded"},
            detected_at=datetime.now(),
            state="NEW"
        )
        assert violation.state == "NEW"

    def test_invalid_violation_state(self):
        with pytest.raises(Exception):
            Violation(
                violation_id="VIO-123",
                app_id="APP-123",
                rule_id="threshold_orphan",
                severity=Severity.HIGH,
                kpi_values={"orphan_accounts": 5.0},
                threshold_breached={},
                evidence={},
                detected_at=datetime.now(),
                state="INVALID"
            )


class TestAlert:
    """Test Alert DTO."""

    def test_valid_alert(self):
        alert = Alert(
            alert_id="ALERT-123",
            app_id="APP-123",
            severity=Severity.CRITICAL,
            risk_score=90.0,
            violation_ids=["VIO-123"],
            title="Critical vulnerability",
            description="Found critical issue",
            recommendations=[
                "Review access",
                "Investigate",
                "Take action"
            ],
            created_at=datetime.now(),
            persona="compliance_officer"
        )
        assert alert.severity == Severity.CRITICAL

    def test_invalid_persona(self):
        with pytest.raises(Exception):
            Alert(
                alert_id="ALERT-123",
                app_id="APP-123",
                severity=Severity.CRITICAL,
                risk_score=90.0,
                violation_ids=["VIO-123"],
                title="Test",
                description="Test",
                recommendations=["1", "2", "3"],
                created_at=datetime.now(),
                persona="invalid_persona"
            )

    def test_recommendations_count_validation(self):
        with pytest.raises(Exception):
            Alert(
                alert_id="ALERT-123",
                app_id="APP-123",
                severity=Severity.CRITICAL,
                risk_score=90.0,
                violation_ids=["VIO-123"],
                title="Test",
                description="Test",
                recommendations=["Only one"],  # Must have 3-5
                created_at=datetime.now(),
                persona="compliance_officer"
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
