# =============================================================================
# MedeX - Medical Tools: Lab Interpreter
# =============================================================================
"""
Laboratory result interpretation tools for MedeX V2.

This module provides:
- Complete blood count interpretation
- Metabolic panel interpretation
- Liver function tests interpretation
- Thyroid function interpretation
- Clinical correlation suggestions

Design:
- Age and sex-specific reference ranges
- Pattern recognition for common conditions
- Evidence-based interpretations
"""

from __future__ import annotations

import logging
from typing import Any

from ..models import ParameterType, ToolCategory
from ..registry import ToolParameter, tool

logger = logging.getLogger(__name__)


# =============================================================================
# Reference Ranges
# =============================================================================

# Complete Blood Count reference ranges
CBC_RANGES: dict[str, dict[str, dict[str, float]]] = {
    "hemoglobin": {
        "male": {"low": 13.5, "high": 17.5, "unit": "g/dL"},
        "female": {"low": 12.0, "high": 16.0, "unit": "g/dL"},
        "child": {"low": 11.0, "high": 14.0, "unit": "g/dL"},
    },
    "hematocrit": {
        "male": {"low": 40, "high": 54, "unit": "%"},
        "female": {"low": 36, "high": 48, "unit": "%"},
        "child": {"low": 33, "high": 42, "unit": "%"},
    },
    "mcv": {
        "adult": {"low": 80, "high": 100, "unit": "fL"},
        "child": {"low": 75, "high": 95, "unit": "fL"},
    },
    "mch": {
        "adult": {"low": 27, "high": 33, "unit": "pg"},
    },
    "mchc": {
        "adult": {"low": 32, "high": 36, "unit": "g/dL"},
    },
    "rdw": {
        "adult": {"low": 11.5, "high": 14.5, "unit": "%"},
    },
    "wbc": {
        "adult": {"low": 4.5, "high": 11.0, "unit": "x10³/µL"},
        "child": {"low": 5.0, "high": 15.0, "unit": "x10³/µL"},
    },
    "platelets": {
        "adult": {"low": 150, "high": 400, "unit": "x10³/µL"},
    },
    "neutrophils": {
        "adult": {"low": 40, "high": 70, "unit": "%"},
    },
    "lymphocytes": {
        "adult": {"low": 20, "high": 40, "unit": "%"},
    },
    "monocytes": {
        "adult": {"low": 2, "high": 8, "unit": "%"},
    },
    "eosinophils": {
        "adult": {"low": 1, "high": 4, "unit": "%"},
    },
    "basophils": {
        "adult": {"low": 0, "high": 1, "unit": "%"},
    },
}

# Metabolic panel reference ranges
METABOLIC_RANGES: dict[str, dict[str, Any]] = {
    "glucose_fasting": {
        "adult": {"low": 70, "high": 100, "unit": "mg/dL"},
        "interpretation": {
            "low": "Hipoglucemia",
            "normal": "Normal",
            "elevated": "Prediabetes (100-125) o Diabetes (≥126)",
        },
    },
    "creatinine": {
        "male": {"low": 0.7, "high": 1.3, "unit": "mg/dL"},
        "female": {"low": 0.6, "high": 1.1, "unit": "mg/dL"},
    },
    "bun": {
        "adult": {"low": 7, "high": 20, "unit": "mg/dL"},
    },
    "sodium": {
        "adult": {"low": 136, "high": 145, "unit": "mEq/L"},
    },
    "potassium": {
        "adult": {"low": 3.5, "high": 5.0, "unit": "mEq/L"},
    },
    "chloride": {
        "adult": {"low": 98, "high": 106, "unit": "mEq/L"},
    },
    "bicarbonate": {
        "adult": {"low": 22, "high": 28, "unit": "mEq/L"},
    },
    "calcium": {
        "adult": {"low": 8.5, "high": 10.5, "unit": "mg/dL"},
    },
}

# Liver function tests
LIVER_RANGES: dict[str, dict[str, Any]] = {
    "alt": {
        "adult": {"low": 7, "high": 56, "unit": "U/L"},
        "name": "Alanina aminotransferasa",
    },
    "ast": {
        "adult": {"low": 10, "high": 40, "unit": "U/L"},
        "name": "Aspartato aminotransferasa",
    },
    "alp": {
        "adult": {"low": 44, "high": 147, "unit": "U/L"},
        "name": "Fosfatasa alcalina",
    },
    "ggt": {
        "male": {"low": 0, "high": 65, "unit": "U/L"},
        "female": {"low": 0, "high": 45, "unit": "U/L"},
        "name": "Gamma-glutamil transferasa",
    },
    "bilirubin_total": {
        "adult": {"low": 0.1, "high": 1.2, "unit": "mg/dL"},
        "name": "Bilirrubina total",
    },
    "bilirubin_direct": {
        "adult": {"low": 0, "high": 0.3, "unit": "mg/dL"},
        "name": "Bilirrubina directa",
    },
    "albumin": {
        "adult": {"low": 3.5, "high": 5.0, "unit": "g/dL"},
    },
    "inr": {
        "adult": {"low": 0.8, "high": 1.2, "unit": ""},
        "therapeutic": {"low": 2.0, "high": 3.0},
    },
}

# Thyroid function
THYROID_RANGES: dict[str, dict[str, Any]] = {
    "tsh": {
        "adult": {"low": 0.4, "high": 4.0, "unit": "mIU/L"},
        "name": "Hormona estimulante de tiroides",
    },
    "t4_free": {
        "adult": {"low": 0.8, "high": 1.8, "unit": "ng/dL"},
        "name": "Tiroxina libre",
    },
    "t3_free": {
        "adult": {"low": 2.3, "high": 4.2, "unit": "pg/mL"},
        "name": "Triyodotironina libre",
    },
}


# =============================================================================
# CBC Interpretation Tool
# =============================================================================


@tool(
    name="interpret_cbc",
    description="Interpreta resultados de hemograma completo (CBC). Proporciona "
    "análisis de cada parámetro y posibles diagnósticos diferenciales.",
    category=ToolCategory.LAB,
    parameters=[
        ToolParameter(
            name="hemoglobin",
            type=ParameterType.NUMBER,
            description="Hemoglobina en g/dL",
            required=True,
        ),
        ToolParameter(
            name="hematocrit",
            type=ParameterType.NUMBER,
            description="Hematocrito en %",
            required=False,
        ),
        ToolParameter(
            name="mcv",
            type=ParameterType.NUMBER,
            description="Volumen corpuscular medio en fL",
            required=False,
        ),
        ToolParameter(
            name="wbc",
            type=ParameterType.NUMBER,
            description="Leucocitos en x10³/µL",
            required=False,
        ),
        ToolParameter(
            name="platelets",
            type=ParameterType.NUMBER,
            description="Plaquetas en x10³/µL",
            required=False,
        ),
        ToolParameter(
            name="sex",
            type=ParameterType.STRING,
            description="Sexo del paciente",
            enum=["male", "female"],
            required=True,
        ),
        ToolParameter(
            name="age_years",
            type=ParameterType.INTEGER,
            description="Edad en años",
            required=True,
        ),
    ],
    tags=["hematología", "hemograma", "anemia"],
    cache_ttl=300,
)
async def interpret_cbc(
    hemoglobin: float,
    sex: str,
    age_years: int,
    hematocrit: float | None = None,
    mcv: float | None = None,
    wbc: float | None = None,
    platelets: float | None = None,
) -> dict[str, Any]:
    """
    Interpret complete blood count results.

    Args:
        hemoglobin: Hemoglobin in g/dL
        sex: Patient sex (male/female)
        age_years: Patient age
        hematocrit: Hematocrit percentage (optional)
        mcv: Mean corpuscular volume in fL (optional)
        wbc: White blood cell count (optional)
        platelets: Platelet count (optional)

    Returns:
        Dict with interpretation and differential diagnoses
    """
    interpretations = []
    findings = []
    differentials = []

    # Determine reference population
    pop = "child" if age_years < 18 else sex

    # Hemoglobin interpretation
    hb_range = CBC_RANGES["hemoglobin"].get(pop, CBC_RANGES["hemoglobin"]["male"])
    hb_status = _classify_value(hemoglobin, hb_range["low"], hb_range["high"])

    interpretations.append(
        {
            "parameter": "Hemoglobina",
            "value": hemoglobin,
            "unit": hb_range["unit"],
            "reference": f"{hb_range['low']}-{hb_range['high']}",
            "status": hb_status,
        }
    )

    if hb_status == "bajo":
        findings.append("Anemia")
        if mcv:
            if mcv < 80:
                findings.append("Microcítica")
                differentials.extend(
                    [
                        "Anemia ferropénica (más común)",
                        "Talasemia",
                        "Anemia de enfermedad crónica",
                        "Anemia sideroblástica",
                    ]
                )
            elif mcv > 100:
                findings.append("Macrocítica")
                differentials.extend(
                    [
                        "Deficiencia de B12",
                        "Deficiencia de folato",
                        "Mielodisplasia",
                        "Hipotiroidismo",
                        "Hepatopatía",
                    ]
                )
            else:
                findings.append("Normocítica")
                differentials.extend(
                    [
                        "Anemia de enfermedad crónica",
                        "Insuficiencia renal crónica",
                        "Hemorragia aguda",
                        "Hemólisis",
                    ]
                )

    # MCV interpretation
    if mcv:
        mcv_range = CBC_RANGES["mcv"].get("adult", CBC_RANGES["mcv"]["adult"])
        mcv_status = _classify_value(mcv, mcv_range["low"], mcv_range["high"])
        interpretations.append(
            {
                "parameter": "VCM",
                "value": mcv,
                "unit": mcv_range["unit"],
                "reference": f"{mcv_range['low']}-{mcv_range['high']}",
                "status": mcv_status,
            }
        )

    # WBC interpretation
    if wbc:
        wbc_pop = "child" if age_years < 18 else "adult"
        wbc_range = CBC_RANGES["wbc"].get(wbc_pop, CBC_RANGES["wbc"]["adult"])
        wbc_status = _classify_value(wbc, wbc_range["low"], wbc_range["high"])
        interpretations.append(
            {
                "parameter": "Leucocitos",
                "value": wbc,
                "unit": wbc_range["unit"],
                "reference": f"{wbc_range['low']}-{wbc_range['high']}",
                "status": wbc_status,
            }
        )

        if wbc_status == "alto":
            findings.append("Leucocitosis")
            differentials.extend(
                [
                    "Infección bacteriana",
                    "Inflamación aguda",
                    "Leucemia",
                    "Corticosteroides",
                ]
            )
        elif wbc_status == "bajo":
            findings.append("Leucopenia")
            differentials.extend(
                [
                    "Infección viral",
                    "Quimioterapia",
                    "Enfermedad autoinmune",
                    "Deficiencia nutricional",
                ]
            )

    # Platelets interpretation
    if platelets:
        plt_range = CBC_RANGES["platelets"]["adult"]
        plt_status = _classify_value(platelets, plt_range["low"], plt_range["high"])
        interpretations.append(
            {
                "parameter": "Plaquetas",
                "value": platelets,
                "unit": plt_range["unit"],
                "reference": f"{plt_range['low']}-{plt_range['high']}",
                "status": plt_status,
            }
        )

        if plt_status == "bajo":
            findings.append("Trombocitopenia")
            if platelets < 50:
                findings.append("Severa - riesgo de sangrado")
        elif plt_status == "alto":
            findings.append("Trombocitosis")

    return {
        "patient": {
            "sex": "Masculino" if sex == "male" else "Femenino",
            "age_years": age_years,
        },
        "interpretations": interpretations,
        "clinical_findings": findings,
        "differential_diagnoses": list(set(differentials)),
        "recommended_workup": _recommend_cbc_workup(findings, differentials),
        "disclaimer": "⚠️ Interpretación de referencia. Correlacionar con "
        "historia clínica y examen físico.",
    }


def _classify_value(value: float, low: float, high: float) -> str:
    """Classify value relative to reference range."""
    if value < low:
        return "bajo"
    elif value > high:
        return "alto"
    return "normal"


def _recommend_cbc_workup(findings: list[str], differentials: list[str]) -> list[str]:
    """Recommend additional workup based on findings."""
    recommendations = []

    if "Anemia" in findings:
        if "Microcítica" in findings:
            recommendations.extend(
                [
                    "Perfil de hierro (ferritina, hierro sérico, TIBC)",
                    "Electroforesis de hemoglobina si ferritina normal",
                ]
            )
        elif "Macrocítica" in findings:
            recommendations.extend(
                [
                    "Vitamina B12 y folato sérico",
                    "Reticulocitos",
                    "TSH si no disponible",
                ]
            )
        else:
            recommendations.extend(
                [
                    "Reticulocitos",
                    "LDH, haptoglobina (descartar hemólisis)",
                    "Función renal",
                ]
            )

    if "Leucocitosis" in findings:
        recommendations.append("Frotis de sangre periférica")

    if "Trombocitopenia" in findings:
        recommendations.extend(
            [
                "Frotis de sangre periférica",
                "Función hepática y renal",
            ]
        )

    return (
        list(set(recommendations))
        if recommendations
        else ["Ninguno adicional requerido"]
    )


# =============================================================================
# Liver Function Interpretation
# =============================================================================


@tool(
    name="interpret_liver_panel",
    description="Interpreta pruebas de función hepática. Identifica patrones "
    "hepatocelular, colestásico o mixto.",
    category=ToolCategory.LAB,
    parameters=[
        ToolParameter(
            name="alt",
            type=ParameterType.NUMBER,
            description="ALT/GPT en U/L",
            required=True,
        ),
        ToolParameter(
            name="ast",
            type=ParameterType.NUMBER,
            description="AST/GOT en U/L",
            required=True,
        ),
        ToolParameter(
            name="alp",
            type=ParameterType.NUMBER,
            description="Fosfatasa alcalina en U/L",
            required=False,
        ),
        ToolParameter(
            name="ggt",
            type=ParameterType.NUMBER,
            description="GGT en U/L",
            required=False,
        ),
        ToolParameter(
            name="bilirubin_total",
            type=ParameterType.NUMBER,
            description="Bilirrubina total en mg/dL",
            required=False,
        ),
        ToolParameter(
            name="albumin",
            type=ParameterType.NUMBER,
            description="Albúmina en g/dL",
            required=False,
        ),
    ],
    tags=["hepatología", "función hepática", "enzimas"],
    cache_ttl=300,
)
async def interpret_liver_panel(
    alt: float,
    ast: float,
    alp: float | None = None,
    ggt: float | None = None,
    bilirubin_total: float | None = None,
    albumin: float | None = None,
) -> dict[str, Any]:
    """
    Interpret liver function panel.

    Args:
        alt: ALT in U/L
        ast: AST in U/L
        alp: Alkaline phosphatase in U/L (optional)
        ggt: GGT in U/L (optional)
        bilirubin_total: Total bilirubin in mg/dL (optional)
        albumin: Albumin in g/dL (optional)

    Returns:
        Dict with pattern identification and interpretation
    """
    interpretations = []
    findings = []

    # ALT interpretation
    alt_range = LIVER_RANGES["alt"]["adult"]
    alt_status = _classify_value(alt, alt_range["low"], alt_range["high"])
    alt_ratio = alt / alt_range["high"]

    interpretations.append(
        {
            "parameter": "ALT (GPT)",
            "value": alt,
            "unit": "U/L",
            "reference": f"{alt_range['low']}-{alt_range['high']}",
            "status": alt_status,
            "times_upper_limit": round(alt_ratio, 1),
        }
    )

    # AST interpretation
    ast_range = LIVER_RANGES["ast"]["adult"]
    ast_status = _classify_value(ast, ast_range["low"], ast_range["high"])
    ast_ratio = ast / ast_range["high"]

    interpretations.append(
        {
            "parameter": "AST (GOT)",
            "value": ast,
            "unit": "U/L",
            "reference": f"{ast_range['low']}-{ast_range['high']}",
            "status": ast_status,
            "times_upper_limit": round(ast_ratio, 1),
        }
    )

    # Calculate AST/ALT ratio (De Ritis ratio)
    de_ritis = ast / alt if alt > 0 else 0

    # Pattern recognition
    pattern = "normal"
    differentials = []

    if alt_status == "alto" or ast_status == "alto":
        if alp:
            alp_range = LIVER_RANGES["alp"]["adult"]
            alp_ratio = alp / alp_range["high"]

            # R factor = (ALT/ULN) / (ALP/ULN)
            r_factor = alt_ratio / alp_ratio if alp_ratio > 0 else 0

            if r_factor >= 5:
                pattern = "hepatocelular"
                findings.append("Patrón hepatocelular (R ≥5)")
                differentials.extend(
                    [
                        "Hepatitis viral aguda",
                        "Hepatitis tóxica/medicamentosa",
                        "Hepatitis autoinmune",
                        "Hepatitis isquémica",
                    ]
                )
            elif r_factor <= 2:
                pattern = "colestásico"
                findings.append("Patrón colestásico (R ≤2)")
                differentials.extend(
                    [
                        "Obstrucción biliar",
                        "Colangitis biliar primaria",
                        "Colangitis esclerosante",
                        "Colestasis intrahepática",
                    ]
                )
            else:
                pattern = "mixto"
                findings.append("Patrón mixto (2 < R < 5)")
                differentials.extend(
                    [
                        "Hepatitis con colestasis",
                        "Cirrosis biliar",
                        "Enfermedad hepática por infiltración",
                    ]
                )
        else:
            # Without ALP, classify by transaminase elevation
            if alt_ratio > 10:
                findings.append("Elevación severa de transaminasas (>10x)")
                differentials.extend(
                    [
                        "Hepatitis viral aguda",
                        "Hepatitis tóxica/isquémica",
                        "Síndrome HELLP",
                    ]
                )
            elif alt_ratio > 3:
                findings.append("Elevación moderada de transaminasas (3-10x)")
            else:
                findings.append("Elevación leve de transaminasas (<3x)")
                differentials.extend(
                    [
                        "Esteatosis hepática (NAFLD)",
                        "Hepatitis crónica viral",
                        "Enfermedad celíaca",
                    ]
                )

    # De Ritis ratio interpretation
    if de_ritis > 2:
        findings.append(
            f"Ratio AST/ALT = {round(de_ritis, 2)} (>2 sugiere hepatopatía alcohólica)"
        )
        differentials.append("Hepatopatía alcohólica")
    elif de_ritis < 1 and alt_status == "alto":
        findings.append(
            f"Ratio AST/ALT = {round(de_ritis, 2)} (<1 sugiere NAFLD/hepatitis viral)"
        )

    # Synthetic function
    synthetic_function = "preservada"
    if albumin and albumin < 3.5:
        synthetic_function = "disminuida"
        findings.append("Hipoalbuminemia - función sintética disminuida")

    return {
        "interpretations": interpretations,
        "pattern": pattern,
        "de_ritis_ratio": round(de_ritis, 2),
        "clinical_findings": findings,
        "synthetic_function": synthetic_function,
        "differential_diagnoses": list(set(differentials)),
        "recommended_workup": _recommend_liver_workup(pattern, differentials),
        "disclaimer": "⚠️ Correlacionar con historia clínica, medicamentos "
        "y factores de riesgo del paciente.",
    }


def _recommend_liver_workup(pattern: str, differentials: list[str]) -> list[str]:
    """Recommend workup based on liver panel pattern."""
    recommendations = []

    if pattern == "hepatocelular":
        recommendations.extend(
            [
                "Serologías virales (VHA, VHB, VHC)",
                "Ecografía hepática",
                "Anticuerpos antinucleares, anti-músculo liso",
            ]
        )
    elif pattern == "colestásico":
        recommendations.extend(
            [
                "Ecografía de vías biliares",
                "Anticuerpos antimitocondriales (AMA)",
                "MRCP si obstrucción biliar sospechada",
            ]
        )

    if "Hepatopatía alcohólica" in differentials:
        recommendations.append("Historia detallada de consumo de alcohol")

    return recommendations if recommendations else ["Monitorización seriada"]


# =============================================================================
# Thyroid Function Interpretation
# =============================================================================


@tool(
    name="interpret_thyroid_panel",
    description="Interpreta pruebas de función tiroidea (TSH, T4L, T3L). "
    "Identifica hiper/hipotiroidismo y posibles etiologías.",
    category=ToolCategory.LAB,
    parameters=[
        ToolParameter(
            name="tsh",
            type=ParameterType.NUMBER,
            description="TSH en mIU/L",
            required=True,
        ),
        ToolParameter(
            name="t4_free",
            type=ParameterType.NUMBER,
            description="T4 libre en ng/dL",
            required=False,
        ),
        ToolParameter(
            name="t3_free",
            type=ParameterType.NUMBER,
            description="T3 libre en pg/mL",
            required=False,
        ),
    ],
    tags=["endocrinología", "tiroides", "TSH"],
    cache_ttl=300,
)
async def interpret_thyroid_panel(
    tsh: float,
    t4_free: float | None = None,
    t3_free: float | None = None,
) -> dict[str, Any]:
    """
    Interpret thyroid function tests.

    Args:
        tsh: TSH in mIU/L
        t4_free: Free T4 in ng/dL (optional)
        t3_free: Free T3 in pg/mL (optional)

    Returns:
        Dict with thyroid status and interpretation
    """
    interpretations = []

    # TSH interpretation
    tsh_range = THYROID_RANGES["tsh"]["adult"]
    tsh_status = _classify_value(tsh, tsh_range["low"], tsh_range["high"])

    interpretations.append(
        {
            "parameter": "TSH",
            "value": tsh,
            "unit": tsh_range["unit"],
            "reference": f"{tsh_range['low']}-{tsh_range['high']}",
            "status": tsh_status,
        }
    )

    # T4 libre interpretation
    t4_status = None
    if t4_free:
        t4_range = THYROID_RANGES["t4_free"]["adult"]
        t4_status = _classify_value(t4_free, t4_range["low"], t4_range["high"])
        interpretations.append(
            {
                "parameter": "T4 Libre",
                "value": t4_free,
                "unit": t4_range["unit"],
                "reference": f"{t4_range['low']}-{t4_range['high']}",
                "status": t4_status,
            }
        )

    # Determine thyroid status
    thyroid_status = "eutiroideo"
    differentials = []
    findings = []

    if tsh_status == "alto":
        if t4_status == "bajo":
            thyroid_status = "hipotiroidismo_primario"
            findings.append("Hipotiroidismo primario manifiesto")
            differentials.extend(
                [
                    "Tiroiditis de Hashimoto (más común)",
                    "Tiroiditis post-parto",
                    "Deficiencia de yodo",
                    "Tiroidectomía previa",
                ]
            )
        elif t4_status == "normal":
            thyroid_status = "hipotiroidismo_subclinico"
            findings.append("Hipotiroidismo subclínico")
            differentials.extend(
                [
                    "Tiroiditis de Hashimoto temprana",
                    "Recuperación de tiroiditis",
                ]
            )
        elif t4_status is None:
            findings.append("TSH elevada - solicitar T4L para caracterizar")

    elif tsh_status == "bajo":
        if t4_status == "alto":
            thyroid_status = "hipertiroidismo_primario"
            findings.append("Hipertiroidismo manifiesto")
            differentials.extend(
                [
                    "Enfermedad de Graves",
                    "Bocio multinodular tóxico",
                    "Adenoma tóxico",
                    "Tiroiditis (fase tirotóxica)",
                ]
            )
        elif t4_status == "normal":
            thyroid_status = "hipertiroidismo_subclinico"
            findings.append("Hipertiroidismo subclínico")
            differentials.extend(
                [
                    "Enfermedad de Graves temprana",
                    "Nódulo autónomo",
                    "Supresión por medicamentos",
                ]
            )
        elif t4_status == "bajo":
            thyroid_status = "hipotiroidismo_central"
            findings.append("Posible hipotiroidismo central (secundario/terciario)")
            differentials.extend(
                [
                    "Adenoma hipofisario",
                    "Síndrome de Sheehan",
                    "Enfermedad hipotalámica",
                ]
            )

    return {
        "interpretations": interpretations,
        "thyroid_status": thyroid_status,
        "clinical_findings": findings,
        "differential_diagnoses": differentials,
        "recommended_workup": _recommend_thyroid_workup(thyroid_status),
        "disclaimer": "⚠️ Interpretar en contexto clínico. Considerar medicamentos "
        "y condiciones que alteran pruebas tiroideas.",
    }


def _recommend_thyroid_workup(status: str) -> list[str]:
    """Recommend additional thyroid workup."""
    workup_map = {
        "hipotiroidismo_primario": [
            "Anticuerpos anti-TPO y anti-tiroglobulina",
            "Ecografía tiroidea",
        ],
        "hipotiroidismo_subclinico": [
            "Anticuerpos anti-TPO",
            "Repetir TSH en 6-8 semanas",
        ],
        "hipertiroidismo_primario": [
            "Anticuerpos anti-receptor de TSH (TRAb)",
            "Ecografía tiroidea con Doppler",
            "Gammagrafía tiroidea",
        ],
        "hipertiroidismo_subclinico": [
            "Repetir perfil tiroideo en 6-8 semanas",
            "Considerar gammagrafía si persiste",
        ],
        "hipotiroidismo_central": [
            "RM de silla turca",
            "Evaluación de otros ejes hipofisarios",
        ],
    }

    return workup_map.get(status, ["Monitorización clínica"])
