# =============================================================================
# MedeX - Observability Module
# =============================================================================
"""
Observability module for MedeX.

Provides comprehensive observability features:
- Metrics: Prometheus-compatible metrics collection
- Tracing: OpenTelemetry-compatible distributed tracing
- Logging: Structured JSON logging with correlation
- Health Checks: Kubernetes-ready liveness/readiness probes

Example:
    >>> from medex.observability import init_observability, ServiceConfig
    >>>
    >>> # Initialize observability
    >>> obs = init_observability(ServiceConfig(
    ...     service_name="medex",
    ...     environment="production",
    ... ))
    >>>
    >>> # Track metrics
    >>> obs.track_request("GET", "/api/query", 200, 0.150)
    >>>
    >>> # Trace operations
    >>> with obs.start_span("process_query") as span:
    ...     span.set_attribute("query_length", 100)
    ...     result = process(query)
    >>>
    >>> # Health checks
    >>> health = await obs.check_health()
    >>> print(health.status)
"""

from medex.observability.health import (
    CallableHealthCheck,
    HealthCheck,
    HealthManager,
    HealthManagerConfig,
    LLMProviderHealthCheck,
    PostgresHealthCheck,
    QdrantHealthCheck,
    RedisHealthCheck,
    get_health_manager,
    init_health_manager,
    register_health_check,
)
from medex.observability.logging import (
    JSONFormatter,
    LoggingConfig,
    StructuredLogger,
    TextFormatter,
    clear_correlation_context,
    configure_logging,
    get_correlation_context,
    get_logger,
    set_correlation_context,
)
from medex.observability.metrics import (
    Counter,
    Gauge,
    Histogram,
    HistogramTimer,
    MetricsConfig,
    MetricsRegistry,
    Summary,
    get_metrics_registry,
    inc_counter,
    init_metrics,
    observe_histogram,
    set_gauge,
    time_histogram,
)
from medex.observability.models import (
    ComponentHealth,
    ComponentType,
    HealthStatus,
    LogEntry,
    LogLevel,
    MetricDefinition,
    MetricType,
    MetricValue,
    ObservabilityConfig,
    SpanContext,
    SpanData,
    SpanEvent,
    SpanKind,
    SystemHealth,
)
from medex.observability.service import (
    ObservabilityService,
    ServiceConfig,
    create_observability_service,
    get_observability_service,
    init_observability,
)
from medex.observability.tracing import (
    ConsoleSpanExporter,
    InMemorySpanExporter,
    Span,
    SpanExporter,
    Tracer,
    TracerConfig,
    async_trace_block,
    get_current_span,
    get_current_span_id,
    get_current_trace_id,
    get_tracer,
    init_tracer,
    start_span,
    trace,
    trace_block,
)

__all__ = [
    # Models
    "MetricType",
    "MetricDefinition",
    "MetricValue",
    "LogLevel",
    "LogEntry",
    "HealthStatus",
    "ComponentType",
    "ComponentHealth",
    "SystemHealth",
    "SpanKind",
    "SpanContext",
    "SpanEvent",
    "SpanData",
    "ObservabilityConfig",
    # Metrics
    "Counter",
    "Gauge",
    "Histogram",
    "HistogramTimer",
    "Summary",
    "MetricsConfig",
    "MetricsRegistry",
    "get_metrics_registry",
    "init_metrics",
    "inc_counter",
    "set_gauge",
    "observe_histogram",
    "time_histogram",
    # Logging
    "JSONFormatter",
    "TextFormatter",
    "LoggingConfig",
    "StructuredLogger",
    "configure_logging",
    "get_logger",
    "set_correlation_context",
    "get_correlation_context",
    "clear_correlation_context",
    # Health
    "HealthCheck",
    "PostgresHealthCheck",
    "RedisHealthCheck",
    "QdrantHealthCheck",
    "LLMProviderHealthCheck",
    "CallableHealthCheck",
    "HealthManager",
    "HealthManagerConfig",
    "get_health_manager",
    "init_health_manager",
    "register_health_check",
    # Tracing
    "SpanExporter",
    "ConsoleSpanExporter",
    "InMemorySpanExporter",
    "Span",
    "Tracer",
    "TracerConfig",
    "get_tracer",
    "init_tracer",
    "start_span",
    "get_current_span",
    "get_current_trace_id",
    "get_current_span_id",
    "trace",
    "trace_block",
    "async_trace_block",
    # Service
    "ServiceConfig",
    "ObservabilityService",
    "get_observability_service",
    "init_observability",
    "create_observability_service",
]
