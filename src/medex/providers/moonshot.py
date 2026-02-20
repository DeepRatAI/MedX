"""
Moonshot (Kimi K2) Model Provider.

Provider implementation for Moonshot AI's Kimi K2 model.
"""

from __future__ import annotations

from collections.abc import Generator

from medex.providers.base import (
    ModelProvider,
    ProviderConfig,
    ProviderResponse,
    ProviderStatus,
)

# Default Moonshot configuration
MOONSHOT_CONFIG = ProviderConfig(
    name="Moonshot Kimi K2",
    model_id="kimi-k2-0711-preview",
    api_key_env="KIMI_API_KEY",
    api_key_file="api_key.txt",
    base_url="https://api.moonshot.ai/v1",
    max_tokens=5120,
    temperature=0.6,
    supports_streaming=True,
    supports_vision=True,
    is_free=False,
    description="Advanced reasoning model with 128K context",
)


class MoonshotProvider(ModelProvider):
    """Moonshot AI (Kimi K2) provider implementation."""

    def __init__(self, config: ProviderConfig | None = None) -> None:
        """Initialize Moonshot provider.

        Args:
            config: Optional custom configuration
        """
        super().__init__(config or MOONSHOT_CONFIG)

    def initialize(self) -> bool:
        """Initialize the OpenAI-compatible client for Moonshot.

        Returns:
            True if initialization successful
        """
        try:
            from openai import OpenAI

            api_key = self.config.get_api_key()
            if not api_key:
                self._status = ProviderStatus.AUTH_ERROR
                return False

            self._client = OpenAI(
                api_key=api_key,
                base_url=self.config.base_url,
            )
            self._status = ProviderStatus.AVAILABLE
            return True

        except ImportError:
            self._status = ProviderStatus.UNAVAILABLE
            return False
        except Exception as e:
            self._update_status_from_error(e)
            return False

    def generate(
        self,
        messages: list[dict],
        system_prompt: str = "",
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> ProviderResponse:
        """Generate a response using Moonshot API.

        Args:
            messages: Conversation messages
            system_prompt: System prompt to use
            max_tokens: Override default max tokens
            temperature: Override default temperature

        Returns:
            ProviderResponse with content or error
        """
        if not self._client:
            if not self.initialize():
                return ProviderResponse(
                    provider=self.name,
                    model=self.model_id,
                    status=self._status,
                    error="Failed to initialize client",
                )

        try:
            # Build messages with system prompt
            full_messages = []
            if system_prompt:
                full_messages.append({"role": "system", "content": system_prompt})
            full_messages.extend(messages)

            response = self._client.chat.completions.create(
                model=self.model_id,
                messages=full_messages,
                max_tokens=max_tokens or self.config.max_tokens,
                temperature=temperature or self.config.temperature,
            )

            content = response.choices[0].message.content or ""
            tokens = response.usage.total_tokens if response.usage else 0

            self._status = ProviderStatus.AVAILABLE
            return ProviderResponse(
                content=content,
                provider=self.name,
                model=self.model_id,
                status=self._status,
                tokens_used=tokens,
            )

        except Exception as e:
            self._update_status_from_error(e)
            return ProviderResponse(
                provider=self.name,
                model=self.model_id,
                status=self._status,
                error=str(e),
            )

    def stream(
        self,
        messages: list[dict],
        system_prompt: str = "",
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> Generator[str, None, ProviderResponse]:
        """Stream a response using Moonshot API.

        Args:
            messages: Conversation messages
            system_prompt: System prompt to use
            max_tokens: Override default max tokens
            temperature: Override default temperature

        Yields:
            Content chunks as they arrive

        Returns:
            Final ProviderResponse with complete content
        """
        if not self._client:
            if not self.initialize():
                return ProviderResponse(
                    provider=self.name,
                    model=self.model_id,
                    status=self._status,
                    error="Failed to initialize client",
                )

        try:
            # Build messages with system prompt
            full_messages = []
            if system_prompt:
                full_messages.append({"role": "system", "content": system_prompt})
            full_messages.extend(messages)

            stream = self._client.chat.completions.create(
                model=self.model_id,
                messages=full_messages,
                max_tokens=max_tokens or self.config.max_tokens,
                temperature=temperature or self.config.temperature,
                stream=True,
            )

            full_content = ""
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_content += content
                    yield content

            self._status = ProviderStatus.AVAILABLE
            return ProviderResponse(
                content=full_content,
                provider=self.name,
                model=self.model_id,
                status=self._status,
            )

        except Exception as e:
            self._update_status_from_error(e)
            return ProviderResponse(
                provider=self.name,
                model=self.model_id,
                status=self._status,
                error=str(e),
            )
