# =============================================================================
# MedeX - Repository Pattern Implementation
# =============================================================================
"""
Repository pattern for database access in MedeX V2.

This module provides:
- Type-safe CRUD operations
- Query builders with filtering/pagination
- Soft delete support
- Optimistic locking
- Audit trail integration

Design Principles:
- Single Responsibility: Each repository handles one aggregate
- Dependency Injection: Sessions injected, not created
- Async-first: All operations are async
- Type Safety: Full typing with generics
"""

from __future__ import annotations

import logging
import uuid
from collections.abc import Sequence
from datetime import datetime, timezone
from typing import Any, Generic, TypeVar

from sqlalchemy import desc, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.medex.db.models import (
    Base,
    Conversation,
    EmergencyLevel,
    Message,
    MessageRole,
    PatientContext,
    ToolExecution,
    ToolStatus,
    User,
    UserType,
)

# =============================================================================
# Logging Configuration
# =============================================================================

logger = logging.getLogger(__name__)


# =============================================================================
# Generic Base Repository
# =============================================================================

T = TypeVar("T", bound=Base)


class BaseRepository(Generic[T]):
    """
    Generic base repository with common CRUD operations.

    Type Parameters:
        T: SQLAlchemy model class

    Usage:
        class UserRepository(BaseRepository[User]):
            model = User
    """

    model: type[T]

    def __init__(self, session: AsyncSession):
        """
        Initialize repository with database session.

        Args:
            session: AsyncSession from connection pool
        """
        self.session = session

    async def get_by_id(self, id: uuid.UUID) -> T | None:
        """
        Get entity by primary key.

        Args:
            id: UUID primary key

        Returns:
            Entity or None if not found
        """
        return await self.session.get(self.model, id)

    async def get_all(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[T]:
        """
        Get all entities with pagination.

        Args:
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of entities
        """
        stmt = select(self.model).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def create(self, entity: T) -> T:
        """
        Create new entity.

        Args:
            entity: Entity instance to persist

        Returns:
            Persisted entity with generated ID
        """
        self.session.add(entity)
        await self.session.flush()
        await self.session.refresh(entity)
        logger.debug(f"Created {self.model.__name__}: {entity.id}")
        return entity

    async def update(self, entity: T) -> T:
        """
        Update existing entity.

        Args:
            entity: Entity instance with modifications

        Returns:
            Updated entity
        """
        await self.session.flush()
        await self.session.refresh(entity)
        logger.debug(f"Updated {self.model.__name__}: {entity.id}")
        return entity

    async def delete(self, entity: T) -> None:
        """
        Hard delete entity.

        Args:
            entity: Entity instance to delete

        Warning:
            Use soft_delete for audit compliance
        """
        await self.session.delete(entity)
        await self.session.flush()
        logger.debug(f"Deleted {self.model.__name__}: {entity.id}")

    async def soft_delete(self, entity: T) -> T:
        """
        Soft delete entity by setting is_deleted flag.

        Args:
            entity: Entity instance to soft delete

        Returns:
            Updated entity with is_deleted=True
        """
        if hasattr(entity, "is_deleted"):
            entity.is_deleted = True
            await self.session.flush()
            logger.debug(f"Soft deleted {self.model.__name__}: {entity.id}")
        return entity

    async def count(self) -> int:
        """
        Count total entities.

        Returns:
            Total count of entities
        """
        stmt = select(func.count()).select_from(self.model)
        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def exists(self, id: uuid.UUID) -> bool:
        """
        Check if entity exists by ID.

        Args:
            id: UUID primary key

        Returns:
            True if entity exists
        """
        entity = await self.get_by_id(id)
        return entity is not None


# =============================================================================
# User Repository
# =============================================================================


class UserRepository(BaseRepository[User]):
    """
    Repository for User entity operations.

    Handles:
    - Session-based user lookup
    - User type detection updates
    - Rate limiting tracking
    """

    model = User

    async def get_by_session_id(self, session_id: str) -> User | None:
        """
        Get user by browser/client session ID.

        Args:
            session_id: Session identifier from client

        Returns:
            User or None if not found
        """
        stmt = (
            select(User)
            .where(User.session_id == session_id)
            .where(User.is_deleted == False)  # noqa: E712
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_or_create_by_session(
        self,
        session_id: str,
    ) -> tuple[User, bool]:
        """
        Get existing user or create new one for session.

        Args:
            session_id: Session identifier from client

        Returns:
            Tuple of (User, was_created)
        """
        existing = await self.get_by_session_id(session_id)
        if existing:
            return existing, False

        new_user = User(session_id=session_id)
        await self.create(new_user)
        logger.info(f"Created new user for session: {session_id[:8]}...")
        return new_user, True

    async def update_detected_type(
        self,
        user_id: uuid.UUID,
        user_type: UserType,
    ) -> None:
        """
        Update detected user type based on query analysis.

        Args:
            user_id: User UUID
            user_type: Detected type (professional/educational)
        """
        stmt = update(User).where(User.id == user_id).values(detected_type=user_type)
        await self.session.execute(stmt)
        logger.debug(f"Updated user {user_id} type to {user_type}")

    async def increment_request_count(self, user_id: uuid.UUID) -> int:
        """
        Increment daily request count for rate limiting.

        Args:
            user_id: User UUID

        Returns:
            Updated request count
        """
        user = await self.get_by_id(user_id)
        if user:
            user.request_count_today += 1
            user.last_request_at = datetime.now(timezone.utc)
            await self.session.flush()
            return user.request_count_today
        return 0

    async def reset_daily_counts(self) -> int:
        """
        Reset all users' daily request counts (for scheduled job).

        Returns:
            Number of users reset
        """
        stmt = (
            update(User)
            .where(User.request_count_today > 0)
            .values(request_count_today=0)
        )
        result = await self.session.execute(stmt)
        count = result.rowcount
        logger.info(f"Reset daily request counts for {count} users")
        return count


# =============================================================================
# Conversation Repository
# =============================================================================


class ConversationRepository(BaseRepository[Conversation]):
    """
    Repository for Conversation entity operations.

    Handles:
    - User's conversation history
    - Conversation search and filtering
    - Message count tracking
    """

    model = Conversation

    async def get_by_user(
        self,
        user_id: uuid.UUID,
        limit: int = 50,
        offset: int = 0,
        include_deleted: bool = False,
    ) -> Sequence[Conversation]:
        """
        Get user's conversations ordered by last activity.

        Args:
            user_id: User UUID
            limit: Maximum conversations to return
            offset: Pagination offset
            include_deleted: Include soft-deleted conversations

        Returns:
            List of conversations
        """
        stmt = (
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(desc(Conversation.updated_at))
            .limit(limit)
            .offset(offset)
        )

        if not include_deleted:
            stmt = stmt.where(Conversation.is_deleted == False)  # noqa: E712

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_with_messages(
        self,
        conversation_id: uuid.UUID,
        message_limit: int = 100,
    ) -> Conversation | None:
        """
        Get conversation with eager-loaded messages.

        Args:
            conversation_id: Conversation UUID
            message_limit: Maximum messages to load

        Returns:
            Conversation with messages or None
        """
        stmt = (
            select(Conversation)
            .where(Conversation.id == conversation_id)
            .where(Conversation.is_deleted == False)  # noqa: E712
            .options(
                selectinload(Conversation.messages),
                selectinload(Conversation.patient_contexts),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_for_user(
        self,
        user_id: uuid.UUID,
        title: str = "Nueva conversación",
    ) -> Conversation:
        """
        Create new conversation for user.

        Args:
            user_id: User UUID
            title: Initial conversation title

        Returns:
            New conversation instance
        """
        conversation = Conversation(
            user_id=user_id,
            title=title,
        )
        return await self.create(conversation)

    async def update_title(
        self,
        conversation_id: uuid.UUID,
        title: str,
    ) -> None:
        """
        Update conversation title.

        Args:
            conversation_id: Conversation UUID
            title: New title
        """
        stmt = (
            update(Conversation)
            .where(Conversation.id == conversation_id)
            .values(title=title[:255], updated_at=datetime.now(timezone.utc))
        )
        await self.session.execute(stmt)

    async def increment_message_count(
        self,
        conversation_id: uuid.UUID,
    ) -> int:
        """
        Increment message count and update timestamp.

        Args:
            conversation_id: Conversation UUID

        Returns:
            Updated message count
        """
        conversation = await self.get_by_id(conversation_id)
        if conversation:
            conversation.message_count += 1
            conversation.updated_at = datetime.now(timezone.utc)
            await self.session.flush()
            return conversation.message_count
        return 0

    async def set_emergency_detected(
        self,
        conversation_id: uuid.UUID,
        detected: bool = True,
    ) -> None:
        """
        Mark conversation as having emergency content.

        Args:
            conversation_id: Conversation UUID
            detected: Emergency detection flag
        """
        stmt = (
            update(Conversation)
            .where(Conversation.id == conversation_id)
            .values(emergency_detected=detected)
        )
        await self.session.execute(stmt)

    async def search_by_title(
        self,
        user_id: uuid.UUID,
        query: str,
        limit: int = 20,
    ) -> Sequence[Conversation]:
        """
        Search user's conversations by title.

        Args:
            user_id: User UUID
            query: Search query string
            limit: Maximum results

        Returns:
            Matching conversations
        """
        stmt = (
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .where(Conversation.is_deleted == False)  # noqa: E712
            .where(Conversation.title.ilike(f"%{query}%"))
            .order_by(desc(Conversation.updated_at))
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()


# =============================================================================
# Message Repository
# =============================================================================


class MessageRepository(BaseRepository[Message]):
    """
    Repository for Message entity operations.

    Handles:
    - Message creation with sequence tracking
    - Token counting for context window
    - Role-based message filtering
    """

    model = Message

    async def get_by_conversation(
        self,
        conversation_id: uuid.UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[Message]:
        """
        Get messages for conversation in order.

        Args:
            conversation_id: Conversation UUID
            limit: Maximum messages
            offset: Pagination offset

        Returns:
            Ordered list of messages
        """
        stmt = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.sequence_number)
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_latest(
        self,
        conversation_id: uuid.UUID,
        count: int = 10,
    ) -> Sequence[Message]:
        """
        Get latest N messages for context window.

        Args:
            conversation_id: Conversation UUID
            count: Number of latest messages

        Returns:
            Latest messages in chronological order
        """
        # Subquery to get latest messages
        subquery = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(desc(Message.sequence_number))
            .limit(count)
            .subquery()
        )

        # Re-order chronologically
        stmt = (
            select(Message)
            .join(subquery, Message.id == subquery.c.id)
            .order_by(Message.sequence_number)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def create_message(
        self,
        conversation_id: uuid.UUID,
        role: MessageRole,
        content: str,
        token_count: int = 0,
        model_used: str | None = None,
        latency_ms: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Message:
        """
        Create new message with auto-incrementing sequence.

        Args:
            conversation_id: Parent conversation UUID
            role: Message role (user/assistant/system/tool)
            content: Message content
            token_count: Estimated token count
            model_used: LLM model name (for assistant messages)
            latency_ms: Response time (for assistant messages)
            metadata: Additional metadata

        Returns:
            Created message
        """
        # Get next sequence number
        next_seq = await self._get_next_sequence(conversation_id)

        message = Message(
            conversation_id=conversation_id,
            sequence_number=next_seq,
            role=role,
            content=content,
            token_count=token_count,
            model_used=model_used,
            latency_ms=latency_ms,
            metadata=metadata or {},
        )

        return await self.create(message)

    async def _get_next_sequence(
        self,
        conversation_id: uuid.UUID,
    ) -> int:
        """
        Get next available sequence number for conversation.

        Args:
            conversation_id: Conversation UUID

        Returns:
            Next sequence number (1-indexed)
        """
        stmt = select(func.coalesce(func.max(Message.sequence_number), 0)).where(
            Message.conversation_id == conversation_id
        )
        result = await self.session.execute(stmt)
        current_max = result.scalar() or 0
        return current_max + 1

    async def get_total_tokens(
        self,
        conversation_id: uuid.UUID,
    ) -> int:
        """
        Get total token count for conversation.

        Args:
            conversation_id: Conversation UUID

        Returns:
            Total tokens across all messages
        """
        stmt = select(func.coalesce(func.sum(Message.token_count), 0)).where(
            Message.conversation_id == conversation_id
        )
        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def get_by_role(
        self,
        conversation_id: uuid.UUID,
        role: MessageRole,
    ) -> Sequence[Message]:
        """
        Get messages filtered by role.

        Args:
            conversation_id: Conversation UUID
            role: Message role to filter

        Returns:
            Messages with specified role
        """
        stmt = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .where(Message.role == role)
            .order_by(Message.sequence_number)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()


# =============================================================================
# Patient Context Repository
# =============================================================================


class PatientContextRepository(BaseRepository[PatientContext]):
    """
    Repository for PatientContext entity operations.

    Handles:
    - Clinical context extraction storage
    - Multi-patient conversation support
    - Emergency indicator tracking
    """

    model = PatientContext

    async def get_by_conversation(
        self,
        conversation_id: uuid.UUID,
    ) -> Sequence[PatientContext]:
        """
        Get all patient contexts for conversation.

        Args:
            conversation_id: Conversation UUID

        Returns:
            List of patient contexts
        """
        stmt = (
            select(PatientContext)
            .where(PatientContext.conversation_id == conversation_id)
            .order_by(PatientContext.patient_reference)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_latest_for_patient(
        self,
        conversation_id: uuid.UUID,
        patient_reference: str = "patient_1",
    ) -> PatientContext | None:
        """
        Get latest context version for specific patient.

        Args:
            conversation_id: Conversation UUID
            patient_reference: Patient identifier

        Returns:
            Latest patient context or None
        """
        stmt = (
            select(PatientContext)
            .where(PatientContext.conversation_id == conversation_id)
            .where(PatientContext.patient_reference == patient_reference)
            .order_by(desc(PatientContext.version))
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_or_update(
        self,
        conversation_id: uuid.UUID,
        patient_reference: str,
        context_data: dict[str, Any],
    ) -> PatientContext:
        """
        Create new context version or initial context.

        Args:
            conversation_id: Conversation UUID
            patient_reference: Patient identifier
            context_data: Clinical context dictionary

        Returns:
            New patient context version
        """
        # Get current version if exists
        current = await self.get_latest_for_patient(conversation_id, patient_reference)

        new_version = (current.version + 1) if current else 1

        context = PatientContext(
            conversation_id=conversation_id,
            patient_reference=patient_reference,
            version=new_version,
            **context_data,
        )

        return await self.create(context)

    async def get_emergencies(
        self,
        min_level: EmergencyLevel = EmergencyLevel.HIGH,
    ) -> Sequence[PatientContext]:
        """
        Get patient contexts with emergency indicators.

        Args:
            min_level: Minimum emergency level to include

        Returns:
            Patient contexts with emergencies
        """
        levels_to_include = []
        include_from_here = False
        for level in [
            EmergencyLevel.NONE,
            EmergencyLevel.LOW,
            EmergencyLevel.MODERATE,
            EmergencyLevel.HIGH,
            EmergencyLevel.CRITICAL,
        ]:
            if level == min_level:
                include_from_here = True
            if include_from_here:
                levels_to_include.append(level)

        stmt = (
            select(PatientContext)
            .where(PatientContext.emergency_level.in_(levels_to_include))
            .order_by(desc(PatientContext.updated_at))
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()


# =============================================================================
# Tool Execution Repository
# =============================================================================


class ToolExecutionRepository(BaseRepository[ToolExecution]):
    """
    Repository for ToolExecution entity operations.

    Handles:
    - Tool execution audit trail
    - Performance metrics tracking
    - Error analysis
    """

    model = ToolExecution

    async def create_execution(
        self,
        conversation_id: uuid.UUID,
        tool_name: str,
        tool_category: str,
        input_params: dict[str, Any],
        message_id: uuid.UUID | None = None,
    ) -> ToolExecution:
        """
        Create new tool execution record.

        Args:
            conversation_id: Parent conversation UUID
            tool_name: Tool identifier
            tool_category: Tool category
            input_params: Tool input parameters
            message_id: Associated message UUID

        Returns:
            Created execution record
        """
        execution = ToolExecution(
            conversation_id=conversation_id,
            message_id=message_id,
            tool_name=tool_name,
            tool_category=tool_category,
            input_params=input_params,
            status=ToolStatus.PENDING,
        )
        return await self.create(execution)

    async def mark_running(
        self,
        execution_id: uuid.UUID,
    ) -> None:
        """
        Mark execution as running.

        Args:
            execution_id: Execution UUID
        """
        stmt = (
            update(ToolExecution)
            .where(ToolExecution.id == execution_id)
            .values(status=ToolStatus.RUNNING)
        )
        await self.session.execute(stmt)

    async def mark_success(
        self,
        execution_id: uuid.UUID,
        output_result: dict[str, Any],
        latency_ms: int,
        cache_hit: bool = False,
    ) -> None:
        """
        Mark execution as successful.

        Args:
            execution_id: Execution UUID
            output_result: Tool output
            latency_ms: Execution time
            cache_hit: Whether result was cached
        """
        stmt = (
            update(ToolExecution)
            .where(ToolExecution.id == execution_id)
            .values(
                status=ToolStatus.SUCCESS,
                output_result=output_result,
                latency_ms=latency_ms,
                cache_hit=cache_hit,
                completed_at=datetime.now(timezone.utc),
            )
        )
        await self.session.execute(stmt)

    async def mark_failed(
        self,
        execution_id: uuid.UUID,
        error_message: str,
        error_traceback: str | None = None,
        latency_ms: int | None = None,
    ) -> None:
        """
        Mark execution as failed.

        Args:
            execution_id: Execution UUID
            error_message: Error description
            error_traceback: Full traceback
            latency_ms: Time until failure
        """
        stmt = (
            update(ToolExecution)
            .where(ToolExecution.id == execution_id)
            .values(
                status=ToolStatus.FAILED,
                error_message=error_message,
                error_traceback=error_traceback,
                latency_ms=latency_ms,
                completed_at=datetime.now(timezone.utc),
            )
        )
        await self.session.execute(stmt)

    async def get_by_conversation(
        self,
        conversation_id: uuid.UUID,
        limit: int = 100,
    ) -> Sequence[ToolExecution]:
        """
        Get tool executions for conversation.

        Args:
            conversation_id: Conversation UUID
            limit: Maximum results

        Returns:
            Tool executions ordered by time
        """
        stmt = (
            select(ToolExecution)
            .where(ToolExecution.conversation_id == conversation_id)
            .order_by(desc(ToolExecution.started_at))
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_metrics_by_tool(
        self,
        tool_name: str,
        days: int = 7,
    ) -> dict[str, Any]:
        """
        Get aggregated metrics for a tool.

        Args:
            tool_name: Tool identifier
            days: Days to analyze

        Returns:
            Metrics dictionary
        """
        from datetime import timedelta

        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        stmt = (
            select(
                func.count().label("total"),
                func.sum(
                    func.cast(
                        ToolExecution.status == ToolStatus.SUCCESS, type_=func.Integer
                    )
                ).label("success"),
                func.avg(ToolExecution.latency_ms).label("avg_latency"),
                func.sum(
                    func.cast(
                        ToolExecution.cache_hit == True, type_=func.Integer
                    )  # noqa: E712
                ).label("cache_hits"),
            )
            .where(ToolExecution.tool_name == tool_name)
            .where(ToolExecution.started_at >= cutoff)
        )

        result = await self.session.execute(stmt)
        row = result.one()

        return {
            "tool_name": tool_name,
            "period_days": days,
            "total_executions": row.total or 0,
            "success_count": row.success or 0,
            "success_rate": (row.success / row.total * 100) if row.total else 0,
            "avg_latency_ms": round(row.avg_latency or 0, 2),
            "cache_hit_count": row.cache_hits or 0,
            "cache_hit_rate": (row.cache_hits / row.total * 100) if row.total else 0,
        }
