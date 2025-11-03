"""Tests for enhanced audit logger."""

import pytest
import tempfile
import shutil
import json
from datetime import datetime, timedelta
from pathlib import Path

from src.adapters.audit import StructlogAuditLogger
from src.interfaces.dto import AuditEvent


class TestEnhancedAuditLogger:
    """Test enhanced audit logger functionality."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def audit_logger(self, temp_dir):
        """Create audit logger instance."""
        return StructlogAuditLogger(log_dir=temp_dir, enable_file_rotation=False)

    def test_initialization(self, audit_logger, temp_dir):
        """Test audit logger initialization."""
        assert audit_logger.log_dir == Path(temp_dir)
        assert audit_logger.enable_file_rotation is False
        assert (Path(temp_dir) / "audit.log").exists()
        assert (Path(temp_dir) / "security.log").exists()

    def test_log_basic_event(self, audit_logger):
        """Test logging basic audit event."""
        event = AuditEvent(
            event_type="TEST_EVENT",
            timestamp=datetime.now(),
            details={"test_key": "test_value"}
        )
        
        audit_logger.log(event)
        
        # Verify log file contains event
        audit_file = audit_logger.log_dir / "audit.log"
        with open(audit_file, 'r') as f:
            log_content = f.read()
        
        assert "TEST_EVENT" in log_content
        assert "test_value" in log_content

    def test_log_security_event(self, audit_logger):
        """Test logging security events."""
        event = AuditEvent(
            event_type="LOGIN",
            timestamp=datetime.now(),
            details={"user_id": "user123", "source_ip": "192.168.1.1"}
        )
        
        audit_logger.log(event)
        
        # Verify security log file contains event
        security_file = audit_logger.log_dir / "security.log"
        with open(security_file, 'r') as f:
            log_content = f.read()
        
        assert "LOGIN" in log_content
        assert "user123" in log_content
        assert "security_event" in log_content

    def test_log_data_access(self, audit_logger):
        """Test data access logging."""
        audit_logger.log_data_access(
            user_id="user123",
            resource_type="KPI",
            resource_id="APP-123",
            action="READ",
            success=True
        )
        
        audit_trail = audit_logger.get_audit_trail()
        data_access_events = [e for e in audit_trail if e.get('event_type') == 'DATA_ACCESS']
        
        assert len(data_access_events) == 1
        event = data_access_events[0]
        assert event['user_id'] == 'user123'
        assert event['resource_type'] == 'KPI'
        assert event['action'] == 'READ'

    def test_log_configuration_change(self, audit_logger):
        """Test configuration change logging."""
        audit_logger.log_configuration_change(
            user_id="admin",
            component="PolicyEngine",
            setting_name="threshold",
            old_value="5.0",
            new_value="10.0"
        )
        
        audit_trail = audit_logger.get_audit_trail()
        config_events = [e for e in audit_trail if e.get('event_type') == 'CONFIGURATION_CHANGE']
        
        assert len(config_events) == 1
        event = config_events[0]
        assert event['component'] == 'PolicyEngine'
        assert event['old_value'] == '5.0'
        assert event['new_value'] == '10.0'

    def test_log_security_event_method(self, audit_logger):
        """Test security event logging method."""
        audit_logger.log_security_event(
            event_type="ACCESS_DENIED",
            severity="HIGH",
            user_id="user123",
            source_ip="192.168.1.1",
            details={"resource": "/admin", "reason": "insufficient_privileges"}
        )
        
        audit_trail = audit_logger.get_audit_trail()
        security_events = [e for e in audit_trail if e.get('event_type') == 'ACCESS_DENIED']
        
        assert len(security_events) == 1
        event = security_events[0]
        assert event['user_id'] == 'user123'
        assert event['source_ip'] == '192.168.1.1'

    def test_get_audit_trail_with_filters(self, audit_logger):
        """Test audit trail filtering."""
        from datetime import timezone
        now = datetime.now(timezone.utc)
        old_time = now - timedelta(days=1)
        
        # Create events at different times
        old_event = AuditEvent(
            event_type="OLD_EVENT",
            timestamp=old_time.replace(tzinfo=None),
            details={"test": "old"}
        )
        new_event = AuditEvent(
            event_type="NEW_EVENT",
            timestamp=now.replace(tzinfo=None),
            details={"test": "new"}
        )
        
        audit_logger.log(old_event)
        audit_logger.log(new_event)
        
        # Test time filtering
        recent_trail = audit_logger.get_audit_trail(start_time=now - timedelta(hours=1))
        recent_events = [e for e in recent_trail if e.get('event_type') == 'NEW_EVENT']
        assert len(recent_events) == 1
        
        # Test event type filtering
        filtered_trail = audit_logger.get_audit_trail(event_type="NEW_EVENT")
        assert len(filtered_trail) == 1
        assert filtered_trail[0]['event_type'] == 'NEW_EVENT'

    def test_export_compliance_report(self, audit_logger, temp_dir):
        """Test compliance report export."""
        from datetime import timezone
        now = datetime.now(timezone.utc)
        start_time = now - timedelta(hours=1)
        end_time = now + timedelta(hours=1)
        
        # Create test events
        event = AuditEvent(
            event_type="TEST_EVENT",
            timestamp=now.replace(tzinfo=None),
            details={"test": "data"}
        )
        audit_logger.log(event)
        
        # Export report
        report_file = Path(temp_dir) / "compliance_report.json"
        audit_logger.export_compliance_report(str(report_file), start_time, end_time)
        
        # Verify report structure
        assert report_file.exists()
        with open(report_file, 'r') as f:
            report = json.load(f)
        
        assert "report_metadata" in report
        assert "audit_trail" in report
        assert report["report_metadata"]["total_events"] >= 1
        assert report["report_metadata"]["compliance_standard"] == "UAM-v2.0"

    def test_compliance_metadata_in_logs(self, audit_logger):
        """Test that compliance metadata is added to logs."""
        event = AuditEvent(
            event_type="TEST_EVENT",
            timestamp=datetime.now(),
            details={"test": "data"}
        )
        
        audit_logger.log(event)
        
        audit_trail = audit_logger.get_audit_trail()
        test_events = [e for e in audit_trail if e.get('event_type') == 'TEST_EVENT']
        
        assert len(test_events) == 1
        event_data = test_events[0]
        assert event_data.get('compliance_version') == 'UAM-v2.0'
        assert event_data.get('log_source') == 'uam_compliance_system'
        assert event_data.get('retention_days') == 2555

    def test_startup_event_logged(self, audit_logger):
        """Test that startup event is automatically logged."""
        audit_trail = audit_logger.get_audit_trail()
        startup_events = [e for e in audit_trail if e.get('event_type') == 'SYSTEM_STARTUP']
        
        assert len(startup_events) == 1
        startup_event = startup_events[0]
        assert startup_event['component'] == 'StructlogAuditLogger'

    def test_multiple_security_events(self, audit_logger):
        """Test logging multiple security event types."""
        security_events = [
            ("LOGIN", {"user_id": "user1"}),
            ("AUTHENTICATION", {"user_id": "user2"}),
            ("PRIVILEGE_ESCALATION", {"user_id": "user3"}),
            ("DATA_BREACH", {"severity": "CRITICAL"})
        ]
        
        for event_type, details in security_events:
            event = AuditEvent(
                event_type=event_type,
                timestamp=datetime.now(),
                details=details
            )
            audit_logger.log(event)
        
        # Verify all security events are logged
        audit_trail = audit_logger.get_audit_trail()
        logged_security_events = [
            e for e in audit_trail 
            if e.get('event_type') in [se[0] for se in security_events]
        ]
        
        assert len(logged_security_events) == len(security_events)
        
        # Verify security metadata
        for event in logged_security_events:
            assert event.get('security_event') == 'true'
            assert event.get('severity') == 'HIGH'
            assert event.get('requires_immediate_review') == 'true'