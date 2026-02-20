# =============================================================================
# MedeX - LLM Service
# =============================================================================
"""
High-level LLM service façade for MedeX.

Integrates:
- Multi-provider routing with failover
- Prompt management and formatting
- Response parsing and validation
- Streaming support with SSE
- Memory and context integration
- Tool execution support
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, AsyncIterator

from medex.llm.models import (
    FinishReason,
    LLMProvider,
    LLMRequest,
    LLMResponse,
    Message,
    ResponseFormat,
    StreamChunk,
    StreamEventType,
    TokenUsage,
)
from medex.llm.parser import (
    ParsedContentType,
    ParsedResponse,
    ResponseParser,
)
from medex.llm.prompts import (
    Language,
    PromptConfig,
    PromptManager,
    UserMode,
)
from medex.llm.router import (
    LLMRouter,
    RouterConfig,
    get_llm_router,
)
from medex.llm.streaming import (
    StreamConfig,
    StreamHandler,
    StreamState,
)


logger = logging.getLogger(__name__)


# =============================================================================
# Configuration
# =============================================================================


@dataclass
class LLMServiceConfig:
    """Configuration for LLM service."""

    # Prompt settings
    default_language: Language = Language.SPANISH
    default_user_mode: UserMode = UserMode.EDUCATIONAL
    include_disclaimer: bool = True
    include_sources: bool = True

    # Generation defaults
    default_temperature: float = 0.7
    default_max_tokens: int = 4096

    # Context limits
    max_context_tokens: int = 4000
    max_history_turns: int = 10

    # Streaming
    stream_by_default: bool = True
    heartbeat_interval: float = 15.0

    # Caching
    enable_cache: bool = True
    cache_ttl: int = 3600

    # Retry
    max_retries: int = 3
    retry_delay: float = 1.0

    # Metrics
    track_metrics: bool = True


# =============================================================================
# Service Metrics
# =============================================================================


@dataclass
class LLMServiceMetrics:
    """Metrics for LLM service."""

    total_requests: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0

    successful_requests: int = 0
    failed_requests: int = 0

    avg_latency_ms: float = 0.0
    avg_ttft_ms: float = 0.0

    requests_by_mode: dict[str, int] = field(default_factory=dict)
    requests_by_provider: dict[str, int] = field(default_factory=dict)

    last_request_at: datetime | None = None

    def record_request(
        self,
        response: LLMResponse,
        user_mode: UserMode,
    ) -> None:
        """Record a completed request."""
        self.total_requests += 1
        self.total_tokens += response.usage.total_tokens
        self.total_cost += response.usage.total_cost
        self.last_request_at = datetime.utcnow()

        if response.has_error:
            self.failed_requests += 1
        else:
            self.successful_requests += 1

        # Update averages (exponential moving average)
        alpha = 0.1
        self.avg_latency_ms = (
            alpha * response.latency_ms + (1 - alpha) * self.avg_latency_ms
        )

        if response.time_to_first_token_ms:
            self.avg_ttft_ms = (
                alpha * response.time_to_first_token_ms + (1 - alpha) * self.avg_ttft_ms
            )

        # Track by mode
        mode_key = user_mode.value
        self.requests_by_mode[mode_key] = self.requests_by_mode.get(mode_key, 0) + 1

        # Track by provider
        if response.provider:
            provider_key = response.provider.value
            self.requests_by_provider[provider_key] = (
                self.requests_by_provider.get(provider_key, 0) + 1
            )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_requests": self.total_requests,
            "total_tokens": self.total_tokens,
            "total_cost": self.total_cost,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "success_rate": (
                self.successful_requests / self.total_requests
                if self.total_requests > 0
                else 0.0
            ),
            "avg_latency_ms": self.avg_latency_ms,
            "avg_ttft_ms": self.avg_ttft_ms,
            "requests_by_mode": self.requests_by_mode,
            "requests_by_provider": self.requests_by_provider,
            "last_request_at": (
                self.last_request_at.isoformat() if self.last_request_at else None
            ),
        }


# =============================================================================
# LLM Service
# =============================================================================


class LLMService:
    """High-level LLM service for MedeX."""

    def __init__(
        self,
        config: LLMServiceConfig | None = None,
        router: LLMRouter | None = None,
    ) -> None:
        """Initialize LLM service."""
        self.config = config or LLMServiceConfig()

        # Core components
        self.router = router or get_llm_router()
        self.prompt_manager = PromptManager(
            config=PromptConfig(
                language=self.config.default_language,
                user_mode=self.config.default_user_mode,
                include_disclaimer=self.config.include_disclaimer,
                include_sources=self.config.include_sources,
                max_context_tokens=self.config.max_context_tokens,
            )
        )
        self.parser = ResponseParser()
        self.stream_handler = StreamHandler(
            config=StreamConfig(
                heartbeat_interval=self.config.heartbeat_interval,
            )
        )

        # Metrics
        self.metrics = LLMServiceMetrics()

    async def query(
        self,
        query: str,
        context: str | None = None,
        history: list[Message] | None = None,
        user_mode: UserMode | None = None,
        language: Language | None = None,
        tools: list[dict[str, Any]] | None = None,
        response_format: ResponseFormat = ResponseFormat.MARKDOWN,
        stream: bool | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        provider: LLMProvider | None = None,
        include_disclaimer: bool | None = None,
        model: str | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """
        Send a query to the LLM.

        Args:
            query: User query text
            context: Optional RAG context
            history: Optional conversation history
            user_mode: Educational or professional mode
            language: Response language
            tools: Available tools for the LLM
            response_format: Expected response format
            stream: Whether to stream (overrides config)
            temperature: Temperature (overrides config)
            max_tokens: Max tokens (overrides config)
            provider: Specific provider to use
            model: Specific model to use (e.g., "Qwen/Qwen2.5-72B-Instruct")
            **kwargs: Additional prompt variables

        Returns:
            LLMResponse with content and metadata
        """
        mode = user_mode or self.config.default_user_mode
        lang = language or self.config.default_language
        use_stream = stream if stream is not None else self.config.stream_by_default

        # Build messages
        messages = self.prompt_manager.build_messages(
            query=query,
            context=self._truncate_context(context) if context else None,
            history=self._truncate_history(history),
            user_mode=mode,
            language=lang,
            **kwargs,
        )

        # Build request
        request = LLMRequest(
            messages=messages,
            model=model,  # Pass model override to request
            temperature=temperature or self.config.default_temperature,
            max_tokens=max_tokens or self.config.default_max_tokens,
            response_format=response_format,
            tools=tools,
            stream=use_stream,
        )

        # Execute request
        start_time = time.time()

        if use_stream:
            # Collect streaming response
            response = await self.stream_handler.collect_stream(
                self.router.stream(request, provider=provider)
            )
        else:
            response = await self.router.complete(request, provider=provider)

        # Post-process response
        should_add_disclaimer = (
            include_disclaimer
            if include_disclaimer is not None
            else self.config.include_disclaimer
        )
        if not response.has_error and should_add_disclaimer:
            response.content = self.prompt_manager.add_disclaimer(
                response.content,
                user_mode=mode,
                language=lang,
            )

        # Record metrics
        if self.config.track_metrics:
            self.metrics.record_request(response, mode)

        return response

    async def query_stream(
        self,
        query: str,
        context: str | None = None,
        history: list[Message] | None = None,
        user_mode: UserMode | None = None,
        language: Language | None = None,
        tools: list[dict[str, Any]] | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        provider: LLMProvider | None = None,
        model: str | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[StreamChunk]:
        """
        Stream a query response.

        Yields StreamChunk objects for real-time display.
        """
        mode = user_mode or self.config.default_user_mode
        lang = language or self.config.default_language

        # Build messages
        messages = self.prompt_manager.build_messages(
            query=query,
            context=self._truncate_context(context) if context else None,
            history=self._truncate_history(history),
            user_mode=mode,
            language=lang,
            **kwargs,
        )

        # Build request
        request = LLMRequest(
            messages=messages,
            model=model,  # Pass model override to request
            temperature=temperature or self.config.default_temperature,
            max_tokens=max_tokens or self.config.default_max_tokens,
            stream=True,
            tools=tools,
        )

        # Stream response
        async for chunk in self.router.stream(request, provider=provider):
            yield chunk

    async def query_stream_sse(
        self,
        query: str,
        context: str | None = None,
        history: list[Message] | None = None,
        user_mode: UserMode | None = None,
        model: str | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """
        Stream a query response as SSE events.

        Yields SSE-formatted strings for direct HTTP streaming.
        """
        from uuid import uuid4

        request_id = f"req_{uuid4().hex[:12]}"

        chunks = self.query_stream(
            query=query,
            context=context,
            history=history,
            user_mode=user_mode,
            model=model,  # Pass model override
            **kwargs,
        )

        async for sse_event in self.stream_handler.create_stream(
            chunks,
            request_id=request_id,
        ):
            yield sse_event

    async def query_with_parse(
        self,
        query: str,
        context: str | None = None,
        expected_type: ParsedContentType = ParsedContentType.TEXT,
        **kwargs: Any,
    ) -> ParsedResponse:
        """
        Query and parse the response.

        Returns structured parsed response with extracted entities.
        """
        response = await self.query(
            query=query,
            context=context,
            stream=False,  # Parsing requires complete response
            **kwargs,
        )

        return self.parser.parse(response, expected_type=expected_type)

    async def query_medical(
        self,
        query: str,
        context: str | None = None,
        history: list[Message] | None = None,
        **kwargs: Any,
    ) -> ParsedResponse:
        """
        Query for medical professional use case.

        Returns parsed medical report with structured data.
        """
        response = await self.query(
            query=query,
            context=context,
            history=history,
            user_mode=UserMode.PROFESSIONAL,
            stream=False,
            **kwargs,
        )

        return self.parser.parse(
            response,
            expected_type=ParsedContentType.MEDICAL_REPORT,
        )

    async def query_educational(
        self,
        query: str,
        context: str | None = None,
        history: list[Message] | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """
        Query for educational use case.

        Returns friendly, accessible response.
        """
        return await self.query(
            query=query,
            context=context,
            history=history,
            user_mode=UserMode.EDUCATIONAL,
            **kwargs,
        )

    def _truncate_context(self, context: str) -> str:
        """Truncate context to fit token limit."""
        return self.prompt_manager.truncate_context(
            context,
            max_tokens=self.config.max_context_tokens,
        )

    def _truncate_history(
        self,
        history: list[Message] | None,
    ) -> list[Message] | None:
        """Truncate history to max turns."""
        if not history:
            return None

        max_messages = self.config.max_history_turns * 2  # User + assistant pairs
        if len(history) <= max_messages:
            return history

        return history[-max_messages:]

    async def health_check(self) -> dict[str, Any]:
        """Check service health."""
        router_health = await self.router.health_check()

        return {
            "status": "healthy" if any(router_health.values()) else "degraded",
            "providers": router_health,
            "metrics": self.metrics.to_dict(),
            "config": {
                "default_language": self.config.default_language.value,
                "default_user_mode": self.config.default_user_mode.value,
                "stream_by_default": self.config.stream_by_default,
            },
        }

    def get_available_providers(self) -> list[str]:
        """Get list of available providers."""
        return [p.value for p in self.router.get_available_providers()]

    def get_metrics(self) -> dict[str, Any]:
        """Get service metrics."""
        return self.metrics.to_dict()

    async def close(self) -> None:
        """Close service and release resources."""
        await self.router.close()


# =============================================================================
# Factory Functions
# =============================================================================

_service_instance: LLMService | None = None


def get_llm_service() -> LLMService:
    """Get or create global LLM service instance."""
    global _service_instance
    if _service_instance is None:
        _service_instance = LLMService()
    return _service_instance


async def shutdown_llm_service() -> None:
    """Shutdown global LLM service."""
    global _service_instance
    if _service_instance:
        await _service_instance.close()
        _service_instance = None


def create_llm_service(config: LLMServiceConfig | None = None) -> LLMService:
    """Create new LLM service with custom config."""
    return LLMService(config)
