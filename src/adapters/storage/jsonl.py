"""
JSON Lines Storage Adapter for UAM Compliance Intelligence System.

Provides file-based storage using JSON Lines format.
"""

import json
from pathlib import Path
from typing import List
from ...interfaces.ports import Storage
from ...interfaces.dto import KPIRecord, Violation, Alert
from ...interfaces.errors import StorageError


class JsonlStorage(Storage):
    """
    JSON Lines storage adapter for file-based persistence.

    Each record is written as a JSON object on a single line.
    Suitable for POC and local development.

    Example:
        storage = JsonlStorage(directory="./data")
        storage.persist_kpi(kpi_record)
    """

    def __init__(self, directory: str = "./data"):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)

        self.kpis_file = self.directory / "kpis.jsonl"
        self.violations_file = self.directory / "violations.jsonl"
        self.alerts_file = self.directory / "alerts.jsonl"

    def persist_kpi(self, kpi: KPIRecord) -> None:
        """
        Persist KPI record to JSONL file.

        Args:
            kpi: KPIRecord DTO to persist

        Raises:
            StorageError: If write fails
        """
        try:
            with open(self.kpis_file, "a") as f:
                f.write(kpi.model_dump_json() + "\n")
        except Exception as e:
            raise StorageError(
                message=f"Failed to persist KPI: {str(e)}",
                context={
                    "file": str(self.kpis_file),
                    "app_id": kpi.app_id,
                    "kpi_name": kpi.kpi_name
                }
            )

    def persist_violation(self, violation: Violation) -> None:
        """
        Persist violation record to JSONL file.

        Args:
            violation: Violation DTO to persist

        Raises:
            StorageError: If write fails
        """
        try:
            with open(self.violations_file, "a") as f:
                f.write(violation.model_dump_json() + "\n")
        except Exception as e:
            raise StorageError(
                message=f"Failed to persist violation: {str(e)}",
                context={
                    "file": str(self.violations_file),
                    "violation_id": violation.violation_id
                }
            )

    def persist_alert(self, alert: Alert) -> None:
        """
        Persist alert record to JSONL file.

        Args:
            alert: Alert DTO to persist

        Raises:
            StorageError: If write fails
        """
        try:
            with open(self.alerts_file, "a") as f:
                f.write(alert.model_dump_json() + "\n")
        except Exception as e:
            raise StorageError(
                message=f"Failed to persist alert: {str(e)}",
                context={
                    "file": str(self.alerts_file),
                    "alert_id": alert.alert_id
                }
            )

    def query_violations(self, app_id: str, state: str) -> List[Violation]:
        """
        Query violations by application and state.

        Args:
            app_id: Application identifier
            state: Violation state (NEW/RECURRING/RESOLVED)

        Returns:
            List of matching violations

        Raises:
            StorageError: If read fails
        """
        try:
            violations = []
            if self.violations_file.exists():
                with open(self.violations_file, "r") as f:
                    for line in f:
                        violation_data = json.loads(line)
                        if (violation_data.get("app_id") == app_id and
                                violation_data.get("state") == state):
                            violations.append(Violation(**violation_data))
            return violations
        except Exception as e:
            raise StorageError(
                message=f"Failed to query violations: {str(e)}",
                context={
                    "file": str(self.violations_file),
                    "app_id": app_id,
                    "state": state
                }
            )
