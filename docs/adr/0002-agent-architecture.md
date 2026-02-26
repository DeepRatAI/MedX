# ADR-0002: Arquitectura Multi-Agente Médica

**Fecha:** 2026-01-15  
**Estado:** Aceptado  
**Autor:** Gonzalo

## Contexto

MedeX es un asistente médico que necesita manejar múltiples tipos de consultas:
consultas simples de chat, uso de herramientas especializadas (interacciones
medicamentosas, dosificación, interpretación de laboratorio), triage de emergencia,
investigación profunda con fuentes externas y análisis de imágenes médicas.

Un enfoque monolítico con un solo prompt y un solo modelo LLM no escala para:
- Diferentes niveles de criticidad (emergencia vs. consulta informativa)
- Diferentes fuentes de conocimiento (base local vs. PubMed vs. web)
- Diferentes latencias aceptables (triage inmediato vs. investigación exhaustiva)
- Presupuestos de tokens variables por tipo de consulta

## Decisión

**Adoptar una arquitectura de controlador-agente con routing inteligente.**

### Componentes

```
┌─────────────────────────────────────────────────┐
│                  Controller                      │
│  (agent/controller.py)                          │
│  - Intent analysis                              │
│  - Route selection                              │
│  - Context assembly                             │
│  - Response orchestration                       │
└──────────┬──────────────────────────────────────┘
           │
    ┌──────┴──────┐
    │   Planner   │  (agent/planner.py)
    │   + Intent  │  (agent/intent_analysis.py)
    └──────┬──────┘
           │
  ┌────────┼────────┬────────────┬──────────┐
  ▼        ▼        ▼            ▼          ▼
┌─────┐ ┌─────┐ ┌────────┐ ┌────────┐ ┌────────┐
│Chat │ │Tools│ │Triage  │ │Deep    │ │Vision  │
│     │ │     │ │        │ │Research│ │        │
│ LLM │ │Local│ │Detect +│ │RAG +   │ │Image   │
│ only│ │calc │ │LLM     │ │Sources │ │Analysis│
└─────┘ └─────┘ └────────┘ └────────┘ └────────┘
```

### Routing

El `IntentAnalyzer` clasifica cada consulta del usuario y el `Controller` la
enruta al subsistema apropiado:

| Intent | Subsistema | Modelo | Latencia |
|--------|-----------|--------|----------|
| Consulta general | Chat (LLM) | Kimi K2 | ~2-5s |
| Interacción medicamentosa | Tools (local) | Ninguno | <100ms |
| Dosificación | Tools (local) | Ninguno | <100ms |
| Valores de laboratorio | Tools (local) | Ninguno | <100ms |
| Emergencia detectada | Triage | Detection + LLM | ~1-3s |
| Investigación profunda | Deep Research | RAG + LLM | ~30-120s |
| Imagen médica | Vision | LLM multimodal | ~5-15s |

### Principios de Diseño

1. **Herramientas locales sin LLM**: Las calculadoras de dosificación, interacciones
   medicamentosas e interpretación de laboratorio operan con lógica determinista
   (base de conocimiento local de 1061 condiciones). No requieren llamada a LLM,
   lo que garantiza respuestas instantáneas y reproducibles.

2. **Detección de emergencia como guardia**: Antes de cualquier routing, el
   `EmergencyDetector` evalúa la consulta. Si detecta una emergencia, el triage
   se activa inmediatamente, bypasseando el routing normal.

3. **Memoria contextual por sesión**: El `MemoryService` mantiene una ventana de
   contexto por sesión del usuario, permitiendo consultas de seguimiento sin
   repetir información clínica.

4. **Multi-modelo**: El `LLMRouter` puede dirigir consultas a diferentes modelos
   según el tipo de tarea (razonamiento complejo vs. respuesta rápida).

## Consecuencias

### Positivas

- Latencia optimizada por tipo de consulta
- Las herramientas locales funcionan offline (sin dependencia de API externa)
- La detección de emergencia es determinista y no depende de un LLM
- Los módulos son independientemente testables
- Nuevas herramientas se agregan sin modificar el controller

### Negativas

- Complejidad de routing: errores en clasificación de intent llevan a respuestas
  incorrectas
- El `IntentAnalyzer` mismo puede requerir un LLM, añadiendo latencia
- Mantener coherencia entre módulos (misma terminología, mismo nivel de detalle)
  requiere disciplina

### Trade-offs Aceptados

- **Controller centralizado vs. orquestador distribuido**: Se eligió un controller
  centralizado por simplicidad. Si la cantidad de agentes crece >10, se
  reconsiderará un orquestador basado en grafos (LangGraph, AutoGen).

- **Herramientas deterministas vs. LLM-powered**: Las herramientas médicas usan
  lógica determinista para garantizar reproducibilidad y auditabilidad. El trade-off
  es que no pueden manejar casos ambiguos o fuera de su base de conocimiento.

## Implementación

### Estructura de Archivos

```
src/medex/
├── agent/
│   ├── controller.py       # Controlador principal, orquesta el flujo
│   ├── planner.py          # Planificación de acciones
│   └── intent_analysis.py  # Clasificación de intents del usuario
├── detection/
│   └── emergency.py        # Detección de emergencia (determinista)
├── tools/
│   ├── drug_interactions.py    # Interacciones medicamentosas
│   ├── dosage_calculator.py    # Calculadora de dosificación
│   ├── lab_interpreter.py      # Interpretación de laboratorio
│   └── triage.py               # Motor de triage
├── llm/
│   ├── router.py           # Routing multi-modelo
│   ├── parser.py           # Parsing de respuestas LLM
│   └── streaming.py        # Streaming de tokens
├── rag/
│   ├── chunker.py          # Chunking de documentos
│   ├── embedder.py         # Generación de embeddings
│   └── reranker.py         # Re-ranking de resultados
└── memory/
    └── memory_service.py   # Gestión de contexto conversacional
```

### Extensibilidad

Para agregar una nueva herramienta:

1. Crear módulo en `src/medex/tools/`
2. Registrar en `IntentAnalyzer` el nuevo intent
3. Agregar routing en `Controller`
4. Agregar panel de UI en `app.py`
5. Agregar estado en `state.py`
6. Escribir tests en `tests/`
