# =============================================================================
# MedeX - Tool Executor
# =============================================================================
"""
Async tool execution engine for MedeX V2.

This module provides:
- ToolExecutor: Execute tools with validation and error handling
- Timeout management
- Retry logic
- Result caching
- Execution metrics

Design:
- Fully async execution
- Graceful error handling
- Structured logging
- Integration with cache layer
"""

from __future__ import annotations

import asyncio
import logging
import time
import traceback
from typing import TYPE_CHECKING, Any

from .models import (
    ToolCall,
    ToolError,
    ToolResult,
    ToolStatus,
)
from .registry import ToolRegistry, get_tool_registry

if TYPE_CHECKING:
    from ..db.cache import ToolResultCache

logger = logging.getLogger(__name__)


# =============================================================================
# Tool Executor
# =============================================================================


class ToolExecutor:
    """
    Execute tools with full lifecycle management.

    Handles:
    - Argument validation
    - Timeout enforcement
    - Retry logic
    - Error handling
    - Result caching
    - Metrics collection
    """

    def __init__(
        self,
        registry: ToolRegistry | None = None,
        cache: ToolResultCache | None = None,
        default_timeout: float = 30.0,
        max_concurrent: int = 5,
    ):
        """
        Initialize executor.

        Args:
            registry: Tool registry (uses global if None)
            cache: Optional result cache
            default_timeout: Default timeout in seconds
            max_concurrent: Max concurrent executions
        """
        self._registry = registry or get_tool_registry()
        self._cache = cache
        self._default_timeout = default_timeout
        self._semaphore = asyncio.Semaphore(max_concurrent)

        # Metrics
        self._execution_count = 0
        self._success_count = 0
        self._error_count = 0
        self._total_time_ms = 0.0

    # -------------------------------------------------------------------------
    # Execution Methods
    # -------------------------------------------------------------------------

    async def execute(
        self,
        call: ToolCall,
        context: dict[str, Any] | None = None,
    ) -> ToolResult:
        """
        Execute a tool call.

        Args:
            call: ToolCall to execute
            context: Optional execution context

        Returns:
            ToolResult with output or error
        """
        self._execution_count += 1
        start_time = time.perf_counter()

        # Create initial result
        result = ToolResult(
            call_id=call.id,
            tool_name=call.tool_name,
            status=ToolStatus.PENDING,
            started_at=call.created_at,
        )

        try:
            # Get tool definition
            tool_def = self._registry.get(call.tool_name)
            if tool_def is None:
                return self._handle_error(
                    call,
                    ToolError.NOT_FOUND,
                    f"Tool not found: {call.tool_name}",
                    start_time,
                )

            if not tool_def.enabled:
                return self._handle_error(
                    call,
                    ToolError.PERMISSION_DENIED,
                    f"Tool is disabled: {call.tool_name}",
                    start_time,
                )

            # Validate arguments
            validation_errors = tool_def.validate_arguments(call.arguments)
            if validation_errors:
                return self._handle_error(
                    call,
                    ToolError.VALIDATION_ERROR,
                    "; ".join(validation_errors),
                    start_time,
                )

            # Check cache
            if self._cache and tool_def.cache_ttl:
                cached = await self._get_cached(call)
                if cached:
                    cached.metadata["cached"] = True
                    return cached

            # Execute with concurrency control
            async with self._semaphore:
                result = await self._execute_with_retry(
                    call, tool_def, context, start_time
                )

            # Cache successful result
            if result.is_success and self._cache and tool_def.cache_ttl:
                await self._cache_result(call, result, tool_def.cache_ttl)

            return result

        except Exception as e:
            logger.exception(f"Unexpected error executing {call.tool_name}")
            return self._handle_error(
                call,
                ToolError.INTERNAL_ERROR,
                str(e),
                start_time,
                exception=e,
            )

    async def execute_batch(
        self,
        calls: list[ToolCall],
        context: dict[str, Any] | None = None,
        parallel: bool = True,
    ) -> list[ToolResult]:
        """
        Execute multiple tool calls.

        Args:
            calls: List of ToolCall to execute
            context: Optional shared context
            parallel: If True, execute in parallel

        Returns:
            List of ToolResult in same order as calls
        """
        if not calls:
            return []

        if parallel:
            tasks = [self.execute(call, context) for call in calls]
            return await asyncio.gather(*tasks)
        else:
            results = []
            for call in calls:
                result = await self.execute(call, context)
                results.append(result)
            return results

    async def _execute_with_retry(
        self,
        call: ToolCall,
        tool_def: Any,
        context: dict[str, Any] | None,
        start_time: float,
    ) -> ToolResult:
        """Execute tool with retry logic."""
        last_error = None
        attempts = tool_def.max_retries + 1

        for attempt in range(attempts):
            try:
                result = await self._execute_once(call, tool_def, context, start_time)
                if result.is_success:
                    return result
                last_error = result.error
            except Exception as e:
                last_error = str(e)
                if attempt < attempts - 1:
                    # Exponential backoff
                    await asyncio.sleep(0.1 * (2**attempt))

        return self._handle_error(
            call,
            ToolError.INTERNAL_ERROR,
            f"Failed after {attempts} attempts: {last_error}",
            start_time,
        )

    async def _execute_once(
        self,
        call: ToolCall,
        tool_def: Any,
        context: dict[str, Any] | None,
        start_time: float,
    ) -> ToolResult:
        """Execute tool once with timeout."""
        timeout = tool_def.timeout_seconds or self._default_timeout

        try:
            # Call handler with timeout
            output = await asyncio.wait_for(
                tool_def.handler(**call.arguments),
                timeout=timeout,
            )

            elapsed = (time.perf_counter() - start_time) * 1000

            self._success_count += 1
            self._total_time_ms += elapsed

            return ToolResult(
                call_id=call.id,
                tool_name=call.tool_name,
                status=ToolStatus.SUCCESS,
                output=output,
                started_at=call.created_at,
                execution_time_ms=elapsed,
                metadata={"context": context} if context else {},
            )

        except asyncio.TimeoutError:
            return self._handle_error(
                call,
                ToolError.TIMEOUT,
                f"Execution timed out after {timeout}s",
                start_time,
            )

    # -------------------------------------------------------------------------
    # Error Handling
    # -------------------------------------------------------------------------

    def _handle_error(
        self,
        call: ToolCall,
        error_code: str,
        message: str,
        start_time: float,
        exception: Exception | None = None,
    ) -> ToolResult:
        """Create error result."""
        elapsed = (time.perf_counter() - start_time) * 1000
        self._error_count += 1
        self._total_time_ms += elapsed

        logger.warning(
            f"Tool execution error: {call.tool_name} - {error_code}: {message}"
        )

        metadata: dict[str, Any] = {}
        if exception:
            metadata["exception_type"] = type(exception).__name__
            metadata["stack_trace"] = traceback.format_exc()

        return ToolResult(
            call_id=call.id,
            tool_name=call.tool_name,
            status=ToolStatus.ERROR,
            error=message,
            error_code=error_code,
            started_at=call.created_at,
            execution_time_ms=elapsed,
            metadata=metadata,
        )

    # -------------------------------------------------------------------------
    # Caching
    # -------------------------------------------------------------------------

    async def _get_cached(self, call: ToolCall) -> ToolResult | None:
        """Get cached result if available."""
        if not self._cache:
            return None

        try:
            cache_key = self._make_cache_key(call)
            cached = await self._cache.get(cache_key)
            if cached:
                logger.debug(f"Cache hit for {call.tool_name}")
                return ToolResult(
                    call_id=call.id,
                    tool_name=call.tool_name,
                    status=ToolStatus.SUCCESS,
                    output=cached.get("output"),
                    execution_time_ms=0.0,
                    metadata={"cached": True},
                )
        except Exception as e:
            logger.warning(f"Cache get error: {e}")

        return None

    async def _cache_result(
        self,
        call: ToolCall,
        result: ToolResult,
        ttl: int,
    ) -> None:
        """Cache successful result."""
        if not self._cache:
            return

        try:
            cache_key = self._make_cache_key(call)
            await self._cache.set(
                key=cache_key,
                value={"output": result.output},
                ttl=ttl,
            )
            logger.debug(f"Cached result for {call.tool_name}")
        except Exception as e:
            logger.warning(f"Cache set error: {e}")

    def _make_cache_key(self, call: ToolCall) -> str:
        """Create cache key from tool call."""
        import hashlib
        import json

        args_str = json.dumps(call.arguments, sort_keys=True)
        hash_val = hashlib.md5(args_str.encode()).hexdigest()[:16]
        return f"tool:{call.tool_name}:{hash_val}"

    # -------------------------------------------------------------------------
    # Metrics
    # -------------------------------------------------------------------------

    def get_metrics(self) -> dict[str, Any]:
        """Get execution metrics."""
        return {
            "total_executions": self._execution_count,
            "successful": self._success_count,
            "errors": self._error_count,
            "success_rate": (
                self._success_count / self._execution_count
                if self._execution_count > 0
                else 0.0
            ),
            "avg_execution_time_ms": (
                self._total_time_ms / self._execution_count
                if self._execution_count > 0
                else 0.0
            ),
        }

    def reset_metrics(self) -> None:
        """Reset execution metrics."""
        self._execution_count = 0
        self._success_count = 0
        self._error_count = 0
        self._total_time_ms = 0.0


# =============================================================================
# Factory Function
# =============================================================================


def create_tool_executor(
    registry: ToolRegistry | None = None,
    cache: ToolResultCache | None = None,
    default_timeout: float = 30.0,
    max_concurrent: int = 5,
) -> ToolExecutor:
    """
    Create configured tool executor.

    Args:
        registry: Tool registry
        cache: Result cache
        default_timeout: Default timeout
        max_concurrent: Max concurrent executions

    Returns:
        Configured ToolExecutor
    """
    return ToolExecutor(
        registry=registry,
        cache=cache,
        default_timeout=default_timeout,
        max_concurrent=max_concurrent,
    )
