# =============================================================================
# MedeX - Security Models
# =============================================================================
"""
Security domain models for MedeX.

Features:
- PII entity classification
- Audit event models
- Security configuration
- Risk assessment models
"""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

# =============================================================================
# Enums
# =============================================================================


class PIIType(Enum):
    """Types of Personally Identifiable Information."""

    # Direct identifiers
    FULL_NAME = "full_name"
    DNI = "dni"  # Documento Nacional de Identidad
    PASSPORT = "passport"
    SSN = "ssn"  # Social Security Number
    CURP = "curp"  # México
    RUT = "rut"  # Chile
    CUIL = "cuil"  # Argentina

    # Contact information
    EMAIL = "email"
    PHONE = "phone"
    ADDRESS = "address"

    # Medical identifiers
    MEDICAL_RECORD_NUMBER = "medical_record_number"
    HEALTH_INSURANCE_ID = "health_insurance_id"

    # Financial
    CREDIT_CARD = "credit_card"
    BANK_ACCOUNT = "bank_account"

    # Biometric
    FINGERPRINT = "fingerprint"
    FACIAL_DATA = "facial_data"

    # Other sensitive
    DATE_OF_BIRTH = "date_of_birth"
    IP_ADDRESS = "ip_address"
    GEOLOCATION = "geolocation"


class PIISeverity(Enum):
    """Severity level of PII exposure."""

    CRITICAL = "critical"  # Direct identifier (DNI, passport)
    HIGH = "high"  # Contact info, medical IDs
    MEDIUM = "medium"  # Partial info, DOB
    LOW = "low"  # General location, IP


class AuditEventType(Enum):
    """Types of audit events."""

    # Authentication
    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"
    TOKEN_REFRESH = "token_refresh"

    # Authorization
    ACCESS_GRANTED = "access_granted"
    ACCESS_DENIED = "access_denied"
    PERMISSION_CHANGED = "permission_changed"

    # Data operations
    DATA_READ = "data_read"
    DATA_WRITE = "data_write"
    DATA_DELETE = "data_delete"
    DATA_EXPORT = "data_export"

    # Medical specific
    PATIENT_QUERY = "patient_query"
    DIAGNOSIS_GENERATED = "diagnosis_generated"
    TREATMENT_RECOMMENDED = "treatment_recommended"
    EMERGENCY_DETECTED = "emergency_detected"

    # Security events
    PII_DETECTED = "pii_detected"
    PII_REDACTED = "pii_redacted"
    INJECTION_BLOCKED = "injection_blocked"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"

    # System events
    CONFIG_CHANGED = "config_changed"
    SERVICE_START = "service_start"
    SERVICE_STOP = "service_stop"
    ERROR_OCCURRED = "error_occurred"


class RiskLevel(Enum):
    """Risk level classification."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"


class SanitizationType(Enum):
    """Types of input sanitization."""

    HTML_ESCAPE = "html_escape"
    SQL_ESCAPE = "sql_escape"
    COMMAND_ESCAPE = "command_escape"
    PATH_ESCAPE = "path_escape"
    PROMPT_INJECTION = "prompt_injection"


# =============================================================================
# PII Models
# =============================================================================


@dataclass
class PIIEntity:
    """Detected PII entity."""

    type: PIIType
    value: str
    start_pos: int
    end_pos: int
    confidence: float = 1.0
    severity: PIISeverity = PIISeverity.MEDIUM
    context: str = ""

    @property
    def masked_value(self) -> str:
        """Get masked version of the value."""
        if len(self.value) <= 4:
            return "*" * len(self.value)
        return self.value[:2] + "*" * (len(self.value) - 4) + self.value[-2:]

    @property
    def hash_value(self) -> str:
        """Get SHA-256 hash of the value for logging."""
        return hashlib.sha256(self.value.encode()).hexdigest()[:16]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "type": self.type.value,
            "masked_value": self.masked_value,
            "position": f"{self.start_pos}-{self.end_pos}",
            "confidence": self.confidence,
            "severity": self.severity.value,
        }


@dataclass
class PIIDetectionResult:
    """Result of PII detection scan."""

    original_text: str
    entities: list[PIIEntity] = field(default_factory=list)
    redacted_text: str = ""
    has_pii: bool = False
    risk_level: RiskLevel = RiskLevel.NONE
    scan_time_ms: float = 0.0

    def __post_init__(self) -> None:
        """Calculate derived fields."""
        self.has_pii = len(self.entities) > 0
        if self.entities:
            max_severity = max(e.severity for e in self.entities)
            severity_to_risk = {
                PIISeverity.CRITICAL: RiskLevel.CRITICAL,
                PIISeverity.HIGH: RiskLevel.HIGH,
                PIISeverity.MEDIUM: RiskLevel.MEDIUM,
                PIISeverity.LOW: RiskLevel.LOW,
            }
            self.risk_level = severity_to_risk.get(max_severity, RiskLevel.NONE)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "has_pii": self.has_pii,
            "entity_count": len(self.entities),
            "risk_level": self.risk_level.value,
            "entities": [e.to_dict() for e in self.entities],
            "scan_time_ms": self.scan_time_ms,
        }


# =============================================================================
# Audit Models
# =============================================================================


@dataclass
class AuditEvent:
    """Audit trail event."""

    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: AuditEventType = AuditEventType.DATA_READ
    timestamp: datetime = field(default_factory=datetime.utcnow)

    # Actor information
    user_id: str | None = None
    session_id: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None

    # Resource information
    resource_type: str = ""
    resource_id: str = ""
    action: str = ""

    # Result
    success: bool = True
    error_message: str | None = None

    # Additional context
    metadata: dict[str, Any] = field(default_factory=dict)
    risk_level: RiskLevel = RiskLevel.NONE

    # Compliance
    data_classification: str = "internal"  # public, internal, confidential, restricted
    retention_days: int = 365

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "user_id": self.user_id,
            "session_id": self.session_id,
            "ip_address": self.ip_address,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "action": self.action,
            "success": self.success,
            "error_message": self.error_message,
            "metadata": self.metadata,
            "risk_level": self.risk_level.value,
            "data_classification": self.data_classification,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AuditEvent:
        """Create from dictionary."""
        return cls(
            event_id=data.get("event_id", str(uuid.uuid4())),
            event_type=AuditEventType(data.get("event_type", "data_read")),
            timestamp=(
                datetime.fromisoformat(data["timestamp"])
                if isinstance(data.get("timestamp"), str)
                else data.get("timestamp", datetime.utcnow())
            ),
            user_id=data.get("user_id"),
            session_id=data.get("session_id"),
            ip_address=data.get("ip_address"),
            resource_type=data.get("resource_type", ""),
            resource_id=data.get("resource_id", ""),
            action=data.get("action", ""),
            success=data.get("success", True),
            error_message=data.get("error_message"),
            metadata=data.get("metadata", {}),
            risk_level=RiskLevel(data.get("risk_level", "none")),
        )


@dataclass
class AuditQuery:
    """Query parameters for audit search."""

    user_id: str | None = None
    event_types: list[AuditEventType] | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    resource_type: str | None = None
    resource_id: str | None = None
    success_only: bool | None = None
    risk_levels: list[RiskLevel] | None = None
    limit: int = 100
    offset: int = 0


# =============================================================================
# Sanitization Models
# =============================================================================


@dataclass
class SanitizationResult:
    """Result of input sanitization."""

    original_input: str
    sanitized_input: str
    was_modified: bool = False
    threats_detected: list[str] = field(default_factory=list)
    sanitization_types: list[SanitizationType] = field(default_factory=list)
    risk_level: RiskLevel = RiskLevel.NONE

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "was_modified": self.was_modified,
            "threats_detected": self.threats_detected,
            "sanitization_types": [s.value for s in self.sanitization_types],
            "risk_level": self.risk_level.value,
        }


@dataclass
class ThreatDetection:
    """Detected security threat."""

    threat_type: str
    pattern_matched: str
    severity: RiskLevel
    context: str = ""
    blocked: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "threat_type": self.threat_type,
            "pattern": (
                self.pattern_matched[:50] + "..."
                if len(self.pattern_matched) > 50
                else self.pattern_matched
            ),
            "severity": self.severity.value,
            "blocked": self.blocked,
        }


# =============================================================================
# Security Configuration
# =============================================================================


@dataclass
class SecurityConfig:
    """Security module configuration."""

    # PII Detection
    pii_detection_enabled: bool = True
    pii_auto_redact: bool = True
    pii_log_detections: bool = True
    pii_types_to_detect: list[PIIType] = field(default_factory=lambda: list(PIIType))

    # Audit
    audit_enabled: bool = True
    audit_log_queries: bool = True
    audit_log_responses: bool = False  # May contain sensitive data
    audit_retention_days: int = 365

    # Sanitization
    sanitization_enabled: bool = True
    block_prompt_injection: bool = True
    block_sql_injection: bool = True
    block_command_injection: bool = True

    # Rate limiting
    rate_limit_enabled: bool = True
    rate_limit_requests_per_minute: int = 60
    rate_limit_burst: int = 10

    # Data classification
    default_classification: str = "internal"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "pii_detection_enabled": self.pii_detection_enabled,
            "pii_auto_redact": self.pii_auto_redact,
            "audit_enabled": self.audit_enabled,
            "sanitization_enabled": self.sanitization_enabled,
            "rate_limit_enabled": self.rate_limit_enabled,
            "rate_limit_requests_per_minute": self.rate_limit_requests_per_minute,
        }
