# =============================================================================
# MedeX - Conversation Manager
# =============================================================================
"""
Conversation management for MedeX V2.

This module provides:
- Conversation CRUD operations
- Message history management
- Conversation metadata updates
- User conversation lists

Design:
- Async operations throughout
- Integration with database repositories
- Title auto-generation support
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from ..db.models import Conversation, Message, MessageRole
from ..db.repositories import ConversationRepository, MessageRepository
from .title_generator import TitleGenerator, get_title_generator

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


# =============================================================================
# Data Classes
# =============================================================================


class ConversationSummary:
    """Summary of a conversation for listing."""

    __slots__ = (
        "id",
        "title",
        "created_at",
        "updated_at",
        "message_count",
        "last_message_preview",
    )

    def __init__(
        self,
        id: UUID,
        title: str,
        created_at: datetime,
        updated_at: datetime,
        message_count: int = 0,
        last_message_preview: str | None = None,
    ):
        self.id = id
        self.title = title
        self.created_at = created_at
        self.updated_at = updated_at
        self.message_count = message_count
        self.last_message_preview = last_message_preview


class MessageData:
    """Structured message data."""

    __slots__ = ("role", "content", "metadata", "created_at")

    def __init__(
        self,
        role: MessageRole,
        content: str,
        metadata: dict | None = None,
        created_at: datetime | None = None,
    ):
        self.role = role
        self.content = content
        self.metadata = metadata or {}
        self.created_at = created_at or datetime.utcnow()


# =============================================================================
# Conversation Manager
# =============================================================================


class ConversationManager:
    """
    Manage conversations and messages.

    Provides high-level operations for:
    - Creating and retrieving conversations
    - Adding messages to conversations
    - Listing user conversations
    - Updating conversation metadata
    """

    def __init__(
        self,
        session: AsyncSession,
        title_generator: TitleGenerator | None = None,
    ):
        """
        Initialize conversation manager.

        Args:
            session: Async database session
            title_generator: Optional title generator instance
        """
        self._session = session
        self._conv_repo = ConversationRepository(session)
        self._msg_repo = MessageRepository(session)
        self._title_gen = title_generator or get_title_generator()

    # -------------------------------------------------------------------------
    # Conversation Operations
    # -------------------------------------------------------------------------

    async def create_conversation(
        self,
        user_id: UUID,
        title: str | None = None,
        metadata: dict | None = None,
    ) -> Conversation:
        """
        Create a new conversation.

        Args:
            user_id: Owner user ID
            title: Optional title (auto-generated if not provided)
            metadata: Optional metadata dict

        Returns:
            Created Conversation entity
        """
        conversation = Conversation(
            id=uuid4(),
            user_id=user_id,
            title=title or "Nueva conversación",
            metadata=metadata or {},
            message_count=0,
        )

        created = await self._conv_repo.create(conversation)
        logger.info(f"Created conversation {created.id} for user {user_id}")
        return created

    async def get_conversation(
        self,
        conversation_id: UUID,
        user_id: UUID | None = None,
    ) -> Conversation | None:
        """
        Get conversation by ID.

        Args:
            conversation_id: Conversation UUID
            user_id: Optional user ID for ownership validation

        Returns:
            Conversation if found and owned by user, None otherwise
        """
        conversation = await self._conv_repo.get_by_id(conversation_id)

        if conversation is None:
            return None

        # Validate ownership if user_id provided
        if user_id is not None and conversation.user_id != user_id:
            logger.warning(
                f"User {user_id} attempted to access "
                f"conversation {conversation_id} owned by {conversation.user_id}"
            )
            return None

        return conversation

    async def list_conversations(
        self,
        user_id: UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ConversationSummary]:
        """
        List user conversations with summaries.

        Args:
            user_id: User UUID
            limit: Maximum conversations to return
            offset: Pagination offset

        Returns:
            List of ConversationSummary objects
        """
        conversations = await self._conv_repo.list_by_user(
            user_id=user_id,
            limit=limit,
            offset=offset,
        )

        summaries = []
        for conv in conversations:
            # Get last message for preview
            last_message = await self._msg_repo.get_last_message(conv.id)
            preview = None
            if last_message:
                preview = last_message.content[:100]
                if len(last_message.content) > 100:
                    preview += "..."

            summaries.append(
                ConversationSummary(
                    id=conv.id,
                    title=conv.title,
                    created_at=conv.created_at,
                    updated_at=conv.updated_at,
                    message_count=conv.message_count,
                    last_message_preview=preview,
                )
            )

        return summaries

    async def update_title(
        self,
        conversation_id: UUID,
        title: str,
    ) -> Conversation | None:
        """
        Update conversation title.

        Args:
            conversation_id: Conversation UUID
            title: New title

        Returns:
            Updated Conversation or None if not found
        """
        conversation = await self._conv_repo.get_by_id(conversation_id)
        if conversation is None:
            return None

        conversation.title = title
        updated = await self._conv_repo.update(conversation)
        logger.debug(f"Updated title for conversation {conversation_id}")
        return updated

    async def delete_conversation(
        self,
        conversation_id: UUID,
        user_id: UUID | None = None,
        soft: bool = True,
    ) -> bool:
        """
        Delete a conversation.

        Args:
            conversation_id: Conversation UUID
            user_id: Optional user ID for ownership validation
            soft: If True, soft delete; if False, hard delete

        Returns:
            True if deleted, False if not found
        """
        conversation = await self.get_conversation(conversation_id, user_id)
        if conversation is None:
            return False

        if soft:
            await self._conv_repo.soft_delete(conversation_id)
        else:
            await self._conv_repo.delete(conversation_id)

        logger.info(f"Deleted conversation {conversation_id} (soft={soft})")
        return True

    # -------------------------------------------------------------------------
    # Message Operations
    # -------------------------------------------------------------------------

    async def add_message(
        self,
        conversation_id: UUID,
        role: MessageRole,
        content: str,
        metadata: dict | None = None,
        auto_title: bool = True,
    ) -> Message:
        """
        Add a message to a conversation.

        Args:
            conversation_id: Target conversation UUID
            role: Message role (user, assistant, system)
            content: Message content
            metadata: Optional message metadata
            auto_title: If True, auto-generate title from first user message

        Returns:
            Created Message entity
        """
        # Create message
        message = Message(
            id=uuid4(),
            conversation_id=conversation_id,
            role=role,
            content=content,
            metadata=metadata or {},
        )

        created = await self._msg_repo.create(message)

        # Update conversation message count
        conversation = await self._conv_repo.get_by_id(conversation_id)
        if conversation:
            conversation.message_count += 1

            # Auto-generate title from first user message
            if (
                auto_title
                and role == MessageRole.USER
                and conversation.message_count == 1
                and conversation.title == "Nueva conversación"
            ):
                new_title = self._title_gen.generate_from_message(content)
                conversation.title = new_title
                logger.debug(f"Auto-generated title: {new_title}")

            await self._conv_repo.update(conversation)

        logger.debug(f"Added {role.value} message to conversation {conversation_id}")
        return created

    async def add_user_message(
        self,
        conversation_id: UUID,
        content: str,
        metadata: dict | None = None,
    ) -> Message:
        """Convenience method to add a user message."""
        return await self.add_message(
            conversation_id=conversation_id,
            role=MessageRole.USER,
            content=content,
            metadata=metadata,
        )

    async def add_assistant_message(
        self,
        conversation_id: UUID,
        content: str,
        metadata: dict | None = None,
    ) -> Message:
        """Convenience method to add an assistant message."""
        return await self.add_message(
            conversation_id=conversation_id,
            role=MessageRole.ASSISTANT,
            content=content,
            metadata=metadata,
            auto_title=False,
        )

    async def add_system_message(
        self,
        conversation_id: UUID,
        content: str,
        metadata: dict | None = None,
    ) -> Message:
        """Convenience method to add a system message."""
        return await self.add_message(
            conversation_id=conversation_id,
            role=MessageRole.SYSTEM,
            content=content,
            metadata=metadata,
            auto_title=False,
        )

    async def get_messages(
        self,
        conversation_id: UUID,
        limit: int | None = None,
        include_system: bool = True,
    ) -> list[Message]:
        """
        Get messages for a conversation.

        Args:
            conversation_id: Conversation UUID
            limit: Optional limit on messages returned
            include_system: Whether to include system messages

        Returns:
            List of Message entities ordered by creation time
        """
        messages = await self._msg_repo.list_by_conversation(
            conversation_id=conversation_id,
            limit=limit,
        )

        if not include_system:
            messages = [m for m in messages if m.role != MessageRole.SYSTEM]

        return messages

    async def get_message_history(
        self,
        conversation_id: UUID,
        limit: int | None = None,
    ) -> list[MessageData]:
        """
        Get message history as structured data.

        Args:
            conversation_id: Conversation UUID
            limit: Optional limit on messages

        Returns:
            List of MessageData objects
        """
        messages = await self.get_messages(conversation_id, limit)

        return [
            MessageData(
                role=msg.role,
                content=msg.content,
                metadata=msg.metadata,
                created_at=msg.created_at,
            )
            for msg in messages
        ]

    # -------------------------------------------------------------------------
    # Utility Methods
    # -------------------------------------------------------------------------

    async def get_or_create_conversation(
        self,
        user_id: UUID,
        conversation_id: UUID | None = None,
    ) -> Conversation:
        """
        Get existing or create new conversation.

        Args:
            user_id: User UUID
            conversation_id: Optional existing conversation ID

        Returns:
            Existing or new Conversation
        """
        if conversation_id:
            conversation = await self.get_conversation(conversation_id, user_id)
            if conversation:
                return conversation

        return await self.create_conversation(user_id)

    async def count_messages(self, conversation_id: UUID) -> int:
        """
        Count messages in a conversation.

        Args:
            conversation_id: Conversation UUID

        Returns:
            Number of messages
        """
        return await self._msg_repo.count_by_conversation(conversation_id)
