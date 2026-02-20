# =============================================================================
# MedeX - Security Service
# =============================================================================
"""
Unified security service façade.

Integrates:
- PII detection and redaction
- Audit trail logging
- Input sanitization
- Rate limiting
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any

from medex.security.audit import AuditTrail, AuditTrailConfig, create_audit_trail
from medex.security.models import (
    AuditEvent,
    AuditEventType,
    PIIDetectionResult,
    RiskLevel,
    SanitizationResult,
    SecurityConfig,
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


logger = logging.getLogger(__name__)


# =============================================================================
# Rate Limiter
# =============================================================================


@dataclass
class RateLimitState:
    """State for rate limiting."""

    requests: list[float] = field(default_factory=list)
    blocked_until: float | None = None


class RateLimiter:
    """Token bucket rate limiter."""

    def __init__(
        self,
        requests_per_minute: int = 60,
        burst: int = 10,
    ) -> None:
        """Initialize rate limiter."""
        self.requests_per_minute = requests_per_minute
        self.burst = burst
        self._window_seconds = 60.0
        self._states: dict[str, RateLimitState] = {}

    def is_allowed(self, key: str) -> tuple[bool, int]:
        """
        Check if request is allowed.

        Args:
            key: Rate limit key (user_id, ip, etc.)

        Returns:
            Tuple of (is_allowed, remaining_requests)
        """
        now = time.time()

        if key not in self._states:
            self._states[key] = RateLimitState()

        state = self._states[key]

        # Check if blocked
        if state.blocked_until and now < state.blocked_until:
            return False, 0

        # Clean old requests
        cutoff = now - self._window_seconds
        state.requests = [t for t in state.requests if t > cutoff]

        # Check limit
        if len(state.requests) >= self.requests_per_minute:
            # Block for remaining window
            state.blocked_until = now + (
                self._window_seconds - (now - state.requests[0])
            )
            return False, 0

        # Allow and record
        state.requests.append(now)
        remaining = self.requests_per_minute - len(state.requests)

        return True, remaining

    def reset(self, key: str) -> None:
        """Reset rate limit for key."""
        if key in self._states:
            del self._states[key]


# =============================================================================
# Security Service
# =============================================================================


@dataclass
class SecurityServiceConfig:
    """Configuration for security service."""

    # Component configs
    pii_config: PIIDetectorConfig | None = None
    audit_config: AuditTrailConfig | None = None
    sanitizer_config: SanitizerConfig | None = None

    # Feature toggles
    enable_pii_detection: bool = True
    enable_audit: bool = True
    enable_sanitization: bool = True
    enable_rate_limiting: bool = True
    enable_medical_validation: bool = True

    # Rate limiting
    rate_limit_per_minute: int = 60
    rate_limit_burst: int = 10

    # Auto-actions
    auto_redact_pii: bool = True
    block_unsafe_input: bool = True


class SecurityService:
    """
    Unified security service.

    Provides a single interface for all security operations.
    """

    def __init__(self, config: SecurityServiceConfig | None = None) -> None:
        """Initialize security service."""
        self.config = config or SecurityServiceConfig()

        # Initialize components
        self._pii_detector: PIIDetector | None = None
        self._audit_trail: AuditTrail | None = None
        self._sanitizer: InputSanitizer | None = None
        self._medical_validator: MedicalInputValidator | None = None
        self._rate_limiter: RateLimiter | None = None

        self._initialize_components()
        logger.info("Security service initialized")

    def _initialize_components(self) -> None:
        """Initialize security components based on config."""
        if self.config.enable_pii_detection:
            self._pii_detector = create_pii_detector(
                self.config.pii_config, medical=True
            )

        if self.config.enable_audit:
            self._audit_trail = create_audit_trail(self.config.audit_config)

        if self.config.enable_sanitization:
            self._sanitizer = create_input_sanitizer(self.config.sanitizer_config)

        if self.config.enable_medical_validation:
            self._medical_validator = create_medical_validator()

        if self.config.enable_rate_limiting:
            self._rate_limiter = RateLimiter(
                self.config.rate_limit_per_minute,
                self.config.rate_limit_burst,
            )

    # -------------------------------------------------------------------------
    # PII Operations
    # -------------------------------------------------------------------------

    def detect_pii(self, text: str) -> PIIDetectionResult:
        """
        Detect PII in text.

        Args:
            text: Text to scan

        Returns:
            PIIDetectionResult
        """
        if not self._pii_detector:
            return PIIDetectionResult(original_text=text, redacted_text=text)

        return self._pii_detector.detect(text)

    def redact_pii(self, text: str) -> str:
        """
        Redact PII from text.

        Args:
            text: Text to redact

        Returns:
            Redacted text
        """
        if not self._pii_detector:
            return text

        return self._pii_detector.redact(text)

    def has_pii(self, text: str) -> bool:
        """Check if text contains PII."""
        if not self._pii_detector:
            return False
        return self._pii_detector.has_pii(text)

    # -------------------------------------------------------------------------
    # Sanitization Operations
    # -------------------------------------------------------------------------

    def sanitize_input(self, text: str) -> SanitizationResult:
        """
        Sanitize user input.

        Args:
            text: Input to sanitize

        Returns:
            SanitizationResult
        """
        if not self._sanitizer:
            return SanitizationResult(
                original_input=text,
                sanitized_input=text,
            )

        return self._sanitizer.sanitize(text)

    def is_input_safe(self, text: str) -> bool:
        """Check if input is safe."""
        if not self._sanitizer:
            return True
        return self._sanitizer.is_safe(text)

    def check_prompt_injection(self, text: str) -> bool:
        """
        Check for prompt injection attempts.

        Returns:
            True if prompt injection detected
        """
        if not self._sanitizer:
            return False

        threats = self._sanitizer.check_prompt_injection(text)
        return len(threats) > 0

    # -------------------------------------------------------------------------
    # Medical Validation
    # -------------------------------------------------------------------------

    def validate_medical_query(self, query: str) -> tuple[bool, str | None]:
        """
        Validate medical query.

        Returns:
            Tuple of (is_valid, rejection_reason)
        """
        if not self._medical_validator:
            return True, None

        return self._medical_validator.validate(query)

    def get_rejection_response(self, reason: str) -> str:
        """Get safe response for rejected query."""
        if not self._medical_validator:
            return "Query not allowed."

        return self._medical_validator.get_safe_response(reason)

    # -------------------------------------------------------------------------
    # Rate Limiting
    # -------------------------------------------------------------------------

    def check_rate_limit(self, key: str) -> tuple[bool, int]:
        """
        Check rate limit.

        Args:
            key: Rate limit key (user_id, ip, etc.)

        Returns:
            Tuple of (is_allowed, remaining_requests)
        """
        if not self._rate_limiter:
            return True, 999

        return self._rate_limiter.is_allowed(key)

    def reset_rate_limit(self, key: str) -> None:
        """Reset rate limit for key."""
        if self._rate_limiter:
            self._rate_limiter.reset(key)

    # -------------------------------------------------------------------------
    # Audit Operations
    # -------------------------------------------------------------------------

    async def audit_log(self, event: AuditEvent) -> None:
        """Log audit event."""
        if self._audit_trail:
            await self._audit_trail.log(event)

    async def audit_query(
        self,
        user_id: str,
        query_text: str,
        session_id: str | None = None,
        ip_address: str | None = None,
    ) -> AuditEvent | None:
        """Log a query event."""
        if not self._audit_trail:
            return None

        return await self._audit_trail.log_query(
            user_id, query_text, session_id, ip_address
        )

    async def audit_pii_detection(
        self,
        user_id: str | None,
        pii_type: str,
        was_redacted: bool = True,
    ) -> AuditEvent | None:
        """Log PII detection event."""
        if not self._audit_trail:
            return None

        return await self._audit_trail.log_pii_detection(
            user_id, pii_type, "detected", was_redacted
        )

    async def audit_security_event(
        self,
        event_type: AuditEventType,
        user_id: str | None = None,
        details: dict[str, Any] | None = None,
        risk_level: RiskLevel = RiskLevel.HIGH,
    ) -> AuditEvent | None:
        """Log security event."""
        if not self._audit_trail:
            return None

        return await self._audit_trail.log_security_event(
            event_type, user_id, None, details, risk_level
        )

    async def get_audit_history(
        self,
        user_id: str,
        days: int = 30,
    ) -> list[AuditEvent]:
        """Get user's audit history."""
        if not self._audit_trail:
            return []

        return await self._audit_trail.get_user_history(user_id, days)

    async def generate_compliance_report(
        self,
        start_date: Any,
        end_date: Any,
    ) -> dict[str, Any]:
        """Generate compliance report."""
        if not self._audit_trail:
            return {"error": "Audit trail not enabled"}

        return await self._audit_trail.generate_compliance_report(start_date, end_date)

    # -------------------------------------------------------------------------
    # Composite Operations
    # -------------------------------------------------------------------------

    async def process_input(
        self,
        text: str,
        user_id: str | None = None,
        session_id: str | None = None,
        ip_address: str | None = None,
    ) -> tuple[str, bool, list[str]]:
        """
        Full input processing pipeline.

        Args:
            text: Input text
            user_id: User identifier
            session_id: Session identifier
            ip_address: Client IP

        Returns:
            Tuple of (processed_text, is_safe, warnings)
        """
        warnings = []
        processed = text
        is_safe = True

        # Rate limiting
        if user_id and self._rate_limiter:
            allowed, remaining = self.check_rate_limit(user_id)
            if not allowed:
                warnings.append("Rate limit exceeded")
                is_safe = False
                if self._audit_trail:
                    await self._audit_trail.log_security_event(
                        AuditEventType.RATE_LIMIT_EXCEEDED,
                        user_id,
                        ip_address,
                    )
                return "[RATE_LIMITED]", False, warnings

        # Sanitization
        if self._sanitizer:
            result = self._sanitizer.sanitize(text)
            if result.was_modified:
                warnings.extend(result.threats_detected)
                if result.risk_level in {RiskLevel.CRITICAL, RiskLevel.HIGH}:
                    is_safe = False
                    if self.config.block_unsafe_input:
                        if self._audit_trail:
                            await self._audit_trail.log_security_event(
                                AuditEventType.INJECTION_BLOCKED,
                                user_id,
                                ip_address,
                                {"threats": result.threats_detected},
                            )
                        return result.sanitized_input, False, warnings
                processed = result.sanitized_input

        # Medical validation
        if self._medical_validator:
            valid, reason = self._medical_validator.validate(processed)
            if not valid:
                warnings.append(f"Medical validation failed: {reason}")
                is_safe = False
                return (
                    self._medical_validator.get_safe_response(reason or ""),
                    False,
                    warnings,
                )

        # PII detection
        if self._pii_detector:
            pii_result = self._pii_detector.detect(processed)
            if pii_result.has_pii:
                warnings.append(f"PII detected: {len(pii_result.entities)} entities")
                if self.config.auto_redact_pii:
                    processed = pii_result.redacted_text
                    for entity in pii_result.entities:
                        if self._audit_trail:
                            await self._audit_trail.log_pii_detection(
                                user_id, entity.type.value
                            )

        # Log the query
        if self._audit_trail and user_id:
            await self._audit_trail.log_query(
                user_id, processed, session_id, ip_address
            )

        return processed, is_safe, warnings

    async def close(self) -> None:
        """Close security service."""
        if self._audit_trail:
            await self._audit_trail.close()


# =============================================================================
# Factory Functions
# =============================================================================


def create_security_service(
    config: SecurityServiceConfig | None = None,
) -> SecurityService:
    """Create security service."""
    return SecurityService(config)
