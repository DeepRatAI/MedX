# =============================================================================
# MedeX - Medical Module Service
# =============================================================================
"""
Medical service façade that integrates all medical components.

This service provides a unified interface for:
- Triage assessment
- Diagnostic reasoning
- Treatment planning
- Clinical formatting
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

from medex.medical.formatter import ClinicalFormatter, FormatterConfig
from medex.medical.models import (
    ClinicalCase,
    ClinicalResponse,
    ConsultationType,
    DiagnosticHypothesis,
    DiagnosticPlan,
    PatientProfile,
    Specialty,
    Symptom,
    TreatmentPlan,
    TriageAssessment,
    VitalSigns,
)
from medex.medical.reasoner import DiagnosticReasoner, DiagnosticReasonerConfig
from medex.medical.treatment import TreatmentPlanner, TreatmentPlannerConfig
from medex.medical.triage import TriageEngine, TriageEngineConfig

if TYPE_CHECKING:
    from medex.medical.models import LabValue


logger = logging.getLogger(__name__)


# =============================================================================
# Configuration
# =============================================================================


@dataclass
class MedicalServiceConfig:
    """Configuration for medical service."""

    # Triage settings
    triage_config: TriageEngineConfig | None = None

    # Reasoner settings
    reasoner_config: DiagnosticReasonerConfig | None = None

    # Treatment planner settings
    treatment_config: TreatmentPlannerConfig | None = None

    # Formatter settings
    formatter_config: FormatterConfig | None = None

    # Default language
    language: str = "es"

    # Enable auto-triage for all cases
    auto_triage: bool = True

    # Minimum probability for treatment planning
    min_probability_for_treatment: float = 0.4


# =============================================================================
# Medical Service
# =============================================================================


class MedicalService:
    """
    Medical service façade.

    Integrates triage, diagnostic reasoning, treatment planning,
    and response formatting into a unified interface.
    """

    def __init__(self, config: MedicalServiceConfig | None = None) -> None:
        """Initialize medical service."""
        self.config = config or MedicalServiceConfig()

        # Initialize components
        self.triage_engine = TriageEngine(self.config.triage_config)
        self.reasoner = DiagnosticReasoner(self.config.reasoner_config)
        self.treatment_planner = TreatmentPlanner(self.config.treatment_config)
        self.formatter = ClinicalFormatter(self.config.formatter_config)

        logger.info("Medical service initialized")

    async def analyze_case(
        self,
        symptoms: list[Symptom],
        patient: PatientProfile | None = None,
        vital_signs: VitalSigns | None = None,
        lab_values: list[LabValue] | None = None,
        consultation_type: ConsultationType = ConsultationType.EDUCATIONAL,
    ) -> ClinicalResponse:
        """
        Perform complete clinical analysis.

        Args:
            symptoms: List of patient symptoms
            patient: Patient profile with demographics and history
            vital_signs: Current vital signs
            lab_values: Laboratory values if available
            consultation_type: Type of consultation

        Returns:
            ClinicalResponse with complete analysis
        """
        logger.info(f"Analyzing case with {len(symptoms)} symptoms")

        # Build clinical case
        case = ClinicalCase(
            symptoms=symptoms,
            patient=patient,
            vital_signs=vital_signs,
            lab_values=lab_values or [],
        )

        # Step 1: Triage assessment
        if self.config.auto_triage:
            case.triage = self._assess_triage(case)
            logger.info(
                f"Triage level: {case.triage.level.name if case.triage else 'N/A'}"
            )

        # Step 2: Diagnostic reasoning
        case.differential_diagnosis = await self._generate_differential(case)
        logger.info(f"Generated {len(case.differential_diagnosis)} diagnoses")

        # Step 3: Diagnostic plan
        if case.differential_diagnosis:
            case.diagnostic_plan = self._create_diagnostic_plan(case)

        # Step 4: Treatment planning
        if case.differential_diagnosis:
            primary = case.differential_diagnosis[0]
            if primary.probability >= self.config.min_probability_for_treatment:
                case.treatment_plan = self._create_treatment_plan(case, primary)

        # Step 5: Format response
        response = self.formatter.format_response(case, consultation_type)

        logger.info("Case analysis complete")
        return response

    def _assess_triage(self, case: ClinicalCase) -> TriageAssessment:
        """Perform triage assessment."""
        # Build chief complaint from symptoms
        chief_complaint = ", ".join(s.name for s in case.symptoms)

        return self.triage_engine.assess(
            chief_complaint=chief_complaint,
            vital_signs=case.vital_signs,
            symptoms=[s.name for s in case.symptoms],
        )

    async def _generate_differential(
        self,
        case: ClinicalCase,
    ) -> list[DiagnosticHypothesis]:
        """Generate differential diagnosis."""
        return self.reasoner.analyze(case)

    def _create_diagnostic_plan(self, case: ClinicalCase) -> list[DiagnosticPlan]:
        """Create diagnostic workup plan."""
        return self.reasoner.generate_diagnostic_plan(case)

    def _create_treatment_plan(
        self,
        case: ClinicalCase,
        primary_diagnosis: DiagnosticHypothesis,
    ) -> TreatmentPlan:
        """Create treatment plan."""
        return self.treatment_planner.create_plan(case, primary_diagnosis)

    # -------------------------------------------------------------------------
    # Direct Access Methods
    # -------------------------------------------------------------------------

    def quick_triage(
        self,
        chief_complaint: str,
        vital_signs: VitalSigns | None = None,
    ) -> TriageAssessment:
        """
        Quick triage assessment without full analysis.

        Args:
            chief_complaint: Main complaint text
            vital_signs: Vital signs if available

        Returns:
            TriageAssessment with urgency level
        """
        return self.triage_engine.assess(
            chief_complaint=chief_complaint,
            vital_signs=vital_signs,
        )

    def is_emergency(
        self,
        chief_complaint: str,
        vital_signs: VitalSigns | None = None,
    ) -> bool:
        """
        Quick check if case is an emergency.

        Args:
            chief_complaint: Main complaint
            vital_signs: Vital signs

        Returns:
            True if emergency
        """
        return self.triage_engine.is_emergency(
            chief_complaint=chief_complaint,
            vital_signs=vital_signs,
        )

    def get_emergency_warning(self, language: str = "es") -> str:
        """Get emergency warning message."""
        return self.triage_engine.get_emergency_message(language)

    def interpret_lab(
        self,
        name: str,
        value: float,
        sex: str = "M",
    ) -> dict[str, str]:
        """
        Interpret a single lab value.

        Args:
            name: Lab test name
            value: Numeric result
            sex: Patient sex (M/F)

        Returns:
            Dict with interpretation and reference range
        """
        return self.reasoner.interpret_lab(name, value, sex)

    def get_specialty_for_diagnosis(
        self,
        diagnosis: str,
    ) -> Specialty:
        """Get appropriate specialty for a diagnosis."""
        # Map common diagnoses to specialties
        diagnosis_lower = diagnosis.lower()

        cardio_terms = [
            "coronario",
            "cardíaco",
            "infarto",
            "arritmia",
            "insuficiencia cardíaca",
        ]
        neuro_terms = ["stroke", "avc", "cefalea", "migraña", "epilepsia"]
        gastro_terms = ["celíaca", "gastritis", "hepatitis", "colitis"]
        rheum_terms = ["dermatomiositis", "artritis", "lupus", "vasculitis"]
        endo_terms = ["diabetes", "tiroides", "hipotiroidismo", "hipertiroidismo"]
        pulmo_terms = ["neumonía", "asma", "epoc", "bronquitis"]

        if any(term in diagnosis_lower for term in cardio_terms):
            return Specialty.CARDIOLOGY
        if any(term in diagnosis_lower for term in neuro_terms):
            return Specialty.NEUROLOGY
        if any(term in diagnosis_lower for term in gastro_terms):
            return Specialty.GASTROENTEROLOGY
        if any(term in diagnosis_lower for term in rheum_terms):
            return Specialty.RHEUMATOLOGY
        if any(term in diagnosis_lower for term in endo_terms):
            return Specialty.ENDOCRINOLOGY
        if any(term in diagnosis_lower for term in pulmo_terms):
            return Specialty.PULMONOLOGY

        return Specialty.INTERNAL_MEDICINE


# =============================================================================
# Factory Functions
# =============================================================================


def create_medical_service(
    config: MedicalServiceConfig | None = None,
) -> MedicalService:
    """
    Create medical service.

    Args:
        config: Optional configuration

    Returns:
        Configured MedicalService
    """
    return MedicalService(config)
