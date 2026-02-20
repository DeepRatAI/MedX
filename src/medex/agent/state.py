# =============================================================================
# MedeX - State Manager
# =============================================================================
"""
State management for the MedeX agent.

Features:
- Finite State Machine for agent phases
- State persistence and recovery
- Transition validation
- State snapshots for debugging
- Event emission on transitions
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable

from medex.agent.models import (
    AgentContext,
    AgentEvent,
    AgentPhase,
    AgentPlan,
    AgentResult,
    AgentState,
)


logger = logging.getLogger(__name__)


# =============================================================================
# Transition Rules
# =============================================================================

# Valid phase transitions
VALID_TRANSITIONS: dict[AgentPhase, set[AgentPhase]] = {
    AgentPhase.IDLE: {
        AgentPhase.RECEIVING,
        AgentPhase.ERROR,
    },
    AgentPhase.RECEIVING: {
        AgentPhase.ANALYZING,
        AgentPhase.ERROR,
    },
    AgentPhase.ANALYZING: {
        AgentPhase.PLANNING,
        AgentPhase.GENERATING,  # Simple queries skip planning
        AgentPhase.ERROR,
    },
    AgentPhase.PLANNING: {
        AgentPhase.EXECUTING,
        AgentPhase.ERROR,
    },
    AgentPhase.EXECUTING: {
        AgentPhase.TOOL_CALLING,
        AgentPhase.RAG_SEARCHING,
        AgentPhase.GENERATING,
        AgentPhase.REVIEWING,
        AgentPhase.ERROR,
    },
    AgentPhase.TOOL_CALLING: {
        AgentPhase.EXECUTING,
        AgentPhase.GENERATING,
        AgentPhase.ERROR,
    },
    AgentPhase.RAG_SEARCHING: {
        AgentPhase.EXECUTING,
        AgentPhase.GENERATING,
        AgentPhase.ERROR,
    },
    AgentPhase.GENERATING: {
        AgentPhase.REVIEWING,
        AgentPhase.COMPLETED,
        AgentPhase.ERROR,
    },
    AgentPhase.REVIEWING: {
        AgentPhase.GENERATING,  # Re-generate if review fails
        AgentPhase.COMPLETED,
        AgentPhase.ERROR,
    },
    AgentPhase.COMPLETED: set(),  # Terminal state
    AgentPhase.ERROR: {
        AgentPhase.IDLE,  # Can reset from error
    },
}


# =============================================================================
# Configuration
# =============================================================================


@dataclass
class StateManagerConfig:
    """Configuration for state manager."""

    # Limits
    max_iterations: int = 10
    max_phase_duration_ms: float = 30_000  # 30 seconds per phase
    max_total_duration_ms: float = 120_000  # 2 minutes total

    # Persistence
    enable_snapshots: bool = True
    snapshot_interval: int = 3  # Snapshot every N transitions

    # Events
    emit_events: bool = True


# =============================================================================
# State Snapshot
# =============================================================================


@dataclass
class StateSnapshot:
    """Snapshot of agent state at a point in time."""

    state: dict[str, Any]
    phase: AgentPhase
    timestamp: datetime = field(default_factory=datetime.utcnow)
    sequence: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "state": self.state,
            "phase": self.phase.value,
            "timestamp": self.timestamp.isoformat(),
            "sequence": self.sequence,
        }


# =============================================================================
# State Manager
# =============================================================================


class StateManager:
    """Manages agent state and transitions."""

    def __init__(self, config: StateManagerConfig | None = None) -> None:
        """Initialize state manager."""
        self.config = config or StateManagerConfig()

        # Current state
        self._state: AgentState | None = None

        # History
        self._snapshots: list[StateSnapshot] = []
        self._transition_count: int = 0
        self._event_sequence: int = 0

        # Event handlers
        self._event_handlers: list[Callable[[AgentEvent], None]] = []

        # Lock for thread safety
        self._lock = asyncio.Lock()

    @property
    def state(self) -> AgentState | None:
        """Get current state."""
        return self._state

    @property
    def phase(self) -> AgentPhase:
        """Get current phase."""
        return self._state.phase if self._state else AgentPhase.IDLE

    @property
    def is_active(self) -> bool:
        """Check if agent is actively processing."""
        return self._state is not None and not self._state.is_terminal

    def initialize(self, context: AgentContext) -> AgentState:
        """Initialize new agent state."""
        self._state = AgentState(
            phase=AgentPhase.IDLE,
            context=context,
            started_at=datetime.utcnow(),
            phase_started_at=datetime.utcnow(),
            max_iterations=self.config.max_iterations,
        )

        self._snapshots.clear()
        self._transition_count = 0
        self._event_sequence = 0

        self._emit_event("state_initialized", {"context": context.to_dict()})
        self._take_snapshot()

        return self._state

    async def transition(self, new_phase: AgentPhase) -> bool:
        """
        Transition to a new phase.

        Returns True if transition was successful.
        """
        async with self._lock:
            if not self._state:
                logger.error("Cannot transition: no active state")
                return False

            current = self._state.phase

            # Validate transition
            if not self._is_valid_transition(current, new_phase):
                logger.warning(
                    f"Invalid transition: {current.value} -> {new_phase.value}"
                )
                return False

            # Check safety limits
            if self._state.should_stop:
                logger.warning("Max iterations reached, forcing error state")
                new_phase = AgentPhase.ERROR
                self._state.add_error("Max iterations exceeded")

            # Check phase timeout
            if self._is_phase_timeout():
                logger.warning("Phase timeout, forcing error state")
                new_phase = AgentPhase.ERROR
                self._state.add_error(
                    f"Phase {current.value} exceeded timeout "
                    f"({self.config.max_phase_duration_ms}ms)"
                )

            # Perform transition
            self._state.transition(new_phase)
            self._state.increment_iteration()
            self._transition_count += 1

            logger.info(f"Phase transition: {current.value} -> {new_phase.value}")

            # Take snapshot if needed
            if (
                self.config.enable_snapshots
                and self._transition_count % self.config.snapshot_interval == 0
            ):
                self._take_snapshot()

            # Emit event
            self._emit_event(
                "phase_transition",
                {
                    "from": current.value,
                    "to": new_phase.value,
                    "iteration": self._state.iteration_count,
                },
            )

            return True

    def can_transition(self, new_phase: AgentPhase) -> bool:
        """Check if transition to new phase is valid."""
        if not self._state:
            return False
        return self._is_valid_transition(self._state.phase, new_phase)

    def _is_valid_transition(
        self,
        from_phase: AgentPhase,
        to_phase: AgentPhase,
    ) -> bool:
        """Check if transition is valid according to rules."""
        valid = VALID_TRANSITIONS.get(from_phase, set())
        return to_phase in valid

    def _is_phase_timeout(self) -> bool:
        """Check if current phase has exceeded timeout."""
        if not self._state:
            return False
        return self._state.phase_elapsed_ms > self.config.max_phase_duration_ms

    def _is_total_timeout(self) -> bool:
        """Check if total execution has exceeded timeout."""
        if not self._state:
            return False
        return self._state.elapsed_ms > self.config.max_total_duration_ms

    def set_plan(self, plan: AgentPlan) -> None:
        """Set execution plan."""
        if self._state:
            self._state.plan = plan
            self._emit_event("plan_set", {"plan": plan.to_dict()})

    def update_response(self, content: str) -> None:
        """Update response buffer."""
        if self._state:
            self._state.response_buffer = content
            self._emit_event(
                "response_updated",
                {"length": len(content)},
            )

    def append_response(self, content: str) -> None:
        """Append to response buffer."""
        if self._state:
            self._state.response_buffer += content

    def add_error(self, error: str) -> None:
        """Add error to state."""
        if self._state:
            self._state.add_error(error)
            self._emit_event("error_added", {"error": error})

    def get_result(self) -> AgentResult:
        """Build final result from current state."""
        if not self._state:
            return AgentResult(
                content="",
                success=False,
                error="No state available",
            )

        context = self._state.context
        plan = self._state.plan

        # Collect tools used
        tools_used = []
        if plan:
            for action in plan.actions:
                if action.tool_name and action.status.value == "completed":
                    tools_used.append(action.tool_name)

        # Collect sources
        sources = []
        if context and context.rag_sources:
            sources = context.rag_sources

        return AgentResult(
            content=self._state.response_buffer,
            success=not self._state.errors,
            intent_type=context.intent.intent_type
            if context and context.intent
            else None,
            urgency=context.intent.urgency if context and context.intent else None,
            sources=sources,
            tools_used=tools_used,
            latency_ms=self._state.elapsed_ms,
            phases_completed=[
                p.value
                for p in AgentPhase
                if p != self._state.phase and p not in {AgentPhase.ERROR}
            ],
            error=self._state.last_error,
            raw_state=self._state.to_dict() if self._state else None,
        )

    def _take_snapshot(self) -> None:
        """Take state snapshot."""
        if not self._state:
            return

        snapshot = StateSnapshot(
            state=self._state.to_dict(),
            phase=self._state.phase,
            sequence=len(self._snapshots),
        )
        self._snapshots.append(snapshot)

    def get_snapshots(self) -> list[StateSnapshot]:
        """Get all state snapshots."""
        return self._snapshots.copy()

    def get_latest_snapshot(self) -> StateSnapshot | None:
        """Get most recent snapshot."""
        return self._snapshots[-1] if self._snapshots else None

    # =========================================================================
    # Event Handling
    # =========================================================================

    def add_event_handler(
        self,
        handler: Callable[[AgentEvent], None],
    ) -> None:
        """Add event handler."""
        self._event_handlers.append(handler)

    def remove_event_handler(
        self,
        handler: Callable[[AgentEvent], None],
    ) -> None:
        """Remove event handler."""
        if handler in self._event_handlers:
            self._event_handlers.remove(handler)

    def _emit_event(self, event_type: str, data: dict[str, Any]) -> None:
        """Emit event to handlers."""
        if not self.config.emit_events:
            return

        event = AgentEvent(
            event_type=event_type,
            phase=self.phase,
            data=data,
            sequence=self._event_sequence,
        )
        self._event_sequence += 1

        for handler in self._event_handlers:
            try:
                handler(event)
            except Exception as e:
                logger.error(f"Event handler error: {e}")

    # =========================================================================
    # Reset and Cleanup
    # =========================================================================

    def reset(self) -> None:
        """Reset state manager."""
        self._state = None
        self._snapshots.clear()
        self._transition_count = 0
        self._event_sequence = 0

    def force_error(self, error: str) -> None:
        """Force transition to error state."""
        if self._state:
            self._state.add_error(error)
            self._state.transition(AgentPhase.ERROR)

    def force_complete(self) -> None:
        """Force transition to completed state."""
        if self._state:
            self._state.transition(AgentPhase.COMPLETED)


# =============================================================================
# Factory Functions
# =============================================================================


def create_state_manager(
    config: StateManagerConfig | None = None,
) -> StateManager:
    """Create state manager with configuration."""
    return StateManager(config)


def get_state_manager() -> StateManager:
    """Get default state manager instance."""
    return StateManager()
