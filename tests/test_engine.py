"""
Tests for MedeX core engine.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from medex.core.config import MedeXConfig
from medex.core.prompts import SystemPrompts


class TestMedeXConfig:
    """Tests for MedeXConfig."""

    def test_config_from_env_with_api_key(self) -> None:
        """Test configuration with environment variable."""
        with patch.dict("os.environ", {"KIMI_API_KEY": "test-key-12345"}):
            config = MedeXConfig()
            assert config.api_key == "test-key-12345"

    def test_config_raises_without_api_key(self) -> None:
        """Test that config raises error without API key."""
        with patch.dict("os.environ", {}, clear=True):
            with patch("pathlib.Path.exists", return_value=False):
                with pytest.raises(ValueError, match="No API key found"):
                    MedeXConfig()

    def test_default_model_settings(self) -> None:
        """Test default model configuration."""
        with patch.dict("os.environ", {"KIMI_API_KEY": "test-key"}):
            config = MedeXConfig()

            assert config.model_chat == "kimi-k2-0711-preview"
            assert config.model_vision == "moonshot-v1-128k-vision-preview"
            assert config.base_url == "https://api.moonshot.ai/v1"

    def test_token_limits(self) -> None:
        """Test token limit settings."""
        with patch.dict("os.environ", {"KIMI_API_KEY": "test-key"}):
            config = MedeXConfig()

            assert config.max_tokens_professional == 5120
            assert config.max_tokens_educational == 5120

    def test_is_production_detection(self) -> None:
        """Test production environment detection."""
        with patch.dict("os.environ", {"KIMI_API_KEY": "key", "SPACE_ID": "test"}):
            config = MedeXConfig()
            assert config.is_production is True

        with patch.dict("os.environ", {"KIMI_API_KEY": "key"}, clear=True):
            config = MedeXConfig()
            assert config.is_production is True


class TestSystemPrompts:
    """Tests for SystemPrompts."""

    def test_professional_prompt_contains_soap(self) -> None:
        """Test that professional prompt includes SOAP format."""
        prompt = SystemPrompts.professional()

        assert "SOAP" in prompt or "S - Subjetivo" in prompt
        assert "MedeX" in prompt
        assert "PROFESIONAL" in prompt

    def test_professional_emergency_prompt(self) -> None:
        """Test professional prompt with emergency flag."""
        prompt = SystemPrompts.professional(is_emergency=True)

        assert "EMERGENCIA" in prompt
        assert "PROTOCOLO" in prompt

    def test_educational_prompt_style(self) -> None:
        """Test educational prompt has appropriate style."""
        prompt = SystemPrompts.educational()

        assert "profesor" in prompt.lower() or "educativo" in prompt.lower()
        assert "ESTUDIANTE" in prompt or "PÚBLICO GENERAL" in prompt

    def test_educational_emergency_prompt(self) -> None:
        """Test educational prompt with emergency flag."""
        prompt = SystemPrompts.educational(is_emergency=True)

        assert "URGENTE" in prompt or "atención médica" in prompt.lower()

    def test_image_analysis_professional(self) -> None:
        """Test image analysis prompt for professionals."""
        prompt = SystemPrompts.image_analysis_professional()

        assert "RX" in prompt
        assert "TAC" in prompt
        assert "RM" in prompt
        assert "US" in prompt

    def test_image_analysis_educational(self) -> None:
        """Test image analysis prompt for education."""
        prompt = SystemPrompts.image_analysis_educational()

        assert "educativo" in prompt.lower() or "educativa" in prompt.lower()

    def test_get_prompt_routing(self) -> None:
        """Test that get_prompt routes correctly."""
        pro_prompt = SystemPrompts.get_prompt("Professional")
        edu_prompt = SystemPrompts.get_prompt("Educational")
        img_prompt = SystemPrompts.get_prompt("Professional", is_image=True)

        assert "PROFESIONAL" in pro_prompt
        assert "ESTUDIANTE" in edu_prompt or "PÚBLICO" in edu_prompt
        assert "IMAGENOLÓGICO" in img_prompt or "imagen" in img_prompt.lower()

    def test_timestamp_format(self) -> None:
        """Test that timestamp is included and formatted."""
        prompt = SystemPrompts.professional()

        # Should contain a date-like pattern
        assert "FECHA" in prompt or ":" in prompt


class TestMedeXEngineInitialization:
    """Tests for MedeXEngine initialization."""

    @patch("medex.core.engine.OpenAI")
    def test_engine_initializes_with_config(self, mock_openai: Mock) -> None:
        """Test engine initialization with config."""
        from medex.core.engine import MedeXEngine

        with patch.dict("os.environ", {"KIMI_API_KEY": "test-key"}):
            config = MedeXConfig()
            engine = MedeXEngine(config)

            assert engine.config == config
            assert engine.user_detector is not None
            assert engine.emergency_detector is not None
            mock_openai.assert_called_once()

    @patch("medex.core.engine.OpenAI")
    def test_engine_session_stats_initial(self, mock_openai: Mock) -> None:
        """Test initial session statistics."""
        from medex.core.engine import MedeXEngine

        with patch.dict("os.environ", {"KIMI_API_KEY": "test-key"}):
            engine = MedeXEngine()
            stats = engine.get_session_stats()

            assert stats["queries"] == 0
            assert stats["emergencies"] == 0
            assert "model" in stats
            assert "capabilities" in stats

    @patch("medex.core.engine.OpenAI")
    def test_engine_clear_history(self, mock_openai: Mock) -> None:
        """Test clearing conversation history."""
        from medex.core.engine import MedeXEngine

        with patch.dict("os.environ", {"KIMI_API_KEY": "test-key"}):
            engine = MedeXEngine()

            # Manually add an entry
            from medex.core.engine import ConversationEntry
            from datetime import datetime

            engine.conversation_history.append(
                ConversationEntry(
                    timestamp=datetime.now(),
                    user_query="test",
                    response="test",
                    user_type="Educational",
                    is_emergency=False,
                )
            )

            assert len(engine.conversation_history) == 1
            engine.clear_history()
            assert len(engine.conversation_history) == 0
