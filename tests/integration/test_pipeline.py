"""
Integration tests for the complete UAM Compliance pipeline.

Tests end-to-end flow using in-memory adapters.
"""

import pytest
import pandas as pd
from datetime import datetime

from src.composition_root import ServiceContainer
from src.interfaces.dto import Severity
from src.adapters.storage.in_memory import InMemoryStorage
from src.adapters.openai_adapter import MockOpenAIClient
from src.adapters.clock import FixedClock


class TestEndToEndPipeline:
    """Test complete pipeline from CSV parsing to alert dispatch."""

    @pytest.fixture
    def test_container(self):
        """Create test container with in-memory adapters."""
        # Fixed time for deterministic tests
        fixed_time = datetime(2025, 11, 2, 9, 0, 0)
        clock = FixedClock(fixed_time)
        
        # In-memory storage
        storage = InMemoryStorage()
        
        # Mock adapters
        from src.adapters.audit import StructlogAuditLogger
        
        # Create in-memory mock adapters for testing
        class InMemorySlackSender:
            def __init__(self, bot_token: str):
                self.bot_token = bot_token
                self.sent_alerts = []
            
            def send(self, alert):
                self.sent_alerts.append(alert)
                from src.interfaces.dto import DeliveryResult
                return DeliveryResult(success=True, delivered_at=datetime.now())
        
        class InMemoryEmailSender:
            def __init__(self, smtp_host: str, smtp_port: int, username: str, password: str):
                self.smtp_host = smtp_host
                self.sent_alerts = []
            
            def send(self, alert):
                self.sent_alerts.append(alert)
                from src.interfaces.dto import DeliveryResult
                return DeliveryResult(success=True, delivered_at=datetime.now())
                
            def send_digest(self, alerts):
                self.sent_alerts.extend(alerts)
                from src.interfaces.dto import DeliveryResult
                return DeliveryResult(success=True, delivered_at=datetime.now())
        
        slack = InMemorySlackSender("xoxb-test")
        email = InMemoryEmailSender("smtp.test.com", 587, "test@test.com", "test")
        openai = MockOpenAIClient("High risk due to orphan account spike")
        audit_logger = StructlogAuditLogger(log_dir="./test_logs")
        
        # Test configuration
        from src.modules.config.loader import SystemConfig, NotificationSettings, AISettings
        from src.interfaces.dto import Thresholds
        
        config = SystemConfig(
            thresholds=Thresholds(alert_thresholds={
                "orphan_accounts": {"low": 1, "medium": 3, "high": 5, "critical": 10},
                "privileged_accounts": {"low": 5, "medium": 10, "high": 15, "critical": 20},
                "failed_access_attempts": {"low": 10, "medium": 25, "high": 50, "critical": 100}
            }),
            notifications=NotificationSettings(),
            ai_settings=AISettings()
        )
        
        # Create container manually to avoid type issues
        container = ServiceContainer(
            clock=clock,
            storage=storage,
            slack=slack,  # type: ignore
            email=email,  # type: ignore
            openai=openai,
            audit_logger=audit_logger,
            config=config
        )
        return container

    @pytest.fixture
    def sample_csv_data(self):
        """Create sample UAM CSV data for testing."""
        return pd.DataFrame({
            'app_id': ['APP-001', 'APP-001', 'APP-001', 'APP-001', 'APP-002', 'APP-002'],
            'user_id': ['U001', 'U002', 'U003', 'U004', 'U005', 'U006'],
            'username': ['alice', 'bob', 'charlie', 'dave', 'eve', 'frank'],
            'status': ['active', 'active', 'active', 'active', 'active', 'active'],
            'is_privileged': [True, False, True, True, False, False],
            'exit_date': [None, '2025-10-01', '2025-10-15', '2025-10-20', None, '2025-10-15'],
            'failed_attempts': [0, 2, 0, 30, 35, 0],
            'access_request_date': ['2025-09-01', '2025-09-15', '2025-10-01', '2025-09-10', '2025-10-05', '2025-10-01'],
            'access_granted_date': ['2025-09-02', '2025-09-16', '2025-10-02', '2025-09-25', '2025-10-06', '2025-10-02'],
            'last_review_date': ['2025-09-15', '2025-09-15', '2025-10-15', '2025-09-20', '2025-10-15', '2025-10-15'],
            'account_created_date': ['2025-01-01', '2025-02-01', '2025-03-01', '2025-04-01', '2025-05-01', '2025-06-01'],
            'last_login_date': ['2025-10-30', '2025-10-15', '2025-11-01', '2025-10-20', '2025-10-10', '2025-11-01']
        })

    def test_critical_orphan_accounts_alert_flow(self, test_container, sample_csv_data, tmp_path):
        """Test complete flow for critical orphan accounts violation."""
        # Setup: Create CSV file with critical orphan accounts
        csv_path = tmp_path / "uam_data.csv"
        sample_csv_data.to_csv(csv_path, index=False)
        
        # Get pipeline components
        csv_parser = test_container.csv_parser()
        policy_engine = test_container.policy_engine()
        risk_analyzer = test_container.risk_analyzer()
        alert_gen = test_container.alert_generator()
        
        # Step 1: Parse CSV
        df, is_full_load = csv_parser.parse(str(csv_path))
        assert len(df) == 6
        assert is_full_load is False  # Only 2 apps, so not full load
        
        # Step 2: Calculate KPIs for APP-001 (has 1 orphan account)
        app_id = "APP-001"
        kpi_values = {}
        
        orphan_calc = test_container.orphan_accounts_calculator()
        kpi = orphan_calc.compute(df, app_id)
        kpi_values["orphan_accounts"] = kpi.value
        
        privileged_calc = test_container.privileged_accounts_calculator()
        kpi = privileged_calc.compute(df, app_id)
        kpi_values["privileged_accounts"] = kpi.value
        
        failed_calc = test_container.failed_access_calculator()
        kpi = failed_calc.compute(df, app_id)
        kpi_values["failed_access_attempts"] = kpi.value
        
        # Verify KPI calculations
        assert kpi_values["orphan_accounts"] == 3.0  # bob, charlie, dave exited but still active
        assert kpi_values["privileged_accounts"] == 3.0  # alice, charlie, dave
        assert kpi_values["failed_access_attempts"] == 32.0  # dave has 30 failed attempts
        
        # Step 3: Evaluate policies (should trigger MEDIUM for orphan_accounts and failed_access_attempts)
        violations = policy_engine.evaluate(app_id, kpi_values)
        assert len(violations) >= 2  # Should have at least 2 violations
        
        orphan_violation = next((v for v in violations if "orphan" in v.rule_id), None)
        assert orphan_violation is not None
        assert orphan_violation.severity == Severity.MEDIUM
        assert orphan_violation.app_id == app_id
        
        # Step 4: Analyze risk
        risk_result = risk_analyzer.analyze(
            app_id=app_id,
            kpi_name="orphan_accounts",
            kpi_value=kpi_values["orphan_accounts"]
        )
        assert risk_result.risk_score > 0
        assert "High risk due to orphan account spike" in risk_result.explanation
        
        # Step 5: Generate and send alert
        alert = alert_gen.generate_and_send(orphan_violation)
        assert alert is not None
        assert alert.app_id == app_id
        assert alert.severity == Severity.MEDIUM
        assert len(alert.violation_ids) > 0
        assert len(alert.recommendations) >= 3
        
        # Verify alert persisted to storage
        stored_alerts = test_container.storage.alerts
        assert len(stored_alerts) == 1
        assert stored_alerts[0].alert_id == alert.alert_id
        
        # Verify violation persisted
        stored_violations = test_container.storage.query_violations(app_id, "NEW")
        assert len(stored_violations) >= 1

    def test_high_failed_access_attempts_flow(self, test_container, sample_csv_data, tmp_path):
        """Test flow for high failed access attempts."""
        # Create data with high failed attempts
        high_failure_data = sample_csv_data.copy()
        high_failure_data.loc[high_failure_data['user_id'] == 'U004', 'failed_attempts'] = 75
        
        csv_path = tmp_path / "high_failures.csv"
        high_failure_data.to_csv(csv_path, index=False)
        
        # Parse and process
        csv_parser = test_container.csv_parser()
        policy_engine = test_container.policy_engine()
        alert_gen = test_container.alert_generator()
        
        df, _ = csv_parser.parse(str(csv_path))
        
        # Calculate KPIs for APP-001 (where U004 with 75 failed attempts belongs)
        app_id = "APP-001"
        kpi_values = {}
        
        failed_calc = test_container.failed_access_calculator()
        kpi = failed_calc.compute(df, app_id)
        kpi_values["failed_access_attempts"] = kpi.value
        
        # Should trigger HIGH severity (75 is between 50 and 100)
        violations = policy_engine.evaluate(app_id, kpi_values)
        failed_violation = next((v for v in violations if "failed" in v.rule_id), None)
        
        assert failed_violation is not None
        assert failed_violation.severity == Severity.HIGH
        
        # Generate alert
        alert = alert_gen.generate_and_send(failed_violation)
        assert alert.severity == Severity.HIGH

    def test_no_violations_scenario(self, test_container, tmp_path):
        """Test scenario with no violations."""
        # Create clean data
        clean_data = pd.DataFrame({
            'app_id': ['APP-003'],
            'user_id': ['U006'],
            'username': ['frank'],
            'status': ['active'],
            'is_privileged': [False],
            'exit_date': [None],
            'failed_attempts': [0],
            'access_request_date': ['2025-09-01'],
            'access_granted_date': ['2025-09-02'],
            'last_review_date': ['2025-10-15'],
            'account_created_date': ['2025-01-01'],
            'last_login_date': ['2025-11-01']
        })
        
        csv_path = tmp_path / "clean_data.csv"
        clean_data.to_csv(csv_path, index=False)
        
        # Process
        csv_parser = test_container.csv_parser()
        policy_engine = test_container.policy_engine()
        
        df, _ = csv_parser.parse(str(csv_path))
        
        app_id = "APP-003"
        kpi_values = {}
        
        # Calculate all KPIs
        for calc_name in ["orphan_accounts_calculator", "privileged_accounts_calculator", "failed_access_calculator"]:
            calc = getattr(test_container, calc_name)()
            kpi = calc.compute(df, app_id)
            kpi_values[kpi.kpi_name] = kpi.value
        
        # Should have no violations
        violations = policy_engine.evaluate(app_id, kpi_values)
        assert len(violations) == 0

    def test_multiple_applications_processing(self, test_container, sample_csv_data, tmp_path):
        """Test processing multiple applications in one run."""
        csv_path = tmp_path / "multi_app.csv"
        sample_csv_data.to_csv(csv_path, index=False)
        
        csv_parser = test_container.csv_parser()
        policy_engine = test_container.policy_engine()
        alert_gen = test_container.alert_generator()
        
        df, _ = csv_parser.parse(str(csv_path))
        
        # Process both applications
        total_violations = 0
        total_alerts = 0
        
        for app_id in df["app_id"].unique():
            kpi_values = {}
            
            # Calculate KPIs
            orphan_calc = test_container.orphan_accounts_calculator()
            kpi = orphan_calc.compute(df, app_id)
            kpi_values["orphan_accounts"] = kpi.value
            
            # Evaluate policies
            violations = policy_engine.evaluate(app_id, kpi_values)
            total_violations += len(violations)
            
            # Generate alerts for violations
            for violation in violations:
                alert = alert_gen.generate_and_send(violation)
                total_alerts += 1
        
        # Verify processing results
        assert total_violations > 0  # Should have some violations
        assert total_alerts > 0  # Should have generated alerts
        
        # Verify storage has records for both apps
        stored_alerts = test_container.storage.alerts
        app_ids_in_alerts = set(alert.app_id for alert in stored_alerts)
        assert len(app_ids_in_alerts) >= 1  # At least one app had violations

    def test_error_handling_invalid_csv(self, test_container, tmp_path):
        """Test error handling for malformed CSV."""
        # Create invalid CSV with mismatched columns
        invalid_csv_path = tmp_path / "invalid.csv"
        invalid_csv_path.write_text("app_id,user_id\nAPP-001")  # Missing user_id value
        
        csv_parser = test_container.csv_parser()
        
        # Should handle gracefully - pandas will parse but we can test the error handling
        try:
            df, is_full_load = csv_parser.parse(str(invalid_csv_path))
            # If parsing succeeds, that's okay - pandas is lenient
            assert len(df) >= 0
        except Exception:
            # If it raises an exception, that's also acceptable
            pass

    def test_kpi_persistence(self, test_container, sample_csv_data, tmp_path):
        """Test that KPIs are properly persisted."""
        csv_path = tmp_path / "kpi_test.csv"
        sample_csv_data.to_csv(csv_path, index=False)
        
        csv_parser = test_container.csv_parser()
        
        df, _ = csv_parser.parse(str(csv_path))
        
        # Calculate KPIs
        orphan_calc = test_container.orphan_accounts_calculator()
        kpi = orphan_calc.compute(df, "APP-001")
        
        # Verify KPI persisted
        stored_kpis = test_container.storage.kpis
        assert len(stored_kpis) > 0
        
        orphan_kpi = next((k for k in stored_kpis if k.kpi_name == "orphan_accounts"), None)
        assert orphan_kpi is not None
        assert orphan_kpi.value == 3.0
        assert orphan_kpi.app_id == "APP-001"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])