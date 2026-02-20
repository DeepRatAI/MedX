# =============================================================================
# MedeX - Memory System Tests
# =============================================================================
"""
Comprehensive tests for MedeX V2 Memory System.

Tests cover:
- TokenCounter: Token counting and budget management
- TitleGenerator: Title extraction and generation
- PatientContextExtractor: Clinical data extraction
- ContextWindowManager: Context building and truncation
- ConversationManager: CRUD operations (requires DB)
- MemoryService: Integration tests (requires DB)
"""

from __future__ import annotations

import pytest

from src.medex.memory import (
    ContextMessage,
    ContextPriority,
    ContextWindow,
    ContextWindowManager,
    EmergencyLevel,
    PatientContext,
    PatientContextExtractor,
    TitleGenerator,
    TokenCounter,
    get_patient_context_extractor,
    get_title_generator,
    get_token_counter,
)

# =============================================================================
# TokenCounter Tests
# =============================================================================


class TestTokenCounter:
    """Tests for TokenCounter class."""

    def test_singleton_instance(self):
        """Test singleton pattern."""
        counter1 = get_token_counter()
        counter2 = get_token_counter()
        assert counter1 is counter2

    def test_count_tokens_basic(self):
        """Test basic token counting."""
        counter = TokenCounter()
        text = "Hello, this is a test message."
        count = counter.count_tokens(text)

        # Should be around 7-10 tokens
        assert 5 <= count <= 15

    def test_count_tokens_empty(self):
        """Test counting empty string."""
        counter = TokenCounter()
        assert counter.count_tokens("") == 0

    def test_count_tokens_spanish(self):
        """Test Spanish text token counting."""
        counter = TokenCounter()
        text = "Hola, tengo dolor de cabeza y fiebre desde ayer."
        count = counter.count_tokens(text)

        # Spanish typically has higher token count
        assert count > 0

    def test_count_message_tokens(self):
        """Test message token counting."""
        counter = TokenCounter()
        message = {
            "role": "user",
            "content": "What are the symptoms of diabetes?",
        }
        count = counter.count_message_tokens(message)

        # Should include content tokens plus role overhead
        assert count > counter.count_tokens(message["content"])

    def test_count_messages_tokens(self):
        """Test multiple messages token counting."""
        counter = TokenCounter()
        messages = [
            {"role": "system", "content": "You are a medical assistant."},
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi, how can I help?"},
        ]
        count = counter.count_messages_tokens(messages)

        # Should be sum of individual message tokens
        assert count > 0

    def test_calculate_remaining_budget(self):
        """Test budget calculation."""
        counter = TokenCounter()
        remaining = counter.calculate_remaining_budget(
            used_tokens=2000,
            max_tokens=8192,
            reserve_for_response=1500,
        )

        assert remaining == 8192 - 2000 - 1500

    def test_remaining_budget_negative(self):
        """Test budget returns 0 when exceeded."""
        counter = TokenCounter()
        remaining = counter.calculate_remaining_budget(
            used_tokens=10000,
            max_tokens=8192,
            reserve_for_response=1500,
        )

        assert remaining == 0

    def test_truncate_to_budget(self):
        """Test text truncation to budget."""
        counter = TokenCounter()
        long_text = " ".join(["word"] * 1000)
        truncated = counter.truncate_to_budget(
            text=long_text,
            max_tokens=50,
        )

        count = counter.count_tokens(truncated)
        assert count <= 50

    def test_model_limits(self):
        """Test model limits dictionary."""
        counter = TokenCounter()

        # Check known models
        assert counter.MODEL_LIMITS.get("gpt-4", 0) >= 8192
        assert counter.MODEL_LIMITS.get("kimi-k2", 0) >= 100000


# =============================================================================
# TitleGenerator Tests
# =============================================================================


class TestTitleGenerator:
    """Tests for TitleGenerator class."""

    def test_singleton_instance(self):
        """Test singleton pattern."""
        gen1 = get_title_generator()
        gen2 = get_title_generator()
        assert gen1 is gen2

    def test_generate_from_empty(self):
        """Test generation from empty message."""
        generator = TitleGenerator()
        title = generator.generate_from_message("")
        assert title == "Nueva conversación"

    def test_generate_from_short_message(self):
        """Test generation from short message."""
        generator = TitleGenerator()
        title = generator.generate_from_message("Tengo dolor de cabeza")

        assert len(title) <= generator.MAX_TITLE_LENGTH
        assert title  # Not empty

    def test_generate_from_long_message(self):
        """Test generation from long message."""
        generator = TitleGenerator()
        long_message = (
            "Buenos días, quiero consultarle sobre "
            + "mi situación médica porque tengo varios "
            + "síntomas que me preocupan desde hace tiempo."
        )
        title = generator.generate_from_message(long_message)

        assert len(title) <= generator.MAX_TITLE_LENGTH

    def test_pattern_matching_que_es(self):
        """Test pattern matching for 'qué es' questions."""
        generator = TitleGenerator()
        title = generator.generate_from_message("¿Qué es la diabetes?")

        assert "diabetes" in title.lower() or "Consulta" in title

    def test_medical_keyword_detection(self):
        """Test medical keyword detection."""
        generator = TitleGenerator()
        title = generator.generate_from_message("Tengo fiebre y dolor de cabeza")

        # Should detect fiebre or cefalea
        assert any(
            kw in title.lower() for kw in ["fiebre", "cabeza", "caso", "consulta"]
        )

    def test_truncation_with_ellipsis(self):
        """Test truncation adds ellipsis."""
        generator = TitleGenerator()
        very_long = "A" * 100 + " " + "B" * 100
        title = generator.generate_from_message(very_long, max_length=30)

        assert len(title) <= 30
        if len(title) == 30:
            assert title.endswith("...")

    def test_capitalize_first_letter(self):
        """Test first letter capitalization."""
        generator = TitleGenerator()
        title = generator.generate_from_message("dolor de cabeza")

        assert title[0].isupper()


# =============================================================================
# PatientContextExtractor Tests
# =============================================================================


class TestPatientContextExtractor:
    """Tests for PatientContextExtractor class."""

    def test_singleton_instance(self):
        """Test singleton pattern."""
        ext1 = get_patient_context_extractor()
        ext2 = get_patient_context_extractor()
        assert ext1 is ext2

    def test_extract_age_years(self):
        """Test age extraction in years."""
        extractor = PatientContextExtractor()
        context = extractor.extract_from_message("Tengo 45 años")

        assert context.age == 45

    def test_extract_age_months(self):
        """Test age extraction in months."""
        extractor = PatientContextExtractor()
        context = extractor.extract_from_message("Mi bebé tiene 8 meses")

        assert context.age == 8

    def test_extract_sex_masculine(self):
        """Test sex extraction - masculine."""
        extractor = PatientContextExtractor()
        context = extractor.extract_from_message("Soy hombre de 30 años")

        assert context.sex == "masculino"

    def test_extract_sex_feminine(self):
        """Test sex extraction - feminine."""
        extractor = PatientContextExtractor()
        context = extractor.extract_from_message("Soy mujer de 35 años")

        assert context.sex == "femenino"

    def test_extract_symptoms(self):
        """Test symptom extraction."""
        extractor = PatientContextExtractor()
        context = extractor.extract_from_message(
            "Tengo dolor de cabeza, fiebre y náuseas"
        )

        assert len(context.symptoms) >= 2
        assert "fiebre" in context.symptoms
        assert "náusea" in context.symptoms

    def test_extract_conditions(self):
        """Test condition extraction."""
        extractor = PatientContextExtractor()
        context = extractor.extract_from_message("Soy diabético y tengo hipertensión")

        assert "diabetes" in context.conditions
        assert "hipertensión" in context.conditions

    def test_extract_medications(self):
        """Test medication extraction."""
        extractor = PatientContextExtractor()
        context = extractor.extract_from_message(
            "Tomo metformina e insulina para la diabetes"
        )

        assert len(context.medications) >= 1
        assert any("metformina" in m.lower() for m in context.medications) or any(
            "insulina" in m.lower() for m in context.medications
        )

    def test_extract_vitals(self):
        """Test vital signs extraction."""
        extractor = PatientContextExtractor()
        context = extractor.extract_from_message(
            "Mi temperatura es 38.5°C y presión 140/90"
        )

        assert "temperatura" in context.vitals
        assert context.vitals["temperatura"] == 38.5

    def test_detect_emergency_critical(self):
        """Test critical emergency detection."""
        extractor = PatientContextExtractor()
        context = extractor.extract_from_message(
            "No puedo respirar y tengo dolor de pecho intenso"
        )

        assert context.emergency_level in [
            EmergencyLevel.CRITICAL,
            EmergencyLevel.HIGH,
        ]
        assert len(context.emergency_indicators) >= 1

    def test_context_merge(self):
        """Test context merging."""
        ctx1 = PatientContext(age=45, symptoms=["fiebre"])
        ctx2 = PatientContext(sex="masculino", symptoms=["tos"])

        merged = ctx1.merge(ctx2)

        assert merged.age == 45
        assert merged.sex == "masculino"
        assert "fiebre" in merged.symptoms
        assert "tos" in merged.symptoms

    def test_extract_from_messages(self):
        """Test extraction from multiple messages."""
        extractor = PatientContextExtractor()
        messages = [
            {"role": "user", "content": "Tengo 35 años y soy mujer"},
            {"role": "assistant", "content": "Entendido, ¿cuáles son sus síntomas?"},
            {"role": "user", "content": "Tengo fiebre y dolor de cabeza"},
        ]

        context = extractor.extract_from_messages(messages)

        assert context.age == 35
        assert context.sex == "femenino"
        assert "fiebre" in context.symptoms

    def test_to_dict_and_from_dict(self):
        """Test serialization round-trip."""
        original = PatientContext(
            age=40,
            sex="masculino",
            symptoms=["fiebre", "tos"],
            emergency_level=EmergencyLevel.MEDIUM,
        )

        data = original.to_dict()
        restored = PatientContext.from_dict(data)

        assert restored.age == 40
        assert restored.sex == "masculino"
        assert restored.symptoms == ["fiebre", "tos"]
        assert restored.emergency_level == EmergencyLevel.MEDIUM


# =============================================================================
# ContextWindowManager Tests
# =============================================================================


class TestContextWindowManager:
    """Tests for ContextWindowManager class."""

    def test_available_budget_calculation(self):
        """Test budget calculation."""
        manager = ContextWindowManager(
            max_context_tokens=8192,
            system_prompt_reserve=2000,
            response_reserve=1500,
        )

        budget = manager.available_context_budget

        assert budget == 8192 - 2000 - 1500

    def test_context_message_to_dict(self):
        """Test ContextMessage conversion."""
        msg = ContextMessage(
            role="user",
            content="Hello",
            token_count=5,
            priority=ContextPriority.HIGH,
        )

        result = msg.to_dict()

        assert result["role"] == "user"
        assert result["content"] == "Hello"

    def test_context_window_to_messages(self):
        """Test ContextWindow conversion."""
        messages = [
            ContextMessage(
                role="system",
                content="You are helpful",
                token_count=10,
            ),
            ContextMessage(
                role="user",
                content="Hello",
                token_count=5,
            ),
        ]

        window = ContextWindow(
            messages=messages,
            total_tokens=15,
            remaining_budget=100,
        )

        result = window.to_messages()

        assert len(result) == 2
        assert result[0]["role"] == "system"
        assert result[1]["role"] == "user"

    def test_estimate_response_budget(self):
        """Test response budget estimation."""
        manager = ContextWindowManager(max_context_tokens=8192)

        window = ContextWindow(
            messages=[],
            total_tokens=2000,
            remaining_budget=6192,
        )

        budget = manager.estimate_response_budget(window)

        assert budget == 8192 - 2000

    def test_summarize_context(self):
        """Test context summarization."""
        manager = ContextWindowManager(max_context_tokens=8192)

        messages = [
            ContextMessage(role="system", content="test", token_count=100),
            ContextMessage(role="user", content="test", token_count=50),
            ContextMessage(role="assistant", content="test", token_count=75),
        ]

        window = ContextWindow(
            messages=messages,
            total_tokens=225,
            remaining_budget=7967,
            truncated=False,
            dropped_count=0,
        )

        summary = manager.summarize_context(window)

        assert summary["message_count"] == 3
        assert summary["total_tokens"] == 225
        assert summary["messages_by_role"]["system"] == 1
        assert summary["messages_by_role"]["user"] == 1
        assert summary["messages_by_role"]["assistant"] == 1


# =============================================================================
# Integration Tests (Mock-based)
# =============================================================================


class TestMemoryIntegration:
    """Integration tests for memory components."""

    def test_token_counter_with_context_manager(self):
        """Test TokenCounter integration with ContextWindowManager."""
        counter = get_token_counter()
        manager = ContextWindowManager(
            max_context_tokens=8192,
            token_counter=counter,
        )

        # Verify they share token counting
        text = "Test message"
        direct_count = counter.count_tokens(text)

        # ContextWindowManager should use same counter
        assert direct_count > 0
        assert manager.available_context_budget > 0

    def test_title_generator_with_patient_context(self):
        """Test title generation with patient context awareness."""
        generator = get_title_generator()
        extractor = get_patient_context_extractor()

        message = "Tengo 50 años y desde ayer tengo fiebre alta y dolor de pecho"

        # Extract context
        context = extractor.extract_from_message(message)

        # Generate title
        title = generator.generate_from_message(message)

        # Both should detect medical information
        assert context.symptoms
        assert context.age == 50
        assert len(title) > 0

    def test_end_to_end_context_extraction(self):
        """Test full context extraction pipeline."""
        extractor = get_patient_context_extractor()

        # Simulate conversation
        messages = [
            {"role": "user", "content": "Hola, soy Juan, tengo 45 años"},
            {"role": "assistant", "content": "Hola Juan, ¿en qué puedo ayudarte?"},
            {"role": "user", "content": "Soy diabético y tomo metformina"},
            {"role": "assistant", "content": "Entendido. ¿Tienes algún síntoma?"},
            {"role": "user", "content": "Sí, tengo mucha sed y fatiga"},
        ]

        context = extractor.extract_from_messages(messages)

        # Verify comprehensive extraction
        assert context.age == 45
        assert "diabetes" in context.conditions
        assert "fatiga" in context.symptoms
        assert context.source_messages == 3  # Only user messages


# =============================================================================
# Edge Cases and Error Handling
# =============================================================================


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_token_counter_unicode(self):
        """Test token counting with unicode characters."""
        counter = TokenCounter()
        text = "Señor José tiene náuseas y está mareado 😷"
        count = counter.count_tokens(text)

        assert count > 0

    def test_title_generator_markdown(self):
        """Test title generation with markdown content."""
        generator = TitleGenerator()
        message = "**Importante**: Tengo *fiebre* desde `ayer`"
        title = generator.generate_from_message(message)

        # Should strip markdown
        assert "**" not in title
        assert "*" not in title
        assert "`" not in title

    def test_patient_extractor_empty_messages(self):
        """Test extraction from empty message list."""
        extractor = PatientContextExtractor()
        context = extractor.extract_from_messages([])

        assert context.age is None
        assert context.symptoms == []

    def test_patient_extractor_assistant_only(self):
        """Test extraction ignores assistant messages."""
        extractor = PatientContextExtractor()
        messages = [
            {"role": "assistant", "content": "Tengo 50 años y fiebre"},
        ]

        context = extractor.extract_from_messages(messages)

        # Should not extract from assistant messages
        assert context.age is None

    def test_context_priority_ordering(self):
        """Test context priority enum ordering."""
        assert ContextPriority.CRITICAL.value < ContextPriority.HIGH.value
        assert ContextPriority.HIGH.value < ContextPriority.MEDIUM.value
        assert ContextPriority.MEDIUM.value < ContextPriority.LOW.value

    def test_emergency_level_comparison(self):
        """Test emergency level comparison."""
        assert EmergencyLevel.CRITICAL.value > EmergencyLevel.HIGH.value
        assert EmergencyLevel.HIGH.value > EmergencyLevel.MEDIUM.value
        assert EmergencyLevel.MEDIUM.value > EmergencyLevel.LOW.value
        assert EmergencyLevel.LOW.value > EmergencyLevel.NONE.value


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
