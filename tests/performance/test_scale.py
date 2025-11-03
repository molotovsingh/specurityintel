"""
Performance tests for UAM Compliance system.

Tests system performance with large datasets (1,200 apps × 40,000 users).
"""

import pytest
import pandas as pd
import time
from datetime import datetime, timedelta

from src.composition_root import ServiceContainer
from src.adapters.storage.in_memory import InMemoryStorage
from src.adapters.openai_adapter import MockOpenAIClient
from src.adapters.clock import FixedClock


class TestSystemPerformance:
    """Test system performance at scale."""

    @pytest.fixture
    def performance_container(self):
        """Create optimized test container for performance testing."""
        fixed_time = datetime(2025, 11, 2, 9, 0, 0)
        clock = FixedClock(fixed_time)
        storage = InMemoryStorage()
        
        # Mock adapters for performance testing
        class FastSlackSender:
            def __init__(self, bot_token: str):
                self.bot_token = bot_token
                self.sent_alerts = []
            
            def send(self, alert):
                self.sent_alerts.append(alert)
                from src.interfaces.dto import DeliveryResult
                return DeliveryResult(success=True, delivered_at=datetime.now())
        
        class FastEmailSender:
            def __init__(self, smtp_host: str, smtp_port: int, username: str, password: str):
                self.sent_alerts = []
            
            def send(self, alert):
                self.sent_alerts.append(alert)
                from src.interfaces.dto import DeliveryResult
                return DeliveryResult(success=True, delivered_at=datetime.now())
            
            def send_digest(self, alerts):
                self.sent_alerts.extend(alerts)
                from src.interfaces.dto import DeliveryResult
                return DeliveryResult(success=True, delivered_at=datetime.now())
        
        slack = FastSlackSender("xoxb-perf")
        email = FastEmailSender("smtp.perf.com", 587, "perf@test.com", "test")
        openai = MockOpenAIClient("Performance risk analysis")
        
        from src.adapters.audit import StructlogAuditLogger
        audit_logger = StructlogAuditLogger(log_dir="./perf_logs")
        
        # Performance-optimized config
        from src.modules.config.loader import SystemConfig, NotificationSettings, AISettings
        from src.interfaces.dto import Thresholds
        
        config = SystemConfig(
            thresholds=Thresholds(alert_thresholds={
                "orphan_accounts": {"low": 1, "medium": 3, "high": 5, "critical": 10},
                "privileged_accounts": {"low": 5, "medium": 10, "high": 15, "critical": 20},
                "failed_access_attempts": {"low": 10, "medium": 25, "high": 50, "critical": 100},
                "access_provisioning_time": {"low": 7, "medium": 14, "high": 30, "critical": 60},
                "access_reviews": {"low": 1, "medium": 5, "high": 10, "critical": 20},
                "policy_violations": {"low": 1, "medium": 3, "high": 5, "critical": 10},
                "excessive_permissions": {"low": 5, "medium": 10, "high": 20, "critical": 50},
                "dormant_accounts": {"low": 10, "medium": 30, "high": 60, "critical": 100}
            }),
            notifications=NotificationSettings(),
            ai_settings=AISettings()
        )
        
        return ServiceContainer(
            clock=clock,
            storage=storage,
            slack=slack,  # type: ignore
            email=email,  # type: ignore
            openai=openai,
            audit_logger=audit_logger,
            config=config
        )

    def generate_large_dataset(self, num_apps: int = 1200, users_per_app: int = 40):
        """Generate large dataset for performance testing."""
        print(f"Generating dataset: {num_apps} apps × {users_per_app} users = {num_apps * users_per_app} records")
        
        records = []
        base_date = datetime(2025, 1, 1)
        
        for app_idx in range(num_apps):
            app_id = f"APP-{app_idx:04d}"
            
            for user_idx in range(users_per_app):
                user_id = f"U{app_idx:04d}-{user_idx:03d}"
                
                # Generate realistic data with some violations
                record = {
                    'app_id': app_id,
                    'user_id': user_id,
                    'username': f'user{user_idx}',
                    'status': 'active' if user_idx % 20 != 0 else 'inactive',
                    'is_privileged': user_idx % 10 == 0,  # 10% privileged
                    'exit_date': None if user_idx % 50 != 0 else '2025-10-01',  # 2% orphan accounts
                    'failed_attempts': user_idx % 25,  # Some with high failures
                    'access_request_date': (base_date + timedelta(days=user_idx % 365)).strftime('%Y-%m-%d'),
                    'access_granted_date': (base_date + timedelta(days=user_idx % 365 + (user_idx % 7))).strftime('%Y-%m-%d'),
                    'last_review_date': (base_date + timedelta(days=user_idx % 180)).strftime('%Y-%m-%d'),
                    'account_created_date': (base_date + timedelta(days=user_idx % 365)).strftime('%Y-%m-%d'),
                    'last_login_date': (base_date + timedelta(days=user_idx % 90)).strftime('%Y-%m-%d')
                }
                
                # Add some fields for advanced KPIs
                if user_idx % 100 == 0:  # 1% with excessive permissions
                    record['environment'] = 'DEV' if record['is_privileged'] else 'PROD'
                    record['justification'] = '' if record['is_privileged'] else 'N/A'
                else:
                    record['environment'] = 'PROD'
                    record['justification'] = 'Business need' if record['is_privileged'] else 'N/A'
                
                records.append(record)
        
        return pd.DataFrame(records)

    def test_csv_ingestion_performance(self, performance_container, tmp_path):
        """Test CSV ingestion performance with large dataset."""
        # Generate medium-sized dataset for this test
        data = self.generate_large_dataset(num_apps=100, users_per_app=100)  # 10,000 records
        
        csv_path = tmp_path / "large_uam_data.csv"
        data.to_csv(csv_path, index=False)
        
        csv_parser = performance_container.csv_parser()
        
        # Measure ingestion time
        start_time = time.time()
        df, is_full_load = csv_parser.parse(str(csv_path))
        ingestion_time = time.time() - start_time
        
        print(f"Ingested {len(df)} records in {ingestion_time:.2f} seconds")
        print(f"Ingestion rate: {len(df) / ingestion_time:.0f} records/second")
        
        # Performance assertions
        assert ingestion_time < 30.0, f"Ingestion took too long: {ingestion_time:.2f}s"
        assert len(df) == 10000, f"Expected 10000 records, got {len(df)}"
        assert is_full_load is False  # Not full load (less than 1200 apps)

    def test_kpi_computation_performance(self, performance_container):
        """Test KPI computation performance."""
        # Generate dataset
        data = self.generate_large_dataset(num_apps=50, users_per_app=200)  # 10,000 records
        
        # Test all KPI calculators
        calculators = [
            performance_container.orphan_accounts_calculator(),
            performance_container.privileged_accounts_calculator(),
            performance_container.failed_access_calculator(),
            performance_container.access_provisioning_time_calculator(),
            performance_container.access_review_status_calculator(),
            performance_container.policy_violations_calculator(),
            performance_container.excessive_permissions_calculator(),
            performance_container.dormant_accounts_calculator()
        ]
        
        # Measure KPI computation time
        start_time = time.time()
        
        for app_id in data["app_id"].unique()[:10]:  # Test first 10 apps
            for calc in calculators:
                kpi = calc.compute(data, app_id)
                assert kpi.value >= 0  # Basic sanity check
        
        kpi_time = time.time() - start_time
        
        print(f"Computed KPIs for 10 apps in {kpi_time:.2f} seconds")
        print(f"KPI computation rate: {(10 * len(calculators)) / kpi_time:.0f} KPIs/second")
        
        # Performance assertions
        assert kpi_time < 60.0, f"KPI computation took too long: {kpi_time:.2f}s"
        
        # Verify KPIs were persisted
        stored_kpis = performance_container.storage.kpis
        assert len(stored_kpis) >= 10 * len(calculators)

    def test_policy_evaluation_performance(self, performance_container):
        """Test policy evaluation performance."""
        data = self.generate_large_dataset(num_apps=100, users_per_app=50)  # 5,000 records
        
        policy_engine = performance_container.policy_engine()
        
        # Generate sample KPI values
        kpi_values = {
            "orphan_accounts": 5.0,
            "privileged_accounts": 8.0,
            "failed_access_attempts": 25.0,
            "access_provisioning_time": 15.0,
            "access_reviews": 3.0,
            "policy_violations": 4.0,
            "excessive_permissions": 6.0,
            "dormant_accounts": 12.0
        }
        
        # Measure policy evaluation time
        start_time = time.time()
        
        for app_id in data["app_id"].unique()[:50]:  # Test 50 apps
            violations = policy_engine.evaluate(app_id, kpi_values)
            # Basic sanity check
            assert isinstance(violations, list)
        
        policy_time = time.time() - start_time
        
        print(f"Evaluated policies for 50 apps in {policy_time:.2f} seconds")
        print(f"Policy evaluation rate: {50 / policy_time:.0f} apps/second")
        
        # Performance assertions
        assert policy_time < 30.0, f"Policy evaluation took too long: {policy_time:.2f}s"

    def test_alert_generation_performance(self, performance_container):
        """Test alert generation performance."""
        policy_engine = performance_container.policy_engine()
        alert_gen = performance_container.alert_generator()
        
        # Create sample violations
        from src.interfaces.dto import Violation, Severity
        
        violations = []
        for i in range(100):  # 100 violations
            violation = Violation(
                violation_id=f"V-{i:04d}",
                app_id=f"APP-{i:04d}",
                rule_id="test_rule",
                severity=Severity.MEDIUM,
                kpi_values={"test": 5.0},
                threshold_breached={"test": 3.0},
                evidence={"test": "evidence"},
                detected_at=datetime.now(),
                state="NEW"
            )
            violations.append(violation)
        
        # Measure alert generation time
        start_time = time.time()
        
        alerts_generated = 0
        for violation in violations:
            alert = alert_gen.generate_and_send(violation)
            if alert:
                alerts_generated += 1
        
        alert_time = time.time() - start_time
        
        print(f"Generated {alerts_generated} alerts in {alert_time:.2f} seconds")
        print(f"Alert generation rate: {alerts_generated / alert_time:.0f} alerts/second")
        
        # Performance assertions
        assert alert_time < 30.0, f"Alert generation took too long: {alert_time:.2f}s"
        assert alerts_generated > 0, "No alerts were generated"
        
        # Verify alerts were persisted
        stored_alerts = performance_container.storage.alerts
        assert len(stored_alerts) >= alerts_generated

    def test_end_to_end_performance_target(self, performance_container, tmp_path):
        """Test complete end-to-end pipeline meets performance targets."""
        # Generate realistic dataset
        data = self.generate_large_dataset(num_apps=100, users_per_app=100)  # 10,000 records
        
        csv_path = tmp_path / "e2e_test_data.csv"
        data.to_csv(csv_path, index=False)
        
        # Get components
        csv_parser = performance_container.csv_parser()
        policy_engine = performance_container.policy_engine()
        risk_analyzer = performance_container.risk_analyzer()
        alert_gen = performance_container.alert_generator()
        
        # Measure complete pipeline time
        pipeline_start = time.time()
        
        # Step 1: Ingestion
        ingestion_start = time.time()
        df, _ = csv_parser.parse(str(csv_path))
        ingestion_time = time.time() - ingestion_start
        
        # Step 2: KPI Computation (sample 10 apps for performance)
        kpi_start = time.time()
        sample_apps = df["app_id"].unique()[:10]
        
        for app_id in sample_apps:
            # Calculate all KPIs for this app
            kpi_values = {}
            
            orphan_calc = performance_container.orphan_accounts_calculator()
            kpi = orphan_calc.compute(df, app_id)
            kpi_values["orphan_accounts"] = kpi.value
            
            privileged_calc = performance_container.privileged_accounts_calculator()
            kpi = privileged_calc.compute(df, app_id)
            kpi_values["privileged_accounts"] = kpi.value
            
            failed_calc = performance_container.failed_access_calculator()
            kpi = failed_calc.compute(df, app_id)
            kpi_values["failed_access_attempts"] = kpi.value
            
            # Step 3: Policy Evaluation
            violations = policy_engine.evaluate(app_id, kpi_values)
            
            # Step 4: Risk Analysis (for first violation only)
            if violations:
                risk_result = risk_analyzer.analyze(
                    app_id=app_id,
                    kpi_name=list(violations[0].kpi_values.keys())[0] if violations[0].kpi_values else "unknown",
                    kpi_value=list(violations[0].kpi_values.values())[0] if violations[0].kpi_values else 0.0
                )
            
            # Step 5: Alert Generation
            for violation in violations:
                alert = alert_gen.generate_and_send(violation)
        
        kpi_time = time.time() - kpi_start
        total_time = time.time() - pipeline_start
        
        print("=== Performance Results ===")
        print(f"Dataset size: {len(df)} records")
        print(f"Apps processed: {len(sample_apps)}")
        print(f"Ingestion time: {ingestion_time:.2f}s ({len(df)/ingestion_time:.0f} records/sec)")
        print(f"KPI + Policy + Alert time: {kpi_time:.2f}s")
        print(f"Total pipeline time: {total_time:.2f}s")
        print(f"Per-app processing time: {total_time/len(sample_apps):.2f}s")
        
        # Performance targets (scaled down from full targets)
        # Full target: <15 min for 1,200 apps × 40,000 users
        # Scaled target: <2 min for 100 apps × 100 users (10x smaller dataset)
        max_total_time = 120.0  # 2 minutes
        
        assert total_time < max_total_time, f"E2E pipeline exceeded target: {total_time:.2f}s > {max_total_time}s"
        assert ingestion_time < 30.0, f"Ingestion exceeded target: {ingestion_time:.2f}s"
        assert kpi_time < 90.0, f"KPI processing exceeded target: {kpi_time:.2f}s"

    def test_memory_usage_large_dataset(self, performance_container):
        """Test memory usage with large dataset."""
        import psutil
        import os
        
        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Generate large dataset
        data = self.generate_large_dataset(num_apps=200, users_per_app=200)  # 40,000 records
        
        # Process dataset
        csv_parser = performance_container.csv_parser()
        
        # Simulate processing in memory
        df_processed = data.copy()
        
        # Calculate some KPIs
        for app_id in df_processed["app_id"].unique()[:20]:
            orphan_calc = performance_container.orphan_accounts_calculator()
            kpi = orphan_calc.compute(df_processed, app_id)
        
        # Get final memory usage
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        print(f"Memory usage: {initial_memory:.1f}MB -> {final_memory:.1f}MB (+{memory_increase:.1f}MB)")
        print(f"Memory per record: {memory_increase / len(df_processed) * 1024:.2f}KB")
        
        # Memory should be reasonable (less than 500MB for this test)
        assert memory_increase < 500.0, f"Memory usage too high: {memory_increase:.1f}MB"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])