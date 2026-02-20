# =============================================================================
# MedeX - Database Connection Management
# =============================================================================
"""
Async database connection management for MedeX V2.

This module provides:
- Async SQLAlchemy engine with asyncpg
- Session factory with proper lifecycle
- Connection pooling configuration
- Health check utilities
- Graceful shutdown support

Configuration via environment variables:
- MEDEX_POSTGRES_HOST: PostgreSQL host (default: localhost)
- MEDEX_POSTGRES_PORT: PostgreSQL port (default: 5432)
- MEDEX_POSTGRES_DB: Database name (default: medex)
- MEDEX_POSTGRES_USER: Database user (default: medex)
- MEDEX_POSTGRES_PASSWORD: Database password
- MEDEX_POSTGRES_POOL_SIZE: Connection pool size (default: 10)
- MEDEX_POSTGRES_MAX_OVERFLOW: Max overflow connections (default: 20)
"""

from __future__ import annotations

import logging
import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from src.medex.db.models import Base

# =============================================================================
# Logging Configuration
# =============================================================================

logger = logging.getLogger(__name__)


# =============================================================================
# Environment Configuration
# =============================================================================


def get_database_url(async_driver: bool = True, include_password: bool = True) -> str:
    """
    Build PostgreSQL connection URL from environment variables.

    Args:
        async_driver: Use asyncpg driver (True) or psycopg2 (False)
        include_password: Include password in URL (False for logging)

    Returns:
        PostgreSQL connection URL string
    """
    host = os.getenv("MEDEX_POSTGRES_HOST", "localhost")
    port = os.getenv("MEDEX_POSTGRES_PORT", "5432")
    database = os.getenv("MEDEX_POSTGRES_DB", "medex")
    user = os.getenv("MEDEX_POSTGRES_USER", "medex")
    password = os.getenv("MEDEX_POSTGRES_PASSWORD", "medex_secure_password")

    driver = "postgresql+asyncpg" if async_driver else "postgresql+psycopg2"

    if include_password:
        return f"{driver}://{user}:{password}@{host}:{port}/{database}"
    else:
        return f"{driver}://{user}:***@{host}:{port}/{database}"


def get_pool_config() -> dict:
    """
    Get connection pool configuration from environment.

    Returns:
        Dictionary with pool configuration parameters
    """
    return {
        "pool_size": int(os.getenv("MEDEX_POSTGRES_POOL_SIZE", "10")),
        "max_overflow": int(os.getenv("MEDEX_POSTGRES_MAX_OVERFLOW", "20")),
        "pool_timeout": int(os.getenv("MEDEX_POSTGRES_POOL_TIMEOUT", "30")),
        "pool_recycle": int(os.getenv("MEDEX_POSTGRES_POOL_RECYCLE", "1800")),
        "pool_pre_ping": True,  # Verify connections before use
    }


# =============================================================================
# Engine Factory
# =============================================================================

_engine: AsyncEngine | None = None


def get_async_engine(
    force_new: bool = False,
    use_null_pool: bool = False,
) -> AsyncEngine:
    """
    Get or create async SQLAlchemy engine.

    Uses singleton pattern for connection reuse.

    Args:
        force_new: Force creation of new engine (for testing)
        use_null_pool: Use NullPool (for testing/migrations)

    Returns:
        AsyncEngine instance
    """
    global _engine

    if _engine is not None and not force_new:
        return _engine

    database_url = get_database_url(async_driver=True)
    safe_url = get_database_url(async_driver=True, include_password=False)

    logger.info(f"Creating async database engine: {safe_url}")

    # Engine configuration
    engine_kwargs = {
        "echo": os.getenv("MEDEX_DB_ECHO", "false").lower() == "true",
        "future": True,
    }

    # Pool configuration
    if use_null_pool:
        engine_kwargs["poolclass"] = NullPool
        logger.info("Using NullPool for database connections")
    else:
        pool_config = get_pool_config()
        engine_kwargs.update(pool_config)
        logger.info(
            f"Pool config: size={pool_config['pool_size']}, "
            f"max_overflow={pool_config['max_overflow']}"
        )

    _engine = create_async_engine(database_url, **engine_kwargs)

    # Register event listeners
    @event.listens_for(_engine.sync_engine, "connect")
    def set_search_path(dbapi_connection, connection_record):
        """Set default search path for connections."""
        cursor = dbapi_connection.cursor()
        cursor.execute("SET search_path TO public")
        cursor.close()

    return _engine


# =============================================================================
# Session Factory
# =============================================================================

AsyncSessionLocal: async_sessionmaker[AsyncSession] | None = None


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """
    Get or create async session factory.

    Returns:
        Async session maker configured for the engine
    """
    global AsyncSessionLocal

    if AsyncSessionLocal is None:
        engine = get_async_engine()
        AsyncSessionLocal = async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
        logger.info("Created async session factory")

    return AsyncSessionLocal


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for FastAPI to get database session.

    Usage:
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_async_session)):
            ...

    Yields:
        AsyncSession with automatic cleanup
    """
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_session_context() -> AsyncGenerator[AsyncSession, None]:
    """
    Context manager for getting database session outside FastAPI.

    Usage:
        async with get_session_context() as session:
            result = await session.execute(query)

    Yields:
        AsyncSession with automatic cleanup
    """
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# =============================================================================
# Database Lifecycle
# =============================================================================


async def init_db(create_tables: bool = False) -> None:
    """
    Initialize database connection and optionally create tables.

    Args:
        create_tables: Create all tables if True (use migrations in production)

    Note:
        In production, use Alembic migrations instead of create_tables=True
    """
    engine = get_async_engine()

    # Verify connection
    try:
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT 1"))
            assert result.scalar() == 1
        logger.info("Database connection verified successfully")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise

    # Create tables if requested (development only)
    if create_tables:
        logger.warning(
            "Creating database tables directly (use migrations in production)"
        )
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully")

    # Initialize session factory
    get_session_factory()

    logger.info("Database initialization complete")


async def close_db() -> None:
    """
    Close database connections gracefully.

    Should be called on application shutdown.
    """
    global _engine, AsyncSessionLocal

    if _engine is not None:
        logger.info("Closing database connections...")
        await _engine.dispose()
        _engine = None
        AsyncSessionLocal = None
        logger.info("Database connections closed")


# =============================================================================
# Health Check
# =============================================================================


async def check_db_health() -> dict:
    """
    Check database health status.

    Returns:
        Dictionary with health status and metrics
    """
    engine = get_async_engine()

    result = {
        "status": "unknown",
        "database": os.getenv("MEDEX_POSTGRES_DB", "medex"),
        "host": os.getenv("MEDEX_POSTGRES_HOST", "localhost"),
        "pool_size": None,
        "pool_checked_out": None,
        "latency_ms": None,
    }

    try:
        import time

        start = time.perf_counter()

        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))

        latency = (time.perf_counter() - start) * 1000

        # Get pool stats
        pool = engine.pool
        result.update(
            {
                "status": "healthy",
                "pool_size": pool.size() if hasattr(pool, "size") else None,
                "pool_checked_out": (
                    pool.checkedout() if hasattr(pool, "checkedout") else None
                ),
                "latency_ms": round(latency, 2),
            }
        )

    except Exception as e:
        result.update(
            {
                "status": "unhealthy",
                "error": str(e),
            }
        )

    return result


# =============================================================================
# Transaction Helpers
# =============================================================================


@asynccontextmanager
async def transaction_scope() -> AsyncGenerator[AsyncSession, None]:
    """
    Create a transactional scope with automatic rollback on error.

    Usage:
        async with transaction_scope() as session:
            session.add(entity)
            # Commits on success, rolls back on exception
    """
    session_factory = get_session_factory()
    async with session_factory() as session:
        async with session.begin():
            yield session


async def execute_raw_sql(sql: str, params: dict | None = None) -> list:
    """
    Execute raw SQL query for complex operations.

    Args:
        sql: Raw SQL query string
        params: Optional query parameters

    Returns:
        List of result rows

    Warning:
        Use sparingly. Prefer ORM operations for safety.
    """
    engine = get_async_engine()

    async with engine.begin() as conn:
        if params:
            result = await conn.execute(text(sql), params)
        else:
            result = await conn.execute(text(sql))

        return result.fetchall()
