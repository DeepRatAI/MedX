"""
Tests para el módulo i18n de MedeX
==================================
Verifica traducciones, cambio de idioma y funciones helper.
"""

import pytest
from i18n import (
    TRANSLATIONS,
    Language,
    Translator,
    get_language,
    get_translator,
    set_language,
    t,
)


class TestTranslator:
    """Tests para la clase Translator"""

    def test_translator_initialization(self):
        """Verificar inicialización con idioma por defecto"""
        translator = Translator()
        assert translator.language == "es"

    def test_translator_with_custom_language(self):
        """Verificar inicialización con idioma personalizado"""
        translator = Translator(language="en")
        assert translator.language == "en"

    def test_translator_call_spanish(self):
        """Verificar traducción en español"""
        translator = Translator(language="es")
        result = translator("app_title")
        assert result == "MedeX - Sistema de IA Médica"

    def test_translator_call_english(self):
        """Verificar traducción en inglés"""
        translator = Translator(language="en")
        result = translator("app_title")
        assert result == "MedeX - Medical AI System"

    def test_translator_missing_key(self):
        """Verificar comportamiento con clave inexistente"""
        translator = Translator()
        result = translator("nonexistent_key_12345")
        assert result == "[nonexistent_key_12345]"

    def test_set_language(self):
        """Verificar cambio de idioma"""
        translator = Translator(language="es")
        assert translator.get_language() == "es"

        translator.set_language("en")
        assert translator.get_language() == "en"

    def test_set_invalid_language(self):
        """Verificar que idioma inválido no cambia el estado"""
        translator = Translator(language="es")
        translator.set_language("fr")  # francés no soportado
        assert translator.get_language() == "es"  # debe mantener español

    def test_get_available_languages(self):
        """Verificar idiomas disponibles"""
        translator = Translator()
        langs = translator.get_available_languages()

        assert "es" in langs
        assert "en" in langs
        assert langs["es"] == "Español"
        assert langs["en"] == "English"


class TestGlobalFunctions:
    """Tests para funciones globales del módulo"""

    def test_get_translator_singleton(self):
        """Verificar que get_translator retorna singleton"""
        t1 = get_translator()
        t2 = get_translator()
        assert t1 is t2

    def test_t_shortcut_spanish(self):
        """Verificar función t() en español"""
        set_language("es")
        result = t("knowledge_base")
        assert result == "Base de Conocimiento"

    def test_t_shortcut_english(self):
        """Verificar función t() en inglés"""
        set_language("en")
        result = t("knowledge_base")
        assert result == "Knowledge Base"

    def test_set_and_get_language(self):
        """Verificar set_language y get_language"""
        set_language("es")
        assert get_language() == "es"

        set_language("en")
        assert get_language() == "en"


class TestTranslationKeys:
    """Tests para verificar que todas las claves tienen traducciones"""

    def test_all_keys_have_spanish(self):
        """Verificar que todas las claves tienen traducción española"""
        for key, translations in TRANSLATIONS.items():
            assert "es" in translations, f"Missing Spanish translation for: {key}"
            assert translations["es"], f"Empty Spanish translation for: {key}"

    def test_all_keys_have_english(self):
        """Verificar que todas las claves tienen traducción inglesa"""
        for key, translations in TRANSLATIONS.items():
            assert "en" in translations, f"Missing English translation for: {key}"
            assert translations["en"], f"Empty English translation for: {key}"

    def test_critical_keys_exist(self):
        """Verificar que claves críticas existen"""
        critical_keys = [
            "app_title",
            "app_subtitle",
            "knowledge_base",
            "emergency_detected",
            "emergency_protocol",
            "disclaimer_educational",
            "disclaimer_emergency",
            "conditions",
            "medications",
            "search_kb",
            "user_professional",
            "user_educational",
            "differential_diagnosis",
            "clear_history",
        ]

        for key in critical_keys:
            assert key in TRANSLATIONS, f"Critical key missing: {key}"


class TestUITranslations:
    """Tests para traducciones específicas de la UI"""

    def test_emergency_translations(self):
        """Verificar traducciones de emergencia"""
        set_language("es")
        assert "EMERGENCIA" in t("emergency_detected")

        set_language("en")
        assert "EMERGENCY" in t("emergency_detected")

    def test_user_type_translations(self):
        """Verificar traducciones de tipos de usuario"""
        set_language("es")
        assert "Profesional" in t("user_professional")
        assert "Educativo" in t("user_educational")

        set_language("en")
        assert "Professional" in t("user_professional")
        assert "Educational" in t("user_educational")

    def test_medication_field_translations(self):
        """Verificar traducciones de campos de medicamentos"""
        med_keys = [
            "mechanism",
            "indications",
            "contraindications",
            "adverse_effects",
            "interactions",
            "dosing",
            "monitoring",
        ]

        for key in med_keys:
            set_language("es")
            es_val = t(key)
            assert es_val != f"[{key}]", f"Missing Spanish for {key}"

            set_language("en")
            en_val = t(key)
            assert en_val != f"[{key}]", f"Missing English for {key}"


class TestLanguageEnum:
    """Tests para el enum Language"""

    def test_language_values(self):
        """Verificar valores del enum"""
        assert Language.ES.value == "es"
        assert Language.EN.value == "en"

    def test_language_members(self):
        """Verificar miembros del enum"""
        members = list(Language)
        assert len(members) == 2
        assert Language.ES in members
        assert Language.EN in members


class TestTranslationConsistency:
    """Tests para consistencia de traducciones"""

    def test_translations_not_identical(self):
        """Verificar que traducciones ES/EN son diferentes para claves principales"""
        different_expected = [
            "app_title",
            "app_subtitle",
            "knowledge_base",
            "conditions",
            "medications",
            "emergency_detected",
        ]

        for key in different_expected:
            es = TRANSLATIONS[key]["es"]
            en = TRANSLATIONS[key]["en"]
            assert es != en, f"ES and EN should differ for: {key}"

    def test_translation_length_reasonable(self):
        """Verificar que traducciones no están vacías o excesivamente largas"""
        for key, translations in TRANSLATIONS.items():
            for lang, text in translations.items():
                assert len(text) > 0, f"Empty translation: {key}/{lang}"
                assert len(text) < 2000, f"Excessively long translation: {key}/{lang}"


# Cleanup después de tests
@pytest.fixture(autouse=True)
def reset_language():
    """Resetear idioma a español después de cada test"""
    yield
    set_language("es")
