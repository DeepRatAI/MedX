# =============================================================================
# MedeX - Knowledge Module Tests
# =============================================================================
"""
Tests for the MedeX Knowledge module.

Covers:
- medical_base.py: MedicalCondition, Medication, DiagnosticProcedure,
  ClinicalProtocol, MedicalKnowledgeBase
- pharmaceutical.py: DrugMonograph, DrugInteraction, PharmaceuticalDatabase,
  InteractionSeverity, RouteOfAdministration
"""

from __future__ import annotations

import pytest

from medex.knowledge.medical_base import (
    ClinicalProtocol,
    DiagnosticProcedure,
    MedicalCondition,
    MedicalKnowledgeBase,
    Medication,
)
from medex.knowledge.pharmaceutical import (
    DrugInteraction,
    DrugMonograph,
    InteractionSeverity,
    PharmaceuticalDatabase,
    RouteOfAdministration,
)

# =============================================================================
# InteractionSeverity Enum Tests
# =============================================================================


class TestInteractionSeverity:
    """Tests for InteractionSeverity enum."""

    def test_severity_values(self):
        """Test all severity enum values."""
        assert InteractionSeverity.MINOR.value == "minor"
        assert InteractionSeverity.MODERATE.value == "moderate"
        assert InteractionSeverity.MAJOR.value == "major"
        assert InteractionSeverity.CONTRAINDICATED.value == "contraindicated"

    def test_severity_members(self):
        """Test all severity members exist."""
        members = list(InteractionSeverity)
        assert len(members) == 4

    def test_severity_comparison(self):
        """Test severity enum values are distinct."""
        assert InteractionSeverity.MINOR != InteractionSeverity.MAJOR
        assert InteractionSeverity.MODERATE != InteractionSeverity.CONTRAINDICATED


# =============================================================================
# RouteOfAdministration Enum Tests
# =============================================================================


class TestRouteOfAdministration:
    """Tests for RouteOfAdministration enum."""

    def test_route_values(self):
        """Test core route enum values."""
        assert RouteOfAdministration.ORAL.value == "oral"
        assert RouteOfAdministration.IV.value == "intravenous"
        assert RouteOfAdministration.IM.value == "intramuscular"
        assert RouteOfAdministration.SC.value == "subcutaneous"
        assert RouteOfAdministration.TOPICAL.value == "topical"

    def test_route_members(self):
        """Test all route members exist."""
        members = list(RouteOfAdministration)
        assert len(members) >= 5  # At least 5 standard routes


# =============================================================================
# MedicalCondition Tests
# =============================================================================


class TestMedicalCondition:
    """Tests for MedicalCondition dataclass."""

    def _make_condition(self, **overrides) -> MedicalCondition:
        """Helper to create a MedicalCondition with defaults."""
        defaults = {
            "icd10_code": "I10",
            "name": "Hypertension",
            "category": "Cardiovascular",
            "description": "Elevated blood pressure",
            "symptoms": ["headache", "dizziness"],
            "risk_factors": ["obesity", "smoking"],
            "complications": ["stroke", "heart failure"],
            "diagnostic_criteria": ["BP > 140/90 on 2+ occasions"],
            "differential_diagnosis": ["White coat hypertension"],
            "treatment_protocol": ["Lifestyle changes", "ACE inhibitors"],
            "emergency_signs": ["BP > 180/120", "Vision changes"],
            "prognosis": "Good with treatment",
            "follow_up": ["Quarterly BP checks"],
        }
        defaults.update(overrides)
        return MedicalCondition(**defaults)

    def test_create_condition(self):
        """Test creating a medical condition with all fields."""
        condition = self._make_condition()

        assert condition.name == "Hypertension"
        assert condition.icd10_code == "I10"
        assert condition.description == "Elevated blood pressure"
        assert "headache" in condition.symptoms
        assert len(condition.risk_factors) == 2

    def test_condition_category(self):
        """Test condition category field."""
        condition = self._make_condition(category="Endocrine")
        assert condition.category == "Endocrine"

    def test_condition_complications(self):
        """Test condition complications field."""
        condition = self._make_condition(
            complications=["Retinopathy", "Nephropathy", "Neuropathy"]
        )
        assert len(condition.complications) == 3
        assert "Nephropathy" in condition.complications

    def test_condition_emergency_signs(self):
        """Test condition emergency signs field."""
        condition = self._make_condition(
            emergency_signs=["Altered consciousness", "Chest pain"]
        )
        assert len(condition.emergency_signs) == 2


# =============================================================================
# Medication Tests
# =============================================================================


class TestMedication:
    """Tests for Medication dataclass."""

    def _make_medication(self, **overrides) -> Medication:
        """Helper to create a Medication with defaults."""
        defaults = {
            "name": "Amoxicillin",
            "generic_name": "Amoxicillin",
            "category": "Antibiotic",
            "indications": ["Upper respiratory infection"],
            "contraindications": ["Penicillin allergy"],
            "dosage_adult": "500mg q8h",
            "dosage_pediatric": "25mg/kg/day divided q8h",
            "side_effects": ["Nausea", "Diarrhea", "Rash"],
            "interactions": ["Methotrexate", "Warfarin"],
            "monitoring": ["Renal function", "CBC"],
            "pregnancy_category": "B",
        }
        defaults.update(overrides)
        return Medication(**defaults)

    def test_create_medication(self):
        """Test creating a medication with all fields."""
        med = self._make_medication()

        assert med.name == "Amoxicillin"
        assert med.generic_name == "Amoxicillin"
        assert med.category == "Antibiotic"
        assert med.pregnancy_category == "B"

    def test_medication_dosage_fields(self):
        """Test medication dosage fields."""
        med = self._make_medication(
            dosage_adult="10mg/day",
            dosage_pediatric="5mg/kg/day",
        )
        assert med.dosage_adult == "10mg/day"
        assert med.dosage_pediatric == "5mg/kg/day"

    def test_medication_interactions(self):
        """Test medication drug interactions list."""
        med = self._make_medication(interactions=["Aspirin", "Ibuprofen", "Naproxen"])
        assert len(med.interactions) == 3
        assert "Aspirin" in med.interactions


# =============================================================================
# DiagnosticProcedure Tests
# =============================================================================


class TestDiagnosticProcedure:
    """Tests for DiagnosticProcedure dataclass."""

    def _make_procedure(self, **overrides) -> DiagnosticProcedure:
        """Helper to create a DiagnosticProcedure with defaults."""
        defaults = {
            "name": "Complete Blood Count",
            "category": "Laboratory",
            "indications": ["Anemia screening", "Infection evaluation"],
            "contraindications": [],
            "preparation": ["No fasting required"],
            "procedure_steps": ["Venipuncture", "Analyze sample"],
            "interpretation": ["Low Hgb suggests anemia"],
            "complications": ["Bruising at puncture site"],
            "cost_range": "Low",
        }
        defaults.update(overrides)
        return DiagnosticProcedure(**defaults)

    def test_create_procedure(self):
        """Test creating a diagnostic procedure."""
        proc = self._make_procedure()

        assert proc.name == "Complete Blood Count"
        assert proc.category == "Laboratory"
        assert len(proc.indications) == 2

    def test_procedure_steps(self):
        """Test procedure steps field."""
        proc = self._make_procedure(
            procedure_steps=["Prepare patient", "Administer contrast", "Scan"]
        )
        assert len(proc.procedure_steps) == 3

    def test_procedure_cost_range(self):
        """Test procedure cost range field."""
        proc = self._make_procedure(cost_range="High")
        assert proc.cost_range == "High"


# =============================================================================
# ClinicalProtocol Tests
# =============================================================================


class TestClinicalProtocol:
    """Tests for ClinicalProtocol dataclass."""

    def _make_protocol(self, **overrides) -> ClinicalProtocol:
        """Helper to create a ClinicalProtocol with defaults."""
        defaults = {
            "name": "Sepsis Management",
            "category": "Emergency",
            "indication": "Suspected sepsis",
            "steps": ["Measure lactate", "Blood cultures", "Antibiotics"],
            "decision_points": ["Lactate > 2 mmol/L"],
            "emergency_modifications": ["Vasopressors if MAP < 65"],
            "evidence_level": "1A",
            "last_updated": "2024-01-01",
        }
        defaults.update(overrides)
        return ClinicalProtocol(**defaults)

    def test_create_protocol(self):
        """Test creating a clinical protocol."""
        protocol = self._make_protocol()

        assert protocol.name == "Sepsis Management"
        assert len(protocol.steps) == 3
        assert protocol.evidence_level == "1A"

    def test_protocol_category(self):
        """Test protocol category field."""
        protocol = self._make_protocol(category="Cardiology")
        assert protocol.category == "Cardiology"

    def test_protocol_decision_points(self):
        """Test protocol decision points."""
        protocol = self._make_protocol(
            decision_points=["BP < 90 systolic", "SpO2 < 92%"]
        )
        assert len(protocol.decision_points) == 2


# =============================================================================
# MedicalKnowledgeBase Tests
# =============================================================================


class TestMedicalKnowledgeBase:
    """Tests for MedicalKnowledgeBase class."""

    def test_create_knowledge_base(self):
        """Test creating an empty knowledge base."""
        kb = MedicalKnowledgeBase()
        assert kb is not None

    def test_knowledge_base_has_conditions(self):
        """Test knowledge base conditions dict."""
        kb = MedicalKnowledgeBase()
        assert isinstance(kb.conditions, dict)

    def test_knowledge_base_has_medications(self):
        """Test knowledge base medications dict."""
        kb = MedicalKnowledgeBase()
        assert isinstance(kb.medications, dict)

    def test_knowledge_base_has_procedures(self):
        """Test knowledge base procedures dict."""
        kb = MedicalKnowledgeBase()
        assert isinstance(kb.procedures, dict)

    def test_knowledge_base_has_protocols(self):
        """Test knowledge base protocols dict."""
        kb = MedicalKnowledgeBase()
        assert isinstance(kb.protocols, dict)


# =============================================================================
# DrugMonograph Tests
# =============================================================================


class TestDrugMonograph:
    """Tests for DrugMonograph dataclass."""

    def test_create_monograph(self):
        """Test creating a drug monograph with all required fields."""
        mono = DrugMonograph(
            name="Metformin",
            generic_name="Metformin HCl",
            brand_names=["Glucophage"],
            drug_class="Biguanide",
            therapeutic_category="Antidiabetic",
            mechanism_of_action="Decreases hepatic glucose production",
            indications=["Type 2 diabetes mellitus"],
            dosages=["500mg BID"],
            contraindications=["eGFR < 30"],
            adverse_effects=["GI upset"],
            pharmacokinetics="T1/2 ~6h",
            monitoring_parameters=["HbA1c", "Renal function"],
            patient_counseling=["Take with meals"],
            storage_conditions="Room temperature",
            pregnancy_category="B",
            lactation_safety="Compatible",
            pediatric_use=">10 years",
            geriatric_use="Adjust for renal function",
            cost_effectiveness="High",
        )

        assert mono.name == "Metformin"
        assert mono.generic_name == "Metformin HCl"
        assert mono.drug_class == "Biguanide"
        assert "Glucophage" in mono.brand_names

    def test_monograph_has_expected_fields(self):
        """Test monograph has key expected fields."""
        fields = DrugMonograph.__dataclass_fields__
        assert "name" in fields
        assert "generic_name" in fields
        assert "drug_class" in fields


# =============================================================================
# DrugInteraction Tests
# =============================================================================


class TestDrugInteraction:
    """Tests for DrugInteraction dataclass."""

    def test_create_interaction(self):
        """Test creating a drug interaction."""
        interaction = DrugInteraction(
            drug_a="Warfarin",
            drug_b="Aspirin",
            severity=InteractionSeverity.MAJOR,
            mechanism="Synergistic anticoagulation",
            clinical_effect="Increased bleeding risk",
            management="Avoid or monitor INR closely",
            onset="rapid",
            documentation="excellent",
        )

        assert interaction.drug_a == "Warfarin"
        assert interaction.drug_b == "Aspirin"
        assert interaction.severity == InteractionSeverity.MAJOR
        assert "bleeding" in interaction.clinical_effect.lower()

    def test_create_moderate_interaction(self):
        """Test creating a moderate interaction."""
        interaction = DrugInteraction(
            drug_a="Ibuprofen",
            drug_b="Lisinopril",
            severity=InteractionSeverity.MODERATE,
            mechanism="NSAIDs reduce ACE inhibitor efficacy",
            clinical_effect="Reduced antihypertensive effect",
            management="Monitor blood pressure",
            onset="delayed",
            documentation="good",
        )

        assert interaction.severity == InteractionSeverity.MODERATE

    def test_create_contraindicated_interaction(self):
        """Test creating a contraindicated interaction."""
        interaction = DrugInteraction(
            drug_a="Methotrexate",
            drug_b="Trimethoprim",
            severity=InteractionSeverity.CONTRAINDICATED,
            mechanism="Bone marrow suppression",
            clinical_effect="Pancytopenia risk",
            management="Do not combine",
            onset="delayed",
            documentation="excellent",
        )

        assert interaction.severity == InteractionSeverity.CONTRAINDICATED


# =============================================================================
# PharmaceuticalDatabase Tests
# =============================================================================


class TestPharmaceuticalDatabase:
    """Tests for PharmaceuticalDatabase class."""

    def test_create_database(self):
        """Test creating a pharmaceutical database."""
        db = PharmaceuticalDatabase()
        assert db is not None

    def test_database_has_monographs(self):
        """Test database monographs collection."""
        db = PharmaceuticalDatabase()
        assert isinstance(db.monographs, dict)

    def test_database_has_interactions(self):
        """Test database interactions collection."""
        db = PharmaceuticalDatabase()
        # interactions may be list or dict depending on implementation
        assert isinstance(db.interactions, (list, dict))


# =============================================================================
# Run Tests
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
