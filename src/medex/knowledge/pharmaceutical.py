"""
Pharmaceutical Database.

Re-exports from the legacy pharmaceutical database for backward compatibility.
"""

import sys
from pathlib import Path

# Add parent to path for legacy imports
legacy_path = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(legacy_path))

try:
    from pharmaceutical_database import (
        PharmaceuticalDatabase,
        DrugMonograph,
        DrugInteraction,
        Dosage,
        AdverseEffect,
        Contraindication,
        PharmacokineticData,
        InteractionSeverity,
        RouteOfAdministration,
    )
except ImportError:
    # Stub implementation
    from dataclasses import dataclass
    from typing import Dict, List, Any, Optional
    from enum import Enum

    class InteractionSeverity(Enum):
        MINOR = "minor"
        MODERATE = "moderate"
        MAJOR = "major"
        CONTRAINDICATED = "contraindicated"

    class RouteOfAdministration(Enum):
        ORAL = "oral"
        IV = "intravenous"
        IM = "intramuscular"
        SC = "subcutaneous"
        TOPICAL = "topical"

    @dataclass
    class DrugInteraction:
        drug_a: str
        drug_b: str
        severity: InteractionSeverity
        mechanism: str
        clinical_effect: str
        management: str

    @dataclass
    class Dosage:
        indication: str
        adult_dose: str
        route: RouteOfAdministration
        frequency: str

    @dataclass
    class AdverseEffect:
        effect: str
        frequency: str
        severity: str

    @dataclass
    class Contraindication:
        condition: str
        severity: str
        reason: str

    @dataclass
    class PharmacokineticData:
        absorption: str
        distribution: str
        metabolism: str
        elimination: str
        half_life: str

    @dataclass
    class DrugMonograph:
        name: str
        generic_name: str
        drug_class: str

    class PharmaceuticalDatabase:
        def __init__(self) -> None:
            self.monographs: Dict[str, DrugMonograph] = {}
            self.interactions: List[DrugInteraction] = []


__all__ = [
    "PharmaceuticalDatabase",
    "DrugMonograph",
    "DrugInteraction",
    "Dosage",
    "AdverseEffect",
    "Contraindication",
    "PharmacokineticData",
    "InteractionSeverity",
    "RouteOfAdministration",
]
