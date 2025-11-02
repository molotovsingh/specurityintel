"""
In-Memory Storage Adapter for testing.
"""

from typing import List
from ...interfaces.ports import Storage
from ...interfaces.dto import KPIRecord, Violation, Alert


class InMemoryStorage(Storage):
    """
    In-memory storage for integration testing.

    Example:
        storage = InMemoryStorage()
        storage.persist_kpi(kpi_record)
    """

    def __init__(self):
        self.kpis: List[KPIRecord] = []
        self.violations: List[Violation] = []
        self.alerts: List[Alert] = []

    def persist_kpi(self, kpi: KPIRecord) -> None:
        self.kpis.append(kpi)

    def persist_violation(self, violation: Violation) -> None:
        self.violations.append(violation)

    def persist_alert(self, alert: Alert) -> None:
        self.alerts.append(alert)

    def query_violations(self, app_id: str, state: str) -> List[Violation]:
        return [v for v in self.violations if v.app_id == app_id and v.state == state]
