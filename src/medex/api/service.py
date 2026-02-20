# =============================================================================
# MedeX - API Service
# =============================================================================
"""
API Service facade for the API layer.

Provides a unified interface for all API operations:
- Query processing
- Search operations
- Health checks
- Admin operations
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from .app import AppConfig, AppState, MedeXApp, create_app
from .routes.admin import AdminHandler, create_admin_handler
from .routes.health import HealthRouter, create_health_router
from .routes.query import QueryHandler, create_query_handler
from .websocket import ConnectionManager, WebSocketHandler, create_connection_manager


# =============================================================================
# API Service Configuration
# =============================================================================


@dataclass
class APIServiceConfig:
    """Configuration for API service."""

    # App config
    app_config: AppConfig = field(default_factory=AppConfig)

    # Feature flags
    enable_websocket: bool = True
    enable_metrics: bool = True
    enable_admin: bool = True

    # Timeouts
    query_timeout: float = 60.0
    search_timeout: float = 30.0

    # Limits
    max_concurrent_queries: int = 100
    max_websocket_connections: int = 1000


# =============================================================================
# API Service
# =============================================================================


class APIService:
    """
    Facade for all API layer operations.

    Provides unified access to:
    - Query handling (sync/stream)
    - RAG search
    - Health checks
    - Admin operations
    - WebSocket connections

    Example:
        service = create_api_service()
        await service.startup()

        # Handle query
        response = await service.query(request)

        # Stream response
        async for chunk in service.stream(request):
            print(chunk)

        # Health check
        health = await service.health()

        await service.shutdown()
    """

    def __init__(self, config: APIServiceConfig | None = None) -> None:
        """Initialize API service."""
        self._config = config or APIServiceConfig()
        self._started = False
        self._start_time: float | None = None

        # Initialize components
        self._app = create_app(self._config.app_config)
        self._query_handler = create_query_handler()
        self._health_router = create_health_router(
            version=self._config.app_config.version
        )
        self._admin_handler = create_admin_handler()
        self._connection_manager: ConnectionManager | None = None

        if self._config.enable_websocket:
            self._connection_manager = create_connection_manager()

        # Metrics
        self._total_queries = 0
        self._total_errors = 0

    @property
    def is_running(self) -> bool:
        """Check if service is running."""
        return self._started

    @property
    def uptime_seconds(self) -> float:
        """Get service uptime in seconds."""
        if self._start_time is None:
            return 0.0
        return time.time() - self._start_time

    async def startup(self) -> None:
        """Start API service."""
        if self._started:
            return

        await self._app.startup()

        if self._connection_manager:
            await self._connection_manager.start()

        self._started = True
        self._start_time = time.time()

    async def shutdown(self) -> None:
        """Stop API service."""
        if not self._started:
            return

        if self._connection_manager:
            await self._connection_manager.stop()

        await self._app.shutdown()
        self._started = False

    # -------------------------------------------------------------------------
    # Query Operations
    # -------------------------------------------------------------------------

    async def query(self, request: Any) -> Any:
        """
        Process synchronous medical query.

        Args:
            request: Query request

        Returns:
            Query response
        """
        try:
            response = await self._query_handler.query(request)
            self._total_queries += 1
            return response
        except Exception as e:
            self._total_errors += 1
            raise

    async def stream(self, request: Any) -> Any:
        """
        Process streaming medical query.

        Args:
            request: Query request

        Yields:
            Stream chunks
        """
        try:
            async for chunk in self._query_handler.stream(request):
                yield chunk
            self._total_queries += 1
        except Exception as e:
            self._total_errors += 1
            raise

    async def search(self, request: Any) -> Any:
        """
        Search medical knowledge base.

        Args:
            request: Search request

        Returns:
            Search response
        """
        return await self._query_handler.search(request)

    # -------------------------------------------------------------------------
    # Health Operations
    # -------------------------------------------------------------------------

    async def health(self) -> Any:
        """Get full health status."""
        return await self._health_router.health()

    async def ready(self) -> dict[str, Any]:
        """Check readiness."""
        return await self._health_router.ready()

    async def live(self) -> dict[str, Any]:
        """Check liveness."""
        return await self._health_router.live()

    # -------------------------------------------------------------------------
    # Admin Operations
    # -------------------------------------------------------------------------

    async def get_metrics(self) -> Any:
        """Get system metrics."""
        return await self._admin_handler.get_metrics()

    async def get_audit_logs(self, **kwargs: Any) -> Any:
        """Get audit logs."""
        return await self._admin_handler.get_audit_logs(**kwargs)

    async def clear_cache(self, pattern: str | None = None) -> Any:
        """Clear cache."""
        return await self._admin_handler.clear_cache(pattern)

    async def get_config(self) -> Any:
        """Get system configuration."""
        return await self._admin_handler.get_config()

    # -------------------------------------------------------------------------
    # WebSocket Operations
    # -------------------------------------------------------------------------

    async def ws_connect(
        self, connection_id: str, session_id: str | None = None
    ) -> Any:
        """Handle WebSocket connection."""
        if not self._connection_manager:
            raise RuntimeError("WebSocket not enabled")
        return await self._connection_manager.handler.on_connect(
            connection_id, session_id
        )

    async def ws_disconnect(self, connection_id: str) -> None:
        """Handle WebSocket disconnection."""
        if not self._connection_manager:
            return
        await self._connection_manager.handler.on_disconnect(connection_id)

    async def ws_message(self, connection_id: str, message: str) -> list[Any]:
        """Handle WebSocket message."""
        if not self._connection_manager:
            raise RuntimeError("WebSocket not enabled")
        return await self._connection_manager.handler.on_message(connection_id, message)

    def get_ws_stats(self) -> dict[str, Any]:
        """Get WebSocket connection stats."""
        if not self._connection_manager:
            return {"enabled": False}
        stats = self._connection_manager.handler.get_connection_stats()
        stats["enabled"] = True
        return stats

    # -------------------------------------------------------------------------
    # Service Stats
    # -------------------------------------------------------------------------

    def get_stats(self) -> dict[str, Any]:
        """Get service statistics."""
        return {
            "running": self._started,
            "uptime_seconds": self.uptime_seconds,
            "total_queries": self._total_queries,
            "total_errors": self._total_errors,
            "error_rate": self._total_errors / max(1, self._total_queries),
            "websocket": self.get_ws_stats(),
        }


# =============================================================================
# Factory Functions
# =============================================================================


def create_api_service(config: APIServiceConfig | None = None) -> APIService:
    """Create API service with default configuration."""
    return APIService(config=config)


def create_production_api_service() -> APIService:
    """Create production-ready API service."""
    return APIService(
        config=APIServiceConfig(
            app_config=AppConfig(
                debug=False,
                rate_limit_enabled=True,
                enable_docs=True,
            ),
            enable_websocket=True,
            enable_metrics=True,
            enable_admin=True,
        )
    )


def create_development_api_service() -> APIService:
    """Create development API service."""
    return APIService(
        config=APIServiceConfig(
            app_config=AppConfig(
                debug=True,
                rate_limit_enabled=False,
                enable_docs=True,
            ),
            enable_websocket=True,
            enable_metrics=True,
            enable_admin=True,
        )
    )
