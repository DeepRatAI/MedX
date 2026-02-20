# MedX Architecture

> System design and component reference for MedX — Medical AI Intelligence System.

---

## System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                          CLIENT LAYER                               │
│                                                                     │
│   ┌──────────────┐     ┌──────────────┐     ┌──────────────┐       │
│   │   Reflex UI  │     │  REST Client │     │   PDF Export  │       │
│   │  (ui/)       │     │  (any HTTP)  │     │              │       │
│   └──────┬───────┘     └──────┬───────┘     └──────────────┘       │
│          │                    │                                      │
└──────────┼────────────────────┼──────────────────────────────────────┘
           │                    │
           ▼                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          API LAYER                                   │
│                                                                     │
│   ┌─────────────────────────────────────────────────────────┐       │
│   │                 FastAPI Application                      │       │
│   │           (src/medex/api/ · run_api.py)                 │       │
│   │                                                         │       │
│   │   /chat/stream   /analyze/image   /tools/*   /health   │       │
│   └──────────────────────┬──────────────────────────────────┘       │
│                          │                                          │
└──────────────────────────┼──────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       AGENT LAYER                                    │
│                                                                     │
│   ┌─────────────┐   ┌─────────────┐   ┌─────────────────┐         │
│   │  Controller  │──▶│   Planner   │──▶│  State Manager  │         │
│   │  (agent/)    │   │  (agent/)   │   │   (agent/)      │         │
│   └──────┬───────┘   └─────────────┘   └─────────────────┘         │
│          │                                                          │
└──────────┼──────────────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    INTELLIGENCE LAYER                                │
│                                                                     │
│   ┌────────────┐  ┌────────────┐  ┌───────────┐  ┌────────────┐   │
│   │ Detection  │  │    RAG     │  │   Tools   │  │   Vision   │   │
│   │            │  │            │  │           │  │            │   │
│   │ • Emergency│  │ • Embedder │  │ • PubMed  │  │ • Image    │   │
│   │ • UserType │  │ • Qdrant   │  │ • Scholar │  │   Analysis │   │
│   │ • Triage   │  │ • Retriever│  │ • DiffDx  │  │ • Modality │   │
│   └────────────┘  └────────────┘  │ • Pharma  │  │   Detect   │   │
│                                   └───────────┘  └────────────┘   │
│                                                                     │
│   ┌────────────┐  ┌────────────┐  ┌───────────────────────────┐   │
│   │  Medical   │  │ Knowledge  │  │      LLM Router           │   │
│   │            │  │            │  │                           │   │
│   │ • Ontology │  │ • 1061     │  │  HuggingFace Inference   │   │
│   │ • ICD-10   │  │   Conds.  │  │  Providers (8 models)    │   │
│   │ • Protocols│  │ • 543+    │  │                           │   │
│   │            │  │   Meds.   │  │  Model selection per task │   │
│   └────────────┘  └────────────┘  └───────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   INFRASTRUCTURE LAYER                               │
│                                                                     │
│   ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐  │
│   │ PostgreSQL │  │   Redis    │  │   Qdrant   │  │   Logging  │  │
│   │            │  │            │  │            │  │            │  │
│   │ Sessions   │  │ Cache      │  │ Vectors    │  │ PII-safe   │  │
│   │ Audit log  │  │ Rate limit │  │ Embeddings │  │ Audit trail│  │
│   │ Users      │  │ Sessions   │  │ RAG index  │  │ Telemetry  │  │
│   └────────────┘  └────────────┘  └────────────┘  └────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Component Map

All application code lives under `src/medex/`. Each sub-package is self-contained with clear responsibilities:

### Core Modules

| Package | Purpose | Key Files |
|---|---|---|
| `agent/` | Orchestration layer — plans, executes, and manages conversational state | `controller.py`, `planner.py`, `state.py`, `service.py` |
| `api/` | FastAPI endpoints for chat, image analysis, tools, and health checks | Routes, middleware, request/response schemas |
| `config.py` | Centralized configuration via environment variables and `.env` | Settings, defaults, validation |
| `main.py` | Application entry point and dependency wiring | Startup, shutdown hooks |

### Detection & Safety

| Package | Purpose |
|---|---|
| `detection/` | Emergency pattern recognition (50+ patterns), user-type classification (professional vs. patient), triage level assignment |
| `security/` | PII anonymization, HIPAA-aware log redaction, input sanitization |

### Knowledge & Reasoning

| Package | Purpose |
|---|---|
| `knowledge/` | Medical condition database (1,061 entries with ICD-10 codes), pharmaceutical database (543+ medications with interactions) |
| `medical/` | Medical ontology, clinical protocols, structured diagnostic reasoning |
| `rag/` | RAG pipeline — embedding generation, Qdrant indexing, similarity retrieval, context assembly |
| `tools/` | External tool integrations — PubMed search, Semantic Scholar, differential diagnosis engine, drug lookup |

### LLM & Vision

| Package | Purpose |
|---|---|
| `llm/` | LLM abstraction layer — prompt formatting, streaming, token management |
| `providers/` | Multi-model routing across 8 HuggingFace Inference Provider models — task-based model selection (reasoning, speed, vision) |
| `vision/` | Medical image analysis — modality detection (RX/CT/MRI/US), image preprocessing, vision-model prompting |

### Persistence & Observability

| Package | Purpose |
|---|---|
| `db/` | Database models and migrations (SQLAlchemy + Alembic) for PostgreSQL |
| `memory/` | Conversation memory — session history, context window management, Redis-backed short-term memory |
| `observability/` | Structured logging, metrics, tracing, and audit trails |

### Frontend

| Package | Purpose |
|---|---|
| `ui/` | Reflex-based web interface — chat panel, medical tool widgets, PDF export, session management |

---

## Data Flow

### Query Processing Pipeline

```
1. User Input
   │
   ▼
2. Emergency Detection ──────────────┐
   │ (pattern matching, 50+ rules)   │ If emergency → immediate
   │                                  │ triage response
   ▼                                  │
3. User-Type Classification          │
   │ (professional vs. patient)       │
   │                                  │
   ▼                                  │
4. Agent Planner                     │
   │ ├─ Determine required tools      │
   │ ├─ Select LLM model             │
   │ └─ Build execution plan          │
   │                                  │
   ▼                                  │
5. Tool Execution (parallel)         │
   │ ├─ RAG retrieval (Qdrant)        │
   │ ├─ Drug interaction check        │
   │ ├─ PubMed / Scholar search       │
   │ └─ Differential diagnosis        │
   │                                  │
   ▼                                  │
6. Context Assembly                  │
   │ ├─ Merge tool results            │
   │ ├─ Attach conversation history   │
   │ └─ Format system prompt          │
   │                                  │
   ▼                                  │
7. LLM Generation (streaming)  ◀─────┘
   │ ├─ Model selected by router
   │ └─ Streamed token-by-token
   │
   ▼
8. Response Post-Processing
   │ ├─ PII redaction (logging)
   │ ├─ Audit trail entry
   │ └─ Session persistence
   │
   ▼
9. Client receives streamed response
```

### Knowledge Pipeline

```
knowledge/ YAML/Python files
       │
       ▼
  Embedding Model (SentenceTransformers)
       │
       ▼
  Qdrant Vector Store (indexed collections)
       │
       ▼
  RAG Retriever (similarity search at query time)
       │
       ▼
  Context injected into LLM prompt
```

The knowledge base is indexed via `scripts/index_knowledge_base.py` (or `make index-kb`). At query time, the RAG module retrieves the top-k most relevant knowledge chunks and injects them as context into the LLM system prompt.

---

## Multi-Model Routing

MedX routes queries to the optimal model based on task requirements:

| Task Type | Routing Criteria | Example Models |
|---|---|---|
| **Clinical reasoning** | Complex medical queries requiring deep reasoning | Large reasoning models |
| **Quick response** | Simple factual lookups, greetings, follow-ups | Fast inference models |
| **Vision analysis** | Medical image interpretation | Vision-capable models |
| **Literature search** | Scientific citation and evidence synthesis | Models with long context |

The routing logic lives in `src/medex/providers/` and selects from 8 models available via HuggingFace Inference Providers. Model selection is transparent — the chosen model and reasoning are logged for auditability.

---

## Infrastructure

### Docker Compose Services

| Service | Port | Purpose |
|---|---|---|
| `medx-api` | 8000 | FastAPI application server |
| `medx-ui` | 3000 | Reflex frontend |
| `postgres` | 5432 | Session storage, audit logs, user data |
| `redis` | 6379 | Response caching, rate limiting, session store |
| `qdrant` | 6333 | Vector similarity search for RAG |

### Database Schema (PostgreSQL)

Managed by Alembic migrations (`alembic/`). Key tables:

- **sessions** — Conversation sessions with metadata
- **messages** — Individual messages linked to sessions
- **audit_log** — Immutable audit trail for compliance

### Caching Strategy (Redis)

- **LLM response cache** — Deduplicates identical queries
- **Session state** — Fast session lookup for active users
- **Rate limiting** — Per-user and per-endpoint throttling

---

## Directory Structure

```
MedX/
├── src/medex/           # Main application package
│   ├── agent/           # Orchestration (controller, planner, state)
│   ├── api/             # FastAPI routes and middleware
│   ├── db/              # SQLAlchemy models, Alembic migrations
│   ├── detection/       # Emergency detection, user-type classification
│   ├── knowledge/       # Medical conditions & pharmaceutical data
│   ├── llm/             # LLM abstraction and prompt management
│   ├── medical/         # Ontology, protocols, clinical reasoning
│   ├── memory/          # Conversation memory (Redis-backed)
│   ├── observability/   # Logging, metrics, tracing
│   ├── providers/       # Multi-model HF Inference routing
│   ├── rag/             # RAG pipeline (embed, index, retrieve)
│   ├── security/        # PII anonymization, input sanitization
│   ├── tools/           # PubMed, Scholar, DiffDx, drug lookup
│   ├── ui/              # Reflex UI components
│   └── vision/          # Medical image analysis
├── knowledge/           # Raw knowledge base files
├── ui/                  # Reflex app entry point
├── tests/               # Test suite
├── alembic/             # Database migrations
├── scripts/             # Utility scripts (indexing, data prep)
├── docs/                # Documentation
├── docker-compose.yml   # Full stack orchestration
├── Dockerfile           # Container image
├── run_api.py           # API entry point
├── Makefile             # Development commands
└── pyproject.toml       # Project metadata and tool config
```
