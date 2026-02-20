# =============================================================================
# MedeX - Metrics System
# =============================================================================
"""
Prometheus-compatible metrics system.

Provides:
- Counter, Gauge, Histogram, Summary metrics
- Automatic labeling
- Prometheus exposition format
- Async-safe operations
"""

from __future__ import annotations

import logging
import threading
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

from medex.observability.models import MetricDefinition, MetricType, MetricValue

logger = logging.getLogger(__name__)


# =============================================================================
# Metric Collectors
# =============================================================================


class Counter:
    """Prometheus-style counter metric."""

    def __init__(self, definition: MetricDefinition) -> None:
        """Initialize counter."""
        self.definition = definition
        self._values: dict[tuple[tuple[str, str], ...], float] = defaultdict(float)
        self._lock = threading.Lock()

    def inc(self, value: float = 1.0, labels: dict[str, str] | None = None) -> None:
        """Increment counter."""
        if value < 0:
            raise ValueError("Counter can only be incremented")

        label_key = self._make_label_key(labels)
        with self._lock:
            self._values[label_key] += value

    def get(self, labels: dict[str, str] | None = None) -> float:
        """Get current value."""
        label_key = self._make_label_key(labels)
        with self._lock:
            return self._values[label_key]

    def _make_label_key(
        self, labels: dict[str, str] | None
    ) -> tuple[tuple[str, str], ...]:
        """Create hashable key from labels."""
        if not labels:
            return ()
        return tuple(sorted(labels.items()))

    def collect(self) -> list[MetricValue]:
        """Collect all metric values."""
        with self._lock:
            return [
                MetricValue(
                    name=self.definition.full_name,
                    value=value,
                    labels=dict(label_key),
                )
                for label_key, value in self._values.items()
            ]


class Gauge:
    """Prometheus-style gauge metric."""

    def __init__(self, definition: MetricDefinition) -> None:
        """Initialize gauge."""
        self.definition = definition
        self._values: dict[tuple[tuple[str, str], ...], float] = defaultdict(float)
        self._lock = threading.Lock()

    def set(self, value: float, labels: dict[str, str] | None = None) -> None:
        """Set gauge value."""
        label_key = self._make_label_key(labels)
        with self._lock:
            self._values[label_key] = value

    def inc(self, value: float = 1.0, labels: dict[str, str] | None = None) -> None:
        """Increment gauge."""
        label_key = self._make_label_key(labels)
        with self._lock:
            self._values[label_key] += value

    def dec(self, value: float = 1.0, labels: dict[str, str] | None = None) -> None:
        """Decrement gauge."""
        label_key = self._make_label_key(labels)
        with self._lock:
            self._values[label_key] -= value

    def get(self, labels: dict[str, str] | None = None) -> float:
        """Get current value."""
        label_key = self._make_label_key(labels)
        with self._lock:
            return self._values[label_key]

    def _make_label_key(
        self, labels: dict[str, str] | None
    ) -> tuple[tuple[str, str], ...]:
        """Create hashable key from labels."""
        if not labels:
            return ()
        return tuple(sorted(labels.items()))

    def collect(self) -> list[MetricValue]:
        """Collect all metric values."""
        with self._lock:
            return [
                MetricValue(
                    name=self.definition.full_name,
                    value=value,
                    labels=dict(label_key),
                )
                for label_key, value in self._values.items()
            ]


class Histogram:
    """Prometheus-style histogram metric."""

    DEFAULT_BUCKETS = (
        0.005,
        0.01,
        0.025,
        0.05,
        0.075,
        0.1,
        0.25,
        0.5,
        0.75,
        1.0,
        2.5,
        5.0,
        7.5,
        10.0,
        float("inf"),
    )

    def __init__(
        self,
        definition: MetricDefinition,
        buckets: tuple[float, ...] | None = None,
    ) -> None:
        """Initialize histogram."""
        self.definition = definition
        self.buckets = buckets or self.DEFAULT_BUCKETS
        self._data: dict[tuple[tuple[str, str], ...], dict[str, Any]] = {}
        self._lock = threading.Lock()

    def observe(self, value: float, labels: dict[str, str] | None = None) -> None:
        """Record an observation."""
        label_key = self._make_label_key(labels)

        with self._lock:
            if label_key not in self._data:
                self._data[label_key] = {
                    "buckets": dict.fromkeys(self.buckets, 0),
                    "sum": 0.0,
                    "count": 0,
                }

            data = self._data[label_key]
            data["sum"] += value
            data["count"] += 1

            for bucket in self.buckets:
                if value <= bucket:
                    data["buckets"][bucket] += 1

    def time(self, labels: dict[str, str] | None = None) -> HistogramTimer:
        """Context manager for timing operations."""
        return HistogramTimer(self, labels)

    def _make_label_key(
        self, labels: dict[str, str] | None
    ) -> tuple[tuple[str, str], ...]:
        """Create hashable key from labels."""
        if not labels:
            return ()
        return tuple(sorted(labels.items()))

    def collect(self) -> list[MetricValue]:
        """Collect all metric values."""
        result = []
        base_name = self.definition.full_name

        with self._lock:
            for label_key, data in self._data.items():
                labels = dict(label_key)

                # Bucket values
                cumulative = 0
                for bucket, count in sorted(data["buckets"].items()):
                    cumulative += count
                    bucket_labels = {**labels, "le": str(bucket)}
                    result.append(
                        MetricValue(
                            name=f"{base_name}_bucket",
                            value=cumulative,
                            labels=bucket_labels,
                        )
                    )

                # Sum and count
                result.append(
                    MetricValue(
                        name=f"{base_name}_sum",
                        value=data["sum"],
                        labels=labels,
                    )
                )
                result.append(
                    MetricValue(
                        name=f"{base_name}_count",
                        value=data["count"],
                        labels=labels,
                    )
                )

        return result


class HistogramTimer:
    """Timer context manager for histogram."""

    def __init__(self, histogram: Histogram, labels: dict[str, str] | None) -> None:
        """Initialize timer."""
        self._histogram = histogram
        self._labels = labels
        self._start: float | None = None

    def __enter__(self) -> HistogramTimer:
        """Start timing."""
        self._start = time.perf_counter()
        return self

    def __exit__(self, *args: Any) -> None:
        """Stop timing and record."""
        if self._start is not None:
            duration = time.perf_counter() - self._start
            self._histogram.observe(duration, self._labels)


class Summary:
    """Prometheus-style summary metric."""

    def __init__(
        self,
        definition: MetricDefinition,
        max_age_seconds: int = 600,
    ) -> None:
        """Initialize summary."""
        self.definition = definition
        self.max_age = max_age_seconds
        self._data: dict[tuple[tuple[str, str], ...], dict[str, Any]] = {}
        self._lock = threading.Lock()

    def observe(self, value: float, labels: dict[str, str] | None = None) -> None:
        """Record an observation."""
        label_key = self._make_label_key(labels)
        now = time.time()

        with self._lock:
            if label_key not in self._data:
                self._data[label_key] = {
                    "observations": [],
                    "sum": 0.0,
                    "count": 0,
                }

            data = self._data[label_key]

            # Clean old observations
            cutoff = now - self.max_age
            data["observations"] = [
                (ts, v) for ts, v in data["observations"] if ts > cutoff
            ]

            # Add new observation
            data["observations"].append((now, value))
            data["sum"] += value
            data["count"] += 1

    def _make_label_key(
        self, labels: dict[str, str] | None
    ) -> tuple[tuple[str, str], ...]:
        """Create hashable key from labels."""
        if not labels:
            return ()
        return tuple(sorted(labels.items()))

    def collect(self) -> list[MetricValue]:
        """Collect all metric values."""
        result = []
        base_name = self.definition.full_name

        with self._lock:
            for label_key, data in self._data.items():
                labels = dict(label_key)

                result.append(
                    MetricValue(
                        name=f"{base_name}_sum",
                        value=data["sum"],
                        labels=labels,
                    )
                )
                result.append(
                    MetricValue(
                        name=f"{base_name}_count",
                        value=data["count"],
                        labels=labels,
                    )
                )

        return result


# =============================================================================
# Metrics Registry
# =============================================================================


@dataclass
class MetricsConfig:
    """Configuration for metrics."""

    prefix: str = "medex"
    enable_default_metrics: bool = True
    default_labels: dict[str, str] = field(default_factory=dict)


class MetricsRegistry:
    """Central registry for all metrics."""

    def __init__(self, config: MetricsConfig | None = None) -> None:
        """Initialize registry."""
        self.config = config or MetricsConfig()
        self._metrics: dict[str, Counter | Gauge | Histogram | Summary] = {}
        self._lock = threading.Lock()

        if self.config.enable_default_metrics:
            self._register_default_metrics()

    def _register_default_metrics(self) -> None:
        """Register default application metrics."""
        # Request metrics
        self.register_counter(
            "requests_total",
            "Total number of requests",
            labels=["method", "endpoint", "status"],
        )

        self.register_histogram(
            "request_duration_seconds",
            "Request duration in seconds",
            labels=["method", "endpoint"],
        )

        # LLM metrics
        self.register_counter(
            "llm_requests_total",
            "Total LLM API requests",
            labels=["provider", "model", "status"],
        )

        self.register_histogram(
            "llm_request_duration_seconds",
            "LLM request duration",
            labels=["provider", "model"],
        )

        self.register_counter(
            "llm_tokens_total",
            "Total tokens used",
            labels=["provider", "model", "type"],  # type: input/output
        )

        # RAG metrics
        self.register_counter(
            "rag_searches_total",
            "Total RAG searches",
            labels=["status"],
        )

        self.register_histogram(
            "rag_search_duration_seconds",
            "RAG search duration",
        )

        self.register_gauge(
            "rag_documents_indexed",
            "Number of indexed documents",
        )

        # Security metrics
        self.register_counter(
            "pii_detected_total",
            "Total PII detections",
            labels=["pii_type"],
        )

        self.register_counter(
            "security_threats_total",
            "Total security threats detected",
            labels=["threat_type"],
        )

        # System metrics
        self.register_gauge(
            "active_sessions",
            "Number of active sessions",
        )

        self.register_gauge(
            "memory_usage_bytes",
            "Memory usage in bytes",
        )

    def register_counter(
        self,
        name: str,
        description: str,
        labels: list[str] | None = None,
    ) -> Counter:
        """Register a counter metric."""
        definition = MetricDefinition(
            name=name,
            description=description,
            metric_type=MetricType.COUNTER,
            labels=labels or [],
        )

        counter = Counter(definition)
        with self._lock:
            self._metrics[name] = counter
        return counter

    def register_gauge(
        self,
        name: str,
        description: str,
        labels: list[str] | None = None,
    ) -> Gauge:
        """Register a gauge metric."""
        definition = MetricDefinition(
            name=name,
            description=description,
            metric_type=MetricType.GAUGE,
            labels=labels or [],
        )

        gauge = Gauge(definition)
        with self._lock:
            self._metrics[name] = gauge
        return gauge

    def register_histogram(
        self,
        name: str,
        description: str,
        labels: list[str] | None = None,
        buckets: tuple[float, ...] | None = None,
    ) -> Histogram:
        """Register a histogram metric."""
        definition = MetricDefinition(
            name=name,
            description=description,
            metric_type=MetricType.HISTOGRAM,
            labels=labels or [],
        )

        histogram = Histogram(definition, buckets)
        with self._lock:
            self._metrics[name] = histogram
        return histogram

    def register_summary(
        self,
        name: str,
        description: str,
        labels: list[str] | None = None,
    ) -> Summary:
        """Register a summary metric."""
        definition = MetricDefinition(
            name=name,
            description=description,
            metric_type=MetricType.SUMMARY,
            labels=labels or [],
        )

        summary = Summary(definition)
        with self._lock:
            self._metrics[name] = summary
        return summary

    def get(self, name: str) -> Counter | Gauge | Histogram | Summary | None:
        """Get metric by name."""
        return self._metrics.get(name)

    def counter(self, name: str) -> Counter | None:
        """Get counter by name."""
        metric = self._metrics.get(name)
        return metric if isinstance(metric, Counter) else None

    def gauge(self, name: str) -> Gauge | None:
        """Get gauge by name."""
        metric = self._metrics.get(name)
        return metric if isinstance(metric, Gauge) else None

    def histogram(self, name: str) -> Histogram | None:
        """Get histogram by name."""
        metric = self._metrics.get(name)
        return metric if isinstance(metric, Histogram) else None

    def collect_all(self) -> list[MetricValue]:
        """Collect all metrics."""
        result = []
        with self._lock:
            for metric in self._metrics.values():
                result.extend(metric.collect())
        return result

    def export_prometheus(self) -> str:
        """Export metrics in Prometheus format."""
        lines = []
        metrics_by_name: dict[str, list[MetricValue]] = defaultdict(list)

        # Group by metric name
        for value in self.collect_all():
            metrics_by_name[value.name].append(value)

        # Format each metric
        for name, values in sorted(metrics_by_name.items()):
            if not values:
                continue

            # Get definition
            base_name = (
                name.replace("_bucket", "").replace("_sum", "").replace("_count", "")
            )
            base_name = base_name.replace("medex_", "")
            metric = self._metrics.get(base_name)

            if metric and not name.endswith(("_bucket", "_sum", "_count")):
                lines.append(f"# HELP {name} {metric.definition.description}")
                lines.append(f"# TYPE {name} {metric.definition.metric_type.value}")

            for value in values:
                if value.labels:
                    label_str = ",".join(
                        f'{k}="{v}"' for k, v in sorted(value.labels.items())
                    )
                    lines.append(f"{name}{{{label_str}}} {value.value}")
                else:
                    lines.append(f"{name} {value.value}")

        return "\n".join(lines)


# =============================================================================
# Global Registry and Helpers
# =============================================================================

_global_registry: MetricsRegistry | None = None


def get_metrics_registry() -> MetricsRegistry:
    """Get global metrics registry."""
    global _global_registry
    if _global_registry is None:
        _global_registry = MetricsRegistry()
    return _global_registry


def init_metrics(config: MetricsConfig | None = None) -> MetricsRegistry:
    """Initialize global metrics registry."""
    global _global_registry
    _global_registry = MetricsRegistry(config)
    return _global_registry


# Convenience functions
def inc_counter(
    name: str, value: float = 1.0, labels: dict[str, str] | None = None
) -> None:
    """Increment a counter."""
    registry = get_metrics_registry()
    counter = registry.counter(name)
    if counter:
        counter.inc(value, labels)


def set_gauge(name: str, value: float, labels: dict[str, str] | None = None) -> None:
    """Set a gauge value."""
    registry = get_metrics_registry()
    gauge = registry.gauge(name)
    if gauge:
        gauge.set(value, labels)


def observe_histogram(
    name: str, value: float, labels: dict[str, str] | None = None
) -> None:
    """Record histogram observation."""
    registry = get_metrics_registry()
    histogram = registry.histogram(name)
    if histogram:
        histogram.observe(value, labels)


def time_histogram(name: str, labels: dict[str, str] | None = None) -> HistogramTimer:
    """Get timer for histogram."""
    registry = get_metrics_registry()
    histogram = registry.histogram(name)
    if histogram:
        return histogram.time(labels)
    # Return dummy timer
    return HistogramTimer(
        Histogram(MetricDefinition("dummy", "", MetricType.HISTOGRAM)),
        None,
    )
