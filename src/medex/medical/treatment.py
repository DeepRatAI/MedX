# =============================================================================
# MedeX - Treatment Planner
# =============================================================================
"""
Clinical treatment planning engine.

Features:
- Evidence-based treatment recommendations
- Drug dosage calculations
- Contraindication checking
- Monitoring protocols
- Patient education generation
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from medex.medical.models import (
    ClinicalCase,
    DiagnosticHypothesis,
    EvidenceLevel,
    Medication,
    RecommendationGrade,
    Specialty,
    TreatmentPlan,
    UrgencyLevel,
)


logger = logging.getLogger(__name__)


# =============================================================================
# Treatment Database
# =============================================================================

# Treatment protocols by diagnosis
TREATMENT_PROTOCOLS: dict[str, dict[str, Any]] = {
    # Cardiovascular
    "acute_coronary_syndrome": {
        "medications": [
            {
                "name": "Ácido acetilsalicílico",
                "dose": "300 mg",
                "route": "VO",
                "frequency": "Dosis única de carga, luego 100 mg/día",
                "duration": "Indefinido",
                "indication": "Antiagregación plaquetaria",
                "evidence": EvidenceLevel.LEVEL_1A,
            },
            {
                "name": "Clopidogrel",
                "dose": "300-600 mg",
                "route": "VO",
                "frequency": "Dosis única de carga, luego 75 mg/día",
                "duration": "12 meses",
                "indication": "Antiagregación dual",
                "evidence": EvidenceLevel.LEVEL_1A,
            },
            {
                "name": "Enoxaparina",
                "dose": "1 mg/kg",
                "route": "SC",
                "frequency": "Cada 12 horas",
                "duration": "Durante hospitalización",
                "indication": "Anticoagulación",
                "evidence": EvidenceLevel.LEVEL_1A,
            },
        ],
        "interventions": [
            "Monitorización ECG continua",
            "Reposo absoluto inicial",
            "Oxigenoterapia si SpO2 < 94%",
        ],
        "monitoring": [
            "Troponinas seriadas cada 6 horas",
            "ECG seriados",
            "Función renal diaria",
        ],
        "referrals": ["Cardiología intervencionista URGENTE"],
    },
    "heart_failure": {
        "medications": [
            {
                "name": "Furosemida",
                "dose": "40-80 mg",
                "route": "IV/VO",
                "frequency": "Cada 12-24 horas",
                "duration": "Según respuesta clínica",
                "indication": "Diurético de asa",
                "evidence": EvidenceLevel.LEVEL_1A,
            },
            {
                "name": "Enalapril",
                "dose": "2.5-10 mg",
                "route": "VO",
                "frequency": "Cada 12 horas",
                "duration": "Crónico",
                "indication": "IECA - Remodelado cardíaco",
                "evidence": EvidenceLevel.LEVEL_1A,
            },
            {
                "name": "Carvedilol",
                "dose": "3.125-25 mg",
                "route": "VO",
                "frequency": "Cada 12 horas",
                "duration": "Crónico",
                "indication": "Beta-bloqueante",
                "evidence": EvidenceLevel.LEVEL_1A,
            },
        ],
        "lifestyle": [
            "Restricción de sodio < 2g/día",
            "Restricción hídrica 1.5-2 L/día",
            "Control de peso diario",
            "Ejercicio aeróbico moderado según tolerancia",
        ],
        "monitoring": [
            "Balance hídrico estricto",
            "Peso diario",
            "Función renal y electrolitos semanal",
            "BNP mensual",
        ],
    },
    # Gastrointestinal
    "celiac_disease": {
        "medications": [
            {
                "name": "Sulfato ferroso",
                "dose": "325 mg (65 mg Fe elemental)",
                "route": "VO",
                "frequency": "Cada 8 horas",
                "duration": "3-6 meses hasta normalizar ferritina",
                "indication": "Reposición de hierro",
                "evidence": EvidenceLevel.LEVEL_1B,
            },
            {
                "name": "Ácido fólico",
                "dose": "5 mg",
                "route": "VO",
                "frequency": "Diario",
                "duration": "8 semanas",
                "indication": "Suplementación vitamínica",
                "evidence": EvidenceLevel.LEVEL_2B,
            },
            {
                "name": "Vitamina D3",
                "dose": "1000-2000 UI",
                "route": "VO",
                "frequency": "Diario",
                "duration": "Según niveles 25-OH-D",
                "indication": "Suplementación vitamínica",
                "evidence": EvidenceLevel.LEVEL_2B,
            },
        ],
        "lifestyle": [
            "Dieta libre de gluten ESTRICTA",
            "Evitar contaminación cruzada",
            "Lectura cuidadosa de etiquetas",
            "Contacto con asociación de celíacos",
        ],
        "monitoring": [
            "Anticuerpos anti-TG cada 6 meses",
            "Hemograma y ferritina cada 3 meses",
            "Densitometría ósea anual",
        ],
        "referrals": ["Nutrición especializada en EC"],
        "patient_education": [
            "Alimentos permitidos y prohibidos",
            "Identificación de gluten oculto",
            "Manejo en restaurantes",
            "Signos de alarma para consultar",
        ],
    },
    # Rheumatological
    "dermatomyositis": {
        "medications": [
            {
                "name": "Prednisona",
                "dose": "1 mg/kg/día",
                "route": "VO",
                "frequency": "Diario (mañana)",
                "duration": "4-6 semanas, luego descenso gradual",
                "indication": "Inmunosupresión",
                "evidence": EvidenceLevel.LEVEL_1B,
            },
            {
                "name": "Metotrexato",
                "dose": "15-25 mg/semana",
                "route": "VO/SC",
                "frequency": "Semanal",
                "duration": "Largo plazo como ahorrador de corticoides",
                "indication": "DMARD ahorrador de corticoides",
                "evidence": EvidenceLevel.LEVEL_2A,
            },
            {
                "name": "Ácido fólico",
                "dose": "5 mg",
                "route": "VO",
                "frequency": "Semanal (día siguiente a MTX)",
                "duration": "Mientras use metotrexato",
                "indication": "Reducir toxicidad MTX",
                "evidence": EvidenceLevel.LEVEL_1B,
            },
        ],
        "interventions": [
            "Fotoprotección estricta",
            "Fisioterapia para mantener fuerza muscular",
        ],
        "monitoring": [
            "CK cada 2 semanas inicialmente",
            "Hemograma y función hepática mensual",
            "Screening de malignidad (>40 años)",
        ],
        "referrals": [
            "Reumatología",
            "Dermatología",
            "Fisioterapia",
            "Oncología para screening",
        ],
    },
    # Endocrine
    "diabetes_mellitus_2": {
        "medications": [
            {
                "name": "Metformina",
                "dose": "500-850 mg",
                "route": "VO",
                "frequency": "Con las comidas, titular cada 1-2 semanas",
                "duration": "Crónico",
                "indication": "Primera línea DM2",
                "evidence": EvidenceLevel.LEVEL_1A,
            },
        ],
        "lifestyle": [
            "Dieta mediterránea/baja en carbohidratos",
            "Ejercicio aeróbico 150 min/semana",
            "Reducción de peso 5-10%",
            "Cese tabáquico",
        ],
        "monitoring": [
            "HbA1c cada 3 meses inicialmente",
            "Glucometría domiciliaria",
            "Función renal y perfil lipídico semestral",
            "Fondo de ojo anual",
        ],
        "patient_education": [
            "Signos de hipoglucemia e hiperglucemia",
            "Cuidado de los pies",
            "Monitoreo glucométrico",
            "Manejo de días de enfermedad",
        ],
    },
    # Respiratory
    "pneumonia": {
        "medications": [
            {
                "name": "Amoxicilina-Clavulánico",
                "dose": "875/125 mg",
                "route": "VO",
                "frequency": "Cada 8 horas",
                "duration": "7 días",
                "indication": "Antibiótico para NAC",
                "evidence": EvidenceLevel.LEVEL_1A,
            },
            {
                "name": "Azitromicina",
                "dose": "500 mg",
                "route": "VO",
                "frequency": "Día 1, luego 250 mg días 2-5",
                "duration": "5 días",
                "indication": "Cobertura atípicos",
                "evidence": EvidenceLevel.LEVEL_1A,
            },
        ],
        "interventions": [
            "Hidratación adecuada",
            "Oxigenoterapia si SpO2 < 92%",
            "Nebulizaciones PRN",
        ],
        "monitoring": [
            "Temperatura cada 6 horas",
            "SpO2 continua",
            "Radiografía de control a las 48-72h si no mejora",
        ],
    },
    # Infectious
    "urinary_tract_infection": {
        "medications": [
            {
                "name": "Nitrofurantoína",
                "dose": "100 mg",
                "route": "VO",
                "frequency": "Cada 12 horas",
                "duration": "5 días",
                "indication": "ITU no complicada",
                "evidence": EvidenceLevel.LEVEL_1A,
            },
        ],
        "lifestyle": [
            "Hidratación abundante (>2L/día)",
            "Micción frecuente",
            "Higiene adecuada",
        ],
        "monitoring": [
            "Síntomas a las 48-72 horas",
            "Urocultivo si no mejora",
        ],
    },
    # Hematological
    "iron_deficiency_anemia": {
        "medications": [
            {
                "name": "Sulfato ferroso",
                "dose": "325 mg (65 mg Fe elemental)",
                "route": "VO",
                "frequency": "Cada 8 horas en ayunas",
                "duration": "3-6 meses post-normalización Hb",
                "indication": "Reposición de hierro",
                "evidence": EvidenceLevel.LEVEL_1A,
            },
            {
                "name": "Vitamina C",
                "dose": "500 mg",
                "route": "VO",
                "frequency": "Con cada dosis de hierro",
                "duration": "Mientras use hierro",
                "indication": "Mejora absorción de hierro",
                "evidence": EvidenceLevel.LEVEL_2B,
            },
        ],
        "lifestyle": [
            "Dieta rica en hierro (carnes rojas, legumbres)",
            "Evitar té/café con comidas (inhiben absorción)",
            "Combinar con vitamina C",
        ],
        "monitoring": [
            "Hemograma cada 4 semanas",
            "Ferritina a los 3 meses",
            "Reticulocitos a la semana (respuesta)",
        ],
    },
}


# =============================================================================
# Contraindications Database
# =============================================================================

CONTRAINDICATIONS: dict[str, list[str]] = {
    "aines": [
        "úlcera gástrica",
        "insuficiencia renal",
        "sangrado digestivo",
        "embarazo tercer trimestre",
        "asma sensible a aines",
    ],
    "metformina": [
        "insuficiencia renal severa",
        "insuficiencia hepática",
        "acidosis láctica",
        "uso de contraste yodado",
    ],
    "ieca": [
        "angioedema previo",
        "embarazo",
        "hiperpotasemia",
        "estenosis arteria renal bilateral",
    ],
    "beta_bloqueante": [
        "asma severa",
        "bloqueo av alto grado",
        "bradicardia severa",
        "hipotensión severa",
    ],
    "corticoides": [
        "infección activa no tratada",
        "herpes zóster",
        "tuberculosis activa",
    ],
}


# =============================================================================
# Configuration
# =============================================================================


@dataclass
class TreatmentPlannerConfig:
    """Configuration for treatment planner."""

    # Include evidence level in recommendations
    include_evidence: bool = True

    # Maximum medications to recommend
    max_medications: int = 5

    # Include patient education
    include_education: bool = True

    # Language
    language: str = "es"


# =============================================================================
# Treatment Planner
# =============================================================================


class TreatmentPlanner:
    """Clinical treatment planning engine."""

    def __init__(self, config: TreatmentPlannerConfig | None = None) -> None:
        """Initialize treatment planner."""
        self.config = config or TreatmentPlannerConfig()

    def create_plan(
        self,
        case: ClinicalCase,
        primary_diagnosis: DiagnosticHypothesis | None = None,
    ) -> TreatmentPlan:
        """
        Create treatment plan for a clinical case.

        Args:
            case: ClinicalCase with patient info and diagnosis
            primary_diagnosis: Primary working diagnosis

        Returns:
            TreatmentPlan with medications, interventions, monitoring
        """
        logger.info("Creating treatment plan...")

        if not primary_diagnosis:
            return self._create_symptomatic_plan(case)

        # Find matching protocol
        diagnosis_key = self._match_diagnosis_to_protocol(primary_diagnosis)

        if diagnosis_key and diagnosis_key in TREATMENT_PROTOCOLS:
            return self._create_protocol_plan(
                case, primary_diagnosis, TREATMENT_PROTOCOLS[diagnosis_key]
            )

        return self._create_symptomatic_plan(case)

    def _match_diagnosis_to_protocol(
        self,
        hypothesis: DiagnosticHypothesis,
    ) -> str | None:
        """Match diagnosis to treatment protocol key."""
        diagnosis_lower = hypothesis.diagnosis.lower()

        # Direct mapping
        mappings = {
            "síndrome coronario agudo": "acute_coronary_syndrome",
            "insuficiencia cardíaca": "heart_failure",
            "enfermedad celíaca": "celiac_disease",
            "dermatomiositis": "dermatomyositis",
            "diabetes mellitus tipo 2": "diabetes_mellitus_2",
            "neumonía": "pneumonia",
            "infección del tracto urinario": "urinary_tract_infection",
            "anemia ferropénica": "iron_deficiency_anemia",
        }

        for name, key in mappings.items():
            if name in diagnosis_lower:
                return key

        # CIE-10 based matching
        if hypothesis.cie10:
            code = hypothesis.cie10.code[:3]
            code_mappings = {
                "I21": "acute_coronary_syndrome",
                "I50": "heart_failure",
                "K90": "celiac_disease",
                "M33": "dermatomyositis",
                "E11": "diabetes_mellitus_2",
                "J18": "pneumonia",
                "N39": "urinary_tract_infection",
                "D50": "iron_deficiency_anemia",
            }
            if code in code_mappings:
                return code_mappings[code]

        return None

    def _create_protocol_plan(
        self,
        case: ClinicalCase,
        hypothesis: DiagnosticHypothesis,
        protocol: dict[str, Any],
    ) -> TreatmentPlan:
        """Create plan from treatment protocol."""
        # Build medications
        medications = []
        for med_data in protocol.get("medications", [])[: self.config.max_medications]:
            # Check contraindications
            if not self._check_contraindications(med_data["name"], case):
                medications.append(
                    Medication(
                        name=med_data["name"],
                        dose=med_data.get("dose"),
                        route=med_data.get("route"),
                        frequency=med_data.get("frequency"),
                        duration=med_data.get("duration"),
                        indication=med_data.get("indication"),
                        evidence_level=med_data.get("evidence"),
                    )
                )

        return TreatmentPlan(
            medications=medications,
            interventions=protocol.get("interventions", []),
            lifestyle_modifications=protocol.get("lifestyle", []),
            monitoring=protocol.get("monitoring", []),
            follow_up=self._determine_follow_up(hypothesis),
            referrals=protocol.get("referrals", []),
            patient_education=protocol.get("patient_education", [])
            if self.config.include_education
            else [],
        )

    def _create_symptomatic_plan(self, case: ClinicalCase) -> TreatmentPlan:
        """Create symptomatic treatment plan."""
        medications = []
        interventions = []
        monitoring = []

        # Symptomatic treatment based on findings
        symptoms_text = " ".join(s.name.lower() for s in case.symptoms)

        if "dolor" in symptoms_text or "pain" in symptoms_text:
            medications.append(
                Medication(
                    name="Paracetamol",
                    dose="500-1000 mg",
                    route="VO",
                    frequency="Cada 6-8 horas PRN",
                    indication="Analgesia",
                )
            )

        if "fiebre" in symptoms_text or "fever" in symptoms_text:
            medications.append(
                Medication(
                    name="Paracetamol",
                    dose="500-1000 mg",
                    route="VO",
                    frequency="Cada 6 horas",
                    indication="Antipirético",
                )
            )
            interventions.append("Hidratación abundante")
            monitoring.append("Control de temperatura cada 6 horas")

        if "náusea" in symptoms_text or "vómito" in symptoms_text:
            medications.append(
                Medication(
                    name="Ondansetrón",
                    dose="4-8 mg",
                    route="VO/IV",
                    frequency="Cada 8 horas PRN",
                    indication="Antiemético",
                )
            )

        return TreatmentPlan(
            medications=medications,
            interventions=interventions,
            monitoring=monitoring,
            follow_up="Reevaluar en 48-72 horas si no mejora",
        )

    def _check_contraindications(
        self,
        medication: str,
        case: ClinicalCase,
    ) -> bool:
        """Check if medication is contraindicated."""
        if not case.patient:
            return False

        med_lower = medication.lower()
        history_text = " ".join(case.patient.medical_history).lower()

        # Check each contraindication category
        for med_type, contraindications in CONTRAINDICATIONS.items():
            if med_type in med_lower:
                for contra in contraindications:
                    if contra in history_text:
                        logger.warning(
                            f"Contraindication found: {medication} - {contra}"
                        )
                        return True

        return False

    def _determine_follow_up(
        self,
        hypothesis: DiagnosticHypothesis,
    ) -> str:
        """Determine follow-up timing."""
        if hypothesis.probability >= 0.8:
            if hypothesis.specialty in {Specialty.CARDIOLOGY, Specialty.NEUROLOGY}:
                return "Control en 24-48 horas"
            return "Control en 1 semana"

        if hypothesis.probability >= 0.5:
            return "Control en 2 semanas"

        return "Control según evolución o si empeora"

    def get_admission_criteria(
        self,
        case: ClinicalCase,
        hypothesis: DiagnosticHypothesis | None = None,
    ) -> list[str]:
        """Get criteria for hospital admission."""
        criteria = []

        # Vital sign criteria
        if case.vital_signs:
            vs = case.vital_signs
            if vs.is_hypotensive:
                criteria.append(f"Hipotensión: PAS {vs.blood_pressure_systolic} mmHg")
            if vs.is_hypoxic:
                criteria.append(f"Hipoxemia: SpO2 {vs.oxygen_saturation}%")
            if vs.heart_rate and vs.heart_rate > 120:
                criteria.append(f"Taquicardia: {vs.heart_rate} bpm")
            if vs.glasgow_coma_scale and vs.glasgow_coma_scale < 15:
                criteria.append(f"Alteración conciencia: GCS {vs.glasgow_coma_scale}")

        # Lab criteria
        for lab in case.lab_values:
            if lab.is_critical:
                criteria.append(f"{lab.name} crítico: {lab.value} {lab.unit}")

        # Diagnosis-specific criteria
        if hypothesis:
            if hypothesis.specialty == Specialty.CARDIOLOGY:
                criteria.append("Evaluación cardiológica urgente requerida")
            if hypothesis.specialty == Specialty.NEUROLOGY:
                criteria.append("Descartar evento cerebrovascular agudo")

        return criteria


# =============================================================================
# Factory Functions
# =============================================================================


def create_treatment_planner(
    config: TreatmentPlannerConfig | None = None,
) -> TreatmentPlanner:
    """Create treatment planner."""
    return TreatmentPlanner(config)
