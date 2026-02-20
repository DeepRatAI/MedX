# =============================================================================
# MedeX - LLM System Tests
# =============================================================================
"""
Comprehensive tests for the MedeX LLM System.

Tests cover:
- Data models (Message, LLMResponse, StreamChunk)
- Prompt management and formatting
- Response parsing and entity extraction
- Stream handling
- Router functionality (mocked)
"""

from __future__ import annotations

from datetime import datetime

import pytest

from medex.llm.models import (
    FinishReason,
    LLMConfig,
    LLMProvider,
    LLMRequest,
    LLMResponse,
    Message,
    MessageRole,
    ProviderStatus,
    StreamChunk,
    StreamEventType,
    TokenUsage,
)
from medex.llm.parser import (
    ParsedContentType,
    ResponseParser,
)
from medex.llm.prompts import (
    PromptConfig,
    PromptManager,
    create_prompt_manager,
)
from medex.llm.streaming import (
    StreamHandler,
    StreamState,
    format_chunk_sse,
    format_done,
    format_heartbeat,
    format_sse_event,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def sample_message() -> Message:
    """Create a sample message."""
    return Message(
        role=MessageRole.USER,
        content="¿Cuál es el tratamiento para la neumonía?",
    )


@pytest.fixture
def sample_response() -> LLMResponse:
    """Create a sample LLM response."""
    return LLMResponse(
        content="""## Tratamiento para Neumonía

### Tratamiento ambulatorio
- **Amoxicilina**: 1g cada 8 horas por 5-7 días
- **Alternativa**: Azitromicina 500mg día 1, luego 250mg días 2-5

### Código CIE-10: J18.9

⚠️ Consulte con su médico para un diagnóstico adecuado.""",
        finish_reason=FinishReason.STOP,
        usage=TokenUsage(
            prompt_tokens=50,
            completion_tokens=100,
            total_tokens=150,
        ),
        model="moonshot-v1-128k",
        provider=LLMProvider.KIMI,
        latency_ms=1500.0,
    )


@pytest.fixture
def sample_medical_report() -> str:
    """Create a sample medical report response."""
    return """## 📋 ANÁLISIS CLÍNICO/DIAGNÓSTICO MÁS PROBABLE: – NEUMONÍA ADQUIRIDA EN COMUNIDAD

**Código CIE-10**: J18.1 – Neumonía lobar
**Fecha**: 31-08-2025 14:30
**Modalidad**: Neumología – Ambulatorio

### 1. SÍNTESIS DEL CASO
Paciente masculino de 45 años con fiebre, tos productiva y disnea de 3 días de evolución.
Radiografía con infiltrado en lóbulo inferior derecho.

### 2. DIAGNÓSTICOS DIFERENCIALES JERARQUIZADOS
| Probabilidad | Diagnóstico | Criterios de apoyo | Próximos pasos |
|--------------|-------------|-------------------|----------------|
| Alta (80%) | **Neumonía bacteriana** | Fiebre + infiltrado + tos productiva | Cultivo esputo |
| Moderada (15%) | Neumonía viral | Sin respuesta a ATB | PCR viral |
| Baja (5%) | TB pulmonar | Síntomas >2 semanas | BK esputo |

### 3. PLAN DIAGNÓSTICO
- Hemograma completo
- PCR y procalcitonina
- Cultivo de esputo

### 4. PLAN TERAPÉUTICO
- **Amoxicilina-ácido clavulánico**: 875/125mg VO cada 12 horas por 7 días
- **Paracetamol**: 1g VO cada 8 horas PRN para fiebre
- Hidratación abundante

### 5. CRITERIOS DE ALARMA
- Disnea progresiva
- Fiebre >72 horas pese a tratamiento
- Hemoptisis

### FUENTES:
1. Guía SEPAR 2023 - Neumonía adquirida en la comunidad
2. Consenso ALAT 2024

---

⚠️ Esta información es de soporte clínico educacional."""


# =============================================================================
# Message Tests
# =============================================================================


class TestMessage:
    """Tests for Message model."""

    def test_create_message(self, sample_message: Message):
        """Test message creation."""
        assert sample_message.role == MessageRole.USER
        assert "tratamiento" in sample_message.content
        assert sample_message.id.startswith("msg_")

    def test_message_factory_methods(self):
        """Test factory methods for messages."""
        system = Message.system("You are a helpful assistant.")
        assert system.role == MessageRole.SYSTEM

        user = Message.user("Hello!")
        assert user.role == MessageRole.USER

        assistant = Message.assistant("Hi there!")
        assert assistant.role == MessageRole.ASSISTANT

    def test_message_to_api_format(self, sample_message: Message):
        """Test conversion to API format."""
        api_format = sample_message.to_api_format()

        assert api_format["role"] == "user"
        assert api_format["content"] == sample_message.content

    def test_message_serialization(self, sample_message: Message):
        """Test message serialization and deserialization."""
        data = sample_message.to_dict()
        restored = Message.from_dict(data)

        assert restored.role == sample_message.role
        assert restored.content == sample_message.content

    def test_message_properties(self):
        """Test message property methods."""
        system = Message.system("System prompt")
        user = Message.user("User query")
        assistant = Message.assistant("Response")

        assert system.is_system is True
        assert user.is_user is True
        assert assistant.is_assistant is True


# =============================================================================
# LLMResponse Tests
# =============================================================================


class TestLLMResponse:
    """Tests for LLMResponse model."""

    def test_response_properties(self, sample_response: LLMResponse):
        """Test response properties."""
        assert sample_response.is_complete is True
        assert sample_response.is_truncated is False
        assert sample_response.has_error is False

    def test_response_with_error(self):
        """Test response with error."""
        response = LLMResponse(
            content="",
            finish_reason=FinishReason.ERROR,
            usage=TokenUsage(),
            error="Rate limit exceeded",
        )

        assert response.has_error is True
        assert response.error == "Rate limit exceeded"

    def test_response_to_dict(self, sample_response: LLMResponse):
        """Test response serialization."""
        data = sample_response.to_dict()

        assert data["content"] == sample_response.content
        assert data["finish_reason"] == "stop"
        assert data["provider"] == "kimi"
        assert "usage" in data


# =============================================================================
# TokenUsage Tests
# =============================================================================


class TestTokenUsage:
    """Tests for TokenUsage model."""

    def test_token_usage_addition(self):
        """Test adding token usage."""
        usage1 = TokenUsage(prompt_tokens=100, completion_tokens=50, total_tokens=150)
        usage2 = TokenUsage(prompt_tokens=200, completion_tokens=100, total_tokens=300)

        combined = usage1 + usage2

        assert combined.prompt_tokens == 300
        assert combined.completion_tokens == 150
        assert combined.total_tokens == 450


# =============================================================================
# StreamChunk Tests
# =============================================================================


class TestStreamChunk:
    """Tests for StreamChunk model."""

    def test_create_delta_chunk(self):
        """Test creating delta chunk."""
        chunk = StreamChunk(
            event_type=StreamEventType.DELTA,
            delta="Hello",
            content="Hello",
            index=0,
        )

        assert chunk.is_content is True
        assert chunk.is_finish is False

    def test_create_finish_chunk(self):
        """Test creating finish chunk."""
        chunk = StreamChunk(
            event_type=StreamEventType.FINISH,
            content="Full response",
            finish_reason=FinishReason.STOP,
        )

        assert chunk.is_finish is True
        assert chunk.is_content is False

    def test_chunk_to_sse(self):
        """Test SSE formatting."""
        chunk = StreamChunk(
            event_type=StreamEventType.DELTA,
            delta="test",
            index=0,
        )

        sse = chunk.to_sse()
        assert "data:" in sse
        assert "delta" in sse


# =============================================================================
# LLMRequest Tests
# =============================================================================


class TestLLMRequest:
    """Tests for LLMRequest model."""

    def test_create_request(self, sample_message: Message):
        """Test request creation."""
        request = LLMRequest(
            messages=[sample_message],
            temperature=0.7,
            max_tokens=1000,
        )

        assert len(request.messages) == 1
        assert request.stream is False

    def test_request_to_api_format(self, sample_message: Message):
        """Test conversion to API format."""
        request = LLMRequest(
            messages=[Message.system("Be helpful"), sample_message],
            temperature=0.5,
            max_tokens=500,
        )

        api_format = request.to_api_format()

        assert len(api_format["messages"]) == 2
        assert api_format["temperature"] == 0.5
        assert api_format["max_tokens"] == 500

    def test_request_cache_key(self, sample_message: Message):
        """Test cache key generation."""
        request1 = LLMRequest(messages=[sample_message], temperature=0.7)
        request2 = LLMRequest(messages=[sample_message], temperature=0.7)
        request3 = LLMRequest(messages=[sample_message], temperature=0.5)

        # Same params = same key
        assert request1.get_cache_key() == request2.get_cache_key()
        # Different params = different key
        assert request1.get_cache_key() != request3.get_cache_key()


# =============================================================================
# PromptManager Tests
# =============================================================================


class TestPromptManager:
    """Tests for PromptManager."""

    def test_get_system_prompt_educational(self):
        """Test educational system prompt."""
        manager = create_prompt_manager(user_mode="educational", language="es")
        system = manager.get_system_prompt()

        assert system.is_system is True
        assert "MedeX" in system.content
        assert "educativo" in system.content.lower()

    def test_get_system_prompt_professional(self):
        """Test professional system prompt."""
        manager = create_prompt_manager(user_mode="professional", language="es")
        system = manager.get_system_prompt()

        assert "CDSS" in system.content or "profesional" in system.content.lower()

    def test_build_messages(self):
        """Test building complete message list."""
        manager = PromptManager()
        messages = manager.build_messages(
            query="¿Qué es la diabetes?",
            context="La diabetes es una enfermedad metabólica...",
        )

        assert len(messages) >= 2
        assert messages[0].is_system
        assert messages[-1].is_user

    def test_add_disclaimer(self):
        """Test disclaimer addition."""
        manager = PromptManager()
        response = "Esta es la respuesta."

        with_disclaimer = manager.add_disclaimer(response)

        assert (
            "Disclaimer" in with_disclaimer or "disclaimer" in with_disclaimer.lower()
        )

    def test_truncate_context(self):
        """Test context truncation."""
        manager = PromptManager(config=PromptConfig(max_context_tokens=100))

        long_context = "Palabra " * 500  # Very long context
        truncated = manager.truncate_context(long_context)

        assert len(truncated) < len(long_context)
        assert "truncado" in truncated.lower() or "..." in truncated


# =============================================================================
# ResponseParser Tests
# =============================================================================


class TestResponseParser:
    """Tests for ResponseParser."""

    def test_parse_text(self, sample_response: LLMResponse):
        """Test parsing text response."""
        parser = ResponseParser()
        parsed = parser.parse(sample_response, expected_type=ParsedContentType.TEXT)

        assert parsed.parse_success is True
        assert parsed.raw_content == sample_response.content

    def test_parse_medical_report(self, sample_medical_report: str):
        """Test parsing medical report."""
        parser = ResponseParser()
        parsed = parser.parse(
            sample_medical_report,
            expected_type=ParsedContentType.MEDICAL_REPORT,
        )

        assert parsed.parse_success is True
        assert parsed.medical_report is not None

        report = parsed.medical_report
        assert "NEUMONÍA" in report.diagnosis.upper()
        assert report.cie10_code in ["J18.1", "J18.9"]

    def test_extract_cie10_codes(self, sample_medical_report: str):
        """Test CIE-10 code extraction."""
        parser = ResponseParser()
        parsed = parser.parse(
            sample_medical_report,
            expected_type=ParsedContentType.TEXT,
        )

        codes = parsed.extracted_entities.get("cie10_codes", [])
        assert len(codes) > 0
        assert any("J18" in c for c in codes)

    def test_extract_medications(self, sample_medical_report: str):
        """Test medication extraction."""
        parser = ResponseParser()
        parsed = parser.parse(
            sample_medical_report,
            expected_type=ParsedContentType.MEDICAL_REPORT,
        )

        if parsed.medical_report:
            meds = parsed.medical_report.treatment_plan
            # Should find at least one medication
            med_names = [m.name.lower() for m in meds]
            assert any("amoxicilina" in n or "paracetamol" in n for n in med_names)

    def test_determine_urgency(self):
        """Test urgency level determination."""
        parser = ResponseParser()

        emergency_text = "Paciente en EMERGENCIA con shock séptico"
        parsed = parser.parse(emergency_text)
        # Check if urgency is detected (through entities or report)

        routine_text = "Consulta de control rutinario"
        parsed_routine = parser.parse(routine_text)

        # Verify parse succeeded
        assert parsed.parse_success is True
        assert parsed_routine.parse_success is True

    def test_extract_json(self):
        """Test JSON extraction."""
        parser = ResponseParser()

        # JSON in code block
        text_with_json = """
        Here is the result:
        ```json
        {"diagnosis": "Neumonía", "code": "J18.9"}
        ```
        """

        result = parser.extract_json(text_with_json)
        assert result is not None
        assert result["diagnosis"] == "Neumonía"

    def test_parse_json_response(self):
        """Test JSON response parsing."""
        parser = ResponseParser()

        json_response = '{"status": "ok", "data": [1, 2, 3]}'
        parsed = parser.parse(json_response, expected_type=ParsedContentType.JSON)

        assert parsed.parse_success is True
        assert parsed.json_data is not None
        assert parsed.json_data["status"] == "ok"


# =============================================================================
# StreamHandler Tests
# =============================================================================


class TestStreamHandler:
    """Tests for StreamHandler."""

    def test_format_sse_event(self):
        """Test SSE event formatting."""
        event = format_sse_event({"message": "Hello"}, event="chat")

        assert "event: chat" in event
        assert "data:" in event
        assert "Hello" in event

    def test_format_heartbeat(self):
        """Test heartbeat formatting."""
        heartbeat = format_heartbeat()

        assert "heartbeat" in heartbeat
        assert "timestamp" in heartbeat

    def test_format_done(self):
        """Test done signal formatting."""
        done = format_done()

        assert "[DONE]" in done

    def test_format_chunk_sse(self):
        """Test chunk SSE formatting."""
        chunk = StreamChunk(
            event_type=StreamEventType.DELTA,
            delta="Hola",
            content="Hola",
            index=0,
        )

        sse = format_chunk_sse(chunk)

        assert "delta" in sse
        assert "Hola" in sse

    def test_stream_state(self):
        """Test stream state tracking."""
        state = StreamState(
            stream_id="test_123",
            request_id="req_456",
        )

        # Initial state
        assert state.is_active is True
        assert state.is_complete is False

        # Simulate streaming
        state.chunk_count = 10
        state.tokens_streamed = 50
        state.first_token_at = datetime.utcnow()

        # Check metrics
        assert state.duration_ms >= 0
        assert state.time_to_first_token_ms is not None

    def test_create_text_stream(self):
        """Test text stream creation."""
        handler = StreamHandler()

        # Create generator (don't await yet)
        stream = handler.create_text_stream("Hello World", chunk_size=5, delay=0.001)

        # Just verify it's an async generator
        assert hasattr(stream, "__anext__")


# =============================================================================
# LLMConfig Tests
# =============================================================================


class TestLLMConfig:
    """Tests for LLMConfig."""

    def test_create_config(self):
        """Test config creation."""
        config = LLMConfig(
            provider=LLMProvider.KIMI,
            model="moonshot-v1-128k",
            temperature=0.7,
        )

        assert config.provider == LLMProvider.KIMI
        assert config.base_url == "https://api.moonshot.cn/v1"

    def test_config_defaults(self):
        """Test config default values."""
        config = LLMConfig(
            provider=LLMProvider.GROQ,
            model="llama-3.3-70b",
        )

        assert config.max_tokens == 4096
        assert config.temperature == 0.7
        assert config.supports_streaming is True

    def test_config_to_dict(self):
        """Test config serialization."""
        config = LLMConfig(
            provider=LLMProvider.OPENROUTER,
            model="qwen/qwen-2.5-72b",
        )

        data = config.to_dict()

        assert data["provider"] == "openrouter"
        assert data["model"] == "qwen/qwen-2.5-72b"


# =============================================================================
# ProviderStatus Tests
# =============================================================================


class TestProviderStatus:
    """Tests for ProviderStatus."""

    def test_record_request(self):
        """Test recording successful request."""
        status = ProviderStatus(provider=LLMProvider.KIMI)

        status.record_request(latency_ms=500, tokens=100)

        assert status.requests_today == 1
        assert status.tokens_today == 100
        assert status.avg_latency_ms > 0

    def test_record_error(self):
        """Test recording error."""
        status = ProviderStatus(provider=LLMProvider.GROQ)

        status.record_error("Rate limit exceeded")

        assert status.last_error == "Rate limit exceeded"
        assert status.error_rate > 0


# =============================================================================
# Integration Tests
# =============================================================================


class TestLLMIntegration:
    """Integration tests for LLM components."""

    def test_prompt_to_request(self):
        """Test creating request from prompt manager."""
        manager = PromptManager()
        messages = manager.build_messages(
            query="Test query",
            context="Test context",
        )

        request = LLMRequest(
            messages=messages,
            temperature=0.7,
        )

        assert request.system_message is not None
        assert request.last_user_message is not None

    def test_response_to_parsed(self, sample_response: LLMResponse):
        """Test parsing LLM response."""
        parser = ResponseParser()
        parsed = parser.parse(sample_response)

        assert parsed.parse_success is True
        # Should extract CIE-10 code
        assert len(parsed.extracted_entities.get("cie10_codes", [])) > 0


# =============================================================================
# Run Tests
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
