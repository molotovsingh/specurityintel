"""
Alert Generator Module.
"""

from uuid import uuid4
from typing import List
from ...interfaces.dto import Alert, Violation, Severity
from ...interfaces.ports import Storage, SlackSender, EmailSender, Clock
from ...interfaces.errors import ProcessingError


class AlertGenerator:
    """
    Generates and dispatches alerts.

    Example:
        gen = AlertGenerator(storage, slack, email, clock)
        result = gen.generate_and_send(violation)
    """

    def __init__(
        self,
        storage: Storage,
        slack: SlackSender,
        email: EmailSender,
        clock: Clock
    ):
        self.storage = storage
        self.slack = slack
        self.email = email
        self.clock = clock

    def generate_and_send(self, violation: Violation) -> Alert:
        """
        Generate alert from violation and dispatch via Slack/Email.

        Returns generated Alert.
        """
        try:
            # Create alert
            alert = Alert(
                alert_id=str(uuid4()),
                app_id=violation.app_id,
                severity=violation.severity,
                risk_score=self._calculate_risk_score(violation),
                violation_ids=[violation.violation_id],
                title=f"{violation.severity.value} violation in {violation.app_id}",
                description=f"Rule {violation.rule_id} triggered with {list(violation.kpi_values.values())[0]}",
                recommendations=self._get_recommendations(violation),
                created_at=self.clock.now(),
                persona="compliance_officer"
            )

            # Persist alert
            self.storage.persist_alert(alert)

            # Send via Slack
            try:
                self.slack.send(alert)
            except Exception:
                pass  # Continue to email

            # Send via Email
            try:
                self.email.send(alert)
            except Exception:
                pass

            return alert

        except Exception as e:
            raise ProcessingError(
                message=f"Alert generation failed: {str(e)}",
                context={"violation_id": violation.violation_id}
            )

    def _calculate_risk_score(self, violation: Violation) -> float:
        """Calculate risk score from violation."""
        # Simple heuristic based on severity
        scores = {
            Severity.CRITICAL: 90.0,
            Severity.HIGH: 70.0,
            Severity.MEDIUM: 50.0,
            Severity.LOW: 30.0
        }
        return scores.get(violation.severity, 50.0)

    def _get_recommendations(self, violation: Violation) -> List[str]:
        """Get recommendations based on violation."""
        return [
            f"Review {violation.app_id} access policies",
            "Investigate root cause of anomaly",
            "Take remediation action if needed"
        ]
