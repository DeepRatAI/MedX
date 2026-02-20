# =============================================================================
# MedeX - Observability Models
# =============================================================================
"""
Domain models for observability.

Includes:
- Metric types and definitions
- Log entry structures
- Health check models
- Trace/span models
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

# =============================================================================
# Enums
# =============================================================================


class MetricType(str, Enum):
    """Types of metrics."""

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


class LogLevel(str, Enum):
    """Log severity levels."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class HealthStatus(str, Enum):
    """Health check status."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class SpanKind(str, Enum):
    """OpenTelemetry span kinds."""

    INTERNAL = "internal"
    SERVER = "server"
    CLIENT = "client"
    PRODUCER = "producer"
    CONSUMER = "consumer"


class ComponentType(str, Enum):
    """System component types."""

    DATABASE = "database"
    CACHE = "cache"
    VECTOR_STORE = "vector_store"
    LLM_PROVIDER = "llm_provider"
    EXTERNAL_API = "external_api"
    MESSAGE_QUEUE = "message_queue"


# =============================================================================
# Metric Models
# =============================================================================


@dataclass
class MetricDefinition:
    """Definition of a metric."""

    name: str
    description: str
    metric_type: MetricType
    unit: str = ""
    labels: list[str] = field(default_factory=list)

    @property
    def full_name(self) -> str:
        """Get full metric name with prefix."""
        return f"medex_{self.name}"


@dataclass
class MetricValue:
    """A metric measurement."""

    name: str
    value: float
    labels: dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


# =============================================================================
# Log Models
# =============================================================================


@dataclass
class LogEntry:
    """Structured log entry."""

    level: LogLevel
    message: str
    logger_name: str = "medex"
    timestamp: datetime = field(default_factory=datetime.now)

    # Context
    trace_id: str | None = None
    span_id: str | None = None
    user_id: str | None = None
    session_id: str | None = None
    request_id: str | None = None

    # Additional data
    extra: dict[str, Any] = field(default_factory=dict)
    exception: str | None = None
    stack_trace: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON logging."""
        result = {
            "timestamp": self.timestamp.isoformat(),
            "level": self.level.value,
            "logger": self.logger_name,
            "message": self.message,
        }

        if self.trace_id:
            result["trace_id"] = self.trace_id
        if self.span_id:
            result["span_id"] = self.span_id
        if self.user_id:
            result["user_id"] = self.user_id
        if self.session_id:
            result["session_id"] = self.session_id
        if self.request_id:
            result["request_id"] = self.request_id
        if self.exception:
            result["exception"] = self.exception
        if self.stack_trace:
            result["stack_trace"] = self.stack_trace
        if self.extra:
            result["extra"] = self.extra

        return result


# =============================================================================
# Health Check Models
# =============================================================================


@dataclass
class ComponentHealth:
    """Health status of a component."""

    name: str
    component_type: ComponentType
    status: HealthStatus
    latency_ms: float | None = None
    message: str | None = None
    details: dict[str, Any] = field(default_factory=dict)
    last_check: datetime = field(default_factory=datetime.now)

    @property
    def is_healthy(self) -> bool:
        """Check if component is healthy."""
        return self.status == HealthStatus.HEALTHY


@dataclass
class SystemHealth:
    """Overall system health."""

    status: HealthStatus
    version: str
    uptime_seconds: float
    components: list[ComponentHealth] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)

    @property
    def is_healthy(self) -> bool:
        """Check if system is healthy."""
        return self.status == HealthStatus.HEALTHY

    @property
    def unhealthy_components(self) -> list[ComponentHealth]:
        """Get list of unhealthy components."""
        return [c for c in self.components if not c.is_healthy]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "status": self.status.value,
            "version": self.version,
            "uptime_seconds": self.uptime_seconds,
            "timestamp": self.timestamp.isoformat(),
            "components": [
                {
                    "name": c.name,
                    "type": c.component_type.value,
                    "status": c.status.value,
                    "latency_ms": c.latency_ms,
                    "message": c.message,
                    "details": c.details,
                }
                for c in self.components
            ],
        }


# =============================================================================
# Trace/Span Models
# =============================================================================


@dataclass
class SpanContext:
    """Context for distributed tracing."""

    trace_id: str
    span_id: str
    parent_span_id: str | None = None
    trace_flags: int = 1  # 1 = sampled

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id,
            "trace_flags": self.trace_flags,
        }


@dataclass
class SpanEvent:
    """Event within a span."""

    name: str
    timestamp: datetime = field(default_factory=datetime.now)
    attributes: dict[str, Any] = field(default_factory=dict)


@dataclass
class SpanData:
    """Data for a completed span."""

    name: str
    context: SpanContext
    kind: SpanKind = SpanKind.INTERNAL
    start_time: datetime = field(default_factory=datetime.now)
    end_time: datetime | None = None

    # Attributes
    attributes: dict[str, Any] = field(default_factory=dict)
    events: list[SpanEvent] = field(default_factory=list)

    # Status
    status_code: str = "OK"  # OK, ERROR, UNSET
    status_message: str | None = None

    # Links
    links: list[SpanContext] = field(default_factory=list)

    @property
    def duration_ms(self) -> float | None:
        """Calculate span duration in milliseconds."""
        if self.end_time is None:
            return None
        delta = self.end_time - self.start_time
        return delta.total_seconds() * 1000

    def add_event(self, name: str, attributes: dict[str, Any] | None = None) -> None:
        """Add event to span."""
        self.events.append(
            SpanEvent(
                name=name,
                attributes=attributes or {},
            )
        )

    def set_error(self, message: str) -> None:
        """Mark span as error."""
        self.status_code = "ERROR"
        self.status_message = message


# =============================================================================
# Configuration Models
# =============================================================================


@dataclass
class ObservabilityConfig:
    """Configuration for observability."""

    # Service info
    service_name: str = "medex"
    service_version: str = "2.0.0"
    environment: str = "development"

    # Tracing
    enable_tracing: bool = True
    trace_sample_rate: float = 1.0  # 0.0 to 1.0
    otlp_endpoint: str | None = None  # OpenTelemetry collector endpoint

    # Metrics
    enable_metrics: bool = True
    metrics_port: int = 9090
    metrics_path: str = "/metrics"

    # Logging
    enable_structured_logging: bool = True
    log_level: LogLevel = LogLevel.INFO
    log_format: str = "json"  # json or text

    # Health checks
    enable_health_checks: bool = True
    health_check_interval: int = 30  # seconds

    # Export
    export_to_console: bool = True
    export_to_file: bool = False
    log_file_path: str = "/var/log/medex/app.log"
