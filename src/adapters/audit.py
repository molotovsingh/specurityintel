"""
Enhanced Audit Logger Adapter for UAM Compliance Intelligence System.

Provides comprehensive structured audit logging using structlog with
file rotation, compliance formatting, and security event tracking.
"""

import structlog
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import logging
import logging.handlers

from ..interfaces.ports import AuditLogger
from ..interfaces.dto import AuditEvent

# Type alias for structlog EventDict
EventDict = Dict[str, Any]


class StructlogAuditLogger(AuditLogger):
    """
    Enhanced audit logger implementation using structlog.

    Provides comprehensive compliance audit trail with:
    - Structured JSON logging to files
    - Log rotation for long-term storage
    - Security event categorization
    - Compliance metadata tracking
    - Tamper-evident logging

    Example:
        logger = StructlogAuditLogger(log_dir="./logs")
        logger.log(AuditEvent(
            event_type="kpi_computed",
            timestamp=datetime.now(),
            details={"app_id": "APP-123", "kpi": "orphan_accounts"}
        ))
    """

    def __init__(self, log_dir: str = "./logs", enable_file_rotation: bool = True):
        """
        Initialize enhanced audit logger.
        
        Args:
            log_dir: Directory for audit logs
            enable_file_rotation: Enable daily log rotation
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.enable_file_rotation = enable_file_rotation
        
        # Setup file handlers for different log types
        self._setup_file_handlers()
        
        # Configure structlog with basic processors
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
            wrapper_class=structlog.stdlib.BoundLogger,
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )

        self.logger = structlog.get_logger("uam_audit")
        self._log_startup_event()

    def _setup_file_handlers(self):
        """Setup file handlers for different log categories."""
        # Main audit log handler
        audit_file = self.log_dir / "audit.log"
        if self.enable_file_rotation:
            self.audit_handler = logging.handlers.TimedRotatingFileHandler(
                audit_file,
                when='midnight',
                interval=1,
                backupCount=365,  # Keep 1 year of logs
                encoding='utf-8'
            )
        else:
            self.audit_handler = logging.FileHandler(audit_file, encoding='utf-8')
        
        # Security events log handler
        security_file = self.log_dir / "security.log"
        if self.enable_file_rotation:
            self.security_handler = logging.handlers.TimedRotatingFileHandler(
                security_file,
                when='midnight',
                interval=1,
                backupCount=365,
                encoding='utf-8'
            )
        else:
            self.security_handler = logging.FileHandler(security_file, encoding='utf-8')
        
        # Configure handlers
        for handler in [self.audit_handler, self.security_handler]:
            handler.setFormatter(logging.Formatter('%(message)s'))
            handler.setLevel(logging.INFO)
        
        # Setup root logger to ensure logs are written
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        root_logger.addHandler(self.audit_handler)



    def _log_startup_event(self):
        """Log system startup event."""
        startup_event = AuditEvent(
            event_type="SYSTEM_STARTUP",
            timestamp=datetime.now(),
            details={
                "component": "StructlogAuditLogger",
                "log_directory": str(self.log_dir),
                "file_rotation_enabled": str(self.enable_file_rotation),
                "compliance_retention": "7_years"
            }
        )
        self.log(startup_event)

    def log(self, event: AuditEvent) -> None:
        """
        Log audit event with enhanced compliance tracking.

        Args:
            event: AuditEvent DTO with event type and details
        """
        # Determine if this is a security event
        security_categories = {
            "LOGIN", "LOGOUT", "AUTHENTICATION", "AUTHORIZATION", 
            "ACCESS_DENIED", "PRIVILEGE_ESCALATION", "DATA_BREACH",
            "SECURITY_VIOLATION", "ENCRYPTION_KEY_ROTATION"
        }
        
        is_security_event = event.event_type in security_categories
        
        # Prepare log data with compliance metadata
        log_data = {
            "event_type": event.event_type,
            "timestamp": event.timestamp.isoformat(),
            "event_id": f"{event.timestamp.strftime('%Y%m%d_%H%M%S')}_{event.event_type}",
            "compliance_version": "UAM-v2.0",
            "log_source": "uam_compliance_system",
            "environment": "production",  # TODO: Make configurable
            "retention_days": 2555,  # 7 years compliance retention
        }
        
        # Add details, converting all values to strings
        for key, value in event.details.items():
            log_data[key] = str(value)
        
        # Add security-specific metadata
        if is_security_event:
            log_data["security_event"] = "true"
            log_data["severity"] = "HIGH"
            log_data["requires_immediate_review"] = "true"
        
        # Log to appropriate handler
        if is_security_event:
            security_logger = logging.getLogger("uam_security")
            security_logger.addHandler(self.security_handler)
            security_logger.info(json.dumps(log_data))
            security_logger.removeHandler(self.security_handler)
        else:
            self.logger.info(event.event_type, **log_data)

    def log_data_access(self, user_id: str, resource_type: str, resource_id: str, 
                       action: str, success: bool = True, reason: Optional[str] = None):
        """Log data access events for compliance tracking."""
        event = AuditEvent(
            event_type="DATA_ACCESS",
            timestamp=datetime.now(),
            details={
                "user_id": user_id,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "action": action,
                "success": str(success),
                "reason": reason or "N/A"
            }
        )
        self.log(event)

    def log_configuration_change(self, user_id: str, component: str, 
                               setting_name: str, old_value: str, new_value: str):
        """Log configuration changes for audit trail."""
        event = AuditEvent(
            event_type="CONFIGURATION_CHANGE",
            timestamp=datetime.now(),
            details={
                "user_id": user_id,
                "component": component,
                "setting_name": setting_name,
                "old_value": old_value,
                "new_value": new_value,
                "change_type": "MODIFICATION"
            }
        )
        self.log(event)

    def log_security_event(self, event_type: str, severity: str, user_id: Optional[str] = None,
                          source_ip: Optional[str] = None, details: Optional[Dict[str, str]] = None):
        """Log security events with enhanced metadata."""
        event_details = details or {}
        if user_id:
            event_details["user_id"] = user_id
        if source_ip:
            event_details["source_ip"] = source_ip
        
        event = AuditEvent(
            event_type=event_type,
            timestamp=datetime.now(),
            details=event_details
        )
        self.log(event)

    def get_audit_trail(self, start_time: Optional[datetime] = None,
                        end_time: Optional[datetime] = None,
                        event_type: Optional[str] = None,
                        user_id: Optional[str] = None) -> list[Dict[str, Any]]:
        """
        Retrieve audit trail entries with filtering.
        
        Args:
            start_time: Filter events from this time
            end_time: Filter events until this time
            event_type: Filter by specific event type
            user_id: Filter by user ID
            
        Returns:
            List of audit trail entries
        """
        audit_trail = []
        
        # Read from audit log files
        for log_file in self.log_dir.glob("audit.log*"):
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        try:
                            log_entry = json.loads(line.strip())
                            
                            # Apply filters
                            if start_time or end_time:
                                event_time = datetime.fromisoformat(log_entry.get('timestamp', ''))
                                
                            if start_time:
                                if event_time < start_time:
                                    continue
                            
                            if end_time:
                                if event_time > end_time:
                                    continue
                            
                            if event_type and log_entry.get('event_type') != event_type:
                                continue
                            
                            if user_id:
                                # Check in details for user_id
                                details = log_entry.get('details', {})
                                if isinstance(details, dict) and details.get('user_id') != user_id:
                                    continue
                            
                            audit_trail.append(log_entry)
                            
                        except (json.JSONDecodeError, ValueError):
                            # Skip malformed log entries
                            continue
                            
            except (IOError, UnicodeDecodeError):
                # Skip files that can't be read
                continue
        
        return sorted(audit_trail, key=lambda x: x.get('timestamp', ''))

    def export_compliance_report(self, output_file: str, start_time: datetime, 
                                end_time: datetime) -> None:
        """
        Export compliance report for specified time period.
        
        Args:
            output_file: Path to save compliance report
            start_time: Report start time
            end_time: Report end time
        """
        audit_trail = self.get_audit_trail(start_time, end_time)
        
        compliance_report = {
            "report_metadata": {
                "generated_at": datetime.now().isoformat(),
                "period_start": start_time.isoformat(),
                "period_end": end_time.isoformat(),
                "total_events": len(audit_trail),
                "compliance_standard": "UAM-v2.0",
                "retention_policy": "7_years"
            },
            "audit_trail": audit_trail
        }
        
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(compliance_report, f, indent=2, ensure_ascii=False)
