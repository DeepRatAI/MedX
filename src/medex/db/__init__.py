# =============================================================================
# MedeX - Database Layer
# =============================================================================
"""
Database module for MedeX V2.

This module provides:
- SQLAlchemy async ORM models
- Repository pattern for data access
- Connection management with asyncpg
- Alembic migration support

Architecture:
    - PostgreSQL 16: Primary persistence (conversations, users, context)
    - Redis 7: Cache layer (context window, rate limiting, sessions)
    - Qdrant: Vector database (RAG embeddings, knowledge base search)
"""

from src.medex.db.models import (
    Base,
    User,
    Conversation,
    Message,
    PatientContext,
    ToolExecution,
    KnowledgeBaseIndex,
)
from src.medex.db.connection import (
    get_async_engine,
    get_async_session,
    AsyncSessionLocal,
    init_db,
    close_db,
)
from src.medex.db.repositories import (
    UserRepository,
    ConversationRepository,
    MessageRepository,
    PatientContextRepository,
    ToolExecutionRepository,
)

__all__ = [
    # Models
    "Base",
    "User",
    "Conversation",
    "Message",
    "PatientContext",
    "ToolExecution",
    "KnowledgeBaseIndex",
    # Connection
    "get_async_engine",
    "get_async_session",
    "AsyncSessionLocal",
    "init_db",
    "close_db",
    # Repositories
    "UserRepository",
    "ConversationRepository",
    "MessageRepository",
    "PatientContextRepository",
    "ToolExecutionRepository",
]
