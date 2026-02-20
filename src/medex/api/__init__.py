# =============================================================================
# MedeX - API Module
# =============================================================================
"""
API Layer for MedeX Medical Assistant.

This module provides the HTTP/WebSocket interface for MedeX, including:

Features:
- REST endpoints for medical queries
- WebSocket support for streaming responses
- Health check endpoints for Kubernetes
- Metrics endpoint (Prometheus-compatible)
- Admin endpoints for system management

Components:
- App: FastAPI application factory
- Routes: Endpoint definitions
- Middleware: Request/response processing
- WebSocket: Real-time communication

Usage:
    from medex.api import create_app, AppConfig

    # Create with default config
    app = create_app()

    # Create with custom config
    config = AppConfig(debug=True, port=8080)
    app = create_app(config)

    # Start with lifespan
    async with LifespanManager(app):
        # App is running
        pass
"""

from __future__ import annotations

from .app import (
    AppConfig,
    AppState,
    LifespanManager,
    MedeXApp,
    create_app,
    create_development_app,
    create_production_app,
)
from .middleware import (
    CORSConfig,
    CORSMiddleware,
    ErrorHandlingMiddleware,
    MiddlewareBase,
    MiddlewareStack,
    ObservabilityConfig,
    ObservabilityMiddleware,
    RequestContext,
    SecurityConfig,
    SecurityMiddleware,
    create_default_middleware_stack,
    create_development_middleware_stack,
    get_current_context,
    set_current_context,
)
from .models import (
    APIError,
    ErrorCode,
    FeedbackRequest,
    HealthResponse,
    MessageType,
    QueryRequest,
    QueryResponse,
    QueryStatus,
    SearchRequest,
    SearchResponse,
    SearchResult,
    UserType,
    WSMessage,
)
from .websocket import (
    ConnectionManager,
    ConnectionState,
    WebSocketHandler,
    WSCloseCode,
    WSMessage as WebSocketMessage,
    WSMessageType,
    create_connection_manager,
    create_websocket_handler,
)

__all__ = [
    # App
    "AppConfig",
    "AppState",
    "MedeXApp",
    "LifespanManager",
    "create_app",
    "create_development_app",
    "create_production_app",
    # Models
    "UserType",
    "QueryStatus",
    "MessageType",
    "ErrorCode",
    "QueryRequest",
    "FeedbackRequest",
    "SearchRequest",
    "QueryResponse",
    "SearchResult",
    "SearchResponse",
    "WSMessage",
    "APIError",
    "HealthResponse",
    # Middleware
    "RequestContext",
    "get_current_context",
    "set_current_context",
    "CORSConfig",
    "SecurityConfig",
    "ObservabilityConfig",
    "MiddlewareBase",
    "CORSMiddleware",
    "SecurityMiddleware",
    "ObservabilityMiddleware",
    "ErrorHandlingMiddleware",
    "MiddlewareStack",
    "create_default_middleware_stack",
    "create_development_middleware_stack",
    # WebSocket
    "WSMessageType",
    "WSCloseCode",
    "WebSocketMessage",
    "ConnectionState",
    "WebSocketHandler",
    "ConnectionManager",
    "create_websocket_handler",
    "create_connection_manager",
]

__version__ = "2.0.0"
