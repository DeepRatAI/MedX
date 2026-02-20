"""
User Type Detection Module.

Detects whether a query comes from a medical professional or
a patient/student based on linguistic patterns and scoring.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal, List, Tuple

UserType = Literal["Professional", "Educational"]


@dataclass
class DetectionResult:
    """Result of user type detection.

    Attributes:
        user_type: Detected user type
        confidence: Confidence score (0.0 to 1.0)
        professional_score: Raw score for professional patterns
        educational_score: Raw score for educational patterns
        matched_patterns: List of patterns that matched
    """

    user_type: UserType
    confidence: float
    professional_score: int
    educational_score: int
    matched_patterns: List[str]


class UserTypeDetector:
    """Detects user type from query text.

    Uses pattern matching and scoring to classify queries as coming
    from medical professionals or patients/students.

    The detection prioritizes safety: in ambiguous cases, it defaults
    to Educational mode to avoid providing overly technical responses
    to non-professionals.
    """

    # Professional medical language patterns (Spanish)
    PROFESSIONAL_PATTERNS: List[Tuple[str, int]] = [
        # High-confidence patterns (score: 3)
        (r"paciente\s+de\s+\d+\s+a[ñn]os", 3),  # "paciente de 45 años"
        (r"paciente\s+(masculino|femenino)", 3),  # "paciente masculino/femenino"
        (r"diagn[oó]stico\s+diferencial", 3),  # "diagnóstico diferencial"
        (r"c[oó]digo\s+icd", 3),  # "código ICD"
        (r"protocolo\s+de\s+manejo", 3),  # "protocolo de manejo"
        (r"presenta\s+.{5,30}evoluci[oó]n", 3),  # "presenta... de X evolución"
        # Medium-confidence patterns (score: 2)
        (r"caso\s+cl[ií]nico", 2),  # "caso clínico"
        (r"tratamiento\s+con", 2),  # "tratamiento con"
        (r"dosis\s+de", 2),  # "dosis de"
        (r"mg\s+cada", 2),  # "mg cada"
        (r"manejo\s+de", 2),  # "manejo de"
        (r"exploraci[oó]n\s+f[ií]sica", 2),  # "exploración física"
        (r"signos\s+vitales", 2),  # "signos vitales"
        (r"anamnesis", 2),  # "anamnesis"
        (r"antecedentes\s+patol[oó]gicos", 2),  # "antecedentes patológicos"
        (r"antecedentes\s+de\s+\w+", 2),  # "antecedentes de HTA"
        (r"\b(hta|dm2?|irc|epoc|iam)\b", 2),  # medical abbreviations
        (r"irradiaci[oó]n\s+a", 2),  # "irradiación a"
        (r"diaforesis", 2),  # "diaforesis"
        # Low-confidence patterns (score: 1)
        (r"protocolo\s+de", 1),  # "protocolo de"
        (r"seguimiento", 1),  # "seguimiento"
        (r"antecedentes", 1),  # "antecedentes"
        (r"valoraci[oó]n", 1),  # "valoración"
        (r"interconsulta", 1),  # "interconsulta"
        (r"derivaci[oó]n", 1),  # "derivación"
        (r"historia\s+cl[ií]nica", 1),  # "historia clínica"
        (r"hallazgos", 1),  # "hallazgos"
        (r"evoluci[oó]n", 1),  # "evolución"
        (r"presenta\b", 1),  # "presenta"
    ]

    # Patient/educational language patterns (Spanish)
    EDUCATIONAL_PATTERNS: List[Tuple[str, int]] = [
        # High-confidence patterns (score: 3)
        (r"me\s+duele", 3),  # "me duele"
        (r"tengo\s+dolor", 3),  # "tengo dolor"
        (r"qu[eé]\s+puedo\s+tomar", 3),  # "qué puedo tomar"
        (r"es\s+grave", 3),  # "es grave"
        (r"debo\s+preocuparme", 3),  # "debo preocuparme"
        # Medium-confidence patterns (score: 2)
        (r"me\s+siento", 2),  # "me siento"
        (r"tengo", 2),  # "tengo"
        (r"siento", 2),  # "siento"
        (r"me\s+pasa", 2),  # "me pasa"
        (r"mi\s+hijo", 2),  # "mi hijo"
        (r"mi\s+esposa", 2),  # "mi esposa"
        (r"mi\s+familia", 2),  # "mi familia"
        (r"qu[eé]\s+significa", 2),  # "qué significa"
        # Low-confidence patterns (score: 1)
        (r"me\s+preocupa", 1),  # "me preocupa"
        (r"es\s+normal", 1),  # "es normal"
        (r"por\s+qu[eé]", 1),  # "por qué"
        (r"c[oó]mo\s+puedo", 1),  # "cómo puedo"
        (r"necesito\s+saber", 1),  # "necesito saber"
    ]

    # Professional threshold - scores above this indicate professional
    PROFESSIONAL_THRESHOLD: int = 4

    def __init__(self) -> None:
        """Initialize the detector with compiled patterns."""
        self._professional_compiled = [
            (re.compile(pattern, re.IGNORECASE), score)
            for pattern, score in self.PROFESSIONAL_PATTERNS
        ]
        self._educational_compiled = [
            (re.compile(pattern, re.IGNORECASE), score)
            for pattern, score in self.EDUCATIONAL_PATTERNS
        ]

    def detect(self, query: str) -> DetectionResult:
        """Detect user type from query text.

        Args:
            query: The user's query text

        Returns:
            DetectionResult with user type and confidence
        """
        professional_score = 0
        educational_score = 0
        matched_patterns: List[str] = []

        # Score professional patterns
        for pattern, score in self._professional_compiled:
            if pattern.search(query):
                professional_score += score
                matched_patterns.append(f"PRO: {pattern.pattern}")

        # Score educational patterns
        for pattern, score in self._educational_compiled:
            if pattern.search(query):
                educational_score += score
                matched_patterns.append(f"EDU: {pattern.pattern}")

        # Determine user type
        if (
            professional_score >= self.PROFESSIONAL_THRESHOLD
            and professional_score > educational_score
        ):
            user_type: UserType = "Professional"
            # Confidence based on margin
            margin = professional_score - educational_score
            confidence = min(0.95, 0.6 + margin * 0.05)
        else:
            user_type = "Educational"
            if educational_score > 0:
                confidence = min(0.9, 0.5 + educational_score * 0.05)
            else:
                confidence = 0.5  # Default uncertainty

        return DetectionResult(
            user_type=user_type,
            confidence=confidence,
            professional_score=professional_score,
            educational_score=educational_score,
            matched_patterns=matched_patterns,
        )

    def is_professional(self, query: str) -> bool:
        """Quick check if query is from a professional.

        Args:
            query: The user's query text

        Returns:
            True if detected as professional, False otherwise
        """
        return self.detect(query).user_type == "Professional"
