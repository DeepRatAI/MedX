# =============================================================================
# MedeX - Medical AI Intelligence System
# Multi-stage Production Dockerfile
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1: Builder - Install dependencies and prepare the application
# -----------------------------------------------------------------------------
FROM python:3.12-slim AS builder

# Prevent Python from writing pyc files and buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy and install requirements
WORKDIR /build
COPY requirements.txt .
COPY requirements-api.txt .

# Install dependencies in the virtual environment
RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    pip install -r requirements-api.txt

# -----------------------------------------------------------------------------
# Stage 2: Production - Minimal runtime image
# -----------------------------------------------------------------------------
FROM python:3.12-slim AS production

# Labels for container identification
LABEL org.opencontainers.image.title="MedeX" \
    org.opencontainers.image.description="Medical AI Intelligence System" \
    org.opencontainers.image.version="1.0.0" \
    org.opencontainers.image.vendor="MedeX Team" \
    org.opencontainers.image.licenses="MIT"

# Environment configuration
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    MEDEX_ENV=production \
    MEDEX_LOG_LEVEL=INFO \
    MEDEX_API_PORT=8000 \
    MEDEX_UI_PORT=3000

# Install runtime dependencies only
# Note: libgl1-mesa-glx was renamed to libgl1 in Debian Trixie (python:3.12-slim)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    curl \
    tini \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user for security
RUN groupadd --gid 1000 medex && \
    useradd --uid 1000 --gid medex --shell /bin/bash --create-home medex

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy application code
COPY --chown=medex:medex . .

# Create necessary directories with proper permissions
RUN mkdir -p /app/data /app/logs /app/cache /app/rag_cache && \
    chown -R medex:medex /app

# Switch to non-root user
USER medex

# Expose ports
EXPOSE 8000 3000

# Health check for API
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Use tini as init system to handle signals properly
ENTRYPOINT ["/usr/bin/tini", "--"]

# Default command: start API server
CMD ["python", "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]

# -----------------------------------------------------------------------------
# Stage 3: Development - Full development environment
# -----------------------------------------------------------------------------
FROM production AS development

# Switch to root to install dev dependencies
USER root

# Install development tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    vim \
    htop \
    && rm -rf /var/lib/apt/lists/*

# Install development Python packages
COPY requirements-dev.txt /tmp/
RUN pip install -r /tmp/requirements-dev.txt

# Set development environment
ENV MEDEX_ENV=development \
    MEDEX_LOG_LEVEL=DEBUG

# Switch back to medex user
USER medex

# Override healthcheck for development (more frequent)
HEALTHCHECK --interval=15s --timeout=5s --start-period=20s --retries=2 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command for development: auto-reload
CMD ["python", "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# -----------------------------------------------------------------------------
# Stage 4: UI - Reflex web interface
# -----------------------------------------------------------------------------
FROM production AS ui

# Healthcheck for Reflex frontend
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:3000 || exit 1

# Expose Reflex default port
EXPOSE 3000

# Environment for Reflex
ENV REFLEX_ENV_MODE=prod

# Start Reflex (production mode)
CMD ["reflex", "run", "--env", "prod", "--backend-only", "false"]

# -----------------------------------------------------------------------------
# Stage 5: HuggingFace - For Hugging Face Spaces deployment
# -----------------------------------------------------------------------------
FROM python:3.12-slim AS huggingface

# Set up user for HF Spaces
RUN useradd -m -u 1000 user

USER user

ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    PYTHONUNBUFFERED=1

WORKDIR $HOME/app

# Copy requirements first for better caching
COPY --chown=user requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY --chown=user . .

# Create necessary directories
RUN mkdir -p $HOME/app/rag_cache && \
    mkdir -p $HOME/app/logs && \
    mkdir -p $HOME/app/cache

# Expose HF default port
EXPOSE 7860

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:7860/_stcore/health || exit 1

# Environment for Reflex on HuggingFace Spaces
ENV REFLEX_ENV_MODE=prod \
    PORT=7860

# Run the Reflex app on HF Spaces port
CMD ["reflex", "run", "--env", "prod", "--backend-port", "7860"]
