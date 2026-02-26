# =============================================================================
# MedeX - Diagnostic Reasoner
# =============================================================================
"""
Clinical diagnostic reasoning engine.

Features:
- Differential diagnosis generation
- Probability estimation (Bayesian-inspired)
- Supporting/against evidence analysis
- CIE-10 code mapping
- Specialty routing
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from medex.medical.models import (
    CIE10Code,
    ClinicalCase,
    DiagnosticHypothesis,
    DiagnosticPlan,
    LabValue,
    Specialty,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Common Diagnoses Database
# =============================================================================

# Diagnosis patterns with associated symptoms, labs, and CIE-10 codes
DIAGNOSIS_PATTERNS: dict[str, dict[str, Any]] = {
    # Cardiovascular
    "acute_coronary_syndrome": {
        "name": "Síndrome Coronario Agudo",
        "cie10": CIE10Code("I21.9", "Infarto agudo de miocardio, sin especificar"),
        "symptoms": ["chest pain", "dolor torácico", "dolor de pecho", "disnea"],
        "risk_factors": ["diabetes", "hipertensión", "tabaquismo", "dislipidemia"],
        "labs": ["troponina elevada", "ck-mb elevada"],
        "specialty": Specialty.CARDIOLOGY,
        "base_probability": 0.3,
    },
    "heart_failure": {
        "name": "Insuficiencia Cardíaca",
        "cie10": CIE10Code("I50.9", "Insuficiencia cardíaca, no especificada"),
        "symptoms": ["disnea", "edema", "ortopnea", "fatiga"],
        "risk_factors": ["hipertensión", "cardiopatía", "diabetes"],
        "labs": ["bnp elevado", "pro-bnp elevado"],
        "specialty": Specialty.CARDIOLOGY,
        "base_probability": 0.25,
    },
    # Neurological
    "stroke": {
        "name": "Accidente Cerebrovascular",
        "cie10": CIE10Code("I64", "Accidente vascular encefálico agudo"),
        "symptoms": ["debilidad", "hemiparesia", "afasia", "disartria", "facial droop"],
        "risk_factors": ["hipertensión", "fibrilación auricular", "diabetes"],
        "labs": [],
        "specialty": Specialty.NEUROLOGY,
        "base_probability": 0.35,
    },
    "migraine": {
        "name": "Migraña",
        "cie10": CIE10Code("G43.9", "Migraña, no especificada"),
        "symptoms": ["cefalea", "headache", "fotofobia", "náusea", "aura"],
        "risk_factors": ["antecedente migraña", "estrés"],
        "labs": [],
        "specialty": Specialty.NEUROLOGY,
        "base_probability": 0.4,
    },
    # Gastrointestinal
    "celiac_disease": {
        "name": "Enfermedad Celíaca",
        "cie10": CIE10Code("K90.0", "Enfermedad celíaca"),
        "symptoms": ["diarrea", "dolor abdominal", "pérdida de peso", "distensión"],
        "risk_factors": ["antecedente familiar", "enfermedad autoinmune"],
        "labs": ["anti-transglutaminasa positivo", "anemia", "ferritina baja"],
        "specialty": Specialty.GASTROENTEROLOGY,
        "base_probability": 0.3,
    },
    "gastritis": {
        "name": "Gastritis",
        "cie10": CIE10Code("K29.7", "Gastritis, no especificada"),
        "symptoms": ["epigastralgia", "náusea", "dispepsia", "acidez"],
        "risk_factors": ["aines", "h. pylori", "estrés"],
        "labs": [],
        "specialty": Specialty.GASTROENTEROLOGY,
        "base_probability": 0.35,
    },
    # Rheumatological
    "dermatomyositis": {
        "name": "Dermatomiositis",
        "cie10": CIE10Code("M33.1", "Otra dermatomiositis"),
        "symptoms": ["debilidad proximal", "eritema heliotropo", "gottron", "rash"],
        "risk_factors": ["autoinmune", "malignidad oculta"],
        "labs": ["ck elevada", "ldh elevada", "aldolasa elevada", "anti-jo1"],
        "specialty": Specialty.RHEUMATOLOGY,
        "base_probability": 0.25,
    },
    "rheumatoid_arthritis": {
        "name": "Artritis Reumatoide",
        "cie10": CIE10Code("M06.9", "Artritis reumatoide, no especificada"),
        "symptoms": ["artralgia", "rigidez matutina", "sinovitis", "poliartritis"],
        "risk_factors": ["antecedente familiar", "mujer"],
        "labs": ["factor reumatoide", "anti-ccp positivo", "vsg elevada"],
        "specialty": Specialty.RHEUMATOLOGY,
        "base_probability": 0.3,
    },
    # Endocrine
    "diabetes_mellitus_2": {
        "name": "Diabetes Mellitus Tipo 2",
        "cie10": CIE10Code("E11.9", "Diabetes mellitus tipo 2 sin complicaciones"),
        "symptoms": ["poliuria", "polidipsia", "polifagia", "pérdida de peso"],
        "risk_factors": ["obesidad", "sedentarismo", "antecedente familiar"],
        "labs": ["glucosa elevada", "hba1c elevada"],
        "specialty": Specialty.ENDOCRINOLOGY,
        "base_probability": 0.35,
    },
    "hypothyroidism": {
        "name": "Hipotiroidismo",
        "cie10": CIE10Code("E03.9", "Hipotiroidismo, no especificado"),
        "symptoms": [
            "fatiga",
            "aumento de peso",
            "intolerancia al frío",
            "constipación",
        ],
        "risk_factors": ["mujer", "autoinmune", "antecedente tiroides"],
        "labs": ["tsh elevada", "t4 libre baja"],
        "specialty": Specialty.ENDOCRINOLOGY,
        "base_probability": 0.3,
    },
    # Respiratory
    "pneumonia": {
        "name": "Neumonía",
        "cie10": CIE10Code("J18.9", "Neumonía, no especificada"),
        "symptoms": ["tos", "fiebre", "disnea", "dolor pleurítico", "expectoración"],
        "risk_factors": ["edad avanzada", "inmunosupresión", "tabaquismo"],
        "labs": ["leucocitosis", "pcr elevada", "procalcitonina elevada"],
        "specialty": Specialty.PULMONOLOGY,
        "base_probability": 0.35,
    },
    "asthma": {
        "name": "Asma",
        "cie10": CIE10Code("J45.9", "Asma, no especificada"),
        "symptoms": ["sibilancias", "disnea", "tos", "opresión torácica"],
        "risk_factors": ["atopia", "alergia", "antecedente familiar"],
        "labs": [],
        "specialty": Specialty.PULMONOLOGY,
        "base_probability": 0.4,
    },
    # Infectious
    "urinary_tract_infection": {
        "name": "Infección del Tracto Urinario",
        "cie10": CIE10Code(
            "N39.0", "Infección de vías urinarias, sitio no especificado"
        ),
        "symptoms": ["disuria", "polaquiuria", "urgencia", "dolor suprapúbico"],
        "risk_factors": ["mujer", "diabetes", "sonda vesical"],
        "labs": ["leucocituria", "bacteriuria", "nitritos positivos"],
        "specialty": Specialty.INTERNAL_MEDICINE,
        "base_probability": 0.4,
    },
    # Hematological
    "iron_deficiency_anemia": {
        "name": "Anemia Ferropénica",
        "cie10": CIE10Code(
            "D50.9", "Anemia por deficiencia de hierro, no especificada"
        ),
        "symptoms": ["fatiga", "palidez", "disnea de esfuerzo", "palpitaciones"],
        "risk_factors": ["menstruación abundante", "sangrado gi", "malabsorción"],
        "labs": ["hemoglobina baja", "vcm bajo", "ferritina baja", "hierro bajo"],
        "specialty": Specialty.HEMATOLOGY,
        "base_probability": 0.35,
    },
}


# =============================================================================
# Common Lab Reference Ranges
# =============================================================================

LAB_REFERENCE_RANGES: dict[str, dict[str, Any]] = {
    "hemoglobina": {
        "unit": "g/dL",
        "male": {"min": 13.5, "max": 17.5},
        "female": {"min": 12.0, "max": 16.0},
        "critical_low": 7.0,
        "critical_high": 20.0,
    },
    "vcm": {
        "unit": "fL",
        "min": 80,
        "max": 100,
    },
    "leucocitos": {
        "unit": "/μL",
        "min": 4500,
        "max": 11000,
        "critical_low": 2000,
        "critical_high": 30000,
    },
    "plaquetas": {
        "unit": "/μL",
        "min": 150000,
        "max": 400000,
        "critical_low": 50000,
        "critical_high": 1000000,
    },
    "glucosa": {
        "unit": "mg/dL",
        "min": 70,
        "max": 100,
        "critical_low": 40,
        "critical_high": 500,
    },
    "creatinina": {
        "unit": "mg/dL",
        "male": {"min": 0.7, "max": 1.3},
        "female": {"min": 0.6, "max": 1.1},
        "critical_high": 10.0,
    },
    "potasio": {
        "unit": "mEq/L",
        "min": 3.5,
        "max": 5.0,
        "critical_low": 2.5,
        "critical_high": 6.5,
    },
    "sodio": {
        "unit": "mEq/L",
        "min": 136,
        "max": 145,
        "critical_low": 120,
        "critical_high": 160,
    },
    "tsh": {
        "unit": "mUI/L",
        "min": 0.4,
        "max": 4.0,
    },
    "troponina": {
        "unit": "ng/mL",
        "max": 0.04,
        "critical_high": 0.1,
    },
    "ck": {
        "unit": "U/L",
        "male": {"max": 170},
        "female": {"max": 145},
    },
    "pcr": {
        "unit": "mg/L",
        "max": 5.0,
    },
    "vsg": {
        "unit": "mm/h",
        "male": {"max": 15},
        "female": {"max": 20},
    },
}


# =============================================================================
# Configuration
# =============================================================================


@dataclass
class DiagnosticReasonerConfig:
    """Configuration for diagnostic reasoner."""

    # Number of diagnoses to return
    max_differential: int = 5

    # Probability thresholds
    high_probability_threshold: float = 0.7
    moderate_probability_threshold: float = 0.3
    low_probability_threshold: float = 0.1

    # Weighting factors
    symptom_weight: float = 0.4
    lab_weight: float = 0.3
    risk_factor_weight: float = 0.2
    history_weight: float = 0.1


# =============================================================================
# Diagnostic Reasoner
# =============================================================================


class DiagnosticReasoner:
    """Clinical diagnostic reasoning engine."""

    def __init__(self, config: DiagnosticReasonerConfig | None = None) -> None:
        """Initialize diagnostic reasoner."""
        self.config = config or DiagnosticReasonerConfig()

    def analyze(self, case: ClinicalCase) -> list[DiagnosticHypothesis]:
        """
        Generate differential diagnosis for a clinical case.

        Args:
            case: ClinicalCase with symptoms, labs, history

        Returns:
            List of DiagnosticHypothesis ranked by probability
        """
        logger.info(f"Analyzing case: {case.chief_complaint[:50]}...")

        # Extract features from case
        symptoms_text = self._extract_symptom_text(case)
        lab_findings = self._extract_lab_findings(case)
        risk_factors = self._extract_risk_factors(case)

        # Score each diagnosis
        scored_diagnoses: list[tuple[str, float, dict]] = []

        for dx_id, dx_pattern in DIAGNOSIS_PATTERNS.items():
            score = self._calculate_diagnosis_score(
                dx_pattern,
                symptoms_text,
                lab_findings,
                risk_factors,
                case,
            )

            if score > 0.05:  # Minimum threshold
                scored_diagnoses.append((dx_id, score, dx_pattern))

        # Sort by score
        scored_diagnoses.sort(key=lambda x: x[1], reverse=True)

        # Build hypotheses
        hypotheses = []
        for _dx_id, score, dx_pattern in scored_diagnoses[
            : self.config.max_differential
        ]:
            hypothesis = self._build_hypothesis(
                dx_pattern, score, symptoms_text, lab_findings, case
            )
            hypotheses.append(hypothesis)

        return hypotheses

    def _extract_symptom_text(self, case: ClinicalCase) -> str:
        """Extract all symptom-related text."""
        parts = [case.query.lower(), case.chief_complaint.lower()]

        for symptom in case.symptoms:
            parts.append(symptom.name.lower())
            if symptom.associated:
                parts.extend(s.lower() for s in symptom.associated)

        return " ".join(parts)

    def _extract_lab_findings(self, case: ClinicalCase) -> list[str]:
        """Extract significant lab findings."""
        findings = []

        for lab in case.lab_values:
            if lab.is_abnormal:
                if lab.value < (lab.reference_min or 0):
                    findings.append(f"{lab.name.lower()} baja")
                    findings.append(f"{lab.name.lower()} bajo")
                else:
                    findings.append(f"{lab.name.lower()} alta")
                    findings.append(f"{lab.name.lower()} elevada")
                    findings.append(f"{lab.name.lower()} elevado")

        return findings

    def _extract_risk_factors(self, case: ClinicalCase) -> list[str]:
        """Extract risk factors from patient profile."""
        factors = []

        if case.patient:
            factors.extend(h.lower() for h in case.patient.medical_history)
            factors.extend(m.lower() for m in case.patient.medications)

            # Age-based risks
            if case.patient.age:
                if case.patient.age > 65:
                    factors.append("edad avanzada")
                if case.patient.age < 2:
                    factors.append("lactante")

            # Sex-based risks
            if case.patient.sex:
                factors.append(case.patient.sex.lower())
                if case.patient.sex.lower() in ["f", "female", "femenino"]:
                    factors.append("mujer")
                else:
                    factors.append("hombre")

        return factors

    def _calculate_diagnosis_score(
        self,
        dx_pattern: dict,
        symptoms_text: str,
        lab_findings: list[str],
        risk_factors: list[str],
        case: ClinicalCase,
    ) -> float:
        """Calculate probability score for a diagnosis."""
        base = dx_pattern.get("base_probability", 0.2)

        # Symptom matching
        symptom_score = 0.0
        pattern_symptoms = dx_pattern.get("symptoms", [])
        if pattern_symptoms:
            matches = sum(1 for s in pattern_symptoms if s in symptoms_text)
            symptom_score = matches / len(pattern_symptoms)

        # Lab matching
        lab_score = 0.0
        pattern_labs = dx_pattern.get("labs", [])
        if pattern_labs:
            lab_text = " ".join(lab_findings)
            matches = sum(1 for lab in pattern_labs if lab in lab_text)
            lab_score = matches / len(pattern_labs)
        elif lab_findings:
            lab_score = 0.1  # Some credit for having labs

        # Risk factor matching
        risk_score = 0.0
        pattern_risks = dx_pattern.get("risk_factors", [])
        if pattern_risks:
            risk_text = " ".join(risk_factors)
            matches = sum(1 for r in pattern_risks if r in risk_text)
            risk_score = matches / len(pattern_risks)

        # Weighted combination
        final_score = base * (
            1
            + symptom_score * self.config.symptom_weight
            + lab_score * self.config.lab_weight
            + risk_score * self.config.risk_factor_weight
        )

        return min(final_score, 0.95)  # Cap at 95%

    def _build_hypothesis(
        self,
        dx_pattern: dict,
        score: float,
        symptoms_text: str,
        lab_findings: list[str],
        case: ClinicalCase,
    ) -> DiagnosticHypothesis:
        """Build diagnostic hypothesis from pattern and score."""
        # Find supporting evidence
        supporting = []
        pattern_symptoms = dx_pattern.get("symptoms", [])
        for s in pattern_symptoms:
            if s in symptoms_text:
                supporting.append(f"Presenta: {s}")

        for lab in dx_pattern.get("labs", []):
            if any(lab in lf for lf in lab_findings):
                supporting.append(f"Laboratorio: {lab}")

        # Determine next steps
        next_steps = self._get_diagnostic_steps(dx_pattern, case)

        return DiagnosticHypothesis(
            diagnosis=dx_pattern["name"],
            cie10=dx_pattern.get("cie10"),
            probability=score,
            supporting_findings=supporting[:5],
            against_findings=[],  # Could be enhanced
            next_steps=next_steps,
            specialty=dx_pattern.get("specialty"),
        )

    def _get_diagnostic_steps(
        self,
        dx_pattern: dict,
        case: ClinicalCase,
    ) -> list[str]:
        """Get recommended diagnostic steps."""
        steps = []

        specialty = dx_pattern.get("specialty")

        # Specialty-specific recommendations
        if specialty == Specialty.CARDIOLOGY:
            steps.extend(
                [
                    "ECG de 12 derivaciones",
                    "Troponinas seriadas",
                    "Radiografía de tórax",
                ]
            )
        elif specialty == Specialty.NEUROLOGY:
            steps.extend(
                [
                    "TAC de cráneo",
                    "Evaluación neurológica completa",
                ]
            )
        elif specialty == Specialty.GASTROENTEROLOGY:
            steps.extend(
                [
                    "Serología celíaca (IgA anti-TG)",
                    "Endoscopia digestiva alta con biopsia",
                ]
            )
        elif specialty == Specialty.RHEUMATOLOGY:
            steps.extend(
                [
                    "Panel de autoanticuerpos (ANA, anti-Jo1, anti-Mi2)",
                    "CK, LDH, aldolasa",
                    "EMG y RM muscular",
                ]
            )
        elif specialty == Specialty.ENDOCRINOLOGY:
            steps.extend(
                [
                    "Perfil tiroideo completo (TSH, T4L, T3)",
                    "HbA1c, glucosa en ayunas",
                ]
            )
        elif specialty == Specialty.PULMONOLOGY:
            steps.extend(
                [
                    "Radiografía de tórax",
                    "Espirometría",
                    "Gasometría arterial si disnea severa",
                ]
            )

        # Always add basic labs if not already ordered
        existing_labs = {lv.name.lower() for lv in case.lab_values}
        if "hemograma" not in existing_labs and "hemoglobina" not in existing_labs:
            steps.append("Hemograma completo")
        if "bioquímica" not in existing_labs:
            steps.append("Panel metabólico básico")

        return steps[:5]

    def generate_diagnostic_plan(
        self,
        hypotheses: list[DiagnosticHypothesis],
    ) -> list[DiagnosticPlan]:
        """Generate prioritized diagnostic plan."""
        plan = []
        seen_studies = set()

        for hypothesis in hypotheses:
            for step in hypothesis.next_steps:
                if step not in seen_studies:
                    seen_studies.add(step)

                    priority = "routine"
                    if hypothesis.probability >= 0.7:
                        priority = "urgent"
                    elif hypothesis.probability >= 0.5:
                        priority = "stat"

                    plan.append(
                        DiagnosticPlan(
                            study=step,
                            justification=f"Para evaluar {hypothesis.diagnosis}",
                            priority=priority,
                        )
                    )

        return plan

    def interpret_lab(
        self,
        name: str,
        value: float,
        sex: str | None = None,
    ) -> LabValue:
        """Interpret a lab value against reference ranges."""
        name_lower = name.lower()

        # Find reference range
        ref = LAB_REFERENCE_RANGES.get(name_lower, {})

        unit = ref.get("unit", "")

        # Handle sex-specific ranges
        if sex and sex.lower() in ["m", "male", "masculino"]:
            sex_ref = ref.get("male", ref)
        elif sex and sex.lower() in ["f", "female", "femenino"]:
            sex_ref = ref.get("female", ref)
        else:
            sex_ref = ref

        ref_min = sex_ref.get("min", ref.get("min"))
        ref_max = sex_ref.get("max", ref.get("max"))
        critical_low = ref.get("critical_low")
        critical_high = ref.get("critical_high")

        return LabValue(
            name=name,
            value=value,
            unit=unit,
            reference_min=ref_min,
            reference_max=ref_max,
            critical_min=critical_low,
            critical_max=critical_high,
        )


# =============================================================================
# Factory Functions
# =============================================================================


def create_diagnostic_reasoner(
    config: DiagnosticReasonerConfig | None = None,
) -> DiagnosticReasoner:
    """Create diagnostic reasoner."""
    return DiagnosticReasoner(config)
