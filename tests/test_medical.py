# =============================================================================
# MedeX - Medical Module Tests
# =============================================================================
"""
Comprehensive tests for the medical module.

Tests:
- Models and data classes
- Triage engine with ESI levels
- Diagnostic reasoner
- Treatment planner
- Clinical formatter
- Medical service integration
"""

import pytest

from medex.medical.formatter import (
    ClinicalFormatter,
    FormatterConfig,
    create_clinical_formatter,
)
from medex.medical.models import (
    CIE10Code,
    ClinicalCase,
    ClinicalResponse,
    ConsultationType,
    DiagnosticHypothesis,
    DiagnosticPlan,
    LabValue,
    Medication,
    PatientProfile,
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
    create_medical_service,
)
from medex.medical.treatment import (
    TreatmentPlanner,
    create_treatment_planner,
)
from medex.medical.triage import TriageEngine, create_triage_engine

# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def normal_vital_signs() -> VitalSigns:
    """Normal vital signs."""
    return VitalSigns(
        heart_rate=75,
        blood_pressure_systolic=120,
        blood_pressure_diastolic=80,
        respiratory_rate=16,
        temperature=36.8,
        oxygen_saturation=98,
        pain_scale=2,
        glasgow_coma_scale=15,
    )


@pytest.fixture
def critical_vital_signs() -> VitalSigns:
    """Critical vital signs."""
    return VitalSigns(
        heart_rate=160,
        blood_pressure_systolic=70,
        blood_pressure_diastolic=40,
        respiratory_rate=32,
        temperature=39.5,
        oxygen_saturation=82,
        pain_scale=10,
        glasgow_coma_scale=6,
    )


@pytest.fixture
def celiac_patient() -> PatientProfile:
    """Patient with celiac disease symptoms."""
    return PatientProfile(
        age=32,
        sex="F",
        weight_kg=55,
        height_cm=165,
        medical_history=["anemia"],
        medications=[],
        allergies=[],
    )


@pytest.fixture
def celiac_symptoms() -> list[Symptom]:
    """Symptoms suggestive of celiac disease."""
    return [
        Symptom(
            name="diarrea crónica",
            onset="chronic",
            duration="6 meses",
            severity="moderate",
        ),
        Symptom(
            name="distensión abdominal",
            onset="chronic",
            associated=["flatulencia", "dolor abdominal"],
        ),
        Symptom(
            name="fatiga",
            onset="chronic",
            severity="moderate",
        ),
        Symptom(
            name="pérdida de peso involuntaria",
            duration="3 meses",
        ),
    ]


@pytest.fixture
def celiac_labs() -> list[LabValue]:
    """Lab values suggestive of celiac disease."""
    return [
        LabValue(
            name="Hemoglobina",
            value=10.5,
            unit="g/dL",
            reference_min=12.0,
            reference_max=16.0,
        ),
        LabValue(
            name="VCM",
            value=75,
            unit="fL",
            reference_min=80,
            reference_max=100,
        ),
        LabValue(
            name="Ferritina",
            value=8,
            unit="ng/mL",
            reference_min=12,
            reference_max=150,
        ),
    ]


@pytest.fixture
def cardiac_symptoms() -> list[Symptom]:
    """Symptoms suggestive of acute coronary syndrome."""
    return [
        Symptom(
            name="dolor torácico opresivo",
            onset="acute",
            duration="30 minutos",
            severity="severe",
            location="retroesternal",
            character="opresivo",
            associated=["disnea", "diaforesis", "náuseas"],
        ),
    ]


# =============================================================================
# Test Models
# =============================================================================


class TestVitalSigns:
    """Test VitalSigns model."""

    def test_creation(self, normal_vital_signs: VitalSigns) -> None:
        """Test vital signs creation."""
        assert normal_vital_signs.heart_rate == 75
        assert normal_vital_signs.blood_pressure_systolic == 120
        assert normal_vital_signs.oxygen_saturation == 98

    def test_mean_arterial_pressure(self, normal_vital_signs: VitalSigns) -> None:
        """Test MAP calculation."""
        map_value = normal_vital_signs.mean_arterial_pressure
        assert map_value is not None
        # MAP = DBP + (SBP - DBP) / 3 = 80 + (120 - 80) / 3 ≈ 93.3
        assert 93 <= map_value <= 94

    def test_is_tachycardic(self) -> None:
        """Test tachycardia detection."""
        normal = VitalSigns(heart_rate=80)
        tachy = VitalSigns(heart_rate=120)

        assert not normal.is_tachycardic
        assert tachy.is_tachycardic

    def test_is_hypotensive(self) -> None:
        """Test hypotension detection."""
        normal = VitalSigns(blood_pressure_systolic=120, blood_pressure_diastolic=80)
        hypo = VitalSigns(blood_pressure_systolic=85, blood_pressure_diastolic=50)

        assert not normal.is_hypotensive
        assert hypo.is_hypotensive

    def test_is_febrile(self) -> None:
        """Test fever detection."""
        normal = VitalSigns(temperature=36.8)
        febrile = VitalSigns(temperature=38.5)

        assert not normal.is_febrile
        assert febrile.is_febrile

    def test_is_hypoxic(self) -> None:
        """Test hypoxia detection."""
        normal = VitalSigns(oxygen_saturation=98)
        hypoxic = VitalSigns(oxygen_saturation=88)

        assert not normal.is_hypoxic
        assert hypoxic.is_hypoxic

    def test_to_dict(self, normal_vital_signs: VitalSigns) -> None:
        """Test dictionary conversion."""
        data = normal_vital_signs.to_dict()

        assert data["heart_rate"] == 75
        assert "120/80" in data["blood_pressure"]


class TestLabValue:
    """Test LabValue model."""

    def test_is_abnormal_low(self) -> None:
        """Test low abnormal detection."""
        lab = LabValue(
            name="Hemoglobina",
            value=10.0,
            unit="g/dL",
            reference_min=12.0,
            reference_max=16.0,
        )

        assert lab.is_abnormal
        assert lab.interpretation == "↓ Bajo"

    def test_is_abnormal_high(self) -> None:
        """Test high abnormal detection."""
        lab = LabValue(
            name="Glucosa",
            value=250,
            unit="mg/dL",
            reference_min=70,
            reference_max=100,
        )

        assert lab.is_abnormal
        assert lab.interpretation == "↑ Alto"

    def test_is_critical(self) -> None:
        """Test critical value detection."""
        lab = LabValue(
            name="Potasio",
            value=6.8,
            unit="mEq/L",
            reference_min=3.5,
            reference_max=5.0,
            critical_max=6.5,
        )

        assert lab.is_critical
        assert lab.interpretation == "CRÍTICO"

    def test_normal_value(self) -> None:
        """Test normal value."""
        lab = LabValue(
            name="Sodio",
            value=140,
            unit="mEq/L",
            reference_min=135,
            reference_max=145,
        )

        assert not lab.is_abnormal
        assert lab.interpretation == "Normal"


class TestDiagnosticHypothesis:
    """Test DiagnosticHypothesis model."""

    def test_probability_label_high(self) -> None:
        """Test high probability label."""
        hypothesis = DiagnosticHypothesis(
            diagnosis="Enfermedad celíaca",
            probability=0.85,
        )

        assert hypothesis.probability_label == "Alta"

    def test_probability_label_moderate(self) -> None:
        """Test moderate probability label."""
        hypothesis = DiagnosticHypothesis(
            diagnosis="Gastritis",
            probability=0.50,
        )

        assert hypothesis.probability_label == "Moderada"

    def test_probability_label_low(self) -> None:
        """Test low probability label."""
        hypothesis = DiagnosticHypothesis(
            diagnosis="Neoplasia",
            probability=0.15,
        )

        assert hypothesis.probability_label == "Baja"

    def test_with_cie10(self) -> None:
        """Test hypothesis with CIE-10 code."""
        cie10 = CIE10Code(code="K90.0", description="Enfermedad celíaca")
        hypothesis = DiagnosticHypothesis(
            diagnosis="Enfermedad celíaca",
            cie10=cie10,
            probability=0.85,
        )

        data = hypothesis.to_dict()
        assert data["cie10"]["code"] == "K90.0"


class TestTriageLevel:
    """Test TriageLevel enum."""

    def test_colors(self) -> None:
        """Test triage colors."""
        assert TriageLevel.LEVEL_1.color == "red"
        assert TriageLevel.LEVEL_2.color == "orange"
        assert TriageLevel.LEVEL_3.color == "yellow"
        assert TriageLevel.LEVEL_4.color == "green"
        assert TriageLevel.LEVEL_5.color == "blue"

    def test_wait_times(self) -> None:
        """Test max wait times."""
        assert TriageLevel.LEVEL_1.max_wait_minutes == 0
        assert TriageLevel.LEVEL_2.max_wait_minutes == 10
        assert TriageLevel.LEVEL_3.max_wait_minutes == 30


class TestPatientProfile:
    """Test PatientProfile model."""

    def test_bmi_calculation(self) -> None:
        """Test BMI calculation."""
        patient = PatientProfile(
            weight_kg=70,
            height_cm=175,
        )

        # BMI = 70 / (1.75^2) ≈ 22.9
        assert patient.bmi is not None
        assert 22.8 <= patient.bmi <= 23.0


# =============================================================================
# Test Triage Engine
# =============================================================================


class TestTriageEngine:
    """Test triage engine."""

    def test_factory_creation(self) -> None:
        """Test factory function."""
        engine = create_triage_engine()
        assert isinstance(engine, TriageEngine)

    def test_level_1_cardiac_arrest(self) -> None:
        """Test Level 1 for cardiac arrest."""
        engine = TriageEngine()

        assessment = engine.assess(
            chief_complaint="paro cardíaco",
            vital_signs=None,
        )

        assert assessment.level == TriageLevel.LEVEL_1
        assert assessment.urgency == UrgencyLevel.CRITICAL

    def test_level_1_unresponsive(self) -> None:
        """Test Level 1 for unresponsive patient."""
        engine = TriageEngine()

        assessment = engine.assess(
            chief_complaint="paciente inconsciente, no responde",
            vital_signs=VitalSigns(glasgow_coma_scale=5),
        )

        assert assessment.level == TriageLevel.LEVEL_1

    def test_level_2_chest_pain(self) -> None:
        """Test Level 2 for chest pain."""
        engine = TriageEngine()

        assessment = engine.assess(
            chief_complaint="dolor de pecho intenso",
            vital_signs=VitalSigns(
                heart_rate=110,
                blood_pressure_systolic=150,
                blood_pressure_diastolic=90,
            ),
        )

        assert assessment.level == TriageLevel.LEVEL_2
        assert "dolor de pecho" in assessment.chief_complaint

    def test_level_2_stroke_symptoms(self) -> None:
        """Test Level 2 for stroke symptoms."""
        engine = TriageEngine()

        assessment = engine.assess(
            chief_complaint="debilidad súbita en brazo derecho, dificultad para hablar",
        )

        assert assessment.level == TriageLevel.LEVEL_2

    def test_level_3_abdominal_pain(self) -> None:
        """Test Level 3 for moderate abdominal pain."""
        engine = TriageEngine()

        assessment = engine.assess(
            chief_complaint="dolor abdominal moderado",
            vital_signs=VitalSigns(
                heart_rate=85,
                blood_pressure_systolic=130,
                blood_pressure_diastolic=85,
                temperature=37.5,
            ),
        )

        # Should be level 3 or 4 depending on resources needed
        assert assessment.level in {TriageLevel.LEVEL_3, TriageLevel.LEVEL_4}

    def test_level_5_minor_symptoms(self) -> None:
        """Test Level 5 for minor symptoms."""
        engine = TriageEngine()

        assessment = engine.assess(
            chief_complaint="resfriado común, moqueo nasal",
            vital_signs=VitalSigns(
                heart_rate=72,
                blood_pressure_systolic=120,
                blood_pressure_diastolic=75,
                temperature=37.0,
                oxygen_saturation=99,
            ),
        )

        assert assessment.level in {TriageLevel.LEVEL_4, TriageLevel.LEVEL_5}

    def test_critical_vital_signs(self, critical_vital_signs: VitalSigns) -> None:
        """Test critical vital signs trigger Level 1."""
        engine = TriageEngine()

        assessment = engine.assess(
            chief_complaint="malestar general",
            vital_signs=critical_vital_signs,
        )

        assert assessment.level == TriageLevel.LEVEL_1
        assert len(assessment.red_flags) > 0

    def test_is_emergency_method(self) -> None:
        """Test is_emergency helper."""
        engine = TriageEngine()

        assert engine.is_emergency("paro cardíaco")
        assert engine.is_emergency("dolor torácico severo")
        assert not engine.is_emergency("dolor de cabeza leve")

    def test_emergency_message(self) -> None:
        """Test emergency message generation."""
        engine = TriageEngine()

        msg_es = engine.get_emergency_message("es")
        msg_en = engine.get_emergency_message("en")

        assert "emergencia" in msg_es.lower() or "urgente" in msg_es.lower()
        assert "emergency" in msg_en.lower()


# =============================================================================
# Test Diagnostic Reasoner
# =============================================================================


class TestDiagnosticReasoner:
    """Test diagnostic reasoner."""

    def test_factory_creation(self) -> None:
        """Test factory function."""
        reasoner = create_diagnostic_reasoner()
        assert isinstance(reasoner, DiagnosticReasoner)

    def test_celiac_disease_diagnosis(
        self,
        celiac_patient: PatientProfile,
        celiac_symptoms: list[Symptom],
        celiac_labs: list[LabValue],
    ) -> None:
        """Test celiac disease diagnosis."""
        reasoner = DiagnosticReasoner()

        case = ClinicalCase(
            query="Paciente con diarrea crónica y fatiga",
            consultation_type=ConsultationType.PROFESSIONAL,
            patient=celiac_patient,
            symptoms=celiac_symptoms,
            lab_values=celiac_labs,
        )

        hypotheses = reasoner.analyze(case)

        assert len(hypotheses) > 0

        # Celiac should be in differential
        diagnoses = [h.diagnosis.lower() for h in hypotheses]
        has_celiac = any("celíaca" in d or "celiaca" in d for d in diagnoses)
        has_anemia = any("anemia" in d for d in diagnoses)

        # Either celiac or iron deficiency anemia should be considered
        assert has_celiac or has_anemia

    def test_iron_deficiency_anemia(self) -> None:
        """Test iron deficiency anemia diagnosis."""
        reasoner = DiagnosticReasoner()

        case = ClinicalCase(
            query="Fatiga y palidez",
            consultation_type=ConsultationType.PROFESSIONAL,
            symptoms=[
                Symptom(name="fatiga crónica"),
                Symptom(name="palidez"),
            ],
            lab_values=[
                LabValue(
                    name="Hemoglobina",
                    value=8.5,
                    unit="g/dL",
                    reference_min=12.0,
                    reference_max=16.0,
                ),
                LabValue(
                    name="Ferritina",
                    value=5,
                    unit="ng/mL",
                    reference_min=12,
                    reference_max=150,
                ),
            ],
        )

        hypotheses = reasoner.analyze(case)

        diagnoses = [h.diagnosis.lower() for h in hypotheses]
        assert any("anemia" in d for d in diagnoses)

    def test_diagnostic_plan_generation(
        self,
        celiac_symptoms: list[Symptom],
    ) -> None:
        """Test diagnostic plan generation."""
        reasoner = DiagnosticReasoner()

        case = ClinicalCase(
            query="Diarrea crónica",
            consultation_type=ConsultationType.PROFESSIONAL,
            symptoms=celiac_symptoms,
        )

        plan = reasoner.generate_diagnostic_plan(case)

        assert len(plan) > 0
        assert all(isinstance(p, DiagnosticPlan) for p in plan)

    def test_lab_interpretation(self) -> None:
        """Test lab value interpretation."""
        reasoner = DiagnosticReasoner()

        result = reasoner.interpret_lab("Hemoglobina", 10.0, "F")

        assert "interpretation" in result
        assert result["interpretation"] in ["bajo", "↓ Bajo", "Low", "Bajo"]

    def test_config_max_differential(self) -> None:
        """Test max differential config."""
        config = DiagnosticReasonerConfig(max_differential=3)
        reasoner = DiagnosticReasoner(config)

        case = ClinicalCase(
            query="Múltiples síntomas",
            consultation_type=ConsultationType.PROFESSIONAL,
            symptoms=[
                Symptom(name="fatiga"),
                Symptom(name="dolor articular"),
                Symptom(name="rash cutáneo"),
            ],
        )

        hypotheses = reasoner.analyze(case)

        assert len(hypotheses) <= 3


# =============================================================================
# Test Treatment Planner
# =============================================================================


class TestTreatmentPlanner:
    """Test treatment planner."""

    def test_factory_creation(self) -> None:
        """Test factory function."""
        planner = create_treatment_planner()
        assert isinstance(planner, TreatmentPlanner)

    def test_celiac_treatment_plan(
        self,
        celiac_patient: PatientProfile,
        celiac_symptoms: list[Symptom],
    ) -> None:
        """Test celiac disease treatment plan."""
        planner = TreatmentPlanner()

        case = ClinicalCase(
            query="Tratamiento para celíaca",
            consultation_type=ConsultationType.PROFESSIONAL,
            patient=celiac_patient,
            symptoms=celiac_symptoms,
        )

        hypothesis = DiagnosticHypothesis(
            diagnosis="Enfermedad celíaca",
            cie10=CIE10Code(code="K90.0", description="Enfermedad celíaca"),
            probability=0.85,
        )

        plan = planner.create_plan(case, hypothesis)

        assert isinstance(plan, TreatmentPlan)

        # Should include iron supplementation
        med_names = [m.name.lower() for m in plan.medications]
        has_iron = any("hierro" in n or "ferroso" in n for n in med_names)

        # Should include gluten-free diet in lifestyle
        lifestyle = " ".join(plan.lifestyle_modifications).lower()
        has_gfd = "gluten" in lifestyle

        # At least one should be true
        assert has_iron or has_gfd

    def test_symptomatic_treatment(self) -> None:
        """Test symptomatic treatment when no diagnosis."""
        planner = TreatmentPlanner()

        case = ClinicalCase(
            query="Dolor y fiebre",
            consultation_type=ConsultationType.EDUCATIONAL,
            symptoms=[
                Symptom(name="dolor de cabeza"),
                Symptom(name="fiebre"),
            ],
        )

        plan = planner.create_plan(case, None)

        assert isinstance(plan, TreatmentPlan)

        # Should include paracetamol for pain/fever
        med_names = [m.name.lower() for m in plan.medications]
        assert any("paracetamol" in n for n in med_names)

    def test_admission_criteria(self) -> None:
        """Test admission criteria generation."""
        planner = TreatmentPlanner()

        case = ClinicalCase(
            query="Paciente crítico",
            consultation_type=ConsultationType.EMERGENCY,
            vital_signs=VitalSigns(
                blood_pressure_systolic=75,
                blood_pressure_diastolic=40,
                oxygen_saturation=85,
            ),
        )

        hypothesis = DiagnosticHypothesis(
            diagnosis="Síndrome coronario agudo",
            probability=0.9,
            specialty=Specialty.CARDIOLOGY,
        )

        criteria = planner.get_admission_criteria(case, hypothesis)

        assert len(criteria) > 0
        assert any("hipotensión" in c.lower() for c in criteria)


# =============================================================================
# Test Clinical Formatter
# =============================================================================


class TestClinicalFormatter:
    """Test clinical formatter."""

    def test_factory_creation(self) -> None:
        """Test factory function."""
        formatter = create_clinical_formatter()
        assert isinstance(formatter, ClinicalFormatter)

    def test_educational_format(
        self,
        celiac_symptoms: list[Symptom],
    ) -> None:
        """Test educational response format."""
        formatter = ClinicalFormatter()

        case = ClinicalCase(
            query="¿Qué es la celiaquía?",
            consultation_type=ConsultationType.EDUCATIONAL,
            symptoms=celiac_symptoms,
            differential_diagnosis=[
                DiagnosticHypothesis(
                    diagnosis="Enfermedad celíaca",
                    probability=0.85,
                ),
            ],
        )

        response = formatter.format_response(case, ConsultationType.EDUCATIONAL)

        assert isinstance(response, ClinicalResponse)
        assert response.disclaimer is not None
        assert (
            "educativo" in response.disclaimer.lower()
            or "información" in response.disclaimer.lower()
        )

    def test_professional_format(
        self,
        celiac_patient: PatientProfile,
        celiac_symptoms: list[Symptom],
        celiac_labs: list[LabValue],
    ) -> None:
        """Test professional response format."""
        formatter = ClinicalFormatter()

        case = ClinicalCase(
            query="Caso clínico",
            consultation_type=ConsultationType.PROFESSIONAL,
            patient=celiac_patient,
            symptoms=celiac_symptoms,
            lab_values=celiac_labs,
            differential_diagnosis=[
                DiagnosticHypothesis(
                    diagnosis="Enfermedad celíaca",
                    cie10=CIE10Code(code="K90.0", description="Enfermedad celíaca"),
                    probability=0.85,
                    specialty=Specialty.GASTROENTEROLOGY,
                ),
            ],
            treatment_plan=TreatmentPlan(
                medications=[
                    Medication(name="Sulfato ferroso", dose="325 mg"),
                ],
                lifestyle_modifications=["Dieta libre de gluten"],
            ),
        )

        response = formatter.format_response(case, ConsultationType.PROFESSIONAL)

        assert isinstance(response, ClinicalResponse)
        assert response.content
        # Should include CIE-10 code
        assert "K90.0" in response.content or "CIE-10" in response.content

    def test_emergency_format(self) -> None:
        """Test emergency response format."""
        formatter = ClinicalFormatter()

        case = ClinicalCase(
            query="Emergencia",
            consultation_type=ConsultationType.EMERGENCY,
            symptoms=[
                Symptom(name="dolor torácico severo"),
            ],
            triage=TriageAssessment(
                level=TriageLevel.LEVEL_1,
                urgency=UrgencyLevel.CRITICAL,
                chief_complaint="dolor torácico",
                red_flags=["dolor torácico severo"],
                disposition="Resucitación",
            ),
        )

        response = formatter.format_response(case, ConsultationType.EMERGENCY)

        assert response.urgency == UrgencyLevel.CRITICAL
        assert (
            "emergencia" in response.disclaimer.lower()
            or "emergency" in response.disclaimer.lower()
        )

    def test_spanish_language(self) -> None:
        """Test Spanish language output."""
        config = FormatterConfig(language="es")
        formatter = ClinicalFormatter(config)

        case = ClinicalCase(
            query="Test",
            consultation_type=ConsultationType.EDUCATIONAL,
        )

        response = formatter.format_response(case)

        # Should have Spanish content
        assert (
            "información" in response.disclaimer.lower()
            or "aviso" in response.disclaimer.lower()
        )


# =============================================================================
# Test Medical Service Integration
# =============================================================================


class TestMedicalService:
    """Test medical service integration."""

    def test_factory_creation(self) -> None:
        """Test factory function."""
        service = create_medical_service()
        assert isinstance(service, MedicalService)

    def test_quick_triage(self) -> None:
        """Test quick triage method."""
        service = MedicalService()

        assessment = service.quick_triage(
            chief_complaint="dolor de pecho intenso",
            vital_signs=VitalSigns(heart_rate=110),
        )

        assert isinstance(assessment, TriageAssessment)
        assert assessment.level in {TriageLevel.LEVEL_1, TriageLevel.LEVEL_2}

    def test_is_emergency(self) -> None:
        """Test is_emergency method."""
        service = MedicalService()

        assert service.is_emergency("paro cardíaco")
        assert service.is_emergency("dolor torácico severo")
        assert not service.is_emergency("dolor de cabeza leve")

    def test_lab_interpretation(self) -> None:
        """Test lab interpretation method."""
        service = MedicalService()

        result = service.interpret_lab("Hemoglobina", 10.0, "F")

        assert "interpretation" in result

    def test_specialty_for_diagnosis(self) -> None:
        """Test specialty mapping."""
        service = MedicalService()

        assert (
            service.get_specialty_for_diagnosis("infarto agudo de miocardio")
            == Specialty.CARDIOLOGY
        )
        assert (
            service.get_specialty_for_diagnosis("enfermedad celíaca")
            == Specialty.GASTROENTEROLOGY
        )
        assert (
            service.get_specialty_for_diagnosis("artritis reumatoide")
            == Specialty.RHEUMATOLOGY
        )

    @pytest.mark.asyncio
    async def test_full_case_analysis(
        self,
        celiac_patient: PatientProfile,
        celiac_symptoms: list[Symptom],
        celiac_labs: list[LabValue],
    ) -> None:
        """Test full case analysis pipeline."""
        service = MedicalService()

        response = await service.analyze_case(
            symptoms=celiac_symptoms,
            patient=celiac_patient,
            lab_values=celiac_labs,
            consultation_type=ConsultationType.PROFESSIONAL,
        )

        assert isinstance(response, ClinicalResponse)
        assert response.content
        assert response.differential_diagnoses is not None

    @pytest.mark.asyncio
    async def test_emergency_case(self) -> None:
        """Test emergency case analysis."""
        service = MedicalService()

        response = await service.analyze_case(
            symptoms=[Symptom(name="dolor torácico opresivo severo")],
            vital_signs=VitalSigns(
                heart_rate=120,
                blood_pressure_systolic=90,
                blood_pressure_diastolic=60,
            ),
            consultation_type=ConsultationType.EMERGENCY,
        )

        assert response.urgency in {UrgencyLevel.CRITICAL, UrgencyLevel.HIGH}


# =============================================================================
# Test Edge Cases
# =============================================================================


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_symptoms(self) -> None:
        """Test with empty symptoms."""
        reasoner = DiagnosticReasoner()

        case = ClinicalCase(
            query="Sin síntomas",
            consultation_type=ConsultationType.EDUCATIONAL,
            symptoms=[],
        )

        hypotheses = reasoner.analyze(case)

        # Should return empty or minimal results
        assert isinstance(hypotheses, list)

    def test_none_vital_signs(self) -> None:
        """Test triage with no vital signs."""
        engine = TriageEngine()

        assessment = engine.assess(
            chief_complaint="dolor de cabeza",
            vital_signs=None,
        )

        assert isinstance(assessment, TriageAssessment)

    def test_patient_without_history(self) -> None:
        """Test with minimal patient info."""
        patient = PatientProfile(age=30, sex="M")

        assert patient.medical_history == []
        assert patient.medications == []
        assert patient.bmi is None

    def test_lab_without_references(self) -> None:
        """Test lab value without reference ranges."""
        lab = LabValue(
            name="Test",
            value=100,
            unit="units",
        )

        assert not lab.is_abnormal
        assert not lab.is_critical
        assert lab.interpretation == "Normal"
