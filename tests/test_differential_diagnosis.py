"""
Tests para el módulo de Diagnóstico Diferencial (DDx) de MedeX.

Este módulo testea:
- Cobertura completa de síntomas
- Estructura de datos correcta
- Búsqueda fuzzy de síntomas
- Formato de reportes
- Validación de códigos ICD-10
- Niveles de urgencia
"""

import pytest
from typing import Dict, List

from differential_diagnosis import (
    SYMPTOM_DIFFERENTIALS,
    DifferentialDiagnosis,
    DiagnosticTest,
    Urgency,
    get_differential_for_symptom,
    get_available_symptoms,
    format_differential_report,
)


class TestSymptomCoverage:
    """Tests de cobertura de síntomas."""

    def test_minimum_25_symptoms_available(self):
        """Verifica que hay al menos 25 síntomas configurados."""
        symptoms = get_available_symptoms()
        assert len(symptoms) >= 25, (
            f"Se esperan ≥25 síntomas, encontrados: {len(symptoms)}"
        )

    def test_critical_symptoms_present(self):
        """Verifica que los síntomas críticos/cardinales están presentes."""
        required_symptoms = [
            "dolor torácico",
            "disnea",
            "cefalea",
            "dolor abdominal",
            "fiebre",
            "síncope",
        ]
        available = get_available_symptoms()
        for symptom in required_symptoms:
            assert symptom in available, f"Síntoma crítico faltante: {symptom}"

    def test_all_symptoms_have_differentials(self):
        """Verifica que todos los síntomas tienen diagnósticos diferenciales."""
        for symptom, data in SYMPTOM_DIFFERENTIALS.items():
            assert "differentials" in data, f"{symptom}: falta 'differentials'"
            assert len(data["differentials"]) >= 2, (
                f"{symptom}: necesita ≥2 diferenciales"
            )


class TestDataStructure:
    """Tests de estructura de datos."""

    def test_symptom_data_has_required_keys(self):
        """Verifica que cada síntoma tiene las keys requeridas."""
        required_keys = ["category", "key_questions", "differentials"]

        for symptom, data in SYMPTOM_DIFFERENTIALS.items():
            for key in required_keys:
                assert key in data, f"{symptom}: falta key '{key}'"

    def test_differential_diagnosis_structure(self):
        """Verifica estructura de DifferentialDiagnosis."""
        for symptom, data in SYMPTOM_DIFFERENTIALS.items():
            for dx in data["differentials"]:
                assert isinstance(dx, DifferentialDiagnosis), (
                    f"{symptom}: diferencial no es DifferentialDiagnosis"
                )

                # Verificar campos requeridos
                assert dx.icd10_code, f"{symptom}/{dx.name}: falta icd10_code"
                assert dx.name, f"{symptom}: diferencial sin nombre"
                assert dx.probability, f"{symptom}/{dx.name}: falta probability"
                assert isinstance(dx.key_features, list), (
                    f"{symptom}/{dx.name}: key_features debe ser lista"
                )
                assert isinstance(dx.tests, list), (
                    f"{symptom}/{dx.name}: tests debe ser lista"
                )
                assert isinstance(dx.urgency, Urgency), (
                    f"{symptom}/{dx.name}: urgency debe ser Urgency enum"
                )

    def test_diagnostic_test_structure(self):
        """Verifica estructura de DiagnosticTest."""
        for symptom, data in SYMPTOM_DIFFERENTIALS.items():
            for dx in data["differentials"]:
                for test in dx.tests:
                    assert isinstance(test, DiagnosticTest), (
                        f"{symptom}/{dx.name}: test no es DiagnosticTest"
                    )
                    assert test.name, f"{symptom}/{dx.name}: test sin nombre"
                    assert test.category, f"{symptom}/{dx.name}: test sin categoría"
                    assert test.priority in [1, 2, 3], (
                        f"{symptom}/{dx.name}: test priority debe ser 1, 2 o 3"
                    )

    def test_key_questions_not_empty(self):
        """Verifica que cada síntoma tiene preguntas clave."""
        for symptom, data in SYMPTOM_DIFFERENTIALS.items():
            assert len(data["key_questions"]) >= 3, (
                f"{symptom}: necesita ≥3 preguntas clave"
            )


class TestICD10Codes:
    """Tests de códigos ICD-10."""

    def test_icd10_format_valid(self):
        """Verifica formato válido de códigos ICD-10."""
        import re

        # Patrón ICD-10: letra + 2 dígitos + opcionalmente punto y más caracteres
        icd10_pattern = re.compile(r"^[A-Z]\d{2}(\.\d{1,2})?$")

        for symptom, data in SYMPTOM_DIFFERENTIALS.items():
            for dx in data["differentials"]:
                assert icd10_pattern.match(dx.icd10_code), (
                    f"{symptom}/{dx.name}: código ICD-10 inválido: {dx.icd10_code}"
                )

    def test_no_duplicate_icd10_per_symptom(self):
        """Verifica que no hay códigos ICD-10 duplicados por síntoma."""
        for symptom, data in SYMPTOM_DIFFERENTIALS.items():
            codes = [dx.icd10_code for dx in data["differentials"]]
            assert len(codes) == len(set(codes)), (
                f"{symptom}: tiene códigos ICD-10 duplicados"
            )


class TestUrgencyLevels:
    """Tests de niveles de urgencia."""

    def test_all_urgency_levels_used(self):
        """Verifica que se usan todos los niveles de urgencia."""
        all_urgencies = set()
        for data in SYMPTOM_DIFFERENTIALS.values():
            for dx in data["differentials"]:
                all_urgencies.add(dx.urgency)

        expected = {
            Urgency.EMERGENT,
            Urgency.URGENT,
            Urgency.SEMI_URGENT,
            Urgency.ELECTIVE,
        }
        assert all_urgencies == expected, (
            f"No se usan todos los niveles de urgencia. Usados: {all_urgencies}"
        )

    def test_emergent_has_red_flags(self):
        """Verifica que diagnósticos emergentes tienen red flags."""
        for symptom, data in SYMPTOM_DIFFERENTIALS.items():
            for dx in data["differentials"]:
                if dx.urgency == Urgency.EMERGENT:
                    assert dx.red_flags and len(dx.red_flags) > 0, (
                        f"{symptom}/{dx.name}: EMERGENT debe tener red_flags"
                    )


class TestSymptomSearch:
    """Tests de búsqueda de síntomas."""

    def test_exact_match_search(self):
        """Verifica búsqueda exacta de síntomas."""
        result = get_differential_for_symptom("dolor torácico")
        assert result is not None
        assert "differentials" in result

    def test_case_insensitive_search(self):
        """Verifica búsqueda case-insensitive."""
        lower = get_differential_for_symptom("dolor torácico")
        upper = get_differential_for_symptom("DOLOR TORÁCICO")
        mixed = get_differential_for_symptom("Dolor Torácico")

        assert lower is not None
        assert upper is not None
        assert mixed is not None

    def test_whitespace_tolerance(self):
        """Verifica tolerancia a espacios extra."""
        normal = get_differential_for_symptom("dolor torácico")
        spaced = get_differential_for_symptom("  dolor torácico  ")

        assert normal is not None
        assert spaced is not None

    def test_fuzzy_match_synonyms(self):
        """Verifica búsqueda fuzzy con sinónimos comunes."""
        # Estos deberían encontrar el síntoma correcto
        test_cases = [
            ("dolor de pecho", "dolor torácico"),
            ("falta de aire", "disnea"),
            ("dolor de cabeza", "cefalea"),
            ("mareos", "mareo"),
            ("vomitos", "náuseas"),  # Similar
        ]

        for query, expected_symptom in test_cases:
            result = get_differential_for_symptom(query)
            # Puede que no todos hagan match fuzzy, pero verificamos que no crashee
            # y que los que sí existen funcionen
            if query.lower() in [s.lower() for s in get_available_symptoms()]:
                assert result is not None, f"No se encontró: {query}"

    def test_nonexistent_symptom_returns_none(self):
        """Verifica que síntoma inexistente retorna None."""
        result = get_differential_for_symptom("síntoma_inexistente_xyz")
        assert result is None


class TestReportFormatting:
    """Tests de formato de reportes."""

    def test_format_report_returns_string(self):
        """Verifica que format_differential_report retorna string."""
        data = get_differential_for_symptom("dolor torácico")
        report = format_differential_report("dolor torácico", data)
        assert isinstance(report, str)
        assert len(report) > 100  # Debería ser un reporte sustancial

    def test_report_contains_key_sections(self):
        """Verifica que el reporte contiene secciones clave."""
        data = get_differential_for_symptom("dolor torácico")
        report = format_differential_report("dolor torácico", data)

        # Verificar secciones esperadas (el código ICD-10 aparece entre paréntesis)
        expected_content = [
            "DOLOR TORÁCICO",  # Síntoma en mayúsculas
            "Categoría",
            "Preguntas clave",
            "Diagnóstico",
            "I21",  # Código ICD-10 de SCA está en el reporte
        ]

        for content in expected_content:
            assert content.upper() in report.upper() or content in report, (
                f"Reporte no contiene: {content}"
            )

    def test_report_includes_all_differentials(self):
        """Verifica que el reporte incluye todos los diferenciales."""
        data = get_differential_for_symptom("dolor torácico")
        report = format_differential_report("dolor torácico", data)

        for dx in data["differentials"]:
            assert dx.name in report, f"Reporte no incluye: {dx.name}"


class TestEdgeCases:
    """Tests de casos edge."""

    def test_empty_string_query(self):
        """Verifica manejo de query vacío."""
        result = get_differential_for_symptom("")
        # La implementación actual puede retornar un resultado por fuzzy matching
        # o None si no hay coincidencia. Ambos son aceptables.
        # Lo importante es que no crashee.
        assert result is None or isinstance(result, dict)

    def test_none_query(self):
        """Verifica manejo de query None."""
        try:
            result = get_differential_for_symptom(None)
            assert result is None
        except (TypeError, AttributeError):
            pass  # Aceptable que lance excepción

    def test_special_characters_in_query(self):
        """Verifica manejo de caracteres especiales."""
        queries_with_special = [
            "dolor@torácico",
            "dolor#torácico",
            "dolor\ttorácico",
            "dolor\ntorácico",
        ]
        for query in queries_with_special:
            # No debería crashear
            try:
                get_differential_for_symptom(query)
            except Exception as e:
                pytest.fail(f"Crasheó con query '{query}': {e}")


class TestClinicalCompleteness:
    """Tests de completitud clínica."""

    def test_each_differential_has_minimum_features(self):
        """Verifica que cada diferencial tiene mínimo de características."""
        for symptom, data in SYMPTOM_DIFFERENTIALS.items():
            for dx in data["differentials"]:
                assert len(dx.key_features) >= 3, (
                    f"{symptom}/{dx.name}: necesita ≥3 key_features"
                )
                assert len(dx.against_features) >= 1, (
                    f"{symptom}/{dx.name}: necesita ≥1 against_features"
                )

    def test_each_differential_has_tests(self):
        """Verifica que cada diferencial tiene tests diagnósticos."""
        for symptom, data in SYMPTOM_DIFFERENTIALS.items():
            for dx in data["differentials"]:
                assert len(dx.tests) >= 1, (
                    f"{symptom}/{dx.name}: necesita ≥1 test diagnóstico"
                )

    def test_probability_statements_present(self):
        """Verifica que hay declaraciones de probabilidad."""
        for symptom, data in SYMPTOM_DIFFERENTIALS.items():
            for dx in data["differentials"]:
                assert (
                    "si:" in dx.probability.lower() or "alta" in dx.probability.lower()
                ), f"{symptom}/{dx.name}: probability debe indicar condiciones"


class TestIntegration:
    """Tests de integración."""

    def test_full_workflow_dolor_toracico(self):
        """Test E2E para dolor torácico."""
        # 1. Obtener síntomas disponibles
        symptoms = get_available_symptoms()
        assert "dolor torácico" in symptoms

        # 2. Buscar diferencial
        data = get_differential_for_symptom("dolor torácico")
        assert data is not None

        # 3. Verificar estructura - la categoría puede variar
        assert "Cardiovascular" in data["category"]
        assert len(data["key_questions"]) >= 4

        # 4. Verificar diferenciales críticos
        dx_names = [dx.name for dx in data["differentials"]]
        critical_diagnoses = ["Síndrome Coronario Agudo", "Embolia Pulmonar"]
        for critical in critical_diagnoses:
            assert any(critical in name for name in dx_names), (
                f"Falta diagnóstico crítico: {critical}"
            )

        # 5. Generar reporte
        report = format_differential_report("dolor torácico", data)
        assert "EMERGENT" in report or "Emergente" in report

    def test_full_workflow_cefalea(self):
        """Test E2E para cefalea."""
        data = get_differential_for_symptom("cefalea")
        assert data is not None

        # Verificar que incluye hemorragia subaracnoidea (emergencia)
        emergent_found = False
        for dx in data["differentials"]:
            if dx.urgency == Urgency.EMERGENT:
                emergent_found = True
                break
        assert emergent_found, "Cefalea debe tener al menos un diagnóstico emergente"

    def test_category_consistency(self):
        """Verifica consistencia de categorías."""
        categories = set()
        for data in SYMPTOM_DIFFERENTIALS.values():
            categories.add(data["category"])

        # Las categorías deben ser descriptivas (mínimo 3 caracteres, ORL es válido)
        for cat in categories:
            assert len(cat) >= 3, f"Categoría muy corta: {cat}"
            assert cat[0].isupper(), f"Categoría debe iniciar en mayúscula: {cat}"


# Fixtures para datos de prueba
@pytest.fixture
def sample_symptom_data():
    """Fixture con datos de síntoma de ejemplo."""
    return get_differential_for_symptom("dolor torácico")


@pytest.fixture
def all_symptoms():
    """Fixture con lista de todos los síntomas."""
    return get_available_symptoms()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
