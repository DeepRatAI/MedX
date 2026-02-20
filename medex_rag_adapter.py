#!/usr/bin/env python3
"""
🧬 MedeX SOTA Integration - Integración del RAG SOTA con MedeX
===========================================================================

Este módulo actúa como puente entre el sistema RAG SOTA y el sistema MedeX existente.
Proporciona compatibilidad hacia atrás mientras usa el nuevo sistema RAG mejorado.

MEJORAS INTEGRADAS:
- Embeddings médicos especializados (PubMedBERT)
- Búsqueda híbrida (Dense + BM25)
- Reranking con cross-encoder
- ChromaDB persistente
- Semantic chunking
- Query expansion médica

Author: MedeX AI Team
Version: 2.0.0
"""

import os
import sys
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MedeX-SOTA-Integration")

# Añadir path
sys.path.insert(0, os.path.dirname(__file__))

# Importar sistemas
try:
    from medical_rag_sota import MedicalRAGSOTA, SOTAConfig, RAGContext
    from medical_knowledge_base import MedicalKnowledgeBase

    SOTA_AVAILABLE = True
    logger.info("✅ Sistema RAG SOTA disponible")
except ImportError as e:
    SOTA_AVAILABLE = False
    logger.warning(f"⚠️ Sistema RAG SOTA no disponible: {e}")
    # Fallback al sistema antiguo
    from medical_rag_system import MedicalRAGSystem

# Fallback para sistema antiguo
try:
    from medical_rag_system import MedicalRAGSystem as LegacyRAGSystem

    LEGACY_AVAILABLE = True
except ImportError:
    LEGACY_AVAILABLE = False


class MedeXRAGAdapter:
    """
    Adaptador que proporciona interfaz unificada para ambos sistemas RAG.
    Usa SOTA si está disponible, fallback al sistema legacy si no.
    """

    def __init__(self, use_sota: bool = True, force_legacy: bool = False):
        """
        Inicializa el adaptador RAG.

        Args:
            use_sota: Intentar usar sistema SOTA si está disponible
            force_legacy: Forzar uso del sistema legacy (para testing)
        """
        self.use_sota_system = False
        self.rag_system = None
        self.knowledge_base = None

        # Decidir qué sistema usar
        if SOTA_AVAILABLE and use_sota and not force_legacy:
            try:
                self._init_sota_system()
                self.use_sota_system = True
                logger.info("🚀 Usando sistema RAG SOTA")
            except Exception as e:
                logger.warning(f"⚠️ Error inicializando SOTA, usando legacy: {e}")
                self._init_legacy_system()
        elif LEGACY_AVAILABLE:
            self._init_legacy_system()
            logger.info("📦 Usando sistema RAG legacy")
        else:
            raise RuntimeError("No hay sistema RAG disponible")

    def _init_sota_system(self):
        """Inicializa el sistema SOTA"""
        config = SOTAConfig()
        self.rag_system = MedicalRAGSOTA(config)
        self.knowledge_base = MedicalKnowledgeBase()

        # Indexar knowledge base si no hay documentos
        stats = self.rag_system.get_statistics()
        if stats["total_chunks"] == 0:
            logger.info("📚 Indexando base de conocimiento médico...")
            self.rag_system.index_from_knowledge_base(self.knowledge_base)

    def _init_legacy_system(self):
        """Inicializa el sistema legacy"""
        self.rag_system = LegacyRAGSystem()
        self.knowledge_base = MedicalKnowledgeBase()

    def get_contextual_information(
        self, query: str, user_type: str = "patient", urgency_level: str = "routine"
    ) -> Dict[str, Any]:
        """
        Obtiene información contextual para una consulta.
        Interfaz compatible con sistema legacy.

        Args:
            query: Consulta del usuario
            user_type: "patient" o "professional"
            urgency_level: "routine", "urgent", o "emergency"

        Returns:
            Dict con resultados formateados
        """
        is_emergency = urgency_level == "emergency"

        if self.use_sota_system:
            return self._get_sota_context(query, user_type, is_emergency)
        else:
            return self._get_legacy_context(query, user_type, urgency_level)

    def _get_sota_context(
        self, query: str, user_type: str, is_emergency: bool
    ) -> Dict[str, Any]:
        """Obtiene contexto del sistema SOTA"""

        # Búsqueda SOTA
        context: RAGContext = self.rag_system.search(
            query=query, user_type=user_type, is_emergency=is_emergency, top_k=5
        )

        # Formatear para compatibilidad con sistema existente
        general_results = []
        for result in context.results:
            formatted = {
                "title": result.chunk.source_doc_title,
                "category": result.chunk.category,
                "similarity_score": result.final_score,
                "source": result.chunk.source_doc_id,
            }

            if user_type == "professional":
                formatted["full_content"] = result.chunk.content
                formatted["technical_details"] = True
            else:
                formatted["simplified_content"] = self._simplify_content(
                    result.chunk.content
                )
                formatted["patient_friendly"] = True

            if result.chunk.emergency_relevant and is_emergency:
                formatted["emergency_relevant"] = True

            general_results.append(formatted)

        # Resultados de emergencia
        emergency_results = []
        if is_emergency:
            for result in context.results:
                if result.chunk.emergency_relevant:
                    emergency_results.append(result)

        return {
            "general_results": general_results,
            "emergency_results": emergency_results,
            "total_documents": context.total_chunks_searched,
            "search_query": query,
            "user_type": user_type,
            "urgency_level": "emergency" if is_emergency else "routine",
            "search_time_ms": context.search_time_ms,
            "citations": context.citations,
            "system": "SOTA",
        }

    def _get_legacy_context(
        self, query: str, user_type: str, urgency_level: str
    ) -> Dict[str, Any]:
        """Obtiene contexto del sistema legacy"""
        return self.rag_system.get_contextual_information(
            query=query, user_type=user_type, urgency_level=urgency_level
        )

    def _simplify_content(self, content: str) -> str:
        """Simplifica contenido para pacientes"""
        replacements = {
            "criterios diagnósticos": "señales que busca el médico",
            "diagnóstico diferencial": "otras posibles causas",
            "protocolo de tratamiento": "pasos del tratamiento",
            "contraindicaciones": "cuando no se debe usar",
        }

        result = content.lower()
        for term, replacement in replacements.items():
            result = result.replace(term, replacement)

        if len(result) > 300:
            result = result[:300] + "..."

        return result.capitalize()

    def search_similar_documents(
        self, query: str, top_k: int = 5, category_filter: Optional[str] = None
    ) -> List[Any]:
        """
        Busca documentos similares.
        Interfaz compatible con sistema legacy.
        """
        if self.use_sota_system:
            context = self.rag_system.search(query=query, top_k=top_k)
            return context.results
        else:
            return self.rag_system.search_similar_documents(
                query=query, top_k=top_k, category_filter=category_filter
            )

    def search_by_symptoms(self, symptoms: List[str], top_k: int = 5) -> List[Any]:
        """Busca condiciones por síntomas"""
        symptoms_query = f"síntomas: {', '.join(symptoms)}"

        if self.use_sota_system:
            context = self.rag_system.search(query=symptoms_query, top_k=top_k)
            return context.results
        else:
            return self.rag_system.search_by_symptoms(symptoms, top_k)

    def search_treatment_protocols(self, condition: str, top_k: int = 3) -> List[Any]:
        """Busca protocolos de tratamiento"""
        treatment_query = f"tratamiento protocolo manejo {condition}"

        if self.use_sota_system:
            context = self.rag_system.search(query=treatment_query, top_k=top_k)
            return context.results
        else:
            return self.rag_system.search_treatment_protocols(condition, top_k)

    def search_medication_info(
        self, medication_name: str, context: str = ""
    ) -> List[Any]:
        """Busca información de medicamentos"""
        med_query = f"medicamento {medication_name} {context}"

        if self.use_sota_system:
            rag_context = self.rag_system.search(query=med_query, top_k=5)
            return rag_context.results
        else:
            return self.rag_system.search_medication_info(medication_name, context)

    def search_emergency_protocols(self, emergency_type: str) -> List[Any]:
        """Busca protocolos de emergencia"""
        emergency_query = f"emergencia urgencia protocolo {emergency_type}"

        if self.use_sota_system:
            context = self.rag_system.search(
                query=emergency_query, is_emergency=True, top_k=5
            )
            return context.results
        else:
            return self.rag_system.search_emergency_protocols(emergency_type)

    def get_statistics(self) -> Dict[str, Any]:
        """Obtiene estadísticas del sistema"""
        if self.use_sota_system:
            return self.rag_system.get_statistics()
        else:
            return self.rag_system.get_statistics()

    def save_index(self, filepath: str = None):
        """Guarda índice (solo aplica a sistema legacy)"""
        if not self.use_sota_system and hasattr(self.rag_system, "save_index"):
            self.rag_system.save_index(filepath)

    def load_index(self, filepath: str = None):
        """Carga índice (solo aplica a sistema legacy)"""
        if not self.use_sota_system and hasattr(self.rag_system, "load_index"):
            self.rag_system.load_index(filepath)


def get_rag_context_formatted(
    query: str, user_type: str, is_emergency: bool, adapter: MedeXRAGAdapter = None
) -> str:
    """
    Función helper que formatea contexto RAG para el prompt del LLM.
    Compatible con el método get_rag_context de MEDEX_ULTIMATE_RAG.

    Args:
        query: Consulta del usuario
        user_type: "patient" o "professional"
        is_emergency: Si es emergencia
        adapter: Instancia del adaptador (crea una nueva si no se proporciona)

    Returns:
        String formateado con contexto RAG
    """
    if adapter is None:
        adapter = MedeXRAGAdapter()

    try:
        # Obtener contexto
        context_info = adapter.get_contextual_information(
            query=query,
            user_type=user_type,
            urgency_level="emergency" if is_emergency else "routine",
        )

        # Formatear para prompt
        context_parts = []

        if context_info.get("system") == "SOTA":
            context_parts.append("=== CONTEXTO RAG SOTA ===")
            context_parts.append(
                f"🔍 Búsqueda completada en {context_info.get('search_time_ms', 0):.1f}ms"
            )

        if context_info.get("general_results"):
            if is_emergency:
                context_parts.append("\n🚨 === INFORMACIÓN DE EMERGENCIA === 🚨")
            else:
                context_parts.append(
                    "\n=== INFORMACIÓN RELEVANTE DE BASE DE CONOCIMIENTO ==="
                )

            for i, result in enumerate(context_info["general_results"][:3], 1):
                context_parts.append(
                    f"\n[{i}] {result['title']} (Categoría: {result['category']})"
                )

                if user_type == "professional" and result.get("full_content"):
                    content = result["full_content"][:500]
                    context_parts.append(f"    {content}...")
                elif result.get("simplified_content"):
                    context_parts.append(f"    {result['simplified_content']}")

                if result.get("emergency_relevant") and is_emergency:
                    context_parts.append("    ⚠️ INFORMACIÓN CRÍTICA DE EMERGENCIA")

        # Citaciones si están disponibles
        if context_info.get("citations"):
            context_parts.append("\n📚 FUENTES:")
            for citation in context_info["citations"][:3]:
                context_parts.append(
                    f"  [{citation['number']}] {citation['title']} ({citation['category']})"
                )

        return "\n".join(context_parts)

    except Exception as e:
        logger.warning(f"⚠️ Error obteniendo contexto RAG: {e}")
        return ""


# ============================================================================
# TESTS
# ============================================================================


def test_adapter():
    """Test del adaptador RAG"""

    print("🧪 TESTING MEDEX RAG ADAPTER")
    print("=" * 60)

    # Crear adaptador
    adapter = MedeXRAGAdapter()

    print(f"\n📊 Sistema activo: {'SOTA' if adapter.use_sota_system else 'Legacy'}")

    # Test 1: Contexto para paciente
    print("\n🔍 TEST 1: Contexto para paciente")
    print("-" * 40)

    context = adapter.get_contextual_information(
        query="me duele el pecho cuando respiro",
        user_type="patient",
        urgency_level="routine",
    )

    print(f"  Resultados: {len(context.get('general_results', []))}")
    print(f"  Sistema: {context.get('system', 'legacy')}")

    # Test 2: Contexto para profesional
    print("\n🔍 TEST 2: Contexto para profesional")
    print("-" * 40)

    context = adapter.get_contextual_information(
        query="paciente masculino 65 años, dolor precordial, diaforesis",
        user_type="professional",
        urgency_level="emergency",
    )

    print(f"  Resultados: {len(context.get('general_results', []))}")
    print(f"  Tiempo: {context.get('search_time_ms', 'N/A')}ms")

    # Test 3: Contexto formateado
    print("\n🔍 TEST 3: Contexto formateado para LLM")
    print("-" * 40)

    formatted = get_rag_context_formatted(
        query="protocolo de manejo de infarto",
        user_type="professional",
        is_emergency=True,
        adapter=adapter,
    )

    print(formatted[:500] + "..." if len(formatted) > 500 else formatted)

    # Estadísticas
    print("\n📊 ESTADÍSTICAS")
    print("-" * 40)

    stats = adapter.get_statistics()
    for key, value in stats.items():
        if isinstance(value, dict):
            print(f"  {key}:")
            for k, v in value.items():
                print(f"    {k}: {v}")
        else:
            print(f"  {key}: {value}")

    print("\n✅ Tests del adaptador completados")
    return True


if __name__ == "__main__":
    test_adapter()
