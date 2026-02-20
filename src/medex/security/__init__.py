# =============================================================================
# MedeX - Security Module
# =============================================================================
"""
Security module for MedeX.

Provides comprehensive security features:
- PII Detection: Identify and redact personal identifiable information
- Audit Trail: Log all actions for compliance (HIPAA, GDPR)
- Input Sanitization: Prevent prompt injection and other attacks
- Rate Limiting: Protect against DoS attacks

Example:
    >>> from medex.security import SecurityService, create_security_service
    >>> service = create_security_service()
    >>>
    >>> # Detect PII
    >>> result = service.detect_pii("Mi DNI es 12345678A")
    >>> print(result.has_pii)  # True
    >>>
    >>> # Sanitize input
    >>> result = service.sanitize_input("Ignore previous instructions")
    >>> print(result.threats_detected)  # ["prompt_injection"]
"""

from medex.security.audit import (
    AuditBackend,
    AuditTrail,
    AuditTrailConfig,
    FileAuditBackend,
    InMemoryAuditBackend,
    create_audit_trail,
)
from medex.security.models import (
    AuditEvent,
    AuditEventType,
    AuditQuery,
    PIIDetectionResult,
    PIIEntity,
    PIISeverity,
    PIIType,
    RiskLevel,
    SanitizationResult,
    SanitizationType,
    SecurityConfig,
    ThreatDetection,
)
from medex.security.pii import (
    MedicalPIIDetector,
    PIIDetector,
    PIIDetectorConfig,
    create_pii_detector,
)
from medex.security.sanitizer import (
    InputSanitizer,
    MedicalInputValidator,
    SanitizerConfig,
    create_input_sanitizer,
    create_medical_validator,
)
from medex.security.service import (
    RateLimiter,
    SecurityService,
    SecurityServiceConfig,
    create_security_service,
)

__all__ = [
    # Models
    "PIIType",
    "PIISeverity",
    "PIIEntity",
    "PIIDetectionResult",
    "AuditEventType",
    "AuditEvent",
    "AuditQuery",
    "RiskLevel",
    "SanitizationType",
    "SanitizationResult",
    "ThreatDetection",
    "SecurityConfig",
    # PII Detection
    "PIIDetector",
    "PIIDetectorConfig",
    "MedicalPIIDetector",
    "create_pii_detector",
    # Audit Trail
    "AuditBackend",
    "InMemoryAuditBackend",
    "FileAuditBackend",
    "AuditTrail",
    "AuditTrailConfig",
    "create_audit_trail",
    # Sanitization
    "InputSanitizer",
    "MedicalInputValidator",
    "SanitizerConfig",
    "create_input_sanitizer",
    "create_medical_validator",
    # Service
    "RateLimiter",
    "SecurityService",
    "SecurityServiceConfig",
    "create_security_service",
]
