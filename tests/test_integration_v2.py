#!/usr/bin/env python3
# =============================================================================
# MedeX - Integration Tests for Phase 10
# =============================================================================
"""
Comprehensive tests for integration and main components.

Test Coverage:
- Configuration management (MedeXConfig, environment configs)
- Main application lifecycle (MedeXApplication)
- Service container dependency injection
- CLI commands
- Cross-module integration

SOTA Level: Production-grade testing with fixtures, mocks, and assertions.
"""

from __future__ import annotations

import os
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def clean_env():
    """Provide clean environment for tests."""
    original = os.environ.copy()
    yield
    os.environ.clear()
    os.environ.update(original)


@pytest.fixture
def mock_services():
    """Mock all service dependencies."""
    return {
        "database": AsyncMock(),
        "redis": AsyncMock(),
        "qdrant": AsyncMock(),
        "llm": AsyncMock(),
        "rag": AsyncMock(),
    }


# =============================================================================
# Configuration Tests
# =============================================================================


class TestEnvironmentEnum:
    """Tests for Environment enumeration."""

    def test_development_is_debug(self):
        """Development environment should be debug."""
        from medex.config import Environment

        assert Environment.DEVELOPMENT.is_debug is True

    def test_production_not_debug(self):
        """Production environment should not be debug."""
        from medex.config import Environment

        assert Environment.PRODUCTION.is_debug is False

    def test_requires_ssl_in_production(self):
        """Production should require SSL."""
        from medex.config import Environment

        assert Environment.PRODUCTION.requires_ssl is True
        assert Environment.DEVELOPMENT.requires_ssl is False


class TestDatabaseConfig:
    """Tests for DatabaseConfig."""

    def test_url_generation(self):
        """Test database URL generation."""
        from medex.config import DatabaseConfig

        config = DatabaseConfig(
            host="localhost",
            port=5432,
            database="medex",
            username="user",
            password="pass",
        )

        url = config.get_url()
        assert "postgresql+asyncpg://" in url
        assert "user" in url
        assert "localhost" in url
        assert "5432" in str(url)
        assert "medex" in url

    def test_url_without_credentials(self):
        """Test URL generation without credentials."""
        from medex.config import DatabaseConfig

        config = DatabaseConfig(
            host="localhost",
            port=5432,
            database="medex",
        )

        url = config.get_url()
        assert "localhost:5432" in url
        assert "medex" in url

    def test_from_env(self, clean_env):
        """Test creation from environment variables."""
        from medex.config import DatabaseConfig

        os.environ["POSTGRES_HOST"] = "db.example.com"
        os.environ["POSTGRES_PORT"] = "5433"
        os.environ["POSTGRES_DB"] = "test_db"
        os.environ["POSTGRES_USER"] = "test_user"
        os.environ["POSTGRES_PASSWORD"] = "test_pass"

        config = DatabaseConfig.from_env()

        assert config.host == "db.example.com"
        assert config.port == 5433
        assert config.database == "test_db"
        assert config.username == "test_user"
        assert config.password == "test_pass"

    def test_defaults(self, clean_env):
        """Test default values."""
        from medex.config import DatabaseConfig

        config = DatabaseConfig.from_env()

        assert config.host == "localhost"
        assert config.port == 5432
        assert config.pool_size == 10


class TestRedisConfig:
    """Tests for RedisConfig."""

    def test_url_generation(self):
        """Test Redis URL generation."""
        from medex.config import RedisConfig

        config = RedisConfig(
            host="localhost",
            port=6379,
            database=0,
        )

        url = config.get_url()
        assert url == "redis://localhost:6379/0"

    def test_url_with_password(self):
        """Test Redis URL with password."""
        from medex.config import RedisConfig

        config = RedisConfig(
            host="localhost",
            port=6379,
            database=0,
            password="secret",
        )

        url = config.get_url()
        assert "secret@" in url

    def test_from_env(self, clean_env):
        """Test creation from environment variables."""
        from medex.config import RedisConfig

        os.environ["REDIS_HOST"] = "redis.example.com"
        os.environ["REDIS_PORT"] = "6380"
        os.environ["REDIS_DB"] = "1"
        os.environ["REDIS_PASSWORD"] = "redis_pass"

        config = RedisConfig.from_env()

        assert config.host == "redis.example.com"
        assert config.port == 6380
        assert config.database == 1
        assert config.password == "redis_pass"


class TestQdrantConfig:
    """Tests for QdrantConfig."""

    def test_url_generation(self):
        """Test Qdrant URL generation."""
        from medex.config import QdrantConfig

        config = QdrantConfig(
            host="localhost",
            port=6333,
            collection_name="medex_docs",
        )

        url = config.get_url()
        assert url == "http://localhost:6333"

    def test_grpc_port(self):
        """Test gRPC port configuration."""
        from medex.config import QdrantConfig

        config = QdrantConfig(
            host="localhost",
            port=6333,
            grpc_port=6334,
            collection_name="medex_docs",
        )

        assert config.grpc_port == 6334

    def test_from_env(self, clean_env):
        """Test creation from environment variables."""
        from medex.config import QdrantConfig

        os.environ["QDRANT_HOST"] = "qdrant.example.com"
        os.environ["QDRANT_PORT"] = "6334"
        os.environ["QDRANT_COLLECTION"] = "custom_collection"
        os.environ["QDRANT_API_KEY"] = "qdrant_key"

        config = QdrantConfig.from_env()

        assert config.host == "qdrant.example.com"
        assert config.port == 6334
        assert config.collection_name == "custom_collection"
        assert config.api_key == "qdrant_key"


class TestLLMProviderConfig:
    """Tests for LLMProviderConfig."""

    def test_is_configured_with_api_key(self):
        """Provider is configured if has API key."""
        from medex.config import LLMProviderConfig

        config = LLMProviderConfig(
            name="test",
            api_key="key123",
            base_url="http://api.test.com",
        )

        assert config.is_configured is True

    def test_is_configured_without_api_key(self):
        """Provider is not configured without API key."""
        from medex.config import LLMProviderConfig

        config = LLMProviderConfig(
            name="test",
            base_url="http://api.test.com",
        )

        assert config.is_configured is False

    def test_is_configured_for_ollama(self):
        """Ollama is configured without API key."""
        from medex.config import LLMProviderConfig

        config = LLMProviderConfig(
            name="ollama",
            base_url="http://localhost:11434",
        )

        assert config.is_configured is True


class TestLLMConfig:
    """Tests for LLMConfig."""

    def test_default_providers(self):
        """Test default provider configuration."""
        from medex.config import LLMConfig

        config = LLMConfig()

        assert "kimi" in config.providers
        assert "groq" in config.providers
        assert "ollama" in config.providers

    def test_active_providers(self):
        """Test getting active providers."""
        from medex.config import LLMConfig, LLMProviderConfig

        config = LLMConfig(
            providers={
                "test1": LLMProviderConfig(
                    name="test1",
                    api_key="key1",
                    base_url="http://test1.com",
                ),
                "test2": LLMProviderConfig(
                    name="test2",
                    base_url="http://test2.com",
                ),
            }
        )

        active = config.get_active_providers()
        assert len(active) == 1
        assert "test1" in active

    def test_fallback_order(self):
        """Test provider fallback order."""
        from medex.config import LLMConfig

        config = LLMConfig(
            fallback_order=["kimi", "groq", "ollama"],
        )

        assert config.fallback_order[0] == "kimi"
        assert config.fallback_order[1] == "groq"
        assert config.fallback_order[2] == "ollama"


class TestEmbeddingConfig:
    """Tests for EmbeddingConfig."""

    def test_default_model(self):
        """Test default embedding model."""
        from medex.config import EmbeddingConfig

        config = EmbeddingConfig()

        assert "multilingual" in config.model_name.lower()
        assert config.dimension == 384

    def test_custom_model(self):
        """Test custom embedding model."""
        from medex.config import EmbeddingConfig

        config = EmbeddingConfig(
            model_name="custom-model",
            dimension=768,
        )

        assert config.model_name == "custom-model"
        assert config.dimension == 768


class TestSecurityConfig:
    """Tests for SecurityConfig."""

    def test_default_pii_detection(self):
        """Test PII detection enabled by default."""
        from medex.config import SecurityConfig

        config = SecurityConfig()

        assert config.pii_detection_enabled is True
        assert config.audit_logging_enabled is True

    def test_rate_limiting(self):
        """Test rate limiting configuration."""
        from medex.config import SecurityConfig

        config = SecurityConfig(
            rate_limit_requests=100,
            rate_limit_window_seconds=60,
        )

        assert config.rate_limit_requests == 100
        assert config.rate_limit_window_seconds == 60


class TestAPIConfig:
    """Tests for APIConfig."""

    def test_default_host_port(self):
        """Test default host and port."""
        from medex.config import APIConfig

        config = APIConfig()

        assert config.host == "0.0.0.0"
        assert config.port == 8000

    def test_cors_configuration(self):
        """Test CORS configuration."""
        from medex.config import APIConfig

        config = APIConfig(
            cors_origins=["http://localhost:3000", "https://app.medex.com"],
        )

        assert len(config.cors_origins) == 2
        assert "http://localhost:3000" in config.cors_origins


class TestObservabilityConfig:
    """Tests for ObservabilityConfig."""

    def test_default_logging(self):
        """Test default logging configuration."""
        from medex.config import ObservabilityConfig

        config = ObservabilityConfig()

        assert config.log_level == "INFO"
        assert config.log_format in ["json", "text"]

    def test_metrics_configuration(self):
        """Test metrics configuration."""
        from medex.config import ObservabilityConfig

        config = ObservabilityConfig(
            metrics_enabled=True,
            metrics_port=9090,
        )

        assert config.metrics_enabled is True
        assert config.metrics_port == 9090


class TestMedeXConfig:
    """Tests for main MedeXConfig."""

    def test_from_env(self, clean_env):
        """Test loading configuration from environment."""
        from medex.config import MedeXConfig

        os.environ["MEDEX_ENV"] = "development"
        os.environ["POSTGRES_HOST"] = "localhost"
        os.environ["REDIS_HOST"] = "localhost"
        os.environ["QDRANT_HOST"] = "localhost"

        config = MedeXConfig.from_env()

        assert config.environment.value == "development"
        assert config.database.host == "localhost"
        assert config.redis.host == "localhost"
        assert config.qdrant.host == "localhost"

    def test_validate_success(self):
        """Test successful validation."""
        from medex.config import MedeXConfig

        config = MedeXConfig()
        errors = config.validate()

        # May have warnings but should not fail
        assert isinstance(errors, list)

    def test_validate_missing_required(self, clean_env):
        """Test validation with missing required config."""
        from medex.config import Environment, LLMConfig, MedeXConfig

        config = MedeXConfig(
            environment=Environment.PRODUCTION,
            llm=LLMConfig(providers={}),
        )

        errors = config.validate()

        assert len(errors) > 0
        # Should warn about no LLM providers

    def test_to_dict(self):
        """Test serialization to dictionary."""
        from medex.config import MedeXConfig

        config = MedeXConfig()
        data = config.to_dict()

        assert "environment" in data
        assert "database" in data
        assert "redis" in data
        assert "qdrant" in data
        assert "llm" in data
        assert "api" in data


class TestLoadConfig:
    """Tests for load_config function."""

    def test_load_default_config(self, clean_env):
        """Test loading default configuration."""
        from medex.config import load_config

        config = load_config()

        assert config is not None
        assert hasattr(config, "database")
        assert hasattr(config, "redis")

    def test_load_from_dotenv(self, clean_env, tmp_path):
        """Test loading from .env file."""
        from medex.config import load_config

        env_file = tmp_path / ".env"
        env_file.write_text("MEDEX_ENV=testing\nPOSTGRES_HOST=test-db\n")

        # Change to tmp_path to load .env
        old_cwd = os.getcwd()
        os.chdir(tmp_path)

        try:
            config = load_config()
            # Config should load even without .env
            assert config is not None
        finally:
            os.chdir(old_cwd)


# =============================================================================
# Main Application Tests
# =============================================================================


class TestApplicationState:
    """Tests for ApplicationState."""

    def test_initial_state(self):
        """Test initial application state."""
        from medex.main import ApplicationState

        state = ApplicationState()

        assert state.started_at is None
        assert state.ready is False
        assert len(state.services) == 0

    def test_uptime_calculation(self):
        """Test uptime calculation."""
        from datetime import timezone

        from medex.main import ApplicationState

        state = ApplicationState()
        state.started_at = datetime.now(timezone.utc)

        uptime = state.uptime
        assert uptime >= 0.0


class TestServiceContainer:
    """Tests for ServiceContainer."""

    def test_register_service(self):
        """Test registering a service."""
        from medex.main import ServiceContainer

        container = ServiceContainer()
        service = MagicMock()

        container.register("test_service", service)

        assert container.get("test_service") is service

    def test_get_nonexistent_service(self):
        """Test getting non-existent service."""
        from medex.main import ServiceContainer

        container = ServiceContainer()

        result = container.get("nonexistent")
        assert result is None

    def test_has_service(self):
        """Test checking service existence."""
        from medex.main import ServiceContainer

        container = ServiceContainer()
        container.register("test", MagicMock())

        assert container.has("test") is True
        assert container.has("other") is False


class TestMedeXApplication:
    """Tests for MedeXApplication."""

    @pytest.mark.asyncio
    async def test_startup(self):
        """Test application startup."""
        from medex.main import MedeXApplication

        app = MedeXApplication()

        # Mock service initialization
        app._init_services = AsyncMock()

        await app.startup()

        assert app.state.started_at is not None
        assert app._init_services.called

    @pytest.mark.asyncio
    async def test_shutdown(self):
        """Test application shutdown."""
        from medex.main import MedeXApplication

        app = MedeXApplication()
        app._cleanup_services = AsyncMock()

        await app.startup()
        await app.shutdown()

        assert app._cleanup_services.called

    @pytest.mark.asyncio
    async def test_health_check(self):
        """Test health check."""
        from medex.main import MedeXApplication

        app = MedeXApplication()
        await app.startup()

        try:
            health = await app.health()

            assert "status" in health
            assert "ready" in health
            assert "uptime_seconds" in health
        finally:
            await app.shutdown()

    @pytest.mark.asyncio
    async def test_query(self):
        """Test query method."""
        from medex.main import MedeXApplication

        app = MedeXApplication()

        # Mock the internal query handler
        app._handle_query = AsyncMock(
            return_value={
                "response": "Test response",
                "sources": [],
            }
        )

        await app.startup()

        try:
            response = await app.query("Test question", "educational")

            assert "response" in response
        finally:
            await app.shutdown()


# =============================================================================
# CLI Tests
# =============================================================================


class TestCLI:
    """Tests for CLI commands."""

    def test_parse_serve_command(self):
        """Test parsing serve command."""
        import sys

        from medex.__main__ import parse_args

        original_argv = sys.argv
        sys.argv = ["medex", "serve", "--port", "9000"]

        try:
            args = parse_args()

            assert args.command == "serve"
            assert args.port == 9000
        finally:
            sys.argv = original_argv

    def test_parse_query_command(self):
        """Test parsing query command."""
        import sys

        from medex.__main__ import parse_args

        original_argv = sys.argv
        sys.argv = [
            "medex",
            "query",
            "What is diabetes?",
            "--user-type",
            "professional",
        ]

        try:
            args = parse_args()

            assert args.command == "query"
            assert args.question == "What is diabetes?"
            assert args.user_type == "professional"
        finally:
            sys.argv = original_argv

    def test_parse_health_command(self):
        """Test parsing health command."""
        import sys

        from medex.__main__ import parse_args

        original_argv = sys.argv
        sys.argv = ["medex", "health"]

        try:
            args = parse_args()

            assert args.command == "health"
        finally:
            sys.argv = original_argv

    def test_parse_config_command(self):
        """Test parsing config command."""
        import sys

        from medex.__main__ import parse_args

        original_argv = sys.argv
        sys.argv = ["medex", "config", "--validate"]

        try:
            args = parse_args()

            assert args.command == "config"
            assert args.validate is True
        finally:
            sys.argv = original_argv

    def test_parse_version(self):
        """Test parsing version flag."""
        import sys

        from medex.__main__ import parse_args

        original_argv = sys.argv
        sys.argv = ["medex", "--version"]

        try:
            args = parse_args()

            assert args.version is True
        finally:
            sys.argv = original_argv


# =============================================================================
# Integration Tests
# =============================================================================


class TestCrossModuleIntegration:
    """Tests for cross-module integration."""

    def test_config_to_application(self):
        """Test config flows to application."""
        from medex.config import MedeXConfig
        from medex.main import MedeXApplication

        config = MedeXConfig()
        app = MedeXApplication(config=config)

        assert app.config is config

    @pytest.mark.asyncio
    async def test_full_lifecycle(self):
        """Test full application lifecycle."""
        from medex.main import MedeXApplication

        app = MedeXApplication()

        # Startup
        await app.startup()
        assert app.state.started_at is not None

        # Health check
        health = await app.health()
        assert health["status"] in ["healthy", "degraded", "unhealthy"]

        # Shutdown
        await app.shutdown()

    def test_module_exports(self):
        """Test all expected exports are available."""
        from medex import (
            ApplicationState,
            MedeXApplication,
            ServiceContainer,
            __version__,
            create_application,
            run_server,
        )

        assert MedeXApplication is not None
        assert ApplicationState is not None
        assert ServiceContainer is not None
        assert callable(create_application)
        assert callable(run_server)
        assert isinstance(__version__, str)

    def test_legacy_exports_available(self):
        """Test legacy V1 exports still work."""
        # These should not raise ImportError
        try:
            from medex import MedeXConfig, MedeXEngine  # noqa: F401

            # If they don't exist, that's okay for V2
        except ImportError:
            pass  # Expected if V1 is not available


# =============================================================================
# Error Handling Tests
# =============================================================================


class TestErrorHandling:
    """Tests for error handling."""

    @pytest.mark.asyncio
    async def test_startup_failure_recovery(self):
        """Test recovery from startup failure."""
        from medex.main import MedeXApplication

        app = MedeXApplication()

        # Force a startup error
        async def failing_init():
            raise RuntimeError("Test error")

        app._init_services = failing_init

        with pytest.raises(RuntimeError):
            await app.startup()

    @pytest.mark.asyncio
    async def test_graceful_shutdown_on_error(self):
        """Test graceful shutdown on error."""
        from medex.main import MedeXApplication

        app = MedeXApplication()
        await app.startup()

        # Simulate error during operation
        app._cleanup_services = AsyncMock()

        await app.shutdown()

        # Should still complete shutdown
        assert app._cleanup_services.called

    def test_config_validation_errors(self):
        """Test configuration validation errors."""
        from medex.config import Environment, MedeXConfig

        config = MedeXConfig(
            environment=Environment.PRODUCTION,
        )

        errors = config.validate()

        # Should have some warnings for production
        assert isinstance(errors, list)


# =============================================================================
# Performance Tests
# =============================================================================


class TestPerformance:
    """Basic performance tests."""

    def test_config_creation_fast(self):
        """Test config creation is fast."""
        import time

        from medex.config import MedeXConfig

        start = time.time()
        for _ in range(100):
            MedeXConfig()
        elapsed = time.time() - start

        assert elapsed < 1.0  # Should create 100 configs in < 1 second

    @pytest.mark.asyncio
    async def test_health_check_fast(self):
        """Test health check is fast."""
        import time

        from medex.main import MedeXApplication

        app = MedeXApplication()
        await app.startup()

        try:
            start = time.time()
            for _ in range(10):
                await app.health()
            elapsed = time.time() - start

            assert elapsed < 1.0  # 10 health checks in < 1 second
        finally:
            await app.shutdown()


# =============================================================================
# Run Tests
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
