# =============================================================================
# MedeX - Tracing
# =============================================================================
"""
Distributed tracing system.

Provides:
- OpenTelemetry-compatible tracing
- Span creation and context propagation
- Trace exporters
- Decorator-based instrumentation
"""

from __future__ import annotations

import asyncio
import contextvars
import functools
import logging
import secrets
from collections.abc import AsyncGenerator, Generator
from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from medex.observability.models import SpanContext, SpanData, SpanKind

logger = logging.getLogger(__name__)


# =============================================================================
# Context Propagation
# =============================================================================

_current_span: contextvars.ContextVar[SpanData | None] = contextvars.ContextVar(
    "current_span", default=None
)


def get_current_span() -> SpanData | None:
    """Get the current active span."""
    return _current_span.get()


def get_current_trace_id() -> str | None:
    """Get current trace ID."""
    span = get_current_span()
    return span.context.trace_id if span else None


def get_current_span_id() -> str | None:
    """Get current span ID."""
    span = get_current_span()
    return span.context.span_id if span else None


# =============================================================================
# ID Generation
# =============================================================================


def generate_trace_id() -> str:
    """Generate a new trace ID (32 hex chars)."""
    return secrets.token_hex(16)


def generate_span_id() -> str:
    """Generate a new span ID (16 hex chars)."""
    return secrets.token_hex(8)


# =============================================================================
# Span Implementation
# =============================================================================


class Span:
    """
    A span represents a single operation within a trace.

    Implements context manager protocol for easy usage:
        with tracer.start_span("operation") as span:
            span.set_attribute("key", "value")
            do_work()
    """

    def __init__(
        self,
        name: str,
        kind: SpanKind = SpanKind.INTERNAL,
        parent_context: SpanContext | None = None,
        attributes: dict[str, Any] | None = None,
    ) -> None:
        """Initialize span."""
        # Create context
        parent_span = get_current_span()

        if parent_context:
            trace_id = parent_context.trace_id
            parent_span_id = parent_context.span_id
        elif parent_span:
            trace_id = parent_span.context.trace_id
            parent_span_id = parent_span.context.span_id
        else:
            trace_id = generate_trace_id()
            parent_span_id = None

        self._data = SpanData(
            name=name,
            context=SpanContext(
                trace_id=trace_id,
                span_id=generate_span_id(),
                parent_span_id=parent_span_id,
            ),
            kind=kind,
            start_time=datetime.now(),
            attributes=attributes or {},
        )

        self._token: contextvars.Token[SpanData | None] | None = None
        self._ended = False

    @property
    def trace_id(self) -> str:
        """Get trace ID."""
        return self._data.context.trace_id

    @property
    def span_id(self) -> str:
        """Get span ID."""
        return self._data.context.span_id

    @property
    def name(self) -> str:
        """Get span name."""
        return self._data.name

    @property
    def duration_ms(self) -> float | None:
        """Get span duration in milliseconds."""
        return self._data.duration_ms

    def set_attribute(self, key: str, value: Any) -> Span:
        """Set span attribute."""
        self._data.attributes[key] = value
        return self

    def set_attributes(self, attributes: dict[str, Any]) -> Span:
        """Set multiple span attributes."""
        self._data.attributes.update(attributes)
        return self

    def add_event(
        self,
        name: str,
        attributes: dict[str, Any] | None = None,
    ) -> Span:
        """Add event to span."""
        self._data.add_event(name, attributes)
        return self

    def set_status(self, status: str, message: str | None = None) -> Span:
        """Set span status."""
        self._data.status_code = status
        if message:
            self._data.status_message = message
        return self

    def set_error(self, error: Exception | str) -> Span:
        """Mark span as error."""
        if isinstance(error, Exception):
            self._data.set_error(f"{type(error).__name__}: {str(error)}")
            self.add_event(
                "exception",
                {
                    "exception.type": type(error).__name__,
                    "exception.message": str(error),
                },
            )
        else:
            self._data.set_error(error)
        return self

    def start(self) -> Span:
        """Start the span and set as current."""
        self._token = _current_span.set(self._data)
        return self

    def end(self) -> None:
        """End the span."""
        if self._ended:
            return

        self._data.end_time = datetime.now()
        self._ended = True

        # Restore previous span
        if self._token:
            _current_span.reset(self._token)

        # Export span
        tracer = get_tracer()
        if tracer:
            tracer._export_span(self._data)

    def __enter__(self) -> Span:
        """Enter context manager."""
        return self.start()

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit context manager."""
        if exc_val:
            self.set_error(exc_val)
        self.end()

    async def __aenter__(self) -> Span:
        """Enter async context manager."""
        return self.start()

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit async context manager."""
        if exc_val:
            self.set_error(exc_val)
        self.end()


# =============================================================================
# Span Exporter
# =============================================================================


class SpanExporter:
    """Base class for span exporters."""

    def export(self, spans: list[SpanData]) -> None:
        """Export spans."""
        pass

    def shutdown(self) -> None:
        """Shutdown exporter."""
        pass


class ConsoleSpanExporter(SpanExporter):
    """Export spans to console."""

    def __init__(self, pretty: bool = True) -> None:
        """Initialize console exporter."""
        self.pretty = pretty

    def export(self, spans: list[SpanData]) -> None:
        """Export spans to console."""
        for span in spans:
            duration = span.duration_ms or 0
            status = "✓" if span.status_code == "OK" else "✗"

            if self.pretty:
                indent = "  " if span.context.parent_span_id else ""
                print(
                    f"{indent}[{status}] {span.name} "
                    f"({duration:.2f}ms) "
                    f"trace={span.context.trace_id[:8]}..."
                )
            else:
                print(
                    f"SPAN: name={span.name} "
                    f"trace_id={span.context.trace_id} "
                    f"span_id={span.context.span_id} "
                    f"duration_ms={duration:.2f} "
                    f"status={span.status_code}"
                )


class InMemorySpanExporter(SpanExporter):
    """Store spans in memory for testing."""

    def __init__(self, max_spans: int = 1000) -> None:
        """Initialize in-memory exporter."""
        self.max_spans = max_spans
        self._spans: list[SpanData] = []

    def export(self, spans: list[SpanData]) -> None:
        """Store spans in memory."""
        self._spans.extend(spans)

        # Trim if needed
        if len(self._spans) > self.max_spans:
            self._spans = self._spans[-self.max_spans :]

    def get_spans(self) -> list[SpanData]:
        """Get stored spans."""
        return self._spans.copy()

    def clear(self) -> None:
        """Clear stored spans."""
        self._spans.clear()

    def find_by_name(self, name: str) -> list[SpanData]:
        """Find spans by name."""
        return [s for s in self._spans if s.name == name]

    def find_by_trace(self, trace_id: str) -> list[SpanData]:
        """Find spans by trace ID."""
        return [s for s in self._spans if s.context.trace_id == trace_id]


# =============================================================================
# Tracer
# =============================================================================


@dataclass
class TracerConfig:
    """Configuration for tracer."""

    service_name: str = "medex"
    environment: str = "development"
    sample_rate: float = 1.0  # 0.0 to 1.0

    # Exporters
    enable_console_export: bool = False
    enable_memory_export: bool = True

    # Batching
    batch_size: int = 100
    batch_timeout_seconds: float = 5.0


class Tracer:
    """
    Distributed tracer for MedeX.

    Creates and manages spans for distributed tracing.
    """

    def __init__(self, config: TracerConfig | None = None) -> None:
        """Initialize tracer."""
        self.config = config or TracerConfig()
        self._exporters: list[SpanExporter] = []
        self._pending_spans: list[SpanData] = []

        # Initialize default exporters
        if self.config.enable_console_export:
            self._exporters.append(ConsoleSpanExporter())
        if self.config.enable_memory_export:
            self._memory_exporter = InMemorySpanExporter()
            self._exporters.append(self._memory_exporter)

        logger.info(f"Tracer initialized for service: {self.config.service_name}")

    def start_span(
        self,
        name: str,
        kind: SpanKind = SpanKind.INTERNAL,
        attributes: dict[str, Any] | None = None,
    ) -> Span:
        """
        Start a new span.

        Args:
            name: Span name
            kind: Span kind (INTERNAL, SERVER, CLIENT, etc.)
            attributes: Initial attributes

        Returns:
            Span instance
        """
        # Check sampling
        if not self._should_sample():
            # Return a no-op span
            return Span(name, kind, attributes=attributes)

        span = Span(name, kind, attributes=attributes)

        # Add default attributes
        span.set_attributes(
            {
                "service.name": self.config.service_name,
                "service.environment": self.config.environment,
            }
        )

        return span

    def _should_sample(self) -> bool:
        """Check if this trace should be sampled."""
        if self.config.sample_rate >= 1.0:
            return True
        if self.config.sample_rate <= 0.0:
            return False

        import random

        return random.random() < self.config.sample_rate

    def _export_span(self, span: SpanData) -> None:
        """Export a completed span."""
        self._pending_spans.append(span)

        # Flush if batch is full
        if len(self._pending_spans) >= self.config.batch_size:
            self.flush()

    def flush(self) -> None:
        """Flush pending spans to exporters."""
        if not self._pending_spans:
            return

        spans = self._pending_spans.copy()
        self._pending_spans.clear()

        for exporter in self._exporters:
            try:
                exporter.export(spans)
            except Exception as e:
                logger.error(f"Failed to export spans: {e}")

    def add_exporter(self, exporter: SpanExporter) -> None:
        """Add span exporter."""
        self._exporters.append(exporter)

    def get_memory_spans(self) -> list[SpanData]:
        """Get spans from memory exporter."""
        if hasattr(self, "_memory_exporter"):
            return self._memory_exporter.get_spans()
        return []

    def shutdown(self) -> None:
        """Shutdown tracer."""
        self.flush()
        for exporter in self._exporters:
            exporter.shutdown()


# =============================================================================
# Global Tracer
# =============================================================================

_global_tracer: Tracer | None = None


def get_tracer() -> Tracer | None:
    """Get global tracer."""
    return _global_tracer


def init_tracer(config: TracerConfig | None = None) -> Tracer:
    """Initialize global tracer."""
    global _global_tracer
    _global_tracer = Tracer(config)
    return _global_tracer


def start_span(
    name: str,
    kind: SpanKind = SpanKind.INTERNAL,
    attributes: dict[str, Any] | None = None,
) -> Span:
    """Start a span using global tracer."""
    tracer = get_tracer()
    if tracer:
        return tracer.start_span(name, kind, attributes)
    return Span(name, kind, attributes=attributes)


# =============================================================================
# Instrumentation Decorators
# =============================================================================


def trace(
    name: str | None = None,
    kind: SpanKind = SpanKind.INTERNAL,
    attributes: dict[str, Any] | None = None,
):
    """
    Decorator to trace a function.

    Usage:
        @trace("my_operation")
        def my_function():
            pass

        @trace()
        async def my_async_function():
            pass
    """

    def decorator(func):
        span_name = name or func.__name__

        if asyncio.iscoroutinefunction(func):

            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                with start_span(span_name, kind, attributes) as span:
                    try:
                        result = await func(*args, **kwargs)
                        return result
                    except Exception as e:
                        span.set_error(e)
                        raise

            return async_wrapper
        else:

            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                with start_span(span_name, kind, attributes) as span:
                    try:
                        result = func(*args, **kwargs)
                        return result
                    except Exception as e:
                        span.set_error(e)
                        raise

            return sync_wrapper

    return decorator


@contextmanager
def trace_block(
    name: str,
    kind: SpanKind = SpanKind.INTERNAL,
    attributes: dict[str, Any] | None = None,
) -> Generator[Span, None, None]:
    """
    Context manager for tracing a code block.

    Usage:
        with trace_block("my_operation") as span:
            span.set_attribute("key", "value")
            do_work()
    """
    with start_span(name, kind, attributes) as span:
        yield span


@asynccontextmanager
async def async_trace_block(
    name: str,
    kind: SpanKind = SpanKind.INTERNAL,
    attributes: dict[str, Any] | None = None,
) -> AsyncGenerator[Span, None]:
    """
    Async context manager for tracing a code block.

    Usage:
        async with async_trace_block("my_operation") as span:
            span.set_attribute("key", "value")
            await do_async_work()
    """
    span = start_span(name, kind, attributes)
    span.start()
    try:
        yield span
    except Exception as e:
        span.set_error(e)
        raise
    finally:
        span.end()
