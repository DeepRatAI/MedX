# =============================================================================
# MedeX - Admin Routes
# =============================================================================
"""
Admin endpoints for system management.

Endpoints:
- GET /metrics - Prometheus-compatible metrics
- GET /audit - Audit log entries
- POST /admin/cache/clear - Clear cache
- GET /admin/config - Get configuration
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

# =============================================================================
# Response Models
# =============================================================================


@dataclass
class MetricsResponse:
    """Prometheus-compatible metrics response."""

    metrics: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    def to_prometheus(self) -> str:
        """Format as Prometheus exposition format."""
        lines = []

        for name, data in self.metrics.items():
            metric_type = data.get("type", "gauge")
            help_text = data.get("help", "")
            value = data.get("value", 0)
            labels = data.get("labels", {})

            # HELP line
            lines.append(f"# HELP {name} {help_text}")
            lines.append(f"# TYPE {name} {metric_type}")

            # Value line with labels
            if labels:
                label_str = ",".join(f'{k}="{v}"' for k, v in labels.items())
                lines.append(f"{name}{{{label_str}}} {value}")
            else:
                lines.append(f"{name} {value}")

        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "metrics": self.metrics,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class AuditEntry:
    """Single audit log entry."""

    id: str
    event_type: str
    actor_id: str | None
    resource_type: str | None
    resource_id: str | None
    action: str
    details: dict[str, Any] = field(default_factory=dict)
    ip_address: str | None = None
    user_agent: str | None = None
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "event_type": self.event_type,
            "actor_id": self.actor_id,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "action": self.action,
            "details": self.details,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class AuditResponse:
    """Audit log response."""

    entries: list[AuditEntry] = field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 50

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "entries": [e.to_dict() for e in self.entries],
            "total": self.total,
            "page": self.page,
            "page_size": self.page_size,
            "has_more": self.total > (self.page * self.page_size),
        }


@dataclass
class ConfigResponse:
    """Configuration response (sanitized)."""

    version: str
    environment: str
    features: dict[str, bool] = field(default_factory=dict)
    limits: dict[str, int] = field(default_factory=dict)
    providers: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "version": self.version,
            "environment": self.environment,
            "features": self.features,
            "limits": self.limits,
            "providers": self.providers,
        }


@dataclass
class CacheClearResponse:
    """Cache clear response."""

    cleared: bool
    keys_removed: int = 0
    message: str = "Cache cleared successfully"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "cleared": self.cleared,
            "keys_removed": self.keys_removed,
            "message": self.message,
        }


# =============================================================================
# Admin Handler
# =============================================================================


class AdminHandler:
    """Handler for admin endpoints."""

    def __init__(self) -> None:
        """Initialize admin handler."""
        self._observability_service = None
        self._security_service = None
        self._cache_service = None

    async def get_metrics(self) -> MetricsResponse:
        """
        Get system metrics.

        Returns Prometheus-compatible metrics including:
        - Request counts
        - Latency histograms
        - Error rates
        - LLM token usage
        - Cache hit rates
        """
        # In production: metrics = await self._observability_service.get_metrics()

        metrics = {
            "medex_requests_total": {
                "type": "counter",
                "help": "Total number of requests",
                "value": 15432,
                "labels": {"status": "success"},
            },
            "medex_request_duration_seconds": {
                "type": "histogram",
                "help": "Request duration in seconds",
                "value": 1.234,
                "labels": {"quantile": "0.99"},
            },
            "medex_llm_tokens_total": {
                "type": "counter",
                "help": "Total LLM tokens used",
                "value": 1250000,
                "labels": {"provider": "groq"},
            },
            "medex_cache_hits_total": {
                "type": "counter",
                "help": "Total cache hits",
                "value": 8765,
            },
            "medex_cache_misses_total": {
                "type": "counter",
                "help": "Total cache misses",
                "value": 2341,
            },
            "medex_rag_searches_total": {
                "type": "counter",
                "help": "Total RAG searches",
                "value": 5678,
            },
            "medex_active_connections": {
                "type": "gauge",
                "help": "Current active WebSocket connections",
                "value": 42,
            },
        }

        return MetricsResponse(metrics=metrics)

    async def get_audit_logs(
        self,
        page: int = 1,
        page_size: int = 50,
        event_type: str | None = None,
        actor_id: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> AuditResponse:
        """
        Get audit log entries.

        Supports filtering by:
        - Event type
        - Actor ID
        - Date range
        """
        # In production: entries = await self._security_service.get_audit_logs(...)

        entries = [
            AuditEntry(
                id=f"audit_{i}",
                event_type="medical_query",
                actor_id="user_123",
                resource_type="query",
                resource_id=f"query_{i}",
                action="execute",
                details={"user_type": "educational"},
                ip_address="192.168.1.1",
            )
            for i in range(min(page_size, 10))
        ]

        return AuditResponse(
            entries=entries,
            total=100,
            page=page,
            page_size=page_size,
        )

    async def clear_cache(self, pattern: str | None = None) -> CacheClearResponse:
        """
        Clear cache entries.

        Args:
            pattern: Optional pattern to match keys (default: all)

        Returns:
            CacheClearResponse with count of cleared keys
        """
        # In production: result = await self._cache_service.clear(pattern)

        return CacheClearResponse(
            cleared=True,
            keys_removed=150,
            message=f"Cache cleared{f' (pattern: {pattern})' if pattern else ''}",
        )

    async def get_config(self) -> ConfigResponse:
        """
        Get system configuration (sanitized).

        Returns non-sensitive configuration for diagnostics.
        """
        return ConfigResponse(
            version="2.0.0",
            environment="production",
            features={
                "streaming": True,
                "websocket": True,
                "rag_search": True,
                "tool_calling": True,
                "pii_detection": True,
                "audit_logging": True,
            },
            limits={
                "max_query_length": 10000,
                "max_tokens": 8192,
                "rate_limit_requests": 100,
                "rate_limit_window_seconds": 60,
            },
            providers=["groq", "together", "cerebras", "ollama"],
        )


# =============================================================================
# Factory Functions
# =============================================================================


def create_admin_handler() -> AdminHandler:
    """Create admin handler with dependencies."""
    return AdminHandler()
