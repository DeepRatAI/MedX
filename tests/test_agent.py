# =============================================================================
# MedeX - Agent Tests
# =============================================================================
"""
Comprehensive tests for the Agent Core module.

Tests cover:
- Models and data structures
- State machine transitions
- Plan building and execution
- Intent analysis
- Controller orchestration
- Service façade
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from medex.agent.controller import (
    AgentControllerConfig,
    IntentAnalyzer,
    create_agent_controller,
)
from medex.agent.models import (
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
    create_plan_builder,
    create_plan_executor,
)
from medex.agent.service import (
    AgentServiceConfig,
    ServiceMetrics,
    create_agent_service,
)
from medex.agent.state import (
    VALID_TRANSITIONS,
    StateManager,
    StateManagerConfig,
    create_state_manager,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def sample_context() -> AgentContext:
    """Create sample agent context."""
    return AgentContext(
        query="What are the symptoms of diabetes?",
        session_id="test-session-123",
        user_id="user-456",
        metadata={"source": "test"},
    )


@pytest.fixture
def sample_intent() -> UserIntent:
    """Create sample user intent."""
    return UserIntent(
        raw_query="What are the symptoms of diabetes?",
        intent_type=IntentType.EDUCATIONAL,
        urgency=UrgencyLevel.LOW,
        confidence=0.8,
        symptoms=[],
        medications=[],
        conditions=["diabetes"],
        specialty="endocrinology",
    )


@pytest.fixture
def sample_plan() -> AgentPlan:
    """Create sample execution plan."""
    actions = [
        AgentAction(
            action_type=ActionType.THINK,
            description="Analyze query",
        ),
        AgentAction(
            action_type=ActionType.SEARCH,
            description="Search knowledge base",
            tool_name="rag_search",
            tool_args={"query": "diabetes symptoms"},
        ),
        AgentAction(
            action_type=ActionType.RESPOND,
            description="Generate response",
        ),
    ]
    return AgentPlan(actions=actions)


@pytest.fixture
def state_manager() -> StateManager:
    """Create state manager."""
    return create_state_manager(
        StateManagerConfig(
            max_iterations=10,
            max_phase_duration_ms=30_000,
        )
    )


@pytest.fixture
def plan_builder() -> PlanBuilder:
    """Create plan builder."""
    return create_plan_builder()


@pytest.fixture
def plan_executor() -> PlanExecutor:
    """Create plan executor."""
    return create_plan_executor()


@pytest.fixture
def intent_analyzer() -> IntentAnalyzer:
    """Create intent analyzer."""
    return IntentAnalyzer()


# =============================================================================
# Model Tests
# =============================================================================


class TestAgentModels:
    """Tests for agent data models."""

    def test_agent_action_creation(self):
        """Test AgentAction creation."""
        action = AgentAction(
            action_type=ActionType.TOOL_CALL,
            description="Get drug info",
            tool_name="drug_info",
            tool_args={"drug_name": "aspirin"},
        )

        assert action.action_type == ActionType.TOOL_CALL
        assert action.tool_name == "drug_info"
        assert action.status.value == "pending"
        assert not action.is_completed

    def test_agent_action_lifecycle(self):
        """Test action start, complete, fail."""
        action = AgentAction(
            action_type=ActionType.TOOL_CALL,
            description="Test action",
        )

        # Start
        action.start()
        assert action.status.value == "in_progress"
        assert action.started_at is not None

        # Complete
        action.complete({"result": "success"})
        assert action.status.value == "completed"
        assert action.is_completed
        assert action.result == {"result": "success"}

    def test_agent_action_failure(self):
        """Test action failure."""
        action = AgentAction(
            action_type=ActionType.TOOL_CALL,
            description="Failing action",
        )

        action.start()
        action.fail("Connection timeout")

        assert action.status.value == "failed"
        assert not action.is_completed
        assert action.error == "Connection timeout"

    def test_agent_plan_creation(self):
        """Test AgentPlan creation."""
        actions = [
            AgentAction(action_type=ActionType.THINK, description="Think"),
            AgentAction(action_type=ActionType.RESPOND, description="Respond"),
        ]
        plan = AgentPlan(actions=actions)

        assert len(plan.actions) == 2
        assert plan.status == PlanStatus.PENDING
        assert plan.progress == 0.0

    def test_agent_plan_progress(self):
        """Test plan progress tracking."""
        actions = [
            AgentAction(action_type=ActionType.THINK, description="Step 1"),
            AgentAction(action_type=ActionType.SEARCH, description="Step 2"),
            AgentAction(action_type=ActionType.RESPOND, description="Step 3"),
        ]
        plan = AgentPlan(actions=actions)

        # Complete first action
        actions[0].start()
        actions[0].complete({})
        assert plan.progress == pytest.approx(1 / 3, rel=0.01)

        # Complete second
        actions[1].start()
        actions[1].complete({})
        assert plan.progress == pytest.approx(2 / 3, rel=0.01)

        # Complete all
        actions[2].start()
        actions[2].complete({})
        assert plan.all_completed

    def test_user_intent(self):
        """Test UserIntent creation."""
        intent = UserIntent(
            raw_query="I have chest pain and shortness of breath",
            intent_type=IntentType.EMERGENCY,
            urgency=UrgencyLevel.CRITICAL,
            confidence=0.95,
            symptoms=["chest pain", "shortness of breath"],
            body_parts=["chest"],
            specialty="cardiology",
        )

        assert intent.intent_type == IntentType.EMERGENCY
        assert intent.urgency == UrgencyLevel.CRITICAL
        assert len(intent.symptoms) == 2

    def test_agent_context(self):
        """Test AgentContext creation and tool results."""
        context = AgentContext(
            query="Drug interaction check",
            session_id="sess-123",
        )

        context.add_tool_result("drug_interaction", {"severity": "high"})
        assert "drug_interaction" in context.tool_results
        assert context.tool_results["drug_interaction"]["severity"] == "high"

    def test_agent_state_transitions(self):
        """Test AgentState phase transitions."""
        context = AgentContext(query="test", session_id="s1")
        state = AgentState(
            phase=AgentPhase.IDLE,
            context=context,
        )

        state.transition(AgentPhase.RECEIVING)
        assert state.phase == AgentPhase.RECEIVING

        state.transition(AgentPhase.ANALYZING)
        assert state.phase == AgentPhase.ANALYZING

    def test_agent_state_iteration_limit(self):
        """Test state iteration safety limit."""
        context = AgentContext(query="test", session_id="s1")
        state = AgentState(
            phase=AgentPhase.IDLE,
            context=context,
            max_iterations=5,
        )

        for _ in range(5):
            state.increment_iteration()

        assert state.should_stop
        assert state.iteration_count == 5

    def test_agent_event_sse_format(self):
        """Test AgentEvent SSE formatting."""
        event = AgentEvent(
            event_type="phase_transition",
            phase=AgentPhase.EXECUTING,
            data={"action": "search"},
            sequence=42,
        )

        sse = event.to_sse()
        assert "event: phase_transition" in sse
        assert "id: 42" in sse
        assert "data:" in sse

    def test_agent_result(self):
        """Test AgentResult creation."""
        result = AgentResult(
            content="Diabetes symptoms include...",
            success=True,
            intent_type=IntentType.EDUCATIONAL,
            sources=["medical_textbook.pdf"],
            latency_ms=250.5,
        )

        assert result.success
        assert result.latency_ms == 250.5
        assert "medical_textbook.pdf" in result.sources


# =============================================================================
# State Manager Tests
# =============================================================================


class TestStateManager:
    """Tests for StateManager."""

    def test_state_initialization(self, state_manager, sample_context):
        """Test state initialization."""
        state = state_manager.initialize(sample_context)

        assert state is not None
        assert state.phase == AgentPhase.IDLE
        assert state_manager.is_active

    @pytest.mark.asyncio
    async def test_valid_transition(self, state_manager, sample_context):
        """Test valid phase transition."""
        state_manager.initialize(sample_context)

        result = await state_manager.transition(AgentPhase.RECEIVING)
        assert result
        assert state_manager.phase == AgentPhase.RECEIVING

    @pytest.mark.asyncio
    async def test_invalid_transition(self, state_manager, sample_context):
        """Test invalid phase transition is rejected."""
        state_manager.initialize(sample_context)

        # Try to skip from IDLE to EXECUTING (invalid)
        result = await state_manager.transition(AgentPhase.EXECUTING)
        assert not result
        assert state_manager.phase == AgentPhase.IDLE

    @pytest.mark.asyncio
    async def test_transition_sequence(self, state_manager, sample_context):
        """Test full transition sequence."""
        state_manager.initialize(sample_context)

        transitions = [
            AgentPhase.RECEIVING,
            AgentPhase.ANALYZING,
            AgentPhase.PLANNING,
            AgentPhase.EXECUTING,
            AgentPhase.GENERATING,
            AgentPhase.COMPLETED,
        ]

        for phase in transitions:
            result = await state_manager.transition(phase)
            assert result, f"Failed to transition to {phase.value}"
            assert state_manager.phase == phase

    def test_valid_transitions_map(self):
        """Test VALID_TRANSITIONS coverage."""
        # Every phase should have transitions defined
        for phase in AgentPhase:
            assert phase in VALID_TRANSITIONS

        # COMPLETED should be terminal
        assert VALID_TRANSITIONS[AgentPhase.COMPLETED] == set()

    def test_state_snapshots(self, state_manager, sample_context):
        """Test state snapshot creation."""
        config = StateManagerConfig(enable_snapshots=True, snapshot_interval=1)
        sm = StateManager(config)
        sm.initialize(sample_context)

        snapshots = sm.get_snapshots()
        assert len(snapshots) >= 1  # Initial snapshot

    def test_event_emission(self, state_manager, sample_context):
        """Test event emission."""
        events = []
        state_manager.add_event_handler(lambda e: events.append(e))

        state_manager.initialize(sample_context)

        assert len(events) >= 1
        assert events[0].event_type == "state_initialized"

    def test_force_error(self, state_manager, sample_context):
        """Test force error state."""
        state_manager.initialize(sample_context)
        state_manager.force_error("Test error")

        assert state_manager.phase == AgentPhase.ERROR
        assert state_manager.state.last_error == "Test error"


# =============================================================================
# Plan Builder Tests
# =============================================================================


class TestPlanBuilder:
    """Tests for PlanBuilder."""

    def test_educational_plan(self, plan_builder, sample_intent, sample_context):
        """Test plan for educational intent."""
        plan = plan_builder.build_plan(sample_intent, sample_context)

        assert len(plan.actions) >= 2
        assert plan.status == PlanStatus.PENDING

        # Should have THINK and RESPOND at minimum
        action_types = [a.action_type for a in plan.actions]
        assert ActionType.THINK in action_types
        assert ActionType.RESPOND in action_types

    def test_emergency_plan(self, plan_builder, sample_context):
        """Test plan for emergency intent."""
        emergency_intent = UserIntent(
            raw_query="Severe chest pain",
            intent_type=IntentType.EMERGENCY,
            urgency=UrgencyLevel.CRITICAL,
            confidence=0.95,
            symptoms=["chest pain"],
        )

        plan = plan_builder.build_plan(emergency_intent, sample_context)

        # Should have triage tool call
        tool_actions = [
            a for a in plan.actions if a.action_type == ActionType.TOOL_CALL
        ]
        assert len(tool_actions) >= 1

        tool_names = [a.tool_name for a in tool_actions]
        assert "triage_evaluator" in tool_names

    def test_medication_plan(self, plan_builder, sample_context):
        """Test plan for medication intent."""
        med_intent = UserIntent(
            raw_query="Drug interaction aspirin ibuprofen",
            intent_type=IntentType.MEDICATION,
            urgency=UrgencyLevel.MEDIUM,
            confidence=0.85,
            medications=["aspirin", "ibuprofen"],
        )

        plan = plan_builder.build_plan(med_intent, sample_context)

        # Should have drug info and interaction checks
        tool_actions = [
            a for a in plan.actions if a.action_type == ActionType.TOOL_CALL
        ]
        assert len(tool_actions) >= 1


# =============================================================================
# Plan Executor Tests
# =============================================================================


class TestPlanExecutor:
    """Tests for PlanExecutor."""

    @pytest.mark.asyncio
    async def test_plan_execution(self, plan_executor, sample_plan, sample_context):
        """Test basic plan execution."""
        executed = await plan_executor.execute_plan(sample_plan, sample_context)

        assert executed.status in {PlanStatus.COMPLETED, PlanStatus.IN_PROGRESS}

    @pytest.mark.asyncio
    async def test_action_execution(self, plan_executor, sample_context):
        """Test single action execution."""
        action = AgentAction(
            action_type=ActionType.THINK,
            description="Test thinking",
            tool_args={"query": "test"},
        )

        await plan_executor._execute_action(action, sample_context)

        assert action.is_completed
        assert action.result is not None

    @pytest.mark.asyncio
    async def test_tool_call_without_executor(self, plan_executor, sample_context):
        """Test tool call when no executor configured."""
        action = AgentAction(
            action_type=ActionType.TOOL_CALL,
            description="Call missing tool",
            tool_name="some_tool",
            tool_args={},
        )

        await plan_executor._execute_action(action, sample_context)

        # Should complete with error result
        assert action.is_completed
        assert "error" in action.result

    @pytest.mark.asyncio
    async def test_custom_handler(self, plan_executor, sample_context):
        """Test custom action handler."""
        custom_result = {"custom": True}

        async def custom_handler(action, context):
            return custom_result

        plan_executor.register_handler(ActionType.THINK, custom_handler)

        action = AgentAction(
            action_type=ActionType.THINK,
            description="Custom handled",
        )

        await plan_executor._execute_action(action, sample_context)

        assert action.result == custom_result


# =============================================================================
# Intent Analyzer Tests
# =============================================================================


class TestIntentAnalyzer:
    """Tests for IntentAnalyzer."""

    def test_emergency_detection(self, intent_analyzer):
        """Test emergency intent detection."""
        intent = intent_analyzer.analyze("I have severe chest pain and can't breathe")

        assert intent.intent_type == IntentType.EMERGENCY
        assert intent.urgency == UrgencyLevel.CRITICAL

    def test_medication_detection(self, intent_analyzer):
        """Test medication intent detection."""
        intent = intent_analyzer.analyze(
            "What is the dosage for ibuprofen? Any side effects?"
        )

        assert intent.intent_type == IntentType.MEDICATION
        assert "ibuprofen" in intent.medications

    def test_diagnostic_detection(self, intent_analyzer):
        """Test diagnostic intent detection."""
        intent = intent_analyzer.analyze(
            "I have a headache and fever. What could this be?"
        )

        assert intent.intent_type == IntentType.DIAGNOSTIC
        assert "headache" in intent.symptoms or "fever" in intent.symptoms

    def test_educational_fallback(self, intent_analyzer):
        """Test educational intent as fallback."""
        intent = intent_analyzer.analyze("Explain how the cardiovascular system works")

        assert intent.intent_type == IntentType.EDUCATIONAL
        assert intent.urgency == UrgencyLevel.LOW

    def test_spanish_detection(self, intent_analyzer):
        """Test Spanish language detection."""
        intent = intent_analyzer.analyze("¿Cuáles son los síntomas de la diabetes?")

        assert intent.language == "es"

    def test_specialty_detection(self, intent_analyzer):
        """Test medical specialty detection."""
        intent = intent_analyzer.analyze("My heart rate is irregular")

        assert intent.specialty == "cardiology"


# =============================================================================
# Controller Tests
# =============================================================================


class TestAgentController:
    """Tests for AgentController."""

    @pytest.fixture
    def controller(self):
        """Create test controller."""
        return create_agent_controller(
            AgentControllerConfig(
                max_iterations=5,
                require_disclaimer=False,  # Disable for testing
            )
        )

    @pytest.mark.asyncio
    async def test_basic_processing(self, controller):
        """Test basic query processing."""
        result = await controller.process(
            query="What is diabetes?",
            session_id="test-session",
        )

        assert result is not None
        assert isinstance(result, AgentResult)
        assert result.latency_ms > 0

    @pytest.mark.asyncio
    async def test_emergency_handling(self, controller):
        """Test emergency query fast-path."""
        result = await controller.process(
            query="Emergency! Severe chest pain and difficulty breathing!",
            session_id="test-session",
        )

        assert result is not None
        assert "emergency" in result.content.lower() or "911" in result.content

    @pytest.mark.asyncio
    async def test_streaming_events(self, controller):
        """Test streaming event generation."""
        events = []

        async for event in controller.process_stream(
            query="Explain hypertension",
            session_id="test-session",
        ):
            events.append(event)

        assert len(events) > 0
        assert any(e.event_type == "completed" for e in events)

    @pytest.mark.asyncio
    async def test_service_integration(self, controller):
        """Test with mock services."""
        mock_llm = AsyncMock()
        mock_llm.query = AsyncMock(return_value=MagicMock(content="Mock LLM response"))

        controller.set_llm_service(mock_llm)

        result = await controller.process(
            query="Test query",
            session_id="test",
        )

        assert result is not None


# =============================================================================
# Service Tests
# =============================================================================


class TestAgentService:
    """Tests for AgentService."""

    @pytest.fixture
    def service(self):
        """Create test service."""
        return create_agent_service(
            AgentServiceConfig(
                max_concurrent_queries=5,
                query_timeout_seconds=10.0,
            )
        )

    @pytest.mark.asyncio
    async def test_service_lifecycle(self, service):
        """Test service init and shutdown."""
        await service.initialize()
        assert service._initialized

        await service.shutdown()
        assert not service._initialized

    @pytest.mark.asyncio
    async def test_query(self, service):
        """Test query processing."""
        await service.initialize()

        result = await service.query(
            query="What causes headaches?",
            session_id="test-session",
        )

        assert result is not None
        assert isinstance(result, AgentResult)

    @pytest.mark.asyncio
    async def test_metrics(self, service):
        """Test metrics collection."""
        await service.initialize()

        await service.query("Test query 1", session_id="s1")
        await service.query("Test query 2", session_id="s2")

        metrics = service.get_metrics()
        assert metrics["queries_total"] >= 2

    @pytest.mark.asyncio
    async def test_health_check(self, service):
        """Test health check."""
        await service.initialize()

        health = await service.health_check()
        assert health["status"] in {"healthy", "degraded"}
        assert health["initialized"]

    @pytest.mark.asyncio
    async def test_concurrent_queries(self, service):
        """Test concurrent query handling."""
        await service.initialize()

        queries = [{"query": f"Query {i}", "session_id": f"s{i}"} for i in range(3)]

        results = await service.batch_query(queries)
        assert len(results) == 3

    @pytest.mark.asyncio
    async def test_session_management(self, service):
        """Test session creation."""
        await service.initialize()

        session_id = await service.create_session(user_id="user-123")
        assert session_id is not None

    @pytest.mark.asyncio
    async def test_is_ready(self, service):
        """Test ready state check."""
        await service.initialize()
        assert service.is_ready


# =============================================================================
# Service Metrics Tests
# =============================================================================


class TestServiceMetrics:
    """Tests for ServiceMetrics."""

    def test_record_query(self):
        """Test query recording."""
        metrics = ServiceMetrics()

        metrics.record_query(success=True, latency_ms=100)
        metrics.record_query(success=True, latency_ms=200)
        metrics.record_query(success=False, latency_ms=50)

        assert metrics.queries_total == 3
        assert metrics.queries_success == 2
        assert metrics.queries_failed == 1
        assert metrics.avg_latency_ms == pytest.approx((100 + 200 + 50) / 3, rel=0.01)

    def test_latency_tracking(self):
        """Test min/max latency."""
        metrics = ServiceMetrics()

        metrics.record_query(True, 100)
        metrics.record_query(True, 50)
        metrics.record_query(True, 200)

        assert metrics.min_latency_ms == 50
        assert metrics.max_latency_ms == 200

    def test_concurrent_tracking(self):
        """Test concurrent query tracking."""
        metrics = ServiceMetrics()

        metrics.start_query()
        metrics.start_query()
        assert metrics.active_queries == 2
        assert metrics.peak_concurrent == 2

        metrics.end_query()
        assert metrics.active_queries == 1
        assert metrics.peak_concurrent == 2  # Peak unchanged

    def test_to_dict(self):
        """Test metrics serialization."""
        metrics = ServiceMetrics()
        metrics.record_query(True, 100)

        data = metrics.to_dict()
        assert "queries_total" in data
        assert "success_rate" in data
        assert "uptime_seconds" in data


# =============================================================================
# Integration Tests
# =============================================================================


class TestAgentIntegration:
    """Integration tests for the full agent system."""

    @pytest.mark.asyncio
    async def test_full_flow(self):
        """Test complete agent flow."""
        # Create service with all components
        service = create_agent_service(
            AgentServiceConfig(
                max_iterations=5,
                enable_streaming=True,
            )
        )

        await service.initialize()

        # Process query
        result = await service.query(
            query="What are the symptoms of type 2 diabetes?",
            session_id="integration-test",
            user_id="test-user",
        )

        assert result is not None
        assert isinstance(result.content, str)
        assert len(result.content) > 0

        # Check metrics
        metrics = service.get_metrics()
        assert metrics["queries_total"] >= 1

        await service.shutdown()

    @pytest.mark.asyncio
    async def test_multi_turn(self):
        """Test multi-turn conversation."""
        service = create_agent_service()
        await service.initialize()

        session_id = await service.create_session(user_id="user-1")

        # Turn 1
        result1 = await service.query(
            query="What is hypertension?",
            session_id=session_id,
        )
        assert result1.success or result1.content  # May not have LLM

        # Turn 2
        result2 = await service.query(
            query="What are the treatment options?",
            session_id=session_id,
        )
        assert result2 is not None

        await service.shutdown()


# =============================================================================
# Run Tests
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
