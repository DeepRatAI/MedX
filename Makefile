# =============================================================================
# MedX — Medical AI Intelligence System
# Development Makefile
# =============================================================================

.PHONY: help install dev test lint format clean \
        infra-up infra-down infra-logs infra-health infra-clean \
        db-migrate db-revision db-downgrade db-history db-current db-reset \
        run-api run-ui run \
        test-infra test-cov test-fast \
        check docker-build docker-up docker-down docker-logs docker-clean \
        index-kb docs check-python setup-db

# Default target
help:
	@echo "MedX Development Commands"
	@echo "========================="
	@echo ""
	@echo "Setup:"
	@echo "  make install        Install production dependencies"
	@echo "  make dev            Install development dependencies"
	@echo "  make setup-db       Start infra + run migrations"
	@echo ""
	@echo "Infrastructure:"
	@echo "  make infra-up       Start PostgreSQL, Redis, Qdrant containers"
	@echo "  make infra-down     Stop infrastructure containers"
	@echo "  make infra-logs     View infrastructure logs"
	@echo "  make infra-health   Check infrastructure health"
	@echo "  make infra-clean    Stop infra and remove volumes (DESTRUCTIVE)"
	@echo ""
	@echo "Database:"
	@echo "  make db-migrate     Run Alembic migrations"
	@echo "  make db-revision    Create new migration"
	@echo "  make db-downgrade   Rollback last migration"
	@echo "  make db-history     Show migration history"
	@echo "  make db-current     Show current migration"
	@echo "  make db-reset       Reset database (DESTRUCTIVE)"
	@echo ""
	@echo "Development:"
	@echo "  make run-api        Start FastAPI server (uvicorn, port 8000)"
	@echo "  make run-ui         Start Reflex UI"
	@echo "  make run            Start full stack (infra + API + UI)"
	@echo ""
	@echo "Testing:"
	@echo "  make test           Run all tests"
	@echo "  make test-infra     Run infrastructure tests"
	@echo "  make test-cov       Run tests with coverage"
	@echo "  make test-fast      Run tests, stop on first failure"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint           Run linters (ruff, mypy)"
	@echo "  make format         Format code (black, isort)"
	@echo "  make check          Format + lint + test"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build   Build Docker images"
	@echo "  make docker-up      Start all services via Docker Compose"
	@echo "  make docker-down    Stop all services"
	@echo "  make docker-logs    Follow Docker Compose logs"
	@echo "  make docker-clean   Stop, remove volumes and images"
	@echo ""
	@echo "Utilities:"
	@echo "  make index-kb       Index knowledge base into Qdrant"
	@echo "  make clean          Remove cache and build artifacts"
	@echo "  make check-python   Verify Python version"
	@echo ""

# =============================================================================
# Setup & Installation
# =============================================================================

install:
	pip install -r requirements.txt

dev:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt
	pip install -e .

setup-db: infra-up db-migrate
	@echo "Database setup complete"

# =============================================================================
# Infrastructure Management
# =============================================================================

infra-up:
	docker compose up -d postgres redis qdrant
	@echo "Waiting for services to be healthy..."
	@sleep 5
	@make infra-health

infra-down:
	docker compose down

infra-logs:
	docker compose logs -f postgres redis qdrant

infra-health:
	@echo "=== PostgreSQL ==="
	@docker compose exec postgres pg_isready -U medex -d medex || echo "PostgreSQL not ready"
	@echo ""
	@echo "=== Redis ==="
	@docker compose exec redis redis-cli ping || echo "Redis not ready"
	@echo ""
	@echo "=== Qdrant ==="
	@curl -s http://localhost:6333/readyz || echo "Qdrant not ready"
	@echo ""

infra-clean:
	docker compose down -v
	@echo "Infrastructure volumes removed"

# =============================================================================
# Database Management (Alembic)
# =============================================================================

db-migrate:
	alembic upgrade head
	@echo "Migrations applied successfully"

db-revision:
	@read -p "Migration message: " msg; \
	alembic revision --autogenerate -m "$$msg"

db-downgrade:
	alembic downgrade -1
	@echo "Rolled back one migration"

db-history:
	alembic history --verbose

db-current:
	alembic current

db-reset:
	@echo "WARNING: This will delete all data!"
	@read -p "Are you sure? [y/N] " confirm; \
	if [ "$$confirm" = "y" ]; then \
		alembic downgrade base; \
		alembic upgrade head; \
		echo "Database reset complete"; \
	fi

# =============================================================================
# Development Servers
# =============================================================================

run-api:
	uvicorn run_api:app --reload --host 0.0.0.0 --port 8000

run-ui:
	cd ui && python run.py

run: infra-up
	@echo "Starting API and UI..."
	@make run-api &
	@sleep 2
	@make run-ui

# =============================================================================
# Testing
# =============================================================================

test:
	pytest tests/ -v --asyncio-mode=auto

test-infra:
	pytest tests/test_infrastructure.py -v --asyncio-mode=auto

test-cov:
	pytest tests/ -v --asyncio-mode=auto --cov=src/medex --cov-report=html --cov-report=term-missing
	@echo "Coverage report: htmlcov/index.html"

test-fast:
	pytest tests/ -v --asyncio-mode=auto -x -q

# =============================================================================
# Code Quality
# =============================================================================

lint:
	ruff check src/ tests/
	mypy src/ --ignore-missing-imports

format:
	black src/ tests/
	isort src/ tests/
	ruff check --fix src/ tests/

check: format lint test
	@echo "All checks passed!"

# =============================================================================
# Docker
# =============================================================================

docker-build:
	docker compose build

docker-up:
	docker compose up -d

docker-down:
	docker compose down

docker-logs:
	docker compose logs -f

docker-clean:
	docker compose down -v --rmi local
	docker system prune -f

# =============================================================================
# Utilities
# =============================================================================

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf build/ dist/
	@echo "Cleaned up cache and build artifacts"

index-kb:
	python scripts/index_knowledge_base.py

docs:
	python -m pdoc --html --output-dir docs/api src/medex

check-python:
	@python --version
	@echo "Required: Python 3.10+"
