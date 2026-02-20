# =============================================================================
# MedeX - Plan Executor
# =============================================================================
"""
Plan execution for the MedeX agent.

Features:
- Action execution with retry logic
- Tool and RAG integration
- Parallel action support
- Execution metrics
- Error recovery
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from medex.agent.models import (
    ActionType,
    AgentAction,
    AgentContext,
    AgentPlan,
    IntentType,
    PlanStatus,
    UserIntent,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Configuration
# =============================================================================


@dataclass
class PlanExecutorConfig:
    """Configuration for plan executor."""

    # Execution limits
    max_actions: int = 10
    max_retries: int = 2
    action_timeout_ms: float = 10_000  # 10 seconds per action

    # Parallel execution
    enable_parallel: bool = True
    max_parallel_actions: int = 3

    # Tools
    enable_tools: bool = True
    tool_timeout_ms: float = 5_000

    # RAG
    enable_rag: bool = True
    rag_top_k: int = 5


# =============================================================================
# Action Handlers
# =============================================================================

# Type for action handlers
ActionHandler = Callable[[AgentAction, AgentContext], Awaitable[dict[str, Any]]]


# =============================================================================
# Plan Builder
# =============================================================================


class PlanBuilder:
    """Builds execution plans from user intent."""

    def __init__(self, config: PlanExecutorConfig) -> None:
        """Initialize plan builder."""
        self.config = config

    def build_plan(self, intent: UserIntent, context: AgentContext) -> AgentPlan:
        """Build execution plan based on intent analysis."""
        actions: list[AgentAction] = []

        # Step 1: Initial reasoning
        actions.append(
            AgentAction(
                action_type=ActionType.THINK,
                description=f"Analyze query: {context.query[:100]}...",
                tool_args={"query": context.query, "intent": intent.intent_type.value},
            )
        )

        # Step 2: Add actions based on intent type
        if intent.intent_type == IntentType.EMERGENCY:
            actions.extend(self._build_emergency_plan(intent, context))
        elif intent.intent_type == IntentType.MEDICATION:
            actions.extend(self._build_medication_plan(intent, context))
        elif intent.intent_type == IntentType.DIAGNOSTIC:
            actions.extend(self._build_diagnostic_plan(intent, context))
        elif intent.intent_type == IntentType.TREATMENT:
            actions.extend(self._build_treatment_plan(intent, context))
        elif intent.intent_type == IntentType.LAB_RESULT:
            actions.extend(self._build_lab_plan(intent, context))
        else:
            actions.extend(self._build_educational_plan(intent, context))

        # Step 3: RAG search for context
        if self.config.enable_rag and not intent.intent_type == IntentType.EMERGENCY:
            actions.append(
                AgentAction(
                    action_type=ActionType.SEARCH,
                    description="Search medical knowledge base",
                    tool_name="rag_search",
                    tool_args={
                        "query": context.query,
                        "top_k": self.config.rag_top_k,
                        "specialty": intent.specialty,
                    },
                )
            )

        # Step 4: Generate response
        actions.append(
            AgentAction(
                action_type=ActionType.RESPOND,
                description="Generate response based on gathered information",
                tool_args={
                    "intent_type": intent.intent_type.value,
                    "urgency": intent.urgency.value,
                },
            )
        )

        return AgentPlan(
            actions=actions,
            priority=intent.urgency,
            metadata={
                "intent_type": intent.intent_type.value,
                "confidence": intent.confidence,
                "created_at": datetime.utcnow().isoformat(),
            },
        )

    def _build_emergency_plan(
        self,
        intent: UserIntent,
        context: AgentContext,
    ) -> list[AgentAction]:
        """Build plan for emergency queries."""
        actions = []

        # Emergency triage - priority action
        actions.append(
            AgentAction(
                action_type=ActionType.TOOL_CALL,
                description="Evaluate emergency triage level",
                tool_name="triage_evaluator",
                tool_args={
                    "symptoms": intent.symptoms,
                    "vital_signs": {},
                },
            )
        )

        # Get emergency protocols if symptoms present
        if intent.symptoms:
            actions.append(
                AgentAction(
                    action_type=ActionType.TOOL_CALL,
                    description="Get emergency protocols",
                    tool_name="emergency_protocol",
                    tool_args={
                        "symptoms": intent.symptoms,
                        "conditions": intent.conditions,
                    },
                )
            )

        return actions

    def _build_medication_plan(
        self,
        intent: UserIntent,
        context: AgentContext,
    ) -> list[AgentAction]:
        """Build plan for medication queries."""
        actions = []

        medications = intent.medications or []

        # Drug information lookup
        for med in medications[:3]:  # Limit to 3 medications
            actions.append(
                AgentAction(
                    action_type=ActionType.TOOL_CALL,
                    description=f"Get information for {med}",
                    tool_name="drug_info",
                    tool_args={"drug_name": med},
                )
            )

        # Check interactions if multiple medications
        if len(medications) >= 2:
            actions.append(
                AgentAction(
                    action_type=ActionType.TOOL_CALL,
                    description="Check drug interactions",
                    tool_name="drug_interaction",
                    tool_args={"medications": medications},
                )
            )

        return actions

    def _build_diagnostic_plan(
        self,
        intent: UserIntent,
        context: AgentContext,
    ) -> list[AgentAction]:
        """Build plan for diagnostic queries."""
        actions = []

        # Symptom analysis
        if intent.symptoms:
            actions.append(
                AgentAction(
                    action_type=ActionType.TOOL_CALL,
                    description="Analyze symptoms",
                    tool_name="symptom_analyzer",
                    tool_args={
                        "symptoms": intent.symptoms,
                        "patient_age": intent.patient_age,
                        "patient_sex": intent.patient_sex,
                    },
                )
            )

        # Differential diagnosis
        actions.append(
            AgentAction(
                action_type=ActionType.TOOL_CALL,
                description="Generate differential diagnosis",
                tool_name="differential_diagnosis",
                tool_args={
                    "symptoms": intent.symptoms,
                    "conditions": intent.conditions,
                    "body_parts": intent.body_parts,
                },
            )
        )

        return actions

    def _build_treatment_plan(
        self,
        intent: UserIntent,
        context: AgentContext,
    ) -> list[AgentAction]:
        """Build plan for treatment queries."""
        actions = []

        # Get condition information
        for condition in intent.conditions[:2]:  # Limit
            actions.append(
                AgentAction(
                    action_type=ActionType.TOOL_CALL,
                    description=f"Get treatment for {condition}",
                    tool_name="treatment_lookup",
                    tool_args={"condition": condition},
                )
            )

        # Get guidelines if specialty available
        if intent.specialty:
            actions.append(
                AgentAction(
                    action_type=ActionType.TOOL_CALL,
                    description=f"Get clinical guidelines for {intent.specialty}",
                    tool_name="guideline_lookup",
                    tool_args={
                        "specialty": intent.specialty,
                        "conditions": intent.conditions,
                    },
                )
            )

        return actions

    def _build_lab_plan(
        self,
        intent: UserIntent,
        context: AgentContext,
    ) -> list[AgentAction]:
        """Build plan for lab result queries."""
        actions = []

        # Lab interpretation
        actions.append(
            AgentAction(
                action_type=ActionType.TOOL_CALL,
                description="Interpret lab values",
                tool_name="lab_interpreter",
                tool_args={
                    "query": context.query,
                    "patient_age": intent.patient_age,
                    "patient_sex": intent.patient_sex,
                },
            )
        )

        return actions

    def _build_educational_plan(
        self,
        intent: UserIntent,
        context: AgentContext,
    ) -> list[AgentAction]:
        """Build plan for educational/informational queries."""
        actions = []

        # For educational queries, primarily use RAG
        # No specific tool calls, will rely on RAG search
        actions.append(
            AgentAction(
                action_type=ActionType.THINK,
                description="Identify key concepts to explain",
                tool_args={
                    "topics": intent.topics,
                    "specialty": intent.specialty,
                },
            )
        )

        return actions


# =============================================================================
# Plan Executor
# =============================================================================


class PlanExecutor:
    """Executes agent plans."""

    def __init__(
        self,
        config: PlanExecutorConfig | None = None,
        tool_executor: Any = None,
        rag_service: Any = None,
    ) -> None:
        """Initialize plan executor."""
        self.config = config or PlanExecutorConfig()
        self.tool_executor = tool_executor
        self.rag_service = rag_service

        # Custom action handlers
        self._handlers: dict[ActionType, ActionHandler] = {}

        # Execution metrics
        self._metrics: dict[str, Any] = {}

    def set_tool_executor(self, executor: Any) -> None:
        """Set tool executor (late binding)."""
        self.tool_executor = executor

    def set_rag_service(self, service: Any) -> None:
        """Set RAG service (late binding)."""
        self.rag_service = service

    def register_handler(
        self,
        action_type: ActionType,
        handler: ActionHandler,
    ) -> None:
        """Register custom action handler."""
        self._handlers[action_type] = handler

    async def execute_plan(
        self,
        plan: AgentPlan,
        context: AgentContext,
    ) -> AgentPlan:
        """Execute all actions in the plan."""
        logger.info(f"Executing plan with {len(plan.actions)} actions")

        plan.start()
        self._metrics = {
            "started_at": datetime.utcnow().isoformat(),
            "actions_total": len(plan.actions),
            "actions_completed": 0,
            "actions_failed": 0,
        }

        try:
            if self.config.enable_parallel:
                await self._execute_parallel(plan, context)
            else:
                await self._execute_sequential(plan, context)

            # Check if all actions completed
            if plan.all_completed:
                plan.complete()
            elif plan.has_failed:
                plan.fail()

        except Exception as e:
            logger.error(f"Plan execution failed: {e}")
            plan.fail()
            raise

        self._metrics["completed_at"] = datetime.utcnow().isoformat()
        self._metrics["actions_completed"] = sum(
            1 for a in plan.actions if a.status.value == "completed"
        )
        self._metrics["actions_failed"] = sum(
            1 for a in plan.actions if a.status.value == "failed"
        )

        return plan

    async def _execute_sequential(
        self,
        plan: AgentPlan,
        context: AgentContext,
    ) -> None:
        """Execute actions sequentially."""
        for action in plan.actions:
            if plan.status == PlanStatus.CANCELLED:
                break

            await self._execute_action(action, context)

            # Update context with action results
            self._update_context(action, context)

    async def _execute_parallel(
        self,
        plan: AgentPlan,
        context: AgentContext,
    ) -> None:
        """Execute actions in parallel where possible."""
        # Group actions by dependencies
        # For now, execute THINK actions first, then parallelize TOOL_CALL/SEARCH

        # Phase 1: Execute THINK actions
        think_actions = [a for a in plan.actions if a.action_type == ActionType.THINK]
        for action in think_actions:
            await self._execute_action(action, context)

        # Phase 2: Parallel TOOL_CALL and SEARCH
        parallel_actions = [
            a
            for a in plan.actions
            if a.action_type in {ActionType.TOOL_CALL, ActionType.SEARCH}
        ]

        # Execute in batches
        for i in range(0, len(parallel_actions), self.config.max_parallel_actions):
            batch = parallel_actions[i : i + self.config.max_parallel_actions]
            tasks = [self._execute_action(a, context) for a in batch]
            await asyncio.gather(*tasks, return_exceptions=True)

            # Update context
            for action in batch:
                self._update_context(action, context)

        # Phase 3: Execute RESPOND actions last
        respond_actions = [
            a for a in plan.actions if a.action_type == ActionType.RESPOND
        ]
        for action in respond_actions:
            await self._execute_action(action, context)

    async def _execute_action(
        self,
        action: AgentAction,
        context: AgentContext,
    ) -> None:
        """Execute a single action."""
        logger.info(
            f"Executing action: {action.action_type.value} - {action.description}"
        )

        action.start()

        try:
            # Check for custom handler
            if action.action_type in self._handlers:
                handler = self._handlers[action.action_type]
                result = await handler(action, context)
            else:
                result = await self._default_handler(action, context)

            action.complete(result)
            logger.info(f"Action completed: {action.action_type.value}")

        except asyncio.TimeoutError:
            action.fail(f"Action timed out after {self.config.action_timeout_ms}ms")
            logger.warning(f"Action timed out: {action.description}")

        except Exception as e:
            action.fail(str(e))
            logger.error(f"Action failed: {action.description} - {e}")

            # Retry if configured
            if action.retry_count < self.config.max_retries:
                action.retry_count += 1
                logger.info(f"Retrying action (attempt {action.retry_count})")
                await self._execute_action(action, context)

    async def _default_handler(
        self,
        action: AgentAction,
        context: AgentContext,
    ) -> dict[str, Any]:
        """Default action handler."""
        if action.action_type == ActionType.THINK:
            return await self._handle_think(action, context)

        elif action.action_type == ActionType.TOOL_CALL:
            return await self._handle_tool_call(action, context)

        elif action.action_type == ActionType.SEARCH:
            return await self._handle_search(action, context)

        elif action.action_type == ActionType.RESPOND:
            return await self._handle_respond(action, context)

        elif action.action_type == ActionType.CLARIFY:
            return await self._handle_clarify(action, context)

        elif action.action_type == ActionType.ESCALATE:
            return await self._handle_escalate(action, context)

        elif action.action_type == ActionType.DEFER:
            return await self._handle_defer(action, context)

        else:
            return {"status": "unknown_action_type"}

    async def _handle_think(
        self,
        action: AgentAction,
        context: AgentContext,
    ) -> dict[str, Any]:
        """Handle THINK action - reasoning step."""
        # THINK actions are markers for the LLM to reason
        # They don't execute anything, just track the step
        return {
            "status": "thought_recorded",
            "query": action.tool_args.get("query", ""),
            "context_size": len(context.rag_context) if context.rag_context else 0,
        }

    async def _handle_tool_call(
        self,
        action: AgentAction,
        context: AgentContext,
    ) -> dict[str, Any]:
        """Handle TOOL_CALL action."""
        if not self.tool_executor:
            return {"error": "Tool executor not configured"}

        tool_name = action.tool_name
        tool_args = action.tool_args

        if not tool_name:
            return {"error": "No tool name specified"}

        try:
            # Execute tool with timeout
            result = await asyncio.wait_for(
                self.tool_executor.execute(tool_name, tool_args),
                timeout=self.config.tool_timeout_ms / 1000,
            )

            # Store result in context
            context.add_tool_result(tool_name, result)

            return {
                "tool": tool_name,
                "result": result,
                "success": True,
            }

        except asyncio.TimeoutError:
            return {"error": f"Tool {tool_name} timed out"}
        except Exception as e:
            return {"error": str(e)}

    async def _handle_search(
        self,
        action: AgentAction,
        context: AgentContext,
    ) -> dict[str, Any]:
        """Handle SEARCH action - RAG search."""
        if not self.rag_service:
            return {"error": "RAG service not configured"}

        query = action.tool_args.get("query", context.query)
        top_k = action.tool_args.get("top_k", self.config.rag_top_k)

        try:
            results = await self.rag_service.search(
                query=query,
                top_k=top_k,
            )

            # Update context with RAG results
            context.rag_context = results.get("context", "")
            context.rag_sources = results.get("sources", [])

            return {
                "query": query,
                "results_count": len(results.get("sources", [])),
                "success": True,
            }

        except Exception as e:
            return {"error": str(e)}

    async def _handle_respond(
        self,
        action: AgentAction,
        context: AgentContext,
    ) -> dict[str, Any]:
        """Handle RESPOND action - final response generation marker."""
        # RESPOND is a marker that response should be generated
        # Actual generation is handled by the controller
        return {
            "status": "ready_to_respond",
            "intent_type": action.tool_args.get("intent_type"),
            "urgency": action.tool_args.get("urgency"),
        }

    async def _handle_clarify(
        self,
        action: AgentAction,
        context: AgentContext,
    ) -> dict[str, Any]:
        """Handle CLARIFY action - need more information."""
        return {
            "status": "clarification_needed",
            "questions": action.tool_args.get("questions", []),
        }

    async def _handle_escalate(
        self,
        action: AgentAction,
        context: AgentContext,
    ) -> dict[str, Any]:
        """Handle ESCALATE action - escalate to human/specialist."""
        return {
            "status": "escalation_required",
            "reason": action.tool_args.get("reason"),
            "specialist": action.tool_args.get("specialist"),
        }

    async def _handle_defer(
        self,
        action: AgentAction,
        context: AgentContext,
    ) -> dict[str, Any]:
        """Handle DEFER action - defer response."""
        return {
            "status": "deferred",
            "reason": action.tool_args.get("reason"),
        }

    def _update_context(
        self,
        action: AgentAction,
        context: AgentContext,
    ) -> None:
        """Update context with action results."""
        if not action.result:
            return

        # For tool calls, result is already added in handler
        # Here we can add any additional context processing
        pass

    def get_metrics(self) -> dict[str, Any]:
        """Get execution metrics."""
        return self._metrics.copy()


# =============================================================================
# Factory Functions
# =============================================================================


def create_plan_builder(
    config: PlanExecutorConfig | None = None,
) -> PlanBuilder:
    """Create plan builder."""
    return PlanBuilder(config or PlanExecutorConfig())


def create_plan_executor(
    config: PlanExecutorConfig | None = None,
    tool_executor: Any = None,
    rag_service: Any = None,
) -> PlanExecutor:
    """Create plan executor."""
    return PlanExecutor(
        config=config,
        tool_executor=tool_executor,
        rag_service=rag_service,
    )
