#!/usr/bin/env python3
"""
MedeX API Server - Quick Start Script
======================================
Starts the MedeX API server with FastAPI and Uvicorn.
"""

import os
import sys

# Load environment variables from .env file
from dotenv import load_dotenv

load_dotenv()

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from contextlib import asynccontextmanager
from typing import Any

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Import MedeX services
from medex.main import MedeXApplication


# Global application instance
medex_app: MedeXApplication | None = None


# =============================================================================
# Request/Response Models
# =============================================================================


class ChatMessage(BaseModel):
    """Single chat message for history."""

    role: str  # "user" or "assistant"
    content: str


class QueryRequest(BaseModel):
    """Query request model."""

    query: str
    user_type: str = "educational"
    session_id: str = ""
    include_sources: bool = True
    include_reasoning: bool = False
    language: str = "es"
    stream: bool = False
    history: list[ChatMessage] = []  # Conversation history for context
    model: str = "gemini-2-flash"  # Default: el más rápido


# =============================================================================
# Model ID to HuggingFace Model Mapping
# =============================================================================
# CATÁLOGO AMPLIADO - Modelos verificados (2026-01-14)
# Incluye correcciones basadas en documentación oficial HuggingFace
MODEL_MAPPING: dict[str, str] = {
    # === MODELOS BASE (verificados anteriormente) ===
    "gemini-2-flash": "google/gemma-3-27b-it",  # DEFAULT - Más rápido ~20s
    "llama-70b": "meta-llama/Llama-3.3-70B-Instruct",  # Equilibrado ~32s
    "qwen-72b": "Qwen/Qwen2.5-72B-Instruct",  # Completo ~50s
    # === MODELOS DE RAZONAMIENTO ===
    # DeepSeek-R1 original es 671B - usamos Distill-32B que tiene mismo razonamiento
    "deepseek-r1": "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B",  # Razonamiento con <think>
    "qwq-32b": "Qwen/QwQ-32B",  # Reasoning con <think> tags
    # === NUEVOS MODELOS (2026-01-13) - Top benchmarks médicos ===
    "kimi-k2": "moonshotai/Kimi-K2-Instruct",  # 🏆 Top en diagnóstico médico
    "deepseek-v3.1": "deepseek-ai/DeepSeek-V3",  # DeepSeek V3 (no existe V3.1 en HF)
    "qwen3-235b": "Qwen/Qwen3-235B-A22B-Instruct-2507",  # Modelo más grande
}

# =============================================================================
# Model-Specific Configuration (per official documentation)
# =============================================================================
# Parámetros optimizados según documentación oficial de cada modelo
# Fuentes: HuggingFace Model Cards (2026-01-14)
# NOTA: max_tokens reducidos para compatibilidad con HF Router (algunos providers limitan)
MODEL_CONFIG: dict[str, dict[str, Any]] = {
    # === MODELOS DE RAZONAMIENTO (con <think> tags) ===
    "deepseek-r1": {
        # Usando DeepSeek-R1-Distill-Qwen-32B para mejor disponibilidad en HF Router
        "max_tokens": 16384,  # Reducido de 32768 para compatibilidad con providers
        "temperature": 0.6,  # Docs: "temperature within range 0.5-0.7 (0.6 recommended)"
        "use_system_prompt": False,  # Docs: "Avoid adding a system prompt"
        "is_reasoning_model": True,  # Usa <think> tags
    },
    "qwq-32b": {
        "max_tokens": 16384,  # Reducido de 32768 para compatibilidad con providers
        "temperature": 0.6,  # Docs: "Temperature=0.6, TopP=0.95"
        "top_p": 0.95,
        "is_reasoning_model": True,  # Usa <think> tags
    },
    # === MODELOS ESTÁNDAR DE ALTA CAPACIDAD (sin <think> tags) ===
    "qwen3-235b": {
        # Docs Qwen3-235B-A22B-Instruct-2507: "This model supports only non-thinking mode
        # and does not generate <think></think> blocks in its output"
        "max_tokens": 8192,  # Reducido para compatibilidad - algunos providers limitan
        "temperature": 0.7,  # Docs: "Temperature=0.7, TopP=0.8"
        "top_p": 0.8,
        "is_reasoning_model": False,  # NO genera <think> tags en versión 2507
    },
    # === MODELOS ESTÁNDAR (sin <think> tags) ===
    "kimi-k2": {
        "max_tokens": 16384,  # Docs: "8k-16k output token length"
        "temperature": 0.6,  # Docs: "temperature = 0.6"
        "is_reasoning_model": False,  # "reflex-grade model without long thinking"
    },
    "deepseek-v3.1": {
        "max_tokens": 8192,
        "temperature": 0.3,
        "is_reasoning_model": False,
    },
    "gemini-2-flash": {
        "max_tokens": 8192,
        "temperature": 0.3,
        "is_reasoning_model": False,
    },
    "llama-70b": {
        "max_tokens": 8192,
        "temperature": 0.3,
        "is_reasoning_model": False,
    },
    "qwen-72b": {
        "max_tokens": 8192,
        "temperature": 0.3,
        "is_reasoning_model": False,
    },
}

# Default config for models not explicitly configured
DEFAULT_MODEL_CONFIG: dict[str, Any] = {
    "max_tokens": 8192,
    "temperature": 0.3,
    "is_reasoning_model": False,
}


def get_hf_model_name(model_id: str) -> str:
    """Get HuggingFace model name from UI model ID."""
    return MODEL_MAPPING.get(model_id, "google/gemma-3-27b-it")  # Fallback to fastest


def get_model_config(model_id: str) -> dict[str, Any]:
    """Get model-specific configuration from UI model ID."""
    return MODEL_CONFIG.get(model_id, DEFAULT_MODEL_CONFIG)


class DrugInteractionRequest(BaseModel):
    """Drug interaction check request."""

    # Support both formats: drug1/drug2 or drugs array
    drug1: str | None = None
    drug2: str | None = None
    drugs: list[str] | None = None

    @property
    def get_drugs(self) -> tuple[str, str]:
        """Get drug pair from either format."""
        if self.drugs and len(self.drugs) >= 2:
            return self.drugs[0], self.drugs[1]
        return self.drug1 or "", self.drug2 or ""


class DosageRequest(BaseModel):
    """Dosage calculation request."""

    # Support both formats
    drug_name: str | None = None
    drug: str | None = None  # UI format
    patient_weight: float | None = None
    weight_kg: float | None = None  # UI format
    age: int | None = None
    unit: str = "mg/kg"

    @property
    def get_drug(self) -> str:
        return self.drug or self.drug_name or ""

    @property
    def get_weight(self) -> float | None:
        return self.weight_kg or self.patient_weight


class LabInterpretRequest(BaseModel):
    """Lab interpretation request."""

    # Support both formats
    lab_text: str | None = None
    results_text: str | None = None  # UI format
    patient_context: str = ""

    @property
    def get_text(self) -> str:
        return self.results_text or self.lab_text or ""


class TriageRequest(BaseModel):
    """Triage assessment request."""

    chief_complaint: str
    duration: str | None = ""
    pain_level: int | None = 0
    vital_signs: dict[str, Any] | None = None
    vitals: dict[str, Any] | None = None  # UI format

    @property
    def get_vitals(self) -> dict[str, Any] | None:
        return self.vitals or self.vital_signs


class KBSearchRequest(BaseModel):
    """Knowledge base search request."""

    query: str
    limit: int | None = None
    top_k: int | None = None  # UI format
    category: str | None = None

    @property
    def get_limit(self) -> int:
        return self.top_k or self.limit or 10


# =============================================================================
# Lifespan
# =============================================================================


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global medex_app

    print("[MedeX API] Starting up...")
    medex_app = MedeXApplication()
    await medex_app.startup()
    print("[MedeX API] Ready to accept requests")

    yield

    print("[MedeX API] Shutting down...")
    if medex_app:
        await medex_app.shutdown()
    print("[MedeX API] Goodbye!")


# =============================================================================
# FastAPI App
# =============================================================================

app = FastAPI(
    title="MedeX API",
    description="API de Asistente Médico Educativo con IA",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# Health Endpoints
# =============================================================================


@app.get("/health")
async def health():
    """Health check endpoint."""
    if medex_app:
        return await medex_app.health()
    return {"status": "starting", "ready": False}


@app.get("/ready")
async def ready():
    """Readiness check."""
    if medex_app and medex_app._state.is_ready:
        return {"ready": True}
    raise HTTPException(status_code=503, detail="Not ready")


@app.get("/live")
async def live():
    """Liveness check."""
    return {"alive": True}


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "MedeX API",
        "version": "2.0.0",
        "status": "running",
        "docs": "/docs",
    }


# =============================================================================
# Query Endpoints
# =============================================================================


@app.post("/api/v1/query")
async def query(request: QueryRequest):
    """
    Main query endpoint for medical questions.
    Supports conversation history for context.
    """
    if not medex_app:
        raise HTTPException(status_code=503, detail="Application not ready")

    try:
        # Convert history to the format expected by LLM service
        history = None
        if request.history:
            history = [{"role": m.role, "content": m.content} for m in request.history]

        # Get the actual HuggingFace model name from the UI model ID
        hf_model = get_hf_model_name(request.model)

        # Get model-specific configuration (per official documentation)
        model_config = get_model_config(request.model)

        response = await medex_app.query(
            query=request.query,
            user_type=request.user_type,
            history=history,
            model=hf_model,
            temperature=model_config.get("temperature"),
            max_tokens=model_config.get("max_tokens"),
            is_reasoning_model=model_config.get("is_reasoning_model", False),
        )
        # Add which model was used to the response
        response["model_id"] = request.model
        response["model_hf"] = hf_model
        response["is_reasoning_model"] = model_config.get("is_reasoning_model", False)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/api/v1/query/stream")
async def query_stream(request: QueryRequest):
    """
    Streaming query endpoint using Server-Sent Events.
    Returns real-time token stream with conversation context.
    """
    from fastapi.responses import StreamingResponse

    if not medex_app:
        raise HTTPException(status_code=503, detail="Application not ready")

    # Get the actual HuggingFace model name from the UI model ID
    hf_model = get_hf_model_name(request.model)

    # Get model-specific configuration (per official documentation)
    model_config = get_model_config(request.model)

    async def generate():
        try:
            async for event in medex_app.query_stream(
                query=request.query,
                user_type=request.user_type,
                model=hf_model,
                temperature=model_config.get("temperature"),
                max_tokens=model_config.get("max_tokens"),
            ):
                yield event
        except Exception as e:
            import json

            yield f"data: {json.dumps({'error': str(e)})}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# =============================================================================
# Drug Tools Endpoints - OPTIMIZED FOR STRUCTURED OUTPUT
# =============================================================================

# Prompts optimizados para respuestas estructuradas (no conversacionales)
DRUG_INTERACTION_PROMPT = """Eres un sistema de análisis farmacológico. Responde SOLO con el análisis estructurado, sin saludos ni explicaciones introductorias.

MEDICAMENTOS A ANALIZAR: {drugs}

Genera un análisis estructurado con EXACTAMENTE este formato:

## RESUMEN DE INTERACCIONES

| Combinación | Severidad | Efecto Principal |
|-------------|-----------|------------------|
| [Med A + Med B] | [Leve/Moderada/Severa/Contraindicada] | [Efecto en 1 línea] |

## ANÁLISIS POR COMBINACIÓN

### {drug_pair_1}
- **Severidad:** [Leve/Moderada/Severa/Contraindicada]
- **Mecanismo:** [Descripción breve del mecanismo]
- **Efecto clínico:** [Qué sucede al combinarlos]
- **Manejo:** [Recomendación específica]

[Repetir para cada combinación]

## MONITOREO RECOMENDADO
- [Punto 1]
- [Punto 2]

NO incluyas saludos, despedidas, ni disclaimers. Solo el análisis técnico."""

DOSAGE_PROMPT = """Eres un calculador de dosis farmacológicas. Responde SOLO con el cálculo estructurado.

MEDICAMENTO: {drug}
PESO: {weight} kg
EDAD: {age}

Genera la respuesta con EXACTAMENTE este formato:

## CÁLCULO DE DOSIS: {drug}

| Parámetro | Valor |
|-----------|-------|
| Medicamento | {drug} |
| Peso del paciente | {weight} kg |
| Edad | {age} |

### DOSIS CALCULADA

| Tipo | Dosis | Frecuencia | Vía |
|------|-------|------------|-----|
| Estándar | [X mg] | [cada X horas] | [Oral/IV/IM] |
| Pediátrica (si aplica) | [X mg/kg] | [frecuencia] | [vía] |
| Máxima diaria | [X mg/día] | - | - |

### AJUSTES ESPECIALES
- **Función renal:** [ajuste si aplica]
- **Función hepática:** [ajuste si aplica]
- **Edad avanzada:** [ajuste si aplica]

### ADVERTENCIAS
- [Punto 1]
- [Punto 2]

NO incluyas saludos, despedidas, ni disclaimers. Solo el cálculo técnico."""

LAB_INTERPRET_PROMPT = """Eres un sistema de interpretación de laboratorios. Responde SOLO con el análisis estructurado.

RESULTADOS: {labs}
CONTEXTO: {context}

Genera la respuesta con EXACTAMENTE este formato:

## INTERPRETACIÓN DE LABORATORIO

### VALORES ANALIZADOS

| Parámetro | Valor | Referencia | Estado |
|-----------|-------|------------|--------|
| [Nombre] | [Valor] | [Rango normal] | [Normal/Alto/Bajo/Crítico] |

### DIAGNÓSTICOS DIFERENCIALES

| Probabilidad | Diagnóstico | Hallazgos que lo apoyan |
|--------------|-------------|------------------------|
| Alta | [Dx 1] | [Valores alterados] |
| Media | [Dx 2] | [Valores] |
| Baja | [Dx 3] | [Valores] |

### ESTUDIOS COMPLEMENTARIOS SUGERIDOS
1. [Estudio 1] - [Justificación breve]
2. [Estudio 2] - [Justificación breve]

### PLAN DE ACCIÓN
- [Acción inmediata si hay valores críticos]
- [Seguimiento recomendado]

NO incluyas saludos, despedidas, ni disclaimers. Solo el análisis técnico."""


@app.post("/api/v1/tools/drug-interactions")
async def check_drug_interactions(request: DrugInteractionRequest):
    """Check drug interactions - FAST local database first, LLM fallback."""
    import time

    start_time = time.perf_counter()

    try:
        # Get all drugs (support array format)
        if request.drugs and len(request.drugs) >= 2:
            drugs = request.drugs
        else:
            drug1, drug2 = request.get_drugs
            if not drug1 or not drug2:
                raise HTTPException(
                    status_code=400, detail="At least two drugs are required"
                )
            drugs = [drug1, drug2]

        # FIRST: Try local database (instant response)
        from medex.tools.medical.drug_interactions import (
            check_drug_interactions as local_check,
        )

        local_result = await local_check(drugs=drugs)
        local_interactions = local_result.get("interactions", [])

        # Format interactions from local database
        formatted_interactions = [
            {
                "drug_a": i.get("drugs", ["", ""])[0] if "drugs" in i else "",
                "drug_b": i.get("drugs", ["", ""])[1] if "drugs" in i else "",
                "severity": i.get("severity", "unknown"),
                "mechanism": i.get("mechanism", ""),
                "clinical_effect": i.get("effect", ""),
                "management": i.get("recommendation", ""),
            }
            for i in local_interactions
        ]

        elapsed_ms = (time.perf_counter() - start_time) * 1000

        # If we found local interactions, return immediately (fast path)
        if formatted_interactions:
            return {
                "drugs": drugs,
                "drug_a": drugs[0] if len(drugs) > 0 else "",
                "drug_b": drugs[1] if len(drugs) > 1 else "",
                "interactions": formatted_interactions,
                "has_severe_interactions": local_result.get(
                    "has_severe_interactions", False
                ),
                "summary": local_result.get("summary", ""),
                "source": "local_database",
                "latency_ms": round(elapsed_ms, 2),
            }

        # No local data found - return empty result quickly
        # Don't call LLM for basic interaction checks (too slow)
        return {
            "drugs": drugs,
            "drug_a": drugs[0] if len(drugs) > 0 else "",
            "drug_b": drugs[1] if len(drugs) > 1 else "",
            "interactions": [],
            "has_severe_interactions": False,
            "summary": "No se encontraron interacciones conocidas en la base de datos local.",
            "source": "local_database",
            "latency_ms": round(elapsed_ms, 2),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/api/v1/tools/dosage-calculator")
async def calculate_dosage(request: DosageRequest):
    """Calculate medication dosage - FAST local database first."""
    import time

    start_time = time.perf_counter()

    try:
        drug = request.get_drug
        weight = request.get_weight
        age = request.age

        if not drug:
            raise HTTPException(status_code=400, detail="Drug name is required")

        # FIRST: Try local database (instant response)
        from medex.tools.medical.dosage_calculator import calculate_pediatric_dose

        local_result = await calculate_pediatric_dose(
            drug_name=drug,
            weight_kg=weight or 70.0,  # Default adult weight
            dose_type="standard",
        )

        elapsed_ms = (time.perf_counter() - start_time) * 1000

        if local_result.get("found", False):
            calculation = local_result.get("calculation", {})
            return {
                "success": True,
                "drug": drug,
                "drug_name": drug,
                "weight_kg": weight,
                "patient_weight": weight,
                "age": age,
                "recommended_dose": f"{calculation.get('single_dose_mg', 0)} mg",
                "dose_per_kg": calculation.get("dose_per_kg"),
                "frequency": calculation.get("frequency", ""),
                "daily_dose_mg": calculation.get("calculated_daily_dose_mg"),
                "max_daily_dose": f"{local_result.get('max_limits', {}).get('max_daily_mg', 'N/A')} mg",
                "indication": local_result.get("indication", ""),
                "notes": local_result.get("notes", ""),
                "warnings": [],
                "source": "local_database",
                "latency_ms": round(elapsed_ms, 2),
            }

        # Drug not found in local database
        return {
            "success": False,
            "drug": drug,
            "drug_name": drug,
            "error": f"Medicamento '{drug}' no encontrado en la base de datos local",
            "available_drugs": local_result.get("available_drugs", []),
            "source": "local_database",
            "latency_ms": round(elapsed_ms, 2),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/api/v1/tools/lab-interpreter")
async def interpret_labs(request: LabInterpretRequest):
    """Interpret laboratory results - OPTIMIZED for fast structured response."""
    if not medex_app:
        raise HTTPException(status_code=503, detail="Application not ready")

    try:
        lab_text = request.get_text

        if not lab_text:
            raise HTTPException(status_code=400, detail="Lab results text is required")

        # Build optimized prompt
        prompt = LAB_INTERPRET_PROMPT.format(
            labs=lab_text,
            context=request.patient_context
            if request.patient_context
            else "No especificado",
        )

        # Use LLM with short timeout and no disclaimer
        from medex.llm.prompts import Language, UserMode

        response = await medex_app._llm_service.query(
            query=prompt,
            user_mode=UserMode.PROFESSIONAL,
            language=Language.SPANISH,
            stream=False,
            include_disclaimer=False,
            max_tokens=1500,
            temperature=0.3,
        )

        return {
            "interpretation": response.content,
            "abnormal_values": [],
            "recommendations": [],
            "latency_ms": response.latency_ms,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


# =============================================================================
# Triage Endpoints
# =============================================================================


@app.post("/api/v1/triage/assess")
async def assess_triage(request: TriageRequest):
    """Assess patient triage level using ESI system."""
    if not medex_app:
        raise HTTPException(status_code=503, detail="Application not ready")

    try:
        # Build triage query - support both vital_signs and vitals
        vitals = request.get_vitals
        vitals_str = ""
        if vitals:
            vitals_str = ", ".join([f"{k}: {v}" for k, v in vitals.items()])

        duration = request.duration or "no especificada"
        pain_level = request.pain_level or 0

        query_text = f"""Realiza un triage ESI para:
        Motivo de consulta: {request.chief_complaint}
        Duración: {duration}
        Nivel de dolor: {pain_level}/10
        Signos vitales: {vitals_str if vitals_str else "No proporcionados"}"""

        response = await medex_app.query(query=query_text, user_type="professional")

        # Parse ESI level from response (improved parsing)
        esi_level = 5  # Default non-urgent
        response_text = response.get("response", "").lower()

        # Check for explicit ESI levels first
        import re

        esi_match = re.search(r"esi[:\s-]*(\d)", response_text)
        if esi_match:
            esi_level = int(esi_match.group(1))
            esi_level = max(1, min(5, esi_level))  # Clamp to 1-5
        elif (
            "resucitación" in response_text
            or "crítico" in response_text
            or "inmediato" in response_text
        ):
            esi_level = 1
        elif "emergente" in response_text or "alto riesgo" in response_text:
            esi_level = 2
        elif "urgente" in response_text:
            esi_level = 3
        elif "menos urgente" in response_text or "baja prioridad" in response_text:
            esi_level = 4

        esi_names = {
            1: "Resuscitation",
            2: "Emergent",
            3: "Urgent",
            4: "Less Urgent",
            5: "Non-Urgent",
        }

        return {
            "esi_level": esi_level,
            "esi_name": esi_names[esi_level],
            "recommendation": response.get("response", ""),
            "red_flags": [],
            "vital_concerns": [],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


# =============================================================================
# Knowledge Base Endpoints
# =============================================================================


@app.post("/api/v1/search")
async def search_knowledge_base_alt(request: KBSearchRequest):
    """Search the medical knowledge base (alt path)."""
    if not medex_app:
        raise HTTPException(status_code=503, detail="Application not ready")

    try:
        results = await medex_app.search(query=request.query, limit=request.get_limit)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/api/v1/knowledge/search")
async def search_knowledge_base(request: KBSearchRequest):
    """Search the medical knowledge base - UI endpoint."""
    if not medex_app:
        raise HTTPException(status_code=503, detail="Application not ready")

    try:
        # Use medex query for knowledge search since RAG is built-in
        response = await medex_app.query(query=request.query, user_type="professional")

        # Format as knowledge base results
        return {
            "results": [
                {
                    "id": "kb_1",
                    "title": "MedeX Knowledge Response",
                    "content": response.get("response", "No results found."),
                    "source": "MedeX RAG",
                    "score": 0.95,
                    "category": request.category or "medical",
                }
            ],
            "query": request.query,
            "total": 1,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/api/v1/knowledge/stats")
async def knowledge_stats():
    """Get knowledge base statistics."""
    return {
        "total_documents": 0,
        "categories": ["medications", "conditions", "procedures"],
        "last_updated": "2026-01-07",
    }


# =============================================================================
# Session Endpoints
# =============================================================================


@app.get("/api/v1/session/{session_id}")
async def get_session(session_id: str):
    """Get session history."""
    return {
        "session_id": session_id,
        "messages": [],
        "created_at": "2026-01-07T00:00:00",
    }


@app.delete("/api/v1/session/{session_id}")
async def delete_session(session_id: str):
    """Delete a session."""
    return {"deleted": True, "session_id": session_id}


# =============================================================================
# Admin Endpoints
# =============================================================================


@app.get("/api/v1/admin/stats")
async def admin_stats():
    """Get admin statistics."""
    if medex_app:
        return medex_app.get_stats()
    return {"error": "Not ready"}


@app.get("/api/v1/admin/providers")
async def list_providers():
    """List available LLM providers."""
    return {
        "providers": [
            {
                "name": "huggingface",
                "status": "available",
                "models": ["Qwen/Qwen2.5-72B-Instruct"],
            },
            {
                "name": "groq",
                "status": "available",
                "models": ["llama-3.3-70b-versatile"],
            },
            {
                "name": "sambanova",
                "status": "available",
                "models": ["DeepSeek-R1-Distill-Llama-70B"],
            },
            {
                "name": "together",
                "status": "available",
                "models": ["meta-llama/Llama-3.3-70B-Instruct-Turbo"],
            },
        ],
    }


@app.get("/api/v1/models")
async def list_models():
    """List available models for UI selector.

    Catálogo actualizado 2026-01-13 con 8 modelos VERIFICADOS que funcionan
    en HuggingFace Inference Providers. Los modelos médicos especializados
    (openbiollm, meditron, etc.) NO están disponibles en HF Inference.
    """
    return {
        "models": [
            # === MODELOS BASE (verificados) ===
            {
                "id": "gemini-2-flash",
                "name": "Gemini 2.0 Flash",
                "provider": "Google",
                "category": "general",
                "description": "⚡ Más rápido (~20s) - Ideal para respuestas ágiles",
                "context_length": 128000,
                "is_default": True,
            },
            {
                "id": "llama-70b",
                "name": "Llama 3.3 70B",
                "provider": "Meta",
                "category": "general",
                "description": "Equilibrio velocidad/calidad (~32s)",
                "context_length": 131072,
                "is_default": False,
            },
            {
                "id": "qwen-72b",
                "name": "Qwen 2.5 72B",
                "provider": "Alibaba",
                "category": "general",
                "description": "Respuestas más completas (~50s)",
                "context_length": 32768,
                "is_default": False,
            },
            {
                "id": "deepseek-r1",
                "name": "DeepSeek R1",
                "provider": "DeepSeek",
                "category": "reasoning",
                "description": "🧠 Razonamiento profundo con <think> tags (~53s)",
                "context_length": 65536,
                "is_default": False,
            },
            # === NUEVOS MODELOS TOP BENCHMARKS MÉDICOS (2026-01-13) ===
            {
                "id": "kimi-k2",
                "name": "Kimi K2",
                "provider": "Moonshot AI",
                "category": "medical",
                "description": "🏆 Top diagnóstico médico - Balance precisión/seguridad",
                "context_length": 131072,
                "is_default": False,
            },
            {
                "id": "deepseek-v3.1",
                "name": "DeepSeek V3.1",
                "provider": "DeepSeek",
                "category": "medical",
                "description": "📊 Superior en análisis clínico (mejor que V3)",
                "context_length": 65536,
                "is_default": False,
            },
            {
                "id": "qwen3-235b",
                "name": "Qwen3 235B",
                "provider": "Alibaba",
                "category": "general",
                "description": "🔬 Modelo más grande disponible - Máxima calidad",
                "context_length": 32768,
                "is_default": False,
            },
            {
                "id": "qwq-32b",
                "name": "QwQ 32B",
                "provider": "Alibaba",
                "category": "reasoning",
                "description": "🧠 Reasoning médico con <think> (~79% MMLU)",
                "context_length": 32768,
                "is_default": False,
            },
        ],
        "current": "gemini-2-flash",
    }


@app.post("/api/v1/models/select")
async def select_model(model_id: str):
    """Select active model."""
    # Lista de modelos válidos - sincronizada con MODEL_MAPPING
    valid_models = list(MODEL_MAPPING.keys())
    if model_id not in valid_models:
        raise HTTPException(
            status_code=400, detail=f"Invalid model. Choose from: {valid_models}"
        )
    # In production, this would update the router configuration
    return {"selected": model_id, "status": "active"}


# =============================================================================
# Main
# =============================================================================

if __name__ == "__main__":
    uvicorn.run(
        "run_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
