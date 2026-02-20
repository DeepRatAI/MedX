"""
MedeX State - Complete Application State Management
====================================================
Manages all application state including:
- Chat with streaming
- Medical tools (drug interactions, dosage, labs)
- Knowledge base search
- Triage assessment
- Session management
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Optional

import reflex as rx
import httpx

# PDF export module
from medex_ui.pdf_export import generate_pdf, generate_research_pdf

# Scientific Search module (PubMed, Semantic Scholar) - MAIN RESEARCH ENGINE
from medex_ui.scientific_search import (
    perform_scientific_research,
    build_scientific_research_prompt,
    format_scientific_sources,
)


# =============================================================================
# DATA MODELS
# =============================================================================


class Message(rx.Model):
    """Chat message model."""

    id: str = ""
    role: str = "user"
    content: str = ""
    timestamp: str = ""
    is_streaming: bool = False
    sources: list = []
    is_emergency: bool = False
    triage_level: int = 0
    thinking_content: str = ""  # For reasoning models (R1, QwQ, Qwen3)
    show_thinking: bool = False  # Toggle to show/hide thinking content


class Interaction(rx.Model):
    """Drug interaction model."""

    drug_a: str = ""
    drug_b: str = ""
    severity: str = ""
    mechanism: str = ""
    clinical_effect: str = ""
    management: str = ""


class KBDocument(rx.Model):
    """Knowledge base document model."""

    id: str = ""
    title: str = ""
    content: str = ""
    source: str = ""
    score: float = 0.0
    category: str = ""


class TriageResult(rx.Model):
    """Triage assessment result model."""

    esi_level: int = 5
    esi_name: str = ""
    recommendation: str = ""
    red_flags: list = []
    vital_concerns: list = []


class Artifact(rx.Model):
    """
    Artifact model for displaying results as catalog cards.
    Used for Drug Interactions, Dosage Calculations, and Lab Interpretations.
    """

    id: str = ""
    type: str = ""  # "interaction", "dosage", "lab"
    title: str = ""
    subtitle: str = ""
    severity: str = ""  # "critical", "high", "moderate", "low", "info"
    summary: str = ""  # Short summary for card display
    full_content: str = ""  # Full markdown content for modal
    timestamp: str = ""
    is_new: bool = True  # Show "New!" badge
    extra_data: dict = {}  # Additional data (drugs, weight, etc.)


# =============================================================================
# APPLICATION STATE
# =============================================================================


class MedeXState(rx.State):
    """Complete MedeX application state."""

    # -------------------------------------------------------------------------
    # Connection State
    # -------------------------------------------------------------------------
    api_url: str = "http://localhost:8000"
    is_connected: bool = True
    connection_error: str = ""

    # -------------------------------------------------------------------------
    # Navigation & UI
    # -------------------------------------------------------------------------
    active_section: str = "chat"
    active_tool: str = "interactions"
    sidebar_collapsed: bool = False
    show_model_selector: bool = False

    # -------------------------------------------------------------------------
    # Model Selection - 10 models: 4 general + 6 medical specialized
    # -------------------------------------------------------------------------
    # === MODELOS VERIFICADOS Y FUNCIONALES (2026-01-13) ===
    # Catálogo ampliado con modelos de top benchmarks médicos
    available_models: list[dict] = [
        # === MODELOS BASE ===
        {
            "id": "gemini-2-flash",
            "name": "Gemini 2.0 Flash",
            "provider": "Google",
            "category": "general",
            "description": "⚡ Más rápido (~20s) - Ideal para respuestas ágiles",
            "is_default": True,
        },
        {
            "id": "llama-70b",
            "name": "Llama 3.3 70B",
            "provider": "Meta",
            "category": "general",
            "description": "Equilibrio velocidad/calidad (~32s)",
            "is_default": False,
        },
        {
            "id": "qwen-72b",
            "name": "Qwen 2.5 72B",
            "provider": "Alibaba",
            "category": "general",
            "description": "Respuestas más completas (~50s)",
            "is_default": False,
        },
        {
            "id": "deepseek-r1",
            "name": "DeepSeek R1 (Distill)",
            "provider": "DeepSeek",
            "category": "reasoning",
            "description": "🧠 Razonamiento con <think> tags - Distill 32B",
            "is_default": False,
        },
        # === NUEVOS MODELOS TOP BENCHMARKS MÉDICOS ===
        {
            "id": "kimi-k2",
            "name": "Kimi K2",
            "provider": "Moonshot AI",
            "category": "medical",
            "description": "🏆 Top diagnóstico médico - 1T parámetros MoE",
            "is_default": False,
        },
        {
            "id": "deepseek-v3.1",
            "name": "DeepSeek V3",
            "provider": "DeepSeek",
            "category": "medical",
            "description": "📊 Superior en análisis clínico - 671B MoE",
            "is_default": False,
        },
        {
            "id": "qwen3-235b",
            "name": "Qwen3 235B",
            "provider": "Alibaba",
            "category": "general",
            "description": "🔬 Modelo más grande - Non-thinking mode",
            "is_default": False,
        },
        {
            "id": "qwq-32b",
            "name": "QwQ 32B",
            "provider": "Alibaba",
            "category": "reasoning",
            "description": "🧠 Reasoning médico con <think> (~79% MMLU)",
            "is_default": False,
        },
    ]
    selected_model: str = "gemini-2-flash"  # Default: el más rápido
    model_loading: bool = False

    # -------------------------------------------------------------------------
    # Conversation History (Multiple Chats)
    # -------------------------------------------------------------------------
    conversations: list[dict] = []  # [{id, title, created_at, message_count}]
    active_conversation_id: str = ""
    conversation_messages: dict[str, list] = {}  # {conv_id: [messages]}

    # -------------------------------------------------------------------------
    # Legacy Tools Configuration (Drug Tools section - keep for compatibility)
    # -------------------------------------------------------------------------
    tools_enabled: dict[str, bool] = {
        "drug_interactions": True,
        "dosage_calculator": True,
        "lab_interpreter": True,
    }
    show_tools_panel: bool = False

    # -------------------------------------------------------------------------
    # User Configuration
    # -------------------------------------------------------------------------
    user_type: str = "educational"
    language: str = "es"
    include_sources: bool = True
    include_reasoning: bool = False

    # -------------------------------------------------------------------------
    # Chat State
    # -------------------------------------------------------------------------
    messages: list[Message] = []
    current_input: str = ""
    is_loading: bool = False

    # -------------------------------------------------------------------------
    # Session Statistics
    # -------------------------------------------------------------------------
    session_id: str = ""
    session_start: str = ""
    total_queries: int = 0

    # -------------------------------------------------------------------------
    # Emergency State
    # -------------------------------------------------------------------------
    current_is_emergency: bool = False
    current_triage_level: int = 0

    # -------------------------------------------------------------------------
    # Drug Interactions Tool (unified input)
    # -------------------------------------------------------------------------
    drug_search_1: str = ""  # Legacy - kept for compatibility
    drug_search_2: str = ""  # Legacy - kept for compatibility
    drugs_input: str = ""  # NEW: Unified input (comma-separated)
    interactions_result: list[Interaction] = []
    interactions_loading: bool = False
    interactions_error: str = ""
    interactions_status: str = ""  # Status message for process indicator

    # -------------------------------------------------------------------------
    # Dosage Calculator Tool (with age)
    # -------------------------------------------------------------------------
    dosage_drug_name: str = ""
    dosage_patient_weight: str = ""
    dosage_patient_age: str = ""  # NEW: Patient age field
    dosage_result: str = ""
    dosage_warnings: list = []
    dosage_loading: bool = False
    dosage_error: str = ""
    dosage_status: str = ""  # Status message for process indicator

    # -------------------------------------------------------------------------
    # Lab Interpreter Tool
    # -------------------------------------------------------------------------
    lab_text_input: str = ""
    lab_interpretation: str = ""
    lab_loading: bool = False
    lab_error: str = ""
    lab_status: str = ""  # Status message for process indicator

    # -------------------------------------------------------------------------
    # Artifact Catalog System
    # -------------------------------------------------------------------------
    # Artifacts are the visual representation of all tool results
    interaction_artifacts: list[dict] = []  # List of interaction artifact cards
    dosage_artifacts: list[dict] = []  # List of dosage artifact cards
    lab_artifacts: list[dict] = []  # List of lab interpretation artifact cards

    # Artifact modal state
    show_artifact_modal: bool = False
    active_artifact: dict = {}  # Currently viewed artifact in modal

    # Artifact counter (for numbering)
    _artifact_counter: int = 0

    # -------------------------------------------------------------------------
    # Results Persistence (saved results from all tools - ARTIFACTS)
    # -------------------------------------------------------------------------
    saved_interactions: list[dict] = []  # Persisted interaction results
    saved_dosages: list[dict] = []  # Persisted dosage calculations
    saved_lab_results: list[dict] = []  # Persisted lab interpretations
    saved_research: list[dict] = []  # Persisted research results

    # -------------------------------------------------------------------------
    # Research Mode - Enhanced with Clarification Protocol
    # -------------------------------------------------------------------------
    research_query: str = ""
    research_loading: bool = False
    research_status: str = ""
    research_progress: int = 0  # 0-100 progress percentage
    research_steps: list[dict] = []  # Steps taken in research
    research_result: str = ""
    research_sources: list[dict] = []
    research_error: str = ""

    # Clarification Phase (ChatGPT-style protocol)
    research_phase: str = "input"  # "input" | "clarify" | "researching" | "complete"
    research_clarification_questions: list[dict] = []  # Questions for user
    research_clarification_answers: dict[str, str] = {}  # User's answers
    research_format_preference: str = (
        "comprehensive"  # "comprehensive" | "summary" | "clinical"
    )
    research_include_references: bool = True
    research_include_case_studies: bool = True
    research_evidence_focus: str = "all"  # "all" | "high" | "clinical_trials"

    # -------------------------------------------------------------------------
    # Knowledge Base
    # -------------------------------------------------------------------------
    kb_search_query: str = ""
    kb_search_results: list[KBDocument] = []
    kb_loading: bool = False
    kb_error: str = ""

    # -------------------------------------------------------------------------
    # Triage Assessment
    # -------------------------------------------------------------------------
    triage_chief_complaint: str = ""
    triage_duration: str = ""
    triage_pain_level: int = 0
    triage_vital_hr: str = ""
    triage_vital_bp_sys: str = ""
    triage_vital_bp_dia: str = ""
    triage_vital_rr: str = ""
    triage_vital_temp: str = ""
    triage_vital_spo2: str = ""
    triage_result: Optional[TriageResult] = None
    triage_loading: bool = False
    triage_error: str = ""

    # =========================================================================
    # COMPUTED PROPERTIES
    # =========================================================================

    @rx.var
    def has_messages(self) -> bool:
        return len(self.messages) > 0

    @rx.var
    def message_count(self) -> int:
        return len(self.messages)

    @rx.var
    def messages_as_dicts(self) -> list[dict]:
        """Convert Message objects to dicts for rendering."""
        return [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "timestamp": m.timestamp,
                "is_streaming": m.is_streaming,
                "sources": m.sources,
                "is_emergency": m.is_emergency,
                "triage_level": m.triage_level,
                "thinking_content": m.thinking_content,  # For reasoning models (R1, QwQ)
            }
            for m in self.messages
        ]

    @rx.var
    def user_type_label(self) -> str:
        labels = {
            "educational": "Educational",
            "professional": "Professional",
            "research": "Research",
        }
        return labels.get(self.user_type, "Educational")

    @rx.var
    def session_duration_minutes(self) -> int:
        if not self.session_start:
            return 0
        try:
            start = datetime.fromisoformat(self.session_start)
            return int((datetime.now() - start).total_seconds() // 60)
        except Exception:
            return 0

    @rx.var
    def can_send_message(self) -> bool:
        return bool(self.current_input.strip()) and not self.is_loading

    @rx.var
    def has_interactions(self) -> bool:
        return len(self.interactions_result) > 0

    @rx.var
    def interactions_as_dicts(self) -> list[dict]:
        """Convert Interaction objects to dicts for rendering."""
        return [
            {
                "drug_a": i.drug_a,
                "drug_b": i.drug_b,
                "severity": i.severity,
                "mechanism": i.mechanism,
                "clinical_effect": i.clinical_effect,
                "management": i.management,
            }
            for i in self.interactions_result
        ]

    # -------------------------------------------------------------------------
    # Artifact Catalog Computed Properties
    # -------------------------------------------------------------------------

    @rx.var
    def has_interaction_artifacts(self) -> bool:
        """Check if there are any interaction artifacts."""
        return len(self.interaction_artifacts) > 0

    @rx.var
    def has_dosage_artifacts(self) -> bool:
        """Check if there are any dosage artifacts."""
        return len(self.dosage_artifacts) > 0

    @rx.var
    def has_lab_artifacts(self) -> bool:
        """Check if there are any lab artifacts."""
        return len(self.lab_artifacts) > 0

    @rx.var
    def interaction_artifacts_count(self) -> int:
        """Get count of interaction artifacts."""
        return len(self.interaction_artifacts)

    @rx.var
    def dosage_artifacts_count(self) -> int:
        """Get count of dosage artifacts."""
        return len(self.dosage_artifacts)

    @rx.var
    def lab_artifacts_count(self) -> int:
        """Get count of lab artifacts."""
        return len(self.lab_artifacts)

    # Active artifact computed properties for modal
    @rx.var
    def active_artifact_title(self) -> str:
        """Get active artifact title."""
        return (
            self.active_artifact.get("title", "Detalle")
            if self.active_artifact
            else "Detalle"
        )

    @rx.var
    def active_artifact_subtitle(self) -> str:
        """Get active artifact subtitle."""
        return self.active_artifact.get("subtitle", "") if self.active_artifact else ""

    @rx.var
    def active_artifact_severity_label(self) -> str:
        """Get active artifact severity label."""
        return (
            self.active_artifact.get("severity_label", "Info")
            if self.active_artifact
            else "Info"
        )

    @rx.var
    def active_artifact_severity_color(self) -> str:
        """Get active artifact severity color."""
        return (
            self.active_artifact.get("severity_color", "blue")
            if self.active_artifact
            else "blue"
        )

    @rx.var
    def active_artifact_full_content(self) -> str:
        """Get active artifact full content for modal display."""
        return (
            self.active_artifact.get("full_content", "") if self.active_artifact else ""
        )

    @rx.var
    def has_kb_results(self) -> bool:
        return len(self.kb_search_results) > 0

    @rx.var
    def kb_results_count(self) -> int:
        return len(self.kb_search_results)

    @rx.var
    def kb_results_as_dicts(self) -> list[dict]:
        """Convert KBDocument objects to dicts for rendering."""
        return [
            {
                "id": d.id,
                "title": d.title,
                "content": d.content,
                "source": d.source,
                "score": d.score,
                "category": d.category,
            }
            for d in self.kb_search_results
        ]

    @rx.var
    def has_triage_result(self) -> bool:
        return self.triage_result is not None

    @rx.var
    def triage_esi_level(self) -> int:
        return self.triage_result.esi_level if self.triage_result else 5

    @rx.var
    def triage_esi_name(self) -> str:
        return self.triage_result.esi_name if self.triage_result else ""

    @rx.var
    def triage_recommendation(self) -> str:
        return self.triage_result.recommendation if self.triage_result else ""

    @rx.var
    def triage_red_flags(self) -> list:
        return self.triage_result.red_flags if self.triage_result else []

    @rx.var
    def has_red_flags(self) -> bool:
        return len(self.triage_red_flags) > 0

    @rx.var
    def has_models(self) -> bool:
        return len(self.available_models) > 0

    @rx.var
    def selected_model_name(self) -> str:
        for m in self.available_models:
            if m.get("id") == self.selected_model:
                return m.get("name", self.selected_model)
        return self.selected_model

    @rx.var
    def has_conversations(self) -> bool:
        return len(self.conversations) > 0

    @rx.var
    def conversations_count(self) -> int:
        return len(self.conversations)

    # =========================================================================
    # RESEARCH COMPUTED PROPERTIES
    # =========================================================================

    @rx.var
    def research_sources_count(self) -> int:
        """Number of research sources found."""
        return len(self.research_sources)

    @rx.var
    def has_research_sources(self) -> bool:
        """Check if there are research sources."""
        return len(self.research_sources) > 0

    # =========================================================================
    # ARTIFACTS COMPUTED PROPERTIES
    # =========================================================================

    @rx.var
    def total_artifacts(self) -> int:
        """Total number of saved tool results."""
        return (
            len(self.saved_interactions)
            + len(self.saved_dosages)
            + len(self.saved_lab_results)
            + len(self.saved_research)
        )

    @rx.var
    def has_artifacts(self) -> bool:
        return self.total_artifacts > 0

    @rx.var
    def all_artifacts(self) -> list[dict]:
        """Combined list of all artifacts sorted by timestamp."""
        artifacts = []

        # Add interactions
        for item in self.saved_interactions:
            artifacts.append(
                {
                    "type": "interactions",
                    "icon": "git-compare",
                    "title": f"Interacciones: {', '.join(item.get('drugs', [])[:3])}",
                    "timestamp": item.get("timestamp", ""),
                    "data": item,
                }
            )

        # Add dosages
        for item in self.saved_dosages:
            artifacts.append(
                {
                    "type": "dosage",
                    "icon": "calculator",
                    "title": f"Dosis: {item.get('drug', 'Medicamento')}",
                    "timestamp": item.get("timestamp", ""),
                    "data": item,
                }
            )

        # Add lab results
        for item in self.saved_lab_results:
            artifacts.append(
                {
                    "type": "lab",
                    "icon": "flask-conical",
                    "title": f"Laboratorio: {item.get('summary', 'Interpretación')[:30]}",
                    "timestamp": item.get("timestamp", ""),
                    "data": item,
                }
            )

        # Add research
        for item in self.saved_research:
            artifacts.append(
                {
                    "type": "research",
                    "icon": "search",
                    "title": f"Research: {item.get('query', 'Consulta')[:30]}",
                    "timestamp": item.get("timestamp", ""),
                    "data": item,
                }
            )

        # Sort by timestamp descending (newest first)
        return sorted(artifacts, key=lambda x: x.get("timestamp", ""), reverse=True)

    # =========================================================================
    # LIFECYCLE
    # =========================================================================

    async def on_load(self) -> None:
        self.session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.active_conversation_id = self.session_id
        self.session_start = datetime.now().isoformat()
        await self.check_connection()
        await self.load_models()
        self._init_conversation()

    # =========================================================================
    # CONNECTION
    # =========================================================================

    async def check_connection(self) -> None:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.api_url}/health")
                self.is_connected = response.status_code == 200
                self.connection_error = ""
        except Exception as e:
            self.is_connected = False
            self.connection_error = str(e)

    # =========================================================================
    # MODEL SELECTION
    # =========================================================================

    async def load_models(self) -> None:
        """Load available models from API."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.api_url}/api/v1/models")
                if response.status_code == 200:
                    data = response.json()
                    self.available_models = data.get("models", [])
                    self.selected_model = data.get("current", "gemini-2-flash")
        except Exception:
            # Fallback: mismos 8 modelos verificados que el valor inicial
            # Actualizados 2026-01-13 con modelos que SÍ funcionan en HF Inference
            self.available_models = [
                # === MODELOS BASE ===
                {
                    "id": "gemini-2-flash",
                    "name": "Gemini 2.0 Flash",
                    "provider": "Google",
                    "category": "general",
                    "description": "⚡ Más rápido (~20s) - Ideal para respuestas ágiles",
                    "is_default": True,
                },
                {
                    "id": "llama-70b",
                    "name": "Llama 3.3 70B",
                    "provider": "Meta",
                    "category": "general",
                    "description": "Equilibrio velocidad/calidad (~32s)",
                    "is_default": False,
                },
                {
                    "id": "qwen-72b",
                    "name": "Qwen 2.5 72B",
                    "provider": "Alibaba",
                    "category": "general",
                    "description": "Respuestas más completas (~50s)",
                    "is_default": False,
                },
                {
                    "id": "deepseek-r1",
                    "name": "DeepSeek R1 (Distill)",
                    "provider": "DeepSeek",
                    "category": "reasoning",
                    "description": "🧠 Razonamiento con <think> tags - Distill 32B",
                    "is_default": False,
                },
                # === NUEVOS MODELOS TOP BENCHMARKS MÉDICOS ===
                {
                    "id": "kimi-k2",
                    "name": "Kimi K2",
                    "provider": "Moonshot AI",
                    "category": "medical",
                    "description": "🏆 Top diagnóstico médico - 1T parámetros MoE",
                    "is_default": False,
                },
                {
                    "id": "deepseek-v3.1",
                    "name": "DeepSeek V3",
                    "provider": "DeepSeek",
                    "category": "medical",
                    "description": "📊 Superior en análisis clínico - 671B MoE",
                    "is_default": False,
                },
                {
                    "id": "qwen3-235b",
                    "name": "Qwen3 235B",
                    "provider": "Alibaba",
                    "category": "general",
                    "description": "🔬 Modelo más grande - Non-thinking mode",
                    "is_default": False,
                },
                {
                    "id": "qwq-32b",
                    "name": "QwQ 32B",
                    "provider": "Alibaba",
                    "category": "reasoning",
                    "description": "🧠 Reasoning médico con <think> (~79% MMLU)",
                    "is_default": False,
                },
            ]

    @rx.event
    def toggle_model_selector(self) -> None:
        """Toggle model selector dropdown visibility."""
        self.show_model_selector = not self.show_model_selector

    # =========================================================================
    # CLIPBOARD OPERATIONS
    # =========================================================================

    copied_message_id: str = ""  # Track which message was copied for feedback

    def copy_message_to_clipboard(
        self, content: str, message_id: str = ""
    ) -> rx.event.EventSpec:
        """Copy message content to clipboard and show feedback."""
        self.copied_message_id = message_id
        return rx.set_clipboard(content)

    def clear_copied_feedback(self) -> None:
        """Clear the copied message feedback after timeout."""
        self.copied_message_id = ""

    @rx.event
    def select_model_by_id(self, model_id: str) -> None:
        """Select a model by ID."""
        self.selected_model = model_id
        self.show_model_selector = False

    @rx.event
    async def select_model(self, model_id: str):
        """Select a model and notify backend."""
        self.model_loading = True
        self.selected_model = model_id
        self.show_model_selector = False
        yield

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                await client.post(
                    f"{self.api_url}/api/v1/models/select?model_id={model_id}"
                )
        except Exception:
            pass
        finally:
            self.model_loading = False
            yield

    # =========================================================================
    # CONVERSATION MANAGEMENT
    # =========================================================================

    def _init_conversation(self) -> None:
        """Initialize a new conversation in history."""
        if self.session_id and self.session_id not in [
            c.get("id") for c in self.conversations
        ]:
            self.conversations.insert(
                0,
                {
                    "id": self.session_id,
                    "title": "New Conversation",
                    "created_at": self.session_start,
                    "message_count": 0,
                },
            )
            # Initialize empty message list for this conversation
            self.conversation_messages[self.session_id] = []

    def _save_current_conversation(self) -> None:
        """Save current messages to conversation storage."""
        if self.active_conversation_id and self.messages:
            # Convert Message objects to dicts for storage
            self.conversation_messages[self.active_conversation_id] = [
                {
                    "id": m.id,
                    "role": m.role,
                    "content": m.content,
                    "timestamp": m.timestamp,
                    "sources": m.sources,
                    "is_emergency": m.is_emergency,
                    "triage_level": m.triage_level,
                }
                for m in self.messages
            ]
            # Update message count in conversation list
            for conv in self.conversations:
                if conv.get("id") == self.active_conversation_id:
                    conv["message_count"] = len(self.messages)
                    break

    def _load_conversation(self, conv_id: str) -> None:
        """Load messages for a conversation."""
        stored_messages = self.conversation_messages.get(conv_id, [])
        self.messages = [
            Message(
                id=m.get("id", ""),
                role=m.get("role", "user"),
                content=m.get("content", ""),
                timestamp=m.get("timestamp", ""),
                sources=m.get("sources", []),
                is_emergency=m.get("is_emergency", False),
                triage_level=m.get("triage_level", 0),
            )
            for m in stored_messages
        ]

    def _update_conversation_title(self) -> None:
        """Update conversation title based on first user message."""
        if not self.messages or len(self.messages) < 1:
            return

        # Find the first user message
        first_user_msg = None
        for msg in self.messages:
            if msg.role == "user":
                first_user_msg = msg.content
                break

        if not first_user_msg:
            return

        # Generate a clean title from the first message
        title = first_user_msg.strip()

        # Clean up the title
        title = title.replace("\n", " ").replace("  ", " ")

        # Truncate intelligently at word boundary
        if len(title) > 45:
            truncated = title[:45]
            # Try to cut at last space for cleaner title
            last_space = truncated.rfind(" ")
            if last_space > 20:
                truncated = truncated[:last_space]
            title = truncated + "..."

        # Update the conversation
        for conv in self.conversations:
            if conv.get("id") == self.active_conversation_id:
                conv["title"] = title
                conv["message_count"] = len(self.messages)
                break

    @rx.event
    def switch_conversation(self, conv_id: str) -> None:
        """Switch to a different conversation."""
        # Save current messages before switching
        self._save_current_conversation()

        # Switch to new conversation
        self.active_conversation_id = conv_id
        self.session_id = conv_id

        # Load messages for the target conversation
        self._load_conversation(conv_id)
        self.active_section = "chat"

    @rx.event
    def delete_conversation(self, conv_id: str) -> None:
        """Delete a conversation."""
        self.conversations = [c for c in self.conversations if c.get("id") != conv_id]
        # Also delete stored messages
        if conv_id in self.conversation_messages:
            del self.conversation_messages[conv_id]
        if self.active_conversation_id == conv_id:
            self.new_conversation()

    # =========================================================================
    # NAVIGATION
    # =========================================================================

    @rx.event
    def set_section(self, section: str) -> None:
        """Set the active navigation section."""
        self.active_section = section

    @rx.event
    def set_section_chat(self) -> None:
        """Navigate to Chat section."""
        self.active_section = "chat"

    @rx.event
    def set_section_tools(self) -> None:
        """Navigate to Drug Tools section."""
        self.active_section = "tools"

    @rx.event
    def set_section_knowledge(self) -> None:
        """Navigate to Knowledge Base section."""
        self.active_section = "knowledge"

    @rx.event
    def set_section_triage(self) -> None:
        """Navigate to Triage section."""
        self.active_section = "triage"

    @rx.event
    def set_section_history(self) -> None:
        """Navigate to History section."""
        self.active_section = "history"

    @rx.event
    def set_section_research(self) -> None:
        """Navigate to Deep Research section."""
        self.active_section = "research"

    @rx.event
    def set_tool(self, tool: str) -> None:
        """Set the active tool tab."""
        self.active_tool = tool

    @rx.event
    def set_tool_interactions(self) -> None:
        """Switch to Drug Interactions tool."""
        self.active_tool = "interactions"

    @rx.event
    def set_tool_dosage(self) -> None:
        """Switch to Dosage Calculator tool."""
        self.active_tool = "dosage"

    @rx.event
    def set_tool_labs(self) -> None:
        """Switch to Lab Interpreter tool."""
        self.active_tool = "labs"

    @rx.event
    def toggle_sidebar(self) -> None:
        """Toggle sidebar collapsed/expanded state."""
        self.sidebar_collapsed = not self.sidebar_collapsed

    # =========================================================================
    # USER SETTINGS
    # =========================================================================

    @rx.event
    def set_user_type(self, user_type: str) -> None:
        """Set user type (educational, professional, research)."""
        self.user_type = user_type
        self.include_reasoning = user_type == "professional"

    @rx.event
    def set_user_type_educational(self) -> None:
        """Set user type to educational mode."""
        self.user_type = "educational"
        self.include_reasoning = False

    @rx.event
    def set_user_type_professional(self) -> None:
        """Set user type to professional mode."""
        self.user_type = "professional"
        self.include_reasoning = True

    @rx.event
    def set_user_type_research(self) -> None:
        """Set user type to research mode."""
        self.user_type = "research"
        self.include_reasoning = False

    # =========================================================================
    # TOOLS CONFIGURATION
    # =========================================================================

    @rx.event
    def toggle_tools_panel(self) -> None:
        """Toggle the tools configuration panel."""
        self.show_tools_panel = not self.show_tools_panel

    @rx.event
    def toggle_tool(self, tool_name: str) -> None:
        """Toggle a specific tool on/off."""
        if tool_name in self.tools_enabled:
            self.tools_enabled[tool_name] = not self.tools_enabled[tool_name]

    @rx.event
    def toggle_drug_interactions(self) -> None:
        """Toggle drug interactions tool."""
        self.tools_enabled["drug_interactions"] = not self.tools_enabled.get(
            "drug_interactions", True
        )

    @rx.event
    def toggle_dosage_calculator(self) -> None:
        """Toggle dosage calculator tool."""
        self.tools_enabled["dosage_calculator"] = not self.tools_enabled.get(
            "dosage_calculator", True
        )

    @rx.event
    def toggle_lab_interpreter(self) -> None:
        """Toggle lab interpreter tool."""
        self.tools_enabled["lab_interpreter"] = not self.tools_enabled.get(
            "lab_interpreter", True
        )

    @rx.event
    def toggle_triage(self) -> None:
        """Toggle triage tool."""
        self.tools_enabled["triage"] = not self.tools_enabled.get("triage", True)

    # =========================================================================
    # TOOL COUNTS AND LISTS
    # =========================================================================

    @rx.var
    def active_tools_count(self) -> int:
        """Count of currently active tools."""
        return sum(1 for enabled in self.tools_enabled.values() if enabled)

    @rx.var
    def tools_enabled_list(self) -> list[dict]:
        """Get tools as list for UI rendering."""
        tool_info = {
            "drug_interactions": {"name": "Drug Interactions", "icon": "pill"},
            "dosage_calculator": {"name": "Dosage Calculator", "icon": "calculator"},
            "lab_interpreter": {"name": "Lab Interpreter", "icon": "flask-conical"},
            "triage": {"name": "Triage Assessment", "icon": "heart-pulse"},
        }
        return [
            {
                "id": tool_id,
                "name": info["name"],
                "icon": info["icon"],
                "enabled": self.tools_enabled.get(tool_id, True),
            }
            for tool_id, info in tool_info.items()
        ]

    # =========================================================================
    # CHAT
    # =========================================================================

    def set_input(self, value: str) -> None:
        self.current_input = value

    @rx.event
    async def handle_key_down(self, key: str):
        """Handle keyboard events - Enter to send."""
        if key == "Enter" and self.can_send_message:
            async for _ in self.send_message():
                yield

    @rx.event
    async def send_message(self):
        """Send message with real-time streaming."""
        if not self.current_input.strip() or self.is_loading:
            return

        user_msg = Message(
            id=f"msg_{datetime.now().timestamp()}",
            role="user",
            content=self.current_input.strip(),
            timestamp=datetime.now().isoformat(),
        )
        self.messages.append(user_msg)

        query = self.current_input.strip()
        self.current_input = ""
        self.is_loading = True
        self.total_queries += 1

        # Yield immediately to show user message
        yield

        assistant_msg = Message(
            id=f"msg_{datetime.now().timestamp()}_assistant",
            role="assistant",
            content="",
            timestamp=datetime.now().isoformat(),
            is_streaming=True,
        )
        self.messages.append(assistant_msg)

        # Yield to show streaming state
        yield

        try:
            import re

            # Build conversation history for context (exclude the current message being processed)
            history_for_api = []
            for msg in self.messages[:-1]:  # Exclude last (empty assistant) message
                history_for_api.append({"role": msg.role, "content": msg.content})

            # Use streaming endpoint for real-time response
            async with httpx.AsyncClient(timeout=180.0) as client:
                async with client.stream(
                    "POST",
                    f"{self.api_url}/api/v1/query/stream",
                    json={
                        "query": query,
                        "user_type": self.user_type,
                        "session_id": self.session_id,
                        "language": self.language,
                        "history": history_for_api,  # Send conversation history
                        "model": self.selected_model,  # Send selected model
                    },
                    headers={"Accept": "text/event-stream"},
                ) as response:
                    if response.status_code != 200:
                        self.messages[
                            -1
                        ].content = f"Error: Status {response.status_code}"
                        self.messages[-1].is_streaming = False
                        yield
                        return

                    # =========================================================
                    # REAL-TIME STREAMING WITH THINKING SEPARATION
                    # For reasoning models (deepseek-r1, qwq-32b) that use <think> tags
                    # Stream thinking content to collapsible WHILE receiving,
                    # then stream response separately after </think>
                    # =========================================================

                    is_reasoning_model = self.selected_model in (
                        "deepseek-r1",
                        "qwq-32b",
                    )

                    # State machine for <think> tag parsing
                    raw_buffer = ""  # Full raw stream for fallback
                    thinking_buffer = ""  # Content inside <think>...</think>
                    response_buffer = ""  # Content after </think>
                    in_thinking = False  # Currently inside <think> block
                    thinking_complete = False  # </think> has been seen

                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        if line.startswith("data: "):
                            data_str = line[6:]  # Remove "data: " prefix
                            if data_str == "[DONE]":
                                break
                            try:
                                data = json.loads(data_str)
                                event_type = data.get("event", "")

                                # Handle delta events (streaming tokens)
                                if "delta" in data and data["delta"]:
                                    chunk = data["delta"]
                                    raw_buffer += chunk

                                    if is_reasoning_model and not thinking_complete:
                                        # Parse <think> tags in real-time

                                        if not in_thinking:
                                            # Check if <think> starts
                                            if "<think>" in raw_buffer:
                                                in_thinking = True
                                                # Extract content after <think>
                                                idx = raw_buffer.find("<think>")
                                                thinking_buffer = raw_buffer[idx + 7 :]
                                                self.messages[
                                                    -1
                                                ].thinking_content = thinking_buffer
                                                self.messages[
                                                    -1
                                                ].content = ""  # Clear while thinking
                                                yield
                                            else:
                                                # Not yet in thinking, but for reasoning models
                                                # wait a bit to see if <think> comes
                                                if (
                                                    len(raw_buffer) > 50
                                                    and "<" not in raw_buffer
                                                ):
                                                    # No <think> tag, stream normally
                                                    thinking_complete = True
                                                    response_buffer = raw_buffer
                                                    self.messages[
                                                        -1
                                                    ].content = response_buffer
                                                    yield
                                        else:
                                            # Inside <think> block
                                            if "</think>" in raw_buffer:
                                                # Thinking complete, extract response
                                                in_thinking = False
                                                thinking_complete = True
                                                idx = raw_buffer.find("</think>")
                                                thinking_buffer = raw_buffer[
                                                    raw_buffer.find("<think>") + 7 : idx
                                                ]
                                                response_buffer = raw_buffer[
                                                    idx + 8 :
                                                ].strip()
                                                self.messages[
                                                    -1
                                                ].thinking_content = (
                                                    thinking_buffer.strip()
                                                )
                                                self.messages[
                                                    -1
                                                ].content = response_buffer
                                                yield
                                            else:
                                                # Still thinking, update thinking content
                                                idx = raw_buffer.find("<think>")
                                                thinking_buffer = raw_buffer[idx + 7 :]
                                                self.messages[
                                                    -1
                                                ].thinking_content = thinking_buffer
                                                yield

                                    elif is_reasoning_model and thinking_complete:
                                        # After </think>, stream response normally
                                        idx = raw_buffer.find("</think>")
                                        if idx != -1:
                                            response_buffer = raw_buffer[
                                                idx + 8 :
                                            ].strip()
                                        else:
                                            response_buffer = raw_buffer
                                        self.messages[-1].content = response_buffer
                                        yield

                                    else:
                                        # Non-reasoning model: stream directly
                                        self.messages[-1].content = raw_buffer
                                        yield

                                # Handle finish event - use full content if available
                                elif event_type == "finish" and "content" in data:
                                    if is_reasoning_model:
                                        # Final cleanup for reasoning models
                                        full_content = data["content"]
                                        think_match = re.search(
                                            r"<think>(.*?)</think>",
                                            full_content,
                                            re.DOTALL,
                                        )
                                        if think_match:
                                            self.messages[
                                                -1
                                            ].thinking_content = think_match.group(
                                                1
                                            ).strip()
                                            self.messages[-1].content = re.sub(
                                                r"<think>.*?</think>",
                                                "",
                                                full_content,
                                                flags=re.DOTALL,
                                            ).strip()
                                        else:
                                            self.messages[-1].content = full_content
                                    else:
                                        self.messages[-1].content = data["content"]
                                    yield
                                elif "error" in data:
                                    self.messages[
                                        -1
                                    ].content = f"Error: {data['error']}"
                                    break
                            except json.JSONDecodeError:
                                # Not JSON, might be raw content
                                if data_str and data_str != "[DONE]":
                                    raw_buffer += data_str
                                    if not is_reasoning_model:
                                        self.messages[-1].content = raw_buffer
                                        yield

            # Final cleanup: ensure thinking content is properly separated
            if is_reasoning_model:
                content = self.messages[-1].content
                # Remove any remaining <think> tags from content
                if "<think>" in content or "</think>" in content:
                    think_match = re.search(r"<think>(.*?)</think>", content, re.DOTALL)
                    if think_match:
                        self.messages[-1].thinking_content = think_match.group(
                            1
                        ).strip()
                        self.messages[-1].content = re.sub(
                            r"<think>.*?</think>", "", content, flags=re.DOTALL
                        ).strip()

            # Fix Markdown headers without space after # (common issue with Kimi K2)
            self.messages[-1].content = re.sub(
                r"^(#{1,6})([^\s#])",
                r"\1 \2",
                self.messages[-1].content,
                flags=re.MULTILINE,
            )

            # =================================================================
            # FALLBACK: Remove wrapping code blocks for certain models
            # This is a safety net in case the prompt fix doesn't fully resolve
            # the issue where models wrap their entire response in backticks.
            # Root cause was fixed in prompts.py by removing the ```markdown
            # example block from the Professional mode prompt.
            # This fallback can be removed once verified working.
            # =================================================================
            models_with_codebox_issue = ("deepseek-v3.1", "qwen3-235b", "qwq-32b")
            if self.selected_model in models_with_codebox_issue:
                content = self.messages[-1].content
                # Pattern: content wrapped in ``` at start and end (with optional language identifier)
                # Matches: ```\ncontent\n``` or ```markdown\ncontent\n```
                codebox_pattern = r"^```(?:\w*)?\s*\n?(.*?)\n?```\s*$"
                match = re.match(codebox_pattern, content, re.DOTALL)
                if match:
                    # Extract the content inside the code block
                    self.messages[-1].content = match.group(1).strip()

            self.messages[-1].is_streaming = False
            self._update_conversation_title()
            self._save_current_conversation()

        except httpx.TimeoutException:
            self.messages[
                -1
            ].content = "La solicitud excedió el tiempo de espera. Intente de nuevo."
            self.messages[-1].is_streaming = False
        except httpx.ConnectError:
            # Fallback to non-streaming endpoint
            await self._send_message_fallback(query)
        except Exception as e:
            self.messages[-1].content = f"Error: {str(e)}"
            self.messages[-1].is_streaming = False
        finally:
            self.is_loading = False
            self._save_current_conversation()
            yield

    async def _send_message_fallback(self, query: str):
        """Fallback to non-streaming endpoint if streaming fails."""
        # Build history
        history_for_api = [
            {"role": m.role, "content": m.content} for m in self.messages[:-1]
        ]

        try:
            async with httpx.AsyncClient(
                timeout=180.0
            ) as client:  # Increased for reasoning models
                response = await client.post(
                    f"{self.api_url}/api/v1/query",
                    json={
                        "query": query,
                        "user_type": self.user_type,
                        "session_id": self.session_id,
                        "language": self.language,
                        "history": history_for_api,
                        "model": self.selected_model,  # Send selected model
                    },
                )
                if response.status_code == 200:
                    data = response.json()
                    self.messages[-1].content = data.get("response", "Sin respuesta")
                    # Handle thinking content from reasoning models (R1, QwQ, Qwen3)
                    thinking = data.get("thinking_content")
                    if thinking:
                        self.messages[-1].thinking_content = thinking
                    
                    # FALLBACK: Fix wrapping code blocks (same as streaming)
                    # Root cause fixed in prompts.py
                    import re
                    models_with_codebox_issue = ("deepseek-v3.1", "qwen3-235b", "qwq-32b")
                    if self.selected_model in models_with_codebox_issue:
                        content = self.messages[-1].content
                        codebox_pattern = r"^```(?:\w*)?\s*\n?(.*?)\n?```\s*$"
                        match = re.match(codebox_pattern, content, re.DOTALL)
                        if match:
                            self.messages[-1].content = match.group(1).strip()
                    
                    self.messages[-1].is_streaming = False
                else:
                    self.messages[-1].content = f"Error: Status {response.status_code}"
        except Exception as e:
            self.messages[-1].content = f"Error: {str(e)}"
        finally:
            self.messages[-1].is_streaming = False

    def clear_chat(self) -> None:
        self.messages = []
        self.current_is_emergency = False
        self.current_triage_level = 0

    def new_conversation(self) -> None:
        """Start a new conversation."""
        # Save current conversation before starting new one
        self._save_current_conversation()
        self.clear_chat()
        self.session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.active_conversation_id = self.session_id
        self.session_start = datetime.now().isoformat()
        self._init_conversation()

    # =========================================================================
    # DRUG INTERACTIONS
    # =========================================================================

    def set_drug_1(self, value: str) -> None:
        self.drug_search_1 = value

    def set_drug_2(self, value: str) -> None:
        self.drug_search_2 = value

    def set_drugs_input(self, value: str) -> None:
        """Set unified drugs input (comma-separated)."""
        self.drugs_input = value

    @rx.event
    def clear_interactions(self) -> None:
        """Clear drug interactions form and results."""
        self.drug_search_1 = ""
        self.drug_search_2 = ""
        self.drugs_input = ""
        self.interactions_result = []
        self.interactions_error = ""

    @rx.event
    async def check_interactions(self):
        # Support both unified input and legacy two-field input
        if self.drugs_input.strip():
            # Parse comma-separated drugs
            drugs = [d.strip() for d in self.drugs_input.split(",") if d.strip()]
        else:
            # Legacy: use drug_search_1 and drug_search_2
            drugs = [
                d.strip() for d in [self.drug_search_1, self.drug_search_2] if d.strip()
            ]

        if len(drugs) < 2:
            self.interactions_error = (
                "Por favor ingrese al menos 2 medicamentos (separados por coma)."
            )
            yield
            return

        self.interactions_loading = True
        self.interactions_error = ""
        self.interactions_result = []
        self.interactions_status = "Preparando consulta..."
        yield

        try:
            self.interactions_status = "Analizando interacciones..."
            yield

            async with httpx.AsyncClient(timeout=25.0) as client:
                self.interactions_status = "Procesando medicamentos..."
                yield

                response = await client.post(
                    f"{self.api_url}/api/v1/tools/drug-interactions",
                    json={"drugs": drugs},
                )

                if response.status_code == 200:
                    self.interactions_status = "Procesando resultados..."
                    yield

                    data = response.json()
                    interactions = data.get("interactions", [])

                    self.interactions_result = [
                        Interaction(
                            drug_a=i.get("drug_a", ""),
                            drug_b=i.get("drug_b", ""),
                            severity=i.get("severity", "unknown"),
                            mechanism=i.get("mechanism", ""),
                            clinical_effect=i.get("clinical_effect", ""),
                            management=i.get("management", ""),
                        )
                        for i in interactions
                    ]

                    # Save to persistence
                    self.saved_interactions.append(
                        {
                            "drugs": [self.drug_search_1, self.drug_search_2],
                            "result": data,
                            "timestamp": datetime.now().isoformat(),
                        }
                    )

                    # Create artifact cards for catalog display
                    for idx, inter in enumerate(self.interactions_result):
                        artifact = self._create_interaction_artifact(
                            inter, idx + len(self.interaction_artifacts)
                        )
                        self.interaction_artifacts = self.interaction_artifacts + [
                            artifact
                        ]

                    if not interactions:
                        self.interactions_error = (
                            "No se encontraron interacciones significativas."
                        )
                else:
                    self.interactions_error = f"Error: Status {response.status_code}"
        except httpx.TimeoutException:
            self.interactions_error = (
                "La consulta excedió el tiempo de espera. Intente nuevamente."
            )
        except Exception as e:
            self.interactions_error = f"Error: {str(e)}"
        finally:
            self.interactions_loading = False
            self.interactions_status = ""
            yield

    # =========================================================================
    # DOSAGE CALCULATOR
    # =========================================================================

    def set_dosage_drug(self, value: str) -> None:
        self.dosage_drug_name = value

    def set_dosage_weight(self, value: str) -> None:
        self.dosage_patient_weight = value

    def set_dosage_age(self, value: str) -> None:
        """Set patient age for dosage calculation."""
        self.dosage_patient_age = value

    @rx.event
    def clear_dosage(self) -> None:
        """Clear dosage calculator form and results."""
        self.dosage_drug_name = ""
        self.dosage_patient_weight = ""
        self.dosage_patient_age = ""
        self.dosage_result = ""
        self.dosage_warnings = []
        self.dosage_error = ""

    @rx.event
    async def calculate_dosage(self):
        if not self.dosage_drug_name.strip():
            self.dosage_error = "Por favor ingrese el nombre del medicamento."
            yield
            return

        self.dosage_loading = True
        self.dosage_error = ""
        self.dosage_result = ""
        self.dosage_status = "Calculando dosis..."
        yield

        try:
            weight = (
                float(self.dosage_patient_weight)
                if self.dosage_patient_weight
                else None
            )
            age = int(self.dosage_patient_age) if self.dosage_patient_age else None

            self.dosage_status = "Procesando parámetros..."
            yield

            async with httpx.AsyncClient(timeout=25.0) as client:
                self.dosage_status = "Generando cálculo..."
                yield

                response = await client.post(
                    f"{self.api_url}/api/v1/tools/dosage-calculator",
                    json={
                        "drug": self.dosage_drug_name.strip(),
                        "weight_kg": weight,
                        "age": age,
                    },
                )

                if response.status_code == 200:
                    self.dosage_status = "Generando recomendaciones..."
                    yield

                    data = response.json()
                    self.dosage_result = self._format_dosage(data)
                    self.dosage_warnings = data.get("warnings", [])

                    # Save to persistence
                    self.saved_dosages.append(
                        {
                            "drug": self.dosage_drug_name,
                            "weight": weight,
                            "result": data,
                            "timestamp": datetime.now().isoformat(),
                        }
                    )

                    # Create artifact card for catalog display
                    artifact = self._create_dosage_artifact(
                        self.dosage_drug_name,
                        self.dosage_patient_weight or "N/A",
                        self.dosage_patient_age or "N/A",
                        self.dosage_result,
                    )
                    self.dosage_artifacts = self.dosage_artifacts + [artifact]
                else:
                    self.dosage_error = f"Error: Status {response.status_code}"
        except ValueError:
            self.dosage_error = "Valor de peso inválido."
        except httpx.TimeoutException:
            self.dosage_error = (
                "La consulta excedió el tiempo de espera. Intente nuevamente."
            )
        except Exception as e:
            self.dosage_error = f"Error: {str(e)}"
        finally:
            self.dosage_loading = False
            self.dosage_status = ""
            yield

    def _format_dosage(self, data: dict) -> str:
        result = f"## Dosificación de {data.get('drug', 'Medicamento')}\n\n"
        if w := data.get("weight_kg"):
            result += f"**Peso del paciente:** {w} kg\n\n"
        # Use recommendations from LLM response
        if recommendations := data.get("recommendations"):
            result += recommendations
        else:
            # Fallback to structured fields if available
            if d := data.get("recommended_dose"):
                result += f"**Dosis recomendada:** {d}\n\n"
            if f := data.get("frequency"):
                result += f"**Frecuencia:** {f}\n\n"
            if m := data.get("max_daily_dose"):
                result += f"**Dosis máxima diaria:** {m}\n"
        return result

    # =========================================================================
    # LAB INTERPRETER
    # =========================================================================

    def set_lab_text(self, value: str) -> None:
        self.lab_text_input = value

    @rx.event
    def clear_labs(self) -> None:
        """Clear lab interpreter form and results."""
        self.lab_text_input = ""
        self.lab_interpretation = ""
        self.lab_error = ""

    @rx.event
    async def interpret_labs(self):
        if not self.lab_text_input.strip():
            self.lab_error = "Por favor ingrese los resultados de laboratorio."
            yield
            return

        self.lab_loading = True
        self.lab_error = ""
        self.lab_interpretation = ""
        self.lab_status = "Analizando valores..."
        yield

        try:
            self.lab_status = "Procesando resultados..."
            yield

            async with httpx.AsyncClient(timeout=25.0) as client:
                self.lab_status = "Generando interpretación..."
                yield

                response = await client.post(
                    f"{self.api_url}/api/v1/tools/lab-interpreter",
                    json={"results_text": self.lab_text_input.strip()},
                )

                if response.status_code == 200:
                    self.lab_status = "Generando interpretación..."
                    yield

                    data = response.json()
                    self.lab_interpretation = data.get(
                        "interpretation", "No hay interpretación disponible."
                    )

                    # Save to persistence
                    self.saved_lab_results.append(
                        {
                            "input": self.lab_text_input[:200],
                            "result": data,
                            "timestamp": datetime.now().isoformat(),
                        }
                    )

                    # Create artifact card for catalog display
                    artifact = self._create_lab_artifact(
                        self.lab_text_input,
                        self.lab_interpretation,
                    )
                    self.lab_artifacts = self.lab_artifacts + [artifact]
                else:
                    self.lab_error = f"Error: Status {response.status_code}"
        except httpx.TimeoutException:
            self.lab_error = (
                "La consulta excedió el tiempo de espera. Intente nuevamente."
            )
        except Exception as e:
            self.lab_error = f"Error: {str(e)}"
        finally:
            self.lab_loading = False
            self.lab_status = ""
            yield

    # =========================================================================
    # KNOWLEDGE BASE
    # =========================================================================

    def set_kb_query(self, value: str) -> None:
        self.kb_search_query = value

    def clear_kb(self) -> None:
        self.kb_search_query = ""
        self.kb_search_results = []
        self.kb_error = ""

    async def search_knowledge_base(self) -> None:
        if not self.kb_search_query.strip():
            return

        self.kb_loading = True
        self.kb_error = ""
        self.kb_search_results = []

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.api_url}/api/v1/knowledge/search",
                    json={"query": self.kb_search_query.strip(), "top_k": 10},
                )

                if response.status_code == 200:
                    data = response.json()
                    results = data.get("results", [])

                    self.kb_search_results = [
                        KBDocument(
                            id=r.get("id", f"doc_{i}"),
                            title=r.get("title", "Untitled"),
                            content=r.get("content", "")[:300] + "..."
                            if len(r.get("content", "")) > 300
                            else r.get("content", ""),
                            source=r.get("source", ""),
                            score=r.get("score", 0.0),
                            category=r.get("category", ""),
                        )
                        for i, r in enumerate(results)
                    ]
                else:
                    self.kb_error = f"Error: Status {response.status_code}"
        except Exception as e:
            self.kb_error = f"Error: {str(e)}"
        finally:
            self.kb_loading = False

    # =========================================================================
    # TRIAGE
    # =========================================================================

    def set_triage_complaint(self, value: str) -> None:
        self.triage_chief_complaint = value

    def set_triage_duration(self, value: str) -> None:
        self.triage_duration = value

    def set_triage_pain(self, value: list) -> None:
        if value and len(value) > 0:
            self.triage_pain_level = int(value[0])

    def set_vital_hr(self, value: str) -> None:
        self.triage_vital_hr = value

    def set_vital_bp_sys(self, value: str) -> None:
        self.triage_vital_bp_sys = value

    def set_vital_bp_dia(self, value: str) -> None:
        self.triage_vital_bp_dia = value

    def set_vital_rr(self, value: str) -> None:
        self.triage_vital_rr = value

    def set_vital_temp(self, value: str) -> None:
        self.triage_vital_temp = value

    def set_vital_spo2(self, value: str) -> None:
        self.triage_vital_spo2 = value

    def clear_triage(self) -> None:
        self.triage_chief_complaint = ""
        self.triage_duration = ""
        self.triage_pain_level = 0
        self.triage_vital_hr = ""
        self.triage_vital_bp_sys = ""
        self.triage_vital_bp_dia = ""
        self.triage_vital_rr = ""
        self.triage_vital_temp = ""
        self.triage_vital_spo2 = ""
        self.triage_result = None
        self.triage_error = ""

    async def assess_triage(self) -> None:
        if not self.triage_chief_complaint.strip():
            self.triage_error = "Please enter the chief complaint."
            return

        self.triage_loading = True
        self.triage_error = ""
        self.triage_result = None

        try:
            vitals = {}
            if self.triage_vital_hr:
                vitals["heart_rate"] = int(self.triage_vital_hr)
            if self.triage_vital_bp_sys and self.triage_vital_bp_dia:
                vitals["bp_systolic"] = int(self.triage_vital_bp_sys)
                vitals["bp_diastolic"] = int(self.triage_vital_bp_dia)
            if self.triage_vital_rr:
                vitals["respiratory_rate"] = int(self.triage_vital_rr)
            if self.triage_vital_temp:
                vitals["temperature"] = float(self.triage_vital_temp)
            if self.triage_vital_spo2:
                vitals["spo2"] = int(self.triage_vital_spo2)

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.api_url}/api/v1/triage/assess",
                    json={
                        "chief_complaint": self.triage_chief_complaint.strip(),
                        "duration": self.triage_duration
                        if self.triage_duration
                        else None,
                        "pain_level": self.triage_pain_level
                        if self.triage_pain_level > 0
                        else None,
                        "vitals": vitals if vitals else None,
                    },
                )

                if response.status_code == 200:
                    data = response.json()
                    esi_names = {
                        1: "Resuscitation",
                        2: "Emergent",
                        3: "Urgent",
                        4: "Less Urgent",
                        5: "Non-Urgent",
                    }

                    self.triage_result = TriageResult(
                        esi_level=data.get("esi_level", 5),
                        esi_name=esi_names.get(data.get("esi_level", 5), "Unknown"),
                        recommendation=data.get("recommendation", ""),
                        red_flags=data.get("red_flags", []),
                        vital_concerns=data.get("vital_concerns", []),
                    )
                else:
                    self.triage_error = f"Error: Status {response.status_code}"
        except ValueError as e:
            self.triage_error = f"Invalid vital value: {str(e)}"
        except Exception as e:
            self.triage_error = f"Error: {str(e)}"
        finally:
            self.triage_loading = False

    # =========================================================================
    # EXPORT
    # =========================================================================

    def export_session(self):
        session_data = {
            "session_id": self.session_id,
            "user_type": self.user_type,
            "session_start": self.session_start,
            "total_queries": self.total_queries,
            "messages": [
                {
                    "role": m.role,
                    "content": m.content,
                    "timestamp": m.timestamp,
                    "sources": m.sources,
                }
                for m in self.messages
            ],
        }
        return rx.download(
            data=json.dumps(session_data, indent=2, ensure_ascii=False),
            filename=f"medex_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        )

    def _generate_pdf_content(self, title: str, content: str) -> str:
        """Generate HTML content for PDF export."""
        timestamp = datetime.now().strftime("%d/%m/%Y %H:%M")
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: 'Segoe UI', Arial, sans-serif;
            max-width: 800px;
            margin: 40px auto;
            padding: 20px;
            color: #333;
            line-height: 1.6;
        }}
        .header {{
            border-bottom: 2px solid #2563eb;
            padding-bottom: 15px;
            margin-bottom: 25px;
        }}
        .header h1 {{
            color: #1e40af;
            margin: 0;
            font-size: 24px;
        }}
        .header .subtitle {{
            color: #6b7280;
            font-size: 14px;
            margin-top: 5px;
        }}
        .content {{
            font-size: 14px;
        }}
        h2 {{ color: #1e40af; font-size: 18px; margin-top: 20px; }}
        h3 {{ color: #374151; font-size: 16px; }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }}
        th, td {{
            border: 1px solid #e5e7eb;
            padding: 10px;
            text-align: left;
        }}
        th {{
            background: #f3f4f6;
            font-weight: 600;
        }}
        .disclaimer {{
            margin-top: 30px;
            padding: 15px;
            background: #fef3c7;
            border-left: 4px solid #f59e0b;
            font-size: 12px;
        }}
        .footer {{
            margin-top: 40px;
            padding-top: 15px;
            border-top: 1px solid #e5e7eb;
            font-size: 11px;
            color: #9ca3af;
            text-align: center;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>MedeX - {title}</h1>
        <div class="subtitle">Generado: {timestamp} | Modo: {self.user_type.title()}</div>
    </div>
    <div class="content">
        {content}
    </div>
    <div class="disclaimer">
        <strong>IMPORTANTE:</strong> Esta información es de soporte clínico educacional.
        No sustituye la evaluación médica presencial ni el juicio clínico profesional.
        Validar con guías locales y protocolos institucionales.
    </div>
    <div class="footer">
        MedeX v25.83 - Sistema de Soporte Clínico con IA
    </div>
</body>
</html>
"""

    @rx.event
    def export_dosage_pdf(self) -> rx.event.EventSpec:
        """Export dosage calculation to real PDF."""
        if not self.dosage_result:
            return rx.toast.error("No hay resultados para exportar")
        try:
            pdf_bytes = generate_pdf(
                "Cálculo de Dosificación", self.dosage_result, self.user_type.title()
            )
            return rx.download(
                data=pdf_bytes,
                filename=f"medex_dosificacion_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            )
        except Exception as e:
            print(f"PDF export error: {e}")
            return rx.toast.error(f"Error al exportar: {e}")

    @rx.event
    def export_labs_pdf(self) -> rx.event.EventSpec:
        """Export lab interpretation to real PDF."""
        if not self.lab_interpretation:
            return rx.toast.error("No hay resultados para exportar")
        try:
            pdf_bytes = generate_pdf(
                "Interpretación de Laboratorio",
                self.lab_interpretation,
                self.user_type.title(),
            )
            return rx.download(
                data=pdf_bytes,
                filename=f"medex_laboratorio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            )
        except Exception as e:
            print(f"PDF export error: {e}")
            return rx.toast.error(f"Error al exportar: {e}")

    @rx.event
    def export_interactions_pdf(self) -> rx.event.EventSpec:
        """Export drug interactions to real PDF."""
        if not self.interactions_result:
            return rx.toast.error("No hay resultados para exportar")
        try:
            # Build markdown content from interactions
            content = "## Interacciones Encontradas\n\n"
            for inter in self.interactions_result:
                content += f"### {inter.drug_a} + {inter.drug_b}\n"
                content += f"**Severidad:** {inter.severity}\n\n"
                content += f"**Mecanismo:** {inter.mechanism}\n\n"
                content += f"**Efecto Clínico:** {inter.clinical_effect}\n\n"
                content += f"**Manejo:** {inter.management}\n\n"
                content += "---\n\n"

            pdf_bytes = generate_pdf(
                "Interacciones Medicamentosas", content, self.user_type.title()
            )
            return rx.download(
                data=pdf_bytes,
                filename=f"medex_interacciones_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            )
        except Exception as e:
            print(f"PDF export error: {e}")
            return rx.toast.error(f"Error al exportar: {e}")

    # =========================================================================
    # RESEARCH MODE (Deep Research Style) - Enhanced with Clarification Protocol
    # =========================================================================

    def set_research_query(self, value: str) -> None:
        self.research_query = value

    @rx.event
    def clear_research(self) -> None:
        """Clear research form and results, reset to input phase."""
        self.research_query = ""
        self.research_result = ""
        self.research_sources = []
        self.research_steps = []
        self.research_error = ""
        self.research_progress = 0
        self.research_phase = "input"
        self.research_clarification_questions = []
        self.research_clarification_answers = {}
        self.research_format_preference = "comprehensive"
        self.research_include_references = True
        self.research_include_case_studies = True
        self.research_evidence_focus = "all"

    @rx.event
    def initiate_research_clarification(self) -> None:
        """Step 1: Generate clarification questions before research.

        This implements the ChatGPT-style protocol where we ask the user
        specific questions to understand their needs before researching.
        """
        if not self.research_query.strip():
            self.research_error = "Por favor ingrese una consulta de investigación."
            return

        self.research_error = ""

        # Generate contextual clarification questions based on query
        query = self.research_query.strip().lower()

        # Base questions always asked
        questions = [
            {
                "id": "format",
                "question": "¿Qué formato de respuesta prefieres?",
                "type": "select",
                "options": [
                    {
                        "value": "comprehensive",
                        "label": "📚 Informe completo con referencias académicas (estilo tesis doctoral)",
                    },
                    {
                        "value": "clinical",
                        "label": "🏥 Síntesis clínica práctica (estilo guía de práctica clínica)",
                    },
                    {
                        "value": "summary",
                        "label": "📋 Resumen ejecutivo (puntos clave en 1-2 páginas)",
                    },
                ],
                "default": "comprehensive",
            },
            {
                "id": "references",
                "question": "¿Deseas incluir referencias bibliográficas detalladas (estilo Vancouver/APA)?",
                "type": "toggle",
                "default": True,
            },
            {
                "id": "evidence_level",
                "question": "¿Qué nivel de evidencia prefieres priorizar?",
                "type": "select",
                "options": [
                    {
                        "value": "all",
                        "label": "🔍 Toda la literatura disponible (más completo)",
                    },
                    {
                        "value": "high",
                        "label": "⭐ Solo evidencia alta (meta-análisis, ECAs)",
                    },
                    {
                        "value": "clinical_trials",
                        "label": "🧪 Enfoque en ensayos clínicos",
                    },
                ],
                "default": "all",
            },
        ]

        # Add context-specific questions based on query analysis
        if any(
            term in query
            for term in ["tratamiento", "terapia", "fármaco", "medicamento", "droga"]
        ):
            questions.append(
                {
                    "id": "treatment_focus",
                    "question": "¿Qué aspectos del tratamiento te interesan más?",
                    "type": "multiselect",
                    "options": [
                        {"value": "efficacy", "label": "Eficacia comparativa"},
                        {
                            "value": "safety",
                            "label": "Perfil de seguridad y efectos adversos",
                        },
                        {"value": "dosing", "label": "Dosificación y farmacocinética"},
                        {
                            "value": "guidelines",
                            "label": "Recomendaciones de guías clínicas",
                        },
                    ],
                    "default": ["efficacy", "safety"],
                }
            )

        if any(
            term in query
            for term in ["diagnóstico", "prueba", "test", "screening", "detección"]
        ):
            questions.append(
                {
                    "id": "diagnostic_focus",
                    "question": "¿Qué aspectos diagnósticos deseas explorar?",
                    "type": "multiselect",
                    "options": [
                        {
                            "value": "sensitivity",
                            "label": "Sensibilidad y especificidad",
                        },
                        {"value": "algorithms", "label": "Algoritmos diagnósticos"},
                        {"value": "differential", "label": "Diagnóstico diferencial"},
                        {"value": "biomarkers", "label": "Biomarcadores emergentes"},
                    ],
                    "default": ["sensitivity", "algorithms"],
                }
            )

        if any(
            term in query
            for term in ["pronóstico", "supervivencia", "mortalidad", "riesgo"]
        ):
            questions.append(
                {
                    "id": "prognosis_focus",
                    "question": "¿Qué factores pronósticos te interesan?",
                    "type": "multiselect",
                    "options": [
                        {"value": "survival", "label": "Datos de supervivencia"},
                        {
                            "value": "risk_factors",
                            "label": "Factores de riesgo modificables",
                        },
                        {"value": "staging", "label": "Sistemas de estadificación"},
                        {"value": "recurrence", "label": "Tasas de recurrencia"},
                    ],
                    "default": ["survival", "risk_factors"],
                }
            )

        self.research_clarification_questions = questions
        self.research_phase = "clarify"

    @rx.event
    def set_clarification_answer(self, question_id: str, value: str) -> None:
        """Set answer for a clarification question."""
        self.research_clarification_answers = {
            **self.research_clarification_answers,
            question_id: value,
        }

        # Update specific preferences based on answers
        if question_id == "format":
            self.research_format_preference = value
        elif question_id == "references":
            self.research_include_references = value == "true" or value is True
        elif question_id == "evidence_level":
            self.research_evidence_focus = value

    @rx.event
    def skip_clarification(self) -> None:
        """Skip clarification and proceed with default settings."""
        self.research_phase = "researching"
        # Will trigger start_research_with_context

    @rx.event
    def confirm_clarification(self) -> None:
        """User confirms clarification answers, proceed to research."""
        self.research_phase = "researching"
        # Will trigger start_research_with_context

    @rx.event
    async def start_research(self):
        """
        Start deep research mode with REAL scientific literature search.
        Uses PubMed and Semantic Scholar APIs for evidence-based research.
        """
        if not self.research_query.strip():
            self.research_error = "Por favor ingrese una consulta de investigación."
            yield
            return

        self.research_loading = True
        self.research_error = ""
        self.research_result = ""
        self.research_sources = []
        self.research_steps = []
        self.research_progress = 0
        yield

        try:
            query = self.research_query.strip()

            # Step 1: Initialize scientific search
            self.research_status = "Iniciando búsqueda científica..."
            self.research_progress = 5
            self.research_steps = [
                {
                    "step": 1,
                    "title": "Análisis de consulta científica",
                    "status": "in_progress",
                    "icon": "🔬",
                }
            ]
            yield

            # Step 2: Search PubMed and Semantic Scholar
            self.research_status = "Buscando en PubMed y Semantic Scholar..."
            self.research_progress = 10
            self.research_steps[0]["status"] = "completed"
            self.research_steps = self.research_steps + [
                {
                    "step": 2,
                    "title": "Búsqueda en bases de datos científicas",
                    "status": "in_progress",
                    "icon": "📚",
                }
            ]
            yield

            # Define progress callback for scientific search
            async def update_progress(progress: int, status: str):
                self.research_progress = progress
                self.research_status = status

            # Execute REAL scientific literature search
            scientific_context = await perform_scientific_research(
                query,
                on_progress=update_progress,
                max_pubmed=12,
                max_semantic=6,
                include_web_fallback=True,
            )
            yield

            # Step 3: Classify evidence levels
            stats = scientific_context.search_stats
            total_articles = len(scientific_context.articles)

            self.research_status = (
                f"Procesando {total_articles} artículos científicos..."
            )
            self.research_progress = 65
            self.research_steps[1]["status"] = "completed"
            self.research_steps = self.research_steps + [
                {
                    "step": 3,
                    "title": f"Clasificando evidencia ({total_articles} artículos)",
                    "status": "in_progress",
                    "icon": "📊",
                }
            ]
            yield

            # Build comprehensive prompt with scientific evidence and user preferences
            user_preferences = {
                "format": self.research_format_preference,
                "include_references": self.research_include_references,
                "evidence_focus": self.research_evidence_focus,
                "clarification_answers": self.research_clarification_answers,
            }
            research_prompt = build_scientific_research_prompt(
                scientific_context, user_preferences=user_preferences
            )

            # Step 4: LLM synthesis with evidence
            self.research_status = "Sintetizando evidencia científica..."
            self.research_progress = 70
            self.research_steps[2]["status"] = "completed"
            self.research_steps = self.research_steps + [
                {
                    "step": 4,
                    "title": "Síntesis basada en evidencia",
                    "status": "in_progress",
                    "icon": "🧬",
                }
            ]
            yield

            # Call LLM with enriched scientific context
            async with httpx.AsyncClient(timeout=240.0) as client:
                self.research_progress = 75
                self.research_status = "Generando informe científico..."
                yield

                response = await client.post(
                    f"{self.api_url}/api/v1/query",
                    json={
                        "query": research_prompt,
                        "user_type": "professional",
                        "temperature": 0.3,  # Lower temperature for scientific accuracy
                        "max_tokens": 6000,  # More tokens for detailed report
                    },
                )

                if response.status_code == 200:
                    self.research_progress = 90
                    self.research_status = "Formateando referencias..."
                    self.research_steps[3]["status"] = "completed"
                    self.research_steps = self.research_steps + [
                        {
                            "step": 5,
                            "title": "Generación de informe final",
                            "status": "in_progress",
                            "icon": "📝",
                        }
                    ]
                    yield

                    data = response.json()
                    result_content = data.get("response", "")

                    # Fallback if LLM response is empty but we have scientific articles
                    if not result_content.strip() and scientific_context.articles:
                        result_content = (
                            f"## Resultados de la Investigación: {query}\n\n"
                        )
                        result_content += f"Se encontraron **{total_articles}** artículos científicos relevantes.\n\n"
                        result_content += "### Artículos Destacados\n\n"
                        for i, article in enumerate(scientific_context.articles[:5], 1):
                            result_content += f"**{i}. {article.title}**\n"
                            result_content += f"- Autores: {article.authors_short}\n"
                            result_content += (
                                f"- Publicación: {article.journal} ({article.year})\n"
                            )
                            if article.abstract:
                                result_content += (
                                    f"- Resumen: {article.abstract[:300]}...\n"
                                )
                            result_content += "\n"

                    self.research_result = (
                        result_content
                        if result_content.strip()
                        else "No se obtuvo respuesta del servidor. Intente nuevamente."
                    )

                    # Format SCIENTIFIC sources with evidence levels
                    self.research_sources = format_scientific_sources(
                        scientific_context.articles
                    )

                    # Add search statistics to steps
                    self.research_steps[4]["status"] = "completed"
                    self.research_steps = self.research_steps + [
                        {
                            "step": 6,
                            "title": "Investigación completada",
                            "status": "completed",
                            "icon": "✅",
                            "stats": {
                                "pubmed": stats.get("pubmed_found", 0),
                                "semantic_scholar": stats.get(
                                    "semantic_scholar_found", 0
                                ),
                                "high_evidence": stats.get("high_evidence", 0),
                                "moderate_evidence": stats.get("moderate_evidence", 0),
                            },
                        }
                    ]

                    self.research_progress = 100
                    self.research_status = f"Investigación completada: {total_articles} artículos analizados"

                    # Save to artifacts with scientific metadata
                    self.saved_research.append(
                        {
                            "query": self.research_query,
                            "result": self.research_result,
                            "sources": self.research_sources,
                            "steps": self.research_steps,
                            "timestamp": datetime.now().isoformat(),
                            "search_stats": stats,
                            "total_articles": total_articles,
                        }
                    )
                else:
                    error_detail = (
                        response.text[:200] if response.text else "Sin detalles"
                    )
                    self.research_error = (
                        f"Error del servidor: {response.status_code} - {error_detail}"
                    )

        except httpx.TimeoutException:
            self.research_error = "La investigación excedió el tiempo de espera (4 minutos). Intente con una consulta más específica."
        except Exception as e:
            self.research_error = f"Error en investigación científica: {str(e)}"
        finally:
            self.research_loading = False
            yield

    @rx.event
    def export_research_pdf(self):
        """Export research results to real PDF."""
        if not self.research_result:
            yield rx.toast.error("No hay resultados de investigación para exportar")
            return

        try:
            pdf_bytes = generate_research_pdf(
                query=self.research_query,
                result=self.research_result,
                sources=self.research_sources,
                steps=self.research_steps,
                user_mode=self.user_type.title(),
            )
            yield rx.download(
                data=pdf_bytes,
                filename=f"medex_research_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            )
        except Exception as e:
            print(f"PDF export error: {e}")
            yield rx.toast.error(f"Error al exportar PDF: {str(e)}")
            return None

    # =========================================================================
    # ARTIFACT CATALOG SYSTEM
    # =========================================================================

    def _next_artifact_id(self) -> str:
        """Generate unique artifact ID."""
        self._artifact_counter += 1
        return f"artifact_{self._artifact_counter}_{datetime.now().strftime('%H%M%S')}"

    def _create_interaction_artifact(
        self, interaction: Interaction, index: int
    ) -> dict:
        """Create an artifact card from an interaction.

        IMPORTANT: All data must be stored in extra_data for PDF fallback.
        """
        severity_map = {
            "critical": {"label": "Crítica", "color": "red"},
            "high": {"label": "Alta", "color": "orange"},
            "moderate": {"label": "Moderada", "color": "yellow"},
            "low": {"label": "Baja", "color": "green"},
        }
        sev = severity_map.get(interaction.severity, {"label": "Info", "color": "blue"})

        # Build full content
        full_content = f"""## {interaction.drug_a} + {interaction.drug_b}

**Severidad:** {sev["label"]}

### Mecanismo
{interaction.mechanism}

### Efecto Clínico
{interaction.clinical_effect}

### Manejo Recomendado
{interaction.management}
"""

        return {
            "id": self._next_artifact_id(),
            "type": "interaction",
            "number": index + 1,
            "title": f"Interacción #{index + 1}",
            "subtitle": f"{interaction.drug_a} + {interaction.drug_b}",
            "severity": interaction.severity,
            "severity_label": sev["label"],
            "severity_color": sev["color"],
            "summary": interaction.mechanism[:150] + "..."
            if len(interaction.mechanism) > 150
            else interaction.mechanism,
            "full_content": full_content,
            "timestamp": datetime.now().isoformat(),
            "is_new": True,
            # Store ALL data for PDF fallback
            "extra_data": {
                "drug_a": interaction.drug_a,
                "drug_b": interaction.drug_b,
                "severity": interaction.severity,
                "severity_label": sev["label"],
                "mechanism": interaction.mechanism,
                "clinical_effect": interaction.clinical_effect,
                "management": interaction.management,
            },
        }

    def _create_dosage_artifact(
        self, drug: str, weight: str, age: str, result: str
    ) -> dict:
        """Create an artifact card from a dosage calculation."""
        return {
            "id": self._next_artifact_id(),
            "type": "dosage",
            "number": len(self.dosage_artifacts) + 1,
            "title": f"Dosis #{len(self.dosage_artifacts) + 1}",
            "subtitle": f"{drug} - {weight}kg, {age} años",
            "severity": "info",
            "severity_label": "Calculado",
            "severity_color": "blue",
            "summary": f"Cálculo de dosificación para {drug} en paciente de {weight}kg",
            "full_content": result,
            "timestamp": datetime.now().isoformat(),
            "is_new": True,
            # Store ALL data for PDF fallback
            "extra_data": {
                "drug": drug,
                "weight": weight,
                "age": age,
                "result": result,  # Full calculation result
            },
        }

    def _create_lab_artifact(self, lab_input: str, interpretation: str) -> dict:
        """Create an artifact card from a lab interpretation."""
        import re

        # Extract parameter values from input for subtitle
        input_lines = [l.strip() for l in lab_input.split("\n") if l.strip()]
        param_preview = (
            ", ".join(input_lines[:3]) if input_lines else "Valores analizados"
        )
        if len(input_lines) > 3:
            param_preview += "..."
        if len(param_preview) > 60:
            param_preview = param_preview[:57] + "..."

        # Create a VERY clean summary - just extract key findings
        # Start with empty summary and build from interpretation
        summary_parts = []

        # Try to extract diagnóstico principal if mentioned
        diag_match = re.search(
            r"(?:diagnóstico|conclusión|hallazgo)[:\s]+([^.\n]+)",
            interpretation,
            re.IGNORECASE,
        )
        if diag_match:
            summary_parts.append(diag_match.group(1).strip()[:60])

        # If no diagnosis found, just indicate interpretation available
        if not summary_parts:
            summary_parts.append("Interpretación disponible - Ver detalles")

        clean_summary = " • ".join(summary_parts)

        return {
            "id": self._next_artifact_id(),
            "type": "lab",
            "number": len(self.lab_artifacts) + 1,
            "title": f"Lab #{len(self.lab_artifacts) + 1}",
            "subtitle": param_preview,
            "severity": "info",
            "severity_label": "Interpretado",
            "severity_color": "purple",
            "summary": clean_summary,
            "full_content": interpretation,
            "timestamp": datetime.now().isoformat(),
            "is_new": True,
            # Store ALL data for PDF fallback
            "extra_data": {
                "input": lab_input,
                "interpretation": interpretation,  # Full interpretation
            },
        }

    @rx.event
    def open_artifact_modal_by_id(self, artifact_id: str, artifact_type: str):
        """Open modal to view full artifact content by ID.

        This method receives only primitive types (strings) to avoid
        serialization issues when called from rx.foreach.
        Creates a deep copy for active_artifact and forces list update for reactivity.
        """
        import copy

        artifact = None
        updated_list = []

        if artifact_type == "interaction":
            for a in self.interaction_artifacts:
                if a.get("id") == artifact_id:
                    artifact = copy.deepcopy(a)  # Deep copy for modal
                    a["is_new"] = False
                updated_list.append(a)
            # Force reactivity by reassigning list
            self.interaction_artifacts = updated_list

        elif artifact_type == "dosage":
            for a in self.dosage_artifacts:
                if a.get("id") == artifact_id:
                    artifact = copy.deepcopy(a)
                    a["is_new"] = False
                updated_list.append(a)
            self.dosage_artifacts = updated_list

        elif artifact_type == "lab":
            for a in self.lab_artifacts:
                if a.get("id") == artifact_id:
                    artifact = copy.deepcopy(a)
                    a["is_new"] = False
                updated_list.append(a)
            self.lab_artifacts = updated_list

        if artifact:
            # Create explicit dict to ensure all keys are present
            self.active_artifact = {
                "id": artifact.get("id", ""),
                "type": artifact.get("type", ""),
                "number": artifact.get("number", 0),
                "title": artifact.get("title", ""),
                "subtitle": artifact.get("subtitle", ""),
                "severity": artifact.get("severity", ""),
                "severity_label": artifact.get("severity_label", ""),
                "severity_color": artifact.get("severity_color", "blue"),
                "summary": artifact.get("summary", ""),
                "full_content": artifact.get("full_content", ""),
                "timestamp": artifact.get("timestamp", ""),
                "is_new": False,
                "extra_data": artifact.get("extra_data", {}),
            }
            self.show_artifact_modal = True

    @rx.event
    def open_artifact_modal(self, artifact: dict):
        """Open modal to view full artifact content (legacy, for non-foreach use)."""
        self.active_artifact = artifact
        self.show_artifact_modal = True
        # Mark as not new
        if artifact.get("type") == "interaction":
            for a in self.interaction_artifacts:
                if a.get("id") == artifact.get("id"):
                    a["is_new"] = False
        elif artifact.get("type") == "dosage":
            for a in self.dosage_artifacts:
                if a.get("id") == artifact.get("id"):
                    a["is_new"] = False
        elif artifact.get("type") == "lab":
            for a in self.lab_artifacts:
                if a.get("id") == artifact.get("id"):
                    a["is_new"] = False

    @rx.event
    def close_artifact_modal(self):
        """Close the artifact modal."""
        self.show_artifact_modal = False
        self.active_artifact = {}

    @rx.event
    def delete_artifact(self, artifact_id: str, artifact_type: str):
        """Delete an artifact from the catalog."""
        if artifact_type == "interaction":
            self.interaction_artifacts = [
                a for a in self.interaction_artifacts if a.get("id") != artifact_id
            ]
        elif artifact_type == "dosage":
            self.dosage_artifacts = [
                a for a in self.dosage_artifacts if a.get("id") != artifact_id
            ]
        elif artifact_type == "lab":
            self.lab_artifacts = [
                a for a in self.lab_artifacts if a.get("id") != artifact_id
            ]
        # Close modal if viewing deleted artifact
        if self.active_artifact.get("id") == artifact_id:
            self.show_artifact_modal = False
            self.active_artifact = {}

    @rx.event
    def export_artifact_pdf_by_id(self, artifact_id: str, artifact_type: str):
        """Export an artifact to PDF by its ID.

        This method receives only primitive types (strings) to avoid
        serialization issues when called from rx.foreach.
        """
        import copy

        # Find the artifact by ID - use deepcopy to avoid reference issues
        artifact = None
        if artifact_type == "interaction":
            for a in self.interaction_artifacts:
                if a.get("id") == artifact_id:
                    artifact = copy.deepcopy(a)
                    break
        elif artifact_type == "dosage":
            for a in self.dosage_artifacts:
                if a.get("id") == artifact_id:
                    artifact = copy.deepcopy(a)
                    break
        elif artifact_type == "lab":
            for a in self.lab_artifacts:
                if a.get("id") == artifact_id:
                    artifact = copy.deepcopy(a)
                    break

        if not artifact:
            yield rx.toast.error("Artefacto no encontrado")
            return

        # Get content - ensure we have actual content
        title = artifact.get("title", "Resultado MedeX")
        full_content = artifact.get("full_content", "")
        extra = artifact.get("extra_data", {})

        # If full_content is empty, reconstruct from extra_data (which stores all data)
        if not full_content or len(full_content.strip()) < 20:
            subtitle = artifact.get("subtitle", "")

            if artifact_type == "interaction":
                # Use complete data from extra_data
                mechanism = extra.get("mechanism", "No especificado")
                clinical_effect = extra.get("clinical_effect", "No especificado")
                management = extra.get("management", "Consultar con especialista")
                severity_label = extra.get(
                    "severity_label", artifact.get("severity_label", "N/A")
                )

                full_content = f"""## Interacción Medicamentosa

**Medicamentos:** {subtitle}
**Severidad:** {severity_label}

### Mecanismo
{mechanism}

### Efecto Clínico
{clinical_effect}

### Manejo Recomendado
{management}
"""
            elif artifact_type == "dosage":
                drug = extra.get("drug", "")
                weight = extra.get("weight", "")
                age = extra.get("age", "")
                # Use full result from extra_data if available
                result = extra.get("result", artifact.get("summary", ""))

                full_content = f"""## Cálculo de Dosificación

**Medicamento:** {drug}
**Peso del paciente:** {weight} kg
**Edad:** {age} años

### Resultado
{result}
"""
            elif artifact_type == "lab":
                lab_input = extra.get("input", "")
                # Use full interpretation from extra_data if available
                interpretation = extra.get(
                    "interpretation", artifact.get("summary", "")
                )

                full_content = f"""## Interpretación de Laboratorio

### Valores Analizados
{lab_input}

### Interpretación
{interpretation}
"""

        try:
            pdf_bytes = generate_pdf(title, full_content, self.user_type.title())
            yield rx.download(
                data=pdf_bytes,
                filename=f"medex_{artifact_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            )
            yield rx.toast.success("PDF exportado correctamente")
        except Exception as e:
            yield rx.toast.error(f"Error al exportar: {str(e)}")

    @rx.event
    def export_single_artifact_pdf(self, artifact: dict):
        """Export a single artifact to PDF."""
        try:
            title = artifact.get("title", "Resultado")
            content = artifact.get("full_content", "")
            pdf_bytes = generate_pdf(title, content, self.user_type.title())
            yield rx.download(
                data=pdf_bytes,
                filename=f"medex_{artifact.get('type', 'result')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            )
        except Exception as e:
            yield rx.toast.error(f"Error al exportar: {str(e)}")

    @rx.event
    def export_active_artifact_pdf(self):
        """Export the currently active artifact in modal to PDF."""
        if not self.active_artifact:
            yield rx.toast.error("No hay artefacto activo para exportar")
            return
        try:
            title = self.active_artifact.get("title", "Resultado")
            content = self.active_artifact.get("full_content", "")
            pdf_bytes = generate_pdf(title, content, self.user_type.title())
            yield rx.download(
                data=pdf_bytes,
                filename=f"medex_{self.active_artifact.get('type', 'result')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            )
        except Exception as e:
            yield rx.toast.error(f"Error al exportar: {str(e)}")

    @rx.event
    def clear_all_artifacts(self, artifact_type: str):
        """Clear all artifacts of a given type."""
        if artifact_type == "interaction":
            self.interaction_artifacts = []
        elif artifact_type == "dosage":
            self.dosage_artifacts = []
        elif artifact_type == "lab":
            self.lab_artifacts = []

    @rx.event
    def clear_interaction_artifacts(self):
        """Clear all interaction artifacts."""
        self.interaction_artifacts = []

    @rx.event
    def clear_dosage_artifacts(self):
        """Clear all dosage artifacts."""
        self.dosage_artifacts = []

    @rx.event
    def clear_lab_artifacts(self):
        """Clear all lab artifacts."""
        self.lab_artifacts = []
