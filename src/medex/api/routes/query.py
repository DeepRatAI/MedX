# =============================================================================
# MedeX - Query Routes
# =============================================================================
"""
Query endpoints for medical assistance.

Endpoints:
- POST /query - Synchronous medical query
- POST /stream - Streaming medical query
- POST /search - RAG search
"""

from __future__ import annotations

import time
import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

# =============================================================================
# Request/Response Models
# =============================================================================


@dataclass
class MedicalQueryRequest:
    """Request for medical query."""

    query: str
    user_type: str = "educational"  # educational, professional, research
    session_id: str | None = None
    stream: bool = False
    include_sources: bool = True
    include_reasoning: bool = False
    language: str = "es"
    patient_context: dict[str, Any] | None = None

    def validate(self) -> list[str]:
        """Validate request."""
        errors = []

        if not self.query or len(self.query.strip()) < 3:
            errors.append("Query must be at least 3 characters")

        if len(self.query) > 10000:
            errors.append("Query must be less than 10000 characters")

        if self.user_type not in ["educational", "professional", "research"]:
            errors.append(
                "user_type must be 'educational', 'professional', or 'research'"
            )

        if self.language not in ["es", "en", "pt"]:
            errors.append("Language must be 'es', 'en', or 'pt'")

        return errors


@dataclass
class Source:
    """Source document reference."""

    id: str
    title: str
    content: str
    score: float
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content[:500],  # Truncate for response
            "score": round(self.score, 3),
            "metadata": self.metadata,
        }


@dataclass
class MedicalQueryResponse:
    """Response to medical query."""

    query_id: str
    response: str
    user_type: str = "educational"

    # Clinical info
    is_emergency: bool = False
    triage_level: int | None = None
    diagnosis: dict[str, Any] | None = None
    treatment_plan: dict[str, Any] | None = None

    # Sources and reasoning
    sources: list[Source] = field(default_factory=list)
    reasoning_steps: list[str] = field(default_factory=list)

    # Metadata
    model_used: str | None = None
    tokens_used: int = 0
    duration_ms: float = 0
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "query_id": self.query_id,
            "response": self.response,
            "user_type": self.user_type,
            "is_emergency": self.is_emergency,
            "triage_level": self.triage_level,
            "sources": [s.to_dict() for s in self.sources],
            "model_used": self.model_used,
            "tokens_used": self.tokens_used,
            "duration_ms": round(self.duration_ms, 2),
            "created_at": self.created_at.isoformat(),
        }

        if self.diagnosis:
            result["diagnosis"] = self.diagnosis

        if self.treatment_plan:
            result["treatment_plan"] = self.treatment_plan

        if self.reasoning_steps:
            result["reasoning_steps"] = self.reasoning_steps

        return result


@dataclass
class StreamChunk:
    """Streaming response chunk."""

    type: str  # thinking, streaming, tool_call, rag_search, complete, error
    data: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "type": self.type,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
        }

    def to_sse(self) -> str:
        """Convert to Server-Sent Event format."""
        import json

        return f"data: {json.dumps(self.to_dict())}\n\n"


@dataclass
class SearchRequest:
    """RAG search request."""

    query: str
    collection: str = "medical_knowledge"
    limit: int = 10
    min_score: float = 0.5
    filters: dict[str, Any] | None = None

    def validate(self) -> list[str]:
        """Validate request."""
        errors = []

        if not self.query:
            errors.append("Query is required")

        if self.limit < 1 or self.limit > 100:
            errors.append("Limit must be between 1 and 100")

        if self.min_score < 0 or self.min_score > 1:
            errors.append("min_score must be between 0 and 1")

        return errors


@dataclass
class SearchResponse:
    """RAG search response."""

    query: str
    results: list[Source] = field(default_factory=list)
    total: int = 0
    duration_ms: float = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "query": self.query,
            "results": [r.to_dict() for r in self.results],
            "total": self.total,
            "duration_ms": round(self.duration_ms, 2),
        }


# =============================================================================
# Query Handler
# =============================================================================


class QueryHandler:
    """Handler for query endpoints."""

    def __init__(self) -> None:
        """Initialize query handler."""
        # Services would be injected here
        self._agent_service = None
        self._rag_service = None
        self._security_service = None

    async def query(self, request: MedicalQueryRequest) -> MedicalQueryResponse:
        """
        Handle synchronous medical query.

        Flow:
        1. Validate request
        2. Check security (PII, sanitization)
        3. Analyze intent
        4. Search knowledge base
        5. Generate response
        6. Format and return
        """
        start_time = time.time()
        query_id = str(uuid.uuid4())

        # Validate
        errors = request.validate()
        if errors:
            raise ValueError(f"Validation errors: {', '.join(errors)}")

        # Simulate agent processing
        # In production: response = await self._agent_service.process(request)

        response = MedicalQueryResponse(
            query_id=query_id,
            response=self._generate_mock_response(request),
            user_type=request.user_type,
            is_emergency=self._detect_emergency(request.query),
            triage_level=self._calculate_triage(request.query),
            sources=[
                Source(
                    id="src_1",
                    title="Medical Reference",
                    content="Sample medical content...",
                    score=0.92,
                ),
            ],
            model_used="groq/llama-3.3-70b-versatile",
            tokens_used=1500,
            duration_ms=(time.time() - start_time) * 1000,
        )

        return response

    async def stream(
        self,
        request: MedicalQueryRequest,
    ) -> AsyncGenerator[StreamChunk, None]:
        """
        Handle streaming medical query.

        Yields chunks for:
        - Thinking/processing status
        - Tool calls
        - RAG searches
        - Token-by-token response
        - Final complete response
        """
        query_id = str(uuid.uuid4())

        # Validate
        errors = request.validate()
        if errors:
            yield StreamChunk(
                type="error",
                data={"message": f"Validation errors: {', '.join(errors)}"},
            )
            return

        # Yield thinking status
        yield StreamChunk(
            type="thinking",
            data={"message": "Analizando consulta médica..."},
        )

        # Simulate RAG search
        yield StreamChunk(
            type="rag_search",
            data={"query": request.query[:50], "results_count": 5},
        )

        # Simulate tool calls
        if "dosis" in request.query.lower() or "medicamento" in request.query.lower():
            yield StreamChunk(
                type="tool_call",
                data={"tool": "drug_interactions_checker", "status": "executing"},
            )

        # Stream response tokens
        mock_response = self._generate_mock_response(request)
        words = mock_response.split()

        for i, word in enumerate(words):
            yield StreamChunk(
                type="streaming",
                data={"chunk": word + " ", "token_count": i + 1},
            )

        # Yield final response
        yield StreamChunk(
            type="complete",
            data={
                "query_id": query_id,
                "response": mock_response,
                "sources": [
                    {"id": "src_1", "title": "Medical Reference", "score": 0.92}
                ],
                "tokens_used": len(words),
            },
        )

    async def search(self, request: SearchRequest) -> SearchResponse:
        """
        Handle RAG search request.

        Returns matching documents from the knowledge base.
        """
        start_time = time.time()

        # Validate
        errors = request.validate()
        if errors:
            raise ValueError(f"Validation errors: {', '.join(errors)}")

        # Simulate search
        # In production: results = await self._rag_service.search(request)

        results = [
            Source(
                id=f"doc_{i}",
                title=f"Medical Document {i}",
                content=f"Content related to {request.query}...",
                score=0.95 - (i * 0.05),
                metadata={"category": "medical", "source": "pubmed"},
            )
            for i in range(min(request.limit, 5))
        ]

        return SearchResponse(
            query=request.query,
            results=results,
            total=len(results),
            duration_ms=(time.time() - start_time) * 1000,
        )

    def _generate_mock_response(self, request: MedicalQueryRequest) -> str:
        """Generate mock response for demonstration."""
        user_type = request.user_type

        if user_type == "professional":
            return (
                "Basándose en la evidencia clínica actual y las guías de práctica clínica, "
                "se recomienda considerar el siguiente enfoque diagnóstico y terapéutico para "
                "la presentación clínica descrita. Los estudios de laboratorio e imagen pertinentes "
                "incluyen hemograma completo, panel metabólico y estudios de imagen según indicación clínica."
            )
        elif user_type == "research":
            return (
                "La literatura médica actual presenta varios estudios relevantes sobre este tema. "
                "Un metaanálisis reciente (2024) demostró una eficacia significativa con un IC 95% "
                "de [0.72-0.89] y un NNT de 8. Se sugiere revisar las referencias adjuntas para "
                "mayor profundidad metodológica."
            )
        else:  # educational
            return (
                "Entiendo tu consulta. Es importante recordar que esta información es educativa y "
                "no reemplaza la consulta con un profesional de salud. Basándome en tu pregunta, "
                "puedo explicarte los conceptos generales relacionados con este tema de salud. "
                "Si tienes síntomas o preocupaciones específicas, te recomiendo consultar a un médico."
            )

    def _detect_emergency(self, query: str) -> bool:
        """Detect if query indicates emergency."""
        emergency_keywords = [
            "infarto",
            "stroke",
            "convulsion",
            "no respira",
            "inconsciente",
            "sangrado",
            "suicidio",
            "envenenamiento",
        ]
        query_lower = query.lower()
        return any(kw in query_lower for kw in emergency_keywords)

    def _calculate_triage(self, query: str) -> int:
        """Calculate ESI triage level (1-5)."""
        if self._detect_emergency(query):
            return 1
        # Simplified triage logic
        return 4  # Default to ESI-4 for educational queries


# =============================================================================
# Factory Functions
# =============================================================================


def create_query_handler() -> QueryHandler:
    """Create query handler with dependencies."""
    return QueryHandler()
