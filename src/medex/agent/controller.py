# =============================================================================
# MedeX - Agent Controller
# =============================================================================
"""
Main controller for the MedeX agent.

Implements ReAct-style agent loop:
1. Receive query
2. Analyze intent
3. Plan actions
4. Execute actions (tools, RAG)
5. Generate response
6. Review and complete

Features:
- ReAct loop orchestration
- Multi-turn conversation support
- Streaming response generation
- Safety limits and guardrails
- Full observability
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass
from typing import Any

from medex.agent.models import (
    AgentContext,
    AgentEvent,
    AgentPhase,
    AgentPlan,
    AgentResult,
    IntentType,
    UrgencyLevel,
    UserIntent,
)
from medex.agent.planner import (
    PlanExecutorConfig,
    create_plan_builder,
    create_plan_executor,
)
from medex.agent.state import StateManagerConfig, create_state_manager

logger = logging.getLogger(__name__)


# =============================================================================
# Configuration
# =============================================================================


@dataclass
class AgentControllerConfig:
    """Configuration for agent controller."""

    # State manager
    max_iterations: int = 10
    max_phase_duration_ms: float = 30_000
    max_total_duration_ms: float = 120_000

    # Plan executor
    max_actions: int = 10
    max_retries: int = 2
    enable_parallel: bool = True

    # Intent analysis
    default_urgency: UrgencyLevel = UrgencyLevel.MEDIUM
    enable_emergency_detection: bool = True

    # Response generation
    enable_streaming: bool = True
    chunk_size: int = 50

    # Safety
    require_disclaimer: bool = True
    max_response_length: int = 4000


# =============================================================================
# Intent Analyzer
# =============================================================================


class IntentAnalyzer:
    """Analyzes user queries to determine intent."""

    # Keyword patterns for intent detection
    EMERGENCY_KEYWORDS = {
        "emergency",
        "urgent",
        "critical",
        "severe",
        "chest pain",
        "stroke",
        "heart attack",
        "bleeding",
        "unconscious",
        "can't breathe",
        "seizure",
        "overdose",
        "suicide",
        "emergencia",
        "urgente",
        "dolor de pecho",
        "infarto",
    }

    MEDICATION_KEYWORDS = {
        "medication",
        "drug",
        "dose",
        "dosage",
        "prescription",
        "side effect",
        "interaction",
        "pill",
        "tablet",
        "medicamento",
        "medicina",
        "dosis",
        "pastilla",
    }

    DIAGNOSTIC_KEYWORDS = {
        "symptoms",
        "diagnosis",
        "what could",
        "do i have",
        "pain",
        "hurts",
        "swelling",
        "fever",
        "cough",
        "síntomas",
        "diagnóstico",
        "dolor",
        "fiebre",
    }

    TREATMENT_KEYWORDS = {
        "treatment",
        "how to treat",
        "therapy",
        "cure",
        "what to do for",
        "management",
        "care for",
        "tratamiento",
        "cómo tratar",
        "terapia",
    }

    LAB_KEYWORDS = {
        "lab result",
        "blood test",
        "lab value",
        "normal range",
        "glucose",
        "hemoglobin",
        "cholesterol",
        "creatinine",
        "resultado",
        "análisis",
        "glucosa",
        "hemoglobina",
    }

    def analyze(self, query: str, history: list[dict] | None = None) -> UserIntent:
        """Analyze query and return intent."""
        query_lower = query.lower()

        # Detect intent type
        intent_type = self._detect_intent_type(query_lower)

        # Detect urgency
        urgency = self._detect_urgency(query_lower, intent_type)

        # Extract entities
        symptoms = self._extract_symptoms(query_lower)
        medications = self._extract_medications(query_lower)
        conditions = self._extract_conditions(query_lower)
        body_parts = self._extract_body_parts(query_lower)

        # Detect specialty
        specialty = self._detect_specialty(query_lower, symptoms, conditions)

        # Calculate confidence
        confidence = self._calculate_confidence(query_lower, intent_type)

        return UserIntent(
            raw_query=query,
            intent_type=intent_type,
            urgency=urgency,
            confidence=confidence,
            symptoms=symptoms,
            medications=medications,
            conditions=conditions,
            body_parts=body_parts,
            specialty=specialty,
            language=self._detect_language(query),
        )

    def _detect_intent_type(self, query: str) -> IntentType:
        """Detect primary intent type."""
        # Priority order: emergency > medication > diagnostic > treatment > lab > educational

        if any(kw in query for kw in self.EMERGENCY_KEYWORDS):
            return IntentType.EMERGENCY

        if any(kw in query for kw in self.MEDICATION_KEYWORDS):
            return IntentType.MEDICATION

        if any(kw in query for kw in self.DIAGNOSTIC_KEYWORDS):
            return IntentType.DIAGNOSTIC

        if any(kw in query for kw in self.TREATMENT_KEYWORDS):
            return IntentType.TREATMENT

        if any(kw in query for kw in self.LAB_KEYWORDS):
            return IntentType.LAB_RESULT

        return IntentType.EDUCATIONAL

    def _detect_urgency(
        self,
        query: str,
        intent_type: IntentType,
    ) -> UrgencyLevel:
        """Detect urgency level."""
        if intent_type == IntentType.EMERGENCY:
            return UrgencyLevel.CRITICAL

        urgent_words = {"urgent", "asap", "immediately", "right now", "urgente"}
        if any(w in query for w in urgent_words):
            return UrgencyLevel.HIGH

        if intent_type in {IntentType.DIAGNOSTIC, IntentType.MEDICATION}:
            return UrgencyLevel.MEDIUM

        return UrgencyLevel.LOW

    def _extract_symptoms(self, query: str) -> list[str]:
        """Extract symptoms from query."""
        # Simplified extraction - in production use NER model
        symptom_patterns = [
            "pain",
            "ache",
            "fever",
            "cough",
            "nausea",
            "vomiting",
            "dizziness",
            "headache",
            "fatigue",
            "swelling",
            "rash",
            "dolor",
            "fiebre",
            "tos",
            "náusea",
            "mareo",
            "fatiga",
        ]
        return [s for s in symptom_patterns if s in query]

    def _extract_medications(self, query: str) -> list[str]:
        """Extract medication names from query."""
        # Simplified - in production use drug name database
        common_meds = [
            "aspirin",
            "ibuprofen",
            "paracetamol",
            "acetaminophen",
            "metformin",
            "lisinopril",
            "amlodipine",
            "omeprazole",
            "atorvastatin",
            "levothyroxine",
            "metoprolol",
        ]
        return [m for m in common_meds if m in query]

    def _extract_conditions(self, query: str) -> list[str]:
        """Extract condition names from query."""
        # Simplified extraction
        conditions = [
            "diabetes",
            "hypertension",
            "asthma",
            "copd",
            "arthritis",
            "depression",
            "anxiety",
            "heart disease",
            "cancer",
        ]
        return [c for c in conditions if c in query]

    def _extract_body_parts(self, query: str) -> list[str]:
        """Extract body parts from query."""
        body_parts = [
            "head",
            "chest",
            "stomach",
            "back",
            "arm",
            "leg",
            "throat",
            "eye",
            "ear",
            "heart",
            "lung",
            "liver",
            "cabeza",
            "pecho",
            "estómago",
            "espalda",
            "brazo",
        ]
        return [b for b in body_parts if b in query]

    def _detect_specialty(
        self,
        query: str,
        symptoms: list[str],
        conditions: list[str],
    ) -> str | None:
        """Detect relevant medical specialty."""
        specialty_keywords = {
            "cardiology": ["heart", "chest pain", "palpitation", "blood pressure"],
            "neurology": ["headache", "seizure", "dizziness", "stroke"],
            "gastroenterology": ["stomach", "digestion", "nausea", "liver"],
            "pulmonology": ["lung", "breath", "cough", "asthma"],
            "endocrinology": ["diabetes", "thyroid", "hormone"],
            "psychiatry": ["depression", "anxiety", "mental", "mood"],
        }

        for specialty, keywords in specialty_keywords.items():
            if any(kw in query for kw in keywords):
                return specialty
            if any(kw in symptoms for kw in keywords):
                return specialty
            if any(kw in conditions for kw in keywords):
                return specialty

        return None

    def _calculate_confidence(self, query: str, intent_type: IntentType) -> float:
        """Calculate confidence in intent detection."""
        # Base confidence
        confidence = 0.5

        # Increase for clear signals
        if intent_type == IntentType.EMERGENCY:
            confidence = 0.9  # Emergency keywords are clear

        # Increase for longer, more detailed queries
        word_count = len(query.split())
        if word_count > 10:
            confidence += 0.1
        if word_count > 20:
            confidence += 0.1

        return min(confidence, 1.0)

    def _detect_language(self, query: str) -> str:
        """Detect query language."""
        spanish_words = {"el", "la", "de", "que", "es", "para", "con", "por"}
        words = set(query.lower().split())
        if len(words.intersection(spanish_words)) >= 2:
            return "es"
        return "en"


# =============================================================================
# Response Generator
# =============================================================================


class ResponseGenerator:
    """Generates responses based on context and plan results."""

    def __init__(self, config: AgentControllerConfig) -> None:
        """Initialize response generator."""
        self.config = config

    async def generate(
        self,
        context: AgentContext,
        plan: AgentPlan,
        llm_service: Any = None,
    ) -> str:
        """Generate response based on context."""
        # Build prompt from context
        prompt = self._build_prompt(context, plan)

        if llm_service:
            # Use LLM for generation
            response = await llm_service.query(prompt)
            content = response.content
        else:
            # Fallback to template-based response
            content = self._generate_template_response(context, plan)

        # Add disclaimer if required
        if self.config.require_disclaimer:
            content = self._add_disclaimer(content, context)

        # Truncate if needed
        if len(content) > self.config.max_response_length:
            content = content[: self.config.max_response_length - 100]
            content += "\n\n[Response truncated due to length limits]"

        return content

    async def generate_stream(
        self,
        context: AgentContext,
        plan: AgentPlan,
        llm_service: Any = None,
    ) -> AsyncIterator[str]:
        """Generate streaming response."""
        if llm_service and hasattr(llm_service, "query_stream"):
            prompt = self._build_prompt(context, plan)
            async for chunk in llm_service.query_stream(prompt):
                yield chunk.content
        else:
            # Simulate streaming for template response
            response = self._generate_template_response(context, plan)
            for i in range(0, len(response), self.config.chunk_size):
                chunk = response[i : i + self.config.chunk_size]
                yield chunk
                await asyncio.sleep(0.01)

        # Add disclaimer at end
        if self.config.require_disclaimer:
            yield "\n\n" + self._get_disclaimer(context)

    def _build_prompt(self, context: AgentContext, plan: AgentPlan) -> str:
        """Build prompt for LLM."""
        parts = []

        # System instruction
        parts.append(
            "You are a medical assistant. Answer based on the following context."
        )

        # User query
        parts.append(f"\n## User Query\n{context.query}")

        # RAG context
        if context.rag_context:
            parts.append(f"\n## Medical Knowledge\n{context.rag_context}")

        # Tool results
        if context.tool_results:
            parts.append("\n## Tool Results")
            for tool, result in context.tool_results.items():
                parts.append(f"- {tool}: {result}")

        # Intent info
        if context.intent:
            parts.append(f"\n## Intent: {context.intent.intent_type.value}")
            parts.append(f"Urgency: {context.intent.urgency.value}")

        return "\n".join(parts)

    def _generate_template_response(
        self,
        context: AgentContext,
        plan: AgentPlan,
    ) -> str:
        """Generate template-based response (fallback)."""
        parts = []

        # Add intent-specific intro
        if context.intent:
            intent = context.intent
            if intent.intent_type == IntentType.EMERGENCY:
                parts.append(
                    "⚠️ **EMERGENCY DETECTED**\n\n"
                    "If you are experiencing a medical emergency, please call "
                    "emergency services (911) immediately.\n"
                )
            elif intent.intent_type == IntentType.MEDICATION:
                parts.append("## Medication Information\n")
            elif intent.intent_type == IntentType.DIAGNOSTIC:
                parts.append("## Symptom Analysis\n")

        # Add tool results
        if context.tool_results:
            for tool, result in context.tool_results.items():
                if isinstance(result, dict):
                    parts.append(f"### {tool.replace('_', ' ').title()}\n")
                    for k, v in result.items():
                        parts.append(f"- **{k}**: {v}")
                else:
                    parts.append(f"- {result}")

        # Add RAG content summary
        if context.rag_context:
            parts.append("\n## Based on Medical Literature\n")
            parts.append(context.rag_context[:500])  # Limit

        # Default message if no content
        if not parts:
            parts.append(
                "I understand your question. However, I need more specific "
                "information to provide accurate medical guidance. Could you "
                "please provide more details about your symptoms or concerns?"
            )

        return "\n".join(parts)

    def _add_disclaimer(self, content: str, context: AgentContext) -> str:
        """Add medical disclaimer to response."""
        return content + "\n\n" + self._get_disclaimer(context)

    def _get_disclaimer(self, context: AgentContext) -> str:
        """Get appropriate disclaimer."""
        lang = context.intent.language if context.intent else "en"

        if lang == "es":
            return (
                "---\n"
                "⚕️ *Esta información es solo educativa y no reemplaza "
                "la consulta médica profesional. Siempre consulte con un "
                "profesional de salud calificado.*"
            )

        return (
            "---\n"
            "⚕️ *This information is for educational purposes only and "
            "does not replace professional medical advice. Always consult "
            "with a qualified healthcare provider.*"
        )


# =============================================================================
# Agent Controller
# =============================================================================


class AgentController:
    """Main controller orchestrating the agent loop."""

    def __init__(
        self,
        config: AgentControllerConfig | None = None,
        llm_service: Any = None,
        tool_service: Any = None,
        rag_service: Any = None,
        memory_service: Any = None,
    ) -> None:
        """Initialize agent controller."""
        self.config = config or AgentControllerConfig()

        # External services (late binding supported)
        self.llm_service = llm_service
        self.tool_service = tool_service
        self.rag_service = rag_service
        self.memory_service = memory_service

        # Internal components
        self.state_manager = create_state_manager(
            StateManagerConfig(
                max_iterations=self.config.max_iterations,
                max_phase_duration_ms=self.config.max_phase_duration_ms,
                max_total_duration_ms=self.config.max_total_duration_ms,
            )
        )

        self.plan_builder = create_plan_builder(
            PlanExecutorConfig(
                max_actions=self.config.max_actions,
                max_retries=self.config.max_retries,
                enable_parallel=self.config.enable_parallel,
            )
        )

        self.plan_executor = create_plan_executor(
            config=PlanExecutorConfig(
                max_actions=self.config.max_actions,
                max_retries=self.config.max_retries,
                enable_parallel=self.config.enable_parallel,
            ),
            tool_executor=tool_service,
            rag_service=rag_service,
        )

        self.intent_analyzer = IntentAnalyzer()
        self.response_generator = ResponseGenerator(self.config)

        # Event handlers
        self._event_handlers: list[Callable[[AgentEvent], None]] = []

    # =========================================================================
    # Service Setters (Late Binding)
    # =========================================================================

    def set_llm_service(self, service: Any) -> None:
        """Set LLM service."""
        self.llm_service = service

    def set_tool_service(self, service: Any) -> None:
        """Set tool service."""
        self.tool_service = service
        self.plan_executor.set_tool_executor(service)

    def set_rag_service(self, service: Any) -> None:
        """Set RAG service."""
        self.rag_service = service
        self.plan_executor.set_rag_service(service)

    def set_memory_service(self, service: Any) -> None:
        """Set memory service."""
        self.memory_service = memory_service

    # =========================================================================
    # Main Entry Points
    # =========================================================================

    async def process(
        self,
        query: str,
        session_id: str | None = None,
        user_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AgentResult:
        """
        Process a user query through the full agent loop.

        Returns:
            AgentResult with response and metadata.
        """
        logger.info(f"Processing query: {query[:100]}...")

        # Create context
        context = AgentContext(
            query=query,
            session_id=session_id or "",
            user_id=user_id,
            metadata=metadata or {},
        )

        # Load conversation history if available
        if self.memory_service and session_id:
            try:
                history = await self.memory_service.get_history(session_id)
                context.history = history
            except Exception as e:
                logger.warning(f"Failed to load history: {e}")

        # Initialize state
        state = self.state_manager.initialize(context)

        try:
            # Run agent loop
            result = await self._run_loop(context)

            # Save to memory if available
            if self.memory_service and session_id:
                try:
                    await self.memory_service.add_turn(
                        session_id=session_id,
                        user_message=query,
                        assistant_message=result.content,
                    )
                except Exception as e:
                    logger.warning(f"Failed to save to memory: {e}")

            return result

        except Exception as e:
            logger.error(f"Agent loop failed: {e}")
            self.state_manager.force_error(str(e))
            return AgentResult(
                content=f"I apologize, but I encountered an error processing your request: {e}",
                success=False,
                error=str(e),
                latency_ms=(
                    self.state_manager.state.elapsed_ms
                    if self.state_manager.state
                    else 0
                ),
            )

    async def process_stream(
        self,
        query: str,
        session_id: str | None = None,
        user_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AsyncIterator[AgentEvent]:
        """
        Process query with streaming events.

        Yields AgentEvent objects for real-time updates.
        """
        logger.info(f"Processing query (streaming): {query[:100]}...")

        # Create context
        context = AgentContext(
            query=query,
            session_id=session_id or "",
            user_id=user_id,
            metadata=metadata or {},
        )

        # Initialize state
        state = self.state_manager.initialize(context)

        # Setup event forwarding
        event_queue: asyncio.Queue[AgentEvent] = asyncio.Queue()

        def event_handler(event: AgentEvent) -> None:
            event_queue.put_nowait(event)

        self.state_manager.add_event_handler(event_handler)

        try:
            # Start agent loop in background
            loop_task = asyncio.create_task(self._run_loop(context))

            # Yield events as they come
            while not loop_task.done() or not event_queue.empty():
                try:
                    event = await asyncio.wait_for(event_queue.get(), timeout=0.1)
                    yield event
                except asyncio.TimeoutError:
                    continue

            # Get final result
            result = await loop_task

            # Yield final event
            yield AgentEvent(
                event_type="completed",
                phase=AgentPhase.COMPLETED,
                data={"result": result.to_dict()},
            )

        except Exception as e:
            logger.error(f"Streaming failed: {e}")
            yield AgentEvent(
                event_type="error",
                phase=AgentPhase.ERROR,
                data={"error": str(e)},
            )

        finally:
            self.state_manager.remove_event_handler(event_handler)

    # =========================================================================
    # Agent Loop
    # =========================================================================

    async def _run_loop(self, context: AgentContext) -> AgentResult:
        """Run the main agent loop."""

        # Phase 1: RECEIVING
        await self.state_manager.transition(AgentPhase.RECEIVING)

        # Phase 2: ANALYZING - Intent analysis
        await self.state_manager.transition(AgentPhase.ANALYZING)
        intent = self.intent_analyzer.analyze(context.query, context.history)
        context.intent = intent

        logger.info(
            f"Intent: {intent.intent_type.value}, "
            f"Urgency: {intent.urgency.value}, "
            f"Confidence: {intent.confidence:.2f}"
        )

        # Check for emergency
        if intent.intent_type == IntentType.EMERGENCY:
            return await self._handle_emergency(context)

        # Phase 3: PLANNING
        await self.state_manager.transition(AgentPhase.PLANNING)
        plan = self.plan_builder.build_plan(intent, context)
        self.state_manager.set_plan(plan)

        logger.info(f"Plan created with {len(plan.actions)} actions")

        # Phase 4: EXECUTING
        await self.state_manager.transition(AgentPhase.EXECUTING)
        executed_plan = await self.plan_executor.execute_plan(plan, context)

        # Phase 5: GENERATING
        await self.state_manager.transition(AgentPhase.GENERATING)
        response = await self.response_generator.generate(
            context,
            executed_plan,
            self.llm_service,
        )
        self.state_manager.update_response(response)

        # Phase 6: REVIEWING (optional quality check)
        await self.state_manager.transition(AgentPhase.REVIEWING)
        # In production, add response quality validation here

        # Phase 7: COMPLETED
        await self.state_manager.transition(AgentPhase.COMPLETED)

        return self.state_manager.get_result()

    async def _handle_emergency(self, context: AgentContext) -> AgentResult:
        """Handle emergency queries with priority path."""
        logger.warning("Emergency detected - priority handling")

        # Build minimal emergency plan
        plan = self.plan_builder.build_plan(context.intent, context)
        self.state_manager.set_plan(plan)

        # Execute emergency-specific tools only
        await self.state_manager.transition(AgentPhase.EXECUTING)
        await self.plan_executor.execute_plan(plan, context)

        # Generate emergency response
        await self.state_manager.transition(AgentPhase.GENERATING)

        emergency_response = (
            "⚠️ **EMERGENCY ALERT**\n\n"
            "Based on your description, this appears to be an emergency situation.\n\n"
            "**IMMEDIATE ACTIONS:**\n"
            "1. **Call emergency services (911) immediately**\n"
            "2. Do not delay seeking professional medical help\n"
            "3. Stay calm and follow dispatcher instructions\n\n"
        )

        # Add any tool results
        if context.tool_results:
            emergency_response += "**Assessment:**\n"
            for tool, result in context.tool_results.items():
                if isinstance(result, dict):
                    emergency_response += f"- {result.get('recommendation', '')}\n"

        self.state_manager.update_response(emergency_response)

        await self.state_manager.transition(AgentPhase.COMPLETED)

        return self.state_manager.get_result()

    # =========================================================================
    # Event Handling
    # =========================================================================

    def add_event_handler(
        self,
        handler: Callable[[AgentEvent], None],
    ) -> None:
        """Add event handler for agent events."""
        self._event_handlers.append(handler)
        self.state_manager.add_event_handler(handler)

    def remove_event_handler(
        self,
        handler: Callable[[AgentEvent], None],
    ) -> None:
        """Remove event handler."""
        if handler in self._event_handlers:
            self._event_handlers.remove(handler)
        self.state_manager.remove_event_handler(handler)


# =============================================================================
# Factory Functions
# =============================================================================


def create_agent_controller(
    config: AgentControllerConfig | None = None,
    llm_service: Any = None,
    tool_service: Any = None,
    rag_service: Any = None,
    memory_service: Any = None,
) -> AgentController:
    """Create agent controller with configuration."""
    return AgentController(
        config=config,
        llm_service=llm_service,
        tool_service=tool_service,
        rag_service=rag_service,
        memory_service=memory_service,
    )
