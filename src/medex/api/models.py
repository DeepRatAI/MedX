# =============================================================================
# MedeX - API Models
# =============================================================================
"""
Request/Response models for the API layer.

Includes:
- Query models
- Response models
- WebSocket messages
- Error models
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


# =============================================================================
# Enums
# =============================================================================


class UserType(str, Enum):
    """User type for query context."""

    EDUCATIONAL = "educational"
    PROFESSIONAL = "professional"
    RESEARCH = "research"


class QueryStatus(str, Enum):
    """Status of a query."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class MessageType(str, Enum):
    """WebSocket message types."""

    # Client -> Server
    QUERY = "query"
    CANCEL = "cancel"
    PING = "ping"

    # Server -> Client
    THINKING = "thinking"
    STREAMING = "streaming"
    TOOL_CALL = "tool_call"
    RAG_SEARCH = "rag_search"
    COMPLETE = "complete"
    ERROR = "error"
    PONG = "pong"


class ErrorCode(str, Enum):
    """API error codes."""

    # Client errors (4xx)
    INVALID_REQUEST = "invalid_request"
    VALIDATION_ERROR = "validation_error"
    UNAUTHORIZED = "unauthorized"
    FORBIDDEN = "forbidden"
    NOT_FOUND = "not_found"
    RATE_LIMITED = "rate_limited"
    CONTENT_BLOCKED = "content_blocked"

    # Server errors (5xx)
    INTERNAL_ERROR = "internal_error"
    SERVICE_UNAVAILABLE = "service_unavailable"
    LLM_ERROR = "llm_error"
    RAG_ERROR = "rag_error"
    TIMEOUT = "timeout"


# =============================================================================
# Request Models
# =============================================================================


@dataclass
class QueryRequest:
    """Medical query request."""

    query: str
    user_type: UserType = UserType.EDUCATIONAL
    session_id: str | None = None

    # Options
    stream: bool = True
    include_sources: bool = True
    include_reasoning: bool = False
    language: str = "es"

    # Context
    patient_context: dict[str, Any] | None = None
    conversation_history: list[dict[str, str]] | None = None

    def validate(self) -> list[str]:
        """Validate request."""
        errors = []

        if not self.query or len(self.query.strip()) < 3:
            errors.append("Query must be at least 3 characters")

        if len(self.query) > 10000:
            errors.append("Query must be less than 10000 characters")

        if self.language not in ["es", "en", "pt"]:
            errors.append("Language must be 'es', 'en', or 'pt'")

        return errors


@dataclass
class FeedbackRequest:
    """Feedback on a response."""

    query_id: str
    rating: int  # 1-5
    helpful: bool | None = None
    accurate: bool | None = None
    comment: str | None = None

    def validate(self) -> list[str]:
        """Validate request."""
        errors = []

        if not self.query_id:
            errors.append("query_id is required")

        if self.rating < 1 or self.rating > 5:
            errors.append("Rating must be between 1 and 5")

        return errors


@dataclass
class SearchRequest:
    """RAG search request."""

    query: str
    collection: str = "medical_knowledge"
    limit: int = 10
    min_score: float = 0.5
    filters: dict[str, Any] | None = None

    def validate(self) -> list[str]:
        """Validate request."""
        errors = []

        if not self.query:
            errors.append("Query is required")

        if self.limit < 1 or self.limit > 100:
            errors.append("Limit must be between 1 and 100")

        if self.min_score < 0 or self.min_score > 1:
            errors.append("min_score must be between 0 and 1")

        return errors


# =============================================================================
# Response Models
# =============================================================================


@dataclass
class QueryResponse:
    """Response to a medical query."""

    query_id: str
    status: QueryStatus
    response: str | None = None

    # Metadata
    user_type: UserType = UserType.EDUCATIONAL
    is_emergency: bool = False

    # Clinical info
    diagnosis: dict[str, Any] | None = None
    treatment_plan: dict[str, Any] | None = None
    triage_level: int | None = None

    # Sources
    sources: list[dict[str, Any]] = field(default_factory=list)

    # Timing
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: datetime | None = None
    duration_ms: float | None = None

    # Usage
    tokens_used: int = 0
    model_used: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "query_id": self.query_id,
            "status": self.status.value,
            "response": self.response,
            "user_type": self.user_type.value,
            "is_emergency": self.is_emergency,
            "diagnosis": self.diagnosis,
            "treatment_plan": self.treatment_plan,
            "triage_level": self.triage_level,
            "sources": self.sources,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat()
            if self.completed_at
            else None,
            "duration_ms": self.duration_ms,
            "tokens_used": self.tokens_used,
            "model_used": self.model_used,
        }


@dataclass
class SearchResult:
    """Single search result."""

    id: str
    content: str
    score: float
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "content": self.content,
            "score": self.score,
            "metadata": self.metadata,
        }


@dataclass
class SearchResponse:
    """Response to a search request."""

    query: str
    results: list[SearchResult] = field(default_factory=list)
    total: int = 0
    duration_ms: float = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "query": self.query,
            "results": [r.to_dict() for r in self.results],
            "total": self.total,
            "duration_ms": self.duration_ms,
        }


# =============================================================================
# WebSocket Messages
# =============================================================================


@dataclass
class WSMessage:
    """WebSocket message."""

    type: MessageType
    data: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "type": self.type.value,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WSMessage":
        """Create from dictionary."""
        return cls(
            type=MessageType(data.get("type", "query")),
            data=data.get("data", {}),
        )

    # Factory methods for common messages
    @classmethod
    def thinking(cls, message: str = "Analizando consulta...") -> "WSMessage":
        """Create thinking message."""
        return cls(type=MessageType.THINKING, data={"message": message})

    @classmethod
    def streaming(cls, chunk: str, token_count: int = 0) -> "WSMessage":
        """Create streaming chunk message."""
        return cls(
            type=MessageType.STREAMING,
            data={
                "chunk": chunk,
                "token_count": token_count,
            },
        )

    @classmethod
    def tool_call(cls, tool_name: str, status: str = "executing") -> "WSMessage":
        """Create tool call message."""
        return cls(
            type=MessageType.TOOL_CALL,
            data={
                "tool": tool_name,
                "status": status,
            },
        )

    @classmethod
    def rag_search(cls, query: str, results_count: int = 0) -> "WSMessage":
        """Create RAG search message."""
        return cls(
            type=MessageType.RAG_SEARCH,
            data={
                "query": query,
                "results_count": results_count,
            },
        )

    @classmethod
    def complete(cls, response: QueryResponse) -> "WSMessage":
        """Create completion message."""
        return cls(type=MessageType.COMPLETE, data=response.to_dict())

    @classmethod
    def error(
        cls, code: ErrorCode, message: str, details: dict | None = None
    ) -> "WSMessage":
        """Create error message."""
        return cls(
            type=MessageType.ERROR,
            data={
                "code": code.value,
                "message": message,
                "details": details or {},
            },
        )


# =============================================================================
# Error Models
# =============================================================================


@dataclass
class APIError:
    """API error response."""

    code: ErrorCode
    message: str
    details: dict[str, Any] = field(default_factory=dict)
    request_id: str | None = None
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "error": {
                "code": self.code.value,
                "message": self.message,
                "details": self.details,
            },
            "request_id": self.request_id,
            "timestamp": self.timestamp.isoformat(),
        }

    @property
    def status_code(self) -> int:
        """Get HTTP status code for error."""
        code_mapping = {
            ErrorCode.INVALID_REQUEST: 400,
            ErrorCode.VALIDATION_ERROR: 422,
            ErrorCode.UNAUTHORIZED: 401,
            ErrorCode.FORBIDDEN: 403,
            ErrorCode.NOT_FOUND: 404,
            ErrorCode.RATE_LIMITED: 429,
            ErrorCode.CONTENT_BLOCKED: 451,
            ErrorCode.INTERNAL_ERROR: 500,
            ErrorCode.SERVICE_UNAVAILABLE: 503,
            ErrorCode.LLM_ERROR: 502,
            ErrorCode.RAG_ERROR: 502,
            ErrorCode.TIMEOUT: 504,
        }
        return code_mapping.get(self.code, 500)


# =============================================================================
# Health Models
# =============================================================================


@dataclass
class HealthResponse:
    """Health check response."""

    status: str  # healthy, degraded, unhealthy
    version: str
    uptime_seconds: float
    components: list[dict[str, Any]] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "status": self.status,
            "version": self.version,
            "uptime_seconds": self.uptime_seconds,
            "components": self.components,
            "timestamp": self.timestamp.isoformat(),
        }
