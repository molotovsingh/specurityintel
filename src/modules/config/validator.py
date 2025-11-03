"""
Configuration Validator for UAM Compliance Intelligence System.

Validates configuration consistency and completeness.
"""

from ...interfaces.errors import ConfigurationError
from .loader import SystemConfig


class ConfigValidator:
    """
    Validates system configuration for consistency and completeness.

    Example:
        validator = ConfigValidator()
        validator.validate(config)
    """

    def validate(self, config: SystemConfig) -> None:
        """
        Validate system configuration.

        Args:
            config: System configuration to validate

        Raises:
            ConfigurationError: If configuration is invalid or inconsistent
        """
        self._validate_slack(config)
        self._validate_email(config)
        self._validate_ai(config)
        self._validate_storage(config)

    def _validate_slack(self, config: SystemConfig) -> None:
        """Validate Slack configuration."""
        if config.notifications.slack_enabled:
            if not config.notifications.slack_bot_token:
                raise ConfigurationError(
                    message="Slack enabled but bot token not configured",
                    context={"hint": "Set SLACK_BOT_TOKEN environment variable"}
                )

            if not config.notifications.slack_channels:
                raise ConfigurationError(
                    message="Slack enabled but no channels configured",
                    context={"hint": "Configure slack_channels in notifications.yaml"}
                )

    def _validate_email(self, config: SystemConfig) -> None:
        """Validate Email configuration."""
        if config.notifications.email_enabled:
            if not config.notifications.smtp_host:
                raise ConfigurationError(
                    message="Email enabled but SMTP host not configured",
                    context={"hint": "Set SMTP_HOST environment variable"}
                )

    def _validate_ai(self, config: SystemConfig) -> None:
        """Validate AI configuration."""
        if not config.ai_settings.openai_api_key or config.ai_settings.openai_api_key == "demo-key":
            # Allow demo mode - will use mock client
            pass

    def _validate_storage(self, config: SystemConfig) -> None:
        """Validate storage configuration."""
        if config.storage_type == "postgres" and not config.db_url:
            raise ConfigurationError(
                message="PostgreSQL storage selected but DATABASE_URL not configured",
                context={"hint": "Set DATABASE_URL or use storage_type=jsonl"}
            )
