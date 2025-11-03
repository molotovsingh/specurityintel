"""
Composition Root - Dependency Injection Setup.

Wires all adapters and modules together.
"""

from .adapters.clock import SystemClock, FixedClock
from .adapters.audit import StructlogAuditLogger
from .adapters.storage.jsonl import JsonlStorage
from .adapters.storage.in_memory import InMemoryStorage
from .adapters.slack_adapter import SlackAdapter
from .adapters.email_adapter import EmailAdapter
from .adapters.openai_adapter import OpenAIAdapter, MockOpenAIClient
from .modules.config.loader import ConfigLoader, SystemConfig
from .modules.config.validator import ConfigValidator
from .modules.ingestion.parser import CSVParser
from .modules.kpi.calculators import (
    OrphanAccountsCalculator,
    PrivilegedAccountsCalculator,
    FailedAccessAttemptsCalculator,
    AccessProvisioningTimeCalculator,
    AccessReviewStatusCalculator,
    PolicyViolationsCalculator,
    ExcessivePermissionsCalculator,
    DormantAccountsCalculator
)
from .modules.policy.rules import PolicyRuleEngine
from .modules.ai.analyzer import RiskAnalyzer
from .modules.alerting.generator import AlertGenerator
from .interfaces.ports import (
    Clock, Storage, SlackSender, EmailSender, OpenAIClient, AuditLogger
)


class ServiceContainer:
    """
    Service container for dependency injection.

    Example:
        container = ServiceContainer.production()
        alerting = container.alert_generator()
    """

    def __init__(
        self,
        clock: Clock,
        storage: Storage,
        slack: SlackSender,
        email: EmailSender,
        openai: OpenAIClient,
        audit_logger: AuditLogger,
        config: SystemConfig
    ):
        self.clock = clock
        self.storage = storage
        self.slack = slack
        self.email = email
        self.openai = openai
        self.audit_logger = audit_logger
        self.config = config

    @staticmethod
    def production() -> "ServiceContainer":
        """Create production service container."""
        # Load configuration
        loader = ConfigLoader(config_dir="./config")
        config = loader.load()

        # Validate configuration
        validator = ConfigValidator()
        validator.validate(config)

        # Create adapters
        clock = SystemClock()
        audit_logger = StructlogAuditLogger(log_dir="./logs")

        # Storage
        if config.storage_type == "postgres":
            from .adapters.storage.postgres import PostgresStorage
            storage = PostgresStorage(db_url=config.db_url)
        else:
            storage = JsonlStorage(directory="./data")

        # Slack
        if config.notifications.slack_enabled and config.notifications.slack_bot_token:
            slack = SlackAdapter(bot_token=config.notifications.slack_bot_token)
        else:
            slack = SlackAdapter(bot_token="xoxb-mock")

        # Email
        email = EmailAdapter(
            smtp_host=config.notifications.smtp_host or "smtp.mock.com",
            smtp_port=config.notifications.smtp_port,
            username=config.notifications.smtp_username or "mock@mock.com",
            password=config.notifications.smtp_password or "mock"
        )

        # OpenAI
        if config.ai_settings.openai_api_key and config.ai_settings.openai_api_key != "demo-key":
            openai = OpenAIAdapter(
                api_key=config.ai_settings.openai_api_key,
                model=config.ai_settings.model
            )
        else:
            openai = MockOpenAIClient()

        return ServiceContainer(
            clock=clock,
            storage=storage,
            slack=slack,
            email=email,
            openai=openai,
            audit_logger=audit_logger,
            config=config
        )

    @staticmethod
    def test() -> "ServiceContainer":
        """Create test service container with mocks."""
        clock = FixedClock(__import__("datetime").datetime.now())
        storage = InMemoryStorage()
        slack = SlackAdapter(bot_token="xoxb-test")
        email = EmailAdapter(
            smtp_host="smtp.test.com",
            smtp_port=587,
            username="test@test.com",
            password="test"
        )
        openai = MockOpenAIClient()
        audit_logger = StructlogAuditLogger(log_dir="./logs")

        from .modules.config.loader import SystemConfig, NotificationSettings, AISettings
        from .interfaces.dto import Thresholds

        config = SystemConfig(
            thresholds=Thresholds(alert_thresholds={
                "orphan_accounts": {"low": 1, "medium": 3, "high": 5, "critical": 10},
                "privileged_accounts": {"low": 5, "medium": 10, "high": 15, "critical": 20},
                "failed_access_attempts": {"low": 10, "medium": 25, "high": 50, "critical": 100}
            }),
            notifications=NotificationSettings(),
            ai_settings=AISettings()
        )

        return ServiceContainer(
            clock=clock,
            storage=storage,
            slack=slack,
            email=email,
            openai=openai,
            audit_logger=audit_logger,
            config=config
        )

    # Service factory methods

    def csv_parser(self) -> CSVParser:
        return CSVParser(clock=self.clock)

    def orphan_accounts_calculator(self):
        return OrphanAccountsCalculator(storage=self.storage, clock=self.clock)

    def privileged_accounts_calculator(self):
        return PrivilegedAccountsCalculator(storage=self.storage, clock=self.clock)

    def failed_access_calculator(self):
        return FailedAccessAttemptsCalculator(storage=self.storage, clock=self.clock)

    def access_provisioning_time_calculator(self):
        return AccessProvisioningTimeCalculator(storage=self.storage, clock=self.clock)

    def access_review_status_calculator(self):
        return AccessReviewStatusCalculator(storage=self.storage, clock=self.clock)

    def policy_violations_calculator(self):
        return PolicyViolationsCalculator(storage=self.storage, clock=self.clock)

    def excessive_permissions_calculator(self):
        return ExcessivePermissionsCalculator(storage=self.storage, clock=self.clock)

    def dormant_accounts_calculator(self):
        return DormantAccountsCalculator(storage=self.storage, clock=self.clock)

    def policy_engine(self) -> PolicyRuleEngine:
        thresholds = self.config.thresholds.alert_thresholds
        return PolicyRuleEngine(
            storage=self.storage,
            clock=self.clock,
            thresholds=thresholds
        )

    def risk_analyzer(self) -> RiskAnalyzer:
        return RiskAnalyzer(openai_client=self.openai, clock=self.clock)

    def alert_generator(self) -> AlertGenerator:
        return AlertGenerator(
            storage=self.storage,
            slack=self.slack,
            email=self.email,
            clock=self.clock
        )
