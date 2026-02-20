# =============================================================================
# MedeX - Patient Context Extractor
# =============================================================================
"""
Patient context extraction from conversations for MedeX V2.

This module provides:
- Clinical data extraction from messages
- Patient demographics (age, sex)
- Symptom and condition detection
- Vital signs extraction
- Medication and allergy detection
- Emergency indicator identification

Design:
- Rule-based extraction for speed
- Optional LLM enhancement for accuracy
- Incremental context building
- Spanish medical terminology
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


# =============================================================================
# Data Classes
# =============================================================================


class EmergencyLevel(Enum):
    """Emergency severity levels."""

    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class PatientContext:
    """
    Extracted patient context from conversation.

    Accumulates clinical information across messages.
    """

    # Demographics
    age: int | None = None
    age_unit: str = "years"  # years, months
    sex: str | None = None

    # Clinical
    symptoms: list[str] = field(default_factory=list)
    conditions: list[str] = field(default_factory=list)
    medications: list[str] = field(default_factory=list)
    allergies: list[str] = field(default_factory=list)

    # Vitals
    vitals: dict[str, Any] = field(default_factory=dict)

    # Emergency
    emergency_level: EmergencyLevel = EmergencyLevel.NONE
    emergency_indicators: list[str] = field(default_factory=list)

    # Metadata
    extracted_at: datetime = field(default_factory=datetime.utcnow)
    confidence: float = 0.0
    source_messages: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "age": self.age,
            "age_unit": self.age_unit,
            "sex": self.sex,
            "symptoms": self.symptoms,
            "conditions": self.conditions,
            "medications": self.medications,
            "allergies": self.allergies,
            "vitals": self.vitals,
            "emergency_level": self.emergency_level.value,
            "emergency_indicators": self.emergency_indicators,
            "extracted_at": self.extracted_at.isoformat(),
            "confidence": self.confidence,
            "source_messages": self.source_messages,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PatientContext:
        """Create from dictionary."""
        return cls(
            age=data.get("age"),
            age_unit=data.get("age_unit", "years"),
            sex=data.get("sex"),
            symptoms=data.get("symptoms", []),
            conditions=data.get("conditions", []),
            medications=data.get("medications", []),
            allergies=data.get("allergies", []),
            vitals=data.get("vitals", {}),
            emergency_level=EmergencyLevel(data.get("emergency_level", "none")),
            emergency_indicators=data.get("emergency_indicators", []),
            confidence=data.get("confidence", 0.0),
            source_messages=data.get("source_messages", 0),
        )

    def merge(self, other: PatientContext) -> PatientContext:
        """Merge with another context, preferring newer data."""
        return PatientContext(
            age=other.age or self.age,
            age_unit=other.age_unit if other.age else self.age_unit,
            sex=other.sex or self.sex,
            symptoms=list(set(self.symptoms + other.symptoms)),
            conditions=list(set(self.conditions + other.conditions)),
            medications=list(set(self.medications + other.medications)),
            allergies=list(set(self.allergies + other.allergies)),
            vitals={**self.vitals, **other.vitals},
            emergency_level=max(
                self.emergency_level, other.emergency_level, key=lambda x: x.value
            ),
            emergency_indicators=list(
                set(self.emergency_indicators + other.emergency_indicators)
            ),
            confidence=max(self.confidence, other.confidence),
            source_messages=self.source_messages + other.source_messages,
        )


# =============================================================================
# Patient Context Extractor
# =============================================================================


class PatientContextExtractor:
    """
    Extract patient context from conversation messages.

    Uses pattern matching and medical terminology
    to identify clinical information.
    """

    # Age patterns
    AGE_PATTERNS = [
        (r"(?:tengo|tiene|soy|es|de)\s+(\d{1,3})\s*(?:años|año)", "years"),
        (r"(\d{1,3})\s*(?:años|año)\s*(?:de edad)?", "years"),
        (r"(?:bebé|bebe|niño|niña)\s*(?:de)?\s*(\d{1,2})\s*(?:meses|mes)", "months"),
        (r"(\d{1,2})\s*(?:meses|mes)\s*(?:de edad)?", "months"),
        (r"(?:edad|age)[:\s]+(\d{1,3})", "years"),
    ]

    # Sex patterns
    SEX_PATTERNS = [
        (r"\b(?:soy|es)\s+(?:un\s+)?(?:hombre|varón|masculino)\b", "masculino"),
        (r"\b(?:soy|es)\s+(?:una\s+)?(?:mujer|femenina|femenino)\b", "femenino"),
        (r"\b(?:sexo|género)[:\s]+(?:masculino|hombre|varón|M)\b", "masculino"),
        (r"\b(?:sexo|género)[:\s]+(?:femenino|mujer|F)\b", "femenino"),
        (r"\bpaciente\s+(?:masculino|hombre)\b", "masculino"),
        (r"\bpaciente\s+(?:femenina?|mujer)\b", "femenino"),
    ]

    # Symptom keywords
    SYMPTOM_KEYWORDS = {
        "dolor de cabeza": "cefalea",
        "dolor cabeza": "cefalea",
        "cefalea": "cefalea",
        "migraña": "migraña",
        "dolor de pecho": "dolor torácico",
        "dolor pecho": "dolor torácico",
        "dolor torácico": "dolor torácico",
        "dolor abdominal": "dolor abdominal",
        "dolor de estómago": "dolor abdominal",
        "dolor estómago": "dolor abdominal",
        "dolor de espalda": "lumbalgia",
        "lumbalgia": "lumbalgia",
        "fiebre": "fiebre",
        "temperatura alta": "fiebre",
        "calentura": "fiebre",
        "tos": "tos",
        "tos seca": "tos seca",
        "tos con flema": "tos productiva",
        "náusea": "náusea",
        "náuseas": "náusea",
        "vómito": "vómito",
        "vómitos": "vómito",
        "diarrea": "diarrea",
        "estreñimiento": "estreñimiento",
        "fatiga": "fatiga",
        "cansancio": "fatiga",
        "debilidad": "debilidad",
        "mareo": "mareo",
        "vértigo": "vértigo",
        "dificultad para respirar": "disnea",
        "falta de aire": "disnea",
        "disnea": "disnea",
        "palpitaciones": "palpitaciones",
        "taquicardia": "taquicardia",
        "insomnio": "insomnio",
        "ansiedad": "ansiedad",
        "depresión": "depresión",
        "picazón": "prurito",
        "prurito": "prurito",
        "erupción": "erupción cutánea",
        "rash": "erupción cutánea",
        "hinchazón": "edema",
        "edema": "edema",
        "sangrado": "sangrado",
        "hemorragia": "hemorragia",
    }

    # Condition keywords
    CONDITION_KEYWORDS = {
        "diabetes": "diabetes",
        "diabético": "diabetes",
        "diabética": "diabetes",
        "hipertensión": "hipertensión",
        "presión alta": "hipertensión",
        "hipertenso": "hipertensión",
        "asma": "asma",
        "asmático": "asma",
        "artritis": "artritis",
        "artrosis": "artrosis",
        "cáncer": "cáncer",
        "tumor": "tumor",
        "tiroides": "enfermedad tiroidea",
        "hipotiroidismo": "hipotiroidismo",
        "hipertiroidismo": "hipertiroidismo",
        "colesterol alto": "hipercolesterolemia",
        "anemia": "anemia",
        "insuficiencia renal": "insuficiencia renal",
        "insuficiencia cardíaca": "insuficiencia cardíaca",
        "epoc": "EPOC",
        "enfisema": "enfisema",
        "covid": "COVID-19",
        "coronavirus": "COVID-19",
        "neumonía": "neumonía",
        "infección urinaria": "infección urinaria",
        "gastritis": "gastritis",
        "úlcera": "úlcera",
        "embarazo": "embarazo",
        "embarazada": "embarazo",
    }

    # Medication patterns
    MEDICATION_PATTERNS = [
        r"(?:tomo|toma|uso|usa)\s+(.+?)(?:\s+para|\s+desde|\.|\,|$)",
        r"(?:medicamento|medicina|medicación)[:\s]+(.+?)(?:\.|\,|$)",
        r"(?:tratamiento\s+con)\s+(.+?)(?:\s+para|\s+desde|\.|\,|$)",
    ]

    # Common medication names
    MEDICATION_NAMES = {
        "metformina",
        "insulina",
        "losartán",
        "enalapril",
        "amlodipino",
        "atorvastatina",
        "omeprazol",
        "ibuprofeno",
        "paracetamol",
        "aspirina",
        "diclofenaco",
        "naproxeno",
        "amoxicilina",
        "azitromicina",
        "ciprofloxacino",
        "metoprolol",
        "carvedilol",
        "furosemida",
        "hidroclorotiazida",
        "lisinopril",
        "prednisona",
        "salbutamol",
        "budesonida",
        "loratadina",
        "cetirizina",
        "tramadol",
        "gabapentina",
        "pregabalina",
        "sertralina",
        "fluoxetina",
        "alprazolam",
        "clonazepam",
        "levotiroxina",
        "warfarina",
        "clopidogrel",
    }

    # Allergy patterns
    ALLERGY_PATTERNS = [
        r"(?:alérgico|alérgica|alergia)\s+(?:a|al|a la)?\s*(.+?)(?:\.|\,|$)",
        r"(?:no\s+(?:puedo|puede)\s+(?:tomar|usar))\s+(.+?)(?:\s+porque|\.|\,|$)",
    ]

    # Vital signs patterns
    VITAL_PATTERNS = {
        "temperatura": (
            r"(?:temperatura|temp)[:\s]+(\d{2}[.,]\d)\s*(?:°?[cC]|grados)?",
            lambda x: float(x.replace(",", ".")),
        ),
        "presion_sistolica": (
            r"(?:presión|tensión)[:\s]+(\d{2,3})/\d{2,3}",
            lambda x: int(x),
        ),
        "presion_diastolica": (
            r"(?:presión|tensión)[:\s]+\d{2,3}/(\d{2,3})",
            lambda x: int(x),
        ),
        "frecuencia_cardiaca": (
            r"(?:frecuencia\s+card[íi]aca|pulso|FC)[:\s]+(\d{2,3})\s*(?:lpm|bpm)?",
            lambda x: int(x),
        ),
        "saturacion": (
            r"(?:saturación|SpO2|oxígeno)[:\s]+(\d{2,3})\s*%?",
            lambda x: int(x),
        ),
        "glucosa": (
            r"(?:glucosa|glicemia|azúcar)[:\s]+(\d{2,3})\s*(?:mg/dl)?",
            lambda x: int(x),
        ),
        "peso": (
            r"(?:peso)[:\s]+(\d{2,3}[.,]?\d?)\s*(?:kg|kilos)?",
            lambda x: float(x.replace(",", ".")),
        ),
    }

    # Emergency indicators
    EMERGENCY_KEYWORDS = {
        EmergencyLevel.CRITICAL: [
            "no puedo respirar",
            "desmayé",
            "perdí el conocimiento",
            "dolor de pecho intenso",
            "sangrado abundante",
            "convulsiones",
            "parálisis",
            "no puede hablar",
            "infarto",
            "derrame",
            "asfixia",
            "anafilaxia",
            "shock",
        ],
        EmergencyLevel.HIGH: [
            "fiebre muy alta",
            "temperatura sobre 40",
            "dificultad severa para respirar",
            "dolor insoportable",
            "vómito con sangre",
            "sangre en las heces",
            "confusión mental",
            "visión borrosa súbita",
            "debilidad súbita",
            "dolor de cabeza severo",
        ],
        EmergencyLevel.MEDIUM: [
            "fiebre persistente",
            "dolor que no cede",
            "vómitos repetidos",
            "diarrea con sangre",
            "hinchazón facial",
            "erupción generalizada",
            "tos con sangre",
        ],
    }

    def __init__(self):
        """Initialize extractor with compiled patterns."""
        self._compiled_age = [
            (re.compile(p, re.IGNORECASE), unit) for p, unit in self.AGE_PATTERNS
        ]
        self._compiled_sex = [
            (re.compile(p, re.IGNORECASE), sex) for p, sex in self.SEX_PATTERNS
        ]
        self._compiled_meds = [
            re.compile(p, re.IGNORECASE) for p in self.MEDICATION_PATTERNS
        ]
        self._compiled_allergy = [
            re.compile(p, re.IGNORECASE) for p in self.ALLERGY_PATTERNS
        ]
        self._compiled_vitals = {
            name: (re.compile(pattern, re.IGNORECASE), converter)
            for name, (pattern, converter) in self.VITAL_PATTERNS.items()
        }

    def extract_from_message(self, message: str) -> PatientContext:
        """
        Extract patient context from a single message.

        Args:
            message: Message content to analyze

        Returns:
            PatientContext with extracted data
        """
        if not message:
            return PatientContext()

        message_lower = message.lower()

        context = PatientContext(
            age=self._extract_age(message),
            sex=self._extract_sex(message),
            symptoms=self._extract_symptoms(message_lower),
            conditions=self._extract_conditions(message_lower),
            medications=self._extract_medications(message),
            allergies=self._extract_allergies(message),
            vitals=self._extract_vitals(message),
            source_messages=1,
        )

        # Check for emergencies
        level, indicators = self._check_emergency(message_lower)
        context.emergency_level = level
        context.emergency_indicators = indicators

        # Calculate confidence based on what was extracted
        context.confidence = self._calculate_confidence(context)

        return context

    def extract_from_messages(
        self,
        messages: list[dict[str, str]],
    ) -> PatientContext:
        """
        Extract and merge context from multiple messages.

        Args:
            messages: List of message dicts with 'role' and 'content'

        Returns:
            Merged PatientContext
        """
        if not messages:
            return PatientContext()

        # Only analyze user messages
        user_messages = [m["content"] for m in messages if m.get("role") == "user"]

        if not user_messages:
            return PatientContext()

        # Extract from each and merge
        base_context = PatientContext()
        for msg in user_messages:
            extracted = self.extract_from_message(msg)
            base_context = base_context.merge(extracted)

        return base_context

    def _extract_age(self, text: str) -> int | None:
        """Extract age from text."""
        for pattern, unit in self._compiled_age:
            match = pattern.search(text)
            if match:
                age = int(match.group(1))
                # Validate reasonable age
                if unit == "years" and 0 < age < 120:
                    return age
                elif unit == "months" and 0 < age < 36:
                    return age
        return None

    def _extract_sex(self, text: str) -> str | None:
        """Extract sex from text."""
        for pattern, sex in self._compiled_sex:
            if pattern.search(text):
                return sex
        return None

    def _extract_symptoms(self, text: str) -> list[str]:
        """Extract symptoms from text."""
        found = []
        for keyword, normalized in self.SYMPTOM_KEYWORDS.items():
            if keyword in text:
                if normalized not in found:
                    found.append(normalized)
        return found

    def _extract_conditions(self, text: str) -> list[str]:
        """Extract medical conditions from text."""
        found = []
        for keyword, normalized in self.CONDITION_KEYWORDS.items():
            if keyword in text:
                if normalized not in found:
                    found.append(normalized)
        return found

    def _extract_medications(self, text: str) -> list[str]:
        """Extract medications from text."""
        found = []
        text_lower = text.lower()

        # Check known medication names
        for med in self.MEDICATION_NAMES:
            if med in text_lower:
                # Capitalize medication name
                found.append(med.capitalize())

        # Try patterns for unknown medications
        for pattern in self._compiled_meds:
            match = pattern.search(text)
            if match:
                med_text = match.group(1).strip()
                # Clean and validate
                if len(med_text) < 50 and med_text not in found:
                    found.append(med_text)

        return found

    def _extract_allergies(self, text: str) -> list[str]:
        """Extract allergies from text."""
        found = []
        for pattern in self._compiled_allergy:
            match = pattern.search(text)
            if match:
                allergy = match.group(1).strip()
                if len(allergy) < 50 and allergy not in found:
                    found.append(allergy)
        return found

    def _extract_vitals(self, text: str) -> dict[str, Any]:
        """Extract vital signs from text."""
        vitals = {}
        for name, (pattern, converter) in self._compiled_vitals.items():
            match = pattern.search(text)
            if match:
                try:
                    value = converter(match.group(1))
                    vitals[name] = value
                except (ValueError, IndexError):
                    pass
        return vitals

    def _check_emergency(
        self,
        text: str,
    ) -> tuple[EmergencyLevel, list[str]]:
        """Check for emergency indicators."""
        indicators = []
        max_level = EmergencyLevel.NONE

        for level in [
            EmergencyLevel.CRITICAL,
            EmergencyLevel.HIGH,
            EmergencyLevel.MEDIUM,
        ]:
            for keyword in self.EMERGENCY_KEYWORDS.get(level, []):
                if keyword in text:
                    indicators.append(keyword)
                    if level.value > max_level.value:
                        max_level = level

        return max_level, indicators

    def _calculate_confidence(self, context: PatientContext) -> float:
        """Calculate extraction confidence score."""
        score = 0.0
        max_score = 0.0

        # Demographics
        max_score += 0.2
        if context.age:
            score += 0.1
        if context.sex:
            score += 0.1

        # Clinical data
        max_score += 0.5
        if context.symptoms:
            score += min(0.2, len(context.symptoms) * 0.05)
        if context.conditions:
            score += min(0.15, len(context.conditions) * 0.05)
        if context.medications:
            score += min(0.1, len(context.medications) * 0.03)
        if context.allergies:
            score += 0.05

        # Vitals
        max_score += 0.3
        if context.vitals:
            score += min(0.3, len(context.vitals) * 0.05)

        return round(score / max_score, 2) if max_score > 0 else 0.0


# =============================================================================
# Singleton Instance
# =============================================================================

_extractor: PatientContextExtractor | None = None


def get_patient_context_extractor() -> PatientContextExtractor:
    """Get or create patient context extractor instance."""
    global _extractor
    if _extractor is None:
        _extractor = PatientContextExtractor()
    return _extractor
