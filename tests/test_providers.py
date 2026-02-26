# =============================================================================
# MedeX - Providers Module Tests
# =============================================================================
"""
Tests for the MedeX Providers module.

Covers:
- ProviderConfig: creation, API key resolution (env / file / missing)
- ProviderResponse: success property, error handling
- ProviderStatus: enum values
- ModelProvider (ABC): initialization, status management, error classification
- ProviderManager: initialization, provider listing, set_provider
"""

from __future__ import annotations

import os
from collections.abc import Generator
from unittest.mock import patch

import pytest

from medex.providers.base import (
    ModelProvider,
    ProviderConfig,
    ProviderResponse,
    ProviderStatus,
)

# =============================================================================
# ProviderStatus Enum Tests
# =============================================================================


class TestProviderStatus:
    """Tests for ProviderStatus enum."""

    def test_status_values(self):
        """Test all status enum values."""
        assert ProviderStatus.AVAILABLE.value == "available"
        assert ProviderStatus.RATE_LIMITED.value == "rate_limited"
        assert ProviderStatus.QUOTA_EXCEEDED.value == "quota_exceeded"
        assert ProviderStatus.AUTH_ERROR.value == "auth_error"
        assert ProviderStatus.UNAVAILABLE.value == "unavailable"
        assert ProviderStatus.UNKNOWN.value == "unknown"

    def test_status_members(self):
        """Test expected number of status members."""
        members = list(ProviderStatus)
        assert len(members) == 6

    def test_status_distinct_values(self):
        """Test all status values are distinct."""
        values = [s.value for s in ProviderStatus]
        assert len(values) == len(set(values))


# =============================================================================
# ProviderConfig Tests
# =============================================================================


class TestProviderConfig:
    """Tests for ProviderConfig dataclass."""

    def test_create_config(self):
        """Test creating a provider config with required fields."""
        config = ProviderConfig(
            name="openai",
            model_id="gpt-4",
        )

        assert config.name == "openai"
        assert config.model_id == "gpt-4"

    def test_config_defaults(self):
        """Test config defaults are set correctly."""
        config = ProviderConfig(name="test", model_id="m")

        assert config.api_key_env == ""
        assert config.api_key_file == ""
        assert config.base_url == ""
        assert config.max_tokens == 4096
        assert config.temperature == 0.7
        assert config.supports_streaming is True
        assert config.supports_vision is False
        assert config.is_free is False
        assert config.description == ""

    def test_config_with_base_url(self):
        """Test config with custom base URL."""
        config = ProviderConfig(
            name="custom",
            model_id="local-model",
            base_url="http://localhost:8080/v1",
        )

        assert config.base_url == "http://localhost:8080/v1"

    def test_config_with_custom_params(self):
        """Test config with custom temperature and max_tokens."""
        config = ProviderConfig(
            name="huggingface",
            model_id="medex/classifier",
            temperature=0.3,
            max_tokens=1024,
        )

        assert config.temperature == 0.3
        assert config.max_tokens == 1024

    def test_get_api_key_from_env(self):
        """Test getting API key from environment variable."""
        config = ProviderConfig(
            name="openai",
            model_id="gpt-4",
            api_key_env="TEST_MEDEX_API_KEY_PROV",
        )

        with patch.dict(os.environ, {"TEST_MEDEX_API_KEY_PROV": "sk-env-key-123"}):
            key = config.get_api_key()
            assert key == "sk-env-key-123"

    def test_get_api_key_from_file(self, tmp_path):
        """Test getting API key from file."""
        key_file = tmp_path / "api_key.txt"
        key_file.write_text("sk-file-key-456\n")

        config = ProviderConfig(
            name="openai",
            model_id="gpt-4",
            api_key_file=str(key_file),
        )

        key = config.get_api_key()
        assert key == "sk-file-key-456"

    def test_get_api_key_missing(self):
        """Test getting API key when none is configured."""
        config = ProviderConfig(
            name="openai",
            model_id="gpt-4",
        )

        key = config.get_api_key()
        assert key is None

    def test_get_api_key_env_takes_precedence(self, tmp_path):
        """Test env var takes precedence over file."""
        key_file = tmp_path / "api_key.txt"
        key_file.write_text("file-key")

        config = ProviderConfig(
            name="test",
            model_id="m",
            api_key_env="TEST_MEDEX_PRIO_KEY",
            api_key_file=str(key_file),
        )

        with patch.dict(os.environ, {"TEST_MEDEX_PRIO_KEY": "env-key"}):
            key = config.get_api_key()
            assert key == "env-key"

    def test_vision_support_flag(self):
        """Test vision support configuration."""
        config = ProviderConfig(
            name="vision-provider",
            model_id="gpt-4-vision",
            supports_vision=True,
        )

        assert config.supports_vision is True


# =============================================================================
# ProviderResponse Tests
# =============================================================================


class TestProviderResponse:
    """Tests for ProviderResponse dataclass."""

    def test_create_success_response(self):
        """Test creating a successful response."""
        response = ProviderResponse(
            content="Diagnosis: pneumonia",
            model="gpt-4",
            provider="openai",
            tokens_used=150,
        )

        assert response.content == "Diagnosis: pneumonia"
        assert response.model == "gpt-4"
        assert response.provider == "openai"
        assert response.tokens_used == 150
        assert response.success  # truthy: content present and no error

    def test_create_error_response(self):
        """Test creating an error response."""
        response = ProviderResponse(
            content="",
            model="gpt-4",
            provider="openai",
            error="Rate limited",
        )

        assert not response.success
        assert response.error == "Rate limited"

    def test_success_requires_content_and_no_error(self):
        """Test success property requires both content and no error."""
        # Content but no error → success
        ok = ProviderResponse(content="result", model="m", provider="p")
        assert ok.success

        # Error even with content → not success
        err = ProviderResponse(
            content="partial", model="m", provider="p", error="failed"
        )
        assert not err.success

        # No content and no error → falsy
        empty = ProviderResponse(content="", model="m", provider="p")
        assert not empty.success

    def test_response_defaults(self):
        """Test response default values."""
        response = ProviderResponse()

        assert response.content == ""
        assert response.provider == ""
        assert response.model == ""
        assert response.status == ProviderStatus.AVAILABLE
        assert response.tokens_used == 0
        assert response.error is None

    def test_response_with_status(self):
        """Test response with explicit status."""
        response = ProviderResponse(
            content="",
            provider="openai",
            model="gpt-4",
            status=ProviderStatus.RATE_LIMITED,
            error="Too many requests",
        )

        assert response.status == ProviderStatus.RATE_LIMITED


# =============================================================================
# ModelProvider (ABC) Tests
# =============================================================================


class ConcreteProvider(ModelProvider):
    """Concrete implementation for testing abstract base class."""

    def initialize(self) -> bool:
        self._status = ProviderStatus.AVAILABLE
        return True

    def generate(
        self,
        messages: list[dict],
        system_prompt: str = "",
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> ProviderResponse:
        return ProviderResponse(
            content=f"Mock response (messages={len(messages)})",
            model=self.config.model_id,
            provider=self.config.name,
        )

    def stream(
        self,
        messages: list[dict],
        system_prompt: str = "",
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> Generator[str, None, ProviderResponse]:
        yield "chunk1"
        yield "chunk2"
        return ProviderResponse(
            content="chunk1chunk2",
            model=self.config.model_id,
            provider=self.config.name,
        )


class TestModelProvider:
    """Tests for ModelProvider abstract base class."""

    def _make_provider(
        self, name: str = "test", model_id: str = "test-model"
    ) -> ConcreteProvider:
        config = ProviderConfig(name=name, model_id=model_id)
        return ConcreteProvider(config)

    def test_provider_initialization(self):
        """Test provider initializes with config."""
        provider = self._make_provider()

        assert provider.config.name == "test"
        assert provider.config.model_id == "test-model"
        assert provider.status == ProviderStatus.UNKNOWN

    def test_provider_name_property(self):
        """Test provider name property."""
        provider = self._make_provider(name="medex-hf")
        assert provider.name == "medex-hf"

    def test_provider_model_id_property(self):
        """Test provider model_id property."""
        provider = self._make_provider(model_id="gpt-4-turbo")
        assert provider.model_id == "gpt-4-turbo"

    def test_provider_status_after_init(self):
        """Test provider status is UNKNOWN after __init__."""
        provider = self._make_provider()
        assert provider.status == ProviderStatus.UNKNOWN

    def test_provider_initialize(self):
        """Test provider initialize sets status to AVAILABLE."""
        provider = self._make_provider()
        result = provider.initialize()

        assert result is True
        assert provider.status == ProviderStatus.AVAILABLE

    def test_provider_is_available(self):
        """Test is_available property."""
        provider = self._make_provider()
        assert provider.is_available is False  # UNKNOWN initially

        provider.initialize()
        assert provider.is_available is True

    def test_provider_generate(self):
        """Test provider generate method."""
        provider = self._make_provider()
        response = provider.generate(messages=[{"role": "user", "content": "Hello"}])

        assert response.success
        assert "messages=1" in response.content

    def test_update_status_quota_exceeded(self):
        """Test status update on quota error (429)."""
        provider = self._make_provider()
        provider.initialize()

        status = provider._update_status_from_error(
            Exception("Error 429: quota exceeded")
        )
        assert status == ProviderStatus.QUOTA_EXCEEDED
        assert provider.status == ProviderStatus.QUOTA_EXCEEDED

    def test_update_status_auth_error(self):
        """Test status update on auth error (401)."""
        provider = self._make_provider()
        provider.initialize()

        status = provider._update_status_from_error(
            Exception("Error 401: Unauthorized")
        )
        assert status == ProviderStatus.AUTH_ERROR
        assert provider.status == ProviderStatus.AUTH_ERROR

    def test_update_status_rate_limited(self):
        """Test status update on rate limit error."""
        provider = self._make_provider()
        provider.initialize()

        status = provider._update_status_from_error(Exception("Rate limit exceeded"))
        assert status == ProviderStatus.RATE_LIMITED
        assert provider.status == ProviderStatus.RATE_LIMITED

    def test_update_status_server_error(self):
        """Test status update on generic error."""
        provider = self._make_provider()
        provider.initialize()

        status = provider._update_status_from_error(Exception("Internal server error"))
        assert status == ProviderStatus.UNAVAILABLE
        assert provider.status == ProviderStatus.UNAVAILABLE


# =============================================================================
# Provider Manager Tests
# =============================================================================


class TestProviderManager:
    """Tests for ProviderManager."""

    def test_manager_import(self):
        """Test manager can be imported."""
        from medex.providers.manager import ProviderManager

        assert ProviderManager is not None

    def test_manager_initialization(self):
        """Test manager creates with default providers."""
        from medex.providers.manager import ProviderManager

        manager = ProviderManager()
        # Manager auto-configures default providers (Moonshot, HuggingFace, etc.)
        assert manager is not None
        assert manager.auto_fallback is True
        assert manager.primary_provider is not None

    def test_manager_with_primary(self):
        """Test manager with a primary provider."""
        from medex.providers.manager import ProviderManager

        config = ProviderConfig(name="test", model_id="test-model")
        provider = ConcreteProvider(config)

        manager = ProviderManager(primary_provider=provider)
        assert manager.primary_provider is provider

    def test_manager_get_available_providers_default(self):
        """Test listing available providers with default config."""
        from medex.providers.manager import ProviderManager

        manager = ProviderManager()
        available = manager.get_available_providers()
        assert isinstance(available, list)
        # Default manager comes pre-configured with providers
        assert len(available) >= 1

    def test_manager_get_available_providers(self):
        """Test listing available providers with initialized provider."""
        from medex.providers.manager import ProviderManager

        config = ProviderConfig(name="test", model_id="test-model")
        provider = ConcreteProvider(config)
        provider.initialize()

        manager = ProviderManager(
            primary_provider=provider,
            fallback_providers=[],
        )
        available = manager.get_available_providers()
        assert len(available) >= 1

    def test_manager_set_provider(self):
        """Test setting current provider."""
        from medex.providers.manager import ProviderManager

        config1 = ProviderConfig(name="provider-a", model_id="model-a")
        config2 = ProviderConfig(name="provider-b", model_id="model-b")
        prov1 = ConcreteProvider(config1)
        prov2 = ConcreteProvider(config2)
        prov1.initialize()
        prov2.initialize()

        manager = ProviderManager(
            primary_provider=prov1,
            fallback_providers=[prov2],
        )

        manager.set_provider("provider-b")
        assert manager.current_provider is not None
        assert manager.current_provider.name == "provider-b"


# =============================================================================
# Run Tests
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
