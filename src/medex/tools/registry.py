# =============================================================================
# MedeX - Tool Registry
# =============================================================================
"""
Tool registration and management for MedeX V2.

This module provides:
- ToolRegistry: Central registry for all tools
- @tool decorator for easy tool creation
- Tool discovery and filtering
- OpenAI/Anthropic format conversion

Design:
- Singleton registry pattern
- Decorator-based registration
- Category-based organization
- Runtime tool enable/disable
"""

from __future__ import annotations

import functools
import logging
from typing import Any, Callable, Coroutine

from .models import (
    ParameterType,
    ToolCategory,
    ToolDefinition,
    ToolParameter,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Tool Registry
# =============================================================================


class ToolRegistry:
    """
    Central registry for all available tools.

    Manages tool definitions and provides lookup/filtering.
    """

    def __init__(self):
        """Initialize empty registry."""
        self._tools: dict[str, ToolDefinition] = {}
        self._by_category: dict[ToolCategory, list[str]] = {
            cat: [] for cat in ToolCategory
        }

    def register(self, tool: ToolDefinition) -> None:
        """
        Register a tool definition.

        Args:
            tool: ToolDefinition to register

        Raises:
            ValueError: If tool with same name already exists
        """
        if tool.name in self._tools:
            logger.warning(f"Overwriting existing tool: {tool.name}")

        self._tools[tool.name] = tool
        if tool.name not in self._by_category[tool.category]:
            self._by_category[tool.category].append(tool.name)

        logger.debug(f"Registered tool: {tool.name} [{tool.category.value}]")

    def unregister(self, name: str) -> bool:
        """
        Remove a tool from registry.

        Args:
            name: Tool name to remove

        Returns:
            True if removed, False if not found
        """
        if name not in self._tools:
            return False

        tool = self._tools.pop(name)
        self._by_category[tool.category].remove(name)
        logger.debug(f"Unregistered tool: {name}")
        return True

    def get(self, name: str) -> ToolDefinition | None:
        """
        Get tool by name.

        Args:
            name: Tool name

        Returns:
            ToolDefinition or None if not found
        """
        return self._tools.get(name)

    def get_all(self, enabled_only: bool = True) -> list[ToolDefinition]:
        """
        Get all registered tools.

        Args:
            enabled_only: If True, only return enabled tools

        Returns:
            List of ToolDefinition
        """
        tools = list(self._tools.values())
        if enabled_only:
            tools = [t for t in tools if t.enabled]
        return tools

    def get_by_category(
        self,
        category: ToolCategory,
        enabled_only: bool = True,
    ) -> list[ToolDefinition]:
        """
        Get tools by category.

        Args:
            category: ToolCategory to filter by
            enabled_only: If True, only return enabled tools

        Returns:
            List of ToolDefinition in category
        """
        names = self._by_category.get(category, [])
        tools = [self._tools[n] for n in names if n in self._tools]
        if enabled_only:
            tools = [t for t in tools if t.enabled]
        return tools

    def get_by_tags(
        self,
        tags: list[str],
        match_all: bool = False,
        enabled_only: bool = True,
    ) -> list[ToolDefinition]:
        """
        Get tools by tags.

        Args:
            tags: Tags to filter by
            match_all: If True, tool must have all tags
            enabled_only: If True, only return enabled tools

        Returns:
            List of matching ToolDefinition
        """
        results = []
        tag_set = set(tags)

        for tool in self._tools.values():
            if enabled_only and not tool.enabled:
                continue

            tool_tags = set(tool.tags)
            if match_all:
                if tag_set.issubset(tool_tags):
                    results.append(tool)
            else:
                if tag_set & tool_tags:  # Any intersection
                    results.append(tool)

        return results

    def enable(self, name: str) -> bool:
        """Enable a tool by name."""
        tool = self._tools.get(name)
        if tool:
            tool.enabled = True
            return True
        return False

    def disable(self, name: str) -> bool:
        """Disable a tool by name."""
        tool = self._tools.get(name)
        if tool:
            tool.enabled = False
            return True
        return False

    def to_openai_format(
        self,
        tools: list[ToolDefinition] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Convert tools to OpenAI format.

        Args:
            tools: Specific tools to convert, or None for all enabled

        Returns:
            List of OpenAI tool definitions
        """
        if tools is None:
            tools = self.get_all(enabled_only=True)
        return [tool.to_openai_format() for tool in tools]

    def to_anthropic_format(
        self,
        tools: list[ToolDefinition] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Convert tools to Anthropic format.

        Args:
            tools: Specific tools to convert, or None for all enabled

        Returns:
            List of Anthropic tool definitions
        """
        if tools is None:
            tools = self.get_all(enabled_only=True)
        return [tool.to_anthropic_format() for tool in tools]

    def __len__(self) -> int:
        """Return number of registered tools."""
        return len(self._tools)

    def __contains__(self, name: str) -> bool:
        """Check if tool is registered."""
        return name in self._tools

    def summary(self) -> dict[str, Any]:
        """Get registry summary."""
        return {
            "total_tools": len(self._tools),
            "enabled_tools": len(self.get_all(enabled_only=True)),
            "by_category": {
                cat.value: len(
                    [n for n in names if n in self._tools and self._tools[n].enabled]
                )
                for cat, names in self._by_category.items()
            },
        }


# =============================================================================
# Singleton Registry
# =============================================================================

_registry: ToolRegistry | None = None


def get_tool_registry() -> ToolRegistry:
    """Get or create global tool registry."""
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
    return _registry


# =============================================================================
# Tool Decorator
# =============================================================================


def tool(
    name: str,
    description: str,
    category: ToolCategory,
    parameters: list[ToolParameter] | None = None,
    enabled: bool = True,
    requires_auth: bool = False,
    timeout_seconds: float = 30.0,
    max_retries: int = 0,
    cache_ttl: int | None = None,
    tags: list[str] | None = None,
    version: str = "1.0.0",
) -> Callable:
    """
    Decorator to register a function as a tool.

    Usage:
        @tool(
            name="check_drug_interactions",
            description="Check for drug-drug interactions",
            category=ToolCategory.DRUG,
            parameters=[
                ToolParameter(
                    name="drugs",
                    type=ParameterType.ARRAY,
                    description="List of drug names",
                ),
            ],
        )
        async def check_drug_interactions(drugs: list[str]) -> dict:
            ...

    Args:
        name: Unique tool name
        description: Human-readable description
        category: Tool category
        parameters: List of parameter definitions
        enabled: Whether tool is enabled by default
        requires_auth: Whether tool requires authentication
        timeout_seconds: Execution timeout
        max_retries: Max retry attempts on failure
        cache_ttl: Cache TTL in seconds (None to disable)
        tags: Optional tags for filtering
        version: Tool version

    Returns:
        Decorator function
    """

    def decorator(
        func: Callable[..., Coroutine[Any, Any, Any]],
    ) -> Callable[..., Coroutine[Any, Any, Any]]:
        # Create tool definition
        tool_def = ToolDefinition(
            name=name,
            description=description,
            category=category,
            parameters=parameters or [],
            handler=func,
            enabled=enabled,
            requires_auth=requires_auth,
            timeout_seconds=timeout_seconds,
            max_retries=max_retries,
            cache_ttl=cache_ttl,
            tags=tags or [],
            version=version,
        )

        # Register with global registry
        registry = get_tool_registry()
        registry.register(tool_def)

        # Preserve function metadata
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            return await func(*args, **kwargs)

        # Attach tool definition to wrapper
        wrapper._tool_definition = tool_def  # type: ignore

        return wrapper

    return decorator


# =============================================================================
# Parameter Builder Helpers
# =============================================================================


def param(
    name: str,
    type: ParameterType,
    description: str,
    required: bool = True,
    **kwargs: Any,
) -> ToolParameter:
    """
    Shorthand for creating ToolParameter.

    Args:
        name: Parameter name
        type: Parameter type
        description: Parameter description
        required: Whether parameter is required
        **kwargs: Additional parameter options

    Returns:
        ToolParameter instance
    """
    return ToolParameter(
        name=name,
        type=type,
        description=description,
        required=required,
        **kwargs,
    )


def string_param(
    name: str,
    description: str,
    required: bool = True,
    **kwargs: Any,
) -> ToolParameter:
    """Create a string parameter."""
    return param(name, ParameterType.STRING, description, required, **kwargs)


def number_param(
    name: str,
    description: str,
    required: bool = True,
    **kwargs: Any,
) -> ToolParameter:
    """Create a number parameter."""
    return param(name, ParameterType.NUMBER, description, required, **kwargs)


def integer_param(
    name: str,
    description: str,
    required: bool = True,
    **kwargs: Any,
) -> ToolParameter:
    """Create an integer parameter."""
    return param(name, ParameterType.INTEGER, description, required, **kwargs)


def boolean_param(
    name: str,
    description: str,
    required: bool = True,
    **kwargs: Any,
) -> ToolParameter:
    """Create a boolean parameter."""
    return param(name, ParameterType.BOOLEAN, description, required, **kwargs)


def array_param(
    name: str,
    description: str,
    items: dict[str, Any],
    required: bool = True,
    **kwargs: Any,
) -> ToolParameter:
    """Create an array parameter."""
    return param(
        name,
        ParameterType.ARRAY,
        description,
        required,
        items=items,
        **kwargs,
    )


def object_param(
    name: str,
    description: str,
    properties: dict[str, Any],
    required: bool = True,
    **kwargs: Any,
) -> ToolParameter:
    """Create an object parameter."""
    return param(
        name,
        ParameterType.OBJECT,
        description,
        required,
        properties=properties,
        **kwargs,
    )


def enum_param(
    name: str,
    description: str,
    enum: list[str],
    required: bool = True,
    **kwargs: Any,
) -> ToolParameter:
    """Create a string enum parameter."""
    return param(
        name,
        ParameterType.STRING,
        description,
        required,
        enum=enum,
        **kwargs,
    )
