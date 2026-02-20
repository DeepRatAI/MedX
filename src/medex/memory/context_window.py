# =============================================================================
# MedeX - Context Window Manager
# =============================================================================
"""
Context window management for LLM interactions in MedeX V2.

This module provides:
- Context window building from conversation history
- Token budget management
- Message prioritization for context
- System prompt injection
- Context truncation strategies

Design:
- Respects model token limits
- Prioritizes recent messages
- Preserves system prompts
- Supports sliding window
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any

from .token_counter import TokenCounter, get_token_counter

if TYPE_CHECKING:
    from ..db.models import Message

logger = logging.getLogger(__name__)


# =============================================================================
# Enums and Data Classes
# =============================================================================


class ContextPriority(Enum):
    """Message priority levels for context inclusion."""

    CRITICAL = 1  # System prompts, must include
    HIGH = 2  # Recent messages, clinical data
    MEDIUM = 3  # Older conversation history
    LOW = 4  # Can be dropped if needed


@dataclass
class ContextMessage:
    """Message prepared for context window."""

    role: str
    content: str
    token_count: int
    priority: ContextPriority = ContextPriority.MEDIUM
    timestamp: datetime | None = None
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to LLM-ready message dict."""
        return {
            "role": self.role,
            "content": self.content,
        }


@dataclass
class ContextWindow:
    """Built context window ready for LLM."""

    messages: list[ContextMessage]
    total_tokens: int
    remaining_budget: int
    truncated: bool = False
    dropped_count: int = 0

    def to_messages(self) -> list[dict[str, str]]:
        """Convert to LLM message format."""
        return [msg.to_dict() for msg in self.messages]


# =============================================================================
# Context Window Manager
# =============================================================================


class ContextWindowManager:
    """
    Manage context window for LLM interactions.

    Handles:
    - Token budget allocation
    - Message prioritization
    - Context building from history
    - Truncation when needed
    """

    # Default token budgets
    DEFAULT_MAX_TOKENS = 8192
    SYSTEM_PROMPT_RESERVE = 2000
    RESPONSE_RESERVE = 1500
    MIN_CONTEXT_TOKENS = 500

    def __init__(
        self,
        max_context_tokens: int = DEFAULT_MAX_TOKENS,
        system_prompt_reserve: int = SYSTEM_PROMPT_RESERVE,
        response_reserve: int = RESPONSE_RESERVE,
        token_counter: TokenCounter | None = None,
        model_name: str = "gpt-4",
    ):
        """
        Initialize context window manager.

        Args:
            max_context_tokens: Maximum tokens for context
            system_prompt_reserve: Tokens reserved for system prompt
            response_reserve: Tokens reserved for response
            token_counter: Optional token counter instance
            model_name: Model name for token counting
        """
        self._max_tokens = max_context_tokens
        self._system_reserve = system_prompt_reserve
        self._response_reserve = response_reserve
        self._token_counter = token_counter or get_token_counter()
        self._model = model_name

    @property
    def available_context_budget(self) -> int:
        """Calculate available tokens for conversation context."""
        return max(
            self.MIN_CONTEXT_TOKENS,
            self._max_tokens - self._system_reserve - self._response_reserve,
        )

    # -------------------------------------------------------------------------
    # Context Building
    # -------------------------------------------------------------------------

    def build_context(
        self,
        messages: list[Message],
        system_prompt: str | None = None,
        patient_context: dict | None = None,
        include_all: bool = False,
    ) -> ContextWindow:
        """
        Build context window from messages.

        Args:
            messages: List of Message entities (oldest first)
            system_prompt: Optional system prompt to include
            patient_context: Optional patient context data
            include_all: If True, include all messages (may exceed budget)

        Returns:
            ContextWindow with built context
        """
        context_messages: list[ContextMessage] = []
        total_tokens = 0
        budget = self.available_context_budget

        # 1. Add system prompt if provided
        if system_prompt:
            system_msg = self._build_system_prompt(system_prompt, patient_context)
            context_messages.append(system_msg)
            total_tokens += system_msg.token_count
            budget -= system_msg.token_count

        # 2. Convert messages to context messages
        converted = [
            self._convert_message(msg, idx, len(messages))
            for idx, msg in enumerate(messages)
        ]

        # 3. Include messages within budget
        if include_all:
            # Include all, regardless of budget
            context_messages.extend(converted)
            total_tokens += sum(m.token_count for m in converted)
            dropped = 0
            truncated = False
        else:
            # Prioritize and fit to budget
            selected, dropped = self._select_messages(converted, budget)
            context_messages.extend(selected)
            total_tokens += sum(m.token_count for m in selected)
            truncated = dropped > 0

        return ContextWindow(
            messages=context_messages,
            total_tokens=total_tokens,
            remaining_budget=self._max_tokens - total_tokens - self._response_reserve,
            truncated=truncated,
            dropped_count=dropped,
        )

    def _build_system_prompt(
        self,
        base_prompt: str,
        patient_context: dict | None = None,
    ) -> ContextMessage:
        """Build system prompt message with patient context."""
        content = base_prompt

        # Inject patient context if available
        if patient_context:
            context_section = self._format_patient_context(patient_context)
            content = f"{base_prompt}\n\n{context_section}"

        token_count = self._token_counter.count_message_tokens(
            {"role": "system", "content": content},
            model=self._model,
        )

        return ContextMessage(
            role="system",
            content=content,
            token_count=token_count,
            priority=ContextPriority.CRITICAL,
        )

    def _format_patient_context(self, context: dict) -> str:
        """Format patient context for system prompt injection."""
        lines = ["## Contexto del Paciente"]

        if context.get("age"):
            lines.append(f"- Edad: {context['age']} años")
        if context.get("sex"):
            lines.append(f"- Sexo: {context['sex']}")
        if context.get("symptoms"):
            symptoms = ", ".join(context["symptoms"])
            lines.append(f"- Síntomas: {symptoms}")
        if context.get("conditions"):
            conditions = ", ".join(context["conditions"])
            lines.append(f"- Condiciones: {conditions}")
        if context.get("medications"):
            meds = ", ".join(context["medications"])
            lines.append(f"- Medicamentos: {meds}")
        if context.get("allergies"):
            allergies = ", ".join(context["allergies"])
            lines.append(f"- Alergias: {allergies}")
        if context.get("vitals"):
            vitals = context["vitals"]
            vitals_str = ", ".join(f"{k}: {v}" for k, v in vitals.items())
            lines.append(f"- Signos vitales: {vitals_str}")
        if context.get("is_emergency"):
            lines.append("- ⚠️ POSIBLE EMERGENCIA")

        return "\n".join(lines)

    def _convert_message(
        self,
        message: Message,
        index: int,
        total: int,
    ) -> ContextMessage:
        """Convert database message to context message."""
        # Determine priority based on position
        recency = (index + 1) / total  # 0 = oldest, 1 = newest

        if message.role.value == "system":
            priority = ContextPriority.CRITICAL
        elif recency >= 0.8:
            priority = ContextPriority.HIGH
        elif recency >= 0.5:
            priority = ContextPriority.MEDIUM
        else:
            priority = ContextPriority.LOW

        token_count = self._token_counter.count_message_tokens(
            {"role": message.role.value, "content": message.content},
            model=self._model,
        )

        return ContextMessage(
            role=message.role.value,
            content=message.content,
            token_count=token_count,
            priority=priority,
            timestamp=message.created_at,
            metadata=message.metadata or {},
        )

    def _select_messages(
        self,
        messages: list[ContextMessage],
        budget: int,
    ) -> tuple[list[ContextMessage], int]:
        """
        Select messages to fit within budget.

        Uses sliding window approach:
        1. Always include critical messages
        2. Include as many recent messages as possible
        3. Drop oldest messages first

        Args:
            messages: List of context messages
            budget: Available token budget

        Returns:
            Tuple of (selected messages, dropped count)
        """
        if not messages:
            return [], 0

        # Separate critical from non-critical
        critical = [m for m in messages if m.priority == ContextPriority.CRITICAL]
        non_critical = [m for m in messages if m.priority != ContextPriority.CRITICAL]

        # Calculate critical tokens
        critical_tokens = sum(m.token_count for m in critical)
        remaining_budget = budget - critical_tokens

        if remaining_budget <= 0:
            # Only room for critical messages
            return critical, len(non_critical)

        # Select from non-critical (newest first)
        selected = list(critical)
        dropped = 0

        # Work backwards through non-critical (most recent first)
        for msg in reversed(non_critical):
            if msg.token_count <= remaining_budget:
                selected.insert(len(critical), msg)  # Insert after critical
                remaining_budget -= msg.token_count
            else:
                dropped += 1

        # Reorder to maintain chronological order
        selected_non_critical = [
            m for m in selected if m.priority != ContextPriority.CRITICAL
        ]
        selected = critical + selected_non_critical

        return selected, dropped

    # -------------------------------------------------------------------------
    # Context Manipulation
    # -------------------------------------------------------------------------

    def append_message(
        self,
        context: ContextWindow,
        role: str,
        content: str,
    ) -> ContextWindow:
        """
        Append a new message to existing context.

        Args:
            context: Existing context window
            role: Message role
            content: Message content

        Returns:
            Updated context window
        """
        token_count = self._token_counter.count_message_tokens(
            {"role": role, "content": content},
            model=self._model,
        )

        new_msg = ContextMessage(
            role=role,
            content=content,
            token_count=token_count,
            priority=ContextPriority.HIGH,
            timestamp=datetime.utcnow(),
        )

        new_messages = context.messages + [new_msg]
        new_total = context.total_tokens + token_count

        # Check if we need to truncate
        if new_total > self._max_tokens - self._response_reserve:
            # Remove oldest non-critical messages
            new_messages, dropped = self._select_messages(
                new_messages,
                self._max_tokens - self._response_reserve,
            )
            new_total = sum(m.token_count for m in new_messages)
            return ContextWindow(
                messages=new_messages,
                total_tokens=new_total,
                remaining_budget=self._max_tokens - new_total - self._response_reserve,
                truncated=True,
                dropped_count=context.dropped_count + dropped,
            )

        return ContextWindow(
            messages=new_messages,
            total_tokens=new_total,
            remaining_budget=self._max_tokens - new_total - self._response_reserve,
            truncated=context.truncated,
            dropped_count=context.dropped_count,
        )

    def estimate_response_budget(self, context: ContextWindow) -> int:
        """
        Estimate available tokens for response.

        Args:
            context: Current context window

        Returns:
            Estimated tokens available for response
        """
        return max(0, self._max_tokens - context.total_tokens)

    # -------------------------------------------------------------------------
    # Utility Methods
    # -------------------------------------------------------------------------

    def summarize_context(self, context: ContextWindow) -> dict[str, Any]:
        """
        Get summary of context window state.

        Args:
            context: Context window to summarize

        Returns:
            Summary dictionary
        """
        role_counts = {}
        for msg in context.messages:
            role_counts[msg.role] = role_counts.get(msg.role, 0) + 1

        return {
            "message_count": len(context.messages),
            "total_tokens": context.total_tokens,
            "remaining_budget": context.remaining_budget,
            "truncated": context.truncated,
            "dropped_count": context.dropped_count,
            "messages_by_role": role_counts,
            "max_tokens": self._max_tokens,
            "utilization": context.total_tokens / self._max_tokens,
        }
