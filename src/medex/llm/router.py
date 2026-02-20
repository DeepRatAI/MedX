# =============================================================================
# MedeX - LLM Router (Multi-Provider)
# =============================================================================
"""
Intelligent LLM routing system with multi-provider support.

Features:
- Multi-provider routing (Kimi K2, OpenRouter, Groq, DeepSeek, etc.)
- Automatic failover and retry logic
- Rate limiting and quota management
- Provider health monitoring
- Cost optimization routing
- Streaming support
- Response caching
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any

import httpx

from medex.llm.models import (
    FinishReason,
    LLMConfig,
    LLMProvider,
    LLMRequest,
    LLMResponse,
    ProviderStatus,
    StreamChunk,
    StreamEventType,
    TokenUsage,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Provider Configurations
# =============================================================================

PROVIDER_CONFIGS: dict[LLMProvider, dict[str, Any]] = {
    LLMProvider.HUGGINGFACE: {
        "model": "Qwen/Qwen2.5-72B-Instruct",
        "base_url": "https://router.huggingface.co/v1",
        "env_key": "HF_TOKEN",
        "context_window": 32_000,
        "supports_streaming": True,
        "supports_tools": True,
        "rate_limit_rpm": 100,
        "rate_limit_tpm": 500_000,
    },
    LLMProvider.KIMI: {
        "model": "moonshot-v1-128k",
        "base_url": "https://api.moonshot.cn/v1",
        "env_key": "KIMI_API_KEY",
        "context_window": 128_000,
        "supports_streaming": True,
        "supports_tools": True,
        "rate_limit_rpm": 60,
        "rate_limit_tpm": 100_000,
    },
    LLMProvider.OPENROUTER: {
        "model": "qwen/qwen-2.5-72b-instruct",
        "base_url": "https://openrouter.ai/api/v1",
        "env_key": "OPENROUTER_API_KEY",
        "context_window": 131_072,
        "supports_streaming": True,
        "supports_tools": True,
        "rate_limit_rpm": 200,
        "rate_limit_tpm": 500_000,
        "extra_headers": {
            "HTTP-Referer": "https://medex.ai",
            "X-Title": "MedeX Medical Assistant",
        },
    },
    LLMProvider.GROQ: {
        "model": "llama-3.3-70b-versatile",
        "base_url": "https://api.groq.com/openai/v1",
        "env_key": "GROQ_API_KEY",
        "context_window": 128_000,
        "supports_streaming": True,
        "supports_tools": True,
        "rate_limit_rpm": 30,
        "rate_limit_tpm": 15_000,
    },
    LLMProvider.DEEPSEEK: {
        "model": "deepseek-chat",
        "base_url": "https://api.deepseek.com/v1",
        "env_key": "DEEPSEEK_API_KEY",
        "context_window": 64_000,
        "supports_streaming": True,
        "supports_tools": True,
        "rate_limit_rpm": 60,
        "rate_limit_tpm": 100_000,
    },
    LLMProvider.TOGETHER: {
        "model": "meta-llama/Llama-3.3-70B-Instruct-Turbo",
        "base_url": "https://api.together.xyz/v1",
        "env_key": "TOGETHER_API_KEY",
        "context_window": 131_072,
        "supports_streaming": True,
        "supports_tools": False,
        "rate_limit_rpm": 60,
        "rate_limit_tpm": 100_000,
    },
    LLMProvider.CEREBRAS: {
        "model": "llama-3.3-70b",
        "base_url": "https://api.cerebras.ai/v1",
        "env_key": "CEREBRAS_API_KEY",
        "context_window": 128_000,
        "supports_streaming": True,
        "supports_tools": False,
        "rate_limit_rpm": 30,
        "rate_limit_tpm": 60_000,
    },
    LLMProvider.OLLAMA: {
        "model": "llama3.2:latest",
        "base_url": "http://localhost:11434/v1",
        "env_key": None,
        "context_window": 128_000,
        "supports_streaming": True,
        "supports_tools": True,
        "rate_limit_rpm": 1000,
        "rate_limit_tpm": 1_000_000,
    },
}


# Model alternatives for fallback
MODEL_ALTERNATIVES: dict[LLMProvider, list[str]] = {
    LLMProvider.OPENROUTER: [
        "qwen/qwen-2.5-72b-instruct",
        "deepseek/deepseek-chat",
        "meta-llama/llama-3.3-70b-instruct",
        "anthropic/claude-3.5-sonnet",
    ],
    LLMProvider.GROQ: [
        "llama-3.3-70b-versatile",
        "llama-3.1-70b-versatile",
        "mixtral-8x7b-32768",
    ],
    LLMProvider.TOGETHER: [
        "meta-llama/Llama-3.3-70B-Instruct-Turbo",
        "Qwen/Qwen2.5-72B-Instruct-Turbo",
        "deepseek-ai/DeepSeek-V3",
    ],
}


# =============================================================================
# Router Configuration
# =============================================================================


@dataclass
class RouterConfig:
    """Configuration for LLM router."""

    # Provider priority order
    provider_priority: list[LLMProvider] = field(
        default_factory=lambda: [
            LLMProvider.HUGGINGFACE,  # Free, reliable
            LLMProvider.KIMI,
            LLMProvider.GROQ,
            LLMProvider.OPENROUTER,
            LLMProvider.DEEPSEEK,
            LLMProvider.TOGETHER,
            LLMProvider.CEREBRAS,
            LLMProvider.OLLAMA,
        ]
    )

    # Retry settings
    max_retries: int = 3
    retry_delay: float = 1.0
    retry_backoff: float = 2.0

    # Timeout settings
    connect_timeout: float = 10.0
    read_timeout: float = 180.0  # Increased for reasoning models (R1, QwQ, Qwen3)

    # Caching
    enable_cache: bool = True
    cache_ttl: int = 3600

    # Health check
    health_check_interval: int = 60
    max_error_rate: float = 0.5

    # Cost optimization
    prefer_free_tier: bool = True
    max_cost_per_request: float = 0.10


# =============================================================================
# LLM Client
# =============================================================================


class LLMClient:
    """Client for a single LLM provider."""

    def __init__(
        self,
        provider: LLMProvider,
        config: LLMConfig | None = None,
    ) -> None:
        """Initialize LLM client."""
        self.provider = provider
        self.config = config or self._create_default_config()
        self.status = ProviderStatus(provider=provider)

        # HTTP client
        self._client: httpx.AsyncClient | None = None

    def _create_default_config(self) -> LLMConfig:
        """Create default configuration for provider."""
        provider_config = PROVIDER_CONFIGS.get(self.provider, {})

        api_key = None
        env_key = provider_config.get("env_key")
        if env_key:
            api_key = os.environ.get(env_key)

        return LLMConfig(
            provider=self.provider,
            model=provider_config.get("model", ""),
            api_key=api_key,
            base_url=provider_config.get("base_url"),
            context_window=provider_config.get("context_window", 128_000),
            supports_streaming=provider_config.get("supports_streaming", True),
            supports_tools=provider_config.get("supports_tools", True),
            requests_per_minute=provider_config.get("rate_limit_rpm", 60),
            tokens_per_minute=provider_config.get("rate_limit_tpm", 100_000),
        )

    @property
    def is_available(self) -> bool:
        """Check if provider is available."""
        # Must have API key (except Ollama)
        if self.provider != LLMProvider.OLLAMA and not self.config.api_key:
            return False
        return self.status.is_available and self.status.is_healthy

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None or self._client.is_closed:
            headers = {
                "Content-Type": "application/json",
            }

            if self.config.api_key:
                headers["Authorization"] = f"Bearer {self.config.api_key}"

            # Add provider-specific headers
            provider_config = PROVIDER_CONFIGS.get(self.provider, {})
            extra_headers = provider_config.get("extra_headers", {})
            headers.update(extra_headers)

            # Timeout increased to 180s for reasoning models (R1, QwQ, Qwen3)
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(
                    connect=10.0,
                    read=180.0,  # 3 minutes for long reasoning responses
                    write=30.0,
                    pool=10.0,
                ),
                headers=headers,
            )

        return self._client

    async def complete(self, request: LLMRequest) -> LLMResponse:
        """Send completion request to provider."""
        start_time = time.time()

        try:
            client = await self._get_client()

            # Build request body
            body = request.to_api_format()
            # Use request.model if specified, otherwise use config default
            body["model"] = request.model if request.model else self.config.model
            body["stream"] = False

            # Apply config defaults
            if "temperature" not in body or body["temperature"] is None:
                body["temperature"] = self.config.temperature
            if "max_tokens" not in body or body["max_tokens"] is None:
                body["max_tokens"] = self.config.max_tokens

            # Make request
            url = f"{self.config.base_url}/chat/completions"
            response = await client.post(url, json=body)
            response.raise_for_status()

            data = response.json()
            latency_ms = (time.time() - start_time) * 1000

            # Parse response
            choice = data.get("choices", [{}])[0]
            message = choice.get("message", {})
            usage = data.get("usage", {})

            finish_reason = self._parse_finish_reason(choice.get("finish_reason"))

            llm_response = LLMResponse(
                content=message.get("content", ""),
                finish_reason=finish_reason,
                usage=TokenUsage(
                    prompt_tokens=usage.get("prompt_tokens", 0),
                    completion_tokens=usage.get("completion_tokens", 0),
                    total_tokens=usage.get("total_tokens", 0),
                ),
                model=data.get("model", self.config.model),
                provider=self.provider,
                latency_ms=latency_ms,
                tool_calls=message.get("tool_calls", []),
                raw_response=data,
            )

            # Update status
            self.status.record_request(latency_ms, llm_response.usage.total_tokens)

            return llm_response

        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP {e.response.status_code}: {e.response.text[:200]}"
            self.status.record_error(error_msg)
            logger.error(f"Provider {self.provider.value} error: {error_msg}")

            return LLMResponse(
                content="",
                finish_reason=FinishReason.ERROR,
                usage=TokenUsage(),
                provider=self.provider,
                error=error_msg,
                latency_ms=(time.time() - start_time) * 1000,
            )

        except Exception as e:
            error_msg = str(e)
            self.status.record_error(error_msg)
            logger.error(f"Provider {self.provider.value} exception: {error_msg}")

            return LLMResponse(
                content="",
                finish_reason=FinishReason.ERROR,
                usage=TokenUsage(),
                provider=self.provider,
                error=error_msg,
                latency_ms=(time.time() - start_time) * 1000,
            )

    async def stream(self, request: LLMRequest) -> AsyncIterator[StreamChunk]:
        """Stream completion from provider."""
        start_time = time.time()
        first_token_time: float | None = None
        chunk_index = 0
        full_content = ""

        try:
            client = await self._get_client()

            # Build request body
            body = request.to_api_format()
            # Use request.model if specified, otherwise use config default
            body["model"] = request.model if request.model else self.config.model
            body["stream"] = True

            # Apply config defaults
            if "temperature" not in body or body["temperature"] is None:
                body["temperature"] = self.config.temperature
            if "max_tokens" not in body or body["max_tokens"] is None:
                body["max_tokens"] = self.config.max_tokens

            # Emit start event
            yield StreamChunk(
                event_type=StreamEventType.START,
                index=chunk_index,
            )
            chunk_index += 1

            # Make streaming request
            url = f"{self.config.base_url}/chat/completions"

            async with client.stream("POST", url, json=body) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    if not line or not line.startswith("data: "):
                        continue

                    data_str = line[6:]  # Remove "data: " prefix

                    if data_str == "[DONE]":
                        break

                    try:
                        data = json.loads(data_str)
                    except json.JSONDecodeError:
                        continue

                    choice = data.get("choices", [{}])[0]
                    delta = choice.get("delta", {})
                    content = delta.get("content", "")

                    if content:
                        if first_token_time is None:
                            first_token_time = time.time()

                        full_content += content

                        yield StreamChunk(
                            event_type=StreamEventType.DELTA,
                            delta=content,
                            content=full_content,
                            index=chunk_index,
                        )
                        chunk_index += 1

                    # Check for tool calls
                    if "tool_calls" in delta:
                        yield StreamChunk(
                            event_type=StreamEventType.TOOL_CALL,
                            tool_call=delta["tool_calls"],
                            index=chunk_index,
                        )
                        chunk_index += 1

                    # Check for finish
                    finish_reason = choice.get("finish_reason")
                    if finish_reason:
                        break

            # Emit finish event
            latency_ms = (time.time() - start_time) * 1000
            ttft_ms = (
                (first_token_time - start_time) * 1000 if first_token_time else None
            )

            yield StreamChunk(
                event_type=StreamEventType.FINISH,
                content=full_content,
                finish_reason=FinishReason.STOP,
                usage=TokenUsage(
                    # Estimates for streaming
                    prompt_tokens=len(str(request.messages)) // 4,
                    completion_tokens=len(full_content) // 4,
                    total_tokens=(len(str(request.messages)) + len(full_content)) // 4,
                ),
                index=chunk_index,
            )

            # Update status
            self.status.record_request(latency_ms, len(full_content) // 4)

        except Exception as e:
            error_msg = str(e)
            self.status.record_error(error_msg)
            logger.error(f"Provider {self.provider.value} stream error: {error_msg}")

            yield StreamChunk(
                event_type=StreamEventType.ERROR,
                error=error_msg,
                index=chunk_index,
            )

    def _parse_finish_reason(self, reason: str | None) -> FinishReason:
        """Parse finish reason from API response."""
        if not reason:
            return FinishReason.STOP

        mapping = {
            "stop": FinishReason.STOP,
            "length": FinishReason.LENGTH,
            "tool_calls": FinishReason.TOOL_CALLS,
            "content_filter": FinishReason.CONTENT_FILTER,
            "function_call": FinishReason.TOOL_CALLS,
        }
        return mapping.get(reason, FinishReason.STOP)

    async def health_check(self) -> bool:
        """Check provider health with minimal request."""
        try:
            request = LLMRequest(
                messages=[],
                max_tokens=1,
            )
            request.messages = [
                type(
                    "Message",
                    (),
                    {"to_api_format": lambda: {"role": "user", "content": "test"}},
                )()  # type: ignore
            ]

            client = await self._get_client()
            url = f"{self.config.base_url}/models"

            response = await client.get(url, timeout=5.0)
            self.status.is_healthy = response.status_code == 200
            return self.status.is_healthy

        except Exception as e:
            logger.warning(f"Health check failed for {self.provider.value}: {e}")
            self.status.is_healthy = False
            return False

    async def close(self) -> None:
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None


# =============================================================================
# LLM Router
# =============================================================================


class LLMRouter:
    """Intelligent router for multiple LLM providers."""

    def __init__(self, config: RouterConfig | None = None) -> None:
        """Initialize router."""
        self.config = config or RouterConfig()
        self.clients: dict[LLMProvider, LLMClient] = {}

        # Initialize clients for available providers
        self._initialize_clients()

        # Cache
        self._cache: dict[str, LLMResponse] = {}

        # Metrics
        self._total_requests = 0
        self._total_tokens = 0
        self._provider_usage: dict[LLMProvider, int] = {}

    def _initialize_clients(self) -> None:
        """Initialize clients for configured providers."""
        for provider in self.config.provider_priority:
            client = LLMClient(provider)
            if client.is_available or provider == LLMProvider.OLLAMA:
                self.clients[provider] = client
                logger.info(f"Initialized LLM client for {provider.value}")
            else:
                logger.debug(f"Skipping {provider.value}: no API key configured")

    def get_available_providers(self) -> list[LLMProvider]:
        """Get list of available providers in priority order."""
        available = []
        for provider in self.config.provider_priority:
            client = self.clients.get(provider)
            if client and client.is_available:
                available.append(provider)
        return available

    def _select_provider(
        self,
        request: LLMRequest,
        exclude: list[LLMProvider] | None = None,
    ) -> LLMProvider | None:
        """Select best provider for request."""
        exclude = exclude or []

        for provider in self.config.provider_priority:
            if provider in exclude:
                continue

            client = self.clients.get(provider)
            if not client or not client.is_available:
                continue

            # Check rate limits
            if client.status.requests_remaining <= 0:
                continue

            # Check error rate
            if client.status.error_rate > self.config.max_error_rate:
                continue

            # Check if provider supports required features
            if request.tools and not client.config.supports_tools:
                continue

            if request.stream and not client.config.supports_streaming:
                continue

            return provider

        return None

    async def complete(
        self,
        request: LLMRequest,
        provider: LLMProvider | None = None,
    ) -> LLMResponse:
        """Complete request with automatic failover."""
        # Check cache
        if self.config.enable_cache and not request.stream:
            cache_key = request.get_cache_key()
            if cache_key in self._cache:
                logger.debug("Returning cached response")
                return self._cache[cache_key]

        # Track excluded providers for retry
        excluded: list[LLMProvider] = []
        last_error: str | None = None

        for attempt in range(self.config.max_retries):
            # Select provider
            selected = provider if provider and attempt == 0 else None
            if not selected:
                selected = self._select_provider(request, exclude=excluded)

            if not selected:
                error_msg = "No available providers"
                logger.error(error_msg)
                return LLMResponse(
                    content="",
                    finish_reason=FinishReason.ERROR,
                    usage=TokenUsage(),
                    error=last_error or error_msg,
                )

            client = self.clients[selected]
            logger.info(
                f"Attempting request with {selected.value} (attempt {attempt + 1})"
            )

            # Make request
            response = await client.complete(request)

            if not response.has_error:
                # Cache successful response
                if self.config.enable_cache:
                    self._cache[request.get_cache_key()] = response

                # Update metrics
                self._total_requests += 1
                self._total_tokens += response.usage.total_tokens
                self._provider_usage[selected] = (
                    self._provider_usage.get(selected, 0) + 1
                )

                return response

            # Request failed, try next provider
            last_error = response.error
            excluded.append(selected)
            logger.warning(f"Provider {selected.value} failed: {response.error}")

            # Backoff before retry
            if attempt < self.config.max_retries - 1:
                delay = self.config.retry_delay * (self.config.retry_backoff**attempt)
                await asyncio.sleep(delay)

        # All retries exhausted
        return LLMResponse(
            content="",
            finish_reason=FinishReason.ERROR,
            usage=TokenUsage(),
            error=f"All providers failed. Last error: {last_error}",
        )

    async def stream(
        self,
        request: LLMRequest,
        provider: LLMProvider | None = None,
    ) -> AsyncIterator[StreamChunk]:
        """Stream response with automatic failover."""
        request.stream = True

        # Select provider
        selected = provider or self._select_provider(request)

        if not selected:
            yield StreamChunk(
                event_type=StreamEventType.ERROR,
                error="No available providers",
            )
            return

        client = self.clients[selected]
        logger.info(f"Streaming with {selected.value}")

        async for chunk in client.stream(request):
            yield chunk

            # Update metrics on finish
            if chunk.is_finish and chunk.usage:
                self._total_requests += 1
                self._total_tokens += chunk.usage.total_tokens
                self._provider_usage[selected] = (
                    self._provider_usage.get(selected, 0) + 1
                )

    async def health_check(self) -> dict[str, bool]:
        """Check health of all providers."""
        results = {}
        tasks = []

        for provider, client in self.clients.items():
            task = asyncio.create_task(client.health_check())
            tasks.append((provider, task))

        for provider, task in tasks:
            try:
                results[provider.value] = await task
            except Exception:
                results[provider.value] = False

        return results

    def get_status(self) -> dict[str, Any]:
        """Get router status and metrics."""
        return {
            "available_providers": [p.value for p in self.get_available_providers()],
            "total_requests": self._total_requests,
            "total_tokens": self._total_tokens,
            "provider_usage": {p.value: c for p, c in self._provider_usage.items()},
            "provider_status": {
                p.value: c.status.to_dict() for p, c in self.clients.items()
            },
            "cache_size": len(self._cache),
        }

    async def close(self) -> None:
        """Close all clients."""
        for client in self.clients.values():
            await client.close()


# =============================================================================
# Factory Functions
# =============================================================================

_router_instance: LLMRouter | None = None


def get_llm_router() -> LLMRouter:
    """Get or create global LLM router instance."""
    global _router_instance
    if _router_instance is None:
        _router_instance = LLMRouter()
    return _router_instance


async def shutdown_llm_router() -> None:
    """Shutdown global LLM router."""
    global _router_instance
    if _router_instance:
        await _router_instance.close()
        _router_instance = None


def create_llm_router(config: RouterConfig | None = None) -> LLMRouter:
    """Create new LLM router with custom config."""
    return LLMRouter(config)
