# =============================================================================
# MedeX - Triage Engine
# =============================================================================
"""
Emergency triage engine using ESI 5-level system.

Features:
- Red flag detection
- Vital signs analysis
- ESI level assignment
- Disposition recommendations
- Emergency protocol activation
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from medex.medical.models import (
    TriageAssessment,
    TriageLevel,
    UrgencyLevel,
    VitalSigns,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Red Flags Database
# =============================================================================

# Critical red flags requiring immediate attention (ESI Level 1)
CRITICAL_RED_FLAGS = {
    # Airway/Breathing
    "respiratory arrest",
    "cardiac arrest",
    "apnea",
    "severe respiratory distress",
    "stridor",
    "cyanosis",
    "oxygen saturation < 85",
    "paro respiratorio",
    "paro cardíaco",
    "no respira",
    "cianosis",
    # Circulation
    "pulseless",
    "unresponsive",
    "active massive hemorrhage",
    "exsanguinating hemorrhage",
    "sin pulso",
    "inconsciente",
    "hemorragia masiva",
    # Neurological
    "unresponsive to pain",
    "gcs < 8",
    "glasgow < 8",
    "status epilepticus",
    "convulsión continua",
}

# High-risk red flags (ESI Level 2)
HIGH_RISK_RED_FLAGS = {
    # Cardiac
    "chest pain",
    "acute coronary syndrome",
    "stemi",
    "nstemi",
    "new onset arrhythmia",
    "dolor torácico",
    "dolor de pecho",
    "infarto",
    "arritmia",
    # Neurological
    "stroke symptoms",
    "sudden weakness",
    "slurred speech",
    "facial droop",
    "worst headache of life",
    "thunderclap headache",
    "altered mental status",
    "ictus",
    "derrame cerebral",
    "debilidad súbita",
    "confusión aguda",
    "cefalea en trueno",
    # Respiratory
    "severe shortness of breath",
    "acute asthma attack",
    "pulmonary embolism symptoms",
    "disnea severa",
    "crisis asmática",
    # Other
    "anaphylaxis",
    "severe allergic reaction",
    "overdose",
    "suicidal ideation with plan",
    "anafilaxia",
    "sobredosis",
    "intento suicida",
}

# Moderate red flags (ESI Level 3)
MODERATE_RED_FLAGS = {
    "fever with rash",
    "abdominal pain severe",
    "back pain with neurological symptoms",
    "dehydration",
    "diabetic symptoms",
    "hypoglycemia",
    "hyperglycemia",
    "fiebre con rash",
    "dolor abdominal severo",
    "deshidratación",
}


# =============================================================================
# Configuration
# =============================================================================


@dataclass
class TriageEngineConfig:
    """Configuration for triage engine."""

    # Vital sign thresholds
    critical_hr_high: int = 150
    critical_hr_low: int = 40
    critical_sbp_low: int = 80
    critical_sbp_high: int = 220
    critical_spo2_low: int = 88
    critical_temp_high: float = 40.5
    critical_rr_high: int = 35
    critical_rr_low: int = 8

    # High-risk thresholds
    high_hr_high: int = 120
    high_hr_low: int = 50
    high_sbp_low: int = 90
    high_spo2_low: int = 92
    high_temp_high: float = 39.5
    high_pain_score: int = 8


# =============================================================================
# Triage Engine
# =============================================================================


class TriageEngine:
    """ESI 5-level triage engine."""

    def __init__(self, config: TriageEngineConfig | None = None) -> None:
        """Initialize triage engine."""
        self.config = config or TriageEngineConfig()

    def assess(
        self,
        chief_complaint: str,
        vital_signs: VitalSigns | None = None,
        symptoms: list[str] | None = None,
        age: int | None = None,
        medical_history: list[str] | None = None,
    ) -> TriageAssessment:
        """
        Perform triage assessment.

        Args:
            chief_complaint: Main reason for visit
            vital_signs: Patient vital signs
            symptoms: List of reported symptoms
            age: Patient age
            medical_history: Relevant medical history

        Returns:
            TriageAssessment with level and recommendations
        """
        logger.info(f"Triage assessment for: {chief_complaint[:50]}...")

        symptoms = symptoms or []
        medical_history = medical_history or []

        # Combine text for analysis
        all_text = " ".join(
            [
                chief_complaint.lower(),
                " ".join(s.lower() for s in symptoms),
            ]
        )

        # Check for critical red flags
        critical_flags = self._check_red_flags(all_text, CRITICAL_RED_FLAGS)
        if critical_flags:
            return self._create_level1_assessment(
                chief_complaint, vital_signs, critical_flags
            )

        # Check vital signs for critical values
        if vital_signs:
            critical_vitals = self._check_critical_vitals(vital_signs)
            if critical_vitals:
                return self._create_level1_assessment(
                    chief_complaint, vital_signs, critical_vitals
                )

        # Check for high-risk red flags
        high_risk_flags = self._check_red_flags(all_text, HIGH_RISK_RED_FLAGS)
        if high_risk_flags:
            return self._create_level2_assessment(
                chief_complaint, vital_signs, high_risk_flags
            )

        # Check vital signs for high-risk values
        if vital_signs:
            high_risk_vitals = self._check_high_risk_vitals(vital_signs)
            if high_risk_vitals:
                return self._create_level2_assessment(
                    chief_complaint, vital_signs, high_risk_vitals
                )

        # Check for moderate red flags
        moderate_flags = self._check_red_flags(all_text, MODERATE_RED_FLAGS)
        if moderate_flags:
            return self._create_level3_assessment(
                chief_complaint, vital_signs, moderate_flags
            )

        # Assess resource needs for Level 4 vs 5
        resources_needed = self._estimate_resources(all_text, symptoms)

        if resources_needed >= 2:
            return self._create_level3_assessment(
                chief_complaint, vital_signs, ["Multiple resources needed"]
            )
        elif resources_needed == 1:
            return self._create_level4_assessment(chief_complaint, vital_signs)
        else:
            return self._create_level5_assessment(chief_complaint, vital_signs)

    def _check_red_flags(
        self,
        text: str,
        flags: set[str],
    ) -> list[str]:
        """Check text for red flags."""
        found = []
        for flag in flags:
            if flag in text:
                found.append(flag)
        return found

    def _check_critical_vitals(self, vitals: VitalSigns) -> list[str]:
        """Check for critically abnormal vital signs."""
        critical = []

        if vitals.heart_rate:
            if vitals.heart_rate > self.config.critical_hr_high:
                critical.append(f"Taquicardia crítica: {vitals.heart_rate} bpm")
            elif vitals.heart_rate < self.config.critical_hr_low:
                critical.append(f"Bradicardia crítica: {vitals.heart_rate} bpm")

        if vitals.blood_pressure_systolic:
            if vitals.blood_pressure_systolic < self.config.critical_sbp_low:
                critical.append(
                    f"Hipotensión crítica: {vitals.blood_pressure_systolic} mmHg"
                )
            elif vitals.blood_pressure_systolic > self.config.critical_sbp_high:
                critical.append(
                    f"Crisis hipertensiva: {vitals.blood_pressure_systolic} mmHg"
                )

        if vitals.oxygen_saturation:
            if vitals.oxygen_saturation < self.config.critical_spo2_low:
                critical.append(f"Hipoxemia crítica: SpO2 {vitals.oxygen_saturation}%")

        if vitals.temperature:
            if vitals.temperature > self.config.critical_temp_high:
                critical.append(f"Hiperpirexia: {vitals.temperature}°C")

        if vitals.respiratory_rate:
            if vitals.respiratory_rate > self.config.critical_rr_high:
                critical.append(f"Taquipnea severa: {vitals.respiratory_rate} rpm")
            elif vitals.respiratory_rate < self.config.critical_rr_low:
                critical.append(f"Bradipnea severa: {vitals.respiratory_rate} rpm")

        if vitals.glasgow_coma_scale and vitals.glasgow_coma_scale < 9:
            critical.append(f"GCS crítico: {vitals.glasgow_coma_scale}")

        return critical

    def _check_high_risk_vitals(self, vitals: VitalSigns) -> list[str]:
        """Check for high-risk vital signs."""
        high_risk = []

        if vitals.heart_rate:
            if vitals.heart_rate > self.config.high_hr_high:
                high_risk.append(f"Taquicardia: {vitals.heart_rate} bpm")
            elif vitals.heart_rate < self.config.high_hr_low:
                high_risk.append(f"Bradicardia: {vitals.heart_rate} bpm")

        if vitals.blood_pressure_systolic:
            if vitals.blood_pressure_systolic < self.config.high_sbp_low:
                high_risk.append(f"Hipotensión: {vitals.blood_pressure_systolic} mmHg")

        if vitals.oxygen_saturation:
            if vitals.oxygen_saturation < self.config.high_spo2_low:
                high_risk.append(f"Hipoxemia: SpO2 {vitals.oxygen_saturation}%")

        if vitals.temperature:
            if vitals.temperature > self.config.high_temp_high:
                high_risk.append(f"Fiebre alta: {vitals.temperature}°C")

        if vitals.pain_scale and vitals.pain_scale >= self.config.high_pain_score:
            high_risk.append(f"Dolor severo: {vitals.pain_scale}/10")

        return high_risk

    def _estimate_resources(
        self,
        text: str,
        symptoms: list[str],
    ) -> int:
        """Estimate number of resources needed."""
        resources = 0

        # Lab tests
        lab_keywords = [
            "blood test",
            "lab",
            "análisis",
            "laboratorio",
            "hemograma",
            "bioquímica",
        ]
        if any(kw in text for kw in lab_keywords):
            resources += 1

        # Imaging
        imaging_keywords = [
            "x-ray",
            "radiografía",
            "ct",
            "tac",
            "mri",
            "resonancia",
            "ultrasound",
            "ecografía",
        ]
        if any(kw in text for kw in imaging_keywords):
            resources += 1

        # Procedures
        procedure_keywords = [
            "suture",
            "sutura",
            "iv",
            "intravenous",
            "catheter",
            "sonda",
            "nebulization",
            "nebulización",
        ]
        if any(kw in text for kw in procedure_keywords):
            resources += 1

        # Specialist consultation
        specialist_keywords = [
            "specialist",
            "especialista",
            "consultation",
            "interconsulta",
        ]
        if any(kw in text for kw in specialist_keywords):
            resources += 1

        return resources

    # =========================================================================
    # Assessment Creators
    # =========================================================================

    def _create_level1_assessment(
        self,
        chief_complaint: str,
        vital_signs: VitalSigns | None,
        discriminators: list[str],
    ) -> TriageAssessment:
        """Create Level 1 (Resuscitation) assessment."""
        return TriageAssessment(
            level=TriageLevel.LEVEL_1,
            urgency=UrgencyLevel.CRITICAL,
            chief_complaint=chief_complaint,
            discriminators=discriminators,
            red_flags=discriminators,
            vital_signs=vital_signs,
            recommended_action=(
                "⚠️ ATENCIÓN INMEDIATA REQUERIDA\n"
                "• Activar código de emergencia\n"
                "• Iniciar reanimación si procede\n"
                "• Llamar a equipo de emergencia"
            ),
            disposition="Resuscitation Bay / Código de Emergencia",
        )

    def _create_level2_assessment(
        self,
        chief_complaint: str,
        vital_signs: VitalSigns | None,
        discriminators: list[str],
    ) -> TriageAssessment:
        """Create Level 2 (Emergent) assessment."""
        return TriageAssessment(
            level=TriageLevel.LEVEL_2,
            urgency=UrgencyLevel.HIGH,
            chief_complaint=chief_complaint,
            discriminators=discriminators,
            red_flags=discriminators,
            vital_signs=vital_signs,
            recommended_action=(
                "🔴 ATENCIÓN URGENTE\n"
                "• Evaluación médica en <10 minutos\n"
                "• Monitorización continua\n"
                "• Preparar acceso venoso"
            ),
            disposition="Área de Urgencias - Alta prioridad",
        )

    def _create_level3_assessment(
        self,
        chief_complaint: str,
        vital_signs: VitalSigns | None,
        discriminators: list[str],
    ) -> TriageAssessment:
        """Create Level 3 (Urgent) assessment."""
        return TriageAssessment(
            level=TriageLevel.LEVEL_3,
            urgency=UrgencyLevel.MEDIUM,
            chief_complaint=chief_complaint,
            discriminators=discriminators,
            red_flags=[],
            vital_signs=vital_signs,
            recommended_action=(
                "🟡 ATENCIÓN PRIORITARIA\n"
                "• Evaluación médica en <30 minutos\n"
                "• Múltiples recursos necesarios\n"
                "• Monitorización periódica"
            ),
            disposition="Área de Urgencias - Prioridad media",
        )

    def _create_level4_assessment(
        self,
        chief_complaint: str,
        vital_signs: VitalSigns | None,
    ) -> TriageAssessment:
        """Create Level 4 (Less Urgent) assessment."""
        return TriageAssessment(
            level=TriageLevel.LEVEL_4,
            urgency=UrgencyLevel.LOW,
            chief_complaint=chief_complaint,
            discriminators=["Un recurso necesario"],
            red_flags=[],
            vital_signs=vital_signs,
            recommended_action=(
                "🟢 ATENCIÓN PROGRAMADA\n"
                "• Evaluación médica en <60 minutos\n"
                "• Un recurso diagnóstico/terapéutico\n"
                "• Puede esperar en sala de espera"
            ),
            disposition="Consulta de Urgencias - Baja prioridad",
        )

    def _create_level5_assessment(
        self,
        chief_complaint: str,
        vital_signs: VitalSigns | None,
    ) -> TriageAssessment:
        """Create Level 5 (Non-Urgent) assessment."""
        return TriageAssessment(
            level=TriageLevel.LEVEL_5,
            urgency=UrgencyLevel.INFORMATIONAL,
            chief_complaint=chief_complaint,
            discriminators=["Sin recursos adicionales necesarios"],
            red_flags=[],
            vital_signs=vital_signs,
            recommended_action=(
                "🔵 ATENCIÓN DIFERIDA\n"
                "• Puede esperar >2 horas\n"
                "• Considerar atención primaria\n"
                "• No requiere recursos de urgencias"
            ),
            disposition="Atención Primaria / Consulta Externa",
        )

    # =========================================================================
    # Emergency Detection
    # =========================================================================

    def is_emergency(self, text: str) -> bool:
        """Quick check if text indicates emergency."""
        text_lower = text.lower()

        # Check critical flags
        for flag in CRITICAL_RED_FLAGS:
            if flag in text_lower:
                return True

        # Check high-risk flags
        for flag in HIGH_RISK_RED_FLAGS:
            if flag in text_lower:
                return True

        # Check emergency keywords
        emergency_keywords = {
            "emergency",
            "urgent",
            "emergencia",
            "urgente",
            "help",
            "ayuda",
            "911",
            "dying",
            "muriendo",
        }
        if any(kw in text_lower for kw in emergency_keywords):
            return True

        return False

    def get_emergency_message(self, language: str = "es") -> str:
        """Get emergency warning message."""
        if language == "es":
            return (
                "⚠️ **EMERGENCIA DETECTADA**\n\n"
                "Si se trata de una emergencia médica real:\n\n"
                "1. **Llame al 911 inmediatamente**\n"
                "2. No se demore en buscar ayuda profesional\n"
                "3. Mantenga la calma y siga las instrucciones del operador\n\n"
                "🚨 *Este sistema es solo informativo y no reemplaza "
                "la atención médica de emergencia.*"
            )

        return (
            "⚠️ **EMERGENCY DETECTED**\n\n"
            "If this is a real medical emergency:\n\n"
            "1. **Call 911 immediately**\n"
            "2. Do not delay seeking professional help\n"
            "3. Stay calm and follow dispatcher instructions\n\n"
            "🚨 *This system is informational only and does not replace "
            "emergency medical care.*"
        )


# =============================================================================
# Factory Functions
# =============================================================================


def create_triage_engine(
    config: TriageEngineConfig | None = None,
) -> TriageEngine:
    """Create triage engine."""
    return TriageEngine(config)
