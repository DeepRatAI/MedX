# =============================================================================
# MedeX - Infrastructure Connection Tests
# =============================================================================
"""
Tests for database, cache, and vector store connectivity.

These tests verify:
- PostgreSQL connection and basic operations
- Redis connection and cache operations
- Qdrant connection and vector operations
- Connection pooling behavior
- Health check endpoints

Prerequisites:
    docker compose up postgres redis qdrant
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import timedelta

import pytest

# Mark all tests in this module as async
pytestmark = pytest.mark.asyncio


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture(scope="module")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def db_session():
    """Provide database session for tests."""
    from src.medex.db.connection import (
        close_db,
        get_session_context,
        init_db,
    )

    # Initialize with test tables
    await init_db(create_tables=True)

    async with get_session_context() as session:
        yield session

    await close_db()


@pytest.fixture
async def redis_client():
    """Provide Redis client for tests."""
    from src.medex.db.cache import close_redis, get_redis_client

    client = await get_redis_client()
    yield client
    await close_redis()


# =============================================================================
# PostgreSQL Connection Tests
# =============================================================================


class TestPostgreSQLConnection:
    """Test PostgreSQL connectivity and basic operations."""

    async def test_database_connection(self, db_session):
        """Test basic database connectivity."""
        from sqlalchemy import text

        result = await db_session.execute(text("SELECT 1 as test"))
        row = result.fetchone()

        assert row is not None
        assert row.test == 1

    async def test_database_version(self, db_session):
        """Test PostgreSQL version is 16+."""
        from sqlalchemy import text

        result = await db_session.execute(text("SHOW server_version"))
        version = result.scalar()

        # Should be PostgreSQL 16.x
        major_version = int(version.split(".")[0])
        assert major_version >= 16, f"Expected PostgreSQL 16+, got {version}"

    async def test_uuid_extension(self, db_session):
        """Test UUID extension is available."""
        from sqlalchemy import text

        result = await db_session.execute(text("SELECT gen_random_uuid() as uuid"))
        generated_uuid = result.scalar()

        # Should be valid UUID
        parsed = uuid.UUID(str(generated_uuid))
        assert parsed is not None

    async def test_jsonb_operations(self, db_session):
        """Test JSONB data type operations."""
        from sqlalchemy import text

        # Test JSONB insertion and query
        result = await db_session.execute(text("""
                SELECT '{"name": "test", "value": 42}'::jsonb ->> 'name' as name,
                       ('{"name": "test", "value": 42}'::jsonb -> 'value')::int as value
            """))
        row = result.fetchone()

        assert row.name == "test"
        assert row.value == 42

    async def test_health_check(self):
        """Test database health check function."""
        from src.medex.db.connection import check_db_health, close_db, init_db

        await init_db()
        health = await check_db_health()
        await close_db()

        assert health["status"] == "healthy"
        assert health["latency_ms"] < 1000  # Should respond within 1s
        assert health["database"] == "medex"


# =============================================================================
# User Repository Tests
# =============================================================================


class TestUserRepository:
    """Test User entity operations."""

    async def test_create_user(self, db_session):
        """Test user creation."""
        from src.medex.db.models import User
        from src.medex.db.repositories import UserRepository

        repo = UserRepository(db_session)
        session_id = f"test_session_{uuid.uuid4().hex[:8]}"

        user = User(session_id=session_id)
        created = await repo.create(user)

        assert created.id is not None
        assert created.session_id == session_id
        assert created.detected_type.value == "unknown"
        assert created.created_at is not None

    async def test_get_or_create_by_session(self, db_session):
        """Test get-or-create pattern for users."""
        from src.medex.db.repositories import UserRepository

        repo = UserRepository(db_session)
        session_id = f"test_session_{uuid.uuid4().hex[:8]}"

        # First call should create
        user1, created1 = await repo.get_or_create_by_session(session_id)
        assert created1 is True
        assert user1.session_id == session_id

        # Second call should retrieve
        user2, created2 = await repo.get_or_create_by_session(session_id)
        assert created2 is False
        assert user2.id == user1.id

    async def test_update_detected_type(self, db_session):
        """Test updating user's detected type."""
        from src.medex.db.models import User, UserType
        from src.medex.db.repositories import UserRepository

        repo = UserRepository(db_session)
        session_id = f"test_session_{uuid.uuid4().hex[:8]}"

        user = User(session_id=session_id)
        created = await repo.create(user)

        # Update type
        await repo.update_detected_type(created.id, UserType.PROFESSIONAL)
        await db_session.flush()

        # Verify update
        updated = await repo.get_by_id(created.id)
        assert updated.detected_type == UserType.PROFESSIONAL


# =============================================================================
# Conversation Repository Tests
# =============================================================================


class TestConversationRepository:
    """Test Conversation entity operations."""

    async def test_create_conversation(self, db_session):
        """Test conversation creation."""
        from src.medex.db.models import User
        from src.medex.db.repositories import ConversationRepository, UserRepository

        # Create user first
        user_repo = UserRepository(db_session)
        user = User(session_id=f"test_{uuid.uuid4().hex[:8]}")
        await user_repo.create(user)

        # Create conversation
        conv_repo = ConversationRepository(db_session)
        conv = await conv_repo.create_for_user(user.id, title="Test Conversation")

        assert conv.id is not None
        assert conv.user_id == user.id
        assert conv.title == "Test Conversation"
        assert conv.message_count == 0
        assert conv.is_deleted is False

    async def test_get_user_conversations(self, db_session):
        """Test fetching user's conversations."""
        from src.medex.db.models import User
        from src.medex.db.repositories import ConversationRepository, UserRepository

        # Create user and multiple conversations
        user_repo = UserRepository(db_session)
        user = User(session_id=f"test_{uuid.uuid4().hex[:8]}")
        await user_repo.create(user)

        conv_repo = ConversationRepository(db_session)
        for i in range(3):
            await conv_repo.create_for_user(user.id, title=f"Conversation {i}")

        # Fetch conversations
        conversations = await conv_repo.get_by_user(user.id)

        assert len(conversations) == 3
        # Should be ordered by updated_at desc
        assert conversations[0].title == "Conversation 2"


# =============================================================================
# Message Repository Tests
# =============================================================================


class TestMessageRepository:
    """Test Message entity operations."""

    async def test_create_messages(self, db_session):
        """Test message creation with auto-sequencing."""
        from src.medex.db.models import MessageRole, User
        from src.medex.db.repositories import (
            ConversationRepository,
            MessageRepository,
            UserRepository,
        )

        # Setup
        user_repo = UserRepository(db_session)
        user = User(session_id=f"test_{uuid.uuid4().hex[:8]}")
        await user_repo.create(user)

        conv_repo = ConversationRepository(db_session)
        conv = await conv_repo.create_for_user(user.id)

        # Create messages
        msg_repo = MessageRepository(db_session)

        msg1 = await msg_repo.create_message(
            conversation_id=conv.id,
            role=MessageRole.USER,
            content="Hello, I have a question about diabetes",
            token_count=10,
        )

        msg2 = await msg_repo.create_message(
            conversation_id=conv.id,
            role=MessageRole.ASSISTANT,
            content="I'd be happy to help with your diabetes question.",
            token_count=15,
            model_used="kimi-k2",
            latency_ms=450,
        )

        assert msg1.sequence_number == 1
        assert msg2.sequence_number == 2
        assert msg1.role == MessageRole.USER
        assert msg2.role == MessageRole.ASSISTANT
        assert msg2.model_used == "kimi-k2"

    async def test_get_total_tokens(self, db_session):
        """Test token counting across messages."""
        from src.medex.db.models import MessageRole, User
        from src.medex.db.repositories import (
            ConversationRepository,
            MessageRepository,
            UserRepository,
        )

        # Setup
        user_repo = UserRepository(db_session)
        user = User(session_id=f"test_{uuid.uuid4().hex[:8]}")
        await user_repo.create(user)

        conv_repo = ConversationRepository(db_session)
        conv = await conv_repo.create_for_user(user.id)

        # Create messages with known token counts
        msg_repo = MessageRepository(db_session)
        await msg_repo.create_message(conv.id, MessageRole.USER, "Msg1", 100)
        await msg_repo.create_message(conv.id, MessageRole.ASSISTANT, "Msg2", 200)
        await msg_repo.create_message(conv.id, MessageRole.USER, "Msg3", 50)

        # Verify total
        total = await msg_repo.get_total_tokens(conv.id)
        assert total == 350


# =============================================================================
# Redis Connection Tests
# =============================================================================


class TestRedisConnection:
    """Test Redis connectivity and cache operations."""

    async def test_redis_ping(self, redis_client):
        """Test basic Redis connectivity."""
        result = await redis_client.ping()
        assert result is True

    async def test_cache_set_get(self, redis_client):
        """Test basic cache set/get operations."""
        from src.medex.db.cache import CacheService

        cache = CacheService(redis_client, prefix="test:")

        # Set value
        key = f"test_key_{uuid.uuid4().hex[:8]}"
        value = {"message": "Hello", "count": 42}

        result = await cache.set(key, value, ttl=timedelta(seconds=60))
        assert result is True

        # Get value
        retrieved = await cache.get(key)
        assert retrieved == value

        # Cleanup
        await cache.delete(key)

    async def test_context_window_cache(self, redis_client):
        """Test context window caching."""
        from src.medex.db.cache import ContextWindowCache

        cache = ContextWindowCache(redis_client)
        conv_id = str(uuid.uuid4())

        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
        ]

        # Cache context
        result = await cache.set_context(conv_id, messages)
        assert result is True

        # Retrieve context
        retrieved = await cache.get_context(conv_id)
        assert retrieved == messages

        # Append message
        await cache.append_message(conv_id, {"role": "user", "content": "Question"})
        updated = await cache.get_context(conv_id)
        assert len(updated) == 3

        # Cleanup
        await cache.invalidate(conv_id)

    async def test_rate_limit_cache(self, redis_client):
        """Test rate limiting cache."""
        from src.medex.db.cache import RateLimitCache

        cache = RateLimitCache(redis_client)
        identifier = f"test_user_{uuid.uuid4().hex[:8]}"

        # First request should be allowed
        allowed, count, remaining = await cache.check_and_increment(
            identifier, limit=5, window=timedelta(seconds=60)
        )
        assert allowed is True
        assert count == 1
        assert remaining == 4

        # Make more requests
        for _ in range(4):
            await cache.check_and_increment(identifier, limit=5)

        # Sixth request should be denied
        allowed, count, remaining = await cache.check_and_increment(identifier, limit=5)
        assert allowed is False
        assert count == 5
        assert remaining == 0

    async def test_health_check(self):
        """Test Redis health check."""
        from src.medex.db.cache import check_redis_health, close_redis, get_redis_client

        await get_redis_client()
        health = await check_redis_health()
        await close_redis()

        assert health["status"] == "healthy"
        assert health["latency_ms"] < 100  # Should be very fast
        assert health["redis_version"] is not None


# =============================================================================
# Tool Result Cache Tests
# =============================================================================


class TestToolResultCache:
    """Test tool result caching."""

    async def test_cache_tool_result(self, redis_client):
        """Test caching and retrieving tool results."""
        from src.medex.db.cache import ToolResultCache

        cache = ToolResultCache(redis_client)

        tool_name = "icd10_search"
        params = {"query": "diabetes", "limit": 10}
        result = {
            "codes": [
                {"code": "E11", "description": "Type 2 diabetes mellitus"},
                {"code": "E10", "description": "Type 1 diabetes mellitus"},
            ],
            "total": 2,
        }

        # Cache result
        cached = await cache.cache_result(tool_name, params, result)
        assert cached is True

        # Retrieve result
        retrieved = await cache.get_result(tool_name, params)
        assert retrieved == result

        # Different params should return None
        different = await cache.get_result(tool_name, {"query": "hypertension"})
        assert different is None

    async def test_cache_key_determinism(self, redis_client):
        """Test that cache keys are deterministic regardless of param order."""
        from src.medex.db.cache import ToolResultCache

        cache = ToolResultCache(redis_client)

        # Same params, different order
        params1 = {"a": 1, "b": 2, "c": 3}
        params2 = {"c": 3, "a": 1, "b": 2}

        key1 = cache._make_key("test_tool", params1)
        key2 = cache._make_key("test_tool", params2)

        assert key1 == key2


# =============================================================================
# Integration Tests
# =============================================================================


class TestInfrastructureIntegration:
    """Integration tests for full infrastructure stack."""

    async def test_full_conversation_flow(self, db_session, redis_client):
        """Test complete conversation creation and caching flow."""
        from src.medex.db.cache import ContextWindowCache
        from src.medex.db.models import MessageRole, User
        from src.medex.db.repositories import (
            ConversationRepository,
            MessageRepository,
            UserRepository,
        )

        # Create user
        user_repo = UserRepository(db_session)
        user = User(session_id=f"integration_{uuid.uuid4().hex[:8]}")
        await user_repo.create(user)

        # Create conversation
        conv_repo = ConversationRepository(db_session)
        conv = await conv_repo.create_for_user(user.id, "Integration Test")

        # Create messages and cache context
        msg_repo = MessageRepository(db_session)
        cache = ContextWindowCache(redis_client)

        messages_for_cache = []

        for _i, (role, content) in enumerate(
            [
                (MessageRole.USER, "What is hypertension?"),
                (MessageRole.ASSISTANT, "Hypertension is high blood pressure..."),
                (MessageRole.USER, "What are the symptoms?"),
            ]
        ):
            msg = await msg_repo.create_message(  # noqa: F841
                conversation_id=conv.id,
                role=role,
                content=content,
                token_count=len(content.split()) * 2,
            )
            messages_for_cache.append(
                {
                    "role": role.value,
                    "content": content,
                }
            )

        # Cache the context
        await cache.set_context(str(conv.id), messages_for_cache)

        # Verify persistence
        db_messages = await msg_repo.get_by_conversation(conv.id)
        assert len(db_messages) == 3

        # Verify cache
        cached = await cache.get_context(str(conv.id))
        assert len(cached) == 3
        assert cached[0]["content"] == "What is hypertension?"

        # Cleanup
        await cache.invalidate(str(conv.id))


# =============================================================================
# Run Tests
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])
