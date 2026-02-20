"""
Provider Manager with Automatic Fallback.

Manages multiple model providers with automatic fallback when primary fails.
"""

from __future__ import annotations

from collections.abc import Generator
from dataclasses import dataclass, field

from medex.providers.base import (
    ModelProvider,
    ProviderResponse,
    ProviderStatus,
)
from medex.providers.huggingface import HuggingFaceProvider
from medex.providers.moonshot import MoonshotProvider


@dataclass
class ProviderManager:
    """Manages multiple providers with automatic fallback.

    When the primary provider fails (e.g., quota exceeded),
    automatically falls back to secondary providers.
    """

    primary_provider: ModelProvider | None = None
    fallback_providers: list[ModelProvider] = field(default_factory=list)
    _current_provider: ModelProvider | None = None
    auto_fallback: bool = True

    def __post_init__(self) -> None:
        """Initialize default providers if none specified."""
        if self.primary_provider is None:
            self.primary_provider = MoonshotProvider()

        if not self.fallback_providers:
            # Add HuggingFace as default fallback
            self.fallback_providers = [
                HuggingFaceProvider(model_key="mistral-medical"),
                HuggingFaceProvider(model_key="qwen-medical"),
            ]

        self._current_provider = self.primary_provider

    def initialize_all(self) -> bool:
        """Initialize all providers.

        Returns:
            True if at least one provider initialized successfully
        """
        success = False

        if self.primary_provider:
            if self.primary_provider.initialize():
                success = True
                self._current_provider = self.primary_provider

        for provider in self.fallback_providers:
            if provider.initialize():
                success = True
                if self._current_provider is None:
                    self._current_provider = provider

        return success

    @property
    def current_provider(self) -> ModelProvider | None:
        """Get the currently active provider."""
        return self._current_provider

    @property
    def current_model_name(self) -> str:
        """Get the current model's display name."""
        if self._current_provider:
            return self._current_provider.name
        return "No provider available"

    def set_provider(self, provider_name: str) -> bool:
        """Manually set the active provider.

        Args:
            provider_name: Name of provider to activate

        Returns:
            True if provider was set successfully
        """
        # Check primary
        if self.primary_provider and self.primary_provider.name == provider_name:
            if self.primary_provider.initialize():
                self._current_provider = self.primary_provider
                return True

        # Check fallbacks
        for provider in self.fallback_providers:
            if provider.name == provider_name:
                if provider.initialize():
                    self._current_provider = provider
                    return True

        return False

    def get_available_providers(self) -> list[str]:
        """Get list of available provider names.

        Returns:
            List of provider display names
        """
        providers = []
        if self.primary_provider:
            providers.append(self.primary_provider.name)
        providers.extend(p.name for p in self.fallback_providers)
        return providers

    def _try_fallback(self) -> ModelProvider | None:
        """Try to switch to a fallback provider.

        Returns:
            Active fallback provider or None if all failed
        """
        for provider in self.fallback_providers:
            if provider.status == ProviderStatus.AVAILABLE:
                self._current_provider = provider
                return provider
            # Try to initialize if not yet done
            if provider.initialize():
                self._current_provider = provider
                return provider
        return None

    def generate(
        self,
        messages: list[dict],
        system_prompt: str = "",
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> ProviderResponse:
        """Generate response with automatic fallback.

        Args:
            messages: Conversation messages
            system_prompt: System prompt to use
            max_tokens: Override default max tokens
            temperature: Override default temperature

        Returns:
            ProviderResponse from successful provider
        """
        if not self._current_provider:
            if not self.initialize_all():
                return ProviderResponse(
                    error="No providers available",
                    status=ProviderStatus.UNAVAILABLE,
                )

        # Try current provider
        response = self._current_provider.generate(
            messages=messages,
            system_prompt=system_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
        )

        # If failed and auto_fallback enabled, try fallbacks
        if not response.success and self.auto_fallback:
            if response.status in (
                ProviderStatus.QUOTA_EXCEEDED,
                ProviderStatus.RATE_LIMITED,
            ):
                fallback = self._try_fallback()
                if fallback:
                    response = fallback.generate(
                        messages=messages,
                        system_prompt=system_prompt,
                        max_tokens=max_tokens,
                        temperature=temperature,
                    )

        return response

    def stream(
        self,
        messages: list[dict],
        system_prompt: str = "",
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> Generator[str, None, ProviderResponse]:
        """Stream response with automatic fallback.

        Args:
            messages: Conversation messages
            system_prompt: System prompt to use
            max_tokens: Override default max tokens
            temperature: Override default temperature

        Yields:
            Content chunks as they arrive

        Returns:
            Final ProviderResponse
        """
        if not self._current_provider:
            if not self.initialize_all():
                return ProviderResponse(
                    error="No providers available",
                    status=ProviderStatus.UNAVAILABLE,
                )

        try:
            # Try current provider
            gen = self._current_provider.stream(
                messages=messages,
                system_prompt=system_prompt,
                max_tokens=max_tokens,
                temperature=temperature,
            )

            full_content = ""
            for chunk in gen:
                full_content += chunk
                yield chunk

            return ProviderResponse(
                content=full_content,
                provider=self._current_provider.name,
                model=self._current_provider.model_id,
                status=ProviderStatus.AVAILABLE,
            )

        except Exception as e:
            # Check if we should fallback
            error_str = str(e).lower()
            should_fallback = (
                "429" in str(e)
                or "quota" in error_str
                or "balance" in error_str
                or "rate" in error_str
            )

            if should_fallback and self.auto_fallback:
                fallback = self._try_fallback()
                if fallback:
                    # Notify about fallback
                    yield f"\n[Switching to {fallback.name}...]\n"

                    gen = fallback.stream(
                        messages=messages,
                        system_prompt=system_prompt,
                        max_tokens=max_tokens,
                        temperature=temperature,
                    )

                    full_content = ""
                    for chunk in gen:
                        full_content += chunk
                        yield chunk

                    return ProviderResponse(
                        content=full_content,
                        provider=fallback.name,
                        model=fallback.model_id,
                        status=ProviderStatus.AVAILABLE,
                    )

            return ProviderResponse(
                error=str(e),
                status=ProviderStatus.UNAVAILABLE,
            )
