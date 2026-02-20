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
        MedicalKnowledgeBase,
        MedicalCondition,
        Medication,
        DiagnosticProcedure,
        ClinicalProtocol,
    )
except ImportError:
    # Stub implementations for when legacy module isn't available
    from dataclasses import dataclass
    from typing import Dict, List, Any

    @dataclass
    class MedicalCondition:
        """Medical condition data structure."""

        icd10_code: str
        name: str
        category: str
        description: str
        symptoms: List[str]
        risk_factors: List[str]
        complications: List[str]
        diagnostic_criteria: List[str]
        differential_diagnosis: List[str]
        treatment_protocol: List[str]
        emergency_signs: List[str]
        prognosis: str
        follow_up: List[str]

    @dataclass
    class Medication:
        """Medication data structure."""

        name: str
        generic_name: str
        category: str
        indications: List[str]
        contraindications: List[str]
        dosage_adult: str
        dosage_pediatric: str
        side_effects: List[str]
        interactions: List[str]
        monitoring: List[str]
        pregnancy_category: str

    @dataclass
    class DiagnosticProcedure:
        """Diagnostic procedure data structure."""

        name: str
        category: str
        indications: List[str]
        contraindications: List[str]
        preparation: List[str]
        procedure_steps: List[str]
        interpretation: List[str]
        complications: List[str]
        cost_range: str

    @dataclass
    class ClinicalProtocol:
        """Clinical protocol data structure."""

        name: str
        category: str
        indication: str
        steps: List[str]
        decision_points: List[str]
        emergency_modifications: List[str]
        evidence_level: str
        last_updated: str

    class MedicalKnowledgeBase:
        """Stub medical knowledge base."""

        def __init__(self) -> None:
            self.conditions: Dict[str, MedicalCondition] = {}
            self.medications: Dict[str, Medication] = {}
            self.procedures: Dict[str, DiagnosticProcedure] = {}
            self.protocols: Dict[str, ClinicalProtocol] = {}


__all__ = [
    "MedicalKnowledgeBase",
    "MedicalCondition",
    "Medication",
    "DiagnosticProcedure",
    "ClinicalProtocol",
]
