# Development Environment Setup

Complete guide to set up MedeX for local development.

## Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| Python | ≥ 3.10 | Runtime |
| pip | Latest | Package management |
| Git | ≥ 2.30 | Version control |
| Docker | ≥ 24.0 | Container runtime (optional) |
| Docker Compose | ≥ 2.20 | Service orchestration (optional) |

## Quick Start (Minimal)

```bash
# 1. Clone the repository
git clone https://github.com/DeepRatAI/MedX.git
cd MedX

# 2. Create virtual environment
python3.10 -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# 3. Install dependencies
pip install --upgrade pip
pip install -e ".[dev]"
# Or from requirements.txt:
pip install -r requirements.txt
pip install pytest pytest-asyncio pytest-cov pytest-mock black ruff mypy pre-commit

# 4. Install pre-commit hooks
pre-commit install

# 5. Verify installation
python -c "import medex; print('MedeX imported successfully')"
pytest tests/test_detection.py -v  # Quick sanity check
```

## Environment Variables

Create a `.env` file in the project root:

```env
# Required for LLM features
KIMI_API_KEY=your_kimi_api_key_here

# Optional: HuggingFace (for embedding models)
HF_TOKEN=your_huggingface_token_here

# Optional: Database (defaults to SQLite if not set)
DATABASE_URL=postgresql+asyncpg://medex:medex@localhost:5432/medex
REDIS_URL=redis://localhost:6379/0
QDRANT_URL=http://localhost:6333

# Optional: Environment
MEDEX_ENV=development
MEDEX_LOG_LEVEL=DEBUG
MEDEX_UI_PORT=3000
```

> **Note**: The application runs without any API keys for local medical tools
> (drug interactions, dosage calculator, lab interpreter, triage). LLM features
> require at least `KIMI_API_KEY`.

## Full Stack (Docker Compose)

For the complete development stack with all services:

```bash
# Build and start all services
docker compose up --build -d

# Services will be available at:
# - API:    http://localhost:8000
# - UI:     http://localhost:3000
# - Docs:   http://localhost:8000/docs (OpenAPI/Swagger)

# View logs
docker compose logs -f api
docker compose logs -f ui

# Stop all services
docker compose down
```

### Individual Services

```bash
# API only (FastAPI + Uvicorn)
docker compose up api -d

# UI only (Reflex)
docker compose up ui -d

# Infrastructure only (Postgres + Redis + Qdrant)
docker compose up postgres redis qdrant -d
```

## Running Without Docker

### API Server

```bash
# Development mode with auto-reload
uvicorn medex.api.app:create_app --factory --reload --host 0.0.0.0 --port 8000

# Or use the standalone server
python run_api.py
```

### UI (Reflex)

```bash
cd ui
reflex init  # First time only
reflex run --env dev
# UI available at http://localhost:3000
```

## Development Workflow

### 1. Code Quality

```bash
# Format code
black src/ tests/

# Lint
ruff check src/ tests/
ruff check --fix src/ tests/  # Auto-fix safe issues

# Type checking
mypy src/medex --ignore-missing-imports

# All checks at once (via pre-commit)
pre-commit run --all-files
```

### 2. Testing

```bash
# Run stable tests
pytest tests/test_api_v2.py tests/test_detection.py tests/test_differential_diagnosis.py -v

# Run with coverage
pytest tests/ -v --cov=src/medex --cov-report=html
open htmlcov/index.html

# Run specific test
pytest tests/test_detection.py::TestEmergencyDetection::test_chest_pain_detected -v

# Skip slow/integration tests
pytest tests/ -v -m "not slow and not integration"
```

### 3. Branch Naming

```
fix/short-description     # Bug fixes
feat/short-description    # New features
docs/short-description    # Documentation
ci/short-description      # CI/CD changes
refactor/short-description # Code restructuring
test/short-description    # Test additions/fixes
```

### 4. Commit Messages (Conventional Commits)

```
fix: correct dosage calculation for pediatric patients
feat: add ICD-10 code lookup API endpoint
docs: update development setup guide
ci: enforce ruff check in CI pipeline
test: add unit tests for triage engine
refactor: extract medical ontology into separate module
```

## Project Structure

```
MedX/
├── src/medex/              # Main package
│   ├── agent/              # Agentic controller, planner, intent analysis
│   ├── api/                # FastAPI app, routes, middleware, models
│   ├── core/               # Config, constants, base classes
│   ├── db/                 # SQLAlchemy models, repositories, migrations
│   ├── detection/          # Emergency detection engine
│   ├── knowledge/          # Medical knowledge base (1000+ conditions)
│   ├── llm/                # LLM router, parser, streaming
│   ├── medical/            # Clinical models, triage, reasoner, formatter
│   ├── memory/             # Conversation memory, context windows
│   ├── observability/      # Logging, tracing, metrics
│   ├── providers/          # LLM provider adapters (Kimi, HuggingFace)
│   ├── rag/                # RAG pipeline (chunker, embedder, reranker)
│   ├── security/           # Audit logging, input validation
│   ├── tools/              # Medical tools (drugs, dosage, labs, triage)
│   └── vision/             # Medical image analysis
├── ui/medex_ui/            # Reflex UI application
│   ├── app.py              # UI components (3800+ lines)
│   └── state.py            # Reactive state management (2900+ lines)
├── tests/                  # Test suite (18 test files + 2 E2E)
├── docs/                   # Documentation
│   ├── adr/                # Architecture Decision Records
│   ├── ARCHITECTURE.md     # System architecture overview
│   └── *.md                # Various technical docs
├── .github/workflows/      # CI/CD
├── pyproject.toml          # Project config (black, ruff, mypy, pytest)
├── requirements.txt        # Python dependencies
├── Dockerfile              # Multi-stage Docker build
└── docker-compose.yml      # Service orchestration
```

## API Reference

The API is auto-documented via OpenAPI/Swagger:

```bash
# Start the API server
python run_api.py
# or
uvicorn medex.api.app:create_app --factory --port 8000

# Access documentation
open http://localhost:8000/docs     # Swagger UI
open http://localhost:8000/redoc    # ReDoc
```

### Key Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/query` | Main query endpoint (LLM-powered) |
| `POST` | `/api/v1/tools/drug-interactions` | Check drug interactions |
| `POST` | `/api/v1/tools/dosage-calculator` | Calculate dosage |
| `POST` | `/api/v1/tools/lab-interpreter` | Interpret lab values |
| `POST` | `/api/v1/triage/assess` | Emergency triage assessment |
| `GET`  | `/api/v1/tools/` | List available tools |
| `GET`  | `/health` | Health check |
| `WS`   | `/ws` | WebSocket for streaming |

## Troubleshooting

### Common Issues

**Import errors after install:**
```bash
pip install -e . --no-deps
# If still failing, install deps explicitly:
pip install -r requirements.txt
```

**Port already in use:**
```bash
# Find and kill the process
lsof -i :8000  # API
lsof -i :3000  # UI
kill -9 <PID>
```

**Database connection errors:**
```bash
# Check if Postgres is running
docker compose ps postgres
# Or use SQLite (no setup needed):
unset DATABASE_URL
```

**Pre-commit hook failures:**
```bash
# Auto-fix formatting
black src/ tests/ && ruff check --fix src/ tests/
git add -u && git commit
```
