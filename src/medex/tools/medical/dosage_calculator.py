# =============================================================================
# MedeX - Medical Tools: Dosage Calculator
# =============================================================================
"""
Dosage calculation tools for MedeX V2.

This module provides:
- Pediatric dosage calculations (weight-based)
- Renal dosage adjustments
- Body surface area calculations
- Unit conversions

Safety:
- All calculations are for reference only
- Always validate with clinical pharmacist
- Consider patient-specific factors
"""

from __future__ import annotations

import logging
import math
from typing import Any

from ..models import ParameterType, ToolCategory
from ..registry import ToolParameter, tool

logger = logging.getLogger(__name__)


# =============================================================================
# Constants
# =============================================================================

# Pediatric dosing reference (mg/kg/day unless specified)
PEDIATRIC_DOSES: dict[str, dict[str, Any]] = {
    "amoxicilina": {
        "standard": {"dose": 25, "max_daily": 3000, "frequency": "c/8h"},
        "high_dose": {"dose": 80, "max_daily": 3000, "frequency": "c/8h"},
        "indication": "Infecciones respiratorias, OMA",
        "notes": "Dosis alta para OMA o sospecha de resistencia",
    },
    "ibuprofeno": {
        "standard": {"dose": 10, "max_daily": 40, "frequency": "c/6-8h"},
        "indication": "Fiebre, dolor, inflamación",
        "notes": "No usar en <6 meses. Máximo 40 mg/kg/día",
        "max_single_dose": 400,
    },
    "paracetamol": {
        "standard": {"dose": 15, "max_daily": 75, "frequency": "c/6h"},
        "indication": "Fiebre, dolor leve-moderado",
        "notes": "Máximo 75 mg/kg/día o 4g/día",
        "max_single_dose": 1000,
    },
    "azitromicina": {
        "standard": {"dose": 10, "max_daily": 500, "frequency": "c/24h"},
        "indication": "Infecciones respiratorias atípicas",
        "notes": "Día 1: 10mg/kg, días 2-5: 5mg/kg",
        "duration": "5 días",
    },
    "amoxicilina_clavulanico": {
        "standard": {"dose": 40, "max_daily": 3000, "frequency": "c/8h"},
        "high_dose": {"dose": 80, "max_daily": 3000, "frequency": "c/8h"},
        "indication": "Infecciones con sospecha de betalactamasas",
        "notes": "Dosis basada en componente amoxicilina",
    },
    "cefalexina": {
        "standard": {"dose": 25, "max_daily": 4000, "frequency": "c/6h"},
        "indication": "Infecciones piel, tejidos blandos",
        "notes": "Puede aumentar a 50-100 mg/kg/día en infecciones severas",
    },
    "prednisolona": {
        "standard": {"dose": 1, "max_daily": 60, "frequency": "c/24h"},
        "high_dose": {"dose": 2, "max_daily": 60, "frequency": "c/24h"},
        "indication": "Asma aguda, crup, reacciones alérgicas",
        "notes": "Ciclos cortos 3-5 días no requieren descenso gradual",
    },
    "salbutamol_nebulizado": {
        "standard": {"dose": 0.15, "max_daily": 5, "frequency": "c/20min x3"},
        "indication": "Crisis asmática",
        "notes": "Dosis en mg/kg. Nebulizar con 3ml SSF. Máximo 5mg/dosis",
        "unit": "mg/dosis",
    },
}

# Renal adjustment factors
RENAL_ADJUSTMENTS: dict[str, dict[str, Any]] = {
    "metformina": {
        "normal": {"tfg_min": 60, "adjustment": "Dosis completa"},
        "mild": {
            "tfg_min": 45,
            "tfg_max": 60,
            "adjustment": "Reducir a 50%, monitorizar",
        },
        "moderate": {"tfg_min": 30, "tfg_max": 45, "adjustment": "Contraindicada"},
        "severe": {"tfg_min": 0, "tfg_max": 30, "adjustment": "Contraindicada"},
    },
    "gabapentina": {
        "normal": {"tfg_min": 60, "adjustment": "300-1200 mg c/8h"},
        "mild": {"tfg_min": 30, "tfg_max": 60, "adjustment": "200-700 mg c/12h"},
        "moderate": {"tfg_min": 15, "tfg_max": 30, "adjustment": "200-700 mg c/24h"},
        "severe": {"tfg_min": 0, "tfg_max": 15, "adjustment": "100-300 mg c/24h"},
    },
    "ciprofloxacino": {
        "normal": {"tfg_min": 30, "adjustment": "Dosis completa"},
        "moderate": {"tfg_min": 0, "tfg_max": 30, "adjustment": "Reducir 50%"},
    },
    "vancomicina": {
        "normal": {"tfg_min": 90, "adjustment": "15-20 mg/kg c/8-12h"},
        "mild": {"tfg_min": 50, "tfg_max": 90, "adjustment": "15-20 mg/kg c/12-24h"},
        "moderate": {
            "tfg_min": 20,
            "tfg_max": 50,
            "adjustment": "15-20 mg/kg c/24-48h",
        },
        "severe": {
            "tfg_min": 0,
            "tfg_max": 20,
            "adjustment": "Dosis de carga, luego según niveles",
        },
        "notes": "Ajustar según niveles valle (15-20 mcg/mL)",
    },
    "enoxaparina": {
        "normal": {"tfg_min": 30, "adjustment": "Dosis completa"},
        "severe": {"tfg_min": 0, "tfg_max": 30, "adjustment": "Reducir 50% o usar HNF"},
        "notes": "Monitorizar anti-Xa en IRC",
    },
}


# =============================================================================
# Pediatric Dosage Calculator
# =============================================================================


@tool(
    name="calculate_pediatric_dose",
    description="Calcula la dosis pediátrica de un medicamento basándose en el peso "
    "del paciente. Proporciona dosis por toma y frecuencia de administración.",
    category=ToolCategory.DOSAGE,
    parameters=[
        ToolParameter(
            name="drug_name",
            type=ParameterType.STRING,
            description="Nombre del medicamento",
            min_length=2,
        ),
        ToolParameter(
            name="weight_kg",
            type=ParameterType.NUMBER,
            description="Peso del paciente en kilogramos",
            minimum=0.5,
            maximum=150,
        ),
        ToolParameter(
            name="dose_type",
            type=ParameterType.STRING,
            description="Tipo de dosificación",
            required=False,
            enum=["standard", "high_dose"],
            default="standard",
        ),
    ],
    tags=["pediatría", "dosificación", "cálculo"],
)
async def calculate_pediatric_dose(
    drug_name: str,
    weight_kg: float,
    dose_type: str = "standard",
) -> dict[str, Any]:
    """
    Calculate pediatric medication dose.

    Args:
        drug_name: Name of the medication
        weight_kg: Patient weight in kg
        dose_type: Dosing type (standard or high_dose)

    Returns:
        Dict with calculated doses and recommendations
    """
    # Normalize drug name
    drug_key = drug_name.lower().strip().replace(" ", "_")
    drug_key = drug_key.replace("-", "_").replace("/", "_")

    drug_info = PEDIATRIC_DOSES.get(drug_key)
    if not drug_info:
        return {
            "found": False,
            "drug_name": drug_name,
            "message": f"No se encontró información de dosificación para '{drug_name}'",
            "available_drugs": list(PEDIATRIC_DOSES.keys()),
        }

    # Get dose parameters
    dose_params = drug_info.get(dose_type, drug_info.get("standard"))
    if not dose_params:
        return {
            "found": False,
            "drug_name": drug_name,
            "message": f"Tipo de dosis '{dose_type}' no disponible para {drug_name}",
        }

    dose_per_kg = dose_params["dose"]
    max_daily = dose_params.get("max_daily", float("inf"))
    frequency = dose_params.get("frequency", "c/8h")

    # Calculate doses
    daily_dose = dose_per_kg * weight_kg
    daily_dose = min(daily_dose, max_daily)

    # Determine doses per day from frequency
    doses_per_day = _parse_frequency(frequency)
    single_dose = daily_dose / doses_per_day

    # Apply max single dose if specified
    max_single = dose_params.get("max_single_dose")
    if max_single and single_dose > max_single:
        single_dose = max_single
        daily_dose = single_dose * doses_per_day

    return {
        "found": True,
        "drug_name": drug_name,
        "dose_type": dose_type,
        "patient_weight_kg": weight_kg,
        "calculation": {
            "dose_per_kg": dose_per_kg,
            "calculated_daily_dose_mg": round(daily_dose, 1),
            "single_dose_mg": round(single_dose, 1),
            "frequency": frequency,
            "doses_per_day": doses_per_day,
        },
        "indication": drug_info.get("indication"),
        "notes": drug_info.get("notes"),
        "duration": drug_info.get("duration"),
        "max_limits": {
            "max_daily_mg": max_daily,
            "max_single_dose_mg": max_single,
        },
        "disclaimer": "⚠️ Dosis de referencia. Verificar con fuentes oficiales "
        "y ajustar según condición clínica del paciente.",
    }


def _parse_frequency(frequency: str) -> int:
    """Parse frequency string to doses per day."""
    freq_map = {
        "c/4h": 6,
        "c/6h": 4,
        "c/8h": 3,
        "c/12h": 2,
        "c/24h": 1,
        "c/6-8h": 3,  # Conservative estimate
        "c/20min x3": 3,  # Special case for acute nebulization
    }
    return freq_map.get(frequency, 3)


# =============================================================================
# Renal Dose Adjustment
# =============================================================================


@tool(
    name="adjust_dose_renal",
    description="Proporciona ajuste de dosis de medicamentos según función renal "
    "(TFG). Incluye recomendaciones específicas para insuficiencia renal.",
    category=ToolCategory.DOSAGE,
    parameters=[
        ToolParameter(
            name="drug_name",
            type=ParameterType.STRING,
            description="Nombre del medicamento",
            min_length=2,
        ),
        ToolParameter(
            name="gfr",
            type=ParameterType.NUMBER,
            description="Tasa de filtración glomerular (TFG/GFR) en mL/min/1.73m²",
            minimum=0,
            maximum=200,
        ),
    ],
    tags=["nefrología", "ajuste", "insuficiencia renal"],
)
async def adjust_dose_renal(
    drug_name: str,
    gfr: float,
) -> dict[str, Any]:
    """
    Get renal dose adjustment recommendations.

    Args:
        drug_name: Name of the medication
        gfr: Glomerular filtration rate in mL/min/1.73m²

    Returns:
        Dict with adjustment recommendations
    """
    drug_key = drug_name.lower().strip()

    adjustments = RENAL_ADJUSTMENTS.get(drug_key)
    if not adjustments:
        return {
            "found": False,
            "drug_name": drug_name,
            "gfr": gfr,
            "message": f"No se encontró información de ajuste renal para '{drug_name}'",
            "available_drugs": list(RENAL_ADJUSTMENTS.keys()),
            "recommendation": "Consultar literatura farmacológica o farmacéutico clínico",
        }

    # Find applicable adjustment level
    applicable_adjustment = None
    renal_stage = "unknown"

    for stage, params in adjustments.items():
        if stage in ("notes",):
            continue

        tfg_min = params.get("tfg_min", 0)
        tfg_max = params.get("tfg_max", float("inf"))

        if tfg_min <= gfr < tfg_max or (tfg_max == float("inf") and gfr >= tfg_min):
            applicable_adjustment = params["adjustment"]
            renal_stage = stage
            break

    return {
        "found": True,
        "drug_name": drug_name,
        "gfr": gfr,
        "gfr_category": _categorize_gfr(gfr),
        "renal_stage": renal_stage,
        "adjustment": applicable_adjustment or "No se encontró ajuste específico",
        "notes": adjustments.get("notes"),
        "disclaimer": "⚠️ Ajustes de referencia. Individualizar según respuesta "
        "clínica y niveles séricos cuando estén disponibles.",
    }


def _categorize_gfr(gfr: float) -> str:
    """Categorize GFR according to KDIGO stages."""
    if gfr >= 90:
        return "G1 - Normal o alto (≥90)"
    elif gfr >= 60:
        return "G2 - Levemente disminuido (60-89)"
    elif gfr >= 45:
        return "G3a - Leve a moderadamente disminuido (45-59)"
    elif gfr >= 30:
        return "G3b - Moderada a severamente disminuido (30-44)"
    elif gfr >= 15:
        return "G4 - Severamente disminuido (15-29)"
    else:
        return "G5 - Falla renal (<15)"


# =============================================================================
# Body Surface Area Calculator
# =============================================================================


@tool(
    name="calculate_bsa",
    description="Calcula el área de superficie corporal (ASC/BSA) usando las fórmulas "
    "de Mosteller y DuBois. Útil para dosificación de quimioterapia.",
    category=ToolCategory.DOSAGE,
    parameters=[
        ToolParameter(
            name="weight_kg",
            type=ParameterType.NUMBER,
            description="Peso en kilogramos",
            minimum=0.5,
            maximum=300,
        ),
        ToolParameter(
            name="height_cm",
            type=ParameterType.NUMBER,
            description="Altura en centímetros",
            minimum=30,
            maximum=250,
        ),
    ],
    tags=["oncología", "superficie corporal", "quimioterapia"],
)
async def calculate_bsa(
    weight_kg: float,
    height_cm: float,
) -> dict[str, Any]:
    """
    Calculate body surface area using multiple formulas.

    Args:
        weight_kg: Weight in kilograms
        height_cm: Height in centimeters

    Returns:
        Dict with BSA calculations
    """
    # Mosteller formula: sqrt((height_cm * weight_kg) / 3600)
    bsa_mosteller = math.sqrt((height_cm * weight_kg) / 3600)

    # DuBois formula: 0.007184 * height^0.725 * weight^0.425
    bsa_dubois = 0.007184 * (height_cm**0.725) * (weight_kg**0.425)

    # Haycock formula (preferred for pediatrics)
    bsa_haycock = 0.024265 * (height_cm**0.3964) * (weight_kg**0.5378)

    # Calculate BMI for reference
    height_m = height_cm / 100
    bmi = weight_kg / (height_m**2)

    return {
        "input": {
            "weight_kg": weight_kg,
            "height_cm": height_cm,
        },
        "bsa_m2": {
            "mosteller": round(bsa_mosteller, 3),
            "dubois": round(bsa_dubois, 3),
            "haycock": round(bsa_haycock, 3),
            "recommended": round(bsa_mosteller, 3),  # Most commonly used
        },
        "bmi": round(bmi, 1),
        "bmi_category": _categorize_bmi(bmi),
        "notes": {
            "mosteller": "Fórmula más utilizada en oncología",
            "dubois": "Fórmula clásica para adultos",
            "haycock": "Preferida en pediatría",
        },
        "disclaimer": "Usar BSA para cálculo de dosis de quimioterapia "
        "y otros medicamentos que requieran dosificación por superficie.",
    }


def _categorize_bmi(bmi: float) -> str:
    """Categorize BMI according to WHO classification."""
    if bmi < 18.5:
        return "Bajo peso (<18.5)"
    elif bmi < 25:
        return "Normal (18.5-24.9)"
    elif bmi < 30:
        return "Sobrepeso (25-29.9)"
    elif bmi < 35:
        return "Obesidad grado I (30-34.9)"
    elif bmi < 40:
        return "Obesidad grado II (35-39.9)"
    else:
        return "Obesidad grado III (≥40)"


# =============================================================================
# Creatinine Clearance Calculator
# =============================================================================


@tool(
    name="calculate_creatinine_clearance",
    description="Calcula el aclaramiento de creatinina usando la fórmula de "
    "Cockcroft-Gault. Esencial para ajuste de dosis en insuficiencia renal.",
    category=ToolCategory.DOSAGE,
    parameters=[
        ToolParameter(
            name="age_years",
            type=ParameterType.INTEGER,
            description="Edad en años",
            minimum=18,
            maximum=120,
        ),
        ToolParameter(
            name="weight_kg",
            type=ParameterType.NUMBER,
            description="Peso en kilogramos",
            minimum=30,
            maximum=200,
        ),
        ToolParameter(
            name="creatinine_mg_dl",
            type=ParameterType.NUMBER,
            description="Creatinina sérica en mg/dL",
            minimum=0.1,
            maximum=20,
        ),
        ToolParameter(
            name="is_female",
            type=ParameterType.BOOLEAN,
            description="True si el paciente es mujer",
        ),
    ],
    tags=["nefrología", "función renal", "aclaramiento"],
)
async def calculate_creatinine_clearance(
    age_years: int,
    weight_kg: float,
    creatinine_mg_dl: float,
    is_female: bool,
) -> dict[str, Any]:
    """
    Calculate creatinine clearance using Cockcroft-Gault formula.

    Args:
        age_years: Patient age in years
        weight_kg: Weight in kilograms
        creatinine_mg_dl: Serum creatinine in mg/dL
        is_female: True if patient is female

    Returns:
        Dict with calculated clearance and interpretation
    """
    # Cockcroft-Gault formula
    # CrCl = ((140 - age) * weight) / (72 * SCr)
    # Multiply by 0.85 for females

    crcl = ((140 - age_years) * weight_kg) / (72 * creatinine_mg_dl)
    if is_female:
        crcl *= 0.85

    # Estimate GFR stage
    gfr_category = _categorize_gfr(crcl)

    return {
        "input": {
            "age_years": age_years,
            "weight_kg": weight_kg,
            "creatinine_mg_dl": creatinine_mg_dl,
            "sex": "Femenino" if is_female else "Masculino",
        },
        "creatinine_clearance_ml_min": round(crcl, 1),
        "gfr_category": gfr_category,
        "formula_used": "Cockcroft-Gault",
        "interpretation": _interpret_crcl(crcl),
        "notes": [
            "Cockcroft-Gault usa peso real (no ideal)",
            "En obesidad mórbida, considerar usar peso ajustado",
            "En caquexia, la fórmula puede sobrestimar TFG",
            "Para ajuste de dosis, preferir esta fórmula sobre MDRD/CKD-EPI",
        ],
        "disclaimer": "⚠️ Esta es una estimación. En situaciones críticas "
        "o pacientes complejos, considerar medición directa de TFG.",
    }


def _interpret_crcl(crcl: float) -> str:
    """Interpret creatinine clearance value."""
    if crcl >= 90:
        return "Función renal normal. No requiere ajuste de dosis en la mayoría de fármacos."
    elif crcl >= 60:
        return "Disminución leve. Algunos fármacos pueden requerir ajuste menor."
    elif crcl >= 30:
        return "Disminución moderada. Múltiples fármacos requieren ajuste de dosis."
    elif crcl >= 15:
        return (
            "Disminución severa. La mayoría de fármacos requieren ajuste significativo."
        )
    else:
        return "Falla renal. Considerar alternativas o diálisis para eliminación de fármacos."
