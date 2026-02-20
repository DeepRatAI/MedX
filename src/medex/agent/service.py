# =============================================================================
# MedeX - Agent Service
# =============================================================================
"""
High-level service façade for the MedeX agent.

Provides a clean API for:
- Single query processing
- Streaming responses
- Batch processing
- Session management
- Health monitoring
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from medex.agent.controller import (
    AgentControllerConfig,
    create_agent_controller,
)
from medex.agent.models import (
    AgentEvent,
    AgentResult,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Configuration
# =============================================================================


@dataclass
class AgentServiceConfig:
    """Configuration for agent service."""

    # Controller settings
    max_iterations: int = 10
    max_phase_duration_ms: float = 30_000
    max_total_duration_ms: float = 120_000

    # Features
    enable_streaming: bool = True
    enable_memory: bool = True
    enable_tools: bool = True
    enable_rag: bool = True

    # Concurrency
    max_concurrent_queries: int = 10

    # Timeouts
    query_timeout_seconds: float = 60.0

    # Metrics
    enable_metrics: bool = True


# =============================================================================
# Service Metrics
# =============================================================================


@dataclass
class ServiceMetrics:
    """Metrics for the agent service."""

    queries_total: int = 0
    queries_success: int = 0
    queries_failed: int = 0
    queries_timeout: int = 0

    avg_latency_ms: float = 0.0
    min_latency_ms: float = float("inf")
    max_latency_ms: float = 0.0

    active_queries: int = 0
    peak_concurrent: int = 0

    started_at: datetime = field(default_factory=datetime.utcnow)

    def record_query(self, success: bool, latency_ms: float) -> None:
        """Record query result."""
        self.queries_total += 1

        if success:
            self.queries_success += 1
        else:
            self.queries_failed += 1

        # Update latency stats
        self.min_latency_ms = min(self.min_latency_ms, latency_ms)
        self.max_latency_ms = max(self.max_latency_ms, latency_ms)

        # Running average
        total_latency = self.avg_latency_ms * (self.queries_total - 1)
        self.avg_latency_ms = (total_latency + latency_ms) / self.queries_total

    def record_timeout(self) -> None:
        """Record timeout."""
        self.queries_timeout += 1
        self.queries_failed += 1
        self.queries_total += 1

    def start_query(self) -> None:
        """Track query start."""
        self.active_queries += 1
        self.peak_concurrent = max(self.peak_concurrent, self.active_queries)

    def end_query(self) -> None:
        """Track query end."""
        self.active_queries = max(0, self.active_queries - 1)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "queries_total": self.queries_total,
            "queries_success": self.queries_success,
            "queries_failed": self.queries_failed,
            "queries_timeout": self.queries_timeout,
            "success_rate": (
                self.queries_success / self.queries_total
                if self.queries_total > 0
                else 0.0
            ),
            "avg_latency_ms": self.avg_latency_ms,
            "min_latency_ms": (
                self.min_latency_ms if self.min_latency_ms != float("inf") else 0
            ),
            "max_latency_ms": self.max_latency_ms,
            "active_queries": self.active_queries,
            "peak_concurrent": self.peak_concurrent,
            "uptime_seconds": (datetime.utcnow() - self.started_at).total_seconds(),
        }


# =============================================================================
# Agent Service
# =============================================================================


class AgentService:
    """High-level service façade for the agent."""

    def __init__(
        self,
        config: AgentServiceConfig | None = None,
        llm_service: Any = None,
        tool_service: Any = None,
        rag_service: Any = None,
        memory_service: Any = None,
    ) -> None:
        """Initialize agent service."""
        self.config = config or AgentServiceConfig()

        # Create controller config
        controller_config = AgentControllerConfig(
            max_iterations=self.config.max_iterations,
            max_phase_duration_ms=self.config.max_phase_duration_ms,
            max_total_duration_ms=self.config.max_total_duration_ms,
            enable_streaming=self.config.enable_streaming,
        )

        # Create controller
        self.controller = create_agent_controller(
            config=controller_config,
            llm_service=llm_service,
            tool_service=tool_service,
            rag_service=rag_service,
            memory_service=memory_service,
        )

        # Services (stored for late binding)
        self.llm_service = llm_service
        self.tool_service = tool_service
        self.rag_service = rag_service
        self.memory_service = memory_service

        # Metrics
        self._metrics = ServiceMetrics()

        # Concurrency control
        self._semaphore = asyncio.Semaphore(self.config.max_concurrent_queries)

        # Initialized flag
        self._initialized = False

    # =========================================================================
    # Initialization
    # =========================================================================

    async def initialize(self) -> None:
        """Initialize the service and its dependencies."""
        if self._initialized:
            return

        logger.info("Initializing agent service...")

        # Initialize dependent services if they have init methods
        if self.llm_service and hasattr(self.llm_service, "initialize"):
            await self.llm_service.initialize()

        if self.rag_service and hasattr(self.rag_service, "initialize"):
            await self.rag_service.initialize()

        if self.tool_service and hasattr(self.tool_service, "initialize"):
            await self.tool_service.initialize()

        if self.memory_service and hasattr(self.memory_service, "initialize"):
            await self.memory_service.initialize()

        self._initialized = True
        logger.info("Agent service initialized")

    async def shutdown(self) -> None:
        """Shutdown the service gracefully."""
        logger.info("Shutting down agent service...")

        # Wait for active queries
        if self._metrics.active_queries > 0:
            logger.info(f"Waiting for {self._metrics.active_queries} active queries...")
            for _ in range(10):  # Wait up to 10 seconds
                if self._metrics.active_queries == 0:
                    break
                await asyncio.sleep(1)

        # Shutdown dependent services
        if self.memory_service and hasattr(self.memory_service, "shutdown"):
            await self.memory_service.shutdown()

        self._initialized = False
        logger.info("Agent service shutdown complete")

    # =========================================================================
    # Service Setters (Late Binding)
    # =========================================================================

    def set_llm_service(self, service: Any) -> None:
        """Set LLM service."""
        self.llm_service = service
        self.controller.set_llm_service(service)

    def set_tool_service(self, service: Any) -> None:
        """Set tool service."""
        self.tool_service = service
        self.controller.set_tool_service(service)

    def set_rag_service(self, service: Any) -> None:
        """Set RAG service."""
        self.rag_service = service
        self.controller.set_rag_service(service)

    def set_memory_service(self, service: Any) -> None:
        """Set memory service."""
        self.memory_service = service
        self.controller.set_memory_service(service)

    # =========================================================================
    # Query Processing
    # =========================================================================

    async def query(
        self,
        query: str,
        session_id: str | None = None,
        user_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AgentResult:
        """
        Process a query and return the result.

        Args:
            query: User query text
            session_id: Optional session ID for conversation context
            user_id: Optional user ID
            metadata: Optional metadata

        Returns:
            AgentResult with response and metadata
        """
        async with self._semaphore:
            self._metrics.start_query()

            try:
                result = await asyncio.wait_for(
                    self.controller.process(
                        query=query,
                        session_id=session_id,
                        user_id=user_id,
                        metadata=metadata,
                    ),
                    timeout=self.config.query_timeout_seconds,
                )

                self._metrics.record_query(
                    success=result.success,
                    latency_ms=result.latency_ms,
                )

                return result

            except asyncio.TimeoutError:
                logger.error(f"Query timed out: {query[:50]}...")
                self._metrics.record_timeout()

                return AgentResult(
                    content="I apologize, but your request took too long to process. Please try again.",
                    success=False,
                    error="Query timeout",
                    latency_ms=self.config.query_timeout_seconds * 1000,
                )

            except Exception as e:
                logger.error(f"Query failed: {e}")
                self._metrics.record_query(success=False, latency_ms=0)

                return AgentResult(
                    content=f"An error occurred: {str(e)}",
                    success=False,
                    error=str(e),
                )

            finally:
                self._metrics.end_query()

    async def query_stream(
        self,
        query: str,
        session_id: str | None = None,
        user_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AsyncIterator[AgentEvent]:
        """
        Process a query with streaming events.

        Args:
            query: User query text
            session_id: Optional session ID
            user_id: Optional user ID
            metadata: Optional metadata

        Yields:
            AgentEvent objects for real-time updates
        """
        async with self._semaphore:
            self._metrics.start_query()
            start_time = datetime.utcnow()

            try:
                async for event in self.controller.process_stream(
                    query=query,
                    session_id=session_id,
                    user_id=user_id,
                    metadata=metadata,
                ):
                    yield event

                    # Check for completion
                    if event.event_type == "completed":
                        elapsed = (
                            datetime.utcnow() - start_time
                        ).total_seconds() * 1000
                        self._metrics.record_query(success=True, latency_ms=elapsed)

                    elif event.event_type == "error":
                        elapsed = (
                            datetime.utcnow() - start_time
                        ).total_seconds() * 1000
                        self._metrics.record_query(success=False, latency_ms=elapsed)

            except Exception as e:
                logger.error(f"Stream failed: {e}")
                self._metrics.record_query(success=False, latency_ms=0)
                raise

            finally:
                self._metrics.end_query()

    # =========================================================================
    # Batch Processing
    # =========================================================================

    async def batch_query(
        self,
        queries: list[dict[str, Any]],
        max_concurrent: int | None = None,
    ) -> list[AgentResult]:
        """
        Process multiple queries in batch.

        Args:
            queries: List of query dicts with 'query', 'session_id', etc.
            max_concurrent: Override max concurrent limit

        Returns:
            List of AgentResult objects
        """
        concurrent = max_concurrent or self.config.max_concurrent_queries
        semaphore = asyncio.Semaphore(concurrent)

        async def process_one(q: dict[str, Any]) -> AgentResult:
            async with semaphore:
                return await self.query(
                    query=q.get("query", ""),
                    session_id=q.get("session_id"),
                    user_id=q.get("user_id"),
                    metadata=q.get("metadata"),
                )

        tasks = [process_one(q) for q in queries]
        return await asyncio.gather(*tasks)

    # =========================================================================
    # Session Management
    # =========================================================================

    async def create_session(self, user_id: str | None = None) -> str:
        """Create a new session."""
        if self.memory_service and hasattr(self.memory_service, "create_session"):
            return await self.memory_service.create_session(user_id)

        # Fallback: generate UUID
        import uuid

        return str(uuid.uuid4())

    async def clear_session(self, session_id: str) -> bool:
        """Clear session history."""
        if self.memory_service and hasattr(self.memory_service, "clear_session"):
            return await self.memory_service.clear_session(session_id)
        return True

    async def get_session_history(
        self,
        session_id: str,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """Get session conversation history."""
        if self.memory_service and hasattr(self.memory_service, "get_history"):
            return await self.memory_service.get_history(session_id, limit=limit)
        return []

    # =========================================================================
    # Health & Metrics
    # =========================================================================

    def get_metrics(self) -> dict[str, Any]:
        """Get service metrics."""
        return self._metrics.to_dict()

    async def health_check(self) -> dict[str, Any]:
        """Check service health."""
        health = {
            "status": "healthy",
            "initialized": self._initialized,
            "active_queries": self._metrics.active_queries,
            "services": {},
        }

        # Check dependent services
        if self.llm_service:
            try:
                if hasattr(self.llm_service, "health_check"):
                    health["services"]["llm"] = await self.llm_service.health_check()
                else:
                    health["services"]["llm"] = {"status": "configured"}
            except Exception as e:
                health["services"]["llm"] = {"status": "error", "error": str(e)}
                health["status"] = "degraded"

        if self.rag_service:
            try:
                if hasattr(self.rag_service, "health_check"):
                    health["services"]["rag"] = await self.rag_service.health_check()
                else:
                    health["services"]["rag"] = {"status": "configured"}
            except Exception as e:
                health["services"]["rag"] = {"status": "error", "error": str(e)}
                health["status"] = "degraded"

        if self.tool_service:
            try:
                if hasattr(self.tool_service, "health_check"):
                    health["services"]["tools"] = await self.tool_service.health_check()
                else:
                    health["services"]["tools"] = {"status": "configured"}
            except Exception as e:
                health["services"]["tools"] = {"status": "error", "error": str(e)}
                health["status"] = "degraded"

        return health

    @property
    def is_ready(self) -> bool:
        """Check if service is ready to accept queries."""
        return (
            self._initialized
            and self._metrics.active_queries < self.config.max_concurrent_queries
        )


# =============================================================================
# Factory Functions
# =============================================================================


def create_agent_service(
    config: AgentServiceConfig | None = None,
    llm_service: Any = None,
    tool_service: Any = None,
    rag_service: Any = None,
    memory_service: Any = None,
) -> AgentService:
    """Create agent service with configuration."""
    return AgentService(
        config=config,
        llm_service=llm_service,
        tool_service=tool_service,
        rag_service=rag_service,
        memory_service=memory_service,
    )


async def get_agent_service() -> AgentService:
    """
    Get or create singleton agent service instance.

    For use in dependency injection (e.g., FastAPI).
    """
    global _agent_service

    if "_agent_service" not in globals() or _agent_service is None:
        _agent_service = create_agent_service()
        await _agent_service.initialize()

    return _agent_service


_agent_service: AgentService | None = None
