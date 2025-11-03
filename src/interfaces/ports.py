"""
Port Interfaces for UAM Compliance Intelligence System.

Defines abstract interfaces for all external dependencies to enable
dependency inversion, testability, and adapter swapping.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List
from .dto import Alert, AuditEvent, DeliveryResult, KPIRecord, Violation


class SlackSender(ABC):
    """
    Port for Slack alert delivery.

    Implementations must handle authentication, retry logic, rate limiting,
    and channel-based routing.

    Example usage:
        slack = SlackAdapter(bot_token="xoxb-...")
        result = slack.send(alert)
        if result.success:
            print(f"Alert delivered to Slack at {result.delivered_at}")
    """

    @abstractmethod
    def send(self, alert: Alert) -> DeliveryResult:
        """
        Send alert to Slack channel based on severity.

        Args:
            alert: Alert DTO containing message and routing info

        Returns:
            DeliveryResult with success status and retry count

        Raises:
            IntegrationError: If delivery fails after retries
        """
        pass


class EmailSender(ABC):
    """
    Port for email alert delivery.

    Supports both individual alerts and digest mode for batching.

    Example usage:
        email = EmailAdapter(smtp_host="smtp.example.com", ...)
        result = email.send(alert)
    """

    @abstractmethod
    def send(self, alert: Alert) -> DeliveryResult:
        """
        Send alert via email to configured recipients.

        Args:
            alert: Alert DTO with recipient routing based on persona

        Returns:
            DeliveryResult with delivery status

        Raises:
            IntegrationError: If SMTP delivery fails after retries
        """
        pass

    @abstractmethod
    def send_digest(self, alerts: List[Alert]) -> DeliveryResult:
        """
        Send batched digest of alerts.

        Used for MEDIUM/LOW severity alerts to reduce email volume.

        Args:
            alerts: List of alerts to batch in single email

        Returns:
            DeliveryResult for digest delivery
        """
        pass


class OpenAIClient(ABC):
    """
    Port for AI analysis via OpenAI API.

    Abstracts LangChain and OpenAI SDK details to enable testing
    with mock implementations.

    Example usage:
        openai = OpenAIAdapter(api_key="sk-...")
        analysis = openai.analyze(prompt="Analyze KPI spike", max_tokens=500)
    """

    @abstractmethod
    def analyze(self, prompt: str, max_tokens: int) -> str:
        """
        Generate AI analysis for given prompt.

        Args:
            prompt: Text prompt describing analysis task
            max_tokens: Maximum tokens in response

        Returns:
            Generated analysis text

        Raises:
            IntegrationError: If API call fails after retries
        """
        pass

    @abstractmethod
    def get_token_count(self, text: str) -> int:
        """
        Count tokens in text for cost estimation.

        Args:
            text: Text to analyze

        Returns:
            Token count using OpenAI's tokenizer
        """
        pass


class Storage(ABC):
    """
    Port for persistent storage.

    Supports both file-based (JSON Lines) and database (PostgreSQL)
    implementations.

    Example usage:
        storage = JsonlStorage(directory="./data")
        storage.persist_kpi(kpi_record)
    """

    @abstractmethod
    def persist_kpi(self, kpi: KPIRecord) -> None:
        """
        Persist KPI record to storage.

        Args:
            kpi: KPIRecord DTO to persist
        """
        pass

    @abstractmethod
    def persist_violation(self, violation: Violation) -> None:
        """
        Persist violation record to storage.

        Args:
            violation: Violation DTO to persist
        """
        pass

    @abstractmethod
    def persist_alert(self, alert: Alert) -> None:
        """
        Persist alert record to storage.

        Args:
            alert: Alert DTO to persist
        """
        pass

    @abstractmethod
    def query_violations(self, app_id: str, state: str) -> List[Violation]:
        """
        Query violations by application and state.

        Args:
            app_id: Application identifier
            state: Violation state (NEW/RECURRING/RESOLVED)

        Returns:
            List of matching violations
        """
        pass


class AuditLogger(ABC):
    """
    Port for audit logging.

    All processing and alert events must be logged for compliance.

    Example usage:
        logger = StructlogAuditLogger()
        logger.log(AuditEvent(
            event_type="kpi_computed",
            timestamp=datetime.now(),
            details={"app_id": "APP-123", "kpi": "orphan_accounts"}
        ))
    """

    @abstractmethod
    def log(self, event: AuditEvent) -> None:
        """
        Log audit event.

        Args:
            event: AuditEvent DTO with event type and details
        """
        pass


class Clock(ABC):
    """
    Port for time source.

    Enables deterministic time in tests by injecting fixed clock.

    Example usage:
        # Production
        clock = SystemClock()

        # Testing
        clock = FixedClock(datetime(2025, 11, 2, 9, 0))
    """

    @abstractmethod
    def now(self) -> datetime:
        """
        Get current timestamp.

        Returns:
            Current datetime
        """
        pass
