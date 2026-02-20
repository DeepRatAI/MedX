# =============================================================================
# MedeX - Observability Tests
# =============================================================================
"""
Comprehensive tests for the observability module.

Tests cover:
- Metrics collection
- Structured logging
- Distributed tracing
- Health checks
"""

from __future__ import annotations

import pytest

from medex.observability.health import (
    CallableHealthCheck,
    HealthManager,
    HealthManagerConfig,
)
from medex.observability.logging import (
    StructuredLogger,
    clear_correlation_context,
    get_logger,
    set_correlation_context,
)
from medex.observability.metrics import (
    MetricsConfig,
    MetricsRegistry,
)
from medex.observability.models import (
    ComponentType,
    HealthStatus,
)
from medex.observability.service import (
    ObservabilityService,
    ServiceConfig,
)
from medex.observability.tracing import (
    Tracer,
    TracerConfig,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def metrics_registry() -> MetricsRegistry:
    """Create metrics registry."""
    return MetricsRegistry(MetricsConfig(enable_default_metrics=False))


@pytest.fixture
def tracer() -> Tracer:
    """Create tracer."""
    return Tracer(
        TracerConfig(
            enable_console_export=False,
            enable_memory_export=True,
        )
    )


@pytest.fixture
def health_manager() -> HealthManager:
    """Create health manager."""
    return HealthManager(HealthManagerConfig())


@pytest.fixture
def observability_service() -> ObservabilityService:
    """Create observability service."""
    return ObservabilityService(
        ServiceConfig(
            enable_metrics=True,
            enable_tracing=True,
            enable_logging=False,  # Don't mess with global logging in tests
            enable_health_checks=True,
        )
    )


# =============================================================================
# Counter Tests
# =============================================================================


class TestCounter:
    """Tests for Counter metric."""

    def test_increment(self, metrics_registry: MetricsRegistry) -> None:
        """Test counter increment."""
        counter = metrics_registry.register_counter("test_counter", "Test counter")

        counter.inc()
        assert counter.get() == 1.0

        counter.inc(5.0)
        assert counter.get() == 6.0

    def test_increment_with_labels(self, metrics_registry: MetricsRegistry) -> None:
        """Test counter with labels."""
        counter = metrics_registry.register_counter(
            "test_counter_labels",
            "Test counter with labels",
            labels=["method", "status"],
        )

        counter.inc(labels={"method": "GET", "status": "200"})
        counter.inc(labels={"method": "GET", "status": "200"})
        counter.inc(labels={"method": "POST", "status": "201"})

        assert counter.get({"method": "GET", "status": "200"}) == 2.0
        assert counter.get({"method": "POST", "status": "201"}) == 1.0

    def test_cannot_decrement(self, metrics_registry: MetricsRegistry) -> None:
        """Test counter cannot be decremented."""
        counter = metrics_registry.register_counter("test_counter_dec", "Test")

        with pytest.raises(ValueError):
            counter.inc(-1.0)


# =============================================================================
# Gauge Tests
# =============================================================================


class TestGauge:
    """Tests for Gauge metric."""

    def test_set(self, metrics_registry: MetricsRegistry) -> None:
        """Test gauge set."""
        gauge = metrics_registry.register_gauge("test_gauge", "Test gauge")

        gauge.set(42.0)
        assert gauge.get() == 42.0

        gauge.set(100.0)
        assert gauge.get() == 100.0

    def test_increment_decrement(self, metrics_registry: MetricsRegistry) -> None:
        """Test gauge increment and decrement."""
        gauge = metrics_registry.register_gauge("test_gauge_incdec", "Test")

        gauge.set(10.0)
        gauge.inc(5.0)
        assert gauge.get() == 15.0

        gauge.dec(3.0)
        assert gauge.get() == 12.0

    def test_with_labels(self, metrics_registry: MetricsRegistry) -> None:
        """Test gauge with labels."""
        gauge = metrics_registry.register_gauge(
            "test_gauge_labels",
            "Test",
            labels=["host"],
        )

        gauge.set(100.0, {"host": "server1"})
        gauge.set(200.0, {"host": "server2"})

        assert gauge.get({"host": "server1"}) == 100.0
        assert gauge.get({"host": "server2"}) == 200.0


# =============================================================================
# Histogram Tests
# =============================================================================


class TestHistogram:
    """Tests for Histogram metric."""

    def test_observe(self, metrics_registry: MetricsRegistry) -> None:
        """Test histogram observation."""
        histogram = metrics_registry.register_histogram(
            "test_histogram",
            "Test histogram",
        )

        histogram.observe(0.1)
        histogram.observe(0.5)
        histogram.observe(1.0)

        values = histogram.collect()
        # Should have bucket, sum, and count values
        assert len(values) > 0

    def test_timer_context_manager(self, metrics_registry: MetricsRegistry) -> None:
        """Test histogram timer."""
        import time

        histogram = metrics_registry.register_histogram(
            "test_histogram_timer",
            "Test timer",
        )

        with histogram.time():
            time.sleep(0.01)

        values = histogram.collect()
        # Find the sum value
        sum_value = next((v for v in values if "_sum" in v.name), None)
        assert sum_value is not None
        assert sum_value.value > 0


# =============================================================================
# Metrics Registry Tests
# =============================================================================


class TestMetricsRegistry:
    """Tests for MetricsRegistry."""

    def test_register_and_get(self, metrics_registry: MetricsRegistry) -> None:
        """Test registering and getting metrics."""
        counter = metrics_registry.register_counter("my_counter", "Test")
        gauge = metrics_registry.register_gauge("my_gauge", "Test")

        assert metrics_registry.counter("my_counter") is counter
        assert metrics_registry.gauge("my_gauge") is gauge

    def test_collect_all(self, metrics_registry: MetricsRegistry) -> None:
        """Test collecting all metrics."""
        counter = metrics_registry.register_counter("col_counter", "Test")
        gauge = metrics_registry.register_gauge("col_gauge", "Test")

        counter.inc(5.0)
        gauge.set(42.0)

        values = metrics_registry.collect_all()
        assert len(values) >= 2

    def test_prometheus_export(self, metrics_registry: MetricsRegistry) -> None:
        """Test Prometheus format export."""
        counter = metrics_registry.register_counter("prom_counter", "Test counter")
        counter.inc(10.0)

        output = metrics_registry.export_prometheus()
        assert "medex_prom_counter" in output
        assert "10" in output


# =============================================================================
# Tracing Tests
# =============================================================================


class TestTracing:
    """Tests for distributed tracing."""

    def test_create_span(self, tracer: Tracer) -> None:
        """Test span creation."""
        with tracer.start_span("test_operation") as span:
            span.set_attribute("key", "value")

        spans = tracer.get_memory_spans()
        assert len(spans) >= 1
        assert spans[-1].name == "test_operation"

    def test_nested_spans(self, tracer: Tracer) -> None:
        """Test nested spans share trace ID."""
        with tracer.start_span("parent") as parent:
            with tracer.start_span("child") as child:
                pass

        tracer.flush()
        spans = tracer.get_memory_spans()

        # Both spans should have the same trace ID
        parent_span = next((s for s in spans if s.name == "parent"), None)
        child_span = next((s for s in spans if s.name == "child"), None)

        assert parent_span is not None
        assert child_span is not None
        assert parent_span.context.trace_id == child_span.context.trace_id
        assert child_span.context.parent_span_id == parent_span.context.span_id

    def test_span_attributes(self, tracer: Tracer) -> None:
        """Test span attributes."""
        with tracer.start_span("attributed") as span:
            span.set_attribute("user_id", "123")
            span.set_attributes({"action": "query", "count": 5})

        tracer.flush()
        spans = tracer.get_memory_spans()
        span_data = next((s for s in spans if s.name == "attributed"), None)

        assert span_data is not None
        assert span_data.attributes.get("user_id") == "123"
        assert span_data.attributes.get("action") == "query"

    def test_span_error(self, tracer: Tracer) -> None:
        """Test span error handling."""
        try:
            with tracer.start_span("error_span") as span:
                raise ValueError("Test error")
        except ValueError:
            pass

        tracer.flush()
        spans = tracer.get_memory_spans()
        span_data = next((s for s in spans if s.name == "error_span"), None)

        assert span_data is not None
        assert span_data.status_code == "ERROR"

    def test_span_duration(self, tracer: Tracer) -> None:
        """Test span duration calculation."""
        import time

        with tracer.start_span("timed_span") as span:
            time.sleep(0.01)

        tracer.flush()
        spans = tracer.get_memory_spans()
        span_data = next((s for s in spans if s.name == "timed_span"), None)

        assert span_data is not None
        assert span_data.duration_ms is not None
        assert span_data.duration_ms > 0


# =============================================================================
# Health Check Tests
# =============================================================================


class TestHealthChecks:
    """Tests for health checks."""

    @pytest.mark.asyncio
    async def test_healthy_check(self, health_manager: HealthManager) -> None:
        """Test healthy component."""
        health_manager.register(
            CallableHealthCheck(
                name="healthy_service",
                component_type=ComponentType.EXTERNAL_API,
                check_fn=lambda: True,
            )
        )

        health = await health_manager.check_all()
        assert health.status == HealthStatus.HEALTHY

    @pytest.mark.asyncio
    async def test_unhealthy_check(self, health_manager: HealthManager) -> None:
        """Test unhealthy component."""
        health_manager.register(
            CallableHealthCheck(
                name="unhealthy_service",
                component_type=ComponentType.DATABASE,
                check_fn=lambda: False,
                critical=True,
            )
        )

        health = await health_manager.check_all()
        assert health.status == HealthStatus.UNHEALTHY

    @pytest.mark.asyncio
    async def test_mixed_health(self, health_manager: HealthManager) -> None:
        """Test mixed health status."""
        # Non-critical failure -> degraded
        health_manager.register(
            CallableHealthCheck(
                name="healthy_db",
                component_type=ComponentType.DATABASE,
                check_fn=lambda: True,
                critical=True,
            )
        )
        health_manager.register(
            CallableHealthCheck(
                name="unhealthy_cache",
                component_type=ComponentType.CACHE,
                check_fn=lambda: False,
                critical=False,
            )
        )

        health = await health_manager.check_all()
        assert health.status == HealthStatus.DEGRADED

    @pytest.mark.asyncio
    async def test_liveness_probe(self, health_manager: HealthManager) -> None:
        """Test liveness probe."""
        alive, message = await health_manager.liveness_probe()
        assert alive

    @pytest.mark.asyncio
    async def test_readiness_probe(self, health_manager: HealthManager) -> None:
        """Test readiness probe."""
        health_manager.register(
            CallableHealthCheck(
                name="service",
                component_type=ComponentType.DATABASE,
                check_fn=lambda: True,
                critical=True,
            )
        )

        ready, message = await health_manager.readiness_probe()
        assert ready


# =============================================================================
# Logging Tests
# =============================================================================


class TestLogging:
    """Tests for structured logging."""

    def test_get_logger(self) -> None:
        """Test getting a logger."""
        logger = get_logger("test_module")
        assert isinstance(logger, StructuredLogger)

    def test_correlation_context(self) -> None:
        """Test setting correlation context."""
        set_correlation_context(
            trace_id="abc123",
            user_id="user_456",
        )

        from medex.observability.logging import get_correlation_context

        ctx = get_correlation_context()

        assert ctx["trace_id"] == "abc123"
        assert ctx["user_id"] == "user_456"

        clear_correlation_context()


# =============================================================================
# Observability Service Tests
# =============================================================================


class TestObservabilityService:
    """Integration tests for observability service."""

    def test_track_request(self, observability_service: ObservabilityService) -> None:
        """Test tracking HTTP request."""
        observability_service.track_request("GET", "/api/query", 200, 0.150)

        # Check metrics were recorded
        metrics = observability_service.get_metrics_prometheus()
        assert "requests_total" in metrics or len(metrics) > 0

    def test_track_llm_request(
        self, observability_service: ObservabilityService
    ) -> None:
        """Test tracking LLM request."""
        observability_service.track_llm_request(
            provider="kimi",
            model="k2",
            status="success",
            duration_seconds=1.5,
            tokens_in=100,
            tokens_out=500,
        )

        # Check metrics were recorded
        metrics = observability_service.get_metrics_prometheus()
        assert len(metrics) > 0

    def test_start_span(self, observability_service: ObservabilityService) -> None:
        """Test starting a span."""
        with observability_service.start_span("test_op") as span:
            span.set_attribute("key", "value")

        # Span should complete without error
        assert True

    @pytest.mark.asyncio
    async def test_check_health(
        self, observability_service: ObservabilityService
    ) -> None:
        """Test health check."""
        health = await observability_service.check_health()
        assert health.status in [HealthStatus.HEALTHY, HealthStatus.UNKNOWN]

    def test_uptime(self, observability_service: ObservabilityService) -> None:
        """Test uptime tracking."""
        uptime = observability_service.uptime_seconds
        assert uptime >= 0


# =============================================================================
# Performance Tests
# =============================================================================


class TestPerformance:
    """Performance tests for observability."""

    def test_counter_performance(self, metrics_registry: MetricsRegistry) -> None:
        """Test counter performance."""
        import time

        counter = metrics_registry.register_counter("perf_counter", "Test")

        start = time.time()
        for _ in range(10000):
            counter.inc()
        elapsed = time.time() - start

        # Should complete 10000 increments in under 1 second
        assert elapsed < 1.0

    def test_span_creation_performance(self, tracer: Tracer) -> None:
        """Test span creation performance."""
        import time

        start = time.time()
        for i in range(1000):
            with tracer.start_span(f"span_{i}"):
                pass
        elapsed = time.time() - start

        # Should complete 1000 spans in under 1 second
        assert elapsed < 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
