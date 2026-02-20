# 🏗️ MedeX V2 - Arquitectura Completa

> **Fecha de definición**: 2026-01-06  
> **Estado**: Diseño aprobado, pendiente implementación  
> **Costo total**: $0 (todo open source/gratuito)

---

## 📋 ÍNDICE

1. [Visión General](#1-visión-general)
2. [Arquitectura de UX](#2-arquitectura-de-ux)
3. [Sistema de Memoria](#3-sistema-de-memoria)
4. [Tools - 3 Tiers](#4-tools---3-tiers)
5. [Capacidades Agénticas](#5-capacidades-agénticas)
6. [Stack Técnico](#6-stack-técnico)
7. [Plan de Implementación](#7-plan-de-implementación)

---

## 1. VISIÓN GENERAL

### Principio de Diseño

> **"El mejor diseño es invisible"** - El usuario habla naturalmente, el sistema decide qué herramientas usar.

### Cambios Clave vs MedeX Actual

| Aspecto      | MedeX Actual               | MedeX V2                                          |
| ------------ | -------------------------- | ------------------------------------------------- |
| **Interfaz** | Chat simple, sin historial | Chat con sidebar de conversaciones (tipo ChatGPT) |
| **Memoria**  | Sin persistencia           | PostgreSQL + Redis                                |
| **RAG**      | Falso (solo prompting)     | Real (Qdrant + embeddings)                        |
| **Tools**    | Solo Kimi $web_search      | 25+ tools para todos los LLMs                     |
| **Agentes**  | Ninguno                    | Orquestador + agentes especializados              |
| **Contexto** | Por mensaje                | Por conversación + paciente                       |

---

## 2. ARQUITECTURA DE UX

### Layout Principal

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           MEDEX V2                                       │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────┐  ┌───────────────────────────────────────────┐ │
│  │  💬 Conversaciones  │  │  📋 Contexto del Caso (colapsable)        │ │
│  │  ─────────────────  │  │  ─────────────────────────────────────    │ │
│  │  🔍 Buscar...       │  │  Paciente: M, 45 años                     │ │
│  │                     │  │  Dx: DM2, HTA | Meds: Metformina          │ │
│  │  📋 Caso celíaco... │  │  Alergias: Penicilinas                    │ │
│  │  📋 DDx cefalea     │  │  [Editar] [Limpiar]                       │ │
│  │  📋 Interacciones.. │  └───────────────────────────────────────────┘ │
│  │  📋 Score CURB-65   │                                                │
│  │                     │  ┌───────────────────────────────────────────┐ │
│  │  ─────────────────  │  │                                           │ │
│  │  📁 Archivadas      │  │         ÁREA DE CHAT PRINCIPAL            │ │
│  │                     │  │                                           │ │
│  │  ─────────────────  │  │  [Mensajes con formato markdown]          │ │
│  │  ➕ Nueva conv.     │  │                                           │ │
│  │                     │  │  🔍 Consultando KB...                     │ │
│  │                     │  │  💊 Verificando interacciones...          │ │
│  │                     │  │                                           │ │
│  │                     │  ├───────────────────────────────────────────┤ │
│  │                     │  │  💬 Escribe tu consulta médica...    [➤]  │ │
│  └─────────────────────┘  └───────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
```

### Funcionalidades de Conversaciones

| Feature                   | Descripción                                            |
| ------------------------- | ------------------------------------------------------ |
| **Historial persistente** | Todas las conversaciones guardadas en PostgreSQL       |
| **Búsqueda**              | Por texto en título/contenido                          |
| **Auto-título**           | Generado del primer mensaje (ej: "DDx dolor torácico") |
| **Archivar**              | Mover conversaciones antiguas a carpeta archivadas     |
| **Exportar**              | PDF o Markdown de una conversación                     |
| **Continuar**             | Retomar cualquier conversación con contexto completo   |

### Indicadores de Tools (Sutiles)

Cuando el agente usa tools, mostrar discretamente bajo el input:

```
🔍 Consultando base de conocimiento...
💊 Verificando interacciones medicamentosas...
📊 Calculando score CURB-65...
✅ Análisis completado
```

---

## 3. SISTEMA DE MEMORIA

### Arquitectura de Datos

```
┌─────────────────────────────────────────────────────────────────┐
│                     CAPA DE PERSISTENCIA                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐  │
│  │ PostgreSQL  │    │    Redis    │    │      Qdrant         │  │
│  │             │    │             │    │                     │  │
│  │ - Users     │    │ - Session   │    │ - KB embeddings     │  │
│  │ - Convs     │    │ - Context   │    │ - Conv embeddings   │  │
│  │ - Messages  │    │ - Cache LLM │    │ - Búsqueda semántica│  │
│  │ - Patients  │    │             │    │                     │  │
│  └─────────────┘    └─────────────┘    └─────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Modelos de Datos (PostgreSQL)

```python
# ============================================
# USUARIOS
# ============================================
class User:
    id: UUID
    email: str
    name: str
    role: "professional" | "educational"
    specialty: Optional[str]  # Cardiología, Pediatría, etc.
    preferences: JSON  # idioma, tema, etc.
    created_at: datetime
    last_login: datetime

# ============================================
# CONVERSACIONES
# ============================================
class Conversation:
    id: UUID
    user_id: UUID  # FK -> User
    title: str  # Auto-generado o editado
    status: "active" | "archived"
    patient_context_id: Optional[UUID]  # FK -> PatientContext
    created_at: datetime
    updated_at: datetime
    message_count: int

class Message:
    id: UUID
    conversation_id: UUID  # FK -> Conversation
    role: "user" | "assistant" | "system"
    content: str  # Markdown
    tools_used: List[str]  # ["check_interactions", "calculate_gfr"]
    model_used: str  # "kimi-k2", "qwen-72b", etc.
    tokens_used: int
    latency_ms: int
    created_at: datetime

# ============================================
# CONTEXTO DE PACIENTE (extraído automáticamente)
# ============================================
class PatientContext:
    id: UUID
    conversation_id: UUID  # FK -> Conversation
    age: Optional[int]
    sex: Optional["M" | "F"]
    weight_kg: Optional[float]
    height_cm: Optional[float]
    conditions: List[str]  # ["DM2", "HTA", "EPOC"]
    medications: List[str]  # ["Metformina 850mg", "Losartán 50mg"]
    allergies: List[str]  # ["Penicilinas", "AINEs"]
    lab_values: JSON  # {"creatinina": 1.2, "hb": 12.5}
    vitals: JSON  # {"pa": "140/90", "fc": 88}
    updated_at: datetime

# ============================================
# AUDITORÍA DE TOOLS
# ============================================
class ToolExecution:
    id: UUID
    message_id: UUID  # FK -> Message
    tool_name: str
    input_params: JSON
    output_result: JSON
    execution_time_ms: int
    success: bool
    error_message: Optional[str]
    created_at: datetime
```

### Capas de Memoria

| Capa                | Contenido                    | TTL              | Storage    |
| ------------------- | ---------------------------- | ---------------- | ---------- |
| **Session**         | Usuario actual, conv activa  | 24h              | Redis      |
| **Context Window**  | Últimos N mensajes para LLM  | Por request      | RAM        |
| **Conversation**    | Historial completo           | Permanente       | PostgreSQL |
| **Patient Context** | Datos extraídos del paciente | Por conversación | PostgreSQL |
| **Semantic Index**  | Embeddings de conversaciones | Permanente       | Qdrant     |

---

## 4. TOOLS - 3 TIERS

### Resumen Ejecutivo

| Tier                   | Cantidad | Esfuerzo       | Costo  |
| ---------------------- | -------- | -------------- | ------ |
| Tier 1 - KB Existente  | 7        | 1-2 días       | $0     |
| Tier 2 - APIs Públicas | 6        | 2-3 días       | $0     |
| Tier 3 - Calculadoras  | 21       | 1 semana       | $0     |
| **TOTAL**              | **34**   | **~2 semanas** | **$0** |

---

### TIER 1 - Wrappers sobre KB Existente (1-2 días)

| #   | Tool                             | Input                   | Output                   | Archivo Fuente              |
| --- | -------------------------------- | ----------------------- | ------------------------ | --------------------------- |
| 1   | `kb_search`                      | query: str              | chunks relevantes        | 46K líneas KB → Qdrant      |
| 2   | `check_drug_interactions`        | drug_a, drug_b          | severidad, descripción   | `medications_database.py`   |
| 3   | `get_icd10_code`                 | diagnosis: str          | código, descripción      | `icd10_catalog.py`          |
| 4   | `get_differential_diagnosis`     | symptom: str            | lista DDx ordenada       | `differential_diagnosis.py` |
| 5   | `calculate_creatinine_clearance` | creat, age, weight, sex | mL/min (Cockcroft-Gault) | Fórmula                     |
| 6   | `calculate_bmi`                  | weight, height          | kg/m², categoría         | Fórmula                     |
| 7   | `calculate_body_surface_area`    | weight, height          | m² (Du Bois)             | Fórmula                     |

---

### TIER 2 - APIs Médicas Públicas (2-3 días)

| #   | Tool                     | API                | Límites             | Documentación                                        |
| --- | ------------------------ | ------------------ | ------------------- | ---------------------------------------------------- |
| 8   | `pubmed_search`          | NCBI E-utilities   | 10/s con key gratis | [NCBI](https://www.ncbi.nlm.nih.gov/books/NBK25501/) |
| 9   | `rxnorm_lookup`          | NIH RxNorm         | Sin límites         | [RxNav](https://lhncbc.nlm.nih.gov/RxNav/APIs/)      |
| 10  | `get_drug_info_fda`      | openFDA            | 120K/día con key    | [openFDA](https://open.fda.gov/apis/)                |
| 11  | `snomed_lookup`          | SNOMED Browser     | Gratis educativo    | [IHTSDO](https://browser.ihtsdotools.org/)           |
| 12  | `loinc_lookup`           | LOINC FHIR         | Registro gratuito   | [LOINC](https://loinc.org/fhir/)                     |
| 13  | `clinical_trials_search` | ClinicalTrials.gov | Sin límites         | [CT.gov](https://clinicaltrials.gov/api/)            |

---

### TIER 3 - Calculadoras Clínicas (1 semana)

#### Scores de Severidad/Pronóstico

| #   | Tool                   | Variables         | Uso Clínico                        |
| --- | ---------------------- | ----------------- | ---------------------------------- |
| 14  | `calculate_apache_ii`  | 12 vars           | UCI - predicción mortalidad        |
| 15  | `calculate_meld`       | Bili, INR, Cr, Na | Hepatología - prioridad trasplante |
| 16  | `calculate_child_pugh` | 5 vars            | Cirrosis - pronóstico              |
| 17  | `calculate_sofa`       | 6 sistemas        | Sepsis - disfunción orgánica       |

#### Scores Cardiovasculares

| #   | Tool                     | Variables                 | Uso Clínico                       |
| --- | ------------------------ | ------------------------- | --------------------------------- |
| 18  | `calculate_cha2ds2_vasc` | 7 vars                    | FA - riesgo embólico              |
| 19  | `calculate_hasbled`      | 9 vars                    | Anticoagulación - riesgo sangrado |
| 20  | `calculate_framingham`   | Edad, col, PA, tabaco, DM | RCV 10 años                       |
| 21  | `calculate_heart_score`  | 5 vars                    | SCA - estratificación             |

#### Scores Respiratorios/Infecciosos

| #   | Tool                 | Variables | Uso Clínico               |
| --- | -------------------- | --------- | ------------------------- |
| 22  | `calculate_curb65`   | 5 vars    | Neumonía - severidad      |
| 23  | `calculate_psi_port` | 20 vars   | Neumonía - mortalidad     |
| 24  | `calculate_qsofa`    | 3 vars    | Sepsis - screening rápido |

#### Scores Tromboembolismo

| #   | Tool                  | Variables   | Uso Clínico        |
| --- | --------------------- | ----------- | ------------------ |
| 25  | `calculate_wells_dvt` | Checklist   | TVP - probabilidad |
| 26  | `calculate_wells_pe`  | Checklist   | TEP - probabilidad |
| 27  | `calculate_perc`      | 8 criterios | TEP - rule-out     |

#### Correcciones de Laboratorio

| #   | Tool                          | Fórmula            | Uso Clínico         |
| --- | ----------------------------- | ------------------ | ------------------- |
| 28  | `calculate_anion_gap`         | Na - (Cl + HCO3)   | Acidosis metabólica |
| 29  | `calculate_corrected_calcium` | Payne              | Hipoalbuminemia     |
| 30  | `calculate_corrected_sodium`  | Por glucosa        | Hiperglucemia       |
| 31  | `calculate_osmolar_gap`       | Medida - calculada | Intoxicaciones      |

#### Pediatría/Dosificación

| #   | Tool                        | Fórmula           | Uso Clínico           |
| --- | --------------------------- | ----------------- | --------------------- |
| 32  | `pediatric_dose_calculator` | Clark, Young, BSA | Ajuste pediátrico     |
| 33  | `ideal_body_weight`         | Devine            | Dosificación fármacos |
| 34  | `adjusted_body_weight`      | IBW + factor      | Obesidad              |

---

## 5. CAPACIDADES AGÉNTICAS

### Arquitectura de Agentes

```
┌─────────────────────────────────────────────────────────────────┐
│                    ORQUESTADOR PRINCIPAL                         │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  1. Analiza query del usuario                             │  │
│  │  2. Detecta tipo (profesional/educativo) y urgencia       │  │
│  │  3. Selecciona agente(s) especializado(s)                 │  │
│  │  4. Coordina ejecución de tools                           │  │
│  │  5. Agrega resultados en respuesta coherente              │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────┬───────────────────────────────────┘
                              │
         ┌────────────────────┼────────────────────┐
         ▼                    ▼                    ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  AGENTE TRIAGE  │  │   AGENTE DDx    │  │  AGENTE Rx      │
│                 │  │                 │  │  SEGURA         │
│  - Urgencia     │  │  - Síntomas     │  │                 │
│  - Derivación   │  │  - DDx          │  │  - Dosis        │
│  - Tiempo máx   │  │  - Estudios     │  │  - Interacc.    │
│  - Red flags    │  │  - Plan dx      │  │  - Alergias     │
└────────┬────────┘  └────────┬────────┘  └────────┬────────┘
         │                    │                    │
         └────────────────────┼────────────────────┘
                              ▼
         ┌────────────────────────────────────────────────┐
         │              CAPA DE TOOLS                      │
         │  kb_search | icd10 | interactions | calculators │
         └────────────────────────────────────────────────┘
```

### Flujos Agénticos Implementables

| Agente        | Flujo                                                              | Ejemplo                                                  |
| ------------- | ------------------------------------------------------------------ | -------------------------------------------------------- |
| **Triage**    | Síntomas → Urgencia → Derivación → Tiempo máximo                   | "Dolor torácico + disnea" → ⚠️ Emergencia, derivar ahora |
| **DDx**       | Síntomas → KB search → DDx ordenado → Plan diagnóstico             | "Cefalea + fotofobia" → Migraña vs Meningitis vs...      |
| **Rx Segura** | Fármaco → Dosis → Interacciones → Alergias → Función renal → ✅/❌ | "Prescribir gentamicina" → Verificar TFG, ajustar dosis  |
| **Labs**      | Resultados → Valores críticos → Correlación → Estudios adicionales | "K+ 6.2" → ⚠️ Crítico, ECG urgente                       |
| **Educativo** | Query → Nivel usuario → Complejidad adaptada                       | Explicación técnica vs. layperson                        |

### Capacidades Transversales

| Capacidad                   | Descripción                                 | Implementación            |
| --------------------------- | ------------------------------------------- | ------------------------- |
| **Razonamiento multi-paso** | Flujo Síntomas → DDx → Estudios → Dx → Tx   | Prompting estructurado    |
| **Checklist automático**    | Verificar datos críticos antes de responder | Guardrails en orquestador |
| **Self-correction**         | Revisar respuesta buscando inconsistencias  | Loop de validación        |
| **Extracción de contexto**  | Poblar PatientContext automáticamente       | NER médico en mensajes    |
| **Guardrails médicos**      | Detectar/bloquear respuestas peligrosas     | Reglas + validación       |

---

## 6. STACK TÉCNICO

### Componentes (Todo Gratuito)

| Componente        | Tecnología                     | Propósito                            | Docker |
| ----------------- | ------------------------------ | ------------------------------------ | ------ |
| **API**           | FastAPI                        | Backend principal                    | Sí     |
| **UI**            | Streamlit → React (futuro)     | Frontend                             | Sí     |
| **DB Principal**  | PostgreSQL 16                  | Usuarios, conversaciones, mensajes   | Sí     |
| **Cache/Session** | Redis 7                        | Sesiones, contexto activo, cache LLM | Sí     |
| **Vector DB**     | Qdrant                         | Embeddings KB y conversaciones       | Sí     |
| **Embeddings**    | sentence-transformers          | Vectorización (HuggingFace gratis)   | -      |
| **LLMs**          | Kimi K2, Qwen 72B, DeepSeek V3 | Generación de respuestas             | -      |

### docker-compose.yml (Infraestructura)

```yaml
version: "3.8"

services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: medex
      POSTGRES_USER: medex
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"

  qdrant:
    image: qdrant/qdrant:latest
    volumes:
      - qdrant_data:/qdrant/storage
    ports:
      - "6333:6333"
      - "6334:6334"

  api:
    build: .
    depends_on:
      - postgres
      - redis
      - qdrant
    environment:
      DATABASE_URL: postgresql://medex:${POSTGRES_PASSWORD}@postgres:5432/medex
      REDIS_URL: redis://redis:6379
      QDRANT_URL: http://qdrant:6333
    ports:
      - "8000:8000"

  ui:
    build:
      context: .
      dockerfile: Dockerfile.ui
    depends_on:
      - api
    ports:
      - "8501:8501"

volumes:
  postgres_data:
  redis_data:
  qdrant_data:
```

### Estructura de Archivos Propuesta

```
MedeX/
├── src/
│   ├── medex/
│   │   ├── api/                    # FastAPI endpoints
│   │   │   ├── routes/
│   │   │   │   ├── chat.py         # /chat endpoints
│   │   │   │   ├── conversations.py # CRUD conversaciones
│   │   │   │   └── users.py        # Autenticación
│   │   │   └── main.py
│   │   │
│   │   ├── agents/                 # Sistema agéntico
│   │   │   ├── orchestrator.py     # Orquestador principal
│   │   │   ├── triage_agent.py     # Agente de triage
│   │   │   ├── ddx_agent.py        # Agente diagnóstico
│   │   │   ├── rx_agent.py         # Agente prescripción segura
│   │   │   └── base.py             # Clase base de agentes
│   │   │
│   │   ├── tools/                  # Herramientas
│   │   │   ├── __init__.py         # Registry de tools
│   │   │   ├── base.py             # Tool base class
│   │   │   ├── kb_search.py        # RAG sobre KB
│   │   │   ├── drug_interactions.py
│   │   │   ├── icd10.py
│   │   │   ├── ddx.py
│   │   │   ├── calculators/        # Calculadoras clínicas
│   │   │   │   ├── renal.py        # GFR, Creatinina
│   │   │   │   ├── cardiac.py      # CHA2DS2, Framingham
│   │   │   │   ├── respiratory.py  # CURB-65, PSI
│   │   │   │   └── labs.py         # Correcciones
│   │   │   └── external/           # APIs externas
│   │   │       ├── pubmed.py
│   │   │       ├── rxnorm.py
│   │   │       └── openfda.py
│   │   │
│   │   ├── memory/                 # Sistema de memoria
│   │   │   ├── conversation.py     # CRUD conversaciones
│   │   │   ├── context.py          # Manejo de contexto
│   │   │   ├── patient.py          # Extracción PatientContext
│   │   │   └── session.py          # Redis session
│   │   │
│   │   ├── providers/              # LLM providers (existente)
│   │   │   ├── base.py
│   │   │   ├── moonshot.py
│   │   │   ├── huggingface.py
│   │   │   └── manager.py
│   │   │
│   │   ├── knowledge/              # KB existente
│   │   │   ├── medications_database.py
│   │   │   ├── icd10_catalog.py
│   │   │   └── ...
│   │   │
│   │   └── core/                   # Utilities
│   │       ├── config.py
│   │       ├── database.py         # SQLAlchemy
│   │       └── logger.py
│   │
│   └── ui/                         # Streamlit UI
│       ├── app.py                  # Entry point
│       ├── components/
│       │   ├── sidebar.py          # Lista conversaciones
│       │   ├── chat.py             # Área de chat
│       │   └── context_panel.py    # Panel paciente
│       └── styles/
│
├── docker/
├── tests/
├── docs/
└── ...
```

---

## 7. PLAN DE IMPLEMENTACIÓN

### Fase 0: Infraestructura (1 día)

- [ ] Docker compose con PostgreSQL + Redis + Qdrant
- [ ] Modelos SQLAlchemy (User, Conversation, Message, PatientContext)
- [ ] Migraciones con Alembic
- [ ] Tests de conexión

### Fase 1: Sistema de Memoria (2-3 días)

- [ ] CRUD Conversaciones
- [ ] Persistencia de mensajes
- [ ] Session management con Redis
- [ ] Context window para LLM

### Fase 2: UI Conversacional (2-3 días)

- [ ] Sidebar con lista de conversaciones
- [ ] Crear/continuar/archivar conversaciones
- [ ] Panel de contexto de paciente (colapsable)
- [ ] Auto-título de conversaciones
- [ ] Indicadores de tools (discretos)

### Fase 3: Tools Tier 1 (2-3 días)

- [ ] Base class para tools
- [ ] `get_icd10_code`
- [ ] `check_drug_interactions`
- [ ] `get_differential_diagnosis`
- [ ] Calculadoras básicas (BMI, GFR, BSA)

### Fase 4: RAG Real (3-4 días)

- [ ] Indexar KB en Qdrant
- [ ] Implementar `kb_search`
- [ ] Integrar en flujo de respuesta
- [ ] Tests de relevancia

### Fase 5: Orquestador Agéntico (3-4 días)

- [ ] Orquestador principal
- [ ] Detección de tipo usuario/urgencia
- [ ] Selección automática de tools
- [ ] Agregación de resultados

### Fase 6: APIs Externas (2-3 días)

- [ ] `pubmed_search`
- [ ] `rxnorm_lookup`
- [ ] `get_drug_info_fda`
- [ ] Rate limiting y caching

### Fase 7: Calculadoras Avanzadas (3-4 días)

- [ ] Scores de severidad (APACHE, MELD, SOFA)
- [ ] Scores cardiovasculares
- [ ] Scores respiratorios
- [ ] Correcciones de laboratorio

### Fase 8: Agentes Especializados (1 semana)

- [ ] Agente Triage
- [ ] Agente DDx
- [ ] Agente Rx Segura
- [ ] Guardrails médicos

### Fase 9: Polish y Testing (1 semana)

- [ ] Tests E2E completos
- [ ] Optimización de prompts
- [ ] Performance tuning
- [ ] Documentación

---

## TIMELINE ESTIMADO

| Fase                    | Duración | Acumulado |
| ----------------------- | -------- | --------- |
| Fase 0: Infraestructura | 1 día    | 1 día     |
| Fase 1: Memoria         | 3 días   | 4 días    |
| Fase 2: UI              | 3 días   | 7 días    |
| Fase 3: Tools Tier 1    | 3 días   | 10 días   |
| Fase 4: RAG             | 4 días   | 14 días   |
| Fase 5: Orquestador     | 4 días   | 18 días   |
| Fase 6: APIs            | 3 días   | 21 días   |
| Fase 7: Calculadoras    | 4 días   | 25 días   |
| Fase 8: Agentes         | 5 días   | 30 días   |
| Fase 9: Polish          | 5 días   | 35 días   |

**Total estimado: ~5-6 semanas** para MedeX V2 completo.

---

## MÉTRICAS DE ÉXITO

| Métrica                     | Target                     |
| --------------------------- | -------------------------- |
| Conversaciones persistentes | 100% guardadas             |
| Contexto mantenido          | 100% en misma conversación |
| Tools funcionando           | 34/34                      |
| Latencia promedio           | < 3s primera respuesta     |
| Precisión DDx               | > 85% top-3 correcto       |
| Interacciones detectadas    | > 95% de KB                |

---

_Documento maestro de arquitectura MedeX V2 - Generado 2026-01-06_
