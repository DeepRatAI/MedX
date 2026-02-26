# =============================================================================
# MedeX - API Middleware
# =============================================================================
"""
Middleware components for the FastAPI application.

Includes:
- CORS middleware
- Security middleware
- Observability middleware
- Rate limiting middleware
- Error handling middleware
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .models import ErrorCode


# =============================================================================
# Context for Request
# =============================================================================


@dataclass
class RequestContext:
    """Context information for a request."""

    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    correlation_id: str | None = None
    user_id: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    start_time: float = field(default_factory=time.time)

    # Security context
    authenticated: bool = False
    api_key: str | None = None
    scopes: list[str] = field(default_factory=list)

    # Rate limit context
    rate_limit_remaining: int = -1
    rate_limit_reset: datetime | None = None

    def elapsed_ms(self) -> float:
        """Get elapsed time in milliseconds."""
        return (time.time() - self.start_time) * 1000


# Context variable for current request
_current_context: RequestContext | None = None


def get_current_context() -> RequestContext | None:
    """Get current request context."""
    return _current_context


def set_current_context(ctx: RequestContext | None) -> None:
    """Set current request context."""
    global _current_context
    _current_context = ctx


# =============================================================================
# CORS Configuration
# =============================================================================


@dataclass
class CORSConfig:
    """CORS configuration."""

    allow_origins: list[str] = field(default_factory=lambda: ["*"])
    allow_methods: list[str] = field(
        default_factory=lambda: ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    )
    allow_headers: list[str] = field(
        default_factory=lambda: [
            "Content-Type",
            "Authorization",
            "X-Request-ID",
            "X-Correlation-ID",
            "X-API-Key",
        ]
    )
    expose_headers: list[str] = field(
        default_factory=lambda: [
            "X-Request-ID",
            "X-Rate-Limit-Remaining",
            "X-Rate-Limit-Reset",
        ]
    )
    allow_credentials: bool = True
    max_age: int = 3600


# =============================================================================
# Security Middleware Config
# =============================================================================


@dataclass
class SecurityConfig:
    """Security middleware configuration."""

    # API key settings
    api_key_header: str = "X-API-Key"
    api_key_required: bool = False  # For educational mode
    valid_api_keys: set[str] = field(default_factory=set)

    # Rate limiting
    rate_limit_enabled: bool = True
    rate_limit_requests: int = 100  # Per minute
    rate_limit_burst: int = 20

    # Content security
    max_request_size: int = 1024 * 1024  # 1MB
    content_type_check: bool = True
    allowed_content_types: set[str] = field(
        default_factory=lambda: {"application/json"}
    )

    # Security headers
    security_headers: dict[str, str] = field(
        default_factory=lambda: {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": "default-src 'self'",
            "Referrer-Policy": "strict-origin-when-cross-origin",
        }
    )


# =============================================================================
# Observability Middleware Config
# =============================================================================


@dataclass
class ObservabilityConfig:
    """Observability middleware configuration."""

    # Logging
    log_requests: bool = True
    log_responses: bool = True
    log_slow_requests_ms: float = 1000  # Log requests slower than this
    exclude_paths: set[str] = field(
        default_factory=lambda: {"/health", "/ready", "/live", "/metrics"}
    )

    # Metrics
    collect_metrics: bool = True

    # Tracing
    enable_tracing: bool = True
    trace_header: str = "X-Trace-ID"
    span_header: str = "X-Span-ID"


# =============================================================================
# Middleware Base Class
# =============================================================================


class MiddlewareBase:
    """Base class for middleware."""

    async def process_request(self, ctx: RequestContext, request: Any) -> Any | None:
        """
        Process incoming request.

        Args:
            ctx: Request context
            request: The request object

        Returns:
            None to continue, or response to short-circuit
        """
        return None

    async def process_response(
        self, ctx: RequestContext, request: Any, response: Any
    ) -> Any:
        """
        Process outgoing response.

        Args:
            ctx: Request context
            request: The request object
            response: The response object

        Returns:
            Modified response
        """
        return response

    async def handle_error(
        self, ctx: RequestContext, request: Any, error: Exception
    ) -> Any | None:
        """
        Handle request error.

        Args:
            ctx: Request context
            request: The request object
            error: The exception

        Returns:
            Error response, or None to re-raise
        """
        return None


# =============================================================================
# CORS Middleware
# =============================================================================


class CORSMiddleware(MiddlewareBase):
    """CORS middleware implementation."""

    def __init__(self, config: CORSConfig | None = None) -> None:
        """Initialize CORS middleware."""
        self.config = config or CORSConfig()

    def _is_origin_allowed(self, origin: str) -> bool:
        """Check if origin is allowed."""
        if "*" in self.config.allow_origins:
            return True
        return origin in self.config.allow_origins

    async def process_request(self, ctx: RequestContext, request: Any) -> Any | None:
        """Handle preflight requests."""
        # For preflight, would return early response
        # Implementation depends on framework
        return None

    async def process_response(
        self, ctx: RequestContext, request: Any, response: Any
    ) -> Any:
        """Add CORS headers to response."""
        # Would add headers based on origin
        return response


# =============================================================================
# Security Middleware
# =============================================================================


class SecurityMiddleware(MiddlewareBase):
    """Security middleware implementation."""

    def __init__(self, config: SecurityConfig | None = None) -> None:
        """Initialize security middleware."""
        self.config = config or SecurityConfig()
        self._rate_limit_store: dict[str, list[float]] = {}

    async def process_request(self, ctx: RequestContext, request: Any) -> Any | None:
        """Validate security requirements."""
        # Check API key if required
        if self.config.api_key_required:
            api_key = ctx.api_key
            if not api_key or api_key not in self.config.valid_api_keys:
                # Would return 401 response
                ctx.authenticated = False
                return None  # Simplified - real impl returns error response

            ctx.authenticated = True

        # Check rate limiting
        if self.config.rate_limit_enabled:
            if not self._check_rate_limit(ctx):
                # Would return 429 response
                return None

        return None

    def _check_rate_limit(self, ctx: RequestContext) -> bool:
        """Check if request is within rate limit."""
        key = ctx.ip_address or ctx.api_key or "anonymous"
        now = time.time()

        # Get request timestamps for this key
        timestamps = self._rate_limit_store.get(key, [])

        # Filter to last minute
        window_start = now - 60
        timestamps = [t for t in timestamps if t > window_start]

        # Check limit
        if len(timestamps) >= self.config.rate_limit_requests:
            ctx.rate_limit_remaining = 0
            return False

        # Add current request
        timestamps.append(now)
        self._rate_limit_store[key] = timestamps
        ctx.rate_limit_remaining = self.config.rate_limit_requests - len(timestamps)

        return True

    async def process_response(
        self, ctx: RequestContext, request: Any, response: Any
    ) -> Any:
        """Add security headers to response."""
        # Would add security headers
        return response


# =============================================================================
# Observability Middleware
# =============================================================================


class ObservabilityMiddleware(MiddlewareBase):
    """Observability middleware for logging, metrics, and tracing."""

    def __init__(self, config: ObservabilityConfig | None = None) -> None:
        """Initialize observability middleware."""
        self.config = config or ObservabilityConfig()
        self._request_count = 0
        self._error_count = 0
        self._latencies: list[float] = []

    async def process_request(self, ctx: RequestContext, request: Any) -> Any | None:
        """Start request tracking."""
        if self.config.collect_metrics:
            self._request_count += 1

        if self.config.log_requests:
            self._log_request(ctx, request)

        return None

    async def process_response(
        self, ctx: RequestContext, request: Any, response: Any
    ) -> Any:
        """Complete request tracking."""
        latency_ms = ctx.elapsed_ms()

        if self.config.collect_metrics:
            self._latencies.append(latency_ms)

        if self.config.log_responses:
            self._log_response(ctx, response, latency_ms)

        if latency_ms > self.config.log_slow_requests_ms:
            self._log_slow_request(ctx, latency_ms)

        return response

    async def handle_error(
        self, ctx: RequestContext, request: Any, error: Exception
    ) -> Any | None:
        """Track error."""
        if self.config.collect_metrics:
            self._error_count += 1

        self._log_error(ctx, error)
        return None

    def _log_request(self, ctx: RequestContext, request: Any) -> None:
        """Log incoming request."""
        # Would use structured logging
        pass

    def _log_response(self, ctx: RequestContext, response: Any, latency: float) -> None:
        """Log outgoing response."""
        # Would use structured logging
        pass

    def _log_slow_request(self, ctx: RequestContext, latency: float) -> None:
        """Log slow request warning."""
        # Would log with WARNING level
        pass

    def _log_error(self, ctx: RequestContext, error: Exception) -> None:
        """Log request error."""
        # Would log with ERROR level
        pass

    def get_metrics(self) -> dict[str, Any]:
        """Get collected metrics."""
        return {
            "total_requests": self._request_count,
            "total_errors": self._error_count,
            "error_rate": self._error_count / max(1, self._request_count),
            "avg_latency_ms": sum(self._latencies) / max(1, len(self._latencies)),
            "p99_latency_ms": (
                sorted(self._latencies)[int(len(self._latencies) * 0.99)]
                if self._latencies
                else 0
            ),
        }


# =============================================================================
# Error Handling Middleware
# =============================================================================


class ErrorHandlingMiddleware(MiddlewareBase):
    """Error handling middleware."""

    def __init__(self, debug: bool = False) -> None:
        """Initialize error handling middleware."""
        self.debug = debug

    async def handle_error(
        self, ctx: RequestContext, request: Any, error: Exception
    ) -> Any | None:
        """Handle and format error response."""
        from .models import APIError

        # Determine error type
        error_code = self._classify_error(error)
        message = str(error) if self.debug else self._get_user_message(error_code)

        api_error = APIError(
            code=error_code,
            message=message,
            details={"type": type(error).__name__} if self.debug else {},
            request_id=ctx.request_id,
        )

        return api_error

    def _classify_error(self, error: Exception) -> ErrorCode:
        """Classify error to error code."""
        from .models import ErrorCode

        error_type = type(error).__name__

        if "Validation" in error_type:
            return ErrorCode.VALIDATION_ERROR
        elif "Auth" in error_type or "Permission" in error_type:
            return ErrorCode.FORBIDDEN
        elif "NotFound" in error_type:
            return ErrorCode.NOT_FOUND
        elif "RateLimit" in error_type:
            return ErrorCode.RATE_LIMITED
        elif "Timeout" in error_type:
            return ErrorCode.TIMEOUT
        else:
            return ErrorCode.INTERNAL_ERROR

    def _get_user_message(self, code: ErrorCode) -> str:
        """Get user-friendly error message."""
        from .models import ErrorCode

        messages = {
            ErrorCode.INVALID_REQUEST: "La solicitud no es válida",
            ErrorCode.VALIDATION_ERROR: "Error de validación en los datos enviados",
            ErrorCode.UNAUTHORIZED: "No autorizado",
            ErrorCode.FORBIDDEN: "Acceso denegado",
            ErrorCode.NOT_FOUND: "Recurso no encontrado",
            ErrorCode.RATE_LIMITED: "Demasiadas solicitudes, intente más tarde",
            ErrorCode.CONTENT_BLOCKED: "Contenido bloqueado por políticas de seguridad",
            ErrorCode.INTERNAL_ERROR: "Error interno del servidor",
            ErrorCode.SERVICE_UNAVAILABLE: "Servicio no disponible temporalmente",
            ErrorCode.LLM_ERROR: "Error en el servicio de procesamiento",
            ErrorCode.RAG_ERROR: "Error en la búsqueda de información",
            ErrorCode.TIMEOUT: "La solicitud excedió el tiempo límite",
        }
        return messages.get(code, "Error desconocido")


# =============================================================================
# Middleware Stack
# =============================================================================


class MiddlewareStack:
    """Stack of middleware components."""

    def __init__(self) -> None:
        """Initialize middleware stack."""
        self._middlewares: list[MiddlewareBase] = []

    def add(self, middleware: MiddlewareBase) -> MiddlewareStack:
        """Add middleware to stack."""
        self._middlewares.append(middleware)
        return self

    async def process_request(self, ctx: RequestContext, request: Any) -> Any | None:
        """Process request through all middleware."""
        for middleware in self._middlewares:
            result = await middleware.process_request(ctx, request)
            if result is not None:
                # Short-circuit if middleware returns response
                return result
        return None

    async def process_response(
        self, ctx: RequestContext, request: Any, response: Any
    ) -> Any:
        """Process response through all middleware (reverse order)."""
        for middleware in reversed(self._middlewares):
            response = await middleware.process_response(ctx, request, response)
        return response

    async def handle_error(
        self, ctx: RequestContext, request: Any, error: Exception
    ) -> Any | None:
        """Handle error through middleware."""
        for middleware in reversed(self._middlewares):
            result = await middleware.handle_error(ctx, request, error)
            if result is not None:
                return result
        return None


# =============================================================================
# Factory Functions
# =============================================================================


def create_default_middleware_stack() -> MiddlewareStack:
    """Create default middleware stack."""
    return (
        MiddlewareStack()
        .add(ErrorHandlingMiddleware(debug=False))
        .add(ObservabilityMiddleware())
        .add(SecurityMiddleware())
        .add(CORSMiddleware())
    )


def create_development_middleware_stack() -> MiddlewareStack:
    """Create development middleware stack."""
    return (
        MiddlewareStack()
        .add(ErrorHandlingMiddleware(debug=True))
        .add(
            ObservabilityMiddleware(
                ObservabilityConfig(
                    log_requests=True,
                    log_responses=True,
                    log_slow_requests_ms=500,
                )
            )
        )
        .add(
            SecurityMiddleware(
                SecurityConfig(
                    api_key_required=False,
                    rate_limit_enabled=False,
                )
            )
        )
        .add(
            CORSMiddleware(
                CORSConfig(
                    allow_origins=["*"],
                )
            )
        )
    )
