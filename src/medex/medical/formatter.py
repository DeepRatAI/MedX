# =============================================================================
# MedeX - Clinical Response Formatter
# =============================================================================
"""
Clinical response formatting for different consultation types.

Features:
- Educational vs Professional mode formatting
- Markdown generation with proper structure
- Disclaimer and warning generation
- Reference formatting
- Multi-language support (Spanish/English)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from medex.medical.models import (
    ClinicalCase,
    ClinicalResponse,
    ConsultationType,
    DiagnosticHypothesis,
    DiagnosticPlan,
    Medication,
    Specialty,
    TreatmentPlan,
    TriageAssessment,
    TriageLevel,
    UrgencyLevel,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Response Templates
# =============================================================================


class FormatterLanguage(Enum):
    """Supported languages."""

    SPANISH = "es"
    ENGLISH = "en"


# Disclaimer templates
DISCLAIMERS = {
    "es": {
        "general": (
            "⚠️ **Aviso Legal**: Esta información es solo para fines educativos "
            "y no sustituye la consulta con un profesional de la salud. "
            "Ante cualquier síntoma, consulte a su médico."
        ),
        "professional": (
            "📋 **Nota Clínica**: Esta información está destinada a profesionales "
            "de la salud. Los diagnósticos y tratamientos deben individualizarse "
            "según el contexto clínico de cada paciente."
        ),
        "emergency": (
            "🚨 **EMERGENCIA MÉDICA**: Si presenta síntomas de riesgo vital, "
            "LLAME INMEDIATAMENTE al servicio de emergencias de su país. "
            "No demore la atención médica presencial."
        ),
    },
    "en": {
        "general": (
            "⚠️ **Disclaimer**: This information is for educational purposes only "
            "and does not replace consultation with a healthcare professional. "
            "If you have symptoms, consult your doctor."
        ),
        "professional": (
            "📋 **Clinical Note**: This information is intended for healthcare "
            "professionals. Diagnoses and treatments must be individualized "
            "according to each patient's clinical context."
        ),
        "emergency": (
            "🚨 **MEDICAL EMERGENCY**: If you have life-threatening symptoms, "
            "IMMEDIATELY CALL your country's emergency services. "
            "Do not delay in-person medical care."
        ),
    },
}

# Section headers
SECTION_HEADERS = {
    "es": {
        "summary": "## 📋 Resumen Clínico",
        "triage": "## 🏥 Evaluación de Triaje",
        "differential": "## 🔬 Diagnóstico Diferencial",
        "diagnostic_plan": "## 📊 Plan Diagnóstico",
        "treatment": "## 💊 Plan Terapéutico",
        "medications": "### Medicamentos",
        "lifestyle": "### Modificaciones del Estilo de Vida",
        "monitoring": "### Monitorización",
        "referrals": "### Derivaciones",
        "education": "## 📚 Información para el Paciente",
        "red_flags": "## ⚠️ Signos de Alarma",
        "references": "## 📖 Referencias",
        "admission": "## 🏨 Criterios de Internación",
    },
    "en": {
        "summary": "## 📋 Clinical Summary",
        "triage": "## 🏥 Triage Assessment",
        "differential": "## 🔬 Differential Diagnosis",
        "diagnostic_plan": "## 📊 Diagnostic Plan",
        "treatment": "## 💊 Treatment Plan",
        "medications": "### Medications",
        "lifestyle": "### Lifestyle Modifications",
        "monitoring": "### Monitoring",
        "referrals": "### Referrals",
        "education": "## 📚 Patient Education",
        "red_flags": "## ⚠️ Red Flags",
        "references": "## 📖 References",
        "admission": "## 🏨 Admission Criteria",
    },
}


# =============================================================================
# Configuration
# =============================================================================


@dataclass
class FormatterConfig:
    """Configuration for clinical formatter."""

    # Output language
    language: str = "es"

    # Include evidence levels
    include_evidence: bool = True

    # Include CIE-10 codes
    include_cie10: bool = True

    # Include references section
    include_references: bool = True

    # Include patient education
    include_education: bool = True

    # Max diagnoses to show
    max_differential: int = 5

    # Format timestamps
    timestamp_format: str = "%Y-%m-%d %H:%M:%S"


# =============================================================================
# Clinical Formatter
# =============================================================================


class ClinicalFormatter:
    """Clinical response formatter."""

    def __init__(self, config: FormatterConfig | None = None) -> None:
        """Initialize formatter."""
        self.config = config or FormatterConfig()
        self.headers = SECTION_HEADERS.get(self.config.language, SECTION_HEADERS["es"])
        self.disclaimers = DISCLAIMERS.get(self.config.language, DISCLAIMERS["es"])

    def format_response(
        self,
        case: ClinicalCase,
        consultation_type: ConsultationType = ConsultationType.EDUCATIONAL,
    ) -> ClinicalResponse:
        """
        Format clinical case as structured response.

        Args:
            case: ClinicalCase with all analysis
            consultation_type: Type of consultation

        Returns:
            ClinicalResponse with formatted content
        """
        logger.info(f"Formatting response for {consultation_type.value} consultation")

        sections = []

        # Determine urgency and add appropriate disclaimer
        urgency = self._determine_urgency(case)
        if urgency in {UrgencyLevel.CRITICAL, UrgencyLevel.HIGH}:
            sections.append(self.disclaimers["emergency"])

        # Build response based on consultation type
        if consultation_type == ConsultationType.EMERGENCY:
            sections.extend(self._format_emergency(case))
        elif consultation_type == ConsultationType.PROFESSIONAL:
            sections.extend(self._format_professional(case))
        else:
            sections.extend(self._format_educational(case))

        # Add appropriate disclaimer
        if consultation_type == ConsultationType.PROFESSIONAL:
            sections.append(self.disclaimers["professional"])
        else:
            sections.append(self.disclaimers["general"])

        # Build formatted content
        formatted_content = "\n\n".join(sections)

        return ClinicalResponse(
            content=formatted_content,
            urgency=urgency,
            consultation_type=consultation_type,
            differential_diagnoses=case.differential_diagnosis,
            treatment_plan=case.treatment_plan,
            references=self._generate_references(case),
            disclaimer=self._get_disclaimer(consultation_type),
            timestamp=datetime.now(),
        )

    def _determine_urgency(self, case: ClinicalCase) -> UrgencyLevel:
        """Determine response urgency from case data."""
        if case.triage:
            if case.triage.level in {TriageLevel.LEVEL_1, TriageLevel.LEVEL_2}:
                return UrgencyLevel.CRITICAL
            if case.triage.level == TriageLevel.LEVEL_3:
                return UrgencyLevel.HIGH
            if case.triage.level == TriageLevel.LEVEL_4:
                return UrgencyLevel.MEDIUM
            return UrgencyLevel.LOW

        # Infer from diagnoses
        if case.differential_diagnosis:
            top = case.differential_diagnosis[0]
            if top.probability >= 0.8 and top.specialty in {
                "CARDIOLOGY",
                "NEUROLOGY",
                "EMERGENCY",
            }:
                return UrgencyLevel.HIGH

        return UrgencyLevel.INFORMATIONAL

    def _format_emergency(self, case: ClinicalCase) -> list[str]:
        """Format emergency response."""
        sections = []

        # Triage is priority
        if case.triage:
            sections.append(self._format_triage(case.triage))

        # Quick differential
        if case.differential_diagnosis:
            sections.append(
                self._format_differential_brief(case.differential_diagnosis[:3])
            )

        # Critical actions
        sections.append(self._format_emergency_actions(case))

        return sections

    def _format_professional(self, case: ClinicalCase) -> list[str]:
        """Format professional/clinical response."""
        sections = []

        # Clinical summary
        sections.append(self._format_summary(case))

        # Triage if available
        if case.triage:
            sections.append(self._format_triage(case.triage))

        # Full differential diagnosis
        if case.differential_diagnosis:
            sections.append(
                self._format_differential_full(
                    case.differential_diagnosis[: self.config.max_differential]
                )
            )

        # Diagnostic plan
        if case.diagnostic_plan:
            sections.append(self._format_diagnostic_plan(case.diagnostic_plan))

        # Treatment plan
        if case.treatment_plan:
            sections.append(self._format_treatment(case.treatment_plan))

        # Admission criteria if warranted
        admission = self._get_admission_criteria(case)
        if admission:
            sections.append(self._format_admission_criteria(admission))

        # References
        if self.config.include_references:
            refs = self._generate_references(case)
            if refs:
                sections.append(self._format_references(refs))

        return sections

    def _format_educational(self, case: ClinicalCase) -> list[str]:
        """Format educational response for patients."""
        sections = []

        # Simple summary
        sections.append(self._format_summary_simple(case))

        # Main diagnosis explanation
        if case.differential_diagnosis:
            sections.append(
                self._format_diagnosis_explained(case.differential_diagnosis[0])
            )

        # Treatment in simple terms
        if case.treatment_plan:
            sections.append(self._format_treatment_simple(case.treatment_plan))

        # Red flags
        red_flags = self._extract_red_flags(case)
        if red_flags:
            sections.append(self._format_red_flags(red_flags))

        # Patient education
        if self.config.include_education and case.treatment_plan:
            sections.append(self._format_education(case.treatment_plan))

        return sections

    # -------------------------------------------------------------------------
    # Section Formatters
    # -------------------------------------------------------------------------

    def _format_summary(self, case: ClinicalCase) -> str:
        """Format clinical summary."""
        lines = [self.headers["summary"]]

        if case.patient:
            patient = case.patient
            lines.append(f"**Paciente**: {patient.age} años, {patient.sex}")
            if patient.medical_history:
                lines.append(f"**APP**: {', '.join(patient.medical_history)}")

        if case.symptoms:
            symptoms = ", ".join(s.name for s in case.symptoms)
            lines.append(f"**Motivo de consulta**: {symptoms}")

        if case.vital_signs:
            vs = case.vital_signs
            vitals = []
            if vs.heart_rate:
                vitals.append(f"FC: {vs.heart_rate} bpm")
            if vs.blood_pressure_systolic:
                vitals.append(
                    f"PA: {vs.blood_pressure_systolic}/{vs.blood_pressure_diastolic}"
                )
            if vs.oxygen_saturation:
                vitals.append(f"SpO2: {vs.oxygen_saturation}%")
            if vitals:
                lines.append(f"**Signos vitales**: {', '.join(vitals)}")

        return "\n".join(lines)

    def _format_summary_simple(self, case: ClinicalCase) -> str:
        """Format simple summary for patients."""
        lines = [self.headers["summary"]]

        if case.symptoms:
            lines.append(
                "Según los síntomas que describes, he analizado tu caso "
                "para brindarte información útil."
            )

        return "\n".join(lines)

    def _format_triage(self, triage: TriageAssessment) -> str:
        """Format triage assessment."""
        lines = [self.headers["triage"]]

        level = triage.level
        color = level.color.upper()

        lines.append(
            f"**Nivel de triaje**: {level.name} ({color}) - "
            f"Tiempo máximo de espera: {level.max_wait_minutes} minutos"
        )

        lines.append(f"**Urgencia**: {triage.urgency.value}")

        if triage.discriminators:
            lines.append(f"**Discriminadores**: {', '.join(triage.discriminators)}")

        if triage.red_flags:
            flags = ", ".join(triage.red_flags)
            lines.append(f"**🚨 Banderas rojas**: {flags}")

        lines.append(f"**Disposición**: {triage.disposition}")

        return "\n".join(lines)

    def _format_differential_brief(
        self,
        diagnoses: list[DiagnosticHypothesis],
    ) -> str:
        """Format brief differential diagnosis."""
        lines = [self.headers["differential"]]

        for i, dx in enumerate(diagnoses, 1):
            prob = int(dx.probability * 100)
            lines.append(f"{i}. **{dx.diagnosis}** ({prob}%)")

        return "\n".join(lines)

    def _format_differential_full(
        self,
        diagnoses: list[DiagnosticHypothesis],
    ) -> str:
        """Format full differential diagnosis."""
        lines = [self.headers["differential"]]

        for i, dx in enumerate(diagnoses, 1):
            prob = int(dx.probability * 100)

            # Main line with CIE-10
            if self.config.include_cie10 and dx.cie10:
                lines.append(
                    f"### {i}. {dx.diagnosis} ({prob}%) - CIE-10: {dx.cie10.code}"
                )
            else:
                lines.append(f"### {i}. {dx.diagnosis} ({prob}%)")

            # Supporting findings
            if dx.supporting_findings:
                lines.append(f"**A favor**: {', '.join(dx.supporting_findings)}")

            # Against findings
            if dx.against_findings:
                lines.append(f"**En contra**: {', '.join(dx.against_findings)}")

            # Specialty
            if dx.specialty:
                lines.append(f"**Especialidad**: {dx.specialty.value}")

            lines.append("")  # Blank line between diagnoses

        return "\n".join(lines)

    def _format_diagnostic_plan(self, plan: list[DiagnosticPlan]) -> str:
        """Format diagnostic plan."""
        lines = [self.headers["diagnostic_plan"]]

        for study in plan:
            priority = study.priority.upper() if study.priority else "Rutina"
            lines.append(f"- **{study.study}** ({priority})")
            if study.justification:
                lines.append(f"  - *Justificación*: {study.justification}")

        return "\n".join(lines)

    def _format_treatment(self, treatment: TreatmentPlan) -> str:
        """Format treatment plan."""
        sections = [self.headers["treatment"]]

        # Medications
        if treatment.medications:
            sections.append(self.headers["medications"])
            for med in treatment.medications:
                sections.append(self._format_medication(med))

        # Interventions
        if treatment.interventions:
            sections.append("### Intervenciones")
            for intervention in treatment.interventions:
                sections.append(f"- {intervention}")

        # Lifestyle
        if treatment.lifestyle_modifications:
            sections.append(self.headers["lifestyle"])
            for mod in treatment.lifestyle_modifications:
                sections.append(f"- {mod}")

        # Monitoring
        if treatment.monitoring:
            sections.append(self.headers["monitoring"])
            for item in treatment.monitoring:
                sections.append(f"- {item}")

        # Referrals
        if treatment.referrals:
            sections.append(self.headers["referrals"])
            for ref in treatment.referrals:
                sections.append(f"- {ref}")

        # Follow-up
        if treatment.follow_up:
            sections.append(f"\n**Seguimiento**: {treatment.follow_up}")

        return "\n".join(sections)

    def _format_medication(self, med: Medication) -> str:
        """Format single medication."""
        parts = [f"- **{med.name}**"]

        details = []
        if med.dose:
            details.append(med.dose)
        if med.route:
            details.append(med.route)
        if med.frequency:
            details.append(med.frequency)

        if details:
            parts.append(f" {' - '.join(details)}")

        if med.duration:
            parts.append(f" (Duración: {med.duration})")

        result = "".join(parts)

        if self.config.include_evidence and med.evidence_level:
            result += f" [Evidencia: {med.evidence_level.value}]"

        if med.indication:
            result += f"\n  - *Indicación*: {med.indication}"

        return result

    def _format_treatment_simple(self, treatment: TreatmentPlan) -> str:
        """Format treatment in simple terms for patients."""
        lines = [self.headers["treatment"]]

        if treatment.medications:
            lines.append("**Medicamentos sugeridos** (consultar con médico):")
            for med in treatment.medications:
                if med.indication:
                    lines.append(f"- {med.name}: {med.indication}")
                else:
                    lines.append(f"- {med.name}")

        if treatment.lifestyle_modifications:
            lines.append("\n**Cambios en el estilo de vida**:")
            for mod in treatment.lifestyle_modifications:
                lines.append(f"- {mod}")

        return "\n".join(lines)

    def _format_diagnosis_explained(self, dx: DiagnosticHypothesis) -> str:
        """Format diagnosis explanation for patients."""
        lines = [f"## 🩺 Sobre {dx.diagnosis}"]

        # Simple probability interpretation
        if dx.probability >= 0.7:
            lines.append(
                "Según tus síntomas, este diagnóstico parece **muy probable**."
            )
        elif dx.probability >= 0.4:
            lines.append("Este es un diagnóstico **posible** que debe evaluarse.")
        else:
            lines.append(
                "Este diagnóstico debe **descartarse** con estudios apropiados."
            )

        if dx.supporting_findings:
            lines.append(
                f"\n*Síntomas que apoyan esto*: {', '.join(dx.supporting_findings)}"
            )

        return "\n".join(lines)

    def _format_red_flags(self, red_flags: list[str]) -> str:
        """Format red flags section."""
        lines = [self.headers["red_flags"]]
        lines.append("Consulte **inmediatamente** si presenta:")

        for flag in red_flags:
            lines.append(f"- 🚨 {flag}")

        return "\n".join(lines)

    def _format_education(self, treatment: TreatmentPlan) -> str:
        """Format patient education section."""
        lines = [self.headers["education"]]

        if treatment.patient_education:
            for item in treatment.patient_education:
                lines.append(f"- {item}")
        else:
            lines.append("- Siga las indicaciones de su médico tratante")
            lines.append("- No suspenda medicación sin consultar")
            lines.append("- Acuda a controles programados")

        return "\n".join(lines)

    def _format_emergency_actions(self, case: ClinicalCase) -> str:
        """Format emergency actions."""
        lines = ["## 🚑 Acciones Inmediatas"]

        if case.triage and case.triage.level == TriageLevel.LEVEL_1:
            lines.extend(
                [
                    "1. Activar código de emergencia",
                    "2. Asegurar vía aérea",
                    "3. Acceso venoso periférico",
                    "4. Monitorización continua",
                    "5. Preparar para reanimación",
                ]
            )
        elif case.triage and case.triage.level == TriageLevel.LEVEL_2:
            lines.extend(
                [
                    "1. Evaluación médica inmediata",
                    "2. Monitorización continua",
                    "3. Acceso venoso",
                    "4. Laboratorios urgentes",
                ]
            )
        else:
            lines.extend(
                [
                    "1. Evaluación médica prioritaria",
                    "2. Monitorización de signos vitales",
                    "3. Estudios complementarios según necesidad",
                ]
            )

        return "\n".join(lines)

    def _format_admission_criteria(self, criteria: list[str]) -> str:
        """Format admission criteria."""
        lines = [self.headers["admission"]]

        for criterion in criteria:
            lines.append(f"- {criterion}")

        return "\n".join(lines)

    def _format_references(self, references: list[str]) -> str:
        """Format references section."""
        lines = [self.headers["references"]]

        for i, ref in enumerate(references, 1):
            lines.append(f"{i}. {ref}")

        return "\n".join(lines)

    # -------------------------------------------------------------------------
    # Helper Methods
    # -------------------------------------------------------------------------

    def _extract_red_flags(self, case: ClinicalCase) -> list[str]:
        """Extract red flags from case."""
        flags = []

        if case.triage and case.triage.red_flags:
            flags.extend(case.triage.red_flags)

        # Generic red flags based on diagnosis
        if case.differential_diagnosis:
            top = case.differential_diagnosis[0]
            if top.specialty == Specialty.CARDIOLOGY:
                flags.extend(
                    [
                        "Dolor torácico que irradia a brazo o mandíbula",
                        "Dificultad para respirar severa",
                        "Pérdida de conciencia",
                    ]
                )
            elif top.specialty == Specialty.NEUROLOGY:
                flags.extend(
                    [
                        "Debilidad súbita en un lado del cuerpo",
                        "Dificultad para hablar",
                        "Pérdida de visión",
                        "Dolor de cabeza severo y súbito",
                    ]
                )

        return list(set(flags))  # Remove duplicates

    def _get_admission_criteria(self, case: ClinicalCase) -> list[str]:
        """Get admission criteria from case."""
        criteria = []

        if case.vital_signs:
            vs = case.vital_signs
            if vs.is_hypotensive:
                criteria.append("Hipotensión que requiere monitoreo")
            if vs.is_hypoxic:
                criteria.append("Hipoxemia que requiere oxigenoterapia")
            if vs.glasgow_coma_scale and vs.glasgow_coma_scale < 15:
                criteria.append("Alteración del nivel de conciencia")

        if case.triage and case.triage.level in {
            TriageLevel.LEVEL_1,
            TriageLevel.LEVEL_2,
        }:
            criteria.append("Triaje de alta prioridad")

        return criteria

    def _generate_references(self, case: ClinicalCase) -> list[str]:
        """Generate references based on case."""
        references = []

        if case.differential_diagnosis:
            top = case.differential_diagnosis[0]

            # Generic references by specialty
            specialty_refs = {
                Specialty.CARDIOLOGY: [
                    "ESC Guidelines 2023 - Acute Coronary Syndromes",
                    "AHA/ACC Guidelines 2022 - Heart Failure",
                ],
                Specialty.GASTROENTEROLOGY: [
                    "ACG Clinical Guidelines 2023",
                    "ESPGHAN Guidelines - Celiac Disease",
                ],
                Specialty.RHEUMATOLOGY: [
                    "ACR/EULAR Classification Criteria",
                    "UpToDate - Inflammatory Myopathies",
                ],
                Specialty.NEUROLOGY: [
                    "AAN Practice Guidelines",
                    "ESO Guidelines - Stroke Management",
                ],
                Specialty.ENDOCRINOLOGY: [
                    "ADA Standards of Care 2024 - Diabetes",
                    "Thyroid Guidelines - ATA 2023",
                ],
            }

            if top.specialty in specialty_refs:
                references.extend(specialty_refs[top.specialty])

        # Always include general reference
        references.append("UpToDate Medical Database - Última revisión")

        return references

    def _get_disclaimer(self, consultation_type: ConsultationType) -> str:
        """Get appropriate disclaimer."""
        if consultation_type == ConsultationType.PROFESSIONAL:
            return self.disclaimers["professional"]
        if consultation_type == ConsultationType.EMERGENCY:
            return self.disclaimers["emergency"]
        return self.disclaimers["general"]


# =============================================================================
# Factory Functions
# =============================================================================


def create_clinical_formatter(
    config: FormatterConfig | None = None,
) -> ClinicalFormatter:
    """Create clinical formatter."""
    return ClinicalFormatter(config)
