"""
Encrypted storage adapter for data at rest protection.
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

from ...interfaces.dto import KPIRecord, Violation, Alert, AuditEvent
from ...interfaces.ports import Storage
from ...interfaces.errors import StorageError, ConfigurationError


class EncryptedStorage:
    """
    Encrypted storage adapter using AES-256 encryption.
    
    Provides encryption at rest for sensitive compliance data.
    Uses PBKDF2 key derivation with Fernet symmetric encryption.
    """

    def __init__(self, base_path: str, encryption_key: Optional[str] = None):
        """
        Initialize encrypted storage.
        
        Args:
            base_path: Directory for encrypted files
            encryption_key: Base64 encoded key (generates if None)
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize encryption
        if encryption_key:
            self.fernet = Fernet(encryption_key.encode())
            self.key_source = "provided"
        else:
            self.fernet, self.key_data = self._generate_key()
            self.key_source = "generated"
        
        self._validate_encryption()

    def _generate_key(self) -> tuple[Fernet, Dict[str, Any]]:
        """Generate new encryption key."""
        # Generate random salt
        salt = os.urandom(16)
        
        # Derive key from password (in production, use secure key management)
        password = b"uam-encryption-key-2025"  # TODO: Move to secure vault
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))
        
        fernet = Fernet(key)
        
        # Store key metadata for recovery
        key_data = {
            "salt": base64.b64encode(salt).decode(),
            "iterations": 100000,
            "algorithm": "PBKDF2-HMAC-SHA256",
            "created_at": datetime.now().isoformat()
        }
        
        # Save key metadata (separate from encrypted data)
        key_file = self.base_path / ".encryption_key"
        with open(key_file, 'w') as f:
            json.dump(key_data, f, indent=2)
        
        return fernet, key_data

    def _validate_encryption(self):
        """Validate encryption is working."""
        try:
            test_data = b"test_encryption_validation"
            encrypted = self.fernet.encrypt(test_data)
            decrypted = self.fernet.decrypt(encrypted)
            
            if decrypted != test_data:
                raise ConfigurationError(
                    message="Encryption validation failed",
                    context={"component": "EncryptedStorage"}
                )
        except Exception as e:
            raise ConfigurationError(
                message=f"Encryption setup error: {str(e)}",
                context={"component": "EncryptedStorage"}
            )

    def _encrypt_data(self, data: str) -> bytes:
        """Encrypt string data."""
        try:
            return self.fernet.encrypt(data.encode())
        except Exception as e:
            raise StorageError(
                message=f"Data encryption failed: {str(e)}",
                context={"operation": "encrypt"}
            )

    def _decrypt_data(self, encrypted_data: bytes) -> str:
        """Decrypt bytes to string."""
        try:
            return self.fernet.decrypt(encrypted_data).decode()
        except Exception as e:
            raise StorageError(
                message=f"Data decryption failed: {str(e)}",
                context={"operation": "decrypt"}
            )

    def _get_file_path(self, data_type: str, identifier: str) -> Path:
        """Get encrypted file path for data type."""
        filename = f"{data_type}_{identifier}.enc"
        return self.base_path / filename

    def save_kpi(self, kpi: KPIRecord) -> None:
        """Save encrypted KPI record."""
        try:
            file_path = self._get_file_path("kpi", kpi.app_id)
            
            # Serialize and encrypt
            kpi_data = kpi.model_dump_json()
            encrypted_data = self._encrypt_data(kpi_data)
            
            # Write encrypted data
            with open(file_path, 'wb') as f:
                f.write(encrypted_data)
                
        except Exception as e:
            raise StorageError(
                message=f"Failed to save KPI: {str(e)}",
                context={"app_id": str(kpi.app_id), "operation": "save_kpi"}
            )

    def load_kpis(self, app_id: Optional[str] = None) -> List[KPIRecord]:
        """Load and decrypt KPI records."""
        try:
            kpis = []
            
            if app_id:
                # Load specific app KPIs
                file_path = self._get_file_path("kpi", app_id)
                if file_path.exists():
                    with open(file_path, 'rb') as f:
                        encrypted_data = f.read()
                    
                    decrypted_data = self._decrypt_data(encrypted_data)
                    kpi = KPIRecord.model_validate_json(decrypted_data)
                    kpis.append(kpi)
            else:
                # Load all KPIs
                for file_path in self.base_path.glob("kpi_*.enc"):
                    with open(file_path, 'rb') as f:
                        encrypted_data = f.read()
                    
                    decrypted_data = self._decrypt_data(encrypted_data)
                    kpi = KPIRecord.model_validate_json(decrypted_data)
                    kpis.append(kpi)
            
            return kpis
            
        except Exception as e:
            raise StorageError(
                message=f"Failed to load KPIs: {str(e)}",
                context={"app_id": str(app_id) if app_id else "all", "operation": "load_kpis"}
            )

    def save_violation(self, violation: Violation) -> None:
        """Save encrypted violation record."""
        try:
            file_path = self._get_file_path("violation", violation.violation_id)
            
            # Serialize and encrypt
            violation_data = violation.model_dump_json()
            encrypted_data = self._encrypt_data(violation_data)
            
            # Write encrypted data
            with open(file_path, 'wb') as f:
                f.write(encrypted_data)
                
        except Exception as e:
            raise StorageError(
                message=f"Failed to save violation: {str(e)}",
                context={"violation_id": str(violation.violation_id), "operation": "save_violation"}
            )

    def load_violations(self, app_id: Optional[str] = None) -> List[Violation]:
        """Load and decrypt violation records."""
        try:
            violations = []
            
            if app_id:
                # Load specific app violations
                for file_path in self.base_path.glob(f"violation_*_{app_id}.enc"):
                    with open(file_path, 'rb') as f:
                        encrypted_data = f.read()
                    
                    decrypted_data = self._decrypt_data(encrypted_data)
                    violation = Violation.model_validate_json(decrypted_data)
                    violations.append(violation)
            else:
                # Load all violations
                for file_path in self.base_path.glob("violation_*.enc"):
                    with open(file_path, 'rb') as f:
                        encrypted_data = f.read()
                    
                    decrypted_data = self._decrypt_data(encrypted_data)
                    violation = Violation.model_validate_json(decrypted_data)
                    violations.append(violation)
            
            return violations
            
        except Exception as e:
            raise StorageError(
                message=f"Failed to load violations: {str(e)}",
                context={"app_id": str(app_id) if app_id else "all", "operation": "load_violations"}
            )

    def save_alert(self, alert: Alert) -> None:
        """Save encrypted alert record."""
        try:
            file_path = self._get_file_path("alert", alert.alert_id)
            
            # Serialize and encrypt
            alert_data = alert.model_dump_json()
            encrypted_data = self._encrypt_data(alert_data)
            
            # Write encrypted data
            with open(file_path, 'wb') as f:
                f.write(encrypted_data)
                
        except Exception as e:
            raise StorageError(
                message=f"Failed to save alert: {str(e)}",
                context={"alert_id": str(alert.alert_id), "operation": "save_alert"}
            )

    def load_alerts(self, app_id: Optional[str] = None) -> List[Alert]:
        """Load and decrypt alert records."""
        try:
            alerts = []
            
            if app_id:
                # Load specific app alerts
                for file_path in self.base_path.glob(f"alert_*_{app_id}.enc"):
                    with open(file_path, 'rb') as f:
                        encrypted_data = f.read()
                    
                    decrypted_data = self._decrypt_data(encrypted_data)
                    alert = Alert.model_validate_json(decrypted_data)
                    alerts.append(alert)
            else:
                # Load all alerts
                for file_path in self.base_path.glob("alert_*.enc"):
                    with open(file_path, 'rb') as f:
                        encrypted_data = f.read()
                    
                    decrypted_data = self._decrypt_data(encrypted_data)
                    alert = Alert.model_validate_json(decrypted_data)
                    alerts.append(alert)
            
            return alerts
            
        except Exception as e:
            raise StorageError(
                message=f"Failed to load alerts: {str(e)}",
                context={"app_id": str(app_id) if app_id else "all", "operation": "load_alerts"}
            )

    def save_audit_event(self, event: AuditEvent) -> None:
        """Save encrypted audit event."""
        try:
            # Generate unique filename from timestamp and event type
            event_id = f"{event.timestamp.strftime('%Y%m%d_%H%M%S')}_{event.event_type}"
            file_path = self._get_file_path("audit", event_id)
            
            # Serialize and encrypt
            event_data = event.model_dump_json()
            encrypted_data = self._encrypt_data(event_data)
            
            # Write encrypted data
            with open(file_path, 'wb') as f:
                f.write(encrypted_data)
                
        except Exception as e:
            raise StorageError(
                message=f"Failed to save audit event: {str(e)}",
                context={"event_type": str(event.event_type), "operation": "save_audit_event"}
            )

    def load_audit_events(self, app_id: Optional[str] = None, 
                       start_time: Optional[datetime] = None,
                       end_time: Optional[datetime] = None) -> List[AuditEvent]:
        """Load and decrypt audit events with filtering."""
        try:
            events = []
            
            # Load all audit events
            for file_path in self.base_path.glob("audit_*.enc"):
                with open(file_path, 'rb') as f:
                    encrypted_data = f.read()
                
                decrypted_data = self._decrypt_data(encrypted_data)
                event = AuditEvent.model_validate_json(decrypted_data)
                
                # Apply filters - Note: AuditEvent doesn't have app_id field
                # Filter by app_id in details if present
                if app_id:
                    app_id_in_details = event.details.get("app_id")
                    if app_id_in_details and app_id_in_details != app_id:
                        continue
                    
                if start_time and event.timestamp < start_time:
                    continue
                    
                if end_time and event.timestamp > end_time:
                    continue
                
                events.append(event)
            
            # Sort by timestamp
            events.sort(key=lambda e: e.timestamp)
            return events
            
        except Exception as e:
            raise StorageError(
                message=f"Failed to load audit events: {str(e)}",
                context={"app_id": str(app_id) if app_id else "all", "operation": "load_audit_events"}
            )

    def get_encryption_info(self) -> Dict[str, Any]:
        """Get encryption configuration information."""
        key_file = self.base_path / ".encryption_key"
        
        if key_file.exists():
            with open(key_file, 'r') as f:
                key_data = json.load(f)
        else:
            key_data = self.key_data if hasattr(self, 'key_data') else {}
        
        return {
            "encryption_enabled": True,
            "algorithm": "AES-256-GCM (via Fernet)",
            "key_source": self.key_source,
            "key_derivation": key_data.get("algorithm", "Unknown"),
            "key_iterations": key_data.get("iterations", "Unknown"),
            "key_created_at": key_data.get("created_at", "Unknown"),
            "storage_path": str(self.base_path)
        }

    def rotate_encryption_key(self, new_key: Optional[str] = None) -> None:
        """Rotate encryption key and re-encrypt all data."""
        try:
            # Get current data
            current_kpis = self.load_kpis()
            current_violations = self.load_violations()
            current_alerts = self.load_alerts()
            current_events = self.load_audit_events()
            
            # Backup current key
            key_file = self.base_path / ".encryption_key"
            if key_file.exists():
                backup_file = self.base_path / f".encryption_key.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                key_file.rename(backup_file)
            
            # Reinitialize with new key
            if new_key:
                self.fernet = Fernet(new_key.encode())
                self.key_source = "rotated_provided"
            else:
                self.fernet, self.key_data = self._generate_key()
                self.key_source = "rotated_generated"
            
            # Re-encrypt and save all data
            for kpi in current_kpis:
                self.save_kpi(kpi)
            
            for violation in current_violations:
                self.save_violation(violation)
            
            for alert in current_alerts:
                self.save_alert(alert)
            
            for event in current_events:
                self.save_audit_event(event)
            
        except Exception as e:
            raise StorageError(
                message=f"Key rotation failed: {str(e)}",
                context={"operation": "rotate_key"}
            )