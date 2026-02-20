# =============================================================================
# MedeX - Input Sanitization
# =============================================================================
"""
Input sanitization and security validation.

Features:
- Prompt injection prevention
- SQL injection prevention
- Command injection prevention
- XSS prevention
- Path traversal prevention
"""

from __future__ import annotations

import html
import logging
import re
from dataclasses import dataclass, field
from enum import Enum

from medex.security.models import (
    RiskLevel,
    SanitizationResult,
    SanitizationType,
    ThreatDetection,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Threat Patterns
# =============================================================================


class ThreatCategory(Enum):
    """Categories of security threats."""

    PROMPT_INJECTION = "prompt_injection"
    SQL_INJECTION = "sql_injection"
    COMMAND_INJECTION = "command_injection"
    PATH_TRAVERSAL = "path_traversal"
    XSS = "xss"
    JAILBREAK = "jailbreak"


# Prompt injection patterns
PROMPT_INJECTION_PATTERNS: list[tuple[str, str, RiskLevel]] = [
    # Direct instruction override
    (
        r"ignore\s+(all\s+)?(previous|prior|above)\s+(instructions?|prompts?|rules?)",
        "instruction_override",
        RiskLevel.CRITICAL,
    ),
    (
        r"disregard\s+(all\s+)?(previous|prior)\s+(instructions?|prompts?)",
        "instruction_override",
        RiskLevel.CRITICAL,
    ),
    (
        r"forget\s+(everything|all)\s+(you\s+)?(know|learned)",
        "memory_wipe",
        RiskLevel.CRITICAL,
    ),
    # Role manipulation
    (
        r"you\s+are\s+now\s+(a\s+)?(?:different|new|evil|unrestricted)",
        "role_manipulation",
        RiskLevel.HIGH,
    ),
    (
        r"act\s+as\s+(a\s+)?(?:different|unrestricted|jailbroken)",
        "role_manipulation",
        RiskLevel.HIGH,
    ),
    (
        r"pretend\s+(?:you\s+are|to\s+be)\s+(?:a\s+)?(?:different|evil)",
        "role_manipulation",
        RiskLevel.HIGH,
    ),
    # System prompt extraction
    (
        r"(?:show|reveal|display|print|output)\s+(?:your\s+)?(?:system\s+)?prompt",
        "prompt_extraction",
        RiskLevel.HIGH,
    ),
    (
        r"what\s+(?:are|is)\s+your\s+(?:initial\s+)?(?:instructions?|prompt|rules)",
        "prompt_extraction",
        RiskLevel.MEDIUM,
    ),
    # Jailbreak attempts
    (
        r"DAN\s+mode|developer\s+mode|unrestricted\s+mode",
        "jailbreak",
        RiskLevel.CRITICAL,
    ),
    (
        r"bypass\s+(?:your\s+)?(?:safety|content|ethical)\s+(?:filters?|guidelines?)",
        "jailbreak",
        RiskLevel.CRITICAL,
    ),
    # Delimiter manipulation
    (
        r"<\|?(?:system|assistant|user|endof\w+)\|?>",
        "delimiter_injection",
        RiskLevel.HIGH,
    ),
    (r"\[(?:SYSTEM|INST|/INST)\]", "delimiter_injection", RiskLevel.HIGH),
    # Spanish variants
    (
        r"ignora\s+(?:todas?\s+)?(?:las\s+)?instrucciones?\s+anteriores?",
        "instruction_override_es",
        RiskLevel.CRITICAL,
    ),
    (
        r"olvida\s+(?:todo\s+)?lo\s+(?:que\s+)?(?:sabes|aprendiste)",
        "memory_wipe_es",
        RiskLevel.CRITICAL,
    ),
    (
        r"ahora\s+eres\s+(?:un\s+)?(?:diferente|nuevo|malvado)",
        "role_manipulation_es",
        RiskLevel.HIGH,
    ),
]

# SQL injection patterns
SQL_INJECTION_PATTERNS: list[tuple[str, str, RiskLevel]] = [
    (
        r"(?:--|#|;)\s*(?:drop|delete|truncate|alter|update|insert)",
        "sql_command",
        RiskLevel.CRITICAL,
    ),
    (r"'\s*(?:or|and)\s*'?\s*\d+\s*=\s*\d+", "sql_tautology", RiskLevel.HIGH),
    (
        r"(?:union\s+(?:all\s+)?select|select\s+.*\s+from\s+)",
        "sql_union_select",
        RiskLevel.HIGH,
    ),
    (r"exec(?:ute)?\s*\(", "sql_exec", RiskLevel.CRITICAL),
    (r"(?:information_schema|sysobjects|syscolumns)", "sql_metadata", RiskLevel.HIGH),
]

# Command injection patterns
COMMAND_INJECTION_PATTERNS: list[tuple[str, str, RiskLevel]] = [
    (
        r"[;&|`]\s*(?:rm|del|format|shutdown|reboot|kill)",
        "destructive_command",
        RiskLevel.CRITICAL,
    ),
    (r"\$\(.*\)|\`.*\`", "command_substitution", RiskLevel.HIGH),
    (r"(?:^|[;&|])\s*(?:cat|less|more|head|tail)\s+/etc/", "file_read", RiskLevel.HIGH),
    (r"(?:wget|curl)\s+(?:http|ftp)", "remote_fetch", RiskLevel.MEDIUM),
    (r"(?:nc|netcat)\s+-\w*[le]", "reverse_shell", RiskLevel.CRITICAL),
]

# Path traversal patterns
PATH_TRAVERSAL_PATTERNS: list[tuple[str, str, RiskLevel]] = [
    (r"\.\.(?:/|\\)+", "directory_traversal", RiskLevel.HIGH),
    (r"(?:/etc/(?:passwd|shadow|hosts))", "sensitive_file", RiskLevel.CRITICAL),
    (r"(?:C:\\Windows|%SystemRoot%)", "windows_system", RiskLevel.HIGH),
]

# XSS patterns
XSS_PATTERNS: list[tuple[str, str, RiskLevel]] = [
    (r"<script[^>]*>.*?</script>", "script_tag", RiskLevel.HIGH),
    (r"javascript:", "javascript_uri", RiskLevel.HIGH),
    (r"on(?:load|click|error|mouseover)\s*=", "event_handler", RiskLevel.HIGH),
    (r"<iframe[^>]*>", "iframe_injection", RiskLevel.MEDIUM),
]


# =============================================================================
# Configuration
# =============================================================================


@dataclass
class SanitizerConfig:
    """Configuration for input sanitizer."""

    # Enable/disable checks
    check_prompt_injection: bool = True
    check_sql_injection: bool = True
    check_command_injection: bool = True
    check_path_traversal: bool = True
    check_xss: bool = True

    # Actions
    block_on_critical: bool = True
    block_on_high: bool = True
    block_on_medium: bool = False
    sanitize_html: bool = True

    # Limits
    max_input_length: int = 50_000
    max_repeated_chars: int = 100

    # Whitelist
    allowed_html_tags: list[str] = field(
        default_factory=lambda: ["b", "i", "em", "strong"]
    )


# =============================================================================
# Input Sanitizer
# =============================================================================


class InputSanitizer:
    """Input sanitization engine."""

    def __init__(self, config: SanitizerConfig | None = None) -> None:
        """Initialize sanitizer."""
        self.config = config or SanitizerConfig()
        self._compiled_patterns: dict[
            ThreatCategory, list[tuple[re.Pattern, str, RiskLevel]]
        ] = {}
        self._compile_patterns()
        logger.info("Input sanitizer initialized")

    def _compile_patterns(self) -> None:
        """Pre-compile regex patterns."""
        pattern_groups = [
            (ThreatCategory.PROMPT_INJECTION, PROMPT_INJECTION_PATTERNS),
            (ThreatCategory.SQL_INJECTION, SQL_INJECTION_PATTERNS),
            (ThreatCategory.COMMAND_INJECTION, COMMAND_INJECTION_PATTERNS),
            (ThreatCategory.PATH_TRAVERSAL, PATH_TRAVERSAL_PATTERNS),
            (ThreatCategory.XSS, XSS_PATTERNS),
        ]

        for category, patterns in pattern_groups:
            self._compiled_patterns[category] = [
                (re.compile(p, re.IGNORECASE | re.DOTALL), name, risk)
                for p, name, risk in patterns
            ]

    def sanitize(self, text: str) -> SanitizationResult:
        """
        Sanitize input text.

        Args:
            text: Input text to sanitize

        Returns:
            SanitizationResult with sanitized text and threat info
        """
        if not text:
            return SanitizationResult(
                original_input=text,
                sanitized_input=text,
            )

        # Truncate if too long
        if len(text) > self.config.max_input_length:
            text = text[: self.config.max_input_length]

        threats: list[ThreatDetection] = []
        sanitized = text
        was_modified = False
        sanitization_types: list[SanitizationType] = []

        # Check for repeated characters (potential DoS)
        sanitized, repeat_modified = self._check_repeated_chars(sanitized)
        if repeat_modified:
            was_modified = True

        # Run threat detection
        if self.config.check_prompt_injection:
            new_threats = self._detect_threats(
                sanitized, ThreatCategory.PROMPT_INJECTION
            )
            threats.extend(new_threats)
            if new_threats:
                sanitization_types.append(SanitizationType.PROMPT_INJECTION)

        if self.config.check_sql_injection:
            new_threats = self._detect_threats(sanitized, ThreatCategory.SQL_INJECTION)
            threats.extend(new_threats)
            if new_threats:
                sanitization_types.append(SanitizationType.SQL_ESCAPE)

        if self.config.check_command_injection:
            new_threats = self._detect_threats(
                sanitized, ThreatCategory.COMMAND_INJECTION
            )
            threats.extend(new_threats)
            if new_threats:
                sanitization_types.append(SanitizationType.COMMAND_ESCAPE)

        if self.config.check_path_traversal:
            new_threats = self._detect_threats(sanitized, ThreatCategory.PATH_TRAVERSAL)
            threats.extend(new_threats)
            if new_threats:
                sanitization_types.append(SanitizationType.PATH_ESCAPE)

        if self.config.check_xss:
            new_threats = self._detect_threats(sanitized, ThreatCategory.XSS)
            threats.extend(new_threats)

        # Apply HTML escaping if configured
        if self.config.sanitize_html:
            escaped = html.escape(sanitized)
            if escaped != sanitized:
                sanitized = escaped
                was_modified = True
                sanitization_types.append(SanitizationType.HTML_ESCAPE)

        # Determine overall risk
        max_risk = RiskLevel.NONE
        for threat in threats:
            if threat.severity.value < max_risk.value:  # Lower value = higher risk
                max_risk = threat.severity

        # Check if we should block
        should_block = self._should_block(threats)

        if threats:
            logger.warning(
                f"Detected {len(threats)} threats, max risk: {max_risk.value}, "
                f"blocked: {should_block}"
            )

        return SanitizationResult(
            original_input=text,
            sanitized_input=sanitized if not should_block else "[BLOCKED]",
            was_modified=was_modified or bool(threats),
            threats_detected=[t.threat_type for t in threats],
            sanitization_types=sanitization_types,
            risk_level=max_risk,
        )

    def _detect_threats(
        self,
        text: str,
        category: ThreatCategory,
    ) -> list[ThreatDetection]:
        """Detect threats of a specific category."""
        threats = []

        if category not in self._compiled_patterns:
            return threats

        for pattern, name, risk in self._compiled_patterns[category]:
            match = pattern.search(text)
            if match:
                threats.append(
                    ThreatDetection(
                        threat_type=f"{category.value}:{name}",
                        pattern_matched=match.group(),
                        severity=risk,
                        context=text[max(0, match.start() - 20) : match.end() + 20],
                    )
                )

        return threats

    def _check_repeated_chars(self, text: str) -> tuple[str, bool]:
        """Check and fix repeated characters."""
        # Match more than N repeated characters
        pattern = re.compile(r"(.)\1{" + str(self.config.max_repeated_chars) + r",}")

        match = pattern.search(text)
        if match:
            # Replace with max allowed
            replacement = match.group(1) * self.config.max_repeated_chars
            return pattern.sub(replacement, text), True

        return text, False

    def _should_block(self, threats: list[ThreatDetection]) -> bool:
        """Determine if input should be blocked."""
        for threat in threats:
            if threat.severity == RiskLevel.CRITICAL and self.config.block_on_critical:
                return True
            if threat.severity == RiskLevel.HIGH and self.config.block_on_high:
                return True
            if threat.severity == RiskLevel.MEDIUM and self.config.block_on_medium:
                return True
        return False

    def is_safe(self, text: str) -> bool:
        """Quick check if text is safe."""
        result = self.sanitize(text)
        return result.risk_level == RiskLevel.NONE

    def check_prompt_injection(self, text: str) -> list[ThreatDetection]:
        """Check specifically for prompt injection."""
        return self._detect_threats(text, ThreatCategory.PROMPT_INJECTION)

    def escape_for_prompt(self, text: str) -> str:
        """Escape text for safe inclusion in prompts."""
        # Remove potential delimiter injections
        escaped = re.sub(r"<\|[^|]*\|>", "", text)
        escaped = re.sub(r"\[(?:SYSTEM|INST|/INST)\]", "", escaped)

        # Escape angle brackets
        escaped = escaped.replace("<", "＜").replace(">", "＞")

        return escaped


# =============================================================================
# Medical Input Validator
# =============================================================================


class MedicalInputValidator:
    """
    Specialized validator for medical inputs.

    Ensures medical queries are appropriate and safe.
    """

    # Medical-specific blocked patterns
    BLOCKED_MEDICAL_PATTERNS: list[tuple[str, str]] = [
        # Dangerous requests
        (r"(?:cómo|como|how\s+to)\s+(?:suicid|matar|kill)", "self_harm"),
        (r"(?:dosis|dose)\s+(?:letal|mortal|lethal|fatal)", "lethal_dose"),
        (r"(?:fabricar|make|create)\s+(?:droga|drug|veneno|poison)", "drug_synthesis"),
        # Prescription fraud
        (r"(?:falsific|fake|forge)\s+(?:receta|prescription)", "prescription_fraud"),
        # Inappropriate content
        (r"(?:contenido|content)\s+(?:sexual|pornográfico)", "inappropriate_content"),
    ]

    def __init__(self) -> None:
        """Initialize validator."""
        self._compiled_patterns = [
            (re.compile(p, re.IGNORECASE), name)
            for p, name in self.BLOCKED_MEDICAL_PATTERNS
        ]

    def validate(self, query: str) -> tuple[bool, str | None]:
        """
        Validate medical query.

        Args:
            query: Medical query to validate

        Returns:
            Tuple of (is_valid, rejection_reason)
        """
        for pattern, name in self._compiled_patterns:
            if pattern.search(query):
                logger.warning(f"Medical query blocked: {name}")
                return False, f"Query blocked: {name}"

        return True, None

    def get_safe_response(self, rejection_reason: str) -> str:
        """Get safe response for blocked query."""
        if "self_harm" in rejection_reason:
            return (
                "Si estás pasando por un momento difícil, por favor contacta una "
                "línea de crisis o emergencias. Tu vida es valiosa y hay ayuda disponible."
            )

        return (
            "Lo siento, no puedo ayudar con esa consulta. "
            "Por favor reformula tu pregunta o consulta con un profesional de salud."
        )


# =============================================================================
# Factory Functions
# =============================================================================


def create_input_sanitizer(
    config: SanitizerConfig | None = None,
) -> InputSanitizer:
    """Create input sanitizer."""
    return InputSanitizer(config)


def create_medical_validator() -> MedicalInputValidator:
    """Create medical input validator."""
    return MedicalInputValidator()
