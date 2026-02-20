# =============================================================================
# MedeX - Agent Core Data Models
# =============================================================================
"""
Data models for the Agent Core system.

This module defines:
- AgentState: Current state of the agent
- AgentAction: Actions the agent can take
- AgentPlan: Multi-step execution plan
- AgentContext: Execution context with history
- AgentResult: Final result of agent execution
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4


# =============================================================================
# Enumerations
# =============================================================================


class AgentPhase(str, Enum):
    """Phases of agent execution."""

    IDLE = "idle"
    RECEIVING = "receiving"
    ANALYZING = "analyzing"
    PLANNING = "planning"
    EXECUTING = "executing"
    TOOL_CALLING = "tool_calling"
    RAG_SEARCHING = "rag_searching"
    GENERATING = "generating"
    REVIEWING = "reviewing"
    COMPLETED = "completed"
    ERROR = "error"


class ActionType(str, Enum):
    """Types of agent actions."""

    THINK = "think"  # Internal reasoning
    SEARCH = "search"  # RAG search
    TOOL_CALL = "tool_call"  # Execute tool
    RESPOND = "respond"  # Generate response
    CLARIFY = "clarify"  # Ask for clarification
    ESCALATE = "escalate"  # Escalate to specialist
    DEFER = "defer"  # Defer to human


class PlanStatus(str, Enum):
    """Status of execution plan."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class IntentType(str, Enum):
    """Types of user intent."""

    EDUCATIONAL = "educational"  # General health question
    DIAGNOSTIC = "diagnostic"  # Symptoms/diagnosis query
    TREATMENT = "treatment"  # Treatment query
    MEDICATION = "medication"  # Drug information
    EMERGENCY = "emergency"  # Emergency situation
    FOLLOW_UP = "follow_up"  # Follow-up question
    CLARIFICATION = "clarification"  # Clarification request
    GREETING = "greeting"  # Social greeting
    OTHER = "other"  # Unclassified


class UrgencyLevel(str, Enum):
    """Urgency classification."""

    CRITICAL = "critical"  # Immediate action needed
    HIGH = "high"  # Urgent attention required
    MEDIUM = "medium"  # Standard priority
    LOW = "low"  # Routine query
    INFORMATIONAL = "informational"  # Pure information


# =============================================================================
# Action Models
# =============================================================================


@dataclass
class AgentAction:
    """A single action in the agent's plan."""

    action_type: ActionType
    description: str

    # Action-specific data
    tool_name: str | None = None
    tool_args: dict[str, Any] | None = None
    search_query: str | None = None
    response_template: str | None = None

    # Execution info
    id: str = field(default_factory=lambda: f"act_{uuid4().hex[:8]}")
    status: PlanStatus = PlanStatus.PENDING
    started_at: datetime | None = None
    completed_at: datetime | None = None

    # Result
    result: Any = None
    error: str | None = None

    @property
    def duration_ms(self) -> float | None:
        """Get action duration in milliseconds."""
        if not self.started_at or not self.completed_at:
            return None
        return (self.completed_at - self.started_at).total_seconds() * 1000

    @property
    def is_complete(self) -> bool:
        """Check if action is complete."""
        return self.status in {PlanStatus.COMPLETED, PlanStatus.FAILED}

    def start(self) -> None:
        """Mark action as started."""
        self.status = PlanStatus.IN_PROGRESS
        self.started_at = datetime.utcnow()

    def complete(self, result: Any = None) -> None:
        """Mark action as completed."""
        self.status = PlanStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.result = result

    def fail(self, error: str) -> None:
        """Mark action as failed."""
        self.status = PlanStatus.FAILED
        self.completed_at = datetime.utcnow()
        self.error = error

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "action_type": self.action_type.value,
            "description": self.description,
            "tool_name": self.tool_name,
            "tool_args": self.tool_args,
            "search_query": self.search_query,
            "status": self.status.value,
            "duration_ms": self.duration_ms,
            "error": self.error,
        }


# =============================================================================
# Plan Models
# =============================================================================


@dataclass
class AgentPlan:
    """Multi-step execution plan."""

    actions: list[AgentAction] = field(default_factory=list)
    reasoning: str = ""

    # Metadata
    id: str = field(default_factory=lambda: f"plan_{uuid4().hex[:8]}")
    created_at: datetime = field(default_factory=datetime.utcnow)
    status: PlanStatus = PlanStatus.PENDING

    # Execution tracking
    current_step: int = 0
    total_steps: int = 0

    @property
    def progress(self) -> float:
        """Get execution progress (0.0 to 1.0)."""
        if not self.actions:
            return 0.0
        completed = sum(1 for a in self.actions if a.is_complete)
        return completed / len(self.actions)

    @property
    def is_complete(self) -> bool:
        """Check if plan is complete."""
        return all(a.is_complete for a in self.actions)

    @property
    def has_errors(self) -> bool:
        """Check if plan has any failed actions."""
        return any(a.status == PlanStatus.FAILED for a in self.actions)

    @property
    def current_action(self) -> AgentAction | None:
        """Get current action to execute."""
        for action in self.actions:
            if action.status == PlanStatus.PENDING:
                return action
        return None

    def add_action(self, action: AgentAction) -> None:
        """Add action to plan."""
        self.actions.append(action)
        self.total_steps = len(self.actions)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "reasoning": self.reasoning,
            "status": self.status.value,
            "progress": self.progress,
            "current_step": self.current_step,
            "total_steps": self.total_steps,
            "actions": [a.to_dict() for a in self.actions],
        }


# =============================================================================
# Context Models
# =============================================================================


@dataclass
class UserIntent:
    """Analyzed user intent."""

    intent_type: IntentType
    confidence: float = 0.0
    urgency: UrgencyLevel = UrgencyLevel.MEDIUM

    # Extracted entities
    symptoms: list[str] = field(default_factory=list)
    medications: list[str] = field(default_factory=list)
    conditions: list[str] = field(default_factory=list)
    body_parts: list[str] = field(default_factory=list)

    # Context
    requires_rag: bool = False
    requires_tools: bool = False
    specialty: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "intent_type": self.intent_type.value,
            "confidence": self.confidence,
            "urgency": self.urgency.value,
            "symptoms": self.symptoms,
            "medications": self.medications,
            "conditions": self.conditions,
            "requires_rag": self.requires_rag,
            "requires_tools": self.requires_tools,
            "specialty": self.specialty,
        }


@dataclass
class AgentContext:
    """Execution context for agent."""

    # User input
    query: str
    user_mode: str = "educational"  # educational | professional
    language: str = "es"

    # Analyzed intent
    intent: UserIntent | None = None

    # Retrieved context
    rag_context: str | None = None
    rag_sources: list[dict[str, Any]] = field(default_factory=list)

    # Tool results
    tool_results: dict[str, Any] = field(default_factory=dict)

    # Conversation history
    history: list[dict[str, Any]] = field(default_factory=list)

    # Session info
    session_id: str = field(default_factory=lambda: f"sess_{uuid4().hex[:12]}")
    user_id: str | None = None

    # Metadata
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_tool_result(self, tool_name: str, result: Any) -> None:
        """Add tool execution result."""
        self.tool_results[tool_name] = result

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "query": self.query,
            "user_mode": self.user_mode,
            "language": self.language,
            "intent": self.intent.to_dict() if self.intent else None,
            "has_rag_context": self.rag_context is not None,
            "rag_sources_count": len(self.rag_sources),
            "tool_results_count": len(self.tool_results),
            "history_length": len(self.history),
            "session_id": self.session_id,
        }


# =============================================================================
# State Models
# =============================================================================


@dataclass
class AgentState:
    """Current state of the agent."""

    # Phase tracking
    phase: AgentPhase = AgentPhase.IDLE
    previous_phase: AgentPhase | None = None

    # Context
    context: AgentContext | None = None

    # Plan
    plan: AgentPlan | None = None

    # Current response being built
    response_buffer: str = ""

    # Timing
    started_at: datetime | None = None
    phase_started_at: datetime | None = None

    # Iteration tracking (for safety limits)
    iteration_count: int = 0
    max_iterations: int = 10

    # Error tracking
    errors: list[str] = field(default_factory=list)
    last_error: str | None = None

    @property
    def elapsed_ms(self) -> float:
        """Get total elapsed time in milliseconds."""
        if not self.started_at:
            return 0.0
        return (datetime.utcnow() - self.started_at).total_seconds() * 1000

    @property
    def phase_elapsed_ms(self) -> float:
        """Get current phase elapsed time in milliseconds."""
        if not self.phase_started_at:
            return 0.0
        return (datetime.utcnow() - self.phase_started_at).total_seconds() * 1000

    @property
    def is_terminal(self) -> bool:
        """Check if state is terminal."""
        return self.phase in {AgentPhase.COMPLETED, AgentPhase.ERROR}

    @property
    def should_stop(self) -> bool:
        """Check if agent should stop (safety limit)."""
        return self.iteration_count >= self.max_iterations

    def transition(self, new_phase: AgentPhase) -> None:
        """Transition to new phase."""
        self.previous_phase = self.phase
        self.phase = new_phase
        self.phase_started_at = datetime.utcnow()

    def increment_iteration(self) -> None:
        """Increment iteration counter."""
        self.iteration_count += 1

    def add_error(self, error: str) -> None:
        """Add error to tracking."""
        self.errors.append(error)
        self.last_error = error

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "phase": self.phase.value,
            "previous_phase": self.previous_phase.value
            if self.previous_phase
            else None,
            "elapsed_ms": self.elapsed_ms,
            "iteration_count": self.iteration_count,
            "has_plan": self.plan is not None,
            "plan_progress": self.plan.progress if self.plan else 0.0,
            "response_length": len(self.response_buffer),
            "error_count": len(self.errors),
            "last_error": self.last_error,
        }


# =============================================================================
# Result Models
# =============================================================================


@dataclass
class AgentResult:
    """Final result of agent execution."""

    # Response
    content: str
    success: bool = True

    # Classification
    intent_type: IntentType = IntentType.OTHER
    urgency: UrgencyLevel = UrgencyLevel.MEDIUM

    # Metadata
    id: str = field(default_factory=lambda: f"res_{uuid4().hex[:12]}")
    created_at: datetime = field(default_factory=datetime.utcnow)

    # Sources
    sources: list[dict[str, Any]] = field(default_factory=list)
    tools_used: list[str] = field(default_factory=list)

    # Metrics
    total_tokens: int = 0
    latency_ms: float = 0.0
    phases_completed: list[str] = field(default_factory=list)

    # Error info
    error: str | None = None

    # Raw data for debugging
    raw_state: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "content": self.content,
            "success": self.success,
            "intent_type": self.intent_type.value,
            "urgency": self.urgency.value,
            "sources": self.sources,
            "tools_used": self.tools_used,
            "total_tokens": self.total_tokens,
            "latency_ms": self.latency_ms,
            "phases_completed": self.phases_completed,
            "error": self.error,
            "created_at": self.created_at.isoformat(),
        }


# =============================================================================
# Event Models (for streaming/observability)
# =============================================================================


@dataclass
class AgentEvent:
    """Event emitted during agent execution."""

    event_type: str
    phase: AgentPhase
    data: dict[str, Any] = field(default_factory=dict)

    # Timing
    timestamp: float = field(default_factory=time.time)
    sequence: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "event_type": self.event_type,
            "phase": self.phase.value,
            "data": self.data,
            "timestamp": self.timestamp,
            "sequence": self.sequence,
        }

    def to_sse(self) -> str:
        """Convert to SSE format."""
        import json

        return f"data: {json.dumps(self.to_dict())}\n\n"
