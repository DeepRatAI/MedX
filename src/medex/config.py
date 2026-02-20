# =============================================================================
# MedeX - Configuration Management
# =============================================================================
"""
Centralized configuration for MedeX application.

Supports:
- Environment variables
- .env files
- Default values
- Validation
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


# =============================================================================
# Environment
# =============================================================================


class Environment(str, Enum):
    """Application environment."""

    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


# =============================================================================
# Database Configuration
# =============================================================================


@dataclass
class DatabaseConfig:
    """PostgreSQL database configuration."""

    host: str = "localhost"
    port: int = 5432
    database: str = "medex"
    username: str = "medex"
    password: str = "medex_secret"

    # Pool settings
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    pool_recycle: int = 1800

    # SSL
    ssl_mode: str = "prefer"

    @property
    def url(self) -> str:
        """Get database URL."""
        return f"postgresql+asyncpg://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"

    @property
    def sync_url(self) -> str:
        """Get synchronous database URL."""
        return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"

    @classmethod
    def from_env(cls) -> "DatabaseConfig":
        """Create from environment variables."""
        return cls(
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=int(os.getenv("POSTGRES_PORT", "5432")),
            database=os.getenv("POSTGRES_DB", "medex"),
            username=os.getenv("POSTGRES_USER", "medex"),
            password=os.getenv("POSTGRES_PASSWORD", "medex_secret"),
            pool_size=int(os.getenv("DB_POOL_SIZE", "10")),
            max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "20")),
        )


# =============================================================================
# Redis Configuration
# =============================================================================


@dataclass
class RedisConfig:
    """Redis cache configuration."""

    host: str = "localhost"
    port: int = 6379
    password: str | None = None
    database: int = 0

    # Pool settings
    max_connections: int = 50

    # Timeouts
    socket_timeout: float = 5.0
    socket_connect_timeout: float = 5.0

    # SSL
    ssl: bool = False

    @property
    def url(self) -> str:
        """Get Redis URL."""
        auth = f":{self.password}@" if self.password else ""
        return f"redis://{auth}{self.host}:{self.port}/{self.database}"

    @classmethod
    def from_env(cls) -> "RedisConfig":
        """Create from environment variables."""
        return cls(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", "6379")),
            password=os.getenv("REDIS_PASSWORD"),
            database=int(os.getenv("REDIS_DB", "0")),
            max_connections=int(os.getenv("REDIS_MAX_CONNECTIONS", "50")),
        )


# =============================================================================
# Qdrant Configuration
# =============================================================================


@dataclass
class QdrantConfig:
    """Qdrant vector database configuration."""

    host: str = "localhost"
    port: int = 6333
    grpc_port: int = 6334
    api_key: str | None = None

    # Collection settings
    collection_name: str = "medical_knowledge"
    vector_size: int = 384  # MiniLM-L12
    distance: str = "Cosine"

    # Performance
    prefer_grpc: bool = True
    timeout: float = 30.0

    @property
    def url(self) -> str:
        """Get Qdrant URL."""
        return f"http://{self.host}:{self.port}"

    @classmethod
    def from_env(cls) -> "QdrantConfig":
        """Create from environment variables."""
        return cls(
            host=os.getenv("QDRANT_HOST", "localhost"),
            port=int(os.getenv("QDRANT_PORT", "6333")),
            grpc_port=int(os.getenv("QDRANT_GRPC_PORT", "6334")),
            api_key=os.getenv("QDRANT_API_KEY"),
            collection_name=os.getenv("QDRANT_COLLECTION", "medical_knowledge"),
            vector_size=int(os.getenv("QDRANT_VECTOR_SIZE", "384")),
        )


# =============================================================================
# LLM Configuration
# =============================================================================


@dataclass
class LLMProviderConfig:
    """Configuration for a single LLM provider."""

    name: str
    api_key: str | None = None
    base_url: str | None = None
    model: str | None = None
    enabled: bool = True
    priority: int = 0
    max_tokens: int = 8192
    timeout: float = 120.0


@dataclass
class LLMConfig:
    """LLM providers configuration."""

    # Provider-specific configs
    providers: list[LLMProviderConfig] = field(default_factory=list)

    # Default settings
    default_provider: str = "groq"
    default_model: str = "llama-3.3-70b-versatile"

    # Fallback settings
    enable_fallback: bool = True
    fallback_order: list[str] = field(
        default_factory=lambda: ["groq", "together", "cerebras", "ollama"]
    )

    # Rate limiting
    requests_per_minute: int = 30
    tokens_per_minute: int = 100000

    @classmethod
    def from_env(cls) -> "LLMConfig":
        """Create from environment variables."""
        providers = []

        # Groq
        if os.getenv("GROQ_API_KEY"):
            providers.append(
                LLMProviderConfig(
                    name="groq",
                    api_key=os.getenv("GROQ_API_KEY"),
                    model="llama-3.3-70b-versatile",
                    priority=1,
                )
            )

        # Together
        if os.getenv("TOGETHER_API_KEY"):
            providers.append(
                LLMProviderConfig(
                    name="together",
                    api_key=os.getenv("TOGETHER_API_KEY"),
                    model="meta-llama/Llama-3.3-70B-Instruct-Turbo",
                    priority=2,
                )
            )

        # Cerebras
        if os.getenv("CEREBRAS_API_KEY"):
            providers.append(
                LLMProviderConfig(
                    name="cerebras",
                    api_key=os.getenv("CEREBRAS_API_KEY"),
                    model="llama-3.3-70b",
                    priority=3,
                )
            )

        # OpenRouter
        if os.getenv("OPENROUTER_API_KEY"):
            providers.append(
                LLMProviderConfig(
                    name="openrouter",
                    api_key=os.getenv("OPENROUTER_API_KEY"),
                    base_url="https://openrouter.ai/api/v1",
                    model="moonshotai/kimi-k2",
                    priority=4,
                )
            )

        # DeepSeek
        if os.getenv("DEEPSEEK_API_KEY"):
            providers.append(
                LLMProviderConfig(
                    name="deepseek",
                    api_key=os.getenv("DEEPSEEK_API_KEY"),
                    base_url="https://api.deepseek.com/v1",
                    model="deepseek-chat",
                    priority=5,
                )
            )

        # Ollama (local)
        if os.getenv("OLLAMA_ENABLED", "true").lower() == "true":
            providers.append(
                LLMProviderConfig(
                    name="ollama",
                    base_url=os.getenv("OLLAMA_HOST", "http://localhost:11434"),
                    model=os.getenv("OLLAMA_MODEL", "llama3.2"),
                    priority=10,  # Last resort
                )
            )

        return cls(
            providers=providers,
            default_provider=os.getenv("DEFAULT_LLM_PROVIDER", "groq"),
            enable_fallback=os.getenv("LLM_FALLBACK_ENABLED", "true").lower() == "true",
        )


# =============================================================================
# Embedding Configuration
# =============================================================================


@dataclass
class EmbeddingConfig:
    """Embedding model configuration."""

    model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    device: str = "cpu"  # cpu, cuda, mps
    batch_size: int = 32
    max_length: int = 512
    normalize: bool = True

    # Cache settings
    cache_embeddings: bool = True
    cache_ttl: int = 86400  # 24 hours

    @classmethod
    def from_env(cls) -> "EmbeddingConfig":
        """Create from environment variables."""
        return cls(
            model_name=os.getenv(
                "EMBEDDING_MODEL",
                "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
            ),
            device=os.getenv("EMBEDDING_DEVICE", "cpu"),
            batch_size=int(os.getenv("EMBEDDING_BATCH_SIZE", "32")),
        )


# =============================================================================
# Security Configuration
# =============================================================================


@dataclass
class SecurityConfig:
    """Security configuration."""

    # API keys
    api_key_required: bool = False  # Educational mode
    api_keys: set[str] = field(default_factory=set)

    # Rate limiting
    rate_limit_enabled: bool = True
    rate_limit_requests: int = 100
    rate_limit_window: int = 60

    # PII detection
    pii_detection_enabled: bool = True
    pii_types: set[str] = field(
        default_factory=lambda: {
            "dni",
            "curp",
            "rut",
            "cuil",
            "cuit",
            "cpf",
            "email",
            "phone",
            "credit_card",
            "ssn",
        }
    )

    # Audit
    audit_enabled: bool = True
    audit_retention_days: int = 90

    # Content filtering
    content_filter_enabled: bool = True
    blocked_patterns: list[str] = field(default_factory=list)

    @classmethod
    def from_env(cls) -> "SecurityConfig":
        """Create from environment variables."""
        api_keys_str = os.getenv("API_KEYS", "")
        api_keys = set(api_keys_str.split(",")) if api_keys_str else set()

        return cls(
            api_key_required=os.getenv("API_KEY_REQUIRED", "false").lower() == "true",
            api_keys=api_keys,
            rate_limit_enabled=os.getenv("RATE_LIMIT_ENABLED", "true").lower()
            == "true",
            rate_limit_requests=int(os.getenv("RATE_LIMIT_REQUESTS", "100")),
            pii_detection_enabled=os.getenv("PII_DETECTION", "true").lower() == "true",
            audit_enabled=os.getenv("AUDIT_ENABLED", "true").lower() == "true",
        )


# =============================================================================
# API Configuration
# =============================================================================


@dataclass
class APIConfig:
    """API server configuration."""

    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1
    debug: bool = False

    # CORS
    cors_origins: list[str] = field(default_factory=lambda: ["*"])
    cors_allow_credentials: bool = True

    # Timeouts
    request_timeout: float = 60.0
    keep_alive: int = 5

    # Features
    enable_docs: bool = True
    enable_websocket: bool = True
    enable_metrics: bool = True

    @classmethod
    def from_env(cls) -> "APIConfig":
        """Create from environment variables."""
        cors_origins_str = os.getenv("CORS_ORIGINS", "*")
        cors_origins = cors_origins_str.split(",")

        return cls(
            host=os.getenv("API_HOST", "0.0.0.0"),
            port=int(os.getenv("API_PORT", "8000")),
            workers=int(os.getenv("API_WORKERS", "1")),
            debug=os.getenv("DEBUG", "false").lower() == "true",
            cors_origins=cors_origins,
            enable_docs=os.getenv("ENABLE_DOCS", "true").lower() == "true",
            enable_websocket=os.getenv("ENABLE_WEBSOCKET", "true").lower() == "true",
            enable_metrics=os.getenv("ENABLE_METRICS", "true").lower() == "true",
        )


# =============================================================================
# Observability Configuration
# =============================================================================


@dataclass
class ObservabilityConfig:
    """Observability configuration."""

    # Logging
    log_level: str = "INFO"
    log_format: str = "json"  # json, text
    log_file: str | None = None

    # Metrics
    metrics_enabled: bool = True
    metrics_port: int = 9090

    # Tracing
    tracing_enabled: bool = True
    trace_sample_rate: float = 0.1

    # Health checks
    health_check_interval: float = 30.0

    @classmethod
    def from_env(cls) -> "ObservabilityConfig":
        """Create from environment variables."""
        return cls(
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            log_format=os.getenv("LOG_FORMAT", "json"),
            log_file=os.getenv("LOG_FILE"),
            metrics_enabled=os.getenv("METRICS_ENABLED", "true").lower() == "true",
            tracing_enabled=os.getenv("TRACING_ENABLED", "true").lower() == "true",
            trace_sample_rate=float(os.getenv("TRACE_SAMPLE_RATE", "0.1")),
        )


# =============================================================================
# Main Application Configuration
# =============================================================================


@dataclass
class MedeXConfig:
    """Main application configuration."""

    # Application info
    name: str = "MedeX"
    version: str = "2.0.0"
    description: str = "Asistente Médico Educativo con IA"
    environment: Environment = Environment.DEVELOPMENT

    # Component configs
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    redis: RedisConfig = field(default_factory=RedisConfig)
    qdrant: QdrantConfig = field(default_factory=QdrantConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    embedding: EmbeddingConfig = field(default_factory=EmbeddingConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    api: APIConfig = field(default_factory=APIConfig)
    observability: ObservabilityConfig = field(default_factory=ObservabilityConfig)

    @classmethod
    def from_env(cls) -> "MedeXConfig":
        """Create configuration from environment variables."""
        env_str = os.getenv("MEDEX_ENV", "development")
        environment = Environment(env_str)

        return cls(
            name=os.getenv("MEDEX_NAME", "MedeX"),
            version=os.getenv("MEDEX_VERSION", "2.0.0"),
            environment=environment,
            database=DatabaseConfig.from_env(),
            redis=RedisConfig.from_env(),
            qdrant=QdrantConfig.from_env(),
            llm=LLMConfig.from_env(),
            embedding=EmbeddingConfig.from_env(),
            security=SecurityConfig.from_env(),
            api=APIConfig.from_env(),
            observability=ObservabilityConfig.from_env(),
        )

    @classmethod
    def load_dotenv(cls, path: str | Path | None = None) -> "MedeXConfig":
        """Load configuration from .env file."""
        env_path = Path(path) if path else Path(".env")

        if env_path.exists():
            with open(env_path) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        os.environ.setdefault(key.strip(), value.strip())

        return cls.from_env()

    def validate(self) -> list[str]:
        """Validate configuration."""
        errors = []

        # Check required API keys for production
        if self.environment == Environment.PRODUCTION:
            if not self.llm.providers:
                errors.append("At least one LLM provider must be configured")

            if not self.database.password or self.database.password == "medex_secret":
                errors.append("Database password must be changed from default")

        # Check port ranges
        if not (1 <= self.api.port <= 65535):
            errors.append(f"Invalid API port: {self.api.port}")

        return errors

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary (sanitized for logging)."""
        return {
            "name": self.name,
            "version": self.version,
            "environment": self.environment.value,
            "api": {
                "host": self.api.host,
                "port": self.api.port,
                "debug": self.api.debug,
            },
            "database": {
                "host": self.database.host,
                "port": self.database.port,
                "database": self.database.database,
            },
            "redis": {
                "host": self.redis.host,
                "port": self.redis.port,
            },
            "qdrant": {
                "host": self.qdrant.host,
                "port": self.qdrant.port,
            },
            "llm": {
                "providers": [p.name for p in self.llm.providers],
                "default": self.llm.default_provider,
            },
        }


# =============================================================================
# Factory Functions
# =============================================================================


def load_config(env_file: str | Path | None = None) -> MedeXConfig:
    """Load configuration from environment."""
    if env_file:
        return MedeXConfig.load_dotenv(env_file)
    return MedeXConfig.from_env()


def create_development_config() -> MedeXConfig:
    """Create development configuration."""
    return MedeXConfig(
        environment=Environment.DEVELOPMENT,
        api=APIConfig(debug=True, enable_docs=True),
        security=SecurityConfig(api_key_required=False, rate_limit_enabled=False),
        observability=ObservabilityConfig(log_level="DEBUG", log_format="text"),
    )


def create_production_config() -> MedeXConfig:
    """Create production configuration."""
    config = MedeXConfig.from_env()
    config.environment = Environment.PRODUCTION
    config.api.debug = False
    return config
