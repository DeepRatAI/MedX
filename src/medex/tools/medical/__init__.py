# =============================================================================
# MedeX - Medical Tools Package
# =============================================================================
"""
Medical-specific tools for MedeX V2.

This package provides:
- Drug interaction checking
- Dosage calculations
- Laboratory interpretation
- Emergency detection

All tools are designed to integrate with the MedeX Tool System
and provide clinical decision support functionality.
"""

from .dosage_calculator import (
    adjust_dose_renal,
    calculate_bsa,
    calculate_creatinine_clearance,
    calculate_pediatric_dose,
)
from .drug_interactions import (
    check_drug_interactions,
    get_drug_info,
)
from .emergency_detector import (
    check_critical_values,
    detect_emergency,
    quick_triage,
)
from .lab_interpreter import (
    interpret_cbc,
    interpret_liver_panel,
    interpret_thyroid_panel,
)

__all__ = [
    # Drug interactions
    "check_drug_interactions",
    "get_drug_info",
    # Dosage calculations
    "calculate_pediatric_dose",
    "adjust_dose_renal",
    "calculate_bsa",
    "calculate_creatinine_clearance",
    # Lab interpretation
    "interpret_cbc",
    "interpret_liver_panel",
    "interpret_thyroid_panel",
    # Emergency detection
    "detect_emergency",
    "check_critical_values",
    "quick_triage",
]
