# =============================================================================
# MedeX - Health Checks
# =============================================================================
"""
Health check system for MedeX.

Provides:
- Component health checks (DB, Redis, Qdrant, LLM providers)
- Liveness and readiness probes
- Dependency status monitoring
- Health aggregation
"""

from __future__ import annotations

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from medex.observability.models import (
    ComponentHealth,
    ComponentType,
    HealthStatus,
    SystemHealth,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Health Check Interface
# =============================================================================


class HealthCheck(ABC):
    """Abstract base class for health checks."""

    def __init__(
        self,
        name: str,
        component_type: ComponentType,
        timeout_seconds: float = 5.0,
        critical: bool = True,
    ) -> None:
        """Initialize health check."""
        self.name = name
        self.component_type = component_type
        self.timeout = timeout_seconds
        self.critical = critical

    @abstractmethod
    async def check(self) -> ComponentHealth:
        """Perform health check."""
        pass

    async def check_with_timeout(self) -> ComponentHealth:
        """Perform health check with timeout."""
        try:
            return await asyncio.wait_for(
                self.check(),
                timeout=self.timeout,
            )
        except asyncio.TimeoutError:
            return ComponentHealth(
                name=self.name,
                component_type=self.component_type,
                status=HealthStatus.UNHEALTHY,
                message=f"Health check timed out after {self.timeout}s",
            )
        except Exception as e:
            return ComponentHealth(
                name=self.name,
                component_type=self.component_type,
                status=HealthStatus.UNHEALTHY,
                message=f"Health check failed: {str(e)}",
            )


# =============================================================================
# Database Health Check
# =============================================================================


class PostgresHealthCheck(HealthCheck):
    """PostgreSQL health check."""

    def __init__(
        self,
        connection_string: str | None = None,
        pool: Any = None,
    ) -> None:
        """Initialize PostgreSQL health check."""
        super().__init__(
            name="postgresql",
            component_type=ComponentType.DATABASE,
            critical=True,
        )
        self.connection_string = connection_string
        self.pool = pool

    async def check(self) -> ComponentHealth:
        """Check PostgreSQL connectivity."""
        start = time.perf_counter()

        try:
            if self.pool:
                # Use existing pool
                async with self.pool.acquire() as conn:
                    await conn.execute("SELECT 1")
            elif self.connection_string:
                # Create new connection
                try:
                    import asyncpg

                    conn = await asyncpg.connect(self.connection_string)
                    await conn.execute("SELECT 1")
                    await conn.close()
                except ImportError:
                    return ComponentHealth(
                        name=self.name,
                        component_type=self.component_type,
                        status=HealthStatus.UNKNOWN,
                        message="asyncpg not installed",
                    )
            else:
                return ComponentHealth(
                    name=self.name,
                    component_type=self.component_type,
                    status=HealthStatus.UNKNOWN,
                    message="No connection configured",
                )

            latency = (time.perf_counter() - start) * 1000

            return ComponentHealth(
                name=self.name,
                component_type=self.component_type,
                status=HealthStatus.HEALTHY,
                latency_ms=latency,
                message="Connected successfully",
            )

        except Exception as e:
            latency = (time.perf_counter() - start) * 1000
            return ComponentHealth(
                name=self.name,
                component_type=self.component_type,
                status=HealthStatus.UNHEALTHY,
                latency_ms=latency,
                message=f"Connection failed: {str(e)}",
            )


# =============================================================================
# Redis Health Check
# =============================================================================


class RedisHealthCheck(HealthCheck):
    """Redis health check."""

    def __init__(
        self,
        url: str | None = None,
        client: Any = None,
    ) -> None:
        """Initialize Redis health check."""
        super().__init__(
            name="redis",
            component_type=ComponentType.CACHE,
            critical=False,  # Cache failure shouldn't bring down service
        )
        self.url = url
        self.client = client

    async def check(self) -> ComponentHealth:
        """Check Redis connectivity."""
        start = time.perf_counter()

        try:
            if self.client:
                await self.client.ping()
            elif self.url:
                try:
                    import redis.asyncio as redis

                    client = redis.from_url(self.url)
                    await client.ping()
                    await client.close()
                except ImportError:
                    return ComponentHealth(
                        name=self.name,
                        component_type=self.component_type,
                        status=HealthStatus.UNKNOWN,
                        message="redis-py not installed",
                    )
            else:
                return ComponentHealth(
                    name=self.name,
                    component_type=self.component_type,
                    status=HealthStatus.UNKNOWN,
                    message="No connection configured",
                )

            latency = (time.perf_counter() - start) * 1000

            return ComponentHealth(
                name=self.name,
                component_type=self.component_type,
                status=HealthStatus.HEALTHY,
                latency_ms=latency,
                message="PONG received",
            )

        except Exception as e:
            latency = (time.perf_counter() - start) * 1000
            return ComponentHealth(
                name=self.name,
                component_type=self.component_type,
                status=HealthStatus.UNHEALTHY,
                latency_ms=latency,
                message=f"Connection failed: {str(e)}",
            )


# =============================================================================
# Qdrant Health Check
# =============================================================================


class QdrantHealthCheck(HealthCheck):
    """Qdrant vector store health check."""

    def __init__(
        self,
        url: str | None = None,
        client: Any = None,
    ) -> None:
        """Initialize Qdrant health check."""
        super().__init__(
            name="qdrant",
            component_type=ComponentType.VECTOR_STORE,
            critical=True,
        )
        self.url = url
        self.client = client

    async def check(self) -> ComponentHealth:
        """Check Qdrant connectivity."""
        start = time.perf_counter()

        try:
            if self.client:
                # Use existing client
                collections = await self.client.get_collections()
                details = {"collections_count": len(collections.collections)}
            elif self.url:
                try:
                    from qdrant_client import QdrantClient

                    client = QdrantClient(url=self.url)
                    collections = client.get_collections()
                    details = {"collections_count": len(collections.collections)}
                except ImportError:
                    return ComponentHealth(
                        name=self.name,
                        component_type=self.component_type,
                        status=HealthStatus.UNKNOWN,
                        message="qdrant-client not installed",
                    )
            else:
                return ComponentHealth(
                    name=self.name,
                    component_type=self.component_type,
                    status=HealthStatus.UNKNOWN,
                    message="No connection configured",
                )

            latency = (time.perf_counter() - start) * 1000

            return ComponentHealth(
                name=self.name,
                component_type=self.component_type,
                status=HealthStatus.HEALTHY,
                latency_ms=latency,
                message="Connected successfully",
                details=details,
            )

        except Exception as e:
            latency = (time.perf_counter() - start) * 1000
            return ComponentHealth(
                name=self.name,
                component_type=self.component_type,
                status=HealthStatus.UNHEALTHY,
                latency_ms=latency,
                message=f"Connection failed: {str(e)}",
            )


# =============================================================================
# LLM Provider Health Check
# =============================================================================


class LLMProviderHealthCheck(HealthCheck):
    """LLM provider health check."""

    def __init__(
        self,
        provider_name: str,
        health_check_url: str | None = None,
        api_key: str | None = None,
    ) -> None:
        """Initialize LLM provider health check."""
        super().__init__(
            name=f"llm_{provider_name}",
            component_type=ComponentType.LLM_PROVIDER,
            critical=False,  # Individual provider failure is okay
            timeout_seconds=10.0,
        )
        self.provider_name = provider_name
        self.health_check_url = health_check_url
        self.api_key = api_key

    async def check(self) -> ComponentHealth:
        """Check LLM provider availability."""
        start = time.perf_counter()

        # For now, just mark as unknown without actual check
        # Real implementation would ping the provider's health endpoint

        latency = (time.perf_counter() - start) * 1000

        return ComponentHealth(
            name=self.name,
            component_type=self.component_type,
            status=HealthStatus.UNKNOWN,
            latency_ms=latency,
            message="Health check not implemented for this provider",
            details={"provider": self.provider_name},
        )


# =============================================================================
# Custom Health Check
# =============================================================================


class CallableHealthCheck(HealthCheck):
    """Health check from a callable."""

    def __init__(
        self,
        name: str,
        component_type: ComponentType,
        check_fn: Any,  # Callable[[], Awaitable[bool]] or Callable[[], bool]
        critical: bool = False,
    ) -> None:
        """Initialize callable health check."""
        super().__init__(name, component_type, critical=critical)
        self._check_fn = check_fn

    async def check(self) -> ComponentHealth:
        """Run the health check function."""
        start = time.perf_counter()

        try:
            result = self._check_fn()
            if asyncio.iscoroutine(result):
                result = await result

            latency = (time.perf_counter() - start) * 1000

            if result:
                return ComponentHealth(
                    name=self.name,
                    component_type=self.component_type,
                    status=HealthStatus.HEALTHY,
                    latency_ms=latency,
                )
            else:
                return ComponentHealth(
                    name=self.name,
                    component_type=self.component_type,
                    status=HealthStatus.UNHEALTHY,
                    latency_ms=latency,
                )

        except Exception as e:
            latency = (time.perf_counter() - start) * 1000
            return ComponentHealth(
                name=self.name,
                component_type=self.component_type,
                status=HealthStatus.UNHEALTHY,
                latency_ms=latency,
                message=str(e),
            )


# =============================================================================
# Health Manager
# =============================================================================


@dataclass
class HealthManagerConfig:
    """Configuration for health manager."""

    service_name: str = "medex"
    service_version: str = "2.0.0"
    check_interval_seconds: int = 30
    parallel_checks: bool = True


class HealthManager:
    """Manages all health checks."""

    def __init__(self, config: HealthManagerConfig | None = None) -> None:
        """Initialize health manager."""
        self.config = config or HealthManagerConfig()
        self._checks: list[HealthCheck] = []
        self._start_time = time.time()
        self._last_check: SystemHealth | None = None

    def register(self, check: HealthCheck) -> None:
        """Register a health check."""
        self._checks.append(check)
        logger.info(f"Registered health check: {check.name}")

    def unregister(self, name: str) -> None:
        """Unregister a health check by name."""
        self._checks = [c for c in self._checks if c.name != name]

    async def check_all(self) -> SystemHealth:
        """Run all health checks."""
        if self.config.parallel_checks:
            # Run checks in parallel
            results = await asyncio.gather(
                *[check.check_with_timeout() for check in self._checks],
                return_exceptions=True,
            )

            components = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    components.append(
                        ComponentHealth(
                            name=self._checks[i].name,
                            component_type=self._checks[i].component_type,
                            status=HealthStatus.UNHEALTHY,
                            message=str(result),
                        )
                    )
                else:
                    components.append(result)
        else:
            # Run checks sequentially
            components = []
            for check in self._checks:
                result = await check.check_with_timeout()
                components.append(result)

        # Determine overall status
        overall_status = self._calculate_overall_status(components)

        self._last_check = SystemHealth(
            status=overall_status,
            version=self.config.service_version,
            uptime_seconds=time.time() - self._start_time,
            components=components,
        )

        return self._last_check

    def _calculate_overall_status(
        self,
        components: list[ComponentHealth],
    ) -> HealthStatus:
        """Calculate overall health status."""
        if not components:
            return HealthStatus.HEALTHY

        critical_unhealthy = False
        any_unhealthy = False
        any_degraded = False

        for comp in components:
            check = next((c for c in self._checks if c.name == comp.name), None)

            if comp.status == HealthStatus.UNHEALTHY:
                any_unhealthy = True
                if check and check.critical:
                    critical_unhealthy = True
            elif comp.status == HealthStatus.DEGRADED:
                any_degraded = True

        if critical_unhealthy:
            return HealthStatus.UNHEALTHY
        elif any_unhealthy or any_degraded:
            return HealthStatus.DEGRADED
        else:
            return HealthStatus.HEALTHY

    async def liveness_probe(self) -> tuple[bool, str]:
        """
        Kubernetes liveness probe.

        Returns True if the application is running.
        This should be a simple check that doesn't depend on external services.
        """
        return True, "Application is running"

    async def readiness_probe(self) -> tuple[bool, str]:
        """
        Kubernetes readiness probe.

        Returns True if the application is ready to accept traffic.
        This checks critical dependencies.
        """
        health = await self.check_all()

        if health.status == HealthStatus.HEALTHY:
            return True, "Ready to accept traffic"
        elif health.status == HealthStatus.DEGRADED:
            return True, "Running in degraded mode"
        else:
            unhealthy = [c.name for c in health.unhealthy_components]
            return False, f"Unhealthy components: {', '.join(unhealthy)}"

    def get_last_check(self) -> SystemHealth | None:
        """Get last health check result."""
        return self._last_check

    @property
    def uptime_seconds(self) -> float:
        """Get service uptime in seconds."""
        return time.time() - self._start_time


# =============================================================================
# Factory Functions
# =============================================================================

_global_health_manager: HealthManager | None = None


def get_health_manager() -> HealthManager:
    """Get global health manager."""
    global _global_health_manager
    if _global_health_manager is None:
        _global_health_manager = HealthManager()
    return _global_health_manager


def init_health_manager(
    config: HealthManagerConfig | None = None,
) -> HealthManager:
    """Initialize global health manager."""
    global _global_health_manager
    _global_health_manager = HealthManager(config)
    return _global_health_manager


def register_health_check(check: HealthCheck) -> None:
    """Register health check with global manager."""
    get_health_manager().register(check)
