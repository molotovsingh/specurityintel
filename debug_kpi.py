"""
Debug script to test KPI calculation.
"""

import pandas as pd
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.composition_root import ServiceContainer

# Create test data
data = pd.DataFrame({
    'app_id': ['APP-001', 'APP-001', 'APP-001', 'APP-001'],
    'user_id': ['U001', 'U002', 'U003', 'U004'],
    'username': ['alice', 'bob', 'charlie', 'dave'],
    'status': ['active', 'active', 'active', 'active'],
    'is_privileged': [True, False, True, True],
    'exit_date': [None, '2025-10-01', '2025-10-15', '2025-10-20'],
    'failed_attempts': [0, 2, 0, 30]
})

print("Test data:")
print(data)
print()

# Create test container
container = ServiceContainer.test()

# Test orphan accounts calculation
orphan_calc = container.orphan_accounts_calculator()
orphan_kpi = orphan_calc.compute(data, "APP-001")
print(f"Orphan accounts KPI: {orphan_kpi.value}")

# Test privileged accounts calculation
privileged_calc = container.privileged_accounts_calculator()
privileged_kpi = privileged_calc.compute(data, "APP-001")
print(f"Privileged accounts KPI: {privileged_kpi.value}")

# Test failed attempts calculation
failed_calc = container.failed_access_calculator()
failed_kpi = failed_calc.compute(data, "APP-001")
print(f"Failed attempts KPI: {failed_kpi.value}")

# Test policy evaluation
policy_engine = container.policy_engine()
kpi_values = {
    "orphan_accounts": orphan_kpi.value,
    "privileged_accounts": privileged_kpi.value,
    "failed_access_attempts": failed_kpi.value
}

print(f"\nKPI values: {kpi_values}")
print(f"Thresholds: {container.config.thresholds.alert_thresholds}")

# Debug severity determination
from src.interfaces.dto import Severity

for kpi_name, value in kpi_values.items():
    thresholds = container.config.thresholds.alert_thresholds.get(kpi_name, {})
    print(f"\nKPI: {kpi_name} = {value}")
    print(f"Thresholds: {thresholds}")
    
    # Manual severity check
    if value >= thresholds.get("critical", float("inf")):
        severity = Severity.CRITICAL
    elif value >= thresholds.get("high", float("inf")):
        severity = Severity.HIGH
    elif value >= thresholds.get("medium", float("inf")):
        severity = Severity.MEDIUM
    else:
        severity = Severity.LOW
    print(f"Determined severity: {severity}")

violations = policy_engine.evaluate("APP-001", kpi_values)
print(f"\nViolations detected: {len(violations)}")
for v in violations:
    print(f"  - {v.rule_id}: {v.severity} (value: {v.kpi_values})")