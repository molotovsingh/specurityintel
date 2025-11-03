"""
Debug the high failed access attempts test.
"""

import pandas as pd
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.composition_root import ServiceContainer

# Create test data with high failed attempts
data = pd.DataFrame({
    'app_id': ['APP-001', 'APP-001', 'APP-001', 'APP-001', 'APP-002', 'APP-002'],
    'user_id': ['U001', 'U002', 'U003', 'U004', 'U005', 'U006'],
    'username': ['alice', 'bob', 'charlie', 'dave', 'eve', 'frank'],
    'status': ['active', 'active', 'active', 'active', 'active', 'active'],
    'is_privileged': [True, False, True, True, False, False],
    'exit_date': [None, '2025-10-01', '2025-10-15', '2025-10-20', None, '2025-10-15'],
    'failed_attempts': [0, 2, 0, 75, 15, 0]  # dave has 75 failed attempts
})

print("Test data:")
print(data)
print()

# Create test container
container = ServiceContainer.test()

# Test APP-002 (has 15 failed attempts for eve)
app_id = "APP-002"
app_data = data[data["app_id"] == app_id]
print(f"APP-002 data:")
print(app_data)
print()

# Calculate KPIs
failed_calc = container.failed_access_calculator()
failed_kpi = failed_calc.compute(data, app_id)
print(f"Failed attempts KPI for {app_id}: {failed_kpi.value}")

# Test policy evaluation
policy_engine = container.policy_engine()
kpi_values = {"failed_access_attempts": failed_kpi.value}

print(f"KPI values: {kpi_values}")
print(f"Thresholds: {container.config.thresholds.alert_thresholds}")

violations = policy_engine.evaluate(app_id, kpi_values)
print(f"Violations detected: {len(violations)}")
for v in violations:
    print(f"  - {v.rule_id}: {v.severity} (value: {v.kpi_values})")