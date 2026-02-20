# =============================================================================
# MedeX - Observability Service
# =============================================================================
"""
Unified observability service.

Integrates:
- Metrics collection and export
- Structured logging
- Distributed tracing
- Health checks
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any

from medex.observability.health import (
    CallableHealthCheck,
    HealthCheck,
    HealthManager,
    HealthManagerConfig,
    PostgresHealthCheck,
    QdrantHealthCheck,
    RedisHealthCheck,
    init_health_manager,
)
from medex.observability.logging import (
    LoggingConfig,
    StructuredLogger,
    configure_logging,
    get_logger,
    set_correlation_context,
)
from medex.observability.metrics import (
    MetricsConfig,
    MetricsRegistry,
    inc_counter,
    init_metrics,
    observe_histogram,
    set_gauge,
    time_histogram,
)
from medex.observability.models import (
    ComponentType,
    HealthStatus,
    LogLevel,
    SpanKind,
    SystemHealth,
)
from medex.observability.tracing import (
    Span,
    Tracer,
    TracerConfig,
    init_tracer,
    start_span,
    trace,
    trace_block,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Observability Service
# =============================================================================


@dataclass
class ServiceConfig:
    """Configuration for observability service."""

    service_name: str = "medex"
    service_version: str = "2.0.0"
    environment: str = "development"

    # Feature toggles
    enable_metrics: bool = True
    enable_tracing: bool = True
    enable_logging: bool = True
    enable_health_checks: bool = True

    # Metrics
    metrics_prefix: str = "medex"

    # Tracing
    trace_sample_rate: float = 1.0
    trace_export_console: bool = False

    # Logging
    log_level: LogLevel = LogLevel.INFO
    log_format: str = "json"
    log_to_file: bool = False
    log_file_path: str = "/var/log/medex/app.log"


class ObservabilityService:
    """
    Unified observability service for MedeX.

    Provides a single interface for:
    - Metrics (Prometheus-compatible)
    - Tracing (OpenTelemetry-compatible)
    - Logging (Structured JSON)
    - Health Checks (Kubernetes-ready)
    """

    def __init__(self, config: ServiceConfig | None = None) -> None:
        """Initialize observability service."""
        self.config = config or ServiceConfig()
        self._start_time = time.time()

        # Initialize components
        self._metrics: MetricsRegistry | None = None
        self._tracer: Tracer | None = None
        self._health: HealthManager | None = None
        self._logger: StructuredLogger | None = None

        self._initialize()
        logger.info(
            f"Observability service initialized for {self.config.service_name} "
            f"v{self.config.service_version}"
        )

    def _initialize(self) -> None:
        """Initialize all observability components."""
        # Logging (first, so other components can log)
        if self.config.enable_logging:
            configure_logging(
                LoggingConfig(
                    level=self.config.log_level,
                    format=self.config.log_format,
                    log_to_file=self.config.log_to_file,
                    file_path=self.config.log_file_path,
                )
            )
            self._logger = get_logger(self.config.service_name)

        # Metrics
        if self.config.enable_metrics:
            self._metrics = init_metrics(
                MetricsConfig(
                    prefix=self.config.metrics_prefix,
                    enable_default_metrics=True,
                )
            )

        # Tracing
        if self.config.enable_tracing:
            self._tracer = init_tracer(
                TracerConfig(
                    service_name=self.config.service_name,
                    environment=self.config.environment,
                    sample_rate=self.config.trace_sample_rate,
                    enable_console_export=self.config.trace_export_console,
                )
            )

        # Health checks
        if self.config.enable_health_checks:
            self._health = init_health_manager(
                HealthManagerConfig(
                    service_name=self.config.service_name,
                    service_version=self.config.service_version,
                )
            )

    # -------------------------------------------------------------------------
    # Metrics API
    # -------------------------------------------------------------------------

    def inc_counter(
        self,
        name: str,
        value: float = 1.0,
        labels: dict[str, str] | None = None,
    ) -> None:
        """Increment a counter metric."""
        if self._metrics:
            inc_counter(name, value, labels)

    def set_gauge(
        self,
        name: str,
        value: float,
        labels: dict[str, str] | None = None,
    ) -> None:
        """Set a gauge metric."""
        if self._metrics:
            set_gauge(name, value, labels)

    def observe(
        self,
        name: str,
        value: float,
        labels: dict[str, str] | None = None,
    ) -> None:
        """Record histogram observation."""
        if self._metrics:
            observe_histogram(name, value, labels)

    def time(self, name: str, labels: dict[str, str] | None = None):
        """Get timer context manager for histogram."""
        return time_histogram(name, labels)

    def get_metrics_prometheus(self) -> str:
        """Export metrics in Prometheus format."""
        if self._metrics:
            return self._metrics.export_prometheus()
        return ""

    # -------------------------------------------------------------------------
    # Tracing API
    # -------------------------------------------------------------------------

    def start_span(
        self,
        name: str,
        kind: SpanKind = SpanKind.INTERNAL,
        attributes: dict[str, Any] | None = None,
    ) -> Span:
        """Start a new trace span."""
        return start_span(name, kind, attributes)

    def trace(
        self,
        name: str | None = None,
        kind: SpanKind = SpanKind.INTERNAL,
    ):
        """Decorator for tracing functions."""
        return trace(name, kind)

    def trace_block(
        self,
        name: str,
        kind: SpanKind = SpanKind.INTERNAL,
        attributes: dict[str, Any] | None = None,
    ):
        """Context manager for tracing code blocks."""
        return trace_block(name, kind, attributes)

    # -------------------------------------------------------------------------
    # Logging API
    # -------------------------------------------------------------------------

    def get_logger(self, name: str) -> StructuredLogger:
        """Get a structured logger."""
        return get_logger(name)

    def set_context(
        self,
        trace_id: str | None = None,
        span_id: str | None = None,
        user_id: str | None = None,
        session_id: str | None = None,
        request_id: str | None = None,
    ) -> None:
        """Set correlation context for logging."""
        set_correlation_context(
            trace_id=trace_id,
            span_id=span_id,
            user_id=user_id,
            session_id=session_id,
            request_id=request_id,
        )

    # -------------------------------------------------------------------------
    # Health Check API
    # -------------------------------------------------------------------------

    def register_health_check(self, check: HealthCheck) -> None:
        """Register a health check."""
        if self._health:
            self._health.register(check)

    def register_postgres(
        self,
        connection_string: str | None = None,
        pool: Any = None,
    ) -> None:
        """Register PostgreSQL health check."""
        if self._health:
            self._health.register(PostgresHealthCheck(connection_string, pool))

    def register_redis(
        self,
        url: str | None = None,
        client: Any = None,
    ) -> None:
        """Register Redis health check."""
        if self._health:
            self._health.register(RedisHealthCheck(url, client))

    def register_qdrant(
        self,
        url: str | None = None,
        client: Any = None,
    ) -> None:
        """Register Qdrant health check."""
        if self._health:
            self._health.register(QdrantHealthCheck(url, client))

    def register_custom_check(
        self,
        name: str,
        check_fn: Any,
        component_type: ComponentType = ComponentType.EXTERNAL_API,
        critical: bool = False,
    ) -> None:
        """Register a custom health check."""
        if self._health:
            self._health.register(
                CallableHealthCheck(name, component_type, check_fn, critical)
            )

    async def check_health(self) -> SystemHealth:
        """Run all health checks."""
        if self._health:
            return await self._health.check_all()
        return SystemHealth(
            status=HealthStatus.UNKNOWN,
            version=self.config.service_version,
            uptime_seconds=self.uptime_seconds,
        )

    async def liveness(self) -> tuple[bool, str]:
        """Kubernetes liveness probe."""
        if self._health:
            return await self._health.liveness_probe()
        return True, "Running"

    async def readiness(self) -> tuple[bool, str]:
        """Kubernetes readiness probe."""
        if self._health:
            return await self._health.readiness_probe()
        return True, "Ready"

    # -------------------------------------------------------------------------
    # Convenience Methods
    # -------------------------------------------------------------------------

    def track_request(
        self,
        method: str,
        path: str,
        status: int,
        duration_seconds: float,
    ) -> None:
        """Track an HTTP request."""
        labels = {"method": method, "endpoint": path, "status": str(status)}
        self.inc_counter("requests_total", labels=labels)
        self.observe(
            "request_duration_seconds",
            duration_seconds,
            {"method": method, "endpoint": path},
        )

    def track_llm_request(
        self,
        provider: str,
        model: str,
        status: str,
        duration_seconds: float,
        tokens_in: int = 0,
        tokens_out: int = 0,
    ) -> None:
        """Track an LLM API request."""
        self.inc_counter(
            "llm_requests_total",
            labels={"provider": provider, "model": model, "status": status},
        )
        self.observe(
            "llm_request_duration_seconds",
            duration_seconds,
            {"provider": provider, "model": model},
        )

        if tokens_in:
            self.inc_counter(
                "llm_tokens_total",
                tokens_in,
                {"provider": provider, "model": model, "type": "input"},
            )
        if tokens_out:
            self.inc_counter(
                "llm_tokens_total",
                tokens_out,
                {"provider": provider, "model": model, "type": "output"},
            )

    def track_rag_search(
        self,
        status: str,
        duration_seconds: float,
    ) -> None:
        """Track a RAG search."""
        self.inc_counter("rag_searches_total", labels={"status": status})
        self.observe("rag_search_duration_seconds", duration_seconds)

    def track_pii_detection(self, pii_type: str) -> None:
        """Track PII detection."""
        self.inc_counter("pii_detected_total", labels={"pii_type": pii_type})

    def track_security_threat(self, threat_type: str) -> None:
        """Track security threat detection."""
        self.inc_counter("security_threats_total", labels={"threat_type": threat_type})

    @property
    def uptime_seconds(self) -> float:
        """Get service uptime in seconds."""
        return time.time() - self._start_time

    def shutdown(self) -> None:
        """Shutdown observability service."""
        if self._tracer:
            self._tracer.shutdown()
        logger.info("Observability service shutdown")


# =============================================================================
# Factory Functions
# =============================================================================

_global_service: ObservabilityService | None = None


def get_observability_service() -> ObservabilityService | None:
    """Get global observability service."""
    return _global_service


def init_observability(
    config: ServiceConfig | None = None,
) -> ObservabilityService:
    """Initialize global observability service."""
    global _global_service
    _global_service = ObservabilityService(config)
    return _global_service


def create_observability_service(
    config: ServiceConfig | None = None,
) -> ObservabilityService:
    """Create observability service (non-global)."""
    return ObservabilityService(config)
