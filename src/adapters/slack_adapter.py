"""
Slack Adapter for UAM Compliance Intelligence System.

Sends alerts to Slack using the Slack SDK.
"""

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from ..interfaces.ports import SlackSender
from ..interfaces.dto import Alert, DeliveryResult, Severity
from ..interfaces.errors import IntegrationError
from datetime import datetime


class SlackAdapter(SlackSender):
    """
    Slack integration using slack-sdk library.

    Routes alerts to channels based on severity.

    Example:
        slack = SlackAdapter(bot_token="xoxb-...")
        result = slack.send(alert)
    """

    def __init__(self, bot_token: str):
        self.client = WebClient(token=bot_token)
        self.channel_map = {
            Severity.CRITICAL: "#security-critical",
            Severity.HIGH: "#security-critical",
            Severity.MEDIUM: "#compliance-alerts",
            Severity.LOW: "#compliance-alerts"
        }

    def send(self, alert: Alert) -> DeliveryResult:
        """Send alert to Slack channel."""
        channel = self.channel_map.get(alert.severity, "#compliance-alerts")
        retries = 0
        max_retries = 3

        while retries < max_retries:
            try:
                self.client.chat_postMessage(
                    channel=channel,
                    text=self._format_message(alert)
                )
                return DeliveryResult(
                    success=True,
                    delivered_at=datetime.now(),
                    retries=retries
                )
            except SlackApiError as e:
                retries += 1
                if retries >= max_retries:
                    raise IntegrationError(
                        message=f"Slack delivery failed after {max_retries} retries",
                        context={
                            "service": "slack",
                            "channel": channel,
                            "error": str(e),
                            "retries": str(retries)
                        }
                    )

    def _format_message(self, alert: Alert) -> str:
        """Format alert as Slack message."""
        severity_emoji = {
            Severity.CRITICAL: "🚨",
            Severity.HIGH: "⚠️",
            Severity.MEDIUM: "📊",
            Severity.LOW: "ℹ️"
        }
        emoji = severity_emoji.get(alert.severity, "ℹ️")

        return (
            f"{emoji} *{alert.title}*\n"
            f"App: {alert.app_id}\n"
            f"Severity: {alert.severity.value}\n"
            f"Risk Score: {alert.risk_score}/100\n\n"
            f"{alert.description}\n\n"
            f"*Recommendations:*\n" +
            "\n".join(f"• {r}" for r in alert.recommendations)
        )
