"""
Policy Rule Engine for violation detection.
"""

import pandas as pd
from uuid import uuid4
from typing import List
from ...interfaces.dto import Violation, Severity
from ...interfaces.ports import Storage, Clock
from ...interfaces.errors import ProcessingError


class PolicyRuleEngine:
    """
    Detects policy violations based on thresholds.

    Example:
        engine = PolicyRuleEngine(storage, clock, thresholds)
        violations = engine.evaluate(app_id, kpi_values)
    """

    def __init__(self, storage: Storage, clock: Clock, thresholds: dict):
        self.storage = storage
        self.clock = clock
        self.thresholds = thresholds

    def evaluate(self, app_id: str, kpi_values: dict) -> List[Violation]:
        """
        Evaluate KPI values against thresholds.

        Returns list of detected violations.
        """
        try:
            violations = []

            for kpi_name, value in kpi_values.items():
                thresholds = self.thresholds.get(kpi_name, {})

                # Determine severity
                severity = self._determine_severity(value, thresholds)

                if severity != Severity.LOW:  # Ignore LOW severity
                    violation = Violation(
                        violation_id=str(uuid4()),
                        app_id=app_id,
                        rule_id=f"threshold_{kpi_name}",
                        severity=severity,
                        kpi_values={kpi_name: value},
                        threshold_breached=thresholds,
                        evidence={"kpi_value": str(value)},
                        detected_at=self.clock.now(),
                        state="NEW"
                    )
                    self.storage.persist_violation(violation)
                    violations.append(violation)

            return violations

        except Exception as e:
            raise ProcessingError(
                message=f"Policy evaluation failed: {str(e)}",
                context={"app_id": app_id}
            )

    def _determine_severity(self, value: float, thresholds: dict) -> Severity:
        """Determine severity based on value vs thresholds."""
        if value >= thresholds.get("critical", float("inf")):
            return Severity.CRITICAL
        elif value >= thresholds.get("high", float("inf")):
            return Severity.HIGH
        elif value >= thresholds.get("medium", float("inf")):
            return Severity.MEDIUM
        else:
            return Severity.LOW
