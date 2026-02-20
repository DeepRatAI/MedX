# =============================================================================
# MedeX - Memory System Module
# =============================================================================
"""
Conversation memory and context management for MedeX V2.

This module provides:
- Conversation lifecycle management
- Message persistence with token tracking
- Context window management for LLM
- Patient clinical context extraction
- Auto-titling for conversations

Architecture:
    MemoryService (Facade)
    ├── ConversationManager (CRUD + lifecycle)
    ├── ContextWindowManager (LLM context building)
    └── PatientContextExtractor (Clinical data extraction)

Usage:
    from medex.memory import MemoryService, create_memory_service

    memory = await create_memory_service(session)
    conversation = await memory.get_or_create_conversation(user_id)
    await memory.add_user_message(conversation.id, "What is diabetes?")
    context = await memory.build_context(conversation.id)
"""

from .context_window import (
    ContextMessage,
    ContextPriority,
    ContextWindow,
    ContextWindowManager,
)
from .conversation_manager import (
    ConversationManager,
    ConversationSummary,
    MessageData,
)
from .patient_context import (
    EmergencyLevel,
    PatientContext,
    PatientContextExtractor,
    get_patient_context_extractor,
)
from .service import MemoryService, create_memory_service
from .title_generator import TitleGenerator, get_title_generator
from .token_counter import TokenCounter, get_token_counter

__all__ = [
    # Service
    "MemoryService",
    "create_memory_service",
    # Conversation
    "ConversationManager",
    "ConversationSummary",
    "MessageData",
    # Context Window
    "ContextWindowManager",
    "ContextWindow",
    "ContextMessage",
    "ContextPriority",
    # Patient Context
    "PatientContextExtractor",
    "PatientContext",
    "EmergencyLevel",
    "get_patient_context_extractor",
    # Title
    "TitleGenerator",
    "get_title_generator",
    # Token Counting
    "TokenCounter",
    "get_token_counter",
]
