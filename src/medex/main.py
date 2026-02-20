# =============================================================================
# MedeX - Main Application Orchestrator
# =============================================================================
"""
Main application entry point and service orchestration.

This module provides:
- Service composition and dependency injection
- Application lifecycle management
- Graceful startup and shutdown
- Health monitoring
"""

from __future__ import annotations

import asyncio
import signal
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


# =============================================================================
# Application State
# =============================================================================


@dataclass
class ApplicationState:
    """Application runtime state."""

    started_at: datetime | None = None
    is_running: bool = False
    is_healthy: bool = False
    is_ready: bool = False

    # Service instances
    services: dict[str, Any] = field(default_factory=dict)

    # Metrics
    total_requests: int = 0
    total_errors: int = 0

    @property
    def uptime_seconds(self) -> float:
        """Get uptime in seconds."""
        if self.started_at is None:
            return 0.0
        return (datetime.now() - self.started_at).total_seconds()


# =============================================================================
# Service Container
# =============================================================================


class ServiceContainer:
    """
    Dependency injection container for MedeX services.

    Manages service lifecycle and dependencies.
    """

    def __init__(self) -> None:
        """Initialize service container."""
        self._services: dict[str, Any] = {}
        self._factories: dict[str, Any] = {}
        self._initialized: set[str] = set()

    def register(self, name: str, factory: Any) -> "ServiceContainer":
        """Register a service factory."""
        self._factories[name] = factory
        return self

    def get(self, name: str) -> Any:
        """Get a service instance."""
        if name not in self._services:
            if name in self._factories:
                self._services[name] = self._factories[name]()
            else:
                raise KeyError(f"Service not registered: {name}")
        return self._services[name]

    async def initialize(self, name: str) -> None:
        """Initialize a service if it has an init method."""
        if name in self._initialized:
            return

        service = self.get(name)
        if hasattr(service, "startup"):
            await service.startup()
        elif hasattr(service, "initialize"):
            await service.initialize()

        self._initialized.add(name)

    async def shutdown(self, name: str) -> None:
        """Shutdown a service if it has a shutdown method."""
        if name not in self._services:
            return

        service = self._services[name]
        if hasattr(service, "shutdown"):
            await service.shutdown()
        elif hasattr(service, "close"):
            await service.close()

        self._initialized.discard(name)

    async def shutdown_all(self) -> None:
        """Shutdown all services in reverse order."""
        for name in reversed(list(self._initialized)):
            try:
                await self.shutdown(name)
            except Exception as e:
                print(f"[MedeX] Error shutting down {name}: {e}")


# =============================================================================
# MedeX Application
# =============================================================================


class MedeXApplication:
    """
    Main MedeX application orchestrator.

    Manages the complete application lifecycle including:
    - Configuration loading
    - Service initialization
    - Request handling
    - Graceful shutdown

    Example:
        app = MedeXApplication()
        await app.startup()

        # Handle request
        response = await app.query("¿Qué es la diabetes?")

        await app.shutdown()
    """

    def __init__(self, config: Any | None = None) -> None:
        """Initialize MedeX application."""
        self._config = config
        self._state = ApplicationState()
        self._container = ServiceContainer()
        self._shutdown_event = asyncio.Event()

        # Register signal handlers
        self._setup_signal_handlers()

    @property
    def is_running(self) -> bool:
        """Check if application is running."""
        return self._state.is_running

    @property
    def is_ready(self) -> bool:
        """Check if application is ready to handle requests."""
        return self._state.is_ready

    @property
    def uptime(self) -> float:
        """Get application uptime in seconds."""
        return self._state.uptime_seconds

    def _setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown."""
        if sys.platform != "win32":
            loop = asyncio.get_event_loop()
            for sig in (signal.SIGTERM, signal.SIGINT):
                loop.add_signal_handler(
                    sig, lambda: asyncio.create_task(self._handle_signal())
                )

    async def _handle_signal(self) -> None:
        """Handle shutdown signal."""
        print("\n[MedeX] Received shutdown signal...")
        self._shutdown_event.set()

    async def startup(self) -> None:
        """
        Start the application.

        Initializes all services in the correct order:
        1. LLM providers
        2. Tools service
        3. Agent service
        """
        print(f"[MedeX] Starting MedeX v2.0.0...")
        print(f"[MedeX] Environment: development")

        start_time = time.time()
        self._state.started_at = datetime.now()
        self._state.is_running = True

        try:
            # Import real services
            from medex.llm.service import LLMService, LLMServiceConfig
            from medex.tools.service import ToolService
            from medex.agent.service import AgentService, AgentServiceConfig

            # Initialize LLM service
            print("[MedeX] Initializing LLM providers...")
            llm_config = LLMServiceConfig(
                default_language="es",
                default_user_mode="educational",
                stream_by_default=False,
                include_disclaimer=True,
                default_temperature=0.7,
                default_max_tokens=2048,
            )
            self._llm_service = LLMService(config=llm_config)
            self._container.register("llm", lambda: self._llm_service)
            print("[MedeX] ✓ LLM service initialized")

            # Initialize tools service
            print("[MedeX] Initializing tools service...")
            self._tool_service = ToolService()
            await self._tool_service.initialize()
            self._container.register("tools", lambda: self._tool_service)
            print("[MedeX] ✓ Tools service initialized")

            # Initialize agent service
            print("[MedeX] Initializing agent service...")
            agent_config = AgentServiceConfig(
                max_iterations=10,
                query_timeout_seconds=60.0,
                enable_tools=True,
                enable_rag=False,
                enable_memory=True,
            )
            self._agent_service = AgentService(
                config=agent_config,
                llm_service=self._llm_service,
                tool_service=self._tool_service,
            )
            await self._agent_service.initialize()
            self._container.register("agent", lambda: self._agent_service)
            print("[MedeX] ✓ Agent service initialized")

            self._state.is_healthy = True
            self._state.is_ready = True

            elapsed = time.time() - start_time
            print(f"[MedeX] ✓ Application started in {elapsed:.2f}s")
            print(f"[MedeX] Ready to accept requests")

        except Exception as e:
            print(f"[MedeX] ✗ Startup failed: {e}")
            import traceback

            traceback.print_exc()
            self._state.is_healthy = False
            raise

    async def shutdown(self) -> None:
        """
        Shutdown the application gracefully.

        1. Stop accepting new requests
        2. Wait for in-flight requests to complete
        3. Close connections
        4. Flush logs and metrics
        """
        print("[MedeX] Shutting down...")

        self._state.is_ready = False
        self._state.is_running = False

        # Shutdown all services
        await self._container.shutdown_all()

        print("[MedeX] Shutdown complete")

    async def run(self) -> None:
        """
        Run the application until shutdown signal.

        This is the main entry point for running MedeX as a server.
        """
        await self.startup()

        print("[MedeX] Press Ctrl+C to stop...")

        # Wait for shutdown signal
        await self._shutdown_event.wait()

        await self.shutdown()

    # -------------------------------------------------------------------------
    # Request Handling
    # -------------------------------------------------------------------------

    async def query(
        self,
        query: str,
        user_type: str = "educational",
        stream: bool = False,
        history: list[dict] | None = None,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        is_reasoning_model: bool = False,
    ) -> Any:
        """
        Process a medical query using the LLM service.

        Args:
            query: The medical question
            user_type: User type (educational, professional, research)
            stream: Whether to stream the response
            history: Conversation history for context
            model: HuggingFace model name to use (e.g., "Qwen/Qwen2.5-72B-Instruct")
            temperature: Model temperature (overrides default)
            max_tokens: Max tokens for response (overrides default)
            is_reasoning_model: Whether model uses <think> tags for reasoning

        Returns:
            Query response with content and metadata
        """
        if not self._state.is_ready:
            raise RuntimeError("Application not ready")

        self._state.total_requests += 1

        try:
            from medex.llm.prompts import Language, UserMode
            from medex.llm.models import Message, MessageRole

            # Map user type to UserMode
            mode_map = {
                "educational": UserMode.EDUCATIONAL,
                "professional": UserMode.PROFESSIONAL,
                "research": UserMode.PROFESSIONAL,
            }
            user_mode = mode_map.get(user_type, UserMode.EDUCATIONAL)

            # Convert history to Message objects if provided
            llm_history = None
            if history:
                llm_history = [
                    Message(
                        role=MessageRole.USER
                        if m.get("role") == "user"
                        else MessageRole.ASSISTANT,
                        content=m.get("content", ""),
                    )
                    for m in history[-20:]  # Keep last 20 messages for context window
                ]

            # Use LLM service to get response with history and model
            response = await self._llm_service.query(
                query=query,
                user_mode=user_mode,
                language=Language.SPANISH,
                history=llm_history,
                stream=False,
                model=model,  # Pass the model override
                temperature=temperature,  # Pass model-specific temperature
                max_tokens=max_tokens,  # Pass model-specific max_tokens
            )

            # Parse reasoning content if this is a reasoning model
            content = response.content
            thinking_content = None

            if is_reasoning_model and content:
                # Extract <think>...</think> content
                import re

                think_pattern = r"<think>(.*?)</think>"
                think_match = re.search(think_pattern, content, re.DOTALL)

                if think_match:
                    thinking_content = think_match.group(1).strip()
                    # Remove the <think>...</think> block from content
                    content = re.sub(
                        think_pattern, "", content, flags=re.DOTALL
                    ).strip()

            # Fix Markdown headers without space after # (common issue with Kimi K2)
            # Pattern: #Text -> # Text (for all header levels 1-6)
            import re

            content = re.sub(
                r"^(#{1,6})([^\s#])", r"\1 \2", content, flags=re.MULTILINE
            )

            return {
                "query_id": f"medex-{self._state.total_requests}",
                "response": content,
                "thinking_content": thinking_content,  # Separate reasoning content
                "user_type": user_type,
                "provider": response.provider.value if response.provider else "unknown",
                "model": response.model,
                "tokens": {
                    "prompt": response.usage.prompt_tokens if response.usage else 0,
                    "completion": response.usage.completion_tokens
                    if response.usage
                    else 0,
                    "total": response.usage.total_tokens if response.usage else 0,
                },
                "latency_ms": response.latency_ms,
                "sources": [],
            }
        except Exception as e:
            self._state.total_errors += 1
            import traceback

            traceback.print_exc()
            raise

    async def query_stream(
        self,
        query: str,
        user_type: str = "educational",
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ):
        """
        Stream a medical query response as SSE events.

        Args:
            query: The medical question
            user_type: User type (educational, professional, research)
            model: HuggingFace model name to use (e.g., "Qwen/Qwen2.5-72B-Instruct")
            temperature: Model temperature (overrides default)
            max_tokens: Max tokens for response (overrides default)

        Yields:
            SSE-formatted strings for direct HTTP streaming
        """
        if not self._state.is_ready:
            raise RuntimeError("Application not ready")

        self._state.total_requests += 1

        try:
            from medex.llm.prompts import Language, UserMode

            mode_map = {
                "educational": UserMode.EDUCATIONAL,
                "professional": UserMode.PROFESSIONAL,
                "research": UserMode.PROFESSIONAL,
            }
            user_mode = mode_map.get(user_type, UserMode.EDUCATIONAL)

            async for sse_event in self._llm_service.query_stream_sse(
                query=query,
                user_mode=user_mode,
                language=Language.SPANISH,
                model=model,  # Pass model override
                temperature=temperature,  # Pass model-specific temperature
                max_tokens=max_tokens,  # Pass model-specific max_tokens
            ):
                yield sse_event
        except Exception as e:
            self._state.total_errors += 1
            import json

            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    async def search(self, query: str, limit: int = 10) -> Any:
        """
        Search the medical knowledge base.

        Args:
            query: Search query
            limit: Maximum results

        Returns:
            Search results
        """
        if not self._state.is_ready:
            raise RuntimeError("Application not ready")

        # Would use actual RAG service
        # rag = self._container.get("rag")
        # results = await rag.search(query, limit)

        return {
            "query": query,
            "results": [],
            "total": 0,
        }

    async def health(self) -> dict[str, Any]:
        """Get application health status."""
        return {
            "status": "healthy" if self._state.is_healthy else "unhealthy",
            "ready": self._state.is_ready,
            "uptime_seconds": self._state.uptime_seconds,
            "total_requests": self._state.total_requests,
            "total_errors": self._state.total_errors,
        }

    def get_stats(self) -> dict[str, Any]:
        """Get application statistics."""
        return {
            "running": self._state.is_running,
            "ready": self._state.is_ready,
            "healthy": self._state.is_healthy,
            "uptime_seconds": self._state.uptime_seconds,
            "total_requests": self._state.total_requests,
            "total_errors": self._state.total_errors,
            "error_rate": (
                self._state.total_errors / max(1, self._state.total_requests)
            ),
        }


# =============================================================================
# CLI Interface
# =============================================================================


def print_banner() -> None:
    """Print MedeX banner."""
    banner = """
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║   ███╗   ███╗███████╗██████╗ ███████╗██╗  ██╗                ║
    ║   ████╗ ████║██╔════╝██╔══██╗██╔════╝╚██╗██╔╝                ║
    ║   ██╔████╔██║█████╗  ██║  ██║█████╗   ╚███╔╝                 ║
    ║   ██║╚██╔╝██║██╔══╝  ██║  ██║██╔══╝   ██╔██╗                 ║
    ║   ██║ ╚═╝ ██║███████╗██████╔╝███████╗██╔╝ ██╗                ║
    ║   ╚═╝     ╚═╝╚══════╝╚═════╝ ╚══════╝╚═╝  ╚═╝                ║
    ║                                                               ║
    ║   Asistente Médico Educativo con IA v2.0.0                   ║
    ║   $0 Cost Implementation - Free LLM Providers                 ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝
    """
    print(banner)


async def main() -> None:
    """Main entry point."""
    print_banner()

    app = MedeXApplication()
    await app.run()


# =============================================================================
# Factory Functions
# =============================================================================


def create_application(config: Any | None = None) -> MedeXApplication:
    """Create MedeX application instance."""
    return MedeXApplication(config=config)


def run_server() -> None:
    """Run MedeX server (synchronous wrapper)."""
    asyncio.run(main())


if __name__ == "__main__":
    run_server()
