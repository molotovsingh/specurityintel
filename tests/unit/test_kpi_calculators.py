"""
Unit tests for all KPI calculators.
"""

import pytest
import pandas as pd
from datetime import datetime

from src.modules.kpi.calculators import (
    AccessProvisioningTimeCalculator,
    AccessReviewStatusCalculator,
    PolicyViolationsCalculator,
    ExcessivePermissionsCalculator,
    DormantAccountsCalculator
)
from src.adapters.storage.in_memory import InMemoryStorage
from src.adapters.clock import FixedClock


class TestNewKPICalculators:
    """Test the new KPI calculators."""

    @pytest.fixture
    def test_setup(self):
        """Setup test infrastructure."""
        storage = InMemoryStorage()
        fixed_time = datetime(2025, 11, 2, 9, 0, 0)
        clock = FixedClock(fixed_time)
        return storage, clock, fixed_time

    def test_access_provisioning_time_calculator(self, test_setup):
        """Test access provisioning time calculator."""
        storage, clock, fixed_time = test_setup
        calc = AccessProvisioningTimeCalculator(storage, clock)

        # Test data with provisioning times
        data = pd.DataFrame({
            'app_id': ['APP-001', 'APP-001', 'APP-002'],
            'access_request_date': ['2025-10-01', '2025-10-05', '2025-10-10'],
            'access_granted_date': ['2025-10-03', '2025-10-06', '2025-10-15']
        })

        # Test APP-001 (2 days + 1 day = 1.5 average)
        result = calc.compute(data, 'APP-001')
        assert result.kpi_name == "access_provisioning_time"
        assert result.value == 1.5
        assert result.app_id == "APP-001"
        assert result.computed_at == fixed_time

        # Test APP-002 (5 days)
        result = calc.compute(data, 'APP-002')
        assert result.value == 5.0

        # Test with missing data
        data_missing = pd.DataFrame({
            'app_id': ['APP-003'],
            'access_request_date': ['2025-10-01']
            # Missing access_granted_date
        })
        result = calc.compute(data_missing, 'APP-003')
        assert result.value == 0.0

    def test_access_review_status_calculator(self, test_setup):
        """Test access review status calculator."""
        storage, clock, fixed_time = test_setup
        calc = AccessReviewStatusCalculator(storage, clock)

        # Test data with review dates
        data = pd.DataFrame({
            'app_id': ['APP-001', 'APP-001', 'APP-001'],
            'status': ['active', 'active', 'inactive'],
            'last_review_date': ['2025-07-01', '2025-10-01', '2025-09-01']  # First one is overdue (>90 days)
        })

        result = calc.compute(data, 'APP-001')
        assert result.kpi_name == "access_reviews"
        assert result.value == 1.0  # One account overdue for review
        assert result.app_id == "APP-001"

        # Test with no overdue reviews
        data_recent = pd.DataFrame({
            'app_id': ['APP-002'],
            'status': ['active'],
            'last_review_date': ['2025-10-15']  # Recent
        })
        result = calc.compute(data_recent, 'APP-002')
        assert result.value == 0.0

    def test_policy_violations_calculator(self, test_setup):
        """Test policy violations calculator."""
        storage, clock, fixed_time = test_setup
        calc = PolicyViolationsCalculator(storage, clock)

        # Test data with various violations
        data = pd.DataFrame({
            'app_id': ['APP-001', 'APP-001', 'APP-001', 'APP-001'],
            'status': ['active', 'active', 'active', 'inactive'],
            'exit_date': [None, '2025-10-01', None, None],  # One orphan account
            'failed_attempts': [5, 15, 0, 2],  # One with excessive failures (>10)
            'is_privileged': [True, False, True, False],
            'last_review_date': ['2025-09-01', '2025-10-01', '2025-10-15', None]  # One privileged without recent review
        })

        result = calc.compute(data, 'APP-001')
        assert result.kpi_name == "policy_violations"
        assert result.value == 3.0  # orphan + excessive failures + privileged without review

        # Test with clean data
        clean_data = pd.DataFrame({
            'app_id': ['APP-002'],
            'status': ['active'],
            'exit_date': [None],
            'failed_attempts': [2],
            'is_privileged': [False],
            'last_review_date': ['2025-10-15']
        })
        result = calc.compute(clean_data, 'APP-002')
        assert result.value == 0.0

    def test_excessive_permissions_calculator(self, test_setup):
        """Test excessive permissions calculator."""
        storage, clock, fixed_time = test_setup
        calc = ExcessivePermissionsCalculator(storage, clock)

        # Test data with excessive permissions
        data = pd.DataFrame({
            'app_id': ['APP-001', 'APP-001', 'APP-001', 'APP-001'],
            'user_id': ['U001', 'U002', 'U003', 'U004'],
            'is_privileged': [True, True, False, True],
            'environment': ['DEV', 'PROD', 'DEV', 'TEST'],  # Two privileged in non-prod
            'role': ['ADMIN', 'USER', 'USER', 'ADMIN'],
            'justification': ['Business need', '', None, 'Valid reason']  # One without justification
        })

        result = calc.compute(data, 'APP-001')
        assert result.kpi_name == "excessive_permissions"
        assert result.value == 3.0  # 2 privileged in non-prod + 1 without justification

        # Test with clean data
        clean_data = pd.DataFrame({
            'app_id': ['APP-002'],
            'is_privileged': [True],
            'environment': ['PROD'],
            'role': ['USER'],
            'justification': ['Valid business reason']
        })
        result = calc.compute(clean_data, 'APP-002')
        assert result.value == 0.0

    def test_dormant_accounts_calculator(self, test_setup):
        """Test dormant accounts calculator."""
        storage, clock, fixed_time = test_setup
        calc = DormantAccountsCalculator(storage, clock)

        # Test data with dormant accounts
        data = pd.DataFrame({
            'app_id': ['APP-001', 'APP-001', 'APP-001', 'APP-001'],
            'status': ['active', 'active', 'active', 'inactive'],
            'last_login_date': ['2025-07-01', '2025-10-15', None, '2025-09-01'],  # First and third are dormant/never logged in
            'account_created_date': ['2025-01-01', '2025-09-01', '2025-09-20', '2025-08-01']  # Third created >7 days ago
        })

        result = calc.compute(data, 'APP-001')
        assert result.kpi_name == "dormant_accounts"
        assert result.value == 2.0  # One with old login, one never logged in

        # Test with active data
        active_data = pd.DataFrame({
            'app_id': ['APP-002'],
            'status': ['active'],
            'last_login_date': ['2025-10-30'],
            'account_created_date': ['2025-10-01']
        })
        result = calc.compute(active_data, 'APP-002')
        assert result.value == 0.0

    def test_calculator_error_handling(self, test_setup):
        """Test that calculators handle errors gracefully."""
        storage, clock, fixed_time = test_setup
        calc = AccessProvisioningTimeCalculator(storage, clock)

        # Test with invalid data that should raise ProcessingError
        invalid_data = pd.DataFrame({
            'app_id': ['APP-001'],
            'access_request_date': ['invalid-date'],
            'access_granted_date': ['also-invalid']
        })

        # Should not raise exception but handle gracefully
        result = calc.compute(invalid_data, 'APP-001')
        assert result.value == 0.0  # Should default to 0 on error

    def test_calculator_persistence(self, test_setup):
        """Test that calculators persist KPIs to storage."""
        storage, clock, fixed_time = test_setup
        calc = AccessProvisioningTimeCalculator(storage, clock)

        data = pd.DataFrame({
            'app_id': ['APP-001'],
            'access_request_date': ['2025-10-01'],
            'access_granted_date': ['2025-10-03']
        })

        result = calc.compute(data, 'APP-001')
        
        # Verify KPI was persisted
        stored_kpis = storage.kpis
        assert len(stored_kpis) == 1
        assert stored_kpis[0].kpi_name == "access_provisioning_time"
        assert stored_kpis[0].app_id == "APP-001"
        assert stored_kpis[0].value == 2.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])