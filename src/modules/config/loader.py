"""
Configuration Loader for UAM Compliance Intelligence System.

Loads and validates configuration from YAML/JSON files.
"""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from ...interfaces.errors import ConfigurationError
from ...interfaces.dto import Thresholds


class NotificationSettings(BaseModel):
    """Notification channel settings."""
    slack_enabled: bool = False
    slack_bot_token: Optional[str] = None
    slack_channels: Dict[str, str] = Field(default_factory=dict)
    email_enabled: bool = False
    smtp_host: Optional[str] = None
    smtp_port: int = 587
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    email_recipients: Dict[str, list] = Field(default_factory=dict)


class AISettings(BaseModel):
    """AI/OpenAI configuration settings."""
    openai_api_key: Optional[str] = "demo-key"
    model: str = "gpt-4-turbo"
    max_tokens: Dict[str, int] = Field(default_factory=lambda: {
        "gpt-4": 8000,
        "gpt-4-turbo": 128000
    })
    temperature: float = 0.7
    timeout: int = 30


class SystemConfig(BaseModel):
    """Complete system configuration."""
    thresholds: Thresholds
    notifications: NotificationSettings
    ai_settings: AISettings
    storage_type: str = "jsonl"  # jsonl | postgres
    db_url: Optional[str] = None
    log_level: str = "INFO"


class ConfigLoader:
    """
    Loads and validates system configuration from YAML/JSON files.

    Example:
        loader = ConfigLoader(config_dir="./config")
        config = loader.load()
    """

    def __init__(self, config_dir: str = "./config"):
        self.config_dir = Path(config_dir)

    def load(self) -> SystemConfig:
        """
        Load complete system configuration.

        Returns:
            Validated SystemConfig

        Raises:
            ConfigurationError: If configuration is missing or invalid
        """
        try:
            # Load thresholds
            thresholds = self._load_yaml("thresholds.yaml")
            thresholds_obj = Thresholds(alert_thresholds=thresholds.get("alert_thresholds", {}))

            # Load notification settings
            notifications_data = self._load_yaml("notifications.yaml")
            notifications = NotificationSettings(**notifications_data)

            # Load AI settings from environment or config
            import os
            ai_settings = AISettings(
                openai_api_key=os.getenv("OPENAI_API_KEY"),
                model=os.getenv("OPENAI_MODEL", "gpt-4-turbo")
            )

            # Create system config
            config = SystemConfig(
                thresholds=thresholds_obj,
                notifications=notifications,
                ai_settings=ai_settings,
                storage_type=os.getenv("STORAGE_TYPE", "jsonl"),
                db_url=os.getenv("DATABASE_URL"),
                log_level=os.getenv("LOG_LEVEL", "INFO")
            )

            return config

        except Exception as e:
            raise ConfigurationError(
                message=f"Failed to load configuration: {str(e)}",
                context={"config_dir": str(self.config_dir)}
            )

    def _load_yaml(self, filename: str) -> Dict[str, Any]:
        """
        Load YAML file from config directory.

        Args:
            filename: Name of YAML file

        Returns:
            Parsed YAML as dictionary

        Raises:
            ConfigurationError: If file not found or invalid YAML
        """
        filepath = self.config_dir / filename
        if not filepath.exists():
            raise ConfigurationError(
                message=f"Configuration file not found: {filename}",
                context={"filepath": str(filepath)}
            )

        try:
            with open(filepath, "r") as f:
                return yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ConfigurationError(
                message=f"Invalid YAML in {filename}: {str(e)}",
                context={"filepath": str(filepath)}
            )
