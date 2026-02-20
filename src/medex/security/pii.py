# =============================================================================
# MedeX - PII Detection Engine
# =============================================================================
"""
PII (Personally Identifiable Information) detection engine.

Features:
- Multi-pattern regex detection
- Spanish/Latin American ID formats
- Medical identifier detection
- Confidence scoring
- Auto-redaction
"""

from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass
from typing import Any

from medex.security.models import (
    PIIDetectionResult,
    PIIEntity,
    PIISeverity,
    PIIType,
    RiskLevel,
)


logger = logging.getLogger(__name__)


# =============================================================================
# PII Patterns Database
# =============================================================================

# Spanish/Latin American patterns
PII_PATTERNS: dict[PIIType, dict[str, Any]] = {
    # Direct identifiers - Critical severity
    PIIType.DNI: {
        "patterns": [
            r"\b\d{7,8}[A-Za-z]?\b",  # Spanish DNI
            r"\b[A-Za-z]\d{7}[A-Za-z]\b",  # NIE
        ],
        "severity": PIISeverity.CRITICAL,
        "context_keywords": ["dni", "documento", "identidad", "nie"],
    },
    PIIType.PASSPORT: {
        "patterns": [
            r"\b[A-Z]{1,2}\d{6,9}\b",  # Generic passport
        ],
        "severity": PIISeverity.CRITICAL,
        "context_keywords": ["pasaporte", "passport"],
    },
    PIIType.SSN: {
        "patterns": [
            r"\b\d{3}-\d{2}-\d{4}\b",  # US SSN
            r"\b\d{9}\b",  # SSN without dashes
        ],
        "severity": PIISeverity.CRITICAL,
        "context_keywords": ["ssn", "social security", "seguro social"],
    },
    PIIType.CURP: {
        "patterns": [
            r"\b[A-Z]{4}\d{6}[HM][A-Z]{5}[0-9A-Z]\d\b",  # Mexican CURP
        ],
        "severity": PIISeverity.CRITICAL,
        "context_keywords": ["curp"],
    },
    PIIType.RUT: {
        "patterns": [
            r"\b\d{1,2}\.\d{3}\.\d{3}-[0-9Kk]\b",  # Chilean RUT with dots
            r"\b\d{7,8}-[0-9Kk]\b",  # Chilean RUT without dots
        ],
        "severity": PIISeverity.CRITICAL,
        "context_keywords": ["rut", "run"],
    },
    PIIType.CUIL: {
        "patterns": [
            r"\b(20|23|24|27)-\d{8}-\d\b",  # Argentine CUIL
            r"\b(20|23|24|27)\d{8}\d\b",  # CUIL without dashes
        ],
        "severity": PIISeverity.CRITICAL,
        "context_keywords": ["cuil", "cuit"],
    },
    # Contact information - High severity
    PIIType.EMAIL: {
        "patterns": [
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        ],
        "severity": PIISeverity.HIGH,
        "context_keywords": ["email", "correo", "mail", "e-mail"],
    },
    PIIType.PHONE: {
        "patterns": [
            r"\b\+?\d{1,3}[-.\s]?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}\b",
            r"\b\d{9,12}\b",  # Simple phone number
        ],
        "severity": PIISeverity.HIGH,
        "context_keywords": [
            "teléfono",
            "telefono",
            "celular",
            "móvil",
            "phone",
            "tel",
        ],
    },
    PIIType.ADDRESS: {
        "patterns": [
            r"\b(?:calle|c/|av\.|avenida|paseo|plaza|carrera)\s+[A-Za-záéíóúñÁÉÍÓÚÑ0-9\s,]+\d+\b",
        ],
        "severity": PIISeverity.HIGH,
        "context_keywords": ["dirección", "direccion", "domicilio", "address", "calle"],
    },
    # Medical identifiers - High severity
    PIIType.MEDICAL_RECORD_NUMBER: {
        "patterns": [
            r"\b(?:HC|HCL|NHC|MRN)[-\s]?\d{5,12}\b",
            r"\b\d{6,12}(?=\s*(?:historia|historial|expediente))\b",
        ],
        "severity": PIISeverity.HIGH,
        "context_keywords": ["historia clínica", "expediente", "nhc", "mrn", "hc"],
    },
    PIIType.HEALTH_INSURANCE_ID: {
        "patterns": [
            r"\b(?:NASS|CIP|TSI)[-\s]?\d{10,16}\b",  # Spanish health IDs
            r"\b[A-Z]{2}\d{12}\b",  # Generic health ID
        ],
        "severity": PIISeverity.HIGH,
        "context_keywords": [
            "seguro",
            "afiliación",
            "tarjeta sanitaria",
            "nass",
            "cip",
        ],
    },
    # Financial - Critical severity
    PIIType.CREDIT_CARD: {
        "patterns": [
            r"\b(?:4\d{3}|5[1-5]\d{2}|6011|3[47]\d{2})[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b",
            r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b",
        ],
        "severity": PIISeverity.CRITICAL,
        "context_keywords": ["tarjeta", "visa", "mastercard", "amex", "credit card"],
    },
    PIIType.BANK_ACCOUNT: {
        "patterns": [
            r"\b[A-Z]{2}\d{2}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b",  # IBAN
            r"\b\d{20,24}\b",  # Account number
        ],
        "severity": PIISeverity.CRITICAL,
        "context_keywords": ["iban", "cuenta bancaria", "bank account", "cuenta"],
    },
    # Other sensitive - Medium severity
    PIIType.DATE_OF_BIRTH: {
        "patterns": [
            r"\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b",  # DD/MM/YYYY or similar
            r"\b\d{4}[-/]\d{1,2}[-/]\d{1,2}\b",  # YYYY-MM-DD
        ],
        "severity": PIISeverity.MEDIUM,
        "context_keywords": [
            "nacimiento",
            "fecha de nacimiento",
            "dob",
            "born",
            "nació",
        ],
    },
    PIIType.IP_ADDRESS: {
        "patterns": [
            r"\b(?:\d{1,3}\.){3}\d{1,3}\b",  # IPv4
            r"\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b",  # IPv6
        ],
        "severity": PIISeverity.LOW,
        "context_keywords": ["ip", "dirección ip", "ip address"],
    },
    # Full name detection (context-based)
    PIIType.FULL_NAME: {
        "patterns": [
            r"\b(?:(?:Sr\.|Sra\.|Dr\.|Dra\.|Don|Doña)\s+)?[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+){1,3}\b",
        ],
        "severity": PIISeverity.HIGH,
        "context_keywords": [
            "nombre",
            "paciente",
            "patient",
            "name",
            "llamado",
            "apellido",
        ],
    },
}


# =============================================================================
# Configuration
# =============================================================================


@dataclass
class PIIDetectorConfig:
    """Configuration for PII detector."""

    # Detection settings
    types_to_detect: list[PIIType] | None = None  # None = all types
    min_confidence: float = 0.7
    use_context: bool = True

    # Redaction settings
    redaction_char: str = "█"
    redaction_placeholder: str = "[REDACTED]"
    preserve_length: bool = False

    # Performance
    max_text_length: int = 100_000
    timeout_seconds: float = 5.0


# =============================================================================
# PII Detector
# =============================================================================


class PIIDetector:
    """PII detection engine."""

    def __init__(self, config: PIIDetectorConfig | None = None) -> None:
        """Initialize PII detector."""
        self.config = config or PIIDetectorConfig()
        self._compiled_patterns: dict[PIIType, list[re.Pattern]] = {}
        self._compile_patterns()
        logger.info("PII detector initialized")

    def _compile_patterns(self) -> None:
        """Pre-compile regex patterns for performance."""
        types_to_compile = self.config.types_to_detect or list(PII_PATTERNS.keys())

        for pii_type in types_to_compile:
            if pii_type in PII_PATTERNS:
                patterns = PII_PATTERNS[pii_type]["patterns"]
                self._compiled_patterns[pii_type] = [
                    re.compile(p, re.IGNORECASE) for p in patterns
                ]

    def detect(self, text: str) -> PIIDetectionResult:
        """
        Detect PII in text.

        Args:
            text: Text to scan for PII

        Returns:
            PIIDetectionResult with detected entities
        """
        start_time = time.time()

        # Truncate if too long
        if len(text) > self.config.max_text_length:
            text = text[: self.config.max_text_length]
            logger.warning(f"Text truncated to {self.config.max_text_length} chars")

        entities: list[PIIEntity] = []
        text_lower = text.lower()

        for pii_type, compiled_patterns in self._compiled_patterns.items():
            pattern_info = PII_PATTERNS[pii_type]
            severity = pattern_info["severity"]
            context_keywords = pattern_info.get("context_keywords", [])

            for pattern in compiled_patterns:
                for match in pattern.finditer(text):
                    value = match.group()
                    start_pos = match.start()
                    end_pos = match.end()

                    # Calculate confidence based on context
                    confidence = self._calculate_confidence(
                        text_lower, start_pos, end_pos, context_keywords, pii_type
                    )

                    if confidence >= self.config.min_confidence:
                        # Get surrounding context
                        context_start = max(0, start_pos - 30)
                        context_end = min(len(text), end_pos + 30)
                        context = text[context_start:context_end]

                        entities.append(
                            PIIEntity(
                                type=pii_type,
                                value=value,
                                start_pos=start_pos,
                                end_pos=end_pos,
                                confidence=confidence,
                                severity=severity,
                                context=context,
                            )
                        )

        # Remove overlapping entities (keep highest confidence)
        entities = self._remove_overlaps(entities)

        # Generate redacted text
        redacted_text = self._redact_text(text, entities)

        scan_time_ms = (time.time() - start_time) * 1000

        result = PIIDetectionResult(
            original_text=text,
            entities=entities,
            redacted_text=redacted_text,
            scan_time_ms=scan_time_ms,
        )

        if entities:
            logger.info(
                f"Detected {len(entities)} PII entities in {scan_time_ms:.2f}ms"
            )

        return result

    def _calculate_confidence(
        self,
        text_lower: str,
        start_pos: int,
        end_pos: int,
        context_keywords: list[str],
        pii_type: PIIType,
    ) -> float:
        """Calculate confidence score for a match."""
        base_confidence = 0.6

        if not self.config.use_context:
            return base_confidence

        # Check for context keywords nearby
        context_window = 100
        context_start = max(0, start_pos - context_window)
        context_end = min(len(text_lower), end_pos + context_window)
        context_text = text_lower[context_start:context_end]

        # Boost confidence if context keywords present
        keyword_boost = 0.0
        for keyword in context_keywords:
            if keyword in context_text:
                keyword_boost = 0.3
                break

        # Type-specific adjustments
        type_boost = 0.0
        if pii_type in {PIIType.EMAIL, PIIType.CREDIT_CARD}:
            # These patterns are very specific
            type_boost = 0.2
        elif pii_type == PIIType.PHONE:
            # Phone numbers need context
            if not keyword_boost:
                type_boost = -0.2
        elif pii_type == PIIType.FULL_NAME:
            # Names are tricky, need strong context
            if not keyword_boost:
                return 0.4

        return min(1.0, base_confidence + keyword_boost + type_boost)

    def _remove_overlaps(self, entities: list[PIIEntity]) -> list[PIIEntity]:
        """Remove overlapping entities, keeping highest confidence."""
        if not entities:
            return entities

        # Sort by start position
        sorted_entities = sorted(entities, key=lambda e: (e.start_pos, -e.confidence))

        result = []
        last_end = -1

        for entity in sorted_entities:
            if entity.start_pos >= last_end:
                result.append(entity)
                last_end = entity.end_pos
            elif entity.confidence > result[-1].confidence:
                # Replace with higher confidence
                result[-1] = entity
                last_end = entity.end_pos

        return result

    def _redact_text(self, text: str, entities: list[PIIEntity]) -> str:
        """Redact PII from text."""
        if not entities:
            return text

        # Sort by position (reverse to maintain positions)
        sorted_entities = sorted(entities, key=lambda e: e.start_pos, reverse=True)

        result = text
        for entity in sorted_entities:
            if self.config.preserve_length:
                replacement = self.config.redaction_char * len(entity.value)
            else:
                replacement = f"[{entity.type.value.upper()}]"

            result = result[: entity.start_pos] + replacement + result[entity.end_pos :]

        return result

    def redact(self, text: str) -> str:
        """Quick redaction without full detection result."""
        result = self.detect(text)
        return result.redacted_text

    def has_pii(self, text: str) -> bool:
        """Quick check if text contains PII."""
        result = self.detect(text)
        return result.has_pii

    def get_risk_level(self, text: str) -> RiskLevel:
        """Get risk level for text."""
        result = self.detect(text)
        return result.risk_level


# =============================================================================
# Specialized Medical PII Detector
# =============================================================================


class MedicalPIIDetector(PIIDetector):
    """PII detector optimized for medical contexts."""

    # Additional medical-specific patterns
    MEDICAL_PATTERNS: dict[str, dict[str, Any]] = {
        "diagnosis_with_name": {
            "pattern": r"(?:paciente|patient)\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+){1,2})",
            "severity": PIISeverity.HIGH,
        },
        "medical_record": {
            "pattern": r"(?:historia|expediente|record)\s*(?:clínica|médica|médico|#)?\s*:?\s*(\d{5,12})",
            "severity": PIISeverity.HIGH,
        },
    }

    def detect(self, text: str) -> PIIDetectionResult:
        """Detect PII with medical-specific patterns."""
        # Run base detection
        result = super().detect(text)

        # Add medical-specific detection
        additional_entities = self._detect_medical_pii(text)

        if additional_entities:
            all_entities = result.entities + additional_entities
            all_entities = self._remove_overlaps(all_entities)

            result = PIIDetectionResult(
                original_text=result.original_text,
                entities=all_entities,
                redacted_text=self._redact_text(text, all_entities),
                scan_time_ms=result.scan_time_ms,
            )

        return result

    def _detect_medical_pii(self, text: str) -> list[PIIEntity]:
        """Detect medical-specific PII patterns."""
        entities = []

        for pattern_name, info in self.MEDICAL_PATTERNS.items():
            pattern = re.compile(info["pattern"], re.IGNORECASE)

            for match in pattern.finditer(text):
                if match.lastindex:
                    # Use captured group
                    value = match.group(1)
                    start_pos = match.start(1)
                    end_pos = match.end(1)
                else:
                    value = match.group()
                    start_pos = match.start()
                    end_pos = match.end()

                entities.append(
                    PIIEntity(
                        type=PIIType.FULL_NAME
                        if "name" in pattern_name
                        else PIIType.MEDICAL_RECORD_NUMBER,
                        value=value,
                        start_pos=start_pos,
                        end_pos=end_pos,
                        confidence=0.85,
                        severity=info["severity"],
                    )
                )

        return entities


# =============================================================================
# Factory Functions
# =============================================================================


def create_pii_detector(
    config: PIIDetectorConfig | None = None,
    medical: bool = True,
) -> PIIDetector:
    """
    Create PII detector.

    Args:
        config: Optional configuration
        medical: Use medical-optimized detector

    Returns:
        Configured PIIDetector
    """
    if medical:
        return MedicalPIIDetector(config)
    return PIIDetector(config)
