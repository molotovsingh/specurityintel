"""
Mock adapters for testing.
"""

from datetime import datetime
from src.interfaces.dto import Alert, DeliveryResult
from src.interfaces.ports import SlackSender, EmailSender


class InMemorySlackSender(SlackSender):
    """In-memory Slack sender for testing."""
    
    def __init__(self, bot_token: str):
        self.bot_token = bot_token
        self.sent_alerts = []
    
    def send(self, alert: Alert) -> DeliveryResult:
        """Mock send alert."""
        self.sent_alerts.append(alert)
        return DeliveryResult(
            success=True,
            delivered_at=datetime.now(),
            retries=0
        )


class InMemoryEmailSender(EmailSender):
    """In-memory Email sender for testing."""
    
    def __init__(self, smtp_host: str, smtp_port: int, username: str, password: str):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.username = username
        self.sent_alerts = []
    
    def send(self, alert: Alert) -> DeliveryResult:
        """Mock send alert."""
        self.sent_alerts.append(alert)
        return DeliveryResult(
            success=True,
            delivered_at=datetime.now(),
            retries=0
        )
    
    def send_digest(self, alerts: list) -> DeliveryResult:
        """Mock send digest."""
        self.sent_alerts.extend(alerts)
        return DeliveryResult(
            success=True,
            delivered_at=datetime.now(),
            retries=0
        )