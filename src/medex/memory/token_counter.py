# =============================================================================
# MedeX - Token Counter
# =============================================================================
"""
Token counting utilities for context window management.

This module provides:
- Accurate token counting using tiktoken
- Fallback estimation for unsupported models
- Message-level and conversation-level counting
- Token budget tracking for LLM context

Supported Models:
- OpenAI GPT-3.5/4 (cl100k_base encoding)
- Kimi K2 (approximation using cl100k_base)
- HuggingFace models (word-based estimation)
"""

from __future__ import annotations

import logging
import re
from typing import Optional
from functools import lru_cache

logger = logging.getLogger(__name__)


# =============================================================================
# Token Counting
# =============================================================================


class TokenCounter:
    """
    Token counter for managing LLM context windows.

    Uses tiktoken when available, falls back to word-based estimation.

    Attributes:
        model: Target model name for tokenization
        encoding: tiktoken encoding instance (if available)
    """

    # Token limits by model
    MODEL_LIMITS = {
        "moonshot-v1-8k": 8192,
        "moonshot-v1-32k": 32768,
        "moonshot-v1-128k": 131072,
        "kimi-k2": 131072,
        "gpt-3.5-turbo": 4096,
        "gpt-4": 8192,
        "gpt-4-32k": 32768,
        "gpt-4-turbo": 128000,
        "qwen-72b": 32768,
        "deepseek-v3": 65536,
    }

    # Default encoding to use
    DEFAULT_ENCODING = "cl100k_base"

    def __init__(self, model: str = "kimi-k2"):
        """
        Initialize token counter for specific model.

        Args:
            model: Target model name
        """
        self.model = model
        self._encoding = None
        self._tiktoken_available = False

        # Try to load tiktoken
        try:
            import tiktoken

            self._encoding = tiktoken.get_encoding(self.DEFAULT_ENCODING)
            self._tiktoken_available = True
            logger.debug(f"Using tiktoken with {self.DEFAULT_ENCODING} encoding")
        except ImportError:
            logger.warning("tiktoken not available, using word-based estimation")
        except Exception as e:
            logger.warning(f"Failed to load tiktoken: {e}")

    @property
    def max_tokens(self) -> int:
        """Get maximum token limit for current model."""
        return self.MODEL_LIMITS.get(self.model, 8192)

    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text.

        Args:
            text: Input text to count

        Returns:
            Estimated token count
        """
        if not text:
            return 0

        if self._tiktoken_available and self._encoding:
            return len(self._encoding.encode(text))

        # Fallback: word-based estimation
        # Average ratio is ~1.3 tokens per word for English
        # Spanish tends to be similar
        return self._estimate_tokens(text)

    @staticmethod
    @lru_cache(maxsize=1000)
    def _estimate_tokens(text: str) -> int:
        """
        Estimate tokens using word-based heuristics.

        This method is cached for frequently repeated texts.

        Args:
            text: Input text

        Returns:
            Estimated token count
        """
        # Split by whitespace and punctuation
        words = re.findall(r"\b\w+\b", text)
        word_count = len(words)

        # Count special characters and punctuation
        special_chars = len(re.findall(r"[^\w\s]", text))

        # Numbers are typically 1 token per 3-4 digits
        numbers = re.findall(r"\d+", text)
        number_tokens = sum(max(1, len(n) // 3) for n in numbers)

        # Estimate: ~1.3 tokens per word + punctuation
        estimated = int(word_count * 1.3) + special_chars + number_tokens

        return max(1, estimated)

    def count_message_tokens(
        self,
        role: str,
        content: str,
        name: Optional[str] = None,
    ) -> int:
        """
        Count tokens for a chat message including overhead.

        OpenAI format adds ~4 tokens per message for formatting.

        Args:
            role: Message role (user, assistant, system)
            content: Message content
            name: Optional name field

        Returns:
            Total token count including overhead
        """
        # Base content tokens
        tokens = self.count_tokens(content)

        # Role tokens (~1 token)
        tokens += 1

        # Message formatting overhead (~3 tokens)
        tokens += 3

        # Name field if present
        if name:
            tokens += self.count_tokens(name) + 1

        return tokens

    def count_messages_tokens(
        self,
        messages: list[dict],
    ) -> int:
        """
        Count total tokens for a list of messages.

        Args:
            messages: List of message dicts with role and content

        Returns:
            Total token count
        """
        total = 0
        for msg in messages:
            total += self.count_message_tokens(
                role=msg.get("role", "user"),
                content=msg.get("content", ""),
                name=msg.get("name"),
            )

        # Add reply priming (~3 tokens)
        total += 3

        return total

    def calculate_remaining_budget(
        self,
        current_tokens: int,
        reserve_for_response: int = 2000,
    ) -> int:
        """
        Calculate remaining token budget for context.

        Args:
            current_tokens: Tokens already used
            reserve_for_response: Tokens to reserve for model response

        Returns:
            Remaining tokens available for context
        """
        available = self.max_tokens - reserve_for_response
        remaining = available - current_tokens
        return max(0, remaining)

    def truncate_to_budget(
        self,
        text: str,
        max_tokens: int,
    ) -> str:
        """
        Truncate text to fit within token budget.

        Args:
            text: Text to truncate
            max_tokens: Maximum allowed tokens

        Returns:
            Truncated text
        """
        current_tokens = self.count_tokens(text)

        if current_tokens <= max_tokens:
            return text

        # Binary search for truncation point
        words = text.split()
        low, high = 0, len(words)

        while low < high:
            mid = (low + high + 1) // 2
            truncated = " ".join(words[:mid])

            if self.count_tokens(truncated) <= max_tokens:
                low = mid
            else:
                high = mid - 1

        return " ".join(words[:low]) + "..."


# =============================================================================
# Singleton Instance
# =============================================================================

_default_counter: Optional[TokenCounter] = None


def get_token_counter(model: str = "kimi-k2") -> TokenCounter:
    """
    Get or create default token counter.

    Args:
        model: Target model name

    Returns:
        TokenCounter instance
    """
    global _default_counter

    if _default_counter is None or _default_counter.model != model:
        _default_counter = TokenCounter(model)

    return _default_counter
