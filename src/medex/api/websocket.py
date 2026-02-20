# =============================================================================
# MedeX - WebSocket Handler
# =============================================================================
"""
WebSocket handler for streaming medical queries.

Features:
- Real-time streaming responses
- Connection management
- Heartbeat/ping-pong
- Graceful disconnection
"""

from __future__ import annotations

import asyncio
import json
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


# =============================================================================
# WebSocket Message Types
# =============================================================================


class WSMessageType(str, Enum):
    """WebSocket message types."""

    # Client -> Server
    QUERY = "query"
    CANCEL = "cancel"
    PING = "ping"

    # Server -> Client
    THINKING = "thinking"
    STREAMING = "streaming"
    TOOL_CALL = "tool_call"
    RAG_SEARCH = "rag_search"
    COMPLETE = "complete"
    ERROR = "error"
    PONG = "pong"


class WSCloseCode(int, Enum):
    """WebSocket close codes."""

    NORMAL = 1000
    GOING_AWAY = 1001
    PROTOCOL_ERROR = 1002
    INVALID_DATA = 1003
    POLICY_VIOLATION = 1008
    MESSAGE_TOO_BIG = 1009
    INTERNAL_ERROR = 1011


# =============================================================================
# WebSocket Messages
# =============================================================================


@dataclass
class WSMessage:
    """WebSocket message."""

    type: WSMessageType
    data: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(
            {
                "type": self.type.value,
                "data": self.data,
                "timestamp": self.timestamp.isoformat(),
            }
        )

    @classmethod
    def from_json(cls, json_str: str) -> "WSMessage":
        """Parse from JSON string."""
        data = json.loads(json_str)
        return cls(
            type=WSMessageType(data.get("type", "query")),
            data=data.get("data", {}),
        )

    # Factory methods
    @classmethod
    def thinking(cls, message: str = "Analizando consulta...") -> "WSMessage":
        """Create thinking message."""
        return cls(type=WSMessageType.THINKING, data={"message": message})

    @classmethod
    def streaming(cls, chunk: str, token_count: int = 0) -> "WSMessage":
        """Create streaming chunk message."""
        return cls(
            type=WSMessageType.STREAMING,
            data={
                "chunk": chunk,
                "token_count": token_count,
            },
        )

    @classmethod
    def tool_call(
        cls,
        tool_name: str,
        status: str = "executing",
        result: Any | None = None,
    ) -> "WSMessage":
        """Create tool call message."""
        return cls(
            type=WSMessageType.TOOL_CALL,
            data={
                "tool": tool_name,
                "status": status,
                "result": result,
            },
        )

    @classmethod
    def rag_search(cls, query: str, results_count: int = 0) -> "WSMessage":
        """Create RAG search message."""
        return cls(
            type=WSMessageType.RAG_SEARCH,
            data={
                "query": query,
                "results_count": results_count,
            },
        )

    @classmethod
    def complete(
        cls,
        query_id: str,
        response: str,
        sources: list[dict] | None = None,
        tokens_used: int = 0,
    ) -> "WSMessage":
        """Create completion message."""
        return cls(
            type=WSMessageType.COMPLETE,
            data={
                "query_id": query_id,
                "response": response,
                "sources": sources or [],
                "tokens_used": tokens_used,
            },
        )

    @classmethod
    def error(cls, code: str, message: str, details: dict | None = None) -> "WSMessage":
        """Create error message."""
        return cls(
            type=WSMessageType.ERROR,
            data={
                "code": code,
                "message": message,
                "details": details or {},
            },
        )


# =============================================================================
# Connection State
# =============================================================================


@dataclass
class ConnectionState:
    """State for a WebSocket connection."""

    connection_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str | None = None
    user_id: str | None = None
    connected_at: datetime = field(default_factory=datetime.now)
    last_ping: datetime = field(default_factory=datetime.now)

    # Current operation
    current_query_id: str | None = None
    is_processing: bool = False
    cancel_requested: bool = False

    # Metrics
    messages_received: int = 0
    messages_sent: int = 0
    queries_processed: int = 0

    def uptime_seconds(self) -> float:
        """Get connection uptime in seconds."""
        return (datetime.now() - self.connected_at).total_seconds()


# =============================================================================
# WebSocket Handler
# =============================================================================


class WebSocketHandler:
    """Handler for WebSocket connections."""

    def __init__(
        self,
        ping_interval: float = 30.0,
        ping_timeout: float = 10.0,
        max_message_size: int = 64 * 1024,  # 64KB
    ) -> None:
        """Initialize WebSocket handler."""
        self.ping_interval = ping_interval
        self.ping_timeout = ping_timeout
        self.max_message_size = max_message_size

        # Active connections
        self._connections: dict[str, ConnectionState] = {}

        # Services would be injected
        self._agent_service = None
        self._security_service = None

    @property
    def active_connections(self) -> int:
        """Get number of active connections."""
        return len(self._connections)

    async def on_connect(
        self, connection_id: str, session_id: str | None = None
    ) -> ConnectionState:
        """
        Handle new WebSocket connection.

        Args:
            connection_id: Unique connection identifier
            session_id: Optional session ID for conversation continuity

        Returns:
            ConnectionState for the new connection
        """
        state = ConnectionState(
            connection_id=connection_id,
            session_id=session_id,
        )
        self._connections[connection_id] = state
        return state

    async def on_disconnect(self, connection_id: str) -> None:
        """
        Handle WebSocket disconnection.

        Cleans up connection state and cancels any pending operations.
        """
        state = self._connections.pop(connection_id, None)
        if state and state.is_processing:
            state.cancel_requested = True

    async def on_message(
        self,
        connection_id: str,
        raw_message: str,
    ) -> list[WSMessage]:
        """
        Handle incoming WebSocket message.

        Args:
            connection_id: Connection identifier
            raw_message: Raw message string

        Returns:
            List of response messages to send
        """
        state = self._connections.get(connection_id)
        if not state:
            return [WSMessage.error("not_connected", "Connection not found")]

        state.messages_received += 1

        # Check message size
        if len(raw_message) > self.max_message_size:
            return [
                WSMessage.error("message_too_large", "Message exceeds maximum size")
            ]

        # Parse message
        try:
            message = WSMessage.from_json(raw_message)
        except json.JSONDecodeError:
            return [WSMessage.error("invalid_json", "Invalid JSON message")]

        # Handle message by type
        if message.type == WSMessageType.PING:
            state.last_ping = datetime.now()
            return [WSMessage(type=WSMessageType.PONG)]

        elif message.type == WSMessageType.CANCEL:
            return await self._handle_cancel(state)

        elif message.type == WSMessageType.QUERY:
            return await self._handle_query(state, message)

        else:
            return [
                WSMessage.error("unknown_type", f"Unknown message type: {message.type}")
            ]

    async def _handle_cancel(self, state: ConnectionState) -> list[WSMessage]:
        """Handle cancel request."""
        if state.is_processing:
            state.cancel_requested = True
            return [WSMessage.error("cancelled", "Query cancelled by user")]
        return [WSMessage.error("no_operation", "No operation to cancel")]

    async def _handle_query(
        self,
        state: ConnectionState,
        message: WSMessage,
    ) -> list[WSMessage]:
        """Handle query request."""
        if state.is_processing:
            return [WSMessage.error("busy", "Already processing a query")]

        query = message.data.get("query", "")
        if not query or len(query.strip()) < 3:
            return [
                WSMessage.error("invalid_query", "Query must be at least 3 characters")
            ]

        state.is_processing = True
        state.current_query_id = str(uuid.uuid4())
        state.cancel_requested = False

        responses: list[WSMessage] = []

        try:
            # Simulate processing (real impl would use agent_service)
            responses.append(WSMessage.thinking("Analizando consulta médica..."))

            # Simulate RAG search
            responses.append(WSMessage.rag_search(query[:50], results_count=5))

            # Check for cancellation
            if state.cancel_requested:
                responses.append(WSMessage.error("cancelled", "Query cancelled"))
                return responses

            # Simulate tool call
            if any(kw in query.lower() for kw in ["dosis", "medicamento", "fármaco"]):
                responses.append(WSMessage.tool_call("drug_interactions_checker"))

            # Stream response
            mock_response = self._generate_mock_response(
                message.data.get("user_type", "educational")
            )
            words = mock_response.split()

            for i, word in enumerate(words):
                if state.cancel_requested:
                    responses.append(WSMessage.error("cancelled", "Query cancelled"))
                    return responses
                responses.append(WSMessage.streaming(word + " ", token_count=i + 1))

            # Complete
            responses.append(
                WSMessage.complete(
                    query_id=state.current_query_id or "",
                    response=mock_response,
                    sources=[
                        {"id": "src_1", "title": "Medical Reference", "score": 0.92}
                    ],
                    tokens_used=len(words),
                )
            )

            state.queries_processed += 1

        finally:
            state.is_processing = False
            state.current_query_id = None

        return responses

    def _generate_mock_response(self, user_type: str) -> str:
        """Generate mock response."""
        if user_type == "professional":
            return "Respuesta profesional con terminología médica avanzada."
        elif user_type == "research":
            return "Respuesta de investigación con referencias académicas."
        else:
            return "Respuesta educativa clara y accesible."

    async def broadcast(self, message: WSMessage) -> int:
        """
        Broadcast message to all connections.

        Returns:
            Number of connections that received the message
        """
        count = 0
        for state in self._connections.values():
            state.messages_sent += 1
            count += 1
        return count

    def get_connection_stats(self) -> dict[str, Any]:
        """Get statistics about connections."""
        if not self._connections:
            return {
                "active_connections": 0,
                "total_messages_received": 0,
                "total_messages_sent": 0,
                "total_queries_processed": 0,
            }

        return {
            "active_connections": len(self._connections),
            "total_messages_received": sum(
                c.messages_received for c in self._connections.values()
            ),
            "total_messages_sent": sum(
                c.messages_sent for c in self._connections.values()
            ),
            "total_queries_processed": sum(
                c.queries_processed for c in self._connections.values()
            ),
            "avg_uptime_seconds": sum(
                c.uptime_seconds() for c in self._connections.values()
            )
            / len(self._connections),
        }


# =============================================================================
# Connection Manager
# =============================================================================


class ConnectionManager:
    """Manages WebSocket connections with cleanup."""

    def __init__(
        self,
        handler: WebSocketHandler,
        cleanup_interval: float = 60.0,
        max_idle_seconds: float = 300.0,
    ) -> None:
        """Initialize connection manager."""
        self.handler = handler
        self.cleanup_interval = cleanup_interval
        self.max_idle_seconds = max_idle_seconds
        self._cleanup_task: asyncio.Task[None] | None = None

    async def start(self) -> None:
        """Start connection manager."""
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())

    async def stop(self) -> None:
        """Stop connection manager."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

    async def _cleanup_loop(self) -> None:
        """Periodically clean up idle connections."""
        while True:
            await asyncio.sleep(self.cleanup_interval)
            await self._cleanup_idle_connections()

    async def _cleanup_idle_connections(self) -> None:
        """Remove connections that have been idle too long."""
        now = datetime.now()
        to_remove = []

        for conn_id, state in self.handler._connections.items():
            idle_seconds = (now - state.last_ping).total_seconds()
            if idle_seconds > self.max_idle_seconds:
                to_remove.append(conn_id)

        for conn_id in to_remove:
            await self.handler.on_disconnect(conn_id)


# =============================================================================
# Factory Functions
# =============================================================================


def create_websocket_handler() -> WebSocketHandler:
    """Create WebSocket handler with default configuration."""
    return WebSocketHandler(
        ping_interval=30.0,
        ping_timeout=10.0,
        max_message_size=64 * 1024,
    )


def create_connection_manager(
    handler: WebSocketHandler | None = None,
) -> ConnectionManager:
    """Create connection manager."""
    return ConnectionManager(
        handler=handler or create_websocket_handler(),
        cleanup_interval=60.0,
        max_idle_seconds=300.0,
    )
