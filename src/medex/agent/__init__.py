# =============================================================================
# MedeX - Agent Module
# =============================================================================
"""
Agent Core module for MedeX.

This module provides the intelligent agent that orchestrates:
- Intent analysis and query understanding
- Action planning and execution
- Tool and RAG integration
- Response generation
- State management and observability

Architecture:
    ┌─────────────────────────────────────────────────────────┐
    │                    AgentService                         │
    │  (High-level façade for query processing)               │
    └─────────────────────────────────────────────────────────┘
                              │
                              ▼
    ┌─────────────────────────────────────────────────────────┐
    │                  AgentController                        │
    │  (ReAct loop orchestration, intent analysis)            │
    └─────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
    ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
    │StateManager │   │ PlanBuilder │   │PlanExecutor │
    │(FSM, events)│   │(planning)   │   │(execution)  │
    └─────────────┘   └─────────────┘   └─────────────┘

Components:
- models: Data models for agent state, actions, and events
- state: State machine for agent execution phases
- planner: Plan building and action execution
- controller: Main agent loop orchestration
- service: High-level service façade

Usage:
    from medex.agent import AgentService, create_agent_service

    # Create service
    agent = create_agent_service(
        llm_service=llm,
        rag_service=rag,
        tool_service=tools,
        memory_service=memory,
    )

    # Initialize
    await agent.initialize()

    # Query
    result = await agent.query("What are the symptoms of diabetes?")
    print(result.content)

    # Stream
    async for event in agent.query_stream("Explain hypertension"):
        print(event.data)

Features:
- ReAct-style agent loop (Reason → Act → Observe)
- Multi-provider LLM support with automatic failover
- RAG integration for medical knowledge retrieval
- 12+ medical tools for specialized tasks
- Conversation memory for multi-turn dialogue
- Emergency detection and priority handling
- Full observability with events and metrics
- Streaming responses with SSE support
"""

from medex.agent.controller import (
    AgentController,
    AgentControllerConfig,
    IntentAnalyzer,
    ResponseGenerator,
    create_agent_controller,
)
from medex.agent.models import (  # Enums; Data classes
    ActionType,
    AgentAction,
    AgentContext,
    AgentEvent,
    AgentPhase,
    AgentPlan,
    AgentResult,
    AgentState,
    IntentType,
    PlanStatus,
    UrgencyLevel,
    UserIntent,
)
from medex.agent.planner import (
    PlanBuilder,
    PlanExecutor,
    PlanExecutorConfig,
    create_plan_builder,
    create_plan_executor,
)
from medex.agent.service import (
    AgentService,
    AgentServiceConfig,
    ServiceMetrics,
    create_agent_service,
    get_agent_service,
)
from medex.agent.state import (
    VALID_TRANSITIONS,
    StateManager,
    StateManagerConfig,
    StateSnapshot,
    create_state_manager,
    get_state_manager,
)

# =============================================================================
# Module Exports
# =============================================================================

__all__ = [
    # === Enums ===
    "ActionType",
    "AgentPhase",
    "IntentType",
    "PlanStatus",
    "UrgencyLevel",
    # === Models ===
    "AgentAction",
    "AgentContext",
    "AgentEvent",
    "AgentPlan",
    "AgentResult",
    "AgentState",
    "UserIntent",
    # === State Management ===
    "StateManager",
    "StateManagerConfig",
    "StateSnapshot",
    "VALID_TRANSITIONS",
    "create_state_manager",
    "get_state_manager",
    # === Planning ===
    "PlanBuilder",
    "PlanExecutor",
    "PlanExecutorConfig",
    "create_plan_builder",
    "create_plan_executor",
    # === Controller ===
    "AgentController",
    "AgentControllerConfig",
    "IntentAnalyzer",
    "ResponseGenerator",
    "create_agent_controller",
    # === Service ===
    "AgentService",
    "AgentServiceConfig",
    "ServiceMetrics",
    "create_agent_service",
    "get_agent_service",
]


# =============================================================================
# Version
# =============================================================================

__version__ = "0.1.0"
