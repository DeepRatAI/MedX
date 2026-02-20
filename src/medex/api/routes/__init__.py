# =============================================================================
# MedeX - API Routes
# =============================================================================
"""
API routes module.

Contains endpoint definitions for:
- Health checks
- Query endpoints
- Admin endpoints
"""

from __future__ import annotations

__all__ = [
    "HEALTH_ROUTES",
    "QUERY_ROUTES",
    "ADMIN_ROUTES",
]

# Route tags for OpenAPI documentation
HEALTH_ROUTES = ["health"]
QUERY_ROUTES = ["query", "stream", "search"]
ADMIN_ROUTES = ["admin", "metrics", "audit"]
