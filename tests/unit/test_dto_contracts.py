"""
DTO serialization/deserialization contract tests.

Validates that all DTOs can be properly serialized to JSON/dict
and deserialized back without data loss.
"""

import pytest
import json
from datetime import datetime

from src.interfaces.dto import (
    Severity, KPIRecord, RiskAnalysisResult, Violation, Alert, 
    AuditEvent, Thresholds, DeliveryResult, Prompt, AIResponse
)
from src.modules.config.loader import SystemConfig, NotificationSettings, AISettings
from src.interfaces.errors import (
    ValidationError, ConfigurationError, 
    IntegrationError, ProcessingError, StorageError
)


class TestDTOContracts:
    """Test DTO serialization/deserialization contracts."""

    def test_severity_enum_serialization(self):
        """Test Severity enum serialization."""
        # Test all severity values
        for severity in Severity:
            # To dict
            severity_dict = severity.value
            assert isinstance(severity_dict, str)
            
            # From string
            reconstructed = Severity(severity_dict)
            assert reconstructed == severity
            
            # JSON serialization
            json_str = json.dumps({"severity": severity.value})
            data = json.loads(json_str)
            reconstructed_from_json = Severity(data["severity"])
            assert reconstructed_from_json == severity

    def test_kpi_record_contract(self):
        """Test KPIRecord serialization contract."""
        # Create test KPI
        kpi = KPIRecord(
            app_id="APP-001",
            kpi_name="orphan_accounts",
            value=5.0,
            computed_at=datetime(2025, 11, 2, 9, 0, 0),
            meta={"source": "csv", "version": "1.0"}
        )
        
        # Test dict serialization
        kpi_dict = kpi.dict()
        assert kpi_dict["app_id"] == "APP-001"
        assert kpi_dict["kpi_name"] == "orphan_accounts"
        assert kpi_dict["value"] == 5.0
        assert "computed_at" in kpi_dict
        assert kpi_dict["meta"]["source"] == "csv"
        
        # Test JSON serialization
        kpi_json = kpi.json()
        assert isinstance(kpi_json, str)
        
        # Test deserialization
        reconstructed = KPIRecord.parse_raw(kpi_json)
        assert reconstructed.app_id == kpi.app_id
        assert reconstructed.kpi_name == kpi.kpi_name
        assert reconstructed.value == kpi.value
        assert reconstructed.meta == kpi.meta
        
        # Test dict deserialization
        reconstructed_from_dict = KPIRecord.parse_obj(kpi_dict)
        assert reconstructed_from_dict.app_id == kpi.app_id

    def test_risk_analysis_result_contract(self):
        """Test RiskAnalysisResult serialization contract."""
        risk = RiskAnalysisResult(
            app_id="APP-001",
            kpi_name="orphan_accounts",
            risk_score=75.5,
            confidence=0.85,
            explanation="High risk due to orphan account spike",
            factors={"orphan_accounts_high": 0.6, "no_recent_review": 0.4},
            analyzed_at=datetime(2025, 11, 2, 9, 0, 0)
        )
        
        # Test serialization
        risk_dict = risk.dict()
        assert risk_dict["risk_score"] == 75.5
        assert len(risk_dict["factors"]) == 2
        assert risk_dict["confidence"] == 0.85
        
        # Test JSON roundtrip
        risk_json = risk.json()
        reconstructed = RiskAnalysisResult.parse_raw(risk_json)
        assert reconstructed.risk_score == risk.risk_score
        assert reconstructed.factors == risk.factors
        assert reconstructed.confidence == risk.confidence

    def test_violation_contract(self):
        """Test Violation serialization contract."""
        violation = Violation(
            violation_id="V-001",
            app_id="APP-001",
            rule_id="orphan_accounts_threshold",
            severity=Severity.HIGH,
            kpi_values={"orphan_accounts": 5.0},
            threshold_breached={"orphan_accounts": 3.0},
            evidence={"current_count": "5", "threshold": "3"},
            detected_at=datetime(2025, 11, 2, 9, 0, 0),
            state="NEW"
        )
        
        # Test serialization
        violation_dict = violation.dict()
        assert violation_dict["severity"] == "HIGH"
        assert violation_dict["state"] == "NEW"
        
        # Test JSON roundtrip
        violation_json = violation.json()
        reconstructed = Violation.parse_raw(violation_json)
        assert reconstructed.severity == Severity.HIGH
        assert reconstructed.state == "NEW"
        assert reconstructed.violation_id == violation.violation_id

    def test_alert_contract(self):
        """Test Alert serialization contract."""
        alert = Alert(
            alert_id="A-001",
            app_id="APP-001",
            severity=Severity.CRITICAL,
            risk_score=85.0,
            violation_ids=["V-001", "V-002"],
            title="Critical Security Violation",
            description="Orphan accounts detected in APP-001",
            recommendations=["Immediate review required", "Disable orphan accounts", "Update access policies"],
            created_at=datetime(2025, 11, 2, 9, 0, 0),
            persona="compliance_officer"
        )
        
        # Test serialization
        alert_dict = alert.dict()
        assert alert_dict["severity"] == "CRITICAL"
        assert len(alert_dict["violation_ids"]) == 2
        assert alert_dict["risk_score"] == 85.0
        
        # Test JSON roundtrip
        alert_json = alert.json()
        reconstructed = Alert.parse_raw(alert_json)
        assert reconstructed.severity == Severity.CRITICAL
        assert len(reconstructed.violation_ids) == 2
        assert reconstructed.risk_score == 85.0

    def test_audit_event_contract(self):
        """Test AuditEvent serialization contract."""
        event = AuditEvent(
            event_type="VIOLATION_DETECTED",
            timestamp=datetime(2025, 11, 2, 9, 0, 0),
            details={"app_id": "APP-001", "kpi_value": "5.0", "threshold": "3.0"}
        )
        
        # Test serialization
        event_dict = event.dict()
        assert event_dict["event_type"] == "VIOLATION_DETECTED"
        assert "details" in event_dict
        
        # Test JSON roundtrip
        event_json = event.json()
        reconstructed = AuditEvent.parse_raw(event_json)
        assert reconstructed.event_type == "VIOLATION_DETECTED"
        assert reconstructed.details["kpi_value"] == "5.0"

    def test_thresholds_contract(self):
        """Test Thresholds serialization contract."""
        thresholds = Thresholds(
            alert_thresholds={
                "orphan_accounts": {"low": 1, "medium": 3, "high": 5, "critical": 10},
                "privileged_accounts": {"low": 5, "medium": 10, "high": 15, "critical": 20},
                "failed_access_attempts": {"low": 10, "medium": 25, "high": 50, "critical": 100}
            }
        )
        
        # Test serialization
        thresholds_dict = thresholds.dict()
        assert "alert_thresholds" in thresholds_dict
        
        # Test JSON roundtrip
        thresholds_json = thresholds.json()
        reconstructed = Thresholds.parse_raw(thresholds_json)
        assert reconstructed.alert_thresholds["orphan_accounts"]["medium"] == 3

    def test_delivery_result_contract(self):
        """Test DeliveryResult serialization contract."""
        result = DeliveryResult(
            success=True,
            delivered_at=datetime(2025, 11, 2, 9, 0, 0),
            retries=2,
            error=None
        )
        
        # Test serialization
        result_dict = result.dict()
        assert result_dict["success"] is True
        assert result_dict["retries"] == 2
        assert result_dict["error"] is None
        
        # Test JSON roundtrip
        result_json = result.json()
        reconstructed = DeliveryResult.parse_raw(result_json)
        assert reconstructed.success is True
        assert reconstructed.retries == 2
        assert reconstructed.error is None

    def test_prompt_contract(self):
        """Test Prompt serialization contract."""
        prompt = Prompt(
            text="Analyze orphan_accounts with value 5.0 for app APP-001",
            max_tokens=4000,
            model="gpt-4-turbo",
            temperature=0.1
        )
        
        # Test serialization
        prompt_dict = prompt.dict()
        assert "text" in prompt_dict
        assert "max_tokens" in prompt_dict
        assert "model" in prompt_dict
        
        # Test JSON roundtrip
        prompt_json = prompt.json()
        reconstructed = Prompt.parse_raw(prompt_json)
        assert reconstructed.text == prompt.text
        assert reconstructed.model == prompt.model
        assert reconstructed.temperature == prompt.temperature

    def test_ai_response_contract(self):
        """Test AIResponse serialization contract."""
        response = AIResponse(
            generated_text="High risk detected due to orphan accounts",
            token_count=150,
            cost_estimate=0.045
        )
        
        # Test serialization
        response_dict = response.dict()
        assert response_dict["token_count"] == 150
        assert response_dict["cost_estimate"] == 0.045
        
        # Test JSON roundtrip
        response_json = response.json()
        reconstructed = AIResponse.parse_raw(response_json)
        assert reconstructed.token_count == 150
        assert reconstructed.cost_estimate == 0.045

    def test_system_config_contract(self):
        """Test SystemConfig serialization contract."""
        config = SystemConfig(
            thresholds=Thresholds(
                alert_thresholds={
                    "orphan_accounts": {"low": 1, "medium": 3, "high": 5, "critical": 10}
                }
            ),
            notifications=NotificationSettings(
                slack_enabled=True,
                email_enabled=True,
                slack_bot_token="xoxb-test",
                smtp_host="smtp.test.com",
                smtp_port=587
            ),
            ai_settings=AISettings(
                openai_api_key="sk-test",
                model="gpt-4-turbo",
                temperature=0.1,
                max_tokens={"gpt-4-turbo": 128000}
            )
        )
        
        # Test serialization
        config_dict = config.dict()
        assert "thresholds" in config_dict
        assert "notifications" in config_dict
        assert "ai_settings" in config_dict
        
        # Test JSON roundtrip
        config_json = config.json()
        reconstructed = SystemConfig.parse_raw(config_json)
        assert reconstructed.notifications.slack_enabled is True
        assert reconstructed.ai_settings.model == "gpt-4-turbo"

    def test_error_hierarchy_serialization(self):
        """Test error hierarchy serialization."""
        # Test each error type
        errors = [
            ValidationError("Invalid data format", {"field": "value"}),
            ConfigurationError("Missing configuration", {"config_file": "config.yaml"}),
            IntegrationError("API call failed", {"service": "openai", "status_code": "500"}),
            ProcessingError("KPI calculation failed", {"kpi": "orphan_accounts"}),
            StorageError("Database connection failed", {"database": "postgres"})
        ]
        
        for error in errors:
            # Test dict serialization
            error_dict = error.to_dict()
            assert "error_code" in error_dict
            assert "message" in error_dict
            assert "timestamp" in error_dict
            
            # Test that context is included
            assert error_dict["error_code"] == error.error_code
            assert error_dict["message"] == error.message

    def test_nested_dto_serialization(self):
        """Test serialization of nested DTOs."""
        # Create complex nested structure
        violation = Violation(
            violation_id="V-001",
            app_id="APP-001",
            rule_id="test_rule",
            severity=Severity.HIGH,
            kpi_values={"orphan_accounts": 5.0},
            threshold_breached={"orphan_accounts": 3.0},
            evidence={"count": "5"},
            detected_at=datetime(2025, 11, 2, 9, 0, 0)
        )
        
        alert = Alert(
            alert_id="A-001",
            app_id="APP-001",
            severity=Severity.HIGH,
            risk_score=75.0,
            violation_ids=[violation.violation_id],
            title="Test Alert",
            description="Test message",
            recommendations=["Fix it", "Review it", "Document it"],
            created_at=datetime(2025, 11, 2, 9, 0, 0),
            persona="compliance_officer"
        )
        
        # Test that nested serialization works
        alert_dict = alert.dict()
        assert isinstance(alert_dict["violation_ids"], list)
        assert alert_dict["violation_ids"][0] == violation.violation_id
        
        # Test JSON roundtrip
        alert_json = alert.json()
        reconstructed = Alert.parse_raw(alert_json)
        assert reconstructed.violation_ids == alert.violation_ids

    def test_datetime_serialization_consistency(self):
        """Test datetime serialization consistency across DTOs."""
        test_time = datetime(2025, 11, 2, 9, 0, 0)
        
        dtos_with_datetime = [
            KPIRecord(app_id="APP-001", kpi_name="test", value=1.0, computed_at=test_time),
            RiskAnalysisResult(app_id="APP-001", kpi_name="test", risk_score=50.0, confidence=0.5, explanation="test", factors={"factor": 0.5}, analyzed_at=test_time),
            Violation(violation_id="V-001", app_id="APP-001", rule_id="rule", severity=Severity.LOW, kpi_values={"test": 1.0}, threshold_breached={"test": 1.0}, evidence={"test": "test"}, detected_at=test_time),
            Alert(alert_id="A-001", app_id="APP-001", severity=Severity.LOW, risk_score=50.0, violation_ids=["V-001"], title="test", description="test", recommendations=["test", "test", "test"], created_at=test_time, persona="compliance_officer"),
            AuditEvent(event_type="TEST", timestamp=test_time, details={"test": "test"}),
            DeliveryResult(success=True, delivered_at=test_time, retries=0)
        ]
        
        for dto in dtos_with_datetime:
            # Test serialization
            dto_dict = dto.dict()
            dto_json = dto.json()
            
            # Test deserialization
            reconstructed = type(dto).parse_raw(dto_json)
            
            # Verify datetime is preserved for DTOs that have it
            if hasattr(dto, 'computed_at'):
                assert reconstructed.computed_at == test_time
            elif hasattr(dto, 'analyzed_at'):
                assert reconstructed.analyzed_at == test_time
            elif hasattr(dto, 'detected_at'):
                assert reconstructed.detected_at == test_time
            elif hasattr(dto, 'created_at'):
                assert reconstructed.created_at == test_time
            elif hasattr(dto, 'timestamp'):
                assert reconstructed.timestamp == test_time
            elif hasattr(dto, 'delivered_at'):
                assert reconstructed.delivered_at == test_time

    def test_optional_fields_serialization(self):
        """Test serialization of optional fields."""
        # Test with all optional fields
        kpi_full = KPIRecord(
            app_id="APP-001",
            kpi_name="test",
            value=1.0,
            computed_at=datetime(2025, 11, 2, 9, 0, 0),
            meta={"source": "test", "version": "1.0"}
        )
        
        # Test with minimal fields (meta should default to empty dict)
        kpi_minimal = KPIRecord(
            app_id="APP-002",
            kpi_name="test2",
            value=2.0,
            computed_at=datetime(2025, 11, 2, 9, 0, 0)
        )
        
        # Both should serialize correctly
        full_dict = kpi_full.dict()
        minimal_dict = kpi_minimal.dict()
        
        assert full_dict["meta"] is not None
        assert minimal_dict["meta"] == {}
        
        # Test JSON roundtrip
        full_reconstructed = KPIRecord.parse_raw(kpi_full.json())
        minimal_reconstructed = KPIRecord.parse_raw(kpi_minimal.json())
        
        assert full_reconstructed.meta == kpi_full.meta
        assert minimal_reconstructed.meta == {}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])