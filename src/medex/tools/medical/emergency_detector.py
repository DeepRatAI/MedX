# =============================================================================
# MedeX - Medical Tools: Emergency Detector
# =============================================================================
"""
Emergency detection and triage tools for MedeX V2.

This module provides:
- Red flag symptom detection
- Emergency triage classification
- Critical value identification
- Urgency assessment

Design:
- Evidence-based red flag detection
- Manchester Triage-inspired classification
- Critical lab value alerts
- Clear escalation recommendations

⚠️ DISCLAIMER: These tools are for educational/clinical decision support only.
They do NOT replace clinical judgment. Always err on the side of caution.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from ..models import ParameterType, ToolCategory
from ..registry import ToolParameter, tool

logger = logging.getLogger(__name__)


# =============================================================================
# Red Flag Symptoms Database
# =============================================================================

RED_FLAGS: dict[str, dict[str, Any]] = {
    # Cardiovascular
    "chest_pain_cardiac": {
        "symptoms": ["dolor torácico", "dolor pecho", "opresión pecho", "chest pain"],
        "qualifiers": [
            "irradiado",
            "brazo izquierdo",
            "mandíbula",
            "sudoración",
            "disnea",
        ],
        "urgency": "emergencia",
        "triage_level": 1,
        "condition": "Posible síndrome coronario agudo",
        "action": "Llamar al servicio de emergencias (911). ECG inmediato. Aspirina si disponible y sin contraindicaciones.",
    },
    "stroke_symptoms": {
        "symptoms": [
            "debilidad facial",
            "dificultad hablar",
            "debilidad brazo",
            "confusión súbita",
        ],
        "qualifiers": ["súbito", "repentino", "inicio agudo"],
        "urgency": "emergencia",
        "triage_level": 1,
        "condition": "Posible accidente cerebrovascular",
        "action": "Llamar al servicio de emergencias. Anotar hora de inicio. NO dar medicamentos orales.",
    },
    "anaphylaxis": {
        "symptoms": [
            "dificultad respirar",
            "edema facial",
            "hinchazón lengua",
            "rash generalizado",
        ],
        "qualifiers": ["tras exposición", "picadura", "medicamento", "alimento"],
        "urgency": "emergencia",
        "triage_level": 1,
        "condition": "Posible anafilaxia",
        "action": "Epinefrina IM si disponible. Llamar emergencias. Posición supina con piernas elevadas.",
    },
    # Respiratory
    "respiratory_distress": {
        "symptoms": [
            "dificultad respirar severa",
            "no puede hablar",
            "cianosis",
            "tiraje",
        ],
        "qualifiers": ["progresivo", "severo", "empeorando"],
        "urgency": "emergencia",
        "triage_level": 1,
        "condition": "Insuficiencia respiratoria",
        "action": "Emergencias. Oxígeno si disponible. Posición sentada.",
    },
    "hemoptysis_massive": {
        "symptoms": ["tos con sangre", "hemoptisis", "sangre al toser"],
        "qualifiers": ["gran cantidad", "masiva", "no para"],
        "urgency": "emergencia",
        "triage_level": 1,
        "condition": "Hemoptisis masiva",
        "action": "Emergencias. Posición lateral del lado afectado si conocido.",
    },
    # Neurological
    "severe_headache": {
        "symptoms": ["cefalea severa", "peor dolor cabeza", "thunderclap"],
        "qualifiers": ["súbito", "el peor de mi vida", "rigidez nuca", "fiebre"],
        "urgency": "emergencia",
        "triage_level": 1,
        "condition": "Posible hemorragia subaracnoidea o meningitis",
        "action": "Emergencias. No administrar analgésicos antes de evaluación.",
    },
    "seizure_prolonged": {
        "symptoms": ["convulsión", "crisis", "ataque", "espasmos"],
        "qualifiers": ["más de 5 minutos", "no para", "primera vez"],
        "urgency": "emergencia",
        "triage_level": 1,
        "condition": "Status epilepticus o primera crisis",
        "action": "Proteger de lesiones. NO introducir objetos en boca. Llamar emergencias.",
    },
    "altered_mental_status": {
        "symptoms": ["confusión", "desorientación", "letargia", "inconsciente"],
        "qualifiers": ["súbito", "progresivo", "nuevo"],
        "urgency": "emergencia",
        "triage_level": 1,
        "condition": "Alteración del estado mental",
        "action": "Emergencias. Evaluar glucemia si posible. Proteger vía aérea.",
    },
    # Abdominal
    "acute_abdomen": {
        "symptoms": [
            "dolor abdominal severo",
            "abdomen rígido",
            "dolor intenso estómago",
        ],
        "qualifiers": ["súbito", "rigidez", "no tolera palpación"],
        "urgency": "emergencia",
        "triage_level": 2,
        "condition": "Posible abdomen agudo quirúrgico",
        "action": "Urgencias. Nada vía oral. No analgésicos hasta evaluación quirúrgica.",
    },
    "gi_bleeding_massive": {
        "symptoms": ["vómito sangre", "hematemesis", "melena", "sangrado rectal"],
        "qualifiers": ["abundante", "mareo", "debilidad"],
        "urgency": "emergencia",
        "triage_level": 1,
        "condition": "Hemorragia digestiva",
        "action": "Emergencias. Posición supina. Monitorizar signos de shock.",
    },
    # Obstetric
    "pregnancy_emergency": {
        "symptoms": [
            "sangrado vaginal embarazo",
            "dolor abdominal embarazada",
            "contracciones prematuras",
        ],
        "qualifiers": ["abundante", "severo", "antes de término"],
        "urgency": "emergencia",
        "triage_level": 1,
        "condition": "Emergencia obstétrica",
        "action": "Emergencias obstétricas. Posición lateral izquierda.",
    },
    # Pediatric
    "pediatric_emergency": {
        "symptoms": [
            "niño no respira bien",
            "bebé flácido",
            "fontanela abombada",
            "rash no blanquea",
        ],
        "qualifiers": ["lactante", "menor 3 meses", "fiebre alta"],
        "urgency": "emergencia",
        "triage_level": 1,
        "condition": "Emergencia pediátrica",
        "action": "Emergencias pediátricas. No dar medicamentos sin indicación médica.",
    },
    # Trauma
    "major_trauma": {
        "symptoms": [
            "accidente grave",
            "caída altura",
            "herida penetrante",
            "aplastamiento",
        ],
        "qualifiers": ["alta energía", "pérdida conciencia", "deformidad"],
        "urgency": "emergencia",
        "triage_level": 1,
        "condition": "Trauma mayor",
        "action": "NO MOVER si sospecha lesión columna. Emergencias. Control hemorragia externa.",
    },
}


# Critical lab values requiring immediate attention
CRITICAL_VALUES: dict[str, dict[str, Any]] = {
    "glucose_low": {
        "parameter": "glucosa",
        "critical_low": 50,
        "unit": "mg/dL",
        "urgency": "crítico",
        "action": "Hipoglucemia severa. Administrar glucosa oral si consciente, IV si no.",
    },
    "glucose_high": {
        "parameter": "glucosa",
        "critical_high": 500,
        "unit": "mg/dL",
        "urgency": "crítico",
        "action": "Hiperglucemia severa. Evaluar cetoacidosis o estado hiperosmolar.",
    },
    "potassium_low": {
        "parameter": "potasio",
        "critical_low": 2.5,
        "unit": "mEq/L",
        "urgency": "crítico",
        "action": "Hipopotasemia severa. Riesgo arritmias. Monitorización cardíaca.",
    },
    "potassium_high": {
        "parameter": "potasio",
        "critical_high": 6.5,
        "unit": "mEq/L",
        "urgency": "crítico",
        "action": "Hiperpotasemia severa. ECG inmediato. Calcio IV, insulina+glucosa.",
    },
    "sodium_low": {
        "parameter": "sodio",
        "critical_low": 120,
        "unit": "mEq/L",
        "urgency": "crítico",
        "action": "Hiponatremia severa. Riesgo convulsiones. Corregir lentamente.",
    },
    "sodium_high": {
        "parameter": "sodio",
        "critical_high": 160,
        "unit": "mEq/L",
        "urgency": "crítico",
        "action": "Hipernatremia severa. Corregir con líquidos hipotónicos lentamente.",
    },
    "hemoglobin_low": {
        "parameter": "hemoglobina",
        "critical_low": 7.0,
        "unit": "g/dL",
        "urgency": "crítico",
        "action": "Anemia severa. Considerar transfusión. Buscar fuente de sangrado.",
    },
    "platelets_low": {
        "parameter": "plaquetas",
        "critical_low": 20,
        "unit": "x10³/µL",
        "urgency": "crítico",
        "action": "Trombocitopenia severa. Riesgo sangrado espontáneo. Transfusión plaquetas.",
    },
    "inr_high": {
        "parameter": "INR",
        "critical_high": 5.0,
        "unit": "",
        "urgency": "crítico",
        "action": "INR supraterapéutico. Alto riesgo sangrado. Vitamina K, FFP si sangrado.",
    },
    "troponin_high": {
        "parameter": "troponina",
        "critical_high": 0.04,  # Depends on assay
        "unit": "ng/mL",
        "urgency": "crítico",
        "action": "Troponina elevada. Posible síndrome coronario agudo. ECG y cardio.",
    },
}


# =============================================================================
# Symptom Analysis Tool
# =============================================================================


@tool(
    name="detect_emergency",
    description="Analiza síntomas para detectar banderas rojas y situaciones de emergencia. "
    "Proporciona nivel de triage y acciones recomendadas.",
    category=ToolCategory.EMERGENCY,
    parameters=[
        ToolParameter(
            name="symptoms",
            type=ParameterType.ARRAY,
            description="Lista de síntomas reportados por el paciente",
            required=True,
            items={"type": "string"},
        ),
        ToolParameter(
            name="duration",
            type=ParameterType.STRING,
            description="Duración de los síntomas (ej: 'minutos', 'horas', 'días')",
            required=False,
        ),
        ToolParameter(
            name="onset",
            type=ParameterType.STRING,
            description="Modo de inicio ('súbito', 'gradual')",
            required=False,
        ),
        ToolParameter(
            name="vital_signs",
            type=ParameterType.OBJECT,
            description="Signos vitales si disponibles (fc, pa, fr, temp, spo2)",
            required=False,
        ),
        ToolParameter(
            name="age_years",
            type=ParameterType.INTEGER,
            description="Edad del paciente en años",
            required=False,
        ),
        ToolParameter(
            name="pregnant",
            type=ParameterType.BOOLEAN,
            description="Si la paciente está embarazada",
            required=False,
        ),
    ],
    tags=["emergencia", "triage", "banderas rojas", "urgencia"],
)
async def detect_emergency(
    symptoms: list[str],
    duration: str | None = None,
    onset: str | None = None,
    vital_signs: dict[str, Any] | None = None,
    age_years: int | None = None,
    pregnant: bool | None = None,
) -> dict[str, Any]:
    """
    Detect emergency conditions from symptoms.

    Args:
        symptoms: List of reported symptoms
        duration: Duration of symptoms
        onset: Mode of onset (sudden/gradual)
        vital_signs: Vital signs if available
        age_years: Patient age
        pregnant: If patient is pregnant

    Returns:
        Dict with emergency assessment and recommendations
    """
    detected_emergencies = []
    red_flags = []
    triage_level = 5  # Start with lowest (non-urgent)

    # Normalize symptoms for matching
    symptoms_lower = [s.lower() for s in symptoms]
    symptoms_text = " ".join(symptoms_lower)

    # Check each red flag pattern
    for flag_id, flag_data in RED_FLAGS.items():
        matched = False

        # Check primary symptoms
        for symptom in flag_data["symptoms"]:
            if symptom.lower() in symptoms_text:
                matched = True
                break

        if matched:
            # Add qualifier weight
            qualifier_count = 0
            for qualifier in flag_data.get("qualifiers", []):
                if qualifier.lower() in symptoms_text or (
                    onset and qualifier.lower() in onset.lower()
                ):
                    qualifier_count += 1

            if qualifier_count > 0 or flag_data["urgency"] == "emergencia":
                detected_emergencies.append(
                    {
                        "condition": flag_data["condition"],
                        "urgency": flag_data["urgency"],
                        "action": flag_data["action"],
                        "confidence": "alta" if qualifier_count >= 2 else "moderada",
                    }
                )
                red_flags.append(flag_data["condition"])
                triage_level = min(triage_level, flag_data["triage_level"])

    # Special population checks
    if pregnant and any(
        kw in symptoms_text for kw in ["sangrado", "dolor", "contracciones"]
    ):
        detected_emergencies.append(
            {
                "condition": "Emergencia obstétrica potencial",
                "urgency": "emergencia",
                "action": "Evaluación obstétrica urgente",
                "confidence": "alta",
            }
        )
        triage_level = 1

    if age_years and age_years < 3:
        # Infants/toddlers have lower threshold
        if any(
            kw in symptoms_text for kw in ["fiebre", "letargia", "vomito", "diarrea"]
        ):
            if triage_level > 2:
                triage_level = 2
            detected_emergencies.append(
                {
                    "condition": "Paciente pediátrico de alto riesgo",
                    "urgency": "urgente",
                    "action": "Evaluación pediátrica prioritaria por edad",
                    "confidence": "moderada",
                }
            )

    # Vital signs analysis
    vital_alerts = []
    if vital_signs:
        vital_alerts = _analyze_vital_signs(vital_signs, age_years)
        if vital_alerts:
            triage_level = min(triage_level, 2)

    # Generate response
    triage_map = {
        1: {"level": "ROJO", "description": "Emergencia - Atención inmediata"},
        2: {"level": "NARANJA", "description": "Muy urgente - <10 minutos"},
        3: {"level": "AMARILLO", "description": "Urgente - <60 minutos"},
        4: {"level": "VERDE", "description": "Poco urgente - <120 minutos"},
        5: {"level": "AZUL", "description": "No urgente - Puede esperar"},
    }

    triage_info = triage_map.get(triage_level, triage_map[5])

    return {
        "emergency_detected": len(detected_emergencies) > 0,
        "triage": {
            "level": triage_level,
            "category": triage_info["level"],
            "description": triage_info["description"],
        },
        "red_flags": red_flags,
        "detected_conditions": detected_emergencies,
        "vital_alerts": vital_alerts,
        "immediate_actions": _get_immediate_actions(detected_emergencies),
        "assessment_time": datetime.now().isoformat(),
        "disclaimer": "⚠️ ESTA HERRAMIENTA NO REEMPLAZA LA EVALUACIÓN MÉDICA. "
        "Si hay duda sobre una emergencia, SIEMPRE buscar atención médica inmediata.",
    }


def _analyze_vital_signs(
    vitals: dict[str, Any], age_years: int | None
) -> list[dict[str, Any]]:
    """Analyze vital signs for critical values."""
    alerts = []

    # Heart rate
    if "fc" in vitals or "heart_rate" in vitals:
        hr = vitals.get("fc") or vitals.get("heart_rate")
        if hr:
            if hr < 40:
                alerts.append(
                    {
                        "parameter": "Frecuencia cardíaca",
                        "value": hr,
                        "alert": "Bradicardia severa",
                        "action": "Evaluación urgente",
                    }
                )
            elif hr > 150:
                alerts.append(
                    {
                        "parameter": "Frecuencia cardíaca",
                        "value": hr,
                        "alert": "Taquicardia severa",
                        "action": "Evaluación urgente",
                    }
                )

    # Blood pressure
    if "pa" in vitals or "blood_pressure" in vitals:
        bp = vitals.get("pa") or vitals.get("blood_pressure")
        if isinstance(bp, dict):
            systolic = bp.get("systolic", bp.get("sistolica"))
            diastolic = bp.get("diastolic", bp.get("diastolica"))
            if systolic and systolic < 90:
                alerts.append(
                    {
                        "parameter": "Presión arterial",
                        "value": f"{systolic}/{diastolic}",
                        "alert": "Hipotensión - posible shock",
                        "action": "Emergencia",
                    }
                )
            elif systolic and systolic > 180 or (diastolic and diastolic > 120):
                alerts.append(
                    {
                        "parameter": "Presión arterial",
                        "value": f"{systolic}/{diastolic}",
                        "alert": "Crisis hipertensiva",
                        "action": "Evaluación urgente",
                    }
                )

    # Oxygen saturation
    if "spo2" in vitals or "oxygen_saturation" in vitals:
        spo2 = vitals.get("spo2") or vitals.get("oxygen_saturation")
        if spo2 and spo2 < 90:
            alerts.append(
                {
                    "parameter": "Saturación O2",
                    "value": spo2,
                    "alert": "Hipoxemia",
                    "action": "Oxígeno suplementario. Emergencia si <88%.",
                }
            )

    # Temperature
    if "temp" in vitals or "temperature" in vitals:
        temp = vitals.get("temp") or vitals.get("temperature")
        if temp:
            if temp > 40:
                alerts.append(
                    {
                        "parameter": "Temperatura",
                        "value": temp,
                        "alert": "Hipertermia severa",
                        "action": "Medidas de enfriamiento. Evaluar causa.",
                    }
                )
            elif temp < 35:
                alerts.append(
                    {
                        "parameter": "Temperatura",
                        "value": temp,
                        "alert": "Hipotermia",
                        "action": "Medidas de calentamiento. Buscar causa.",
                    }
                )

    return alerts


def _get_immediate_actions(emergencies: list[dict[str, Any]]) -> list[str]:
    """Extract prioritized immediate actions."""
    if not emergencies:
        return ["Monitorizar síntomas", "Consultar si empeora"]

    actions = []
    for emergency in emergencies:
        if emergency["urgency"] == "emergencia":
            actions.append(f"🚨 {emergency['action']}")
        else:
            actions.append(emergency["action"])

    # Prioritize calling emergency services
    if any(e["urgency"] == "emergencia" for e in emergencies):
        actions.insert(0, "📞 LLAMAR AL SERVICIO DE EMERGENCIAS (911)")

    return actions


# =============================================================================
# Critical Lab Value Check
# =============================================================================


@tool(
    name="check_critical_values",
    description="Verifica si los valores de laboratorio están en rangos críticos "
    "que requieren atención inmediata.",
    category=ToolCategory.EMERGENCY,
    parameters=[
        ToolParameter(
            name="lab_values",
            type=ParameterType.OBJECT,
            description="Diccionario con valores de laboratorio (ej: {'glucose': 45, 'potassium': 6.8})",
            required=True,
        ),
    ],
    tags=["laboratorio", "valores críticos", "urgencia"],
)
async def check_critical_values(
    lab_values: dict[str, float],
) -> dict[str, Any]:
    """
    Check laboratory values for critical ranges.

    Args:
        lab_values: Dictionary of lab parameter names and values

    Returns:
        Dict with critical alerts and actions
    """
    critical_alerts = []
    warnings = []

    # Normalize parameter names
    normalized_values = {}
    for key, value in lab_values.items():
        normalized_key = key.lower().replace(" ", "_")
        normalized_values[normalized_key] = value

    # Check each critical value
    for crit_id, crit_data in CRITICAL_VALUES.items():
        param = crit_data["parameter"].lower().replace(" ", "_")

        # Check if this parameter is in the provided values
        matching_key = None
        for key in normalized_values:
            if param in key or key in param:
                matching_key = key
                break

        if matching_key:
            value = normalized_values[matching_key]

            # Check critical thresholds
            if "critical_low" in crit_data and value < crit_data["critical_low"]:
                critical_alerts.append(
                    {
                        "parameter": crit_data["parameter"].upper(),
                        "value": value,
                        "unit": crit_data["unit"],
                        "threshold": f"< {crit_data['critical_low']}",
                        "severity": "CRÍTICO BAJO",
                        "action": crit_data["action"],
                    }
                )
            elif "critical_high" in crit_data and value > crit_data["critical_high"]:
                critical_alerts.append(
                    {
                        "parameter": crit_data["parameter"].upper(),
                        "value": value,
                        "unit": crit_data["unit"],
                        "threshold": f"> {crit_data['critical_high']}",
                        "severity": "CRÍTICO ALTO",
                        "action": crit_data["action"],
                    }
                )

    # Determine overall urgency
    urgency = "normal"
    if critical_alerts:
        urgency = "CRÍTICO"

    return {
        "has_critical_values": len(critical_alerts) > 0,
        "urgency": urgency,
        "critical_alerts": critical_alerts,
        "warnings": warnings,
        "recommendation": (
            "🚨 NOTIFICAR INMEDIATAMENTE AL MÉDICO TRATANTE"
            if critical_alerts
            else "✅ Sin valores críticos detectados"
        ),
        "disclaimer": "⚠️ Verificar resultados con el laboratorio. "
        "Los rangos críticos pueden variar según el laboratorio.",
    }


# =============================================================================
# Quick Triage Tool
# =============================================================================


@tool(
    name="quick_triage",
    description="Realiza un triage rápido basado en síntoma principal y características. "
    "Útil para orientación inicial.",
    category=ToolCategory.EMERGENCY,
    parameters=[
        ToolParameter(
            name="chief_complaint",
            type=ParameterType.STRING,
            description="Motivo de consulta principal",
            required=True,
        ),
        ToolParameter(
            name="severity",
            type=ParameterType.STRING,
            description="Severidad percibida",
            enum=["leve", "moderado", "severo"],
            required=True,
        ),
        ToolParameter(
            name="duration_hours",
            type=ParameterType.NUMBER,
            description="Duración en horas (usar 0.5 para 30 minutos, etc.)",
            required=True,
        ),
        ToolParameter(
            name="worsening",
            type=ParameterType.BOOLEAN,
            description="¿Los síntomas están empeorando?",
            required=True,
        ),
    ],
    tags=["triage", "orientación", "urgencia"],
)
async def quick_triage(
    chief_complaint: str,
    severity: str,
    duration_hours: float,
    worsening: bool,
) -> dict[str, Any]:
    """
    Perform quick triage assessment.

    Args:
        chief_complaint: Main reason for consultation
        severity: Perceived severity (mild/moderate/severe)
        duration_hours: Duration in hours
        worsening: Whether symptoms are worsening

    Returns:
        Dict with triage recommendation
    """
    # Base score calculation
    score = 0

    # Severity weight
    severity_scores = {"leve": 1, "moderado": 2, "severo": 4}
    score += severity_scores.get(severity, 2)

    # Duration weight (shorter = potentially more acute)
    if duration_hours < 1:
        score += 2
    elif duration_hours < 6:
        score += 1

    # Worsening weight
    if worsening:
        score += 2

    # Check for high-risk keywords
    high_risk_keywords = [
        "pecho",
        "respirar",
        "inconsciente",
        "sangre",
        "convulsión",
        "embarazo",
        "súbito",
        "severo",
        "intenso",
        "no puede",
    ]
    complaint_lower = chief_complaint.lower()
    keyword_matches = sum(1 for kw in high_risk_keywords if kw in complaint_lower)
    score += keyword_matches * 2

    # Determine triage level
    if score >= 8:
        level = 1
        recommendation = "EMERGENCIA - Buscar atención inmediata"
        disposition = "Llamar al 911 o ir a urgencias"
    elif score >= 6:
        level = 2
        recommendation = "MUY URGENTE - Atención en menos de 10 minutos"
        disposition = "Ir a urgencias lo antes posible"
    elif score >= 4:
        level = 3
        recommendation = "URGENTE - Atención en menos de 60 minutos"
        disposition = "Acudir a urgencias o consulta urgente"
    elif score >= 2:
        level = 4
        recommendation = "POCO URGENTE - Puede esperar"
        disposition = "Agendar cita médica pronto"
    else:
        level = 5
        recommendation = "NO URGENTE - Consulta rutinaria"
        disposition = "Agendar cita médica regular"

    color_map = {1: "ROJO", 2: "NARANJA", 3: "AMARILLO", 4: "VERDE", 5: "AZUL"}

    return {
        "triage_level": level,
        "triage_color": color_map[level],
        "recommendation": recommendation,
        "disposition": disposition,
        "assessment_factors": {
            "chief_complaint": chief_complaint,
            "severity": severity,
            "duration_hours": duration_hours,
            "worsening": worsening,
            "risk_score": score,
        },
        "next_steps": _get_next_steps(level),
        "disclaimer": "⚠️ Esta es una orientación inicial. En caso de duda, "
        "siempre es preferible buscar atención médica.",
    }


def _get_next_steps(level: int) -> list[str]:
    """Get recommended next steps based on triage level."""
    steps_map = {
        1: [
            "Llamar al servicio de emergencias (911)",
            "No mover al paciente si hay sospecha de trauma",
            "Mantener la calma y seguir instrucciones del operador",
        ],
        2: [
            "Ir a urgencias lo antes posible",
            "Llevar lista de medicamentos actuales",
            "Llevar documentación médica relevante",
        ],
        3: [
            "Acudir a urgencias hoy",
            "Monitorizar síntomas durante el traslado",
            "Evitar conducir si los síntomas lo afectan",
        ],
        4: [
            "Agendar cita médica en los próximos días",
            "Monitorizar síntomas",
            "Acudir a urgencias si empeora",
        ],
        5: [
            "Agendar cita médica de rutina",
            "Descansar adecuadamente",
            "Monitorizar y anotar síntomas para la consulta",
        ],
    }
    return steps_map.get(level, steps_map[5])
