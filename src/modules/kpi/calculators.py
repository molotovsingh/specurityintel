"""
KPI Calculator implementations.
"""

import pandas as pd
from datetime import datetime
from ...interfaces.dto import KPIRecord
from ...interfaces.ports import Storage, Clock
from ...interfaces.errors import ProcessingError


class KPICalculator:
    """Base class for KPI calculators."""

    def __init__(self, storage: Storage, clock: Clock):
        self.storage = storage
        self.clock = clock

    def compute(self, data: pd.DataFrame, app_id: str) -> KPIRecord:
        """Compute KPI for application."""
        raise NotImplementedError


class OrphanAccountsCalculator(KPICalculator):
    """Calculates orphan accounts KPI."""

    def compute(self, data: pd.DataFrame, app_id: str) -> KPIRecord:
        """Count accounts with no recent activity."""
        try:
            # Filter for this app
            app_data = data[data["app_id"] == app_id]

            # Simple heuristic: count accounts with status="ORPHAN"
            if "status" in app_data.columns:
                orphan_count = len(app_data[app_data["status"] == "ORPHAN"])
            else:
                orphan_count = 0

            kpi = KPIRecord(
                app_id=app_id,
                kpi_name="orphan_accounts",
                value=float(orphan_count),
                computed_at=self.clock.now()
            )

            self.storage.persist_kpi(kpi)
            return kpi

        except Exception as e:
            raise ProcessingError(
                message=f"Failed to compute orphan_accounts: {str(e)}",
                context={"app_id": app_id}
            )


class PrivilegedAccountsCalculator(KPICalculator):
    """Calculates privileged accounts KPI."""

    def compute(self, data: pd.DataFrame, app_id: str) -> KPIRecord:
        """Count privileged accounts."""
        try:
            app_data = data[data["app_id"] == app_id]

            if "role" in app_data.columns:
                privileged = len(app_data[app_data["role"].isin(["ADMIN", "ROOT"])])
            else:
                privileged = 0

            kpi = KPIRecord(
                app_id=app_id,
                kpi_name="privileged_accounts",
                value=float(privileged),
                computed_at=self.clock.now()
            )

            self.storage.persist_kpi(kpi)
            return kpi

        except Exception as e:
            raise ProcessingError(
                message=f"Failed to compute privileged_accounts: {str(e)}",
                context={"app_id": app_id}
            )


class FailedAccessAttemptsCalculator(KPICalculator):
    """Calculates failed access attempts KPI."""

    def compute(self, data: pd.DataFrame, app_id: str) -> KPIRecord:
        """Count failed access attempts."""
        try:
            app_data = data[data["app_id"] == app_id]

            if "access_result" in app_data.columns:
                failed = len(app_data[app_data["access_result"] == "FAILED"])
            else:
                failed = 0

            kpi = KPIRecord(
                app_id=app_id,
                kpi_name="failed_access_attempts",
                value=float(failed),
                computed_at=self.clock.now()
            )

            self.storage.persist_kpi(kpi)
            return kpi

        except Exception as e:
            raise ProcessingError(
                message=f"Failed to compute failed_access_attempts: {str(e)}",
                context={"app_id": app_id}
            )
