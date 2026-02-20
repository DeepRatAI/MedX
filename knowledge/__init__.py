"""
Base de Conocimiento Médico Expandida - MedeX
==============================================
Módulo de integración que combina todas las condiciones y medicamentos.
Cubre 25+ especialidades médicas con condiciones ICD-10 detalladas.
Categorías normalizadas en español.
"""

from .conditions_cardiovascular import CARDIOVASCULAR_CONDITIONS
from .conditions_respiratory import RESPIRATORY_CONDITIONS
from .conditions_gastrointestinal import GASTROINTESTINAL_CONDITIONS
from .conditions_infectious import INFECTIOUS_CONDITIONS
from .conditions_emergency import EMERGENCY_CONDITIONS
from .conditions_neurological import NEUROLOGICAL_CONDITIONS
from .conditions_endocrine import ENDOCRINE_CONDITIONS
from .conditions_psychiatric import PSYCHIATRIC_CONDITIONS
from .conditions_rheumatologic import RHEUMATOLOGIC_CONDITIONS
from .icd10_catalog import get_all_generated_conditions, GENERATED_STATS
from .medications_database import (
    ALL_MEDICATIONS as _BASE_MEDICATIONS,
    get_medication,
    search_medications as _search_base_meds,
)
from .medications_expanded import MEDICATIONS_EXPANDED_V1
from .category_normalizer import (
    normalize_category,
    get_all_normalized_categories,
    get_master_categories,
    CATEGORY_NORMALIZATION_MAP,
)

# Combinar medicamentos base + expandidos
ALL_MEDICATIONS = {**_BASE_MEDICATIONS, **MEDICATIONS_EXPANDED_V1}


def search_medications(query: str):
    """Busca medicamentos en base completa (original + expandida)."""
    query_lower = query.lower()
    results = []
    # Buscar en base original
    results.extend(_search_base_meds(query))
    # Buscar en expandidos
    for key, med in MEDICATIONS_EXPANDED_V1.items():
        if (
            query_lower in key.lower()
            or query_lower in med.name.lower()
            or query_lower in med.generic_name.lower()
        ):
            results.append(med)
    # Eliminar duplicados por nombre
    seen = set()
    unique = []
    for med in results:
        if med.name not in seen:
            seen.add(med.name)
            unique.append(med)
    return unique


# Get procedurally generated conditions
_GENERATED = get_all_generated_conditions()

# Combinar todas las condiciones (sin normalizar aún)
_ALL_CONDITIONS_RAW = {
    **CARDIOVASCULAR_CONDITIONS,
    **RESPIRATORY_CONDITIONS,
    **GASTROINTESTINAL_CONDITIONS,
    **INFECTIOUS_CONDITIONS,
    **EMERGENCY_CONDITIONS,
    **NEUROLOGICAL_CONDITIONS,
    **ENDOCRINE_CONDITIONS,
    **PSYCHIATRIC_CONDITIONS,
    **RHEUMATOLOGIC_CONDITIONS,
    **_GENERATED,
}


# Normalizar categorías de todas las condiciones
def _normalize_conditions(conditions: dict) -> dict:
    """Aplica normalización de categorías a todas las condiciones."""
    from dataclasses import replace

    normalized = {}
    for code, condition in conditions.items():
        # Normalizar la categoría
        new_category = normalize_category(condition.category)
        # Crear nueva condición con categoría normalizada
        try:
            normalized[code] = replace(condition, category=new_category)
        except TypeError:
            # Si no es dataclass, intentar modificar directamente
            condition.category = new_category
            normalized[code] = condition
    return normalized


# Aplicar normalización
ALL_CONDITIONS = _normalize_conditions(_ALL_CONDITIONS_RAW)


def get_all_conditions():
    """Retorna todas las condiciones médicas."""
    return ALL_CONDITIONS


def get_condition_by_icd10(code: str):
    """Busca condición por código ICD-10."""
    return ALL_CONDITIONS.get(code)


def search_conditions(query: str):
    """Busca condiciones por texto en nombre o descripción."""
    query_lower = query.lower()
    return [
        c
        for c in ALL_CONDITIONS.values()
        if query_lower in c.name.lower() or query_lower in c.description.lower()
    ]


def get_conditions_by_category(category: str):
    """Filtra condiciones por categoria/especialidad."""
    return [
        c for c in ALL_CONDITIONS.values() if category.lower() in c.category.lower()
    ]


# Estadisticas del modulo
STATS = {
    "total_conditions": len(ALL_CONDITIONS),
    "total_medications": len(ALL_MEDICATIONS),
    "medications_base": len(_BASE_MEDICATIONS),
    "medications_expanded": len(MEDICATIONS_EXPANDED_V1),
    "cardiovascular": len(CARDIOVASCULAR_CONDITIONS),
    "respiratory": len(RESPIRATORY_CONDITIONS),
    "gastrointestinal": len(GASTROINTESTINAL_CONDITIONS),
    "infectious": len(INFECTIOUS_CONDITIONS),
    "emergency": len(EMERGENCY_CONDITIONS),
    "neurological": len(NEUROLOGICAL_CONDITIONS),
    "endocrine": len(ENDOCRINE_CONDITIONS),
    "psychiatric": len(PSYCHIATRIC_CONDITIONS),
    "rheumatologic": len(RHEUMATOLOGIC_CONDITIONS),
    **GENERATED_STATS,
}


def get_all_categories() -> list:
    """
    Retorna todas las categorías únicas normalizadas de la KB.
    Ordenadas alfabéticamente.
    """
    categories = {c.category for c in ALL_CONDITIONS.values()}
    return sorted(categories)


def get_category_stats() -> dict:
    """
    Retorna estadísticas de condiciones por categoría.
    """
    from collections import Counter

    categories = [c.category for c in ALL_CONDITIONS.values()]
    return dict(Counter(categories).most_common())


__all__ = [
    "ALL_CONDITIONS",
    "ALL_MEDICATIONS",
    "get_all_conditions",
    "get_condition_by_icd10",
    "search_conditions",
    "search_medications",
    "get_conditions_by_category",
    "get_all_categories",
    "get_category_stats",
    "get_master_categories",
    "normalize_category",
    "STATS",
]

if __name__ == "__main__":
    print(f"MedeX Knowledge Base - {STATS['total_conditions']} condiciones cargadas")
    print(f"Categorías normalizadas: {len(get_all_categories())}")
    for cat, count in STATS.items():
        if cat != "total_conditions":
            print(f"  {cat}: {count}")
