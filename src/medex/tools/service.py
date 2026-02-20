# =============================================================================
# MedeX - Tool Service (Facade)
# =============================================================================
"""
Tool Service - Unified interface for the Tool System.

This module provides a high-level facade that coordinates:
- Tool registry management
- Tool execution
- Result formatting for LLMs
- Metrics and monitoring

The ToolService is the primary interface for the rest of MedeX
to interact with the tool system.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from .executor import ToolExecutor, create_tool_executor
from .models import ToolCall, ToolCategory, ToolDefinition, ToolResult
from .registry import ToolRegistry, get_tool_registry

if TYPE_CHECKING:
    from redis.asyncio import Redis


logger = logging.getLogger(__name__)


class ToolService:
    """
    Unified service interface for tool management and execution.

    The ToolService coordinates between the registry (tool definitions)
    and the executor (tool invocation), providing a clean API for the
    rest of the application.

    Features:
    - Single point of access for all tool operations
    - Automatic tool registration on initialization
    - LLM-formatted tool lists for function calling
    - Execution with caching and retry
    - Metrics collection

    Example:
        service = ToolService()
        await service.initialize()

        # Get tools for LLM
        tools = service.get_tools_for_llm()

        # Execute a tool call
        result = await service.execute(tool_call)
    """

    def __init__(
        self,
        cache_client: Redis | None = None,
        max_concurrent: int = 5,
        default_timeout: float = 30.0,
    ) -> None:
        """
        Initialize the ToolService.

        Args:
            cache_client: Optional Redis client for caching
            max_concurrent: Maximum concurrent tool executions
            default_timeout: Default timeout for tool execution
        """
        self._registry: ToolRegistry = get_tool_registry()
        self._executor: ToolExecutor | None = None
        self._cache_client = cache_client
        self._max_concurrent = max_concurrent
        self._default_timeout = default_timeout
        self._initialized = False

        logger.info("ToolService created")

    async def initialize(self) -> None:
        """
        Initialize the service and register all tools.

        This method must be called before using the service.
        It ensures all medical tools are properly registered.
        """
        if self._initialized:
            return

        # Create executor
        self._executor = create_tool_executor(
            cache=self._cache_client,
            max_concurrent=self._max_concurrent,
            default_timeout=self._default_timeout,
        )

        # Import medical tools to trigger registration
        # (They register themselves via the @tool decorator)
        from . import medical  # noqa: F401

        self._initialized = True

        tool_count = len(self._registry.get_all())
        logger.info(f"ToolService initialized with {tool_count} tools")

    async def shutdown(self) -> None:
        """Shutdown the service and clean up resources."""
        if self._executor:
            await self._executor.shutdown()
        self._initialized = False
        logger.info("ToolService shutdown complete")

    @property
    def registry(self) -> ToolRegistry:
        """Get the tool registry."""
        return self._registry

    @property
    def executor(self) -> ToolExecutor:
        """Get the tool executor."""
        if not self._executor:
            raise RuntimeError("ToolService not initialized. Call initialize() first.")
        return self._executor

    # =========================================================================
    # Tool Discovery
    # =========================================================================

    def get_all_tools(self) -> list[ToolDefinition]:
        """Get all registered tools."""
        return self._registry.get_all_tools()

    def get_tool(self, name: str) -> ToolDefinition | None:
        """Get a specific tool by name."""
        return self._registry.get_tool(name)

    def get_tools_by_category(
        self,
        category: ToolCategory,
    ) -> list[ToolDefinition]:
        """Get all tools in a specific category."""
        return self._registry.get_tools_by_category(category)

    def get_medical_tools(self) -> list[ToolDefinition]:
        """Get all medical-related tools."""
        medical_categories = [
            ToolCategory.DRUG,
            ToolCategory.LAB,
            ToolCategory.DOSAGE,
            ToolCategory.EMERGENCY,
            ToolCategory.DIAGNOSIS,
        ]

        tools = []
        for category in medical_categories:
            tools.extend(self._registry.get_tools_by_category(category))

        return tools

    # =========================================================================
    # LLM Integration
    # =========================================================================

    def get_tools_for_llm(
        self,
        format: str = "openai",
        categories: list[ToolCategory] | None = None,
        enabled_only: bool = True,
    ) -> list[dict[str, Any]]:
        """
        Get tools formatted for LLM function calling.

        Args:
            format: Output format ("openai" or "anthropic")
            categories: Optional list of categories to filter
            enabled_only: Only include enabled tools

        Returns:
            List of tool definitions in the specified format
        """
        tools = self._registry.get_all_tools()

        # Filter by category if specified
        if categories:
            tools = [t for t in tools if t.category in categories]

        # Filter enabled only
        if enabled_only:
            from .models import ToolStatus

            tools = [t for t in tools if t.status == ToolStatus.ENABLED]

        # Convert to requested format
        if format == "openai":
            return [t.to_openai_format() for t in tools]
        elif format == "anthropic":
            return [t.to_anthropic_format() for t in tools]
        else:
            raise ValueError(f"Unsupported format: {format}")

    def get_tools_prompt(self) -> str:
        """
        Get a human-readable description of available tools.

        Useful for including in system prompts when not using
        native function calling.
        """
        tools = self.get_all_tools()
        if not tools:
            return "No tools available."

        lines = ["## Available Tools\n"]

        for tool in tools:
            lines.append(f"### {tool.name}")
            lines.append(f"**Description:** {tool.description}")
            lines.append(f"**Category:** {tool.category.value}")

            if tool.parameters:
                lines.append("**Parameters:**")
                for param in tool.parameters:
                    required = "required" if param.required else "optional"
                    lines.append(
                        f"  - `{param.name}` ({param.type.value}, {required}): {param.description}"
                    )

            lines.append("")

        return "\n".join(lines)

    # =========================================================================
    # Tool Execution
    # =========================================================================

    async def execute(
        self,
        tool_call: ToolCall,
        timeout: float | None = None,
    ) -> ToolResult:
        """
        Execute a tool call.

        Args:
            tool_call: The tool call to execute
            timeout: Optional timeout override

        Returns:
            ToolResult with the execution result
        """
        return await self.executor.execute(tool_call, timeout=timeout)

    async def execute_from_llm_response(
        self,
        tool_calls: list[dict[str, Any]],
        format: str = "openai",
    ) -> list[ToolResult]:
        """
        Execute tool calls from an LLM response.

        Args:
            tool_calls: Raw tool calls from LLM response
            format: The format of the tool calls ("openai" or "anthropic")

        Returns:
            List of ToolResults
        """
        results = []

        for call_data in tool_calls:
            # Parse the tool call
            if format == "openai":
                tool_call = ToolCall.from_openai_response(call_data)
            elif format == "anthropic":
                tool_call = ToolCall.from_anthropic_response(call_data)
            else:
                raise ValueError(f"Unsupported format: {format}")

            # Execute
            result = await self.execute(tool_call)
            results.append(result)

        return results

    async def execute_batch(
        self,
        tool_calls: list[ToolCall],
    ) -> list[ToolResult]:
        """
        Execute multiple tool calls concurrently.

        Args:
            tool_calls: List of tool calls to execute

        Returns:
            List of ToolResults in the same order as input
        """
        return await self.executor.execute_batch(tool_calls)

    # =========================================================================
    # Tool Management
    # =========================================================================

    def enable_tool(self, name: str) -> bool:
        """Enable a tool by name."""
        return self._registry.enable_tool(name)

    def disable_tool(self, name: str) -> bool:
        """Disable a tool by name."""
        return self._registry.disable_tool(name)

    def enable_category(self, category: ToolCategory) -> int:
        """Enable all tools in a category. Returns count of enabled tools."""
        tools = self._registry.get_tools_by_category(category)
        count = 0
        for tool in tools:
            if self._registry.enable_tool(tool.name):
                count += 1
        return count

    def disable_category(self, category: ToolCategory) -> int:
        """Disable all tools in a category. Returns count of disabled tools."""
        tools = self._registry.get_tools_by_category(category)
        count = 0
        for tool in tools:
            if self._registry.disable_tool(tool.name):
                count += 1
        return count

    # =========================================================================
    # Metrics
    # =========================================================================

    def get_metrics(self) -> dict[str, Any]:
        """Get execution metrics for all tools."""
        return self.executor.get_metrics()

    def get_tool_metrics(self, name: str) -> dict[str, Any] | None:
        """Get execution metrics for a specific tool."""
        metrics = self.executor.get_metrics()
        return metrics.get("by_tool", {}).get(name)


# =============================================================================
# Factory Function
# =============================================================================

_tool_service: ToolService | None = None


async def get_tool_service(
    cache_client: Redis | None = None,
) -> ToolService:
    """
    Get or create the global ToolService instance.

    Args:
        cache_client: Optional Redis client for caching

    Returns:
        Initialized ToolService instance
    """
    global _tool_service

    if _tool_service is None:
        _tool_service = ToolService(cache_client=cache_client)
        await _tool_service.initialize()

    return _tool_service


async def shutdown_tool_service() -> None:
    """Shutdown the global ToolService instance."""
    global _tool_service

    if _tool_service:
        await _tool_service.shutdown()
        _tool_service = None
