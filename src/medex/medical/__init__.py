# =============================================================================
# MedeX - Medical Module
# =============================================================================
"""
Medical domain module for MedeX.

This module provides clinical reasoning capabilities:
- Triage assessment using ESI 5-level system
- Diagnostic reasoning with differential diagnosis
- Treatment planning with evidence-based protocols
- Clinical response formatting

Components:
- TriageEngine: Emergency triage assessment
- DiagnosticReasoner: Differential diagnosis generation
- TreatmentPlanner: Treatment protocol application
- ClinicalFormatter: Response formatting
- MedicalService: Unified service façade

Example:
    >>> from medex.medical import create_medical_service
    >>> service = create_medical_service()
    >>> response = await service.analyze_case(symptoms=[...])
"""

from medex.medical.formatter import (
    ClinicalFormatter,
    FormatterConfig,
    FormatterLanguage,
    create_clinical_formatter,
)
from medex.medical.models import (
    CIE10Code,
    ClinicalCase,
    ClinicalResponse,
    ConsultationType,
    DiagnosticHypothesis,
    DiagnosticPlan,
    EvidenceLevel,
    LabValue,
    Medication,
    PatientProfile,
    RecommendationGrade,
    Specialty,
    Symptom,
    TreatmentPlan,
    TriageAssessment,
    TriageLevel,
    UrgencyLevel,
    VitalSigns,
)
from medex.medical.reasoner import (
    DiagnosticReasoner,
    DiagnosticReasonerConfig,
    create_diagnostic_reasoner,
)
from medex.medical.service import (
    MedicalService,
    MedicalServiceConfig,
    create_medical_service,
)
from medex.medical.treatment import (
    TreatmentPlanner,
    TreatmentPlannerConfig,
    create_treatment_planner,
)
from medex.medical.triage import (
    TriageEngine,
    TriageEngineConfig,
    create_triage_engine,
)

__all__ = [
    # Models - Enums
    "TriageLevel",
    "UrgencyLevel",
    "EvidenceLevel",
    "RecommendationGrade",
    "ConsultationType",
    "Specialty",
    # Models - Data Classes
    "VitalSigns",
    "LabValue",
    "CIE10Code",
    "Symptom",
    "Medication",
    "DiagnosticHypothesis",
    "DiagnosticPlan",
    "TreatmentPlan",
    "TriageAssessment",
    "PatientProfile",
    "ClinicalCase",
    "ClinicalResponse",
    # Triage
    "TriageEngine",
    "TriageEngineConfig",
    "create_triage_engine",
    # Reasoner
    "DiagnosticReasoner",
    "DiagnosticReasonerConfig",
    "create_diagnostic_reasoner",
    # Treatment
    "TreatmentPlanner",
    "TreatmentPlannerConfig",
    "create_treatment_planner",
    # Formatter
    "ClinicalFormatter",
    "FormatterConfig",
    "FormatterLanguage",
    "create_clinical_formatter",
    # Service
    "MedicalService",
    "MedicalServiceConfig",
    "create_medical_service",
]
