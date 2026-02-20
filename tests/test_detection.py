"""
Tests for user type and emergency detection.
"""

import pytest

from medex.detection.user_type import UserTypeDetector, DetectionResult
from medex.detection.emergency import EmergencyDetector, EmergencyLevel


class TestUserTypeDetector:
    """Tests for UserTypeDetector."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.detector = UserTypeDetector()

    def test_detects_professional_patient_age_pattern(self) -> None:
        """Test detection of 'paciente de X años' pattern."""
        query = "Paciente de 65 años con antecedentes de diabetes"
        result = self.detector.detect(query)

        assert result.user_type == "Professional"
        assert result.professional_score >= 3

    def test_detects_professional_clinical_case(self) -> None:
        """Test detection of clinical case terminology."""
        query = "Caso clínico: paciente con diagnóstico diferencial de IAM"
        result = self.detector.detect(query)

        assert result.user_type == "Professional"
        assert result.confidence >= 0.6

    def test_detects_educational_personal_pain(self) -> None:
        """Test detection of personal pain description."""
        query = "Me duele mucho la cabeza desde ayer"
        result = self.detector.detect(query)

        assert result.user_type == "Educational"
        assert result.educational_score >= 3

    def test_detects_educational_worry(self) -> None:
        """Test detection of worry/concern patterns."""
        query = "Estoy preocupado porque mi hijo tiene fiebre"
        result = self.detector.detect(query)

        assert result.user_type == "Educational"

    def test_ambiguous_defaults_to_educational(self) -> None:
        """Test that ambiguous queries default to Educational."""
        query = "Información sobre hipertensión"
        result = self.detector.detect(query)

        # Ambiguous should default to Educational for safety
        assert result.user_type == "Educational"

    def test_is_professional_convenience_method(self) -> None:
        """Test the is_professional convenience method."""
        professional_query = "Paciente de 40 años con protocolo de manejo"
        educational_query = "Me duele el estómago"

        assert self.detector.is_professional(professional_query) is True
        assert self.detector.is_professional(educational_query) is False

    def test_matched_patterns_are_recorded(self) -> None:
        """Test that matched patterns are recorded in result."""
        query = "Paciente de 50 años, caso clínico"
        result = self.detector.detect(query)

        assert len(result.matched_patterns) > 0
        assert any("PRO:" in p for p in result.matched_patterns)


class TestEmergencyDetector:
    """Tests for EmergencyDetector."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.detector = EmergencyDetector()

    def test_detects_critical_chest_pain(self) -> None:
        """Test detection of critical chest pain."""
        query = "Tengo dolor precordial muy intenso"
        result = self.detector.detect(query)

        assert result.is_emergency is True
        assert result.level == EmergencyLevel.CRITICAL
        assert result.category == "cardiac"

    def test_detects_critical_respiratory(self) -> None:
        """Test detection of critical respiratory distress."""
        query = "No puede respirar, tiene dificultad respiratoria severa"
        result = self.detector.detect(query)

        assert result.is_emergency is True
        assert result.level == EmergencyLevel.CRITICAL
        assert result.category == "respiratory"

    def test_detects_critical_loss_of_consciousness(self) -> None:
        """Test detection of loss of consciousness."""
        query = "Mi padre perdió la conciencia de repente"
        result = self.detector.detect(query)

        assert result.is_emergency is True
        assert result.level == EmergencyLevel.CRITICAL

    def test_detects_urgent_high_fever(self) -> None:
        """Test detection of urgent conditions."""
        query = "Mi hijo tiene fiebre alta de 40 grados"
        result = self.detector.detect(query)

        assert result.is_emergency is True
        assert result.level == EmergencyLevel.URGENT

    def test_no_emergency_routine_query(self) -> None:
        """Test that routine queries are not flagged."""
        query = "¿Cuáles son los síntomas de la gripe?"
        result = self.detector.detect(query)

        assert result.is_emergency is False
        assert result.level == EmergencyLevel.NONE
        assert len(result.matched_keywords) == 0

    def test_is_emergency_convenience_method(self) -> None:
        """Test the is_emergency convenience method."""
        emergency_query = "Dolor torácico con sudoración"
        routine_query = "Tengo un resfriado"

        assert self.detector.is_emergency(emergency_query) is True
        assert self.detector.is_emergency(routine_query) is False

    def test_is_critical_convenience_method(self) -> None:
        """Test the is_critical convenience method."""
        critical_query = "Convulsiones y pérdida de conciencia"
        urgent_query = "Dolor intenso en el abdomen"

        assert self.detector.is_critical(critical_query) is True
        assert self.detector.is_critical(urgent_query) is False

    def test_psychiatric_emergency(self) -> None:
        """Test detection of psychiatric emergencies."""
        query = "Tengo pensamientos suicidas"
        result = self.detector.detect(query)

        assert result.is_emergency is True
        assert result.category == "psychiatric"


class TestDetectionIntegration:
    """Integration tests for detection modules."""

    def test_professional_emergency_combination(
        self,
        sample_professional_query: str,
    ) -> None:
        """Test detection of professional query with emergency content."""
        user_detector = UserTypeDetector()
        emergency_detector = EmergencyDetector()

        user_result = user_detector.detect(sample_professional_query)
        emergency_result = emergency_detector.detect(sample_professional_query)

        # Should detect as professional AND as emergency
        assert user_result.user_type == "Professional"
        assert emergency_result.is_emergency is True

    def test_educational_emergency_combination(
        self,
        sample_emergency_query: str,
    ) -> None:
        """Test detection of patient query with emergency content."""
        user_detector = UserTypeDetector()
        emergency_detector = EmergencyDetector()

        user_result = user_detector.detect(sample_emergency_query)
        emergency_result = emergency_detector.detect(sample_emergency_query)

        # Should detect as educational (patient) AND as emergency
        assert user_result.user_type == "Educational"
        assert emergency_result.is_emergency is True
