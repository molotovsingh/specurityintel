"""
Custom Exception Hierarchy for UAM Compliance Intelligence System.

All domain errors inherit from DomainError base class and include
error codes, messages, and context for debugging.
"""

from datetime import datetime
from typing import Dict, Optional


class DomainError(Exception):
    """
    Base exception for all domain errors.

    All custom exceptions should inherit from this class.
    """

    def __init__(
        self,
        message: str,
        error_code: str,
        context: Optional[Dict[str, str]] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.context = context or {}
        self.timestamp = datetime.now()

    def to_dict(self) -> Dict[str, str]:
        """
        Serialize error for logging or API response.

        Returns:
            Dictionary with error details (no sensitive information)
        """
        return {
            "error_code": self.error_code,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            **self.context
        }

    def __str__(self) -> str:
        return f"[{self.error_code}] {self.message}"


class ValidationError(DomainError):
    """
    Data validation error.

    Raised when input data fails schema validation or business rules.

    Example:
        raise ValidationError(
            message="Invalid KPI value: must be non-negative",
            error_code="INVALID_KPI_VALUE",
            context={"kpi_name": "orphan_accounts", "value": "-5"}
        )
    """

    def __init__(
        self,
        message: str,
        context: Optional[Dict[str, str]] = None
    ):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            context=context
        )


class ConfigurationError(DomainError):
    """
    Configuration error.

    Raised when configuration is missing, invalid, or inconsistent.

    Example:
        raise ConfigurationError(
            message="Missing required config: slack_bot_token",
            context={"config_file": "config/notifications.yaml"}
        )
    """

    def __init__(
        self,
        message: str,
        context: Optional[Dict[str, str]] = None
    ):
        super().__init__(
            message=message,
            error_code="CONFIGURATION_ERROR",
            context=context
        )


class IntegrationError(DomainError):
    """
    External integration error.

    Raised when external service (Slack, Email, OpenAI) fails after retries.

    Example:
        raise IntegrationError(
            message="Slack API failed after 3 retries",
            context={
                "service": "slack",
                "retries": "3",
                "last_error": "rate_limit_exceeded"
            }
        )
    """

    def __init__(
        self,
        message: str,
        context: Optional[Dict[str, str]] = None
    ):
        super().__init__(
            message=message,
            error_code="INTEGRATION_ERROR",
            context=context
        )


class ProcessingError(DomainError):
    """
    Data processing error.

    Raised when KPI computation, AI analysis, or policy evaluation fails.

    Example:
        raise ProcessingError(
            message="Failed to compute KPI: insufficient data",
            context={
                "app_id": "APP-123",
                "kpi_name": "orphan_accounts",
                "reason": "missing_user_data"
            }
        )
    """

    def __init__(
        self,
        message: str,
        context: Optional[Dict[str, str]] = None
    ):
        super().__init__(
            message=message,
            error_code="PROCESSING_ERROR",
            context=context
        )


class StorageError(DomainError):
    """
    Storage operation error.

    Raised when persistence or query operations fail.

    Example:
        raise StorageError(
            message="Failed to write to JSONL file",
            context={
                "file_path": "./data/kpis.jsonl",
                "reason": "permission_denied"
            }
        )
    """

    def __init__(
        self,
        message: str,
        context: Optional[Dict[str, str]] = None
    ):
        super().__init__(
            message=message,
            error_code="STORAGE_ERROR",
            context=context
        )
