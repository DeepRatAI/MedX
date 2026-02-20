"""
Emergency Detection Module.

Detects medical emergencies from query text using keyword matching
and pattern recognition for critical medical conditions.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum


class EmergencyLevel(Enum):
    """Emergency severity levels."""

    NONE = "none"
    URGENT = "urgent"
    CRITICAL = "critical"


@dataclass
class EmergencyResult:
    """Result of emergency detection.

    Attributes:
        is_emergency: Whether an emergency was detected
        level: Severity level of the emergency
        matched_keywords: Keywords that triggered the detection
        category: Medical category of the emergency
    """

    is_emergency: bool
    level: EmergencyLevel
    matched_keywords: list[str]
    category: str


class EmergencyDetector:
    """Detects medical emergencies from query text.

    Uses comprehensive keyword matching for various emergency
    categories including cardiac, respiratory, neurological,
    trauma, and other critical conditions.
    """

    # Critical emergencies - immediate life threat
    CRITICAL_KEYWORDS: set[str] = {
        # Cardiac
        "dolor precordial",
        "dolor torácico",
        "opresión torácica",
        "dolor en el pecho",
        "me duele el pecho",
        "duele mucho el pecho",
        "infarto",
        "paro cardíaco",
        "paro cardiaco",
        # Respiratory
        "dificultad respiratoria",
        "disnea severa",
        "no puede respirar",
        "ahogo",
        "cianosis",
        "labios morados",
        # Neurological
        "pérdida de conciencia",
        "perdió la conciencia",
        "perdió el conocimiento",
        "inconsciente",
        "convulsiones",
        "crisis epiléptica",
        "síncope",
        "desmayo súbito",
        "parálisis súbita",
        "no puede hablar",
        "no puede mover",
        "ictus",
        "derrame cerebral",
        "avc",
        "acv",
        # Trauma
        "sangrado abundante",
        "hemorragia masiva",
        "accidente grave",
        "trauma craneal",
        "traumatismo craneoencefálico",
        # Other critical
        "anafilaxia",
        "alergia severa",
        "shock",
        "sepsis",
        "intoxicación",
        "envenenamiento",
        "sobredosis",
        "quemadura extensa",
    }

    # Urgent conditions - require prompt attention
    URGENT_KEYWORDS: set[str] = {
        # Pain
        "dolor intenso",
        "dolor severo",
        "dolor insoportable",
        # Fever
        "fiebre alta",
        "fiebre de 40",
        "fiebre persistente",
        # Gastrointestinal
        "vómitos persistentes",
        "vómitos con sangre",
        "sangre en heces",
        "diarrea severa",
        "deshidratación",
        # Cardiovascular
        "palpitaciones",
        "taquicardia",
        "arritmia",
        "presión muy alta",
        # Respiratory
        "tos con sangre",
        "dificultad para respirar",
        # Neurological
        "dolor de cabeza intenso",
        "cefalea súbita",
        "mareos severos",
        "visión borrosa súbita",
        # Trauma
        "fractura",
        "lesión grave",
        "herida profunda",
        # Obstetric
        "sangrado vaginal",
        "contracciones",
        "ruptura de fuente",
        # Psychiatric
        "pensamiento suicida",
        "pensamientos suicidas",
        "quiero morir",
        "hacerme daño",
        # General
        "urgente",
        "emergencia",
        "911",
        "ambulancia",
    }

    # Emergency categories for classification
    CATEGORY_PATTERNS = {
        "cardiac": r"(coraz[oó]n|card[ií]ac|precordial|tor[aá]cic|pecho|infarto|angina)",
        "respiratory": r"(respir|disne|ahog|pulm[oó]n|oxígeno|cianosis)",
        "neurological": r"(cerebr|neurol|convuls|epilep|conscien|paral|ictus|derrame)",
        "trauma": r"(trauma|accidente|fractura|hemorrag|sangrado|herida|quemadura)",
        "psychiatric": r"(suicid|da[ñn]o|morir|matar)",
        "obstetric": r"(embaraz|parto|contracci|sangrado vaginal)",
        "general": r"(urgent|emergenc|911|ambulancia)",
    }

    def __init__(self) -> None:
        """Initialize the detector with compiled patterns."""
        self._critical_pattern = self._build_pattern(self.CRITICAL_KEYWORDS)
        self._urgent_pattern = self._build_pattern(self.URGENT_KEYWORDS)
        self._category_patterns = {
            cat: re.compile(pattern, re.IGNORECASE)
            for cat, pattern in self.CATEGORY_PATTERNS.items()
        }

    @staticmethod
    def _build_pattern(keywords: set[str]) -> re.Pattern:
        """Build regex pattern from keyword set.

        Args:
            keywords: Set of keywords to match

        Returns:
            Compiled regex pattern
        """
        # Escape special characters and join with OR
        escaped = [re.escape(kw) for kw in keywords]
        pattern = "|".join(escaped)
        return re.compile(pattern, re.IGNORECASE)

    def detect(self, query: str) -> EmergencyResult:
        """Detect emergency from query text.

        Args:
            query: The user's query text

        Returns:
            EmergencyResult with detection details
        """
        query_lower = query.lower()
        matched_keywords: list[str] = []

        # Check for critical emergencies first
        critical_matches = self._critical_pattern.findall(query_lower)
        if critical_matches:
            matched_keywords.extend(critical_matches)
            category = self._determine_category(query_lower)
            return EmergencyResult(
                is_emergency=True,
                level=EmergencyLevel.CRITICAL,
                matched_keywords=matched_keywords,
                category=category,
            )

        # Check for urgent conditions
        urgent_matches = self._urgent_pattern.findall(query_lower)
        if urgent_matches:
            matched_keywords.extend(urgent_matches)
            category = self._determine_category(query_lower)
            return EmergencyResult(
                is_emergency=True,
                level=EmergencyLevel.URGENT,
                matched_keywords=matched_keywords,
                category=category,
            )

        # No emergency detected
        return EmergencyResult(
            is_emergency=False,
            level=EmergencyLevel.NONE,
            matched_keywords=[],
            category="none",
        )

    def _determine_category(self, query: str) -> str:
        """Determine the medical category of the emergency.

        Args:
            query: The query text (lowercase)

        Returns:
            Category name
        """
        for category, pattern in self._category_patterns.items():
            if pattern.search(query):
                return category
        return "general"

    def is_emergency(self, query: str) -> bool:
        """Quick check if query indicates an emergency.

        Args:
            query: The user's query text

        Returns:
            True if emergency detected, False otherwise
        """
        return self.detect(query).is_emergency

    def is_critical(self, query: str) -> bool:
        """Check if query indicates a critical emergency.

        Args:
            query: The user's query text

        Returns:
            True if critical emergency, False otherwise
        """
        result = self.detect(query)
        return result.is_emergency and result.level == EmergencyLevel.CRITICAL
