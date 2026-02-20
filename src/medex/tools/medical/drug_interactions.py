# =============================================================================
# MedeX - Medical Tools: Drug Interactions
# =============================================================================
"""
Drug interaction checking tools for MedeX V2.

This module provides:
- Drug-drug interaction checking
- Severity classification
- Clinical recommendations
- Mechanism explanations

Data Sources:
- DrugBank interactions database
- Clinical pharmacology references
- FDA drug interaction warnings
"""

from __future__ import annotations

import logging
from typing import Any

from ..models import ParameterType, ToolCategory
from ..registry import ToolParameter, tool

logger = logging.getLogger(__name__)


# =============================================================================
# Drug Interaction Database (Simplified)
# =============================================================================

# In production, this would be loaded from a proper database
# This is a simplified demonstration dataset
DRUG_INTERACTIONS: dict[frozenset[str], dict[str, Any]] = {
    frozenset({"warfarina", "aspirina"}): {
        "severity": "alta",
        "effect": "Aumento significativo del riesgo de sangrado",
        "mechanism": "Ambos fármacos afectan la hemostasia: warfarina inhibe "
        "factores de coagulación, aspirina inhibe agregación plaquetaria",
        "recommendation": "Evitar combinación si es posible. Si es necesaria, "
        "monitorizar INR frecuentemente y vigilar signos de sangrado",
        "evidence": "Nivel A - Múltiples estudios clínicos",
    },
    frozenset({"metformina", "contraste_yodado"}): {
        "severity": "alta",
        "effect": "Riesgo de acidosis láctica",
        "mechanism": "El contraste yodado puede causar nefropatía, reduciendo "
        "la eliminación de metformina y acumulando lactato",
        "recommendation": "Suspender metformina 48h antes del procedimiento y "
        "reiniciar 48h después con función renal normal",
        "evidence": "Nivel B - Consenso de expertos",
    },
    frozenset({"ibuprofeno", "litio"}): {
        "severity": "alta",
        "effect": "Aumento de niveles séricos de litio (toxicidad)",
        "mechanism": "AINEs reducen la excreción renal de litio por inhibición "
        "de prostaglandinas renales",
        "recommendation": "Evitar AINEs. Si es necesario, monitorizar niveles "
        "de litio y reducir dosis en 25-50%",
        "evidence": "Nivel A - Estudios farmacocinéticos",
    },
    frozenset({"enalapril", "potasio"}): {
        "severity": "moderada",
        "effect": "Riesgo de hiperpotasemia",
        "mechanism": "IECAs reducen la secreción de aldosterona, disminuyendo "
        "la excreción de potasio",
        "recommendation": "Monitorizar potasio sérico. Evitar suplementos de K+ "
        "a menos que exista hipopotasemia documentada",
        "evidence": "Nivel A - Bien documentado",
    },
    frozenset({"metformina", "alcohol"}): {
        "severity": "moderada",
        "effect": "Aumento del riesgo de acidosis láctica e hipoglucemia",
        "mechanism": "El alcohol inhibe la gluconeogénesis hepática y potencia "
        "el efecto hipoglucemiante",
        "recommendation": "Limitar consumo de alcohol. Evitar ayuno prolongado "
        "con consumo de alcohol",
        "evidence": "Nivel B - Estudios observacionales",
    },
    frozenset({"omeprazol", "clopidogrel"}): {
        "severity": "moderada",
        "effect": "Reducción de la eficacia antiagregante del clopidogrel",
        "mechanism": "Omeprazol inhibe CYP2C19, enzima que activa el clopidogrel",
        "recommendation": "Preferir pantoprazol o considerar alternativas. "
        "Separar administración por 12 horas si es posible",
        "evidence": "Nivel B - Datos contradictorios",
    },
    frozenset({"simvastatina", "amiodarona"}): {
        "severity": "alta",
        "effect": "Aumento del riesgo de rabdomiólisis",
        "mechanism": "Amiodarona inhibe CYP3A4, aumentando niveles de simvastatina",
        "recommendation": "Limitar simvastatina a 20mg/día máximo con amiodarona. "
        "Considerar pravastatina o rosuvastatina como alternativas",
        "evidence": "Nivel A - FDA warning",
    },
    frozenset({"fluoxetina", "tramadol"}): {
        "severity": "alta",
        "effect": "Riesgo de síndrome serotoninérgico y convulsiones",
        "mechanism": "Ambos fármacos aumentan serotonina central. Fluoxetina "
        "también inhibe metabolismo de tramadol vía CYP2D6",
        "recommendation": "Evitar combinación. Si es necesaria, usar dosis bajas "
        "y vigilar signos de síndrome serotoninérgico",
        "evidence": "Nivel A - Casos reportados",
    },
    frozenset({"ciprofloxacino", "teofilina"}): {
        "severity": "moderada",
        "effect": "Aumento de niveles de teofilina (toxicidad)",
        "mechanism": "Ciprofloxacino inhibe CYP1A2, principal vía de metabolismo "
        "de teofilina",
        "recommendation": "Reducir dosis de teofilina en 30-50%. Monitorizar "
        "niveles séricos y síntomas de toxicidad",
        "evidence": "Nivel A - Bien documentado",
    },
    frozenset({"metronidazol", "alcohol"}): {
        "severity": "moderada",
        "effect": "Reacción tipo disulfiram",
        "mechanism": "Metronidazol inhibe aldehído deshidrogenasa, causando "
        "acumulación de acetaldehído",
        "recommendation": "Evitar alcohol durante tratamiento y hasta 48h después "
        "de finalizar metronidazol",
        "evidence": "Nivel A - Mecanismo conocido",
    },
}

# Drug name normalization
DRUG_ALIASES: dict[str, str] = {
    "aspirina": "aspirina",
    "acido acetilsalicilico": "aspirina",
    "asa": "aspirina",
    "warfarin": "warfarina",
    "coumadin": "warfarina",
    "sintrom": "warfarina",
    "acenocumarol": "warfarina",
    "metformin": "metformina",
    "glucophage": "metformina",
    "ibuprofen": "ibuprofeno",
    "advil": "ibuprofeno",
    "motrin": "ibuprofeno",
    "enalapril": "enalapril",
    "renitec": "enalapril",
    "omeprazol": "omeprazol",
    "prilosec": "omeprazol",
    "losec": "omeprazol",
    "clopidogrel": "clopidogrel",
    "plavix": "clopidogrel",
    "simvastatina": "simvastatina",
    "zocor": "simvastatina",
    "amiodarona": "amiodarona",
    "cordarone": "amiodarona",
    "fluoxetina": "fluoxetina",
    "prozac": "fluoxetina",
    "tramadol": "tramadol",
    "tramal": "tramadol",
    "litio": "litio",
    "lithium": "litio",
    "ciprofloxacino": "ciprofloxacino",
    "cipro": "ciprofloxacino",
    "teofilina": "teofilina",
    "metronidazol": "metronidazol",
    "flagyl": "metronidazol",
    "potasio": "potasio",
    "kcl": "potasio",
}


def normalize_drug_name(drug: str) -> str:
    """Normalize drug name to standard form."""
    normalized = drug.lower().strip()
    return DRUG_ALIASES.get(normalized, normalized)


# =============================================================================
# Drug Interaction Tool
# =============================================================================


@tool(
    name="check_drug_interactions",
    description="Verifica interacciones medicamentosas entre dos o más fármacos. "
    "Proporciona severidad, mecanismo, y recomendaciones clínicas.",
    category=ToolCategory.DRUG,
    parameters=[
        ToolParameter(
            name="drugs",
            type=ParameterType.ARRAY,
            description="Lista de nombres de medicamentos a verificar (mínimo 2)",
            items={"type": "string"},
            min_length=2,
        ),
    ],
    tags=["farmacología", "interacciones", "seguridad"],
    cache_ttl=3600,  # 1 hour cache
)
async def check_drug_interactions(drugs: list[str]) -> dict[str, Any]:
    """
    Check for drug-drug interactions.

    Args:
        drugs: List of drug names to check

    Returns:
        Dict with interactions found and recommendations
    """
    if len(drugs) < 2:
        return {
            "error": "Se requieren al menos 2 medicamentos para verificar interacciones",
            "interactions": [],
        }

    # Normalize drug names
    normalized = [normalize_drug_name(d) for d in drugs]
    unique_drugs = list(set(normalized))

    interactions = []
    checked_pairs = set()

    # Check all pairs
    for i, drug1 in enumerate(unique_drugs):
        for drug2 in unique_drugs[i + 1 :]:
            pair = frozenset({drug1, drug2})
            if pair in checked_pairs:
                continue
            checked_pairs.add(pair)

            interaction = DRUG_INTERACTIONS.get(pair)
            if interaction:
                interactions.append(
                    {
                        "drugs": sorted([drug1, drug2]),
                        **interaction,
                    }
                )

    # Sort by severity
    severity_order = {"alta": 0, "moderada": 1, "baja": 2}
    interactions.sort(key=lambda x: severity_order.get(x["severity"], 3))

    return {
        "drugs_checked": unique_drugs,
        "total_pairs_checked": len(checked_pairs),
        "interactions_found": len(interactions),
        "interactions": interactions,
        "has_severe_interactions": any(i["severity"] == "alta" for i in interactions),
        "summary": _generate_interaction_summary(interactions),
    }


def _generate_interaction_summary(interactions: list[dict]) -> str:
    """Generate human-readable summary of interactions."""
    if not interactions:
        return "No se encontraron interacciones conocidas entre los medicamentos indicados."

    severe = [i for i in interactions if i["severity"] == "alta"]
    moderate = [i for i in interactions if i["severity"] == "moderada"]

    parts = []
    if severe:
        parts.append(f"⚠️ {len(severe)} interacción(es) de severidad ALTA")
    if moderate:
        parts.append(f"⚡ {len(moderate)} interacción(es) de severidad MODERADA")

    return ". ".join(parts) + ". Revisar recomendaciones específicas."


# =============================================================================
# Drug Info Tool
# =============================================================================


@tool(
    name="get_drug_info",
    description="Obtiene información básica sobre un medicamento incluyendo "
    "clase terapéutica, mecanismo de acción y precauciones.",
    category=ToolCategory.DRUG,
    parameters=[
        ToolParameter(
            name="drug_name",
            type=ParameterType.STRING,
            description="Nombre del medicamento a consultar",
            min_length=2,
            max_length=100,
        ),
    ],
    tags=["farmacología", "información", "referencia"],
    cache_ttl=86400,  # 24 hour cache
)
async def get_drug_info(drug_name: str) -> dict[str, Any]:
    """
    Get basic information about a drug.

    Args:
        drug_name: Name of the drug

    Returns:
        Dict with drug information
    """
    normalized = normalize_drug_name(drug_name)

    # Simplified drug database
    drug_db: dict[str, dict[str, Any]] = {
        "metformina": {
            "name": "Metformina",
            "class": "Biguanida - Antidiabético oral",
            "mechanism": "Reduce producción hepática de glucosa y aumenta "
            "sensibilidad periférica a insulina",
            "indications": [
                "Diabetes mellitus tipo 2",
                "Síndrome de ovario poliquístico",
            ],
            "contraindications": [
                "Insuficiencia renal (TFG <30)",
                "Acidosis metabólica",
                "Insuficiencia hepática severa",
                "Alcoholismo",
            ],
            "common_doses": "500-2550 mg/día dividido en 2-3 dosis",
            "side_effects": ["Náuseas", "Diarrea", "Dolor abdominal", "Sabor metálico"],
            "monitoring": ["Función renal anual", "Vitamina B12 periódica"],
        },
        "enalapril": {
            "name": "Enalapril",
            "class": "IECA - Inhibidor de enzima convertidora de angiotensina",
            "mechanism": "Inhibe conversión de angiotensina I a II, reduciendo "
            "vasoconstricción y retención de sodio",
            "indications": [
                "Hipertensión arterial",
                "Insuficiencia cardíaca",
                "Nefropatía diabética",
            ],
            "contraindications": [
                "Embarazo",
                "Estenosis bilateral arteria renal",
                "Angioedema previo por IECA",
            ],
            "common_doses": "5-40 mg/día en 1-2 dosis",
            "side_effects": ["Tos seca", "Hipotensión", "Hiperpotasemia", "Mareo"],
            "monitoring": ["Potasio sérico", "Creatinina", "Presión arterial"],
        },
        "omeprazol": {
            "name": "Omeprazol",
            "class": "IBP - Inhibidor de bomba de protones",
            "mechanism": "Inhibe irreversiblemente H+/K+-ATPasa en células parietales, "
            "reduciendo secreción ácida gástrica",
            "indications": [
                "ERGE",
                "Úlcera péptica",
                "Gastroprotección con AINEs",
                "Síndrome de Zollinger-Ellison",
            ],
            "contraindications": ["Hipersensibilidad a IBPs"],
            "common_doses": "20-40 mg/día antes del desayuno",
            "side_effects": ["Cefalea", "Diarrea", "Dolor abdominal", "Náuseas"],
            "monitoring": [
                "Magnesio (uso prolongado)",
                "Vitamina B12 (uso prolongado)",
            ],
        },
    }

    info = drug_db.get(normalized)
    if info:
        return {
            "found": True,
            **info,
            "source": "Base de datos MedeX",
            "disclaimer": "Información de referencia. Consultar ficha técnica oficial.",
        }

    return {
        "found": False,
        "drug_name": drug_name,
        "message": f"No se encontró información para '{drug_name}' en la base de datos.",
        "suggestion": "Verificar nombre del medicamento o consultar fuentes oficiales.",
    }
