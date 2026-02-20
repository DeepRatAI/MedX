# =============================================================================
# MedeX - Health Routes
# =============================================================================
"""
Health check endpoints for Kubernetes probes and monitoring.

Endpoints:
- GET /health - Overall health status
- GET /ready - Readiness probe
- GET /live - Liveness probe
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Protocol


# =============================================================================
# Health Status
# =============================================================================


class HealthStatus(str, Enum):
    """Health check status values."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class ComponentHealth:
    """Health status of a component."""

    name: str
    status: HealthStatus
    latency_ms: float = 0
    message: str | None = None
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "status": self.status.value,
            "latency_ms": round(self.latency_ms, 2),
            "message": self.message,
            "details": self.details,
        }


@dataclass
class HealthCheckResponse:
    """Complete health check response."""

    status: HealthStatus
    version: str
    uptime_seconds: float
    components: list[ComponentHealth] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "status": self.status.value,
            "version": self.version,
            "uptime_seconds": round(self.uptime_seconds, 2),
            "components": [c.to_dict() for c in self.components],
            "timestamp": self.timestamp.isoformat(),
        }


# =============================================================================
# Health Check Protocols
# =============================================================================


class HealthCheckProtocol(Protocol):
    """Protocol for health check implementations."""

    @property
    def name(self) -> str:
        """Component name."""
        ...

    async def check(self) -> ComponentHealth:
        """Perform health check."""
        ...


# =============================================================================
# Health Check Implementations
# =============================================================================


class DatabaseHealthCheck:
    """Health check for PostgreSQL database."""

    def __init__(self, connection_string: str | None = None) -> None:
        """Initialize database health check."""
        self._connection_string = connection_string
        self._name = "postgresql"

    @property
    def name(self) -> str:
        """Get component name."""
        return self._name

    async def check(self) -> ComponentHealth:
        """Check database connectivity."""
        start = time.time()

        try:
            # Simulate database ping (real implementation would use asyncpg)
            # In production: await pool.fetchval("SELECT 1")
            latency = (time.time() - start) * 1000

            return ComponentHealth(
                name=self._name,
                status=HealthStatus.HEALTHY,
                latency_ms=latency,
                message="Connected",
                details={"pool_size": 10, "active_connections": 2},
            )
        except Exception as e:
            return ComponentHealth(
                name=self._name,
                status=HealthStatus.UNHEALTHY,
                latency_ms=(time.time() - start) * 1000,
                message=f"Connection failed: {e}",
            )


class RedisHealthCheck:
    """Health check for Redis cache."""

    def __init__(self, url: str | None = None) -> None:
        """Initialize Redis health check."""
        self._url = url
        self._name = "redis"

    @property
    def name(self) -> str:
        """Get component name."""
        return self._name

    async def check(self) -> ComponentHealth:
        """Check Redis connectivity."""
        start = time.time()

        try:
            # Simulate Redis ping (real implementation would use aioredis)
            # In production: await client.ping()
            latency = (time.time() - start) * 1000

            return ComponentHealth(
                name=self._name,
                status=HealthStatus.HEALTHY,
                latency_ms=latency,
                message="PONG",
                details={"connected_clients": 5},
            )
        except Exception as e:
            return ComponentHealth(
                name=self._name,
                status=HealthStatus.UNHEALTHY,
                latency_ms=(time.time() - start) * 1000,
                message=f"Connection failed: {e}",
            )


class QdrantHealthCheck:
    """Health check for Qdrant vector database."""

    def __init__(self, url: str | None = None) -> None:
        """Initialize Qdrant health check."""
        self._url = url
        self._name = "qdrant"

    @property
    def name(self) -> str:
        """Get component name."""
        return self._name

    async def check(self) -> ComponentHealth:
        """Check Qdrant connectivity."""
        start = time.time()

        try:
            # Simulate Qdrant health check
            # In production: await client.get_collections()
            latency = (time.time() - start) * 1000

            return ComponentHealth(
                name=self._name,
                status=HealthStatus.HEALTHY,
                latency_ms=latency,
                message="Available",
                details={"collections": ["medical_knowledge"]},
            )
        except Exception as e:
            return ComponentHealth(
                name=self._name,
                status=HealthStatus.UNHEALTHY,
                latency_ms=(time.time() - start) * 1000,
                message=f"Connection failed: {e}",
            )


class LLMProviderHealthCheck:
    """Health check for LLM providers."""

    def __init__(self, providers: list[str] | None = None) -> None:
        """Initialize LLM provider health check."""
        self._providers = providers or ["groq", "together", "ollama"]
        self._name = "llm_providers"

    @property
    def name(self) -> str:
        """Get component name."""
        return self._name

    async def check(self) -> ComponentHealth:
        """Check LLM provider availability."""
        start = time.time()

        available_providers = []
        unavailable_providers = []

        for provider in self._providers:
            try:
                # Simulate provider check
                # In production: check API key validity, model availability
                available_providers.append(provider)
            except Exception:
                unavailable_providers.append(provider)

        latency = (time.time() - start) * 1000

        if not available_providers:
            return ComponentHealth(
                name=self._name,
                status=HealthStatus.UNHEALTHY,
                latency_ms=latency,
                message="No LLM providers available",
                details={"unavailable": unavailable_providers},
            )
        elif unavailable_providers:
            return ComponentHealth(
                name=self._name,
                status=HealthStatus.DEGRADED,
                latency_ms=latency,
                message=f"{len(available_providers)} providers available",
                details={
                    "available": available_providers,
                    "unavailable": unavailable_providers,
                },
            )
        else:
            return ComponentHealth(
                name=self._name,
                status=HealthStatus.HEALTHY,
                latency_ms=latency,
                message=f"All {len(available_providers)} providers available",
                details={"available": available_providers},
            )


# =============================================================================
# Health Check Router
# =============================================================================


class HealthRouter:
    """Router for health check endpoints."""

    def __init__(
        self,
        version: str = "2.0.0",
        start_time: float | None = None,
    ) -> None:
        """Initialize health router."""
        self.version = version
        self.start_time = start_time or time.time()
        self._health_checks: list[HealthCheckProtocol] = []

    def add_check(self, check: HealthCheckProtocol) -> "HealthRouter":
        """Add a health check."""
        self._health_checks.append(check)
        return self

    @property
    def uptime_seconds(self) -> float:
        """Get uptime in seconds."""
        return time.time() - self.start_time

    async def health(self) -> HealthCheckResponse:
        """
        Full health check endpoint.

        Checks all components and returns aggregate status.
        Use for /health endpoint.
        """
        components = []

        for check in self._health_checks:
            result = await check.check()
            components.append(result)

        # Determine overall status
        if any(c.status == HealthStatus.UNHEALTHY for c in components):
            overall_status = HealthStatus.UNHEALTHY
        elif any(c.status == HealthStatus.DEGRADED for c in components):
            overall_status = HealthStatus.DEGRADED
        else:
            overall_status = HealthStatus.HEALTHY

        return HealthCheckResponse(
            status=overall_status,
            version=self.version,
            uptime_seconds=self.uptime_seconds,
            components=components,
        )

    async def ready(self) -> dict[str, Any]:
        """
        Readiness probe endpoint.

        Checks if the application is ready to accept traffic.
        Use for /ready endpoint (Kubernetes readiness probe).
        """
        response = await self.health()

        return {
            "ready": response.status != HealthStatus.UNHEALTHY,
            "status": response.status.value,
            "timestamp": datetime.now().isoformat(),
        }

    async def live(self) -> dict[str, Any]:
        """
        Liveness probe endpoint.

        Quick check to verify the process is alive.
        Use for /live endpoint (Kubernetes liveness probe).
        """
        return {
            "alive": True,
            "uptime_seconds": round(self.uptime_seconds, 2),
            "timestamp": datetime.now().isoformat(),
        }


# =============================================================================
# Factory Functions
# =============================================================================


def create_health_router(
    version: str = "2.0.0",
    db_url: str | None = None,
    redis_url: str | None = None,
    qdrant_url: str | None = None,
    llm_providers: list[str] | None = None,
) -> HealthRouter:
    """Create configured health router."""
    return (
        HealthRouter(version=version)
        .add_check(DatabaseHealthCheck(db_url))
        .add_check(RedisHealthCheck(redis_url))
        .add_check(QdrantHealthCheck(qdrant_url))
        .add_check(LLMProviderHealthCheck(llm_providers))
    )
