"""
Email Adapter for UAM Compliance Intelligence System.

Sends alerts via SMTP email.
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List
from ..interfaces.ports import EmailSender
from ..interfaces.dto import Alert, DeliveryResult
from ..interfaces.errors import IntegrationError
from datetime import datetime


class EmailAdapter(EmailSender):
    """
    Email integration using SMTP.

    Example:
        email = EmailAdapter(
            smtp_host="smtp.example.com",
            smtp_port=587,
            username="alerts@example.com",
            password="password"
        )
        result = email.send(alert)
    """

    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        username: str,
        password: str,
        from_address: str = "uam-compliance@example.com"
    ):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.from_address = from_address

    def send(self, alert: Alert) -> DeliveryResult:
        """Send alert via email."""
        retries = 0
        max_retries = 3

        while retries < max_retries:
            try:
                recipients = self._get_recipients(alert)
                self._send_email(alert, recipients)
                return DeliveryResult(
                    success=True,
                    delivered_at=datetime.now(),
                    retries=retries
                )
            except Exception as e:
                retries += 1
                if retries >= max_retries:
                    raise IntegrationError(
                        message=f"Email delivery failed after {max_retries} retries",
                        context={
                            "service": "email",
                            "error": str(e),
                            "retries": str(retries)
                        }
                    )

    def send_digest(self, alerts: List[Alert]) -> DeliveryResult:
        """Send batch of alerts as digest email."""
        try:
            recipients = ["compliance@example.com"]
            subject = f"UAM Compliance Daily Digest ({len(alerts)} alerts)"
            body = self._format_digest(alerts)
            self._send_email_raw(subject, body, recipients)
            return DeliveryResult(
                success=True,
                delivered_at=datetime.now()
            )
        except Exception as e:
            raise IntegrationError(
                message="Email digest delivery failed",
                context={"error": str(e), "count": str(len(alerts))}
            )

    def _get_recipients(self, alert: Alert) -> List[str]:
        """Get email recipients based on persona."""
        if alert.persona == "compliance_officer":
            return ["compliance@example.com"]
        else:
            return [f"owner-{alert.app_id}@example.com"]

    def _send_email(self, alert: Alert, recipients: List[str]) -> None:
        """Send email."""
        subject = f"[{alert.severity.value}] {alert.title}"
        body = self._format_alert(alert)
        self._send_email_raw(subject, body, recipients)

    def _send_email_raw(self, subject: str, body: str, recipients: List[str]) -> None:
        """Send raw email via SMTP."""
        msg = MIMEMultipart()
        msg["From"] = self.from_address
        msg["To"] = ", ".join(recipients)
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "html"))

        with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
            server.starttls()
            server.login(self.username, self.password)
            server.send_message(msg)

    def _format_alert(self, alert: Alert) -> str:
        """Format alert as HTML email."""
        return (
            f"<h2>{alert.title}</h2>"
            f"<p><strong>Application:</strong> {alert.app_id}</p>"
            f"<p><strong>Severity:</strong> {alert.severity.value}</p>"
            f"<p><strong>Risk Score:</strong> {alert.risk_score}/100</p>"
            f"<h3>Description</h3>"
            f"<p>{alert.description}</p>"
            f"<h3>Recommendations</h3>"
            f"<ol>" +
            "".join(f"<li>{r}</li>" for r in alert.recommendations) +
            "</ol>"
        )

    def _format_digest(self, alerts: List[Alert]) -> str:
        """Format digest email."""
        html = "<h2>UAM Compliance Daily Digest</h2><ol>"
        for alert in alerts:
            html += f"<li>{alert.title} ({alert.app_id}) - {alert.severity.value}</li>"
        html += "</ol>"
        return html
