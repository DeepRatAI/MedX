# =============================================================================
# MedeX - Redis Cache Integration
# =============================================================================
"""
Redis cache layer for MedeX V2.

This module provides:
- Context window caching for LLM conversations
- Rate limiting per user/session
- Tool result caching
- Session storage for UI state

Configuration via environment variables:
- MEDEX_REDIS_HOST: Redis host (default: localhost)
- MEDEX_REDIS_PORT: Redis port (default: 6379)
- MEDEX_REDIS_DB: Redis database number (default: 0)
- MEDEX_REDIS_PASSWORD: Redis password (optional)
- MEDEX_REDIS_PREFIX: Key prefix (default: medex:)
"""

from __future__ import annotations

import os
import json
import logging
from typing import Optional, Any, TypeVar
from datetime import timedelta

import redis.asyncio as redis
from redis.asyncio.connection import ConnectionPool


# =============================================================================
# Logging Configuration
# =============================================================================

logger = logging.getLogger(__name__)


# =============================================================================
# Configuration
# =============================================================================


def get_redis_url() -> str:
    """
    Build Redis connection URL from environment.

    Returns:
        Redis connection URL string
    """
    host = os.getenv("MEDEX_REDIS_HOST", "localhost")
    port = os.getenv("MEDEX_REDIS_PORT", "6379")
    db = os.getenv("MEDEX_REDIS_DB", "0")
    password = os.getenv("MEDEX_REDIS_PASSWORD", "")

    if password:
        return f"redis://:{password}@{host}:{port}/{db}"
    return f"redis://{host}:{port}/{db}"


def get_key_prefix() -> str:
    """Get Redis key prefix for namespacing."""
    return os.getenv("MEDEX_REDIS_PREFIX", "medex:")


# =============================================================================
# Connection Management
# =============================================================================

_redis_pool: Optional[ConnectionPool] = None
_redis_client: Optional[redis.Redis] = None


async def get_redis_client() -> redis.Redis:
    """
    Get or create Redis client with connection pooling.

    Returns:
        Redis async client instance
    """
    global _redis_pool, _redis_client

    if _redis_client is not None:
        return _redis_client

    redis_url = get_redis_url()
    safe_url = redis_url.replace(os.getenv("MEDEX_REDIS_PASSWORD", ""), "***")
    logger.info(f"Creating Redis connection pool: {safe_url}")

    _redis_pool = ConnectionPool.from_url(
        redis_url,
        max_connections=int(os.getenv("MEDEX_REDIS_MAX_CONNECTIONS", "50")),
        decode_responses=True,
    )

    _redis_client = redis.Redis(connection_pool=_redis_pool)

    # Verify connection
    try:
        await _redis_client.ping()
        logger.info("Redis connection verified successfully")
    except Exception as e:
        logger.error(f"Redis connection failed: {e}")
        raise

    return _redis_client


async def close_redis() -> None:
    """Close Redis connections gracefully."""
    global _redis_pool, _redis_client

    if _redis_client is not None:
        logger.info("Closing Redis connections...")
        await _redis_client.close()
        _redis_client = None

    if _redis_pool is not None:
        await _redis_pool.disconnect()
        _redis_pool = None
        logger.info("Redis connections closed")


async def check_redis_health() -> dict:
    """
    Check Redis health status.

    Returns:
        Health status dictionary
    """
    result = {
        "status": "unknown",
        "host": os.getenv("MEDEX_REDIS_HOST", "localhost"),
        "latency_ms": None,
    }

    try:
        import time

        client = await get_redis_client()

        start = time.perf_counter()
        await client.ping()
        latency = (time.perf_counter() - start) * 1000

        info = await client.info("server")

        result.update(
            {
                "status": "healthy",
                "latency_ms": round(latency, 2),
                "redis_version": info.get("redis_version"),
                "connected_clients": (await client.info("clients")).get(
                    "connected_clients"
                ),
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
# Cache Operations
# =============================================================================

T = TypeVar("T")


class CacheService:
    """
    High-level cache service for MedeX operations.

    Features:
    - Type-safe get/set operations
    - Automatic JSON serialization
    - TTL management
    - Key namespacing
    """

    def __init__(self, client: redis.Redis, prefix: str = ""):
        """
        Initialize cache service.

        Args:
            client: Redis client instance
            prefix: Additional key prefix
        """
        self.client = client
        self.base_prefix = get_key_prefix()
        self.prefix = f"{self.base_prefix}{prefix}"

    def _key(self, key: str) -> str:
        """Build full key with prefix."""
        return f"{self.prefix}{key}"

    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None
        """
        full_key = self._key(key)
        value = await self.client.get(full_key)

        if value is not None:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value

        return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[timedelta] = None,
    ) -> bool:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache (JSON-serializable)
            ttl: Time-to-live (None for no expiration)

        Returns:
            True if set successfully
        """
        full_key = self._key(key)

        try:
            serialized = json.dumps(value) if not isinstance(value, str) else value

            if ttl:
                await self.client.setex(full_key, ttl, serialized)
            else:
                await self.client.set(full_key, serialized)

            return True

        except Exception as e:
            logger.error(f"Cache set failed for {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """
        Delete value from cache.

        Args:
            key: Cache key

        Returns:
            True if key existed and was deleted
        """
        full_key = self._key(key)
        result = await self.client.delete(full_key)
        return result > 0

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        full_key = self._key(key)
        return await self.client.exists(full_key) > 0

    async def get_ttl(self, key: str) -> int:
        """Get remaining TTL in seconds (-1 if no expiry, -2 if not exists)."""
        full_key = self._key(key)
        return await self.client.ttl(full_key)

    async def increment(self, key: str, amount: int = 1) -> int:
        """Increment numeric value atomically."""
        full_key = self._key(key)
        return await self.client.incrby(full_key, amount)

    async def expire(self, key: str, ttl: timedelta) -> bool:
        """Set expiration on existing key."""
        full_key = self._key(key)
        return await self.client.expire(full_key, ttl)


# =============================================================================
# Specialized Cache Services
# =============================================================================


class ContextWindowCache(CacheService):
    """
    Cache for LLM context window management.

    Stores recent messages for quick retrieval during conversation.
    """

    def __init__(self, client: redis.Redis):
        super().__init__(client, prefix="context:")

    async def get_context(
        self,
        conversation_id: str,
    ) -> Optional[list[dict]]:
        """
        Get cached context window for conversation.

        Args:
            conversation_id: Conversation UUID string

        Returns:
            List of message dictionaries or None
        """
        return await self.get(conversation_id)

    async def set_context(
        self,
        conversation_id: str,
        messages: list[dict],
        ttl: timedelta = timedelta(hours=24),
    ) -> bool:
        """
        Cache context window for conversation.

        Args:
            conversation_id: Conversation UUID string
            messages: List of message dictionaries
            ttl: Cache duration (default 24h)

        Returns:
            True if cached successfully
        """
        return await self.set(conversation_id, messages, ttl)

    async def append_message(
        self,
        conversation_id: str,
        message: dict,
        max_messages: int = 50,
    ) -> bool:
        """
        Append message to cached context, maintaining window size.

        Args:
            conversation_id: Conversation UUID string
            message: Message dictionary to append
            max_messages: Maximum messages to keep

        Returns:
            True if appended successfully
        """
        context = await self.get_context(conversation_id) or []
        context.append(message)

        # Trim to window size (keep latest)
        if len(context) > max_messages:
            context = context[-max_messages:]

        return await self.set_context(conversation_id, context)

    async def invalidate(self, conversation_id: str) -> bool:
        """Invalidate cached context for conversation."""
        return await self.delete(conversation_id)


class RateLimitCache(CacheService):
    """
    Cache for API rate limiting.

    Implements sliding window rate limiting with Redis.
    """

    def __init__(self, client: redis.Redis):
        super().__init__(client, prefix="ratelimit:")

    async def check_and_increment(
        self,
        identifier: str,
        limit: int = 60,
        window: timedelta = timedelta(minutes=1),
    ) -> tuple[bool, int, int]:
        """
        Check rate limit and increment counter.

        Args:
            identifier: User/session identifier
            limit: Maximum requests per window
            window: Time window for limit

        Returns:
            Tuple of (allowed, current_count, remaining)
        """
        key = identifier
        full_key = self._key(key)

        # Get current count
        current = await self.client.get(full_key)
        count = int(current) if current else 0

        if count >= limit:
            return False, count, 0

        # Increment with expiry
        pipe = self.client.pipeline()
        pipe.incr(full_key)
        if count == 0:
            pipe.expire(full_key, window)
        await pipe.execute()

        new_count = count + 1
        remaining = limit - new_count

        return True, new_count, remaining

    async def get_remaining(
        self,
        identifier: str,
        limit: int = 60,
    ) -> int:
        """Get remaining requests in current window."""
        key = identifier
        current = await self.get(key)
        count = int(current) if current else 0
        return max(0, limit - count)


class ToolResultCache(CacheService):
    """
    Cache for tool execution results.

    Caches expensive tool results (API calls, calculations) for reuse.
    """

    def __init__(self, client: redis.Redis):
        super().__init__(client, prefix="tool:")

    def _make_key(self, tool_name: str, params: dict) -> str:
        """Create deterministic key from tool name and params."""
        import hashlib

        params_str = json.dumps(params, sort_keys=True)
        hash_str = hashlib.sha256(params_str.encode()).hexdigest()[:16]
        return f"{tool_name}:{hash_str}"

    async def get_result(
        self,
        tool_name: str,
        params: dict,
    ) -> Optional[dict]:
        """
        Get cached tool result.

        Args:
            tool_name: Tool identifier
            params: Tool input parameters

        Returns:
            Cached result or None
        """
        key = self._make_key(tool_name, params)
        return await self.get(key)

    async def cache_result(
        self,
        tool_name: str,
        params: dict,
        result: dict,
        ttl: timedelta = timedelta(hours=1),
    ) -> bool:
        """
        Cache tool result.

        Args:
            tool_name: Tool identifier
            params: Tool input parameters
            result: Tool output to cache
            ttl: Cache duration (default 1h)

        Returns:
            True if cached successfully
        """
        key = self._make_key(tool_name, params)
        return await self.set(key, result, ttl)


class SessionCache(CacheService):
    """
    Cache for UI session state.

    Stores temporary session data (selected conversation, UI preferences).
    """

    def __init__(self, client: redis.Redis):
        super().__init__(client, prefix="session:")

    async def get_session(
        self,
        session_id: str,
    ) -> Optional[dict]:
        """Get session data."""
        return await self.get(session_id)

    async def set_session(
        self,
        session_id: str,
        data: dict,
        ttl: timedelta = timedelta(hours=24),
    ) -> bool:
        """Set session data."""
        return await self.set(session_id, data, ttl)

    async def update_session(
        self,
        session_id: str,
        updates: dict,
    ) -> bool:
        """
        Update specific session fields.

        Args:
            session_id: Session identifier
            updates: Dictionary of fields to update

        Returns:
            True if updated successfully
        """
        session = await self.get_session(session_id) or {}
        session.update(updates)
        return await self.set_session(session_id, session)


# =============================================================================
# Factory Functions
# =============================================================================


async def get_context_cache() -> ContextWindowCache:
    """Get context window cache service."""
    client = await get_redis_client()
    return ContextWindowCache(client)


async def get_rate_limit_cache() -> RateLimitCache:
    """Get rate limiting cache service."""
    client = await get_redis_client()
    return RateLimitCache(client)


async def get_tool_cache() -> ToolResultCache:
    """Get tool result cache service."""
    client = await get_redis_client()
    return ToolResultCache(client)


async def get_session_cache() -> SessionCache:
    """Get session cache service."""
    client = await get_redis_client()
    return SessionCache(client)
