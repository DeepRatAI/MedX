# =============================================================================
# MedeX - Medical Domain Models
# =============================================================================
"""
Medical domain models for clinical reasoning.

Features:
- Triage classification (ESI 5-level)
- Diagnostic hypothesis with probability
- Treatment plans with evidence levels
- CIE-10 code integration
- Clinical findings and vital signs
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

# =============================================================================
# Enums
# =============================================================================


class TriageLevel(Enum):
    """Emergency Severity Index (ESI) 5-level triage."""

    LEVEL_1 = "resuscitation"  # Immediate life-saving intervention
    LEVEL_2 = "emergent"  # High risk, confused, severe pain
    LEVEL_3 = "urgent"  # Multiple resources needed
    LEVEL_4 = "less_urgent"  # One resource needed
    LEVEL_5 = "non_urgent"  # No resources needed

    @property
    def color(self) -> str:
        """Standard triage color."""
        colors = {
            "resuscitation": "red",
            "emergent": "orange",
            "urgent": "yellow",
            "less_urgent": "green",
            "non_urgent": "blue",
        }
        return colors.get(self.value, "white")

    @property
    def max_wait_minutes(self) -> int:
        """Maximum recommended wait time."""
        times = {
            "resuscitation": 0,
            "emergent": 10,
            "urgent": 30,
            "less_urgent": 60,
            "non_urgent": 120,
        }
        return times.get(self.value, 120)


class UrgencyLevel(Enum):
    """Clinical urgency classification."""

    CRITICAL = "critical"  # Immediate action required
    HIGH = "high"  # Within hours
    MEDIUM = "medium"  # Within days
    LOW = "low"  # Routine
    INFORMATIONAL = "informational"  # Educational only


class EvidenceLevel(Enum):
    """Evidence-based medicine levels."""

    LEVEL_1A = "1a"  # Systematic review of RCTs
    LEVEL_1B = "1b"  # Individual RCT
    LEVEL_2A = "2a"  # Systematic review of cohort studies
    LEVEL_2B = "2b"  # Individual cohort study
    LEVEL_3A = "3a"  # Systematic review of case-control
    LEVEL_3B = "3b"  # Individual case-control
    LEVEL_4 = "4"  # Case series
    LEVEL_5 = "5"  # Expert opinion


class RecommendationGrade(Enum):
    """GRADE recommendation strength."""

    STRONG_FOR = "strong_for"  # Benefits clearly outweigh risks
    WEAK_FOR = "weak_for"  # Benefits probably outweigh risks
    WEAK_AGAINST = "weak_against"  # Risks probably outweigh benefits
    STRONG_AGAINST = "strong_against"  # Risks clearly outweigh benefits


class ConsultationType(Enum):
    """Type of medical consultation."""

    EDUCATIONAL = "educational"  # General health information
    PROFESSIONAL = "professional"  # Clinical decision support
    EMERGENCY = "emergency"  # Emergency triage
    FOLLOW_UP = "follow_up"  # Follow-up consultation


class Specialty(Enum):
    """Medical specialties."""

    INTERNAL_MEDICINE = "internal_medicine"
    CARDIOLOGY = "cardiology"
    NEUROLOGY = "neurology"
    GASTROENTEROLOGY = "gastroenterology"
    PULMONOLOGY = "pulmonology"
    NEPHROLOGY = "nephrology"
    ENDOCRINOLOGY = "endocrinology"
    RHEUMATOLOGY = "rheumatology"
    HEMATOLOGY = "hematology"
    ONCOLOGY = "oncology"
    INFECTIOUS_DISEASE = "infectious_disease"
    DERMATOLOGY = "dermatology"
    PSYCHIATRY = "psychiatry"
    PEDIATRICS = "pediatrics"
    GERIATRICS = "geriatrics"
    EMERGENCY_MEDICINE = "emergency_medicine"
    SURGERY = "surgery"
    OBSTETRICS_GYNECOLOGY = "obstetrics_gynecology"
    OPHTHALMOLOGY = "ophthalmology"
    OTOLARYNGOLOGY = "otolaryngology"
    UROLOGY = "urology"
    ORTHOPEDICS = "orthopedics"
    GENERAL_PRACTICE = "general_practice"


# =============================================================================
# Clinical Data Models
# =============================================================================


@dataclass
class VitalSigns:
    """Patient vital signs."""

    heart_rate: int | None = None  # bpm
    blood_pressure_systolic: int | None = None  # mmHg
    blood_pressure_diastolic: int | None = None  # mmHg
    respiratory_rate: int | None = None  # breaths/min
    temperature: float | None = None  # °C
    oxygen_saturation: int | None = None  # %
    pain_scale: int | None = None  # 0-10
    glasgow_coma_scale: int | None = None  # 3-15

    @property
    def mean_arterial_pressure(self) -> float | None:
        """Calculate MAP."""
        if self.blood_pressure_systolic and self.blood_pressure_diastolic:
            return (
                self.blood_pressure_diastolic
                + (self.blood_pressure_systolic - self.blood_pressure_diastolic) / 3
            )
        return None

    @property
    def is_tachycardic(self) -> bool:
        """Heart rate > 100 bpm."""
        return self.heart_rate is not None and self.heart_rate > 100

    @property
    def is_hypotensive(self) -> bool:
        """Systolic BP < 90 mmHg."""
        return (
            self.blood_pressure_systolic is not None
            and self.blood_pressure_systolic < 90
        )

    @property
    def is_febrile(self) -> bool:
        """Temperature > 38°C."""
        return self.temperature is not None and self.temperature > 38.0

    @property
    def is_hypoxic(self) -> bool:
        """SpO2 < 92%."""
        return self.oxygen_saturation is not None and self.oxygen_saturation < 92

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "heart_rate": self.heart_rate,
            "blood_pressure": (
                f"{self.blood_pressure_systolic}/{self.blood_pressure_diastolic}"
                if self.blood_pressure_systolic
                else None
            ),
            "respiratory_rate": self.respiratory_rate,
            "temperature": self.temperature,
            "oxygen_saturation": self.oxygen_saturation,
            "pain_scale": self.pain_scale,
            "glasgow_coma_scale": self.glasgow_coma_scale,
            "mean_arterial_pressure": self.mean_arterial_pressure,
        }


@dataclass
class LabValue:
    """Laboratory value with reference range."""

    name: str
    value: float
    unit: str
    reference_min: float | None = None
    reference_max: float | None = None
    critical_min: float | None = None
    critical_max: float | None = None

    @property
    def is_abnormal(self) -> bool:
        """Check if value is outside reference range."""
        if self.reference_min is not None and self.value < self.reference_min:
            return True
        if self.reference_max is not None and self.value > self.reference_max:
            return True
        return False

    @property
    def is_critical(self) -> bool:
        """Check if value is critically abnormal."""
        if self.critical_min is not None and self.value < self.critical_min:
            return True
        if self.critical_max is not None and self.value > self.critical_max:
            return True
        return False

    @property
    def interpretation(self) -> str:
        """Get interpretation string."""
        if self.is_critical:
            return "CRÍTICO"
        if self.is_abnormal:
            if self.reference_min and self.value < self.reference_min:
                return "↓ Bajo"
            return "↑ Alto"
        return "Normal"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "value": self.value,
            "unit": self.unit,
            "reference_range": (
                f"{self.reference_min}-{self.reference_max}"
                if self.reference_min
                else None
            ),
            "interpretation": self.interpretation,
            "is_critical": self.is_critical,
        }


@dataclass
class CIE10Code:
    """CIE-10 diagnosis code."""

    code: str
    description: str
    chapter: str | None = None
    category: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "code": self.code,
            "description": self.description,
            "chapter": self.chapter,
            "category": self.category,
        }


@dataclass
class Symptom:
    """Clinical symptom with characteristics."""

    name: str
    onset: str | None = None  # acute, subacute, chronic
    duration: str | None = None  # e.g., "3 days"
    severity: str | None = None  # mild, moderate, severe
    location: str | None = None  # body location
    character: str | None = None  # quality of symptom
    aggravating: list[str] = field(default_factory=list)
    relieving: list[str] = field(default_factory=list)
    associated: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "onset": self.onset,
            "duration": self.duration,
            "severity": self.severity,
            "location": self.location,
            "character": self.character,
            "aggravating": self.aggravating,
            "relieving": self.relieving,
            "associated": self.associated,
        }


@dataclass
class Medication:
    """Medication with dosage."""

    name: str
    dose: str | None = None
    route: str | None = None  # oral, IV, IM, SC, topical
    frequency: str | None = None  # e.g., "every 8 hours"
    duration: str | None = None  # e.g., "7 days"
    indication: str | None = None
    contraindications: list[str] = field(default_factory=list)
    interactions: list[str] = field(default_factory=list)
    evidence_level: EvidenceLevel | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "dose": self.dose,
            "route": self.route,
            "frequency": self.frequency,
            "duration": self.duration,
            "indication": self.indication,
            "contraindications": self.contraindications,
            "evidence_level": (
                self.evidence_level.value if self.evidence_level else None
            ),
        }


# =============================================================================
# Diagnostic Models
# =============================================================================


@dataclass
class DiagnosticHypothesis:
    """Diagnostic hypothesis with probability."""

    diagnosis: str
    cie10: CIE10Code | None = None
    probability: float = 0.0  # 0.0 to 1.0
    probability_label: str = ""  # "Alta", "Moderada", "Baja"
    supporting_findings: list[str] = field(default_factory=list)
    against_findings: list[str] = field(default_factory=list)
    next_steps: list[str] = field(default_factory=list)
    specialty: Specialty | None = None

    def __post_init__(self):
        """Set probability label based on probability."""
        if not self.probability_label:
            if self.probability >= 0.7:
                self.probability_label = "Alta"
            elif self.probability >= 0.3:
                self.probability_label = "Moderada"
            elif self.probability >= 0.1:
                self.probability_label = "Baja"
            else:
                self.probability_label = "Muy baja"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "diagnosis": self.diagnosis,
            "cie10": self.cie10.to_dict() if self.cie10 else None,
            "probability": self.probability,
            "probability_label": self.probability_label,
            "probability_range": f"{int(self.probability * 100)}%",
            "supporting_findings": self.supporting_findings,
            "against_findings": self.against_findings,
            "next_steps": self.next_steps,
            "specialty": self.specialty.value if self.specialty else None,
        }


@dataclass
class DiagnosticPlan:
    """Plan for diagnostic workup."""

    study: str
    justification: str
    priority: str = "routine"  # stat, urgent, routine
    reference_values: str | None = None
    interpretation_guide: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "study": self.study,
            "justification": self.justification,
            "priority": self.priority,
            "reference_values": self.reference_values,
            "interpretation_guide": self.interpretation_guide,
        }


@dataclass
class TreatmentPlan:
    """Treatment plan with medications and interventions."""

    medications: list[Medication] = field(default_factory=list)
    interventions: list[str] = field(default_factory=list)
    lifestyle_modifications: list[str] = field(default_factory=list)
    monitoring: list[str] = field(default_factory=list)
    follow_up: str | None = None
    referrals: list[str] = field(default_factory=list)
    patient_education: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "medications": [m.to_dict() for m in self.medications],
            "interventions": self.interventions,
            "lifestyle_modifications": self.lifestyle_modifications,
            "monitoring": self.monitoring,
            "follow_up": self.follow_up,
            "referrals": self.referrals,
            "patient_education": self.patient_education,
        }


# =============================================================================
# Triage Models
# =============================================================================


@dataclass
class TriageAssessment:
    """Triage assessment result."""

    level: TriageLevel
    urgency: UrgencyLevel
    chief_complaint: str
    discriminators: list[str] = field(default_factory=list)
    red_flags: list[str] = field(default_factory=list)
    vital_signs: VitalSigns | None = None
    recommended_action: str = ""
    max_wait_time: str = ""
    disposition: str = ""  # ED, urgent care, primary care, home

    def __post_init__(self):
        """Set recommended action based on level."""
        if not self.recommended_action:
            actions = {
                TriageLevel.LEVEL_1: "Atención inmediata - Activar código de emergencia",
                TriageLevel.LEVEL_2: "Atención urgente - Evaluación en <10 minutos",
                TriageLevel.LEVEL_3: "Atención prioritaria - Evaluación en <30 minutos",
                TriageLevel.LEVEL_4: "Atención programada - Evaluación en <60 minutos",
                TriageLevel.LEVEL_5: "Atención diferida - Puede esperar >2 horas",
            }
            self.recommended_action = actions.get(self.level, "")

        if not self.max_wait_time:
            self.max_wait_time = f"{self.level.max_wait_minutes} minutos"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "level": self.level.value,
            "level_number": int(self.level.name.split("_")[1]),
            "color": self.level.color,
            "urgency": self.urgency.value,
            "chief_complaint": self.chief_complaint,
            "discriminators": self.discriminators,
            "red_flags": self.red_flags,
            "vital_signs": self.vital_signs.to_dict() if self.vital_signs else None,
            "recommended_action": self.recommended_action,
            "max_wait_time": self.max_wait_time,
            "disposition": self.disposition,
        }


# =============================================================================
# Clinical Case Models
# =============================================================================


@dataclass
class PatientProfile:
    """Patient demographic and clinical profile."""

    age: int | None = None
    sex: str | None = None  # M, F, other
    weight_kg: float | None = None
    height_cm: float | None = None
    medical_history: list[str] = field(default_factory=list)
    surgical_history: list[str] = field(default_factory=list)
    medications: list[str] = field(default_factory=list)
    allergies: list[str] = field(default_factory=list)
    social_history: dict[str, Any] = field(default_factory=dict)
    family_history: list[str] = field(default_factory=list)

    @property
    def bmi(self) -> float | None:
        """Calculate BMI."""
        if self.weight_kg and self.height_cm:
            height_m = self.height_cm / 100
            return round(self.weight_kg / (height_m**2), 1)
        return None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "age": self.age,
            "sex": self.sex,
            "weight_kg": self.weight_kg,
            "height_cm": self.height_cm,
            "bmi": self.bmi,
            "medical_history": self.medical_history,
            "surgical_history": self.surgical_history,
            "current_medications": self.medications,
            "allergies": self.allergies,
            "social_history": self.social_history,
            "family_history": self.family_history,
        }


@dataclass
class ClinicalCase:
    """Complete clinical case for analysis."""

    query: str
    consultation_type: ConsultationType
    patient: PatientProfile | None = None
    chief_complaint: str = ""
    symptoms: list[Symptom] = field(default_factory=list)
    vital_signs: VitalSigns | None = None
    physical_exam: dict[str, str] = field(default_factory=dict)
    lab_values: list[LabValue] = field(default_factory=list)
    imaging: list[str] = field(default_factory=list)

    # Analysis results (filled by reasoning)
    triage: TriageAssessment | None = None
    differential_diagnosis: list[DiagnosticHypothesis] = field(default_factory=list)
    primary_diagnosis: DiagnosticHypothesis | None = None
    diagnostic_plan: list[DiagnosticPlan] = field(default_factory=list)
    treatment_plan: TreatmentPlan | None = None
    admission_criteria: list[str] = field(default_factory=list)
    prognosis: str = ""

    # Metadata
    specialty: Specialty | None = None
    modality: str = ""  # Ambulatorio, Hospitalizado, Urgencias
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "query": self.query,
            "consultation_type": self.consultation_type.value,
            "patient": self.patient.to_dict() if self.patient else None,
            "chief_complaint": self.chief_complaint,
            "symptoms": [s.to_dict() for s in self.symptoms],
            "vital_signs": self.vital_signs.to_dict() if self.vital_signs else None,
            "physical_exam": self.physical_exam,
            "lab_values": [l.to_dict() for l in self.lab_values],
            "imaging": self.imaging,
            "triage": self.triage.to_dict() if self.triage else None,
            "differential_diagnosis": [
                d.to_dict() for d in self.differential_diagnosis
            ],
            "primary_diagnosis": (
                self.primary_diagnosis.to_dict() if self.primary_diagnosis else None
            ),
            "diagnostic_plan": [d.to_dict() for d in self.diagnostic_plan],
            "treatment_plan": (
                self.treatment_plan.to_dict() if self.treatment_plan else None
            ),
            "admission_criteria": self.admission_criteria,
            "prognosis": self.prognosis,
            "specialty": self.specialty.value if self.specialty else None,
            "modality": self.modality,
            "created_at": self.created_at.isoformat(),
        }


# =============================================================================
# Response Models
# =============================================================================


@dataclass
class ClinicalResponse:
    """Formatted clinical response."""

    case: ClinicalCase
    formatted_response: str = ""
    summary: str = ""
    references: list[str] = field(default_factory=list)
    disclaimers: list[str] = field(default_factory=list)
    version: str = "25.83"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "case": self.case.to_dict(),
            "formatted_response": self.formatted_response,
            "summary": self.summary,
            "references": self.references,
            "disclaimers": self.disclaimers,
            "version": self.version,
        }
