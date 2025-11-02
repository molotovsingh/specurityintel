"""
Audit Logger Adapter for UAM Compliance Intelligence System.

Provides structured audit logging using structlog.
"""

import structlog
from pathlib import Path
from ..interfaces.ports import AuditLogger
from ..interfaces.dto import AuditEvent


class StructlogAuditLogger(AuditLogger):
    """
    Audit logger implementation using structlog.

    Logs to both console and JSONL file for compliance audit trail.

    Example:
        logger = StructlogAuditLogger(log_dir="./logs")
        logger.log(AuditEvent(
            event_type="kpi_computed",
            timestamp=datetime.now(),
            details={"app_id": "APP-123", "kpi": "orphan_accounts"}
        ))
    """

    def __init__(self, log_dir: str = "./logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Configure structlog
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.processors.JSONRenderer()
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )

        self.logger = structlog.get_logger()

    def log(self, event: AuditEvent) -> None:
        """
        Log audit event to structured log.

        Args:
            event: AuditEvent DTO with event type and details
        """
        self.logger.info(
            event.event_type,
            timestamp=event.timestamp.isoformat(),
            **event.details
        )
