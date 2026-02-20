# =============================================================================
# MedeX - FastAPI Application
# =============================================================================
"""
FastAPI application factory and configuration.

Features:
- Application factory pattern
- Lifespan management (startup/shutdown)
- Router registration
- Middleware configuration
- OpenAPI customization
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

# =============================================================================
# Application Configuration
# =============================================================================


@dataclass
class AppConfig:
    """Application configuration."""

    # Basic info
    title: str = "MedeX API"
    description: str = "API de Asistente Médico Educativo con IA"
    version: str = "2.0.0"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False

    # CORS
    cors_origins: list[str] = field(default_factory=lambda: ["*"])
    cors_allow_credentials: bool = True

    # Rate limiting
    rate_limit_enabled: bool = True
    rate_limit_requests: int = 100
    rate_limit_window: int = 60

    # Timeouts
    request_timeout: float = 60.0
    llm_timeout: float = 120.0

    # Features
    enable_websocket: bool = True
    enable_streaming: bool = True
    enable_metrics: bool = True
    enable_docs: bool = True

    # Security
    api_key_required: bool = False
    api_key_header: str = "X-API-Key"

    # Database
    database_url: str | None = None
    redis_url: str | None = None
    qdrant_url: str | None = None


# =============================================================================
# Application State
# =============================================================================


@dataclass
class AppState:
    """Application runtime state."""

    started_at: datetime = field(default_factory=datetime.now)
    is_healthy: bool = True
    is_ready: bool = False

    # Service references (set during startup)
    agent_service: Any | None = None
    rag_service: Any | None = None
    security_service: Any | None = None
    observability_service: Any | None = None

    # Request tracking
    total_requests: int = 0
    active_requests: int = 0

    @property
    def uptime_seconds(self) -> float:
        """Get uptime in seconds."""
        return (datetime.now() - self.started_at).total_seconds()


# =============================================================================
# Application Factory
# =============================================================================


class MedeXApp:
    """MedeX FastAPI application wrapper."""

    def __init__(self, config: AppConfig | None = None) -> None:
        """Initialize MedeX application."""
        self.config = config or AppConfig()
        self.state = AppState()
        self._startup_handlers: list[Any] = []
        self._shutdown_handlers: list[Any] = []

    def on_startup(self, handler: Any) -> Any:
        """Register startup handler."""
        self._startup_handlers.append(handler)
        return handler

    def on_shutdown(self, handler: Any) -> Any:
        """Register shutdown handler."""
        self._shutdown_handlers.append(handler)
        return handler

    async def startup(self) -> None:
        """
        Execute startup sequence.

        Order:
        1. Initialize database connections
        2. Initialize cache
        3. Initialize vector store
        4. Load LLM providers
        5. Initialize services
        6. Set ready state
        """
        print(f"[MedeX] Starting {self.config.title} v{self.config.version}")

        # Run custom handlers
        for handler in self._startup_handlers:
            await handler() if asyncio.iscoroutinefunction(handler) else handler()

        # Initialize services (placeholder - real impl would create actual services)
        self.state.agent_service = "AgentService"
        self.state.rag_service = "RAGService"
        self.state.security_service = "SecurityService"
        self.state.observability_service = "ObservabilityService"

        self.state.is_ready = True
        print("[MedeX] Application ready")

    async def shutdown(self) -> None:
        """
        Execute shutdown sequence.

        Order:
        1. Set not ready state
        2. Close active connections
        3. Flush metrics
        4. Close database connections
        5. Cleanup resources
        """
        print("[MedeX] Shutting down...")

        self.state.is_ready = False

        # Run custom handlers
        for handler in reversed(self._shutdown_handlers):
            await handler() if asyncio.iscoroutinefunction(handler) else handler()

        print("[MedeX] Shutdown complete")

    def create_openapi_schema(self) -> dict[str, Any]:
        """Create custom OpenAPI schema."""
        return {
            "openapi": "3.1.0",
            "info": {
                "title": self.config.title,
                "description": self.config.description,
                "version": self.config.version,
                "contact": {
                    "name": "MedeX Support",
                    "email": "support@medex.health",
                },
                "license": {
                    "name": "MIT License",
                    "url": "https://opensource.org/licenses/MIT",
                },
            },
            "servers": [
                {
                    "url": f"http://localhost:{self.config.port}",
                    "description": "Local development",
                },
            ],
            "tags": [
                {
                    "name": "health",
                    "description": "Health check endpoints",
                },
                {
                    "name": "query",
                    "description": "Medical query endpoints",
                },
                {
                    "name": "search",
                    "description": "RAG search endpoints",
                },
                {
                    "name": "admin",
                    "description": "Administrative endpoints",
                },
            ],
            "paths": self._generate_paths(),
            "components": self._generate_components(),
        }

    def _generate_paths(self) -> dict[str, Any]:
        """Generate OpenAPI paths."""
        return {
            "/health": {
                "get": {
                    "tags": ["health"],
                    "summary": "Health Check",
                    "description": "Get system health status",
                    "responses": {
                        "200": {"description": "System healthy"},
                        "503": {"description": "System unhealthy"},
                    },
                },
            },
            "/ready": {
                "get": {
                    "tags": ["health"],
                    "summary": "Readiness Check",
                    "description": "Check if system is ready to accept traffic",
                    "responses": {
                        "200": {"description": "System ready"},
                        "503": {"description": "System not ready"},
                    },
                },
            },
            "/live": {
                "get": {
                    "tags": ["health"],
                    "summary": "Liveness Check",
                    "description": "Check if process is alive",
                    "responses": {
                        "200": {"description": "Process alive"},
                    },
                },
            },
            "/query": {
                "post": {
                    "tags": ["query"],
                    "summary": "Medical Query",
                    "description": "Submit a medical query for processing",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/QueryRequest"},
                            },
                        },
                    },
                    "responses": {
                        "200": {
                            "description": "Query processed",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/QueryResponse"
                                    },
                                },
                            },
                        },
                        "400": {"description": "Invalid request"},
                        "429": {"description": "Rate limited"},
                    },
                },
            },
            "/stream": {
                "post": {
                    "tags": ["query"],
                    "summary": "Streaming Query",
                    "description": "Submit a medical query with streaming response",
                    "responses": {
                        "200": {
                            "description": "Streaming response",
                            "content": {"text/event-stream": {}},
                        },
                    },
                },
            },
            "/search": {
                "post": {
                    "tags": ["search"],
                    "summary": "RAG Search",
                    "description": "Search the medical knowledge base",
                    "responses": {
                        "200": {"description": "Search results"},
                    },
                },
            },
            "/metrics": {
                "get": {
                    "tags": ["admin"],
                    "summary": "Get Metrics",
                    "description": "Get Prometheus-compatible metrics",
                    "responses": {
                        "200": {"description": "Metrics in Prometheus format"},
                    },
                },
            },
            "/ws": {
                "get": {
                    "tags": ["query"],
                    "summary": "WebSocket Connection",
                    "description": "Establish WebSocket for streaming queries",
                    "responses": {
                        "101": {"description": "WebSocket upgrade"},
                    },
                },
            },
        }

    def _generate_components(self) -> dict[str, Any]:
        """Generate OpenAPI components."""
        return {
            "schemas": {
                "QueryRequest": {
                    "type": "object",
                    "required": ["query"],
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Medical query text",
                            "minLength": 3,
                            "maxLength": 10000,
                        },
                        "user_type": {
                            "type": "string",
                            "enum": ["educational", "professional", "research"],
                            "default": "educational",
                        },
                        "stream": {
                            "type": "boolean",
                            "default": False,
                        },
                        "include_sources": {
                            "type": "boolean",
                            "default": True,
                        },
                        "language": {
                            "type": "string",
                            "enum": ["es", "en", "pt"],
                            "default": "es",
                        },
                    },
                },
                "QueryResponse": {
                    "type": "object",
                    "properties": {
                        "query_id": {"type": "string"},
                        "response": {"type": "string"},
                        "user_type": {"type": "string"},
                        "is_emergency": {"type": "boolean"},
                        "triage_level": {"type": "integer", "minimum": 1, "maximum": 5},
                        "sources": {
                            "type": "array",
                            "items": {"$ref": "#/components/schemas/Source"},
                        },
                        "tokens_used": {"type": "integer"},
                        "duration_ms": {"type": "number"},
                    },
                },
                "Source": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "title": {"type": "string"},
                        "content": {"type": "string"},
                        "score": {"type": "number"},
                    },
                },
                "HealthResponse": {
                    "type": "object",
                    "properties": {
                        "status": {
                            "type": "string",
                            "enum": ["healthy", "degraded", "unhealthy"],
                        },
                        "version": {"type": "string"},
                        "uptime_seconds": {"type": "number"},
                        "components": {"type": "array"},
                    },
                },
                "Error": {
                    "type": "object",
                    "properties": {
                        "error": {
                            "type": "object",
                            "properties": {
                                "code": {"type": "string"},
                                "message": {"type": "string"},
                                "details": {"type": "object"},
                            },
                        },
                        "request_id": {"type": "string"},
                    },
                },
            },
            "securitySchemes": {
                "ApiKeyAuth": {
                    "type": "apiKey",
                    "in": "header",
                    "name": "X-API-Key",
                },
            },
        }


# =============================================================================
# Lifespan Manager
# =============================================================================


class LifespanManager:
    """Manages application lifespan events."""

    def __init__(self, app: MedeXApp) -> None:
        """Initialize lifespan manager."""
        self.app = app
        self._start_time = time.time()

    async def __aenter__(self) -> LifespanManager:
        """Enter lifespan context (startup)."""
        await self.app.startup()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit lifespan context (shutdown)."""
        await self.app.shutdown()


# =============================================================================
# Factory Functions
# =============================================================================


def create_app(config: AppConfig | None = None) -> MedeXApp:
    """Create MedeX application with default configuration."""
    return MedeXApp(config=config or AppConfig())


def create_production_app() -> MedeXApp:
    """Create production-ready application."""
    return MedeXApp(
        config=AppConfig(
            debug=False,
            rate_limit_enabled=True,
            api_key_required=False,  # Educational mode
            enable_docs=True,
        )
    )


def create_development_app() -> MedeXApp:
    """Create development application."""
    return MedeXApp(
        config=AppConfig(
            debug=True,
            rate_limit_enabled=False,
            api_key_required=False,
            enable_docs=True,
        )
    )


# Import for asyncio check
import asyncio  # noqa: E402
