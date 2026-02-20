"""
Base Model Provider Interface.

Abstract base class for all model providers (Moonshot, HuggingFace, etc.).
"""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Generator, Optional


class ProviderStatus(Enum):
    """Provider availability status."""

    AVAILABLE = "available"
    QUOTA_EXCEEDED = "quota_exceeded"
    RATE_LIMITED = "rate_limited"
    AUTH_ERROR = "auth_error"
    UNAVAILABLE = "unavailable"
    UNKNOWN = "unknown"


@dataclass
class ProviderConfig:
    """Configuration for a model provider.

    Attributes:
        name: Human-readable provider name
        model_id: Model identifier
        api_key_env: Environment variable for API key
        api_key_file: File path for API key (fallback)
        base_url: API base URL
        max_tokens: Maximum tokens for response
        temperature: Sampling temperature
        supports_streaming: Whether provider supports streaming
        supports_vision: Whether provider supports image analysis
    """

    name: str
    model_id: str
    api_key_env: str = ""
    api_key_file: str = ""
    base_url: str = ""
    max_tokens: int = 4096
    temperature: float = 0.7
    supports_streaming: bool = True
    supports_vision: bool = False
    is_free: bool = False
    description: str = ""

    def get_api_key(self) -> Optional[str]:
        """Retrieve API key from environment or file."""
        # Try environment first
        if self.api_key_env:
            key = os.getenv(self.api_key_env)
            if key:
                return key

        # Try file fallback
        if self.api_key_file:
            try:
                with open(self.api_key_file, "r") as f:
                    return f.read().strip()
            except FileNotFoundError:
                pass

        return None


@dataclass
class ProviderResponse:
    """Response from a model provider.

    Attributes:
        content: Response text content
        provider: Provider that generated the response
        model: Model used
        status: Provider status after request
        tokens_used: Approximate tokens used
        error: Error message if failed
    """

    content: str = ""
    provider: str = ""
    model: str = ""
    status: ProviderStatus = ProviderStatus.AVAILABLE
    tokens_used: int = 0
    error: Optional[str] = None

    @property
    def success(self) -> bool:
        """Check if response was successful."""
        return self.error is None and self.content


class ModelProvider(ABC):
    """Abstract base class for model providers."""

    def __init__(self, config: ProviderConfig) -> None:
        """Initialize provider with configuration.

        Args:
            config: Provider configuration
        """
        self.config = config
        self._status = ProviderStatus.UNKNOWN
        self._client = None

    @property
    def name(self) -> str:
        """Provider display name."""
        return self.config.name

    @property
    def model_id(self) -> str:
        """Model identifier."""
        return self.config.model_id

    @property
    def status(self) -> ProviderStatus:
        """Current provider status."""
        return self._status

    @property
    def is_available(self) -> bool:
        """Check if provider is available."""
        return self._status == ProviderStatus.AVAILABLE

    @abstractmethod
    def initialize(self) -> bool:
        """Initialize the provider client.

        Returns:
            True if initialization successful
        """
        pass

    @abstractmethod
    def generate(
        self,
        messages: list[dict],
        system_prompt: str = "",
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> ProviderResponse:
        """Generate a response from the model.

        Args:
            messages: Conversation messages
            system_prompt: System prompt to use
            max_tokens: Override default max tokens
            temperature: Override default temperature

        Returns:
            ProviderResponse with content or error
        """
        pass

    @abstractmethod
    def stream(
        self,
        messages: list[dict],
        system_prompt: str = "",
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> Generator[str, None, ProviderResponse]:
        """Stream a response from the model.

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
        pass

    def _update_status_from_error(self, error: Exception) -> ProviderStatus:
        """Update status based on error type.

        Args:
            error: Exception that occurred

        Returns:
            Updated status
        """
        error_str = str(error).lower()

        if "429" in str(error) or "quota" in error_str or "balance" in error_str:
            self._status = ProviderStatus.QUOTA_EXCEEDED
        elif "401" in str(error) or "403" in str(error) or "auth" in error_str:
            self._status = ProviderStatus.AUTH_ERROR
        elif "rate" in error_str and "limit" in error_str:
            self._status = ProviderStatus.RATE_LIMITED
        else:
            self._status = ProviderStatus.UNAVAILABLE

        return self._status
