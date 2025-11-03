"""Tests for encrypted storage adapter."""

import pytest
import tempfile
import shutil
from datetime import datetime
from pathlib import Path

from src.interfaces.dto import KPIRecord, Violation, Alert, AuditEvent, Severity
from src.adapters.storage.encrypted import EncryptedStorage
from src.interfaces.errors import StorageError


class TestEncryptedStorage:
    """Test encrypted storage functionality."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def encrypted_storage(self, temp_dir):
        """Create encrypted storage instance."""
        return EncryptedStorage(temp_dir)

    @pytest.fixture
    def sample_kpi(self):
        """Create sample KPI record."""
        return KPIRecord(
            app_id="APP-123",
            kpi_name="orphan_accounts",
            value=5.0,
            computed_at=datetime.now()
        )

    @pytest.fixture
    def sample_violation(self):
        """Create sample violation."""
        return Violation(
            violation_id="V-001",
            app_id="APP-123",
            rule_id="RULE-001",
            severity=Severity.HIGH,
            kpi_values={"orphan_accounts": 5.0},
            threshold_breached={"orphan_accounts": 3.0},
            evidence={"details": "Too many orphan accounts"},
            detected_at=datetime.now()
        )

    @pytest.fixture
    def sample_alert(self):
        """Create sample alert."""
        return Alert(
            alert_id="A-001",
            app_id="APP-123",
            severity=Severity.HIGH,
            risk_score=85.0,
            violation_ids=["V-001"],
            title="High Risk: Orphan Accounts",
            description="Application has excessive orphan accounts",
            recommendations=["Review user access", "Clean up inactive accounts", "Implement automated cleanup"],
            created_at=datetime.now(),
            persona="compliance_officer"
        )

    @pytest.fixture
    def sample_audit_event(self):
        """Create sample audit event."""
        return AuditEvent(
            event_type="KPI_COMPUTED",
            timestamp=datetime.now(),
            details={"app_id": "APP-123", "kpi_name": "orphan_accounts", "value": "5.0"}
        )

    def test_initialization_with_generated_key(self, temp_dir):
        """Test storage initialization with generated key."""
        storage = EncryptedStorage(temp_dir)
        
        assert storage.fernet is not None
        assert storage.key_source == "generated"
        assert (Path(temp_dir) / ".encryption_key").exists()

    def test_initialization_with_provided_key(self, temp_dir):
        """Test storage initialization with provided key."""
        from cryptography.fernet import Fernet
        key = Fernet.generate_key().decode()
        
        storage = EncryptedStorage(temp_dir, key)
        
        assert storage.fernet is not None
        assert storage.key_source == "provided"

    def test_save_and_load_kpi(self, encrypted_storage, sample_kpi):
        """Test saving and loading KPI records."""
        # Save KPI
        encrypted_storage.save_kpi(sample_kpi)
        
        # Load KPI
        loaded_kpis = encrypted_storage.load_kpis(app_id="APP-123")
        
        assert len(loaded_kpis) == 1
        loaded_kpi = loaded_kpis[0]
        assert loaded_kpi.app_id == sample_kpi.app_id
        assert loaded_kpi.kpi_name == sample_kpi.kpi_name
        assert loaded_kpi.value == sample_kpi.value

    def test_save_and_load_violation(self, encrypted_storage, sample_violation):
        """Test saving and loading violation records."""
        # Save violation
        encrypted_storage.save_violation(sample_violation)
        
        # Load violation
        loaded_violations = encrypted_storage.load_violations()
        
        assert len(loaded_violations) == 1
        loaded_violation = loaded_violations[0]
        assert loaded_violation.violation_id == sample_violation.violation_id
        assert loaded_violation.app_id == sample_violation.app_id
        assert loaded_violation.severity == sample_violation.severity

    def test_save_and_load_alert(self, encrypted_storage, sample_alert):
        """Test saving and loading alert records."""
        # Save alert
        encrypted_storage.save_alert(sample_alert)
        
        # Load alert
        loaded_alerts = encrypted_storage.load_alerts()
        
        assert len(loaded_alerts) == 1
        loaded_alert = loaded_alerts[0]
        assert loaded_alert.alert_id == sample_alert.alert_id
        assert loaded_alert.app_id == sample_alert.app_id
        assert loaded_alert.severity == sample_alert.severity

    def test_save_and_load_audit_event(self, encrypted_storage, sample_audit_event):
        """Test saving and loading audit events."""
        # Save audit event
        encrypted_storage.save_audit_event(sample_audit_event)
        
        # Load audit events
        loaded_events = encrypted_storage.load_audit_events()
        
        assert len(loaded_events) == 1
        loaded_event = loaded_events[0]
        assert loaded_event.event_type == sample_audit_event.event_type
        assert loaded_event.details == sample_audit_event.details

    def test_encryption_info(self, encrypted_storage):
        """Test getting encryption information."""
        info = encrypted_storage.get_encryption_info()
        
        assert info["encryption_enabled"] is True
        assert "AES-256" in info["algorithm"]
        assert info["key_source"] in ["generated", "provided"]
        assert "storage_path" in info

    def test_key_rotation(self, encrypted_storage, sample_kpi):
        """Test encryption key rotation."""
        # Save initial data
        encrypted_storage.save_kpi(sample_kpi)
        
        # Rotate key
        encrypted_storage.rotate_encryption_key()
        
        # Verify data can still be loaded
        loaded_kpis = encrypted_storage.load_kpis(app_id="APP-123")
        assert len(loaded_kpis) == 1
        assert loaded_kpis[0].app_id == sample_kpi.app_id

    def test_encrypted_files_are_not_human_readable(self, encrypted_storage, sample_kpi, temp_dir):
        """Test that encrypted files cannot be read as plain text."""
        # Save KPI
        encrypted_storage.save_kpi(sample_kpi)
        
        # Try to read encrypted file as text
        encrypted_file = Path(temp_dir) / "kpi_APP-123.enc"
        assert encrypted_file.exists()
        
        with open(encrypted_file, 'rb') as f:
            encrypted_content = f.read()
        
        # Verify content is encrypted (not human-readable JSON)
        assert b'"app_id"' not in encrypted_content
        assert b'"orphan_accounts"' not in encrypted_content

    def test_load_nonexistent_data(self, encrypted_storage):
        """Test loading data that doesn't exist."""
        # Load non-existent KPIs
        kpis = encrypted_storage.load_kpis(app_id="NONEXISTENT")
        assert kpis == []
        
        # Load all KPIs when none exist
        all_kpis = encrypted_storage.load_kpis()
        assert all_kpis == []

    def test_audit_event_filtering(self, encrypted_storage):
        """Test filtering audit events by time range."""
        now = datetime.now()
        old_event = AuditEvent(
            event_type="OLD_EVENT",
            timestamp=datetime(2023, 1, 1),
            details={"test": "old"}
        )
        new_event = AuditEvent(
            event_type="NEW_EVENT",
            timestamp=now,
            details={"test": "new"}
        )
        
        # Save events
        encrypted_storage.save_audit_event(old_event)
        encrypted_storage.save_audit_event(new_event)
        
        # Filter by start time
        filtered_events = encrypted_storage.load_audit_events(
            start_time=datetime(2024, 1, 1)
        )
        assert len(filtered_events) == 1
        assert filtered_events[0].event_type == "NEW_EVENT"