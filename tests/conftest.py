"""
Pytest configuration for MedeX tests.
"""

import sys
from pathlib import Path

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@pytest.fixture
def sample_professional_query() -> str:
    """Sample query from a medical professional."""
    return "Paciente de 55 años, diabético tipo 2, presenta dolor precordial de 2 horas de evolución con irradiación a brazo izquierdo. Antecedentes de hipertensión arterial."


@pytest.fixture
def sample_educational_query() -> str:
    """Sample query from a patient/student."""
    return "Me duele el pecho desde hace unas horas, estoy preocupado. ¿Es grave?"


@pytest.fixture
def sample_emergency_query() -> str:
    """Sample emergency query."""
    return "Dolor torácico intenso con dificultad para respirar y sudoración fría"


@pytest.fixture
def sample_routine_query() -> str:
    """Sample routine (non-emergency) query."""
    return "¿Qué es la diabetes y cómo se puede prevenir?"
