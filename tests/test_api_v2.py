# =============================================================================
# MedeX - API Module Tests (V2)
# =============================================================================
"""
Comprehensive tests for the new API layer v2.

Tests cover:
- Request/Response models
- Middleware components
- Query endpoints
- WebSocket handling
- Health checks
- Admin endpoints
- Error handling
"""

from __future__ import annotations

import time
from typing import Any

import pytest

# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def sample_query_request() -> dict[str, Any]:
    """Sample query request."""
    return {
        "query": "¿Cuáles son los síntomas de la diabetes tipo 2?",
        "user_type": "educational",
        "stream": False,
        "include_sources": True,
        "language": "es",
    }


@pytest.fixture
def sample_search_request() -> dict[str, Any]:
    """Sample search request."""
    return {
        "query": "diabetes mellitus tratamiento",
        "collection": "medical_knowledge",
        "limit": 10,
        "min_score": 0.5,
    }


# =============================================================================
# Model Tests
# =============================================================================


class TestAPIModelsV2:
    """Tests for API models v2."""

    def test_user_type_enum(self) -> None:
        """Test UserType enum values."""
        from medex.api.models import UserType

        assert UserType.EDUCATIONAL.value == "educational"
        assert UserType.PROFESSIONAL.value == "professional"
        assert UserType.RESEARCH.value == "research"

    def test_query_status_enum(self) -> None:
        """Test QueryStatus enum values."""
        from medex.api.models import QueryStatus

        assert QueryStatus.PENDING.value == "pending"
        assert QueryStatus.PROCESSING.value == "processing"
        assert QueryStatus.COMPLETED.value == "completed"
        assert QueryStatus.FAILED.value == "failed"

    def test_error_code_enum(self) -> None:
        """Test ErrorCode enum values."""
        from medex.api.models import ErrorCode

        # Client errors
        assert ErrorCode.INVALID_REQUEST.value == "invalid_request"
        assert ErrorCode.RATE_LIMITED.value == "rate_limited"

        # Server errors
        assert ErrorCode.INTERNAL_ERROR.value == "internal_error"
        assert ErrorCode.LLM_ERROR.value == "llm_error"

    def test_query_request_validation_success(self) -> None:
        """Test valid query request passes validation."""
        from medex.api.models import QueryRequest, UserType

        request = QueryRequest(
            query="¿Cuáles son los síntomas de la gripe?",
            user_type=UserType.EDUCATIONAL,
            language="es",
        )

        errors = request.validate()
        assert len(errors) == 0

    def test_query_request_validation_short_query(self) -> None:
        """Test short query fails validation."""
        from medex.api.models import QueryRequest

        request = QueryRequest(query="ab")
        errors = request.validate()
        assert any("at least 3 characters" in e for e in errors)

    def test_query_request_validation_long_query(self) -> None:
        """Test long query fails validation."""
        from medex.api.models import QueryRequest

        request = QueryRequest(query="a" * 10001)
        errors = request.validate()
        assert any("less than 10000" in e for e in errors)

    def test_query_request_validation_invalid_language(self) -> None:
        """Test invalid language fails validation."""
        from medex.api.models import QueryRequest

        request = QueryRequest(query="valid query", language="fr")
        errors = request.validate()
        assert any("Language" in e for e in errors)

    def test_query_response_to_dict(self) -> None:
        """Test QueryResponse serialization."""
        from medex.api.models import QueryResponse, QueryStatus, UserType

        response = QueryResponse(
            query_id="test-123",
            status=QueryStatus.COMPLETED,
            response="Test response",
            user_type=UserType.EDUCATIONAL,
            tokens_used=100,
        )

        data = response.to_dict()

        assert data["query_id"] == "test-123"
        assert data["status"] == "completed"
        assert data["response"] == "Test response"
        assert data["tokens_used"] == 100

    def test_api_error_status_codes(self) -> None:
        """Test APIError status code mapping."""
        from medex.api.models import APIError, ErrorCode

        # Client errors
        error_400 = APIError(code=ErrorCode.INVALID_REQUEST, message="Bad request")
        assert error_400.status_code == 400

        error_429 = APIError(code=ErrorCode.RATE_LIMITED, message="Too many requests")
        assert error_429.status_code == 429

        # Server errors
        error_500 = APIError(code=ErrorCode.INTERNAL_ERROR, message="Server error")
        assert error_500.status_code == 500

        error_503 = APIError(code=ErrorCode.SERVICE_UNAVAILABLE, message="Unavailable")
        assert error_503.status_code == 503

    def test_ws_message_factory_methods(self) -> None:
        """Test WSMessage factory methods."""
        from medex.api.models import MessageType, WSMessage

        # Thinking message
        msg = WSMessage.thinking("Processing...")
        assert msg.type == MessageType.THINKING
        assert msg.data["message"] == "Processing..."

        # Streaming message
        msg = WSMessage.streaming("chunk", token_count=10)
        assert msg.type == MessageType.STREAMING
        assert msg.data["chunk"] == "chunk"
        assert msg.data["token_count"] == 10

        # Tool call message
        msg = WSMessage.tool_call("drug_checker", status="executing")
        assert msg.type == MessageType.TOOL_CALL
        assert msg.data["tool"] == "drug_checker"

    def test_feedback_request_validation(self) -> None:
        """Test FeedbackRequest validation."""
        from medex.api.models import FeedbackRequest

        # Valid feedback
        feedback = FeedbackRequest(query_id="q-123", rating=5, helpful=True)
        errors = feedback.validate()
        assert len(errors) == 0

        # Invalid rating
        feedback = FeedbackRequest(query_id="q-123", rating=6)
        errors = feedback.validate()
        assert any("Rating" in e for e in errors)

        # Missing query_id
        feedback = FeedbackRequest(query_id="", rating=3)
        errors = feedback.validate()
        assert any("query_id" in e for e in errors)


# =============================================================================
# Middleware Tests
# =============================================================================


class TestMiddlewareV2:
    """Tests for middleware components v2."""

    def test_request_context_creation(self) -> None:
        """Test RequestContext default values."""
        from medex.api.middleware import RequestContext

        ctx = RequestContext()

        assert ctx.request_id is not None
        assert len(ctx.request_id) == 36  # UUID format
        assert ctx.authenticated is False
        assert ctx.rate_limit_remaining == -1

    def test_request_context_elapsed_time(self) -> None:
        """Test RequestContext elapsed time calculation."""
        from medex.api.middleware import RequestContext

        ctx = RequestContext()
        time.sleep(0.01)  # 10ms
        elapsed = ctx.elapsed_ms()

        assert elapsed >= 10
        assert elapsed < 1000  # Reasonable upper bound

    def test_cors_config_defaults(self) -> None:
        """Test CORSConfig default values."""
        from medex.api.middleware import CORSConfig

        config = CORSConfig()

        assert "*" in config.allow_origins
        assert "GET" in config.allow_methods
        assert "POST" in config.allow_methods
        assert "Content-Type" in config.allow_headers
        assert config.allow_credentials is True

    def test_security_config_defaults(self) -> None:
        """Test SecurityConfig default values."""
        from medex.api.middleware import SecurityConfig

        config = SecurityConfig()

        assert config.api_key_header == "X-API-Key"
        assert config.api_key_required is False  # Educational mode
        assert config.rate_limit_enabled is True
        assert config.rate_limit_requests == 100

    def test_security_middleware_rate_limiting(self) -> None:
        """Test SecurityMiddleware rate limiting logic."""
        from medex.api.middleware import (
            RequestContext,
            SecurityConfig,
            SecurityMiddleware,
        )

        config = SecurityConfig(rate_limit_enabled=True, rate_limit_requests=3)
        middleware = SecurityMiddleware(config)

        ctx = RequestContext(ip_address="192.168.1.1")

        # First 3 requests should pass
        for _ in range(3):
            assert middleware._check_rate_limit(ctx) is True

        # 4th request should fail
        assert middleware._check_rate_limit(ctx) is False
        assert ctx.rate_limit_remaining == 0

    def test_observability_config_defaults(self) -> None:
        """Test ObservabilityConfig default values."""
        from medex.api.middleware import ObservabilityConfig

        config = ObservabilityConfig()

        assert config.log_requests is True
        assert config.log_responses is True
        assert config.log_slow_requests_ms == 1000
        assert "/health" in config.exclude_paths
        assert "/metrics" in config.exclude_paths

    @pytest.mark.asyncio
    async def test_observability_middleware_metrics(self) -> None:
        """Test ObservabilityMiddleware metrics collection."""
        from medex.api.middleware import (
            ObservabilityConfig,
            ObservabilityMiddleware,
            RequestContext,
        )

        config = ObservabilityConfig(collect_metrics=True)
        middleware = ObservabilityMiddleware(config)

        ctx = RequestContext()

        # Process request
        await middleware.process_request(ctx, None)
        await middleware.process_response(ctx, None, None)

        metrics = middleware.get_metrics()

        assert metrics["total_requests"] == 1
        assert metrics["total_errors"] == 0
        assert metrics["avg_latency_ms"] > 0

    def test_error_handling_middleware_classification(self) -> None:
        """Test ErrorHandlingMiddleware error classification."""
        from medex.api.middleware import ErrorHandlingMiddleware
        from medex.api.models import ErrorCode

        middleware = ErrorHandlingMiddleware(debug=False)

        # Test different error types
        assert middleware._classify_error(ValueError()) == ErrorCode.INTERNAL_ERROR
        assert middleware._classify_error(TimeoutError()) == ErrorCode.TIMEOUT


# =============================================================================
# Health Route Tests
# =============================================================================


class TestHealthRoutesV2:
    """Tests for health check routes v2."""

    def test_health_status_enum(self) -> None:
        """Test HealthStatus enum values."""
        from medex.api.routes.health import HealthStatus

        assert HealthStatus.HEALTHY.value == "healthy"
        assert HealthStatus.DEGRADED.value == "degraded"
        assert HealthStatus.UNHEALTHY.value == "unhealthy"

    def test_component_health_to_dict(self) -> None:
        """Test ComponentHealth serialization."""
        from medex.api.routes.health import ComponentHealth, HealthStatus

        health = ComponentHealth(
            name="postgresql",
            status=HealthStatus.HEALTHY,
            latency_ms=5.5,
            message="Connected",
        )

        data = health.to_dict()

        assert data["name"] == "postgresql"
        assert data["status"] == "healthy"
        assert data["latency_ms"] == 5.5
        assert data["message"] == "Connected"

    @pytest.mark.asyncio
    async def test_health_router_live_endpoint(self) -> None:
        """Test liveness probe endpoint."""
        from medex.api.routes.health import HealthRouter

        router = HealthRouter(version="2.0.0")
        result = await router.live()

        assert result["alive"] is True
        assert "uptime_seconds" in result
        assert "timestamp" in result

    @pytest.mark.asyncio
    async def test_health_router_ready_endpoint(self) -> None:
        """Test readiness probe endpoint."""
        from medex.api.routes.health import HealthRouter

        router = HealthRouter(version="2.0.0")
        result = await router.ready()

        assert "ready" in result
        assert "status" in result

    @pytest.mark.asyncio
    async def test_database_health_check(self) -> None:
        """Test database health check."""
        from medex.api.routes.health import DatabaseHealthCheck, HealthStatus

        check = DatabaseHealthCheck()
        result = await check.check()

        assert result.name == "postgresql"
        assert result.status == HealthStatus.HEALTHY
        assert result.latency_ms >= 0

    @pytest.mark.asyncio
    async def test_health_router_aggregate_status(self) -> None:
        """Test health router aggregates component statuses."""
        from medex.api.routes.health import (
            DatabaseHealthCheck,
            HealthRouter,
            HealthStatus,
            RedisHealthCheck,
        )

        router = (
            HealthRouter(version="2.0.0")
            .add_check(DatabaseHealthCheck())
            .add_check(RedisHealthCheck())
        )

        result = await router.health()

        assert result.version == "2.0.0"
        assert len(result.components) == 2
        assert result.status in [HealthStatus.HEALTHY, HealthStatus.DEGRADED]


# =============================================================================
# Query Route Tests
# =============================================================================


class TestQueryRoutesV2:
    """Tests for query routes v2."""

    def test_medical_query_request_validation(self) -> None:
        """Test MedicalQueryRequest validation."""
        from medex.api.routes.query import MedicalQueryRequest

        # Valid request
        request = MedicalQueryRequest(
            query="¿Cuáles son los síntomas de la gripe?",
            user_type="educational",
        )
        errors = request.validate()
        assert len(errors) == 0

        # Invalid user_type
        request = MedicalQueryRequest(query="Valid query", user_type="invalid")
        errors = request.validate()
        assert any("user_type" in e for e in errors)

    def test_source_to_dict(self) -> None:
        """Test Source serialization."""
        from medex.api.routes.query import Source

        source = Source(
            id="src-1",
            title="Medical Reference",
            content="This is a very long content..." * 50,
            score=0.95,
        )

        data = source.to_dict()

        assert data["id"] == "src-1"
        assert data["score"] == 0.95
        assert len(data["content"]) <= 500  # Truncated

    def test_stream_chunk_to_sse(self) -> None:
        """Test StreamChunk SSE formatting."""
        from medex.api.routes.query import StreamChunk

        chunk = StreamChunk(type="streaming", data={"chunk": "Hello"})
        sse = chunk.to_sse()

        assert sse.startswith("data: ")
        assert sse.endswith("\n\n")
        assert '"type": "streaming"' in sse

    @pytest.mark.asyncio
    async def test_query_handler_sync_query(self) -> None:
        """Test QueryHandler synchronous query."""
        from medex.api.routes.query import MedicalQueryRequest, QueryHandler

        handler = QueryHandler()
        request = MedicalQueryRequest(
            query="¿Qué es la hipertensión?",
            user_type="educational",
        )

        response = await handler.query(request)

        assert response.query_id is not None
        assert response.response is not None
        assert response.user_type == "educational"
        assert response.duration_ms > 0

    @pytest.mark.asyncio
    async def test_query_handler_stream_query(self) -> None:
        """Test QueryHandler streaming query."""
        from medex.api.routes.query import MedicalQueryRequest, QueryHandler

        handler = QueryHandler()
        request = MedicalQueryRequest(
            query="¿Qué es la diabetes?",
            user_type="educational",
            stream=True,
        )

        chunks = []
        async for chunk in handler.stream(request):
            chunks.append(chunk)

        # Should have thinking, rag_search, streaming, and complete chunks
        assert len(chunks) > 0
        assert any(c.type == "thinking" for c in chunks)
        assert any(c.type == "complete" for c in chunks)

    @pytest.mark.asyncio
    async def test_query_handler_emergency_detection(self) -> None:
        """Test emergency detection in queries."""
        from medex.api.routes.query import MedicalQueryRequest, QueryHandler

        handler = QueryHandler()

        # Emergency query
        request = MedicalQueryRequest(query="Creo que estoy teniendo un infarto")
        response = await handler.query(request)
        assert response.is_emergency is True
        assert response.triage_level == 1

        # Non-emergency query
        request = MedicalQueryRequest(query="Tengo dolor de cabeza leve")
        response = await handler.query(request)
        assert response.is_emergency is False

    @pytest.mark.asyncio
    async def test_query_handler_search(self) -> None:
        """Test QueryHandler search functionality."""
        from medex.api.routes.query import QueryHandler, SearchRequest

        handler = QueryHandler()
        request = SearchRequest(
            query="diabetes tratamiento",
            limit=5,
        )

        response = await handler.search(request)

        assert response.query == "diabetes tratamiento"
        assert len(response.results) <= 5
        assert response.duration_ms > 0


# =============================================================================
# Admin Route Tests
# =============================================================================


class TestAdminRoutesV2:
    """Tests for admin routes v2."""

    @pytest.mark.asyncio
    async def test_admin_handler_get_metrics(self) -> None:
        """Test metrics endpoint."""
        from medex.api.routes.admin import AdminHandler

        handler = AdminHandler()
        response = await handler.get_metrics()

        assert "medex_requests_total" in response.metrics
        assert "medex_request_duration_seconds" in response.metrics

        # Test Prometheus format
        prometheus = response.to_prometheus()
        assert "# HELP" in prometheus
        assert "# TYPE" in prometheus

    @pytest.mark.asyncio
    async def test_admin_handler_get_audit_logs(self) -> None:
        """Test audit logs endpoint."""
        from medex.api.routes.admin import AdminHandler

        handler = AdminHandler()
        response = await handler.get_audit_logs(page=1, page_size=10)

        assert response.page == 1
        assert response.page_size == 10
        assert len(response.entries) <= 10

    @pytest.mark.asyncio
    async def test_admin_handler_clear_cache(self) -> None:
        """Test cache clear endpoint."""
        from medex.api.routes.admin import AdminHandler

        handler = AdminHandler()
        response = await handler.clear_cache(pattern="query:*")

        assert response.cleared is True
        assert response.keys_removed > 0
        assert "query:*" in response.message

    @pytest.mark.asyncio
    async def test_admin_handler_get_config(self) -> None:
        """Test config endpoint."""
        from medex.api.routes.admin import AdminHandler

        handler = AdminHandler()
        response = await handler.get_config()

        assert response.version == "2.0.0"
        assert "streaming" in response.features
        assert "websocket" in response.features
        assert len(response.providers) > 0


# =============================================================================
# WebSocket Tests
# =============================================================================


class TestWebSocketV2:
    """Tests for WebSocket handling v2."""

    def test_ws_message_type_enum(self) -> None:
        """Test WSMessageType enum values."""
        from medex.api.websocket import WSMessageType

        # Client -> Server
        assert WSMessageType.QUERY.value == "query"
        assert WSMessageType.CANCEL.value == "cancel"
        assert WSMessageType.PING.value == "ping"

        # Server -> Client
        assert WSMessageType.STREAMING.value == "streaming"
        assert WSMessageType.COMPLETE.value == "complete"
        assert WSMessageType.ERROR.value == "error"

    def test_ws_message_serialization(self) -> None:
        """Test WSMessage JSON serialization."""
        from medex.api.websocket import WSMessage, WSMessageType

        msg = WSMessage(type=WSMessageType.STREAMING, data={"chunk": "Hello"})
        json_str = msg.to_json()

        assert '"type": "streaming"' in json_str
        assert '"chunk": "Hello"' in json_str

        # Roundtrip
        parsed = WSMessage.from_json(json_str)
        assert parsed.type == WSMessageType.STREAMING
        assert parsed.data["chunk"] == "Hello"

    def test_connection_state_creation(self) -> None:
        """Test ConnectionState default values."""
        from medex.api.websocket import ConnectionState

        state = ConnectionState()

        assert state.connection_id is not None
        assert state.is_processing is False
        assert state.messages_received == 0
        assert state.queries_processed == 0

    @pytest.mark.asyncio
    async def test_websocket_handler_connect_disconnect(self) -> None:
        """Test WebSocket connection lifecycle."""
        from medex.api.websocket import WebSocketHandler

        handler = WebSocketHandler()

        # Connect
        state = await handler.on_connect("conn-1", session_id="sess-1")
        assert state.connection_id == "conn-1"
        assert state.session_id == "sess-1"
        assert handler.active_connections == 1

        # Disconnect
        await handler.on_disconnect("conn-1")
        assert handler.active_connections == 0

    @pytest.mark.asyncio
    async def test_websocket_handler_ping_pong(self) -> None:
        """Test WebSocket ping/pong."""
        import json

        from medex.api.websocket import WebSocketHandler, WSMessageType

        handler = WebSocketHandler()
        await handler.on_connect("conn-1")

        responses = await handler.on_message(
            "conn-1", json.dumps({"type": "ping", "data": {}})
        )

        assert len(responses) == 1
        assert responses[0].type == WSMessageType.PONG

    @pytest.mark.asyncio
    async def test_websocket_handler_query(self) -> None:
        """Test WebSocket query handling."""
        import json

        from medex.api.websocket import WebSocketHandler, WSMessageType

        handler = WebSocketHandler()
        await handler.on_connect("conn-1")

        responses = await handler.on_message(
            "conn-1",
            json.dumps(
                {
                    "type": "query",
                    "data": {"query": "¿Qué es la diabetes?"},
                }
            ),
        )

        # Should have multiple response messages
        assert len(responses) > 0
        assert any(r.type == WSMessageType.THINKING for r in responses)
        assert any(r.type == WSMessageType.COMPLETE for r in responses)

    @pytest.mark.asyncio
    async def test_websocket_handler_invalid_message(self) -> None:
        """Test WebSocket invalid message handling."""
        from medex.api.websocket import WebSocketHandler, WSMessageType

        handler = WebSocketHandler()
        await handler.on_connect("conn-1")

        responses = await handler.on_message("conn-1", "not valid json")

        assert len(responses) == 1
        assert responses[0].type == WSMessageType.ERROR
        assert "invalid_json" in responses[0].data["code"]

    def test_websocket_handler_stats(self) -> None:
        """Test WebSocket statistics."""
        from medex.api.websocket import WebSocketHandler

        handler = WebSocketHandler()

        # Empty stats
        stats = handler.get_connection_stats()
        assert stats["active_connections"] == 0


# =============================================================================
# App Tests
# =============================================================================


class TestAppV2:
    """Tests for FastAPI application v2."""

    def test_app_config_defaults(self) -> None:
        """Test AppConfig default values."""
        from medex.api.app import AppConfig

        config = AppConfig()

        assert config.title == "MedeX API"
        assert config.version == "2.0.0"
        assert config.port == 8000
        assert config.debug is False
        assert config.enable_websocket is True

    def test_app_state_uptime(self) -> None:
        """Test AppState uptime calculation."""
        from medex.api.app import AppState

        state = AppState()
        time.sleep(0.01)

        assert state.uptime_seconds > 0

    def test_medex_app_creation(self) -> None:
        """Test MedeXApp creation."""
        from medex.api.app import AppConfig, MedeXApp

        config = AppConfig(title="Test App", version="1.0.0")
        app = MedeXApp(config=config)

        assert app.config.title == "Test App"
        assert app.config.version == "1.0.0"
        assert app.state.is_ready is False

    def test_openapi_schema_generation(self) -> None:
        """Test OpenAPI schema generation."""
        from medex.api.app import MedeXApp

        app = MedeXApp()
        schema = app.create_openapi_schema()

        assert schema["openapi"] == "3.1.0"
        assert schema["info"]["title"] == "MedeX API"
        assert "/health" in schema["paths"]
        assert "/query" in schema["paths"]
        assert "/ws" in schema["paths"]

    @pytest.mark.asyncio
    async def test_medex_app_startup_shutdown(self) -> None:
        """Test MedeXApp startup and shutdown."""
        from medex.api.app import MedeXApp

        app = MedeXApp()

        # Before startup
        assert app.state.is_ready is False

        # Startup
        await app.startup()
        assert app.state.is_ready is True
        assert app.state.agent_service is not None

        # Shutdown
        await app.shutdown()
        assert app.state.is_ready is False


# =============================================================================
# Error Handling Tests
# =============================================================================


class TestErrorHandlingV2:
    """Tests for error handling v2."""

    @pytest.mark.asyncio
    async def test_validation_error_handling(self) -> None:
        """Test validation error produces correct response."""
        from medex.api.routes.query import MedicalQueryRequest, QueryHandler

        handler = QueryHandler()

        # Invalid request
        request = MedicalQueryRequest(query="ab")  # Too short

        with pytest.raises(ValueError) as exc_info:
            await handler.query(request)

        assert "Validation errors" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_error_middleware_formats_error(self) -> None:
        """Test ErrorHandlingMiddleware formats errors correctly."""
        from medex.api.middleware import ErrorHandlingMiddleware, RequestContext
        from medex.api.models import ErrorCode

        middleware = ErrorHandlingMiddleware(debug=False)
        ctx = RequestContext(request_id="test-123")

        error = ValueError("Test error")
        result = await middleware.handle_error(ctx, None, error)

        assert result is not None
        assert result.code == ErrorCode.INTERNAL_ERROR
        assert result.request_id == "test-123"

    def test_api_error_user_messages(self) -> None:
        """Test APIError provides user-friendly messages."""
        from medex.api.middleware import ErrorHandlingMiddleware
        from medex.api.models import ErrorCode

        middleware = ErrorHandlingMiddleware(debug=False)

        # Test Spanish messages
        msg = middleware._get_user_message(ErrorCode.RATE_LIMITED)
        assert "Demasiadas solicitudes" in msg

        msg = middleware._get_user_message(ErrorCode.INTERNAL_ERROR)
        assert "Error interno" in msg


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
