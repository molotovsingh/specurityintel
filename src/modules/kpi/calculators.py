"""
KPI Calculator implementations.
"""

import pandas as pd
from datetime import timedelta
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
        """Count orphan accounts (accounts whose manager is not in the system)."""
        try:
            # Filter for this app
            app_data = data[data["app_id"] == app_id]

            # Count orphan accounts: active users whose manager_id is not in user_id list
            orphan_count = 0
            if "manager_id" in app_data.columns and "user_id" in app_data.columns:
                orphan_accounts = app_data[
                    (app_data["manager_id"].notna()) & 
                    (~app_data["manager_id"].isin(app_data["user_id"]))
                ]
                orphan_count = len(orphan_accounts)
            elif "manager_id" in app_data.columns:
                # Fallback: count non-null manager_ids (assuming they're orphan)
                orphan_accounts = app_data[app_data["manager_id"].notna()]
                orphan_count = len(orphan_accounts)

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

            if "is_privileged" in app_data.columns:
                privileged = len(app_data[app_data["is_privileged"]])
            elif "role" in app_data.columns:
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

            if "failed_attempts" in app_data.columns:
                failed = int(app_data["failed_attempts"].sum())
            elif "access_result" in app_data.columns:
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


class AccessProvisioningTimeCalculator(KPICalculator):
    """Calculates average access provisioning time KPI."""

    def compute(self, data: pd.DataFrame, app_id: str) -> KPIRecord:
        """Calculate average time between access request and grant."""
        try:
            app_data = data[data["app_id"] == app_id].copy()

            avg_days = 0.0
            if "access_request_date" in app_data.columns and "access_granted_date" in app_data.columns:
                # Convert to datetime
                app_data["access_request_date"] = pd.to_datetime(app_data["access_request_date"], errors='coerce')
                app_data["access_granted_date"] = pd.to_datetime(app_data["access_granted_date"], errors='coerce')
                
                # Filter out rows with missing dates
                valid_rows = app_data[
                    app_data["access_request_date"].notna() & 
                    app_data["access_granted_date"].notna()
                ]
                
                if len(valid_rows) > 0:
                    # Calculate difference in days
                    time_diff = (valid_rows["access_granted_date"] - valid_rows["access_request_date"]).dt.days
                    # Filter out negative values (granted before requested)
                    time_diff = time_diff[time_diff >= 0]
                    if len(time_diff) > 0:
                        avg_days = float(time_diff.mean())

            kpi = KPIRecord(
                app_id=app_id,
                kpi_name="access_provisioning_time",
                value=avg_days,
                computed_at=self.clock.now()
            )

            self.storage.persist_kpi(kpi)
            return kpi

        except Exception as e:
            raise ProcessingError(
                message=f"Failed to compute access_provisioning_time: {str(e)}",
                context={"app_id": app_id}
            )


class AccessReviewStatusCalculator(KPICalculator):
    """Calculates periodic access review status KPI."""

    def compute(self, data: pd.DataFrame, app_id: str) -> KPIRecord:
        """Count accounts overdue for access review."""
        try:
            app_data = data[data["app_id"] == app_id].copy()

            overdue_count = 0
            if "last_review_date" in app_data.columns:
                # Convert to datetime
                app_data["last_review_date"] = pd.to_datetime(app_data["last_review_date"], errors='coerce')
                
                # Consider reviews overdue if older than 90 days
                cutoff_date = self.clock.now() - timedelta(days=90)
                
                # Count active accounts with overdue reviews
                if "status" in app_data.columns:
                    overdue_accounts = app_data[
                        (app_data["status"] == "active") &
                        (app_data["last_review_date"].notna()) &
                        (app_data["last_review_date"] < cutoff_date)
                    ]
                else:
                    # Fallback: just check review date
                    overdue_accounts = app_data[
                        (app_data["last_review_date"].notna()) &
                        (app_data["last_review_date"] < cutoff_date)
                    ]
                
                overdue_count = len(overdue_accounts)

            kpi = KPIRecord(
                app_id=app_id,
                kpi_name="access_reviews",
                value=float(overdue_count),
                computed_at=self.clock.now()
            )

            self.storage.persist_kpi(kpi)
            return kpi

        except Exception as e:
            raise ProcessingError(
                message=f"Failed to compute access_reviews: {str(e)}",
                context={"app_id": app_id}
            )


class PolicyViolationsCalculator(KPICalculator):
    """Calculates policy violations KPI."""

    def compute(self, data: pd.DataFrame, app_id: str) -> KPIRecord:
        """Count policy violations based on various rules."""
        try:
            app_data = data[data["app_id"] == app_id].copy()

            violation_count = 0
            
            # Rule 1: Users with excessive failed attempts (>10)
            if "failed_attempts" in app_data.columns:
                excessive_failures = len(app_data[app_data["failed_attempts"] > 10])
                violation_count += excessive_failures
            
            # Rule 2: Privileged accounts without recent review
            if "is_privileged" in app_data.columns and "last_review_date" in app_data.columns:
                app_data["last_review_date"] = pd.to_datetime(app_data["last_review_date"], errors='coerce')
                cutoff_date = self.clock.now() - timedelta(days=30)
                
                privileged_without_review = len(app_data[
                    (app_data["is_privileged"] == True) &
                    (app_data["last_review_date"].notna()) &
                    (app_data["last_review_date"] < cutoff_date)
                ])
                violation_count += privileged_without_review
            
            # Rule 3: Active accounts with exit dates (orphan accounts)
            if "status" in app_data.columns and "exit_date" in app_data.columns:
                orphan_accounts = len(app_data[
                    (app_data["status"] == "active") &
                    (app_data["exit_date"].notna()) &
                    (app_data["exit_date"] != "")
                ])
                violation_count += orphan_accounts

            kpi = KPIRecord(
                app_id=app_id,
                kpi_name="policy_violations",
                value=float(violation_count),
                computed_at=self.clock.now()
            )

            self.storage.persist_kpi(kpi)
            return kpi

        except Exception as e:
            raise ProcessingError(
                message=f"Failed to compute policy_violations: {str(e)}",
                context={"app_id": app_id}
            )


class ExcessivePermissionsCalculator(KPICalculator):
    """Calculates excessive permissions KPI."""

    def compute(self, data: pd.DataFrame, app_id: str) -> KPIRecord:
        """Count users with excessive permissions."""
        try:
            app_data = data[data["app_id"] == app_id].copy()

            excessive_count = 0
            
            # Rule 1: Count privileged users in non-production apps
            if "is_privileged" in app_data.columns and "environment" in app_data.columns:
                privileged_in_non_prod = len(app_data[
                    (app_data["is_privileged"] == True) &
                    (~app_data["environment"].isin(["PROD", "PRODUCTION"]))
                ])
                excessive_count += privileged_in_non_prod
            
            # Rule 2: Count users with multiple high-level roles
            if "role" in app_data.columns and "user_id" in app_data.columns:
                high_privilege_roles = ["ADMIN", "SUPERUSER", "ROOT", "DBA"]
                users_with_high_roles = app_data[app_data["role"].isin(high_privilege_roles)]
                
                # Count users appearing multiple times with high privilege roles
                role_counts = users_with_high_roles.groupby("user_id")["role"].count()
                multiple_high_roles = len(role_counts[role_counts > 1])
                excessive_count += multiple_high_roles
            
            # Rule 3: Count privileged accounts without justification
            if "is_privileged" in app_data.columns and "justification" in app_data.columns:
                privileged_without_justification = len(app_data[
                    (app_data["is_privileged"] == True) &
                    ((app_data["justification"].isna()) | (app_data["justification"] == ""))
                ])
                excessive_count += privileged_without_justification

            kpi = KPIRecord(
                app_id=app_id,
                kpi_name="excessive_permissions",
                value=float(excessive_count),
                computed_at=self.clock.now()
            )

            self.storage.persist_kpi(kpi)
            return kpi

        except Exception as e:
            raise ProcessingError(
                message=f"Failed to compute excessive_permissions: {str(e)}",
                context={"app_id": app_id}
            )


class DormantAccountsCalculator(KPICalculator):
    """Calculates dormant accounts KPI."""

    def compute(self, data: pd.DataFrame, app_id: str) -> KPIRecord:
        """Count accounts that have been inactive for too long."""
        try:
            app_data = data[data["app_id"] == app_id].copy()

            dormant_count = 0
            
            # Rule 1: Accounts with no recent login (older than 90 days)
            if "last_login_date" in app_data.columns:
                app_data["last_login_date"] = pd.to_datetime(app_data["last_login_date"], errors='coerce')
                cutoff_date = self.clock.now() - timedelta(days=90)
                
                if "status" in app_data.columns:
                    dormant_accounts = app_data[
                        (app_data["status"] == "active") &
                        (app_data["last_login_date"].notna()) &
                        (app_data["last_login_date"] < cutoff_date)
                    ]
                else:
                    # Fallback: just check login date
                    dormant_accounts = app_data[
                        (app_data["last_login_date"].notna()) &
                        (app_data["last_login_date"] < cutoff_date)
                    ]
                
                dormant_count += len(dormant_accounts)
            
            # Rule 2: Accounts created but never logged in
            if "account_created_date" in app_data.columns and "last_login_date" in app_data.columns:
                app_data["account_created_date"] = pd.to_datetime(app_data["account_created_date"], errors='coerce')
                app_data["last_login_date"] = pd.to_datetime(app_data["last_login_date"], errors='coerce')
                
                never_logged_in = app_data[
                    (app_data["account_created_date"].notna()) &
                    (app_data["last_login_date"].isna())
                ]
                
                # Only count if created more than 7 days ago
                creation_cutoff = self.clock.now() - timedelta(days=7)
                never_logged_in_old = never_logged_in[
                    never_logged_in["account_created_date"] < creation_cutoff
                ]
                
                dormant_count += len(never_logged_in_old)

            kpi = KPIRecord(
                app_id=app_id,
                kpi_name="dormant_accounts",
                value=float(dormant_count),
                computed_at=self.clock.now()
            )

            self.storage.persist_kpi(kpi)
            return kpi

        except Exception as e:
            raise ProcessingError(
                message=f"Failed to compute dormant_accounts: {str(e)}",
                context={"app_id": app_id}
            )