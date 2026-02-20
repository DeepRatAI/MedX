"""
Medical Knowledge Base.

Re-exports from the legacy knowledge base for backward compatibility.
"""

# Import from legacy module for compatibility
import sys
from pathlib import Path

# Add parent to path for legacy imports
legacy_path = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(legacy_path))

try:
    from medical_knowledge_base import (
        ClinicalProtocol,
        DiagnosticProcedure,
        MedicalCondition,
        MedicalKnowledgeBase,
        Medication,
    )
except ImportError:
    # Stub implementations for when legacy module isn't available
    from dataclasses import dataclass

    @dataclass
    class MedicalCondition:
        """Medical condition data structure."""

        icd10_code: str
        name: str
        category: str
        description: str
        symptoms: list[str]
        risk_factors: list[str]
        complications: list[str]
        diagnostic_criteria: list[str]
        differential_diagnosis: list[str]
        treatment_protocol: list[str]
        emergency_signs: list[str]
        prognosis: str
        follow_up: list[str]

    @dataclass
    class Medication:
        """Medication data structure."""

        name: str
        generic_name: str
        category: str
        indications: list[str]
        contraindications: list[str]
        dosage_adult: str
        dosage_pediatric: str
        side_effects: list[str]
        interactions: list[str]
        monitoring: list[str]
        pregnancy_category: str

    @dataclass
    class DiagnosticProcedure:
        """Diagnostic procedure data structure."""

        name: str
        category: str
        indications: list[str]
        contraindications: list[str]
        preparation: list[str]
        procedure_steps: list[str]
        interpretation: list[str]
        complications: list[str]
        cost_range: str

    @dataclass
    class ClinicalProtocol:
        """Clinical protocol data structure."""

        name: str
        category: str
        indication: str
        steps: list[str]
        decision_points: list[str]
        emergency_modifications: list[str]
        evidence_level: str
        last_updated: str

    class MedicalKnowledgeBase:
        """Stub medical knowledge base."""

        def __init__(self) -> None:
            self.conditions: dict[str, MedicalCondition] = {}
            self.medications: dict[str, Medication] = {}
            self.procedures: dict[str, DiagnosticProcedure] = {}
            self.protocols: dict[str, ClinicalProtocol] = {}


__all__ = [
    "MedicalKnowledgeBase",
    "MedicalCondition",
    "Medication",
    "DiagnosticProcedure",
    "ClinicalProtocol",
]
