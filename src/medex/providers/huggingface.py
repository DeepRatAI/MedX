"""
HuggingFace Model Provider - Router-based Implementation.

Uses HuggingFace Router API (router.huggingface.co) for fast inference.
HTTP direct calls with 15s timeout - NO SDK overhead.

Based on Cortex's proven implementation for 2-6s response times.
"""

from __future__ import annotations

from collections.abc import Generator

import httpx

from medex.providers.base import (
    ModelProvider,
    ProviderConfig,
    ProviderResponse,
    ProviderStatus,
)

# HuggingFace Router endpoints
HF_ROUTER_MODELS = "https://router.huggingface.co/v1/models"
HF_ROUTER_CHAT = "https://router.huggingface.co/v1/chat/completions"

# Timeout configuration (seconds)
HF_TIMEOUT = 20
HF_STREAM_TIMEOUT = 60

# Fast models confirmed working with Router API (tested 2-7s response times)
HUGGINGFACE_MODELS = {
    # === FAST ROUTER MODELS (RECOMMENDED) ===
    "deepseek-v3": ProviderConfig(
        name="DeepSeek V3.2",
        model_id="deepseek-ai/DeepSeek-V3.2",
        api_key_env="HF_TOKEN",
        max_tokens=8192,
        temperature=0.3,
        supports_streaming=True,
        supports_vision=False,
        is_free=True,
        description="DeepSeek V3.2 - Fastest model (~2.7s)",
    ),
    "llama-8b": ProviderConfig(
        name="Meta Llama 3.1 8B",
        model_id="meta-llama/Llama-3.1-8B-Instruct",
        api_key_env="HF_TOKEN",
        max_tokens=8192,
        temperature=0.3,
        supports_streaming=True,
        supports_vision=False,
        is_free=True,
        description="Llama 3.1 8B - Fast and reliable (~3.4s)",
    ),
    "qwen-72b": ProviderConfig(
        name="Qwen 2.5 72B",
        model_id="Qwen/Qwen2.5-72B-Instruct",
        api_key_env="HF_TOKEN",
        max_tokens=8192,
        temperature=0.3,
        supports_streaming=True,
        supports_vision=False,
        is_free=True,
        description="Qwen 2.5 72B - Best quality (~6.8s)",
    ),
    "qwen-32b": ProviderConfig(
        name="Qwen 2.5 32B",
        model_id="Qwen/Qwen2.5-32B-Instruct",
        api_key_env="HF_TOKEN",
        max_tokens=8192,
        temperature=0.3,
        supports_streaming=True,
        supports_vision=False,
        is_free=True,
        description="Qwen 2.5 32B - Good balance quality/speed",
    ),
    # === LEGACY KEYS (mapped to fast models) ===
    "gemma-9b": ProviderConfig(
        name="DeepSeek V3.2",
        model_id="deepseek-ai/DeepSeek-V3.2",
        api_key_env="HF_TOKEN",
        max_tokens=8192,
        temperature=0.3,
        supports_streaming=True,
        supports_vision=False,
        is_free=True,
        description="DeepSeek V3.2 (was Gemma)",
    ),
    "gemma-2b": ProviderConfig(
        name="Meta Llama 3.1 8B",
        model_id="meta-llama/Llama-3.1-8B-Instruct",
        api_key_env="HF_TOKEN",
        max_tokens=8192,
        temperature=0.3,
        supports_streaming=True,
        supports_vision=False,
        is_free=True,
        description="Llama 3.1 8B (was Gemma 2B)",
    ),
    "llama-3b": ProviderConfig(
        name="Meta Llama 3.1 8B",
        model_id="meta-llama/Llama-3.1-8B-Instruct",
        api_key_env="HF_TOKEN",
        max_tokens=8192,
        temperature=0.3,
        supports_streaming=True,
        supports_vision=False,
        is_free=True,
        description="Llama 3.1 8B Instruct",
    ),
    "qwen-coder": ProviderConfig(
        name="Qwen 2.5 32B",
        model_id="Qwen/Qwen2.5-32B-Instruct",
        api_key_env="HF_TOKEN",
        max_tokens=8192,
        temperature=0.3,
        supports_streaming=True,
        supports_vision=False,
        is_free=True,
        description="Qwen 2.5 32B (was Coder 7B)",
    ),
    "mistral-medical": ProviderConfig(
        name="DeepSeek V3.2",
        model_id="deepseek-ai/DeepSeek-V3.2",
        api_key_env="HF_TOKEN",
        max_tokens=8192,
        temperature=0.3,
        supports_streaming=True,
        supports_vision=False,
        is_free=True,
        description="DeepSeek V3.2 (was Mistral)",
    ),
    "qwen-medical": ProviderConfig(
        name="Qwen 2.5 72B",
        model_id="Qwen/Qwen2.5-72B-Instruct",
        api_key_env="HF_TOKEN",
        max_tokens=8192,
        temperature=0.3,
        supports_streaming=True,
        supports_vision=False,
        is_free=True,
        description="Qwen 2.5 72B (best for medical)",
    ),
    "llama-medical": ProviderConfig(
        name="Meta Llama 3.1 8B",
        model_id="meta-llama/Llama-3.1-8B-Instruct",
        api_key_env="HF_TOKEN",
        max_tokens=8192,
        temperature=0.3,
        supports_streaming=True,
        supports_vision=False,
        is_free=True,
        description="Llama 3.1 8B Instruct",
    ),
    "meditron-7b": ProviderConfig(
        name="Qwen 2.5 72B",
        model_id="Qwen/Qwen2.5-72B-Instruct",
        api_key_env="HF_TOKEN",
        max_tokens=8192,
        temperature=0.3,
        supports_streaming=True,
        supports_vision=False,
        is_free=True,
        description="Qwen 2.5 72B (was Meditron)",
    ),
}

# Fallback order if primary model fails
FALLBACK_MODELS = [
    "deepseek-ai/DeepSeek-V3.2",
    "meta-llama/Llama-3.1-8B-Instruct",
    "Qwen/Qwen2.5-72B-Instruct",
]

# Default model - DeepSeek is fastest
DEFAULT_HF_MODEL = "deepseek-v3"


class HuggingFaceProvider(ModelProvider):
    """HuggingFace Router API provider - HTTP direct implementation.

    Uses router.huggingface.co for fast inference (2-7s response times).
    NO SDK overhead - direct HTTP calls with proper timeouts.
    """

    def __init__(
        self, config: ProviderConfig | None = None, model_key: str = DEFAULT_HF_MODEL
    ) -> None:
        """Initialize HuggingFace provider.

        Args:
            config: Optional custom configuration
            model_key: Key from HUGGINGFACE_MODELS to use
        """
        if config is None:
            config = HUGGINGFACE_MODELS.get(
                model_key, HUGGINGFACE_MODELS[DEFAULT_HF_MODEL]
            )
        super().__init__(config)
        self._http_client: httpx.Client | None = None

    def initialize(self) -> bool:
        """Initialize HTTP client for Router API.

        Returns:
            True if initialization successful
        """
        try:
            api_key = self.config.get_api_key()
            if not api_key:
                self._status = ProviderStatus.UNAVAILABLE
                return False

            self._http_client = httpx.Client(timeout=HF_TIMEOUT)
            self._api_key = api_key
            self._status = ProviderStatus.AVAILABLE
            return True

        except Exception as e:
            self._update_status_from_error(e)
            return False

    def _build_payload(
        self,
        messages: list[dict],
        system_prompt: str = "",
        max_tokens: int | None = None,
        temperature: float | None = None,
        stream: bool = False,
    ) -> dict:
        """Build chat completion payload for Router API."""
        full_messages = []
        if system_prompt:
            full_messages.append({"role": "system", "content": system_prompt})
        full_messages.extend(messages)

        payload = {
            "model": self.config.model_id,
            "messages": full_messages,
            "max_tokens": max_tokens or self.config.max_tokens,
            "temperature": temperature or self.config.temperature,
        }
        if stream:
            payload["stream"] = True
        return payload

    def _post_with_fallback(self, payload: dict, headers: dict) -> httpx.Response:
        """Post to Router API with automatic fallback on model errors."""
        response = self._http_client.post(HF_ROUTER_CHAT, headers=headers, json=payload)

        # If model not supported, try fallbacks
        if response.status_code == 400 and "model" in response.text.lower():
            for fallback_model in FALLBACK_MODELS:
                if fallback_model == payload.get("model"):
                    continue
                payload["model"] = fallback_model
                response = self._http_client.post(
                    HF_ROUTER_CHAT, headers=headers, json=payload
                )
                if response.status_code == 200:
                    break

        return response

    def _extract_content(self, data: dict) -> str:
        """Extract text content from Router API response."""
        try:
            choices = data.get("choices", [])
            if not choices:
                return str(data)[:4000]
            first = choices[0]
            msg = first.get("message", {})
            content = msg.get("content", "")
            if isinstance(content, str) and content.strip():
                return content.strip()
            return str(data)[:4000]
        except Exception:
            return str(data)[:4000]

    def generate(
        self,
        messages: list[dict],
        system_prompt: str = "",
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> ProviderResponse:
        """Generate a response using HuggingFace Router API (HTTP direct).

        Args:
            messages: Conversation messages
            system_prompt: System prompt to use
            max_tokens: Override default max tokens
            temperature: Override default temperature

        Returns:
            ProviderResponse with content or error
        """
        if not self._http_client and not self.initialize():
            return ProviderResponse(
                provider=self.name,
                model=self.model_id,
                status=self._status,
                error="Failed to initialize client",
            )

        try:
            headers = {"Authorization": f"Bearer {self._api_key}"}
            payload = self._build_payload(
                messages, system_prompt, max_tokens, temperature
            )

            response = self._post_with_fallback(payload, headers)

            if response.status_code == 401:
                self._status = ProviderStatus.UNAVAILABLE
                return ProviderResponse(
                    provider=self.name,
                    model=self.model_id,
                    status=self._status,
                    error="Unauthorized - Invalid HF_TOKEN",
                )

            response.raise_for_status()
            content = self._extract_content(response.json())

            self._status = ProviderStatus.AVAILABLE
            return ProviderResponse(
                content=content,
                provider=self.name,
                model=payload.get("model", self.model_id),
                status=self._status,
            )

        except httpx.TimeoutException:
            self._status = ProviderStatus.RATE_LIMITED
            return ProviderResponse(
                provider=self.name,
                model=self.model_id,
                status=self._status,
                error=f"Timeout after {HF_TIMEOUT}s",
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
        """Stream a response using HuggingFace Router API.

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
        if not self._http_client and not self.initialize():
            return ProviderResponse(
                provider=self.name,
                model=self.model_id,
                status=self._status,
                error="Failed to initialize client",
            )

        try:
            headers = {"Authorization": f"Bearer {self._api_key}"}
            payload = self._build_payload(
                messages, system_prompt, max_tokens, temperature, stream=True
            )

            full_content = ""
            with httpx.Client(timeout=HF_STREAM_TIMEOUT) as client:
                with client.stream(
                    "POST", HF_ROUTER_CHAT, headers=headers, json=payload
                ) as response:
                    if response.status_code == 401:
                        raise RuntimeError("Unauthorized HF API key")
                    response.raise_for_status()

                    for line in response.iter_lines():
                        if not line or not line.startswith("data: "):
                            continue
                        data_str = line[6:]
                        if data_str.strip() == "[DONE]":
                            break
                        try:
                            import json

                            data = json.loads(data_str)
                            choices = data.get("choices", [])
                            if choices:
                                delta = choices[0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    full_content += content
                                    yield content
                        except (json.JSONDecodeError, KeyError):
                            continue

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


def get_available_hf_models() -> dict[str, ProviderConfig]:
    """Get all available HuggingFace model configurations.

    Returns:
        Dictionary of model key to configuration
    """
    return HUGGINGFACE_MODELS.copy()
