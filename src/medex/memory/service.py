# =============================================================================
# MedeX - Memory Service (Facade)
# =============================================================================
"""
Unified memory service for MedeX V2.

This module provides:
- Facade pattern for all memory operations
- Conversation management
- Context window building
- Patient context extraction
- Message persistence

Design:
- Single entry point for memory subsystem
- Lazy initialization of components
- Cache integration
- Async operations throughout
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any
from uuid import UUID

from .context_window import ContextWindow, ContextWindowManager
from .conversation_manager import ConversationManager, ConversationSummary, MessageData
from .patient_context import (
    PatientContext,
    get_patient_context_extractor,
)
from .title_generator import get_title_generator
from .token_counter import get_token_counter

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from ..db.cache import ContextWindowCache
    from ..db.models import Conversation, Message, MessageRole

logger = logging.getLogger(__name__)


# =============================================================================
# Memory Service
# =============================================================================


class MemoryService:
    """
    Unified memory service facade.

    Provides a single interface for:
    - Conversation CRUD
    - Message management
    - Context window building
    - Patient context extraction
    - Caching
    """

    def __init__(
        self,
        session: AsyncSession,
        cache: ContextWindowCache | None = None,
        max_context_tokens: int = 8192,
        model_name: str = "gpt-4",
    ):
        """
        Initialize memory service.

        Args:
            session: Async database session
            cache: Optional context window cache
            max_context_tokens: Maximum tokens for context window
            model_name: Model name for token counting
        """
        self._session = session
        self._cache = cache

        # Initialize components
        self._token_counter = get_token_counter()
        self._title_generator = get_title_generator()
        self._patient_extractor = get_patient_context_extractor()

        self._conversation_manager = ConversationManager(
            session=session,
            title_generator=self._title_generator,
        )

        self._context_manager = ContextWindowManager(
            max_context_tokens=max_context_tokens,
            token_counter=self._token_counter,
            model_name=model_name,
        )

        self._model = model_name
        self._max_tokens = max_context_tokens

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
            title: Optional initial title
            metadata: Optional metadata

        Returns:
            Created Conversation
        """
        return await self._conversation_manager.create_conversation(
            user_id=user_id,
            title=title,
            metadata=metadata,
        )

    async def get_conversation(
        self,
        conversation_id: UUID,
        user_id: UUID | None = None,
    ) -> Conversation | None:
        """
        Get conversation by ID.

        Args:
            conversation_id: Conversation UUID
            user_id: Optional user ID for validation

        Returns:
            Conversation if found
        """
        return await self._conversation_manager.get_conversation(
            conversation_id=conversation_id,
            user_id=user_id,
        )

    async def list_conversations(
        self,
        user_id: UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ConversationSummary]:
        """
        List user conversations.

        Args:
            user_id: User UUID
            limit: Max conversations
            offset: Pagination offset

        Returns:
            List of ConversationSummary
        """
        return await self._conversation_manager.list_conversations(
            user_id=user_id,
            limit=limit,
            offset=offset,
        )

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
            user_id: Optional user ID for validation
            soft: If True, soft delete

        Returns:
            True if deleted
        """
        success = await self._conversation_manager.delete_conversation(
            conversation_id=conversation_id,
            user_id=user_id,
            soft=soft,
        )

        # Clear cache if present
        if success and self._cache:
            await self._cache.delete(str(conversation_id))

        return success

    # -------------------------------------------------------------------------
    # Message Operations
    # -------------------------------------------------------------------------

    async def add_message(
        self,
        conversation_id: UUID,
        role: MessageRole,
        content: str,
        metadata: dict | None = None,
    ) -> Message:
        """
        Add a message to conversation.

        Args:
            conversation_id: Target conversation
            role: Message role
            content: Message content
            metadata: Optional metadata

        Returns:
            Created Message
        """
        message = await self._conversation_manager.add_message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            metadata=metadata,
        )

        # Invalidate cache
        if self._cache:
            await self._cache.delete(str(conversation_id))

        return message

    async def add_user_message(
        self,
        conversation_id: UUID,
        content: str,
        metadata: dict | None = None,
    ) -> Message:
        """Add a user message."""
        return await self._conversation_manager.add_user_message(
            conversation_id=conversation_id,
            content=content,
            metadata=metadata,
        )

    async def add_assistant_message(
        self,
        conversation_id: UUID,
        content: str,
        metadata: dict | None = None,
    ) -> Message:
        """Add an assistant message."""
        return await self._conversation_manager.add_assistant_message(
            conversation_id=conversation_id,
            content=content,
            metadata=metadata,
        )

    async def get_messages(
        self,
        conversation_id: UUID,
        limit: int | None = None,
    ) -> list[Message]:
        """
        Get messages for conversation.

        Args:
            conversation_id: Conversation UUID
            limit: Optional message limit

        Returns:
            List of Message entities
        """
        return await self._conversation_manager.get_messages(
            conversation_id=conversation_id,
            limit=limit,
        )

    async def get_message_history(
        self,
        conversation_id: UUID,
        limit: int | None = None,
    ) -> list[MessageData]:
        """
        Get message history as structured data.

        Args:
            conversation_id: Conversation UUID
            limit: Optional limit

        Returns:
            List of MessageData
        """
        return await self._conversation_manager.get_message_history(
            conversation_id=conversation_id,
            limit=limit,
        )

    # -------------------------------------------------------------------------
    # Context Window Operations
    # -------------------------------------------------------------------------

    async def build_context(
        self,
        conversation_id: UUID,
        system_prompt: str | None = None,
        include_patient_context: bool = True,
        max_messages: int | None = None,
    ) -> ContextWindow:
        """
        Build context window for LLM interaction.

        Args:
            conversation_id: Conversation UUID
            system_prompt: Optional system prompt
            include_patient_context: Include extracted patient context
            max_messages: Optional message limit

        Returns:
            Built ContextWindow
        """
        # Check cache first
        if self._cache:
            cached = await self._cache.get(str(conversation_id))
            if cached:
                logger.debug(f"Cache hit for conversation {conversation_id}")
                return ContextWindow(**cached)

        # Get messages
        messages = await self._conversation_manager.get_messages(
            conversation_id=conversation_id,
            limit=max_messages,
        )

        # Extract patient context if needed
        patient_context = None
        if include_patient_context and messages:
            patient_context = await self.extract_patient_context(
                conversation_id=conversation_id,
                messages=messages,
            )

        # Build context window
        context = self._context_manager.build_context(
            messages=messages,
            system_prompt=system_prompt,
            patient_context=patient_context.to_dict() if patient_context else None,
        )

        # Cache result
        if self._cache and not context.truncated:
            await self._cache.set(
                key=str(conversation_id),
                value={
                    "messages": [
                        {
                            "role": m.role,
                            "content": m.content,
                            "token_count": m.token_count,
                            "priority": m.priority.value,
                        }
                        for m in context.messages
                    ],
                    "total_tokens": context.total_tokens,
                    "remaining_budget": context.remaining_budget,
                    "truncated": context.truncated,
                    "dropped_count": context.dropped_count,
                },
                ttl=300,  # 5 minute cache
            )

        return context

    async def get_context_for_llm(
        self,
        conversation_id: UUID,
        system_prompt: str | None = None,
        new_message: str | None = None,
    ) -> list[dict[str, str]]:
        """
        Get context ready for LLM API call.

        Args:
            conversation_id: Conversation UUID
            system_prompt: Optional system prompt
            new_message: Optional new user message to append

        Returns:
            List of message dicts for LLM
        """
        context = await self.build_context(
            conversation_id=conversation_id,
            system_prompt=system_prompt,
        )

        messages = context.to_messages()

        # Append new message if provided
        if new_message:
            messages.append(
                {
                    "role": "user",
                    "content": new_message,
                }
            )

        return messages

    # -------------------------------------------------------------------------
    # Patient Context Operations
    # -------------------------------------------------------------------------

    async def extract_patient_context(
        self,
        conversation_id: UUID,
        messages: list[Message] | None = None,
    ) -> PatientContext:
        """
        Extract patient context from conversation.

        Args:
            conversation_id: Conversation UUID
            messages: Optional pre-fetched messages

        Returns:
            Extracted PatientContext
        """
        if messages is None:
            messages = await self._conversation_manager.get_messages(
                conversation_id=conversation_id,
            )

        # Convert to dict format
        message_dicts = [
            {"role": msg.role.value, "content": msg.content} for msg in messages
        ]

        return self._patient_extractor.extract_from_messages(message_dicts)

    async def get_patient_summary(
        self,
        conversation_id: UUID,
    ) -> dict[str, Any]:
        """
        Get patient context summary.

        Args:
            conversation_id: Conversation UUID

        Returns:
            Patient context as dict
        """
        context = await self.extract_patient_context(conversation_id)
        return context.to_dict()

    # -------------------------------------------------------------------------
    # Title Operations
    # -------------------------------------------------------------------------

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
            Updated Conversation
        """
        return await self._conversation_manager.update_title(
            conversation_id=conversation_id,
            title=title,
        )

    def generate_title(self, message: str) -> str:
        """
        Generate title from first message.

        Args:
            message: First user message

        Returns:
            Generated title
        """
        return self._title_generator.generate_from_message(message)

    # -------------------------------------------------------------------------
    # Token Operations
    # -------------------------------------------------------------------------

    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text.

        Args:
            text: Text to count

        Returns:
            Token count
        """
        return self._token_counter.count_tokens(text, model=self._model)

    def count_message_tokens(self, message: dict[str, str]) -> int:
        """
        Count tokens in a message.

        Args:
            message: Message dict with role and content

        Returns:
            Token count
        """
        return self._token_counter.count_message_tokens(message, model=self._model)

    def get_remaining_budget(
        self,
        used_tokens: int,
        reserve_for_response: int = 1500,
    ) -> int:
        """
        Calculate remaining token budget.

        Args:
            used_tokens: Tokens already used
            reserve_for_response: Tokens to reserve for response

        Returns:
            Remaining budget
        """
        return self._token_counter.calculate_remaining_budget(
            used_tokens=used_tokens,
            max_tokens=self._max_tokens,
            reserve_for_response=reserve_for_response,
        )

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
            Conversation entity
        """
        return await self._conversation_manager.get_or_create_conversation(
            user_id=user_id,
            conversation_id=conversation_id,
        )

    async def get_context_stats(
        self,
        conversation_id: UUID,
    ) -> dict[str, Any]:
        """
        Get context window statistics.

        Args:
            conversation_id: Conversation UUID

        Returns:
            Stats dictionary
        """
        context = await self.build_context(conversation_id)
        return self._context_manager.summarize_context(context)

    async def clear_cache(self, conversation_id: UUID) -> None:
        """
        Clear cached context for conversation.

        Args:
            conversation_id: Conversation UUID
        """
        if self._cache:
            await self._cache.delete(str(conversation_id))


# =============================================================================
# Factory Function
# =============================================================================


async def create_memory_service(
    session: AsyncSession,
    cache: ContextWindowCache | None = None,
    max_context_tokens: int = 8192,
    model_name: str = "gpt-4",
) -> MemoryService:
    """
    Create and configure memory service.

    Args:
        session: Async database session
        cache: Optional cache instance
        max_context_tokens: Max tokens for context
        model_name: Model name for counting

    Returns:
        Configured MemoryService
    """
    return MemoryService(
        session=session,
        cache=cache,
        max_context_tokens=max_context_tokens,
        model_name=model_name,
    )
