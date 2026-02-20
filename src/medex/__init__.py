# =============================================================================
# MedeX - Medical AI Intelligence System V2.0
# =============================================================================
"""
MedeX - Asistente Médico Educativo con IA

A comprehensive medical education assistant powered by AI.

Features:
- Multi-provider LLM support (Groq, Together, Cerebras, Ollama, etc.)
- RAG-powered medical knowledge retrieval
- 12+ specialized medical tools
- ESI 5-level triage system
- Diagnostic reasoning with 14+ patterns
- PII detection and security compliance
- Full observability (metrics, logging, tracing)
- REST API and WebSocket streaming

Example:
    from medex import MedeXApplication

    app = MedeXApplication()
    await app.startup()

    response = await app.query("¿Qué es la diabetes?")
    print(response)

    await app.shutdown()

For CLI usage:
    python -m medex

Configuration via environment variables or .env file.
See config.py for all available options.

Copyright (c) 2025 Gonzalo Romero (DeepRatAI)
Licensed under MIT License
"""

from __future__ import annotations

__version__ = "2.0.0"
__author__ = "Gonzalo Romero"
__email__ = "gonzalorome6@gmail.com"
__license__ = "MIT"


def __getattr__(name: str):
    """Lazy import for optional dependencies."""
    # Legacy imports
    if name == "MedeXEngine":
        from medex.core.engine import MedeXEngine

        return MedeXEngine
    if name == "MedeXConfig":
        from medex.core.config import MedeXConfig

        return MedeXConfig

    # V2 imports
    if name == "MedeXApplication":
        from medex.main import MedeXApplication

        return MedeXApplication
    if name == "ApplicationState":
        from medex.main import ApplicationState

        return ApplicationState
    if name == "ServiceContainer":
        from medex.main import ServiceContainer

        return ServiceContainer
    if name == "create_application":
        from medex.main import create_application

        return create_application
    if name == "run_server":
        from medex.main import run_server

        return run_server
    if name == "load_config":
        from medex.config import load_config

        return load_config
    if name == "Environment":
        from medex.config import Environment

        return Environment

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    # Version info
    "__version__",
    "__author__",
    "__email__",
    "__license__",
    # Legacy (V1)
    "MedeXEngine",
    "MedeXConfig",
    # V2 Main
    "MedeXApplication",
    "ApplicationState",
    "ServiceContainer",
    "create_application",
    "run_server",
    # V2 Config
    "load_config",
    "Environment",
]
