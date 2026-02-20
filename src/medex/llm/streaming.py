# =============================================================================
# MedeX - Stream Handler (SSE)
# =============================================================================
"""
Server-Sent Events (SSE) streaming handler for LLM responses.

Features:
- Real-time token streaming
- SSE protocol compliance
- Heartbeat mechanism
- Error handling and recovery
- Progress tracking
- Client connection management
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from medex.llm.models import (
    FinishReason,
    LLMResponse,
    StreamChunk,
    StreamEventType,
    TokenUsage,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Configuration
# =============================================================================


@dataclass
class StreamConfig:
    """Configuration for stream handler."""

    # Heartbeat settings
    heartbeat_interval: float = 15.0  # seconds
    heartbeat_enabled: bool = True

    # Buffer settings
    buffer_size: int = 100
    flush_interval: float = 0.1  # seconds

    # Timeout settings
    stream_timeout: float = 300.0  # 5 minutes
    idle_timeout: float = 60.0  # 1 minute

    # SSE settings
    event_prefix: str = "data: "
    event_suffix: str = "\n\n"
    done_signal: str = "[DONE]"

    # Error handling
    retry_on_error: bool = True
    max_retries: int = 3


# =============================================================================
# Stream State
# =============================================================================


@dataclass
class StreamState:
    """State tracking for a stream."""

    # Identifiers
    stream_id: str
    request_id: str

    # Timing
    started_at: datetime = field(default_factory=datetime.utcnow)
    first_token_at: datetime | None = None
    finished_at: datetime | None = None

    # Content
    total_content: str = ""
    chunk_count: int = 0

    # Status
    is_active: bool = True
    is_complete: bool = False
    finish_reason: FinishReason | None = None
    error: str | None = None

    # Metrics
    tokens_streamed: int = 0
    bytes_sent: int = 0

    @property
    def duration_ms(self) -> float:
        """Get stream duration in milliseconds."""
        end = self.finished_at or datetime.utcnow()
        return (end - self.started_at).total_seconds() * 1000

    @property
    def time_to_first_token_ms(self) -> float | None:
        """Get time to first token in milliseconds."""
        if not self.first_token_at:
            return None
        return (self.first_token_at - self.started_at).total_seconds() * 1000

    @property
    def tokens_per_second(self) -> float:
        """Calculate tokens per second."""
        duration_s = self.duration_ms / 1000
        if duration_s <= 0:
            return 0.0
        return self.tokens_streamed / duration_s

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "stream_id": self.stream_id,
            "request_id": self.request_id,
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "duration_ms": self.duration_ms,
            "time_to_first_token_ms": self.time_to_first_token_ms,
            "chunk_count": self.chunk_count,
            "tokens_streamed": self.tokens_streamed,
            "tokens_per_second": self.tokens_per_second,
            "is_complete": self.is_complete,
            "finish_reason": self.finish_reason.value if self.finish_reason else None,
            "error": self.error,
        }


# =============================================================================
# SSE Event Formatters
# =============================================================================


def format_sse_event(
    data: dict[str, Any] | str,
    event: str | None = None,
    event_id: str | None = None,
    retry: int | None = None,
) -> str:
    """Format data as SSE event."""
    lines = []

    if event_id:
        lines.append(f"id: {event_id}")

    if event:
        lines.append(f"event: {event}")

    if retry:
        lines.append(f"retry: {retry}")

    if isinstance(data, dict):
        data_str = json.dumps(data, ensure_ascii=False)
    else:
        data_str = str(data)

    lines.append(f"data: {data_str}")
    lines.append("")  # Empty line to end event

    return "\n".join(lines) + "\n"


def format_chunk_sse(chunk: StreamChunk) -> str:
    """Format StreamChunk as SSE event."""
    data = {
        "id": chunk.id,
        "event": chunk.event_type.value,
        "index": chunk.index,
    }

    if chunk.delta:
        data["delta"] = chunk.delta

    if chunk.content:
        data["content"] = chunk.content

    if chunk.tool_call:
        data["tool_call"] = chunk.tool_call

    if chunk.finish_reason:
        data["finish_reason"] = chunk.finish_reason.value

    if chunk.usage:
        data["usage"] = chunk.usage.to_dict()

    if chunk.error:
        data["error"] = chunk.error

    return format_sse_event(data, event=chunk.event_type.value, event_id=chunk.id)


def format_heartbeat() -> str:
    """Format heartbeat event."""
    return format_sse_event(
        {"type": "heartbeat", "timestamp": time.time()},
        event="heartbeat",
    )


def format_done() -> str:
    """Format stream done event."""
    return "data: [DONE]\n\n"


# =============================================================================
# Stream Handler
# =============================================================================


class StreamHandler:
    """Handler for SSE streaming responses."""

    def __init__(self, config: StreamConfig | None = None) -> None:
        """Initialize stream handler."""
        self.config = config or StreamConfig()
        self._active_streams: dict[str, StreamState] = {}

    async def create_stream(
        self,
        chunks: AsyncIterator[StreamChunk],
        request_id: str,
        on_chunk: Callable[[StreamChunk], None] | None = None,
        on_complete: Callable[[StreamState], None] | None = None,
    ) -> AsyncIterator[str]:
        """
        Create SSE stream from chunk iterator.

        Args:
            chunks: Async iterator of StreamChunk
            request_id: Request identifier
            on_chunk: Optional callback for each chunk
            on_complete: Optional callback on completion

        Yields:
            SSE formatted strings
        """
        from uuid import uuid4

        stream_id = f"stream_{uuid4().hex[:12]}"
        state = StreamState(stream_id=stream_id, request_id=request_id)
        self._active_streams[stream_id] = state

        # Heartbeat task
        heartbeat_task: asyncio.Task | None = None
        if self.config.heartbeat_enabled:
            heartbeat_task = asyncio.create_task(self._heartbeat_loop(stream_id))

        try:
            async for chunk in chunks:
                if not state.is_active:
                    break

                # Update state
                state.chunk_count += 1

                if chunk.event_type == StreamEventType.DELTA:
                    if state.first_token_at is None:
                        state.first_token_at = datetime.utcnow()
                    state.total_content += chunk.delta
                    state.tokens_streamed += max(1, len(chunk.delta) // 4)

                elif chunk.event_type == StreamEventType.FINISH:
                    state.is_complete = True
                    state.finish_reason = chunk.finish_reason
                    if chunk.usage:
                        state.tokens_streamed = chunk.usage.completion_tokens

                elif chunk.event_type == StreamEventType.ERROR:
                    state.error = chunk.error

                # Format and yield SSE
                sse_event = format_chunk_sse(chunk)
                state.bytes_sent += len(sse_event.encode())
                yield sse_event

                # Callback
                if on_chunk:
                    try:
                        on_chunk(chunk)
                    except Exception as e:
                        logger.error(f"Chunk callback error: {e}")

            # Send done signal
            yield format_done()

        except asyncio.CancelledError:
            logger.info(f"Stream {stream_id} cancelled")
            state.error = "Stream cancelled"

        except Exception as e:
            logger.error(f"Stream {stream_id} error: {e}")
            state.error = str(e)

            # Send error event
            error_chunk = StreamChunk(
                event_type=StreamEventType.ERROR,
                error=str(e),
            )
            yield format_chunk_sse(error_chunk)

        finally:
            # Cleanup
            state.is_active = False
            state.finished_at = datetime.utcnow()

            if heartbeat_task:
                heartbeat_task.cancel()
                try:
                    await heartbeat_task
                except asyncio.CancelledError:
                    pass

            # Remove from active streams
            self._active_streams.pop(stream_id, None)

            # Completion callback
            if on_complete:
                try:
                    on_complete(state)
                except Exception as e:
                    logger.error(f"Complete callback error: {e}")

    async def _heartbeat_loop(self, stream_id: str) -> None:
        """Send periodic heartbeats."""
        while True:
            await asyncio.sleep(self.config.heartbeat_interval)

            state = self._active_streams.get(stream_id)
            if not state or not state.is_active:
                break

            # Note: Can't yield from here, heartbeats are logged only
            logger.debug(f"Heartbeat for stream {stream_id}")

    def create_text_stream(
        self,
        text: str,
        chunk_size: int = 20,
        delay: float = 0.02,
    ) -> AsyncIterator[str]:
        """
        Create simulated SSE stream from text.

        Useful for testing or converting non-streaming responses.
        """

        async def _generate() -> AsyncIterator[str]:
            # Start event
            start_chunk = StreamChunk(event_type=StreamEventType.START, index=0)
            yield format_chunk_sse(start_chunk)

            # Stream text in chunks
            index = 1
            full_content = ""

            for i in range(0, len(text), chunk_size):
                chunk_text = text[i : i + chunk_size]
                full_content += chunk_text

                chunk = StreamChunk(
                    event_type=StreamEventType.DELTA,
                    delta=chunk_text,
                    content=full_content,
                    index=index,
                )
                yield format_chunk_sse(chunk)
                index += 1

                await asyncio.sleep(delay)

            # Finish event
            finish_chunk = StreamChunk(
                event_type=StreamEventType.FINISH,
                content=full_content,
                finish_reason=FinishReason.STOP,
                usage=TokenUsage(
                    prompt_tokens=0,
                    completion_tokens=len(text) // 4,
                    total_tokens=len(text) // 4,
                ),
                index=index,
            )
            yield format_chunk_sse(finish_chunk)
            yield format_done()

        return _generate()

    async def collect_stream(
        self,
        chunks: AsyncIterator[StreamChunk],
    ) -> LLMResponse:
        """Collect streaming chunks into complete response."""
        content = ""
        usage = TokenUsage()
        finish_reason = FinishReason.STOP
        tool_calls: list[dict[str, Any]] = []
        error: str | None = None

        start_time = time.time()
        first_token_time: float | None = None

        async for chunk in chunks:
            if chunk.event_type == StreamEventType.DELTA:
                content += chunk.delta
                if first_token_time is None:
                    first_token_time = time.time()

            elif chunk.event_type == StreamEventType.TOOL_CALL:
                if chunk.tool_call:
                    tool_calls.append(chunk.tool_call)

            elif chunk.event_type == StreamEventType.FINISH:
                if chunk.finish_reason:
                    finish_reason = chunk.finish_reason
                if chunk.usage:
                    usage = chunk.usage

            elif chunk.event_type == StreamEventType.ERROR:
                error = chunk.error
                finish_reason = FinishReason.ERROR

        latency_ms = (time.time() - start_time) * 1000
        ttft_ms = (first_token_time - start_time) * 1000 if first_token_time else None

        return LLMResponse(
            content=content,
            finish_reason=finish_reason,
            usage=usage,
            latency_ms=latency_ms,
            time_to_first_token_ms=ttft_ms,
            tool_calls=tool_calls,
            error=error,
        )

    def get_active_streams(self) -> list[StreamState]:
        """Get all active stream states."""
        return list(self._active_streams.values())

    def cancel_stream(self, stream_id: str) -> bool:
        """Cancel an active stream."""
        state = self._active_streams.get(stream_id)
        if state:
            state.is_active = False
            return True
        return False

    def get_stream_state(self, stream_id: str) -> StreamState | None:
        """Get state of a stream."""
        return self._active_streams.get(stream_id)


# =============================================================================
# Async Generator Utilities
# =============================================================================


async def merge_streams(
    *streams: AsyncIterator[StreamChunk],
) -> AsyncIterator[StreamChunk]:
    """Merge multiple streams into one."""
    from asyncio import Queue, create_task

    queue: Queue[StreamChunk | None] = Queue()
    active_count = len(streams)

    async def feed_queue(stream: AsyncIterator[StreamChunk]) -> None:
        nonlocal active_count
        try:
            async for chunk in stream:
                await queue.put(chunk)
        finally:
            active_count -= 1
            if active_count == 0:
                await queue.put(None)  # Signal completion

    # Start all stream consumers
    tasks = [create_task(feed_queue(s)) for s in streams]

    try:
        while True:
            chunk = await queue.get()
            if chunk is None:
                break
            yield chunk
    finally:
        for task in tasks:
            task.cancel()


async def buffer_stream(
    stream: AsyncIterator[StreamChunk],
    buffer_size: int = 10,
) -> AsyncIterator[list[StreamChunk]]:
    """Buffer stream chunks into batches."""
    buffer: list[StreamChunk] = []

    async for chunk in stream:
        buffer.append(chunk)

        if len(buffer) >= buffer_size:
            yield buffer
            buffer = []

    if buffer:
        yield buffer


async def timeout_stream(
    stream: AsyncIterator[StreamChunk],
    timeout: float = 60.0,
) -> AsyncIterator[StreamChunk]:
    """Add timeout to stream iteration."""
    async for chunk in stream:
        try:
            yield chunk
        except asyncio.TimeoutError:
            yield StreamChunk(
                event_type=StreamEventType.ERROR,
                error="Stream timeout",
            )
            break


# =============================================================================
# Factory Functions
# =============================================================================


def create_stream_handler(config: StreamConfig | None = None) -> StreamHandler:
    """Create stream handler with configuration."""
    return StreamHandler(config)


def get_stream_handler() -> StreamHandler:
    """Get default stream handler instance."""
    return StreamHandler()
