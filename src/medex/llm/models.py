# =============================================================================
# MedeX - LLM System Data Models
# =============================================================================
"""
Data models for the LLM System.

This module defines:
- LLMProvider: Enum of supported providers
- LLMConfig: Provider configuration
- Message: Chat message representation
- Conversation: Multi-turn conversation
- LLMResponse: Structured response from LLM
- TokenUsage: Token accounting
- StreamChunk: Streaming response chunk
"""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4


# =============================================================================
# Enumerations
# =============================================================================


class LLMProvider(str, Enum):
    """Supported LLM providers."""

    # Primary - Free tier available
    HUGGINGFACE = "huggingface"  # HuggingFace Router (FREE)
    KIMI = "kimi"  # Moonshot AI - Kimi K2
    OPENROUTER = "openrouter"  # Multi-model gateway
    GROQ = "groq"  # Ultra-fast inference

    # Secondary - Free/cheap options
    TOGETHER = "together"  # Together AI
    DEEPSEEK = "deepseek"  # DeepSeek API
    CEREBRAS = "cerebras"  # Cerebras inference

    # Fallback - Local
    OLLAMA = "ollama"  # Local Ollama

    @property
    def is_free_tier(self) -> bool:
        """Check if provider has free tier."""
        return self in {
            LLMProvider.HUGGINGFACE,
            LLMProvider.KIMI,
            LLMProvider.GROQ,
            LLMProvider.CEREBRAS,
            LLMProvider.OLLAMA,
        }


class MessageRole(str, Enum):
    """Message roles in conversation."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"
    FUNCTION = "function"


class ResponseFormat(str, Enum):
    """Expected response format."""

    TEXT = "text"
    JSON = "json"
    MARKDOWN = "markdown"
    MEDICAL_REPORT = "medical_report"


class FinishReason(str, Enum):
    """Reason for completion finish."""

    STOP = "stop"
    LENGTH = "length"
    TOOL_CALLS = "tool_calls"
    CONTENT_FILTER = "content_filter"
    ERROR = "error"


class StreamEventType(str, Enum):
    """Types of streaming events."""

    START = "start"
    DELTA = "delta"
    TOOL_CALL = "tool_call"
    FINISH = "finish"
    ERROR = "error"
    HEARTBEAT = "heartbeat"


# =============================================================================
# Configuration Models
# =============================================================================


@dataclass
class LLMConfig:
    """Configuration for an LLM provider."""

    provider: LLMProvider
    model: str
    api_key: str | None = None
    base_url: str | None = None

    # Generation parameters
    temperature: float = 0.7
    max_tokens: int = 4096
    top_p: float = 0.95
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0

    # Provider-specific
    timeout: float = 60.0
    max_retries: int = 3
    retry_delay: float = 1.0

    # Rate limiting
    requests_per_minute: int = 60
    tokens_per_minute: int = 100_000

    # Features
    supports_streaming: bool = True
    supports_tools: bool = True
    supports_vision: bool = False
    supports_json_mode: bool = True

    # Context window
    context_window: int = 128_000
    output_window: int = 8_192

    def __post_init__(self) -> None:
        """Set default base URLs for known providers."""
        if self.base_url is None:
            self.base_url = self._get_default_base_url()

    def _get_default_base_url(self) -> str:
        """Get default base URL for provider."""
        urls = {
            LLMProvider.KIMI: "https://api.moonshot.cn/v1",
            LLMProvider.OPENROUTER: "https://openrouter.ai/api/v1",
            LLMProvider.GROQ: "https://api.groq.com/openai/v1",
            LLMProvider.TOGETHER: "https://api.together.xyz/v1",
            LLMProvider.DEEPSEEK: "https://api.deepseek.com/v1",
            LLMProvider.CEREBRAS: "https://api.cerebras.ai/v1",
            LLMProvider.OLLAMA: "http://localhost:11434/v1",
        }
        return urls.get(self.provider, "")

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "provider": self.provider.value,
            "model": self.model,
            "base_url": self.base_url,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "context_window": self.context_window,
            "supports_streaming": self.supports_streaming,
            "supports_tools": self.supports_tools,
        }


# =============================================================================
# Message Models
# =============================================================================


@dataclass
class Message:
    """A single message in a conversation."""

    role: MessageRole
    content: str
    name: str | None = None
    tool_call_id: str | None = None
    tool_calls: list[dict[str, Any]] | None = None

    # Metadata
    id: str = field(default_factory=lambda: f"msg_{uuid4().hex[:12]}")
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)

    # Token tracking
    token_count: int | None = None

    @property
    def is_system(self) -> bool:
        """Check if system message."""
        return self.role == MessageRole.SYSTEM

    @property
    def is_user(self) -> bool:
        """Check if user message."""
        return self.role == MessageRole.USER

    @property
    def is_assistant(self) -> bool:
        """Check if assistant message."""
        return self.role == MessageRole.ASSISTANT

    @property
    def has_tool_calls(self) -> bool:
        """Check if message has tool calls."""
        return bool(self.tool_calls)

    def to_api_format(self) -> dict[str, Any]:
        """Convert to OpenAI API format."""
        msg: dict[str, Any] = {
            "role": self.role.value,
            "content": self.content,
        }

        if self.name:
            msg["name"] = self.name

        if self.tool_call_id:
            msg["tool_call_id"] = self.tool_call_id

        if self.tool_calls:
            msg["tool_calls"] = self.tool_calls

        return msg

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "role": self.role.value,
            "content": self.content,
            "name": self.name,
            "tool_call_id": self.tool_call_id,
            "tool_calls": self.tool_calls,
            "timestamp": self.timestamp.isoformat(),
            "token_count": self.token_count,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Message:
        """Create from dictionary."""
        return cls(
            id=data.get("id", f"msg_{uuid4().hex[:12]}"),
            role=MessageRole(data["role"]),
            content=data["content"],
            name=data.get("name"),
            tool_call_id=data.get("tool_call_id"),
            tool_calls=data.get("tool_calls"),
            timestamp=datetime.fromisoformat(data["timestamp"])
            if "timestamp" in data
            else datetime.utcnow(),
            token_count=data.get("token_count"),
            metadata=data.get("metadata", {}),
        )

    @classmethod
    def system(cls, content: str, **kwargs: Any) -> Message:
        """Create system message."""
        return cls(role=MessageRole.SYSTEM, content=content, **kwargs)

    @classmethod
    def user(cls, content: str, **kwargs: Any) -> Message:
        """Create user message."""
        return cls(role=MessageRole.USER, content=content, **kwargs)

    @classmethod
    def assistant(cls, content: str, **kwargs: Any) -> Message:
        """Create assistant message."""
        return cls(role=MessageRole.ASSISTANT, content=content, **kwargs)

    @classmethod
    def tool(cls, content: str, tool_call_id: str, name: str, **kwargs: Any) -> Message:
        """Create tool response message."""
        return cls(
            role=MessageRole.TOOL,
            content=content,
            tool_call_id=tool_call_id,
            name=name,
            **kwargs,
        )


# =============================================================================
# Token Usage Models
# =============================================================================


@dataclass
class TokenUsage:
    """Token usage accounting."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

    # Cost tracking (in USD)
    prompt_cost: float = 0.0
    completion_cost: float = 0.0
    total_cost: float = 0.0

    # Cache stats
    cached_tokens: int = 0
    cache_hit_rate: float = 0.0

    def __add__(self, other: TokenUsage) -> TokenUsage:
        """Add token usage."""
        return TokenUsage(
            prompt_tokens=self.prompt_tokens + other.prompt_tokens,
            completion_tokens=self.completion_tokens + other.completion_tokens,
            total_tokens=self.total_tokens + other.total_tokens,
            prompt_cost=self.prompt_cost + other.prompt_cost,
            completion_cost=self.completion_cost + other.completion_cost,
            total_cost=self.total_cost + other.total_cost,
            cached_tokens=self.cached_tokens + other.cached_tokens,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "prompt_cost": self.prompt_cost,
            "completion_cost": self.completion_cost,
            "total_cost": self.total_cost,
            "cached_tokens": self.cached_tokens,
            "cache_hit_rate": self.cache_hit_rate,
        }


# =============================================================================
# Response Models
# =============================================================================


@dataclass
class LLMResponse:
    """Response from LLM provider."""

    content: str
    finish_reason: FinishReason
    usage: TokenUsage

    # Metadata
    id: str = field(default_factory=lambda: f"resp_{uuid4().hex[:12]}")
    model: str = ""
    provider: LLMProvider | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    # Timing
    latency_ms: float = 0.0
    time_to_first_token_ms: float | None = None

    # Tool calls
    tool_calls: list[dict[str, Any]] = field(default_factory=list)

    # Raw response for debugging
    raw_response: dict[str, Any] | None = None

    # Error info
    error: str | None = None

    @property
    def is_complete(self) -> bool:
        """Check if response completed normally."""
        return self.finish_reason == FinishReason.STOP

    @property
    def is_truncated(self) -> bool:
        """Check if response was truncated."""
        return self.finish_reason == FinishReason.LENGTH

    @property
    def has_tool_calls(self) -> bool:
        """Check if response has tool calls."""
        return bool(self.tool_calls)

    @property
    def has_error(self) -> bool:
        """Check if response has error."""
        return self.error is not None or self.finish_reason == FinishReason.ERROR

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "content": self.content,
            "finish_reason": self.finish_reason.value,
            "model": self.model,
            "provider": self.provider.value if self.provider else None,
            "created_at": self.created_at.isoformat(),
            "latency_ms": self.latency_ms,
            "time_to_first_token_ms": self.time_to_first_token_ms,
            "tool_calls": self.tool_calls,
            "usage": self.usage.to_dict(),
            "error": self.error,
        }


# =============================================================================
# Streaming Models
# =============================================================================


@dataclass
class StreamChunk:
    """A chunk from streaming response."""

    event_type: StreamEventType
    content: str = ""
    delta: str = ""

    # Metadata
    id: str = field(default_factory=lambda: f"chunk_{uuid4().hex[:8]}")
    index: int = 0
    timestamp: float = field(default_factory=time.time)

    # For tool calls
    tool_call: dict[str, Any] | None = None

    # For finish
    finish_reason: FinishReason | None = None
    usage: TokenUsage | None = None

    # For errors
    error: str | None = None

    @property
    def is_content(self) -> bool:
        """Check if chunk has content."""
        return self.event_type == StreamEventType.DELTA and bool(self.delta)

    @property
    def is_finish(self) -> bool:
        """Check if chunk is finish event."""
        return self.event_type == StreamEventType.FINISH

    @property
    def is_error(self) -> bool:
        """Check if chunk is error event."""
        return self.event_type == StreamEventType.ERROR

    def to_sse(self) -> str:
        """Convert to Server-Sent Events format."""
        import json

        data = {
            "event": self.event_type.value,
            "id": self.id,
            "index": self.index,
        }

        if self.delta:
            data["delta"] = self.delta

        if self.content:
            data["content"] = self.content

        if self.tool_call:
            data["tool_call"] = self.tool_call

        if self.finish_reason:
            data["finish_reason"] = self.finish_reason.value

        if self.usage:
            data["usage"] = self.usage.to_dict()

        if self.error:
            data["error"] = self.error

        return f"data: {json.dumps(data)}\n\n"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "event_type": self.event_type.value,
            "content": self.content,
            "delta": self.delta,
            "index": self.index,
            "timestamp": self.timestamp,
            "tool_call": self.tool_call,
            "finish_reason": self.finish_reason.value if self.finish_reason else None,
            "error": self.error,
        }


# =============================================================================
# Request Models
# =============================================================================


@dataclass
class LLMRequest:
    """Request to LLM provider."""

    messages: list[Message]
    config: LLMConfig | None = None

    # Model override (takes precedence over config.model if set)
    model: str | None = None

    # Generation parameters (override config)
    temperature: float | None = None
    max_tokens: int | None = None
    top_p: float | None = None
    stop: list[str] | None = None

    # Response format
    response_format: ResponseFormat = ResponseFormat.TEXT
    json_schema: dict[str, Any] | None = None

    # Tools
    tools: list[dict[str, Any]] | None = None
    tool_choice: str | dict[str, Any] | None = None

    # Streaming
    stream: bool = False

    # Metadata
    id: str = field(default_factory=lambda: f"req_{uuid4().hex[:12]}")
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def system_message(self) -> Message | None:
        """Get system message if present."""
        for msg in self.messages:
            if msg.is_system:
                return msg
        return None

    @property
    def last_user_message(self) -> Message | None:
        """Get last user message."""
        for msg in reversed(self.messages):
            if msg.is_user:
                return msg
        return None

    def get_cache_key(self) -> str:
        """Generate cache key for request."""
        import json

        key_data = {
            "messages": [m.to_api_format() for m in self.messages],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "response_format": self.response_format.value,
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.sha256(key_str.encode()).hexdigest()[:32]

    def to_api_format(self) -> dict[str, Any]:
        """Convert to OpenAI API format."""
        request: dict[str, Any] = {
            "messages": [m.to_api_format() for m in self.messages],
            "stream": self.stream,
        }

        # Add generation parameters
        if self.temperature is not None:
            request["temperature"] = self.temperature
        if self.max_tokens is not None:
            request["max_tokens"] = self.max_tokens
        if self.top_p is not None:
            request["top_p"] = self.top_p
        if self.stop:
            request["stop"] = self.stop

        # Add response format
        if self.response_format == ResponseFormat.JSON:
            request["response_format"] = {"type": "json_object"}
        elif self.json_schema:
            request["response_format"] = {
                "type": "json_schema",
                "json_schema": self.json_schema,
            }

        # Add tools
        if self.tools:
            request["tools"] = self.tools
            if self.tool_choice:
                request["tool_choice"] = self.tool_choice

        return request

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "messages": [m.to_dict() for m in self.messages],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "response_format": self.response_format.value,
            "stream": self.stream,
            "tools": self.tools,
            "metadata": self.metadata,
        }


# =============================================================================
# Provider Status Models
# =============================================================================


@dataclass
class ProviderStatus:
    """Status of an LLM provider."""

    provider: LLMProvider
    is_available: bool = True
    is_healthy: bool = True

    # Rate limiting
    requests_remaining: int = 60
    tokens_remaining: int = 100_000
    reset_at: datetime | None = None

    # Performance
    avg_latency_ms: float = 0.0
    error_rate: float = 0.0
    last_error: str | None = None
    last_error_at: datetime | None = None

    # Usage
    requests_today: int = 0
    tokens_today: int = 0

    def record_request(self, latency_ms: float, tokens: int) -> None:
        """Record a successful request."""
        self.requests_remaining -= 1
        self.tokens_remaining -= tokens
        self.requests_today += 1
        self.tokens_today += tokens

        # Update average latency (exponential moving average)
        alpha = 0.1
        self.avg_latency_ms = alpha * latency_ms + (1 - alpha) * self.avg_latency_ms

    def record_error(self, error: str) -> None:
        """Record an error."""
        self.last_error = error
        self.last_error_at = datetime.utcnow()

        # Update error rate
        alpha = 0.1
        self.error_rate = alpha * 1.0 + (1 - alpha) * self.error_rate

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "provider": self.provider.value,
            "is_available": self.is_available,
            "is_healthy": self.is_healthy,
            "requests_remaining": self.requests_remaining,
            "tokens_remaining": self.tokens_remaining,
            "avg_latency_ms": self.avg_latency_ms,
            "error_rate": self.error_rate,
            "last_error": self.last_error,
            "requests_today": self.requests_today,
            "tokens_today": self.tokens_today,
        }
