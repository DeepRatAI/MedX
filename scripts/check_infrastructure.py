#!/usr/bin/env python3
# =============================================================================
# MedeX - Infrastructure Health Check Script
# =============================================================================
"""
Comprehensive health check for MedeX V2 infrastructure.

Checks:
- PostgreSQL 16 connectivity and version
- Redis 7 connectivity and operations
- Qdrant vector database connectivity
- Connection pooling status
- Basic performance metrics

Usage:
    python scripts/check_infrastructure.py
    python scripts/check_infrastructure.py --verbose
    python scripts/check_infrastructure.py --json
"""

from __future__ import annotations

import asyncio
import argparse
import json
import sys
import os
import time
from datetime import datetime
from typing import Any

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# =============================================================================
# Color Output
# =============================================================================


class Colors:
    """ANSI color codes for terminal output."""

    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    BOLD = "\033[1m"
    END = "\033[0m"


def print_status(name: str, status: str, details: str = ""):
    """Print colored status line."""
    if status == "healthy":
        color = Colors.GREEN
        symbol = "✓"
    elif status == "unhealthy":
        color = Colors.RED
        symbol = "✗"
    else:
        color = Colors.YELLOW
        symbol = "?"

    print(f"  {color}{symbol}{Colors.END} {name}: {color}{status}{Colors.END}")
    if details:
        print(f"      {Colors.BLUE}{details}{Colors.END}")


# =============================================================================
# Health Check Functions
# =============================================================================


async def check_postgresql() -> dict[str, Any]:
    """Check PostgreSQL connectivity and status."""
    result = {
        "name": "PostgreSQL",
        "status": "unknown",
        "version": None,
        "latency_ms": None,
        "details": {},
        "error": None,
    }

    try:
        from src.medex.db.connection import (
            get_async_engine,
            init_db,
            close_db,
            check_db_health,
        )

        await init_db()
        health = await check_db_health()
        await close_db()

        result["status"] = health["status"]
        result["latency_ms"] = health.get("latency_ms")
        result["details"] = {
            "database": health.get("database"),
            "host": health.get("host"),
            "pool_size": health.get("pool_size"),
        }

        # Get version
        from sqlalchemy.ext.asyncio import create_async_engine
        from sqlalchemy import text

        url = f"postgresql+asyncpg://{os.getenv('MEDEX_POSTGRES_USER', 'medex')}:{os.getenv('MEDEX_POSTGRES_PASSWORD', 'medex_secure_password')}@{os.getenv('MEDEX_POSTGRES_HOST', 'localhost')}:{os.getenv('MEDEX_POSTGRES_PORT', '5432')}/{os.getenv('MEDEX_POSTGRES_DB', 'medex')}"

        engine = create_async_engine(url)
        async with engine.begin() as conn:
            ver = await conn.execute(text("SHOW server_version"))
            result["version"] = ver.scalar()
        await engine.dispose()

    except Exception as e:
        result["status"] = "unhealthy"
        result["error"] = str(e)

    return result


async def check_redis() -> dict[str, Any]:
    """Check Redis connectivity and status."""
    result = {
        "name": "Redis",
        "status": "unknown",
        "version": None,
        "latency_ms": None,
        "details": {},
        "error": None,
    }

    try:
        from src.medex.db.cache import (
            get_redis_client,
            close_redis,
            check_redis_health,
        )

        await get_redis_client()
        health = await check_redis_health()
        await close_redis()

        result["status"] = health["status"]
        result["latency_ms"] = health.get("latency_ms")
        result["version"] = health.get("redis_version")
        result["details"] = {
            "connected_clients": health.get("connected_clients"),
        }

    except Exception as e:
        result["status"] = "unhealthy"
        result["error"] = str(e)

    return result


async def check_qdrant() -> dict[str, Any]:
    """Check Qdrant connectivity and status."""
    result = {
        "name": "Qdrant",
        "status": "unknown",
        "version": None,
        "latency_ms": None,
        "details": {},
        "error": None,
    }

    try:
        import httpx

        host = os.getenv("MEDEX_QDRANT_HOST", "localhost")
        port = os.getenv("MEDEX_QDRANT_HTTP_PORT", "6333")
        url = f"http://{host}:{port}"

        start = time.perf_counter()

        async with httpx.AsyncClient() as client:
            # Check readiness
            response = await client.get(f"{url}/readyz", timeout=5.0)
            latency = (time.perf_counter() - start) * 1000

            if response.status_code == 200:
                result["status"] = "healthy"
            else:
                result["status"] = "unhealthy"

            result["latency_ms"] = round(latency, 2)

            # Get version/info
            try:
                info_response = await client.get(f"{url}/", timeout=5.0)
                if info_response.status_code == 200:
                    info = info_response.json()
                    result["version"] = info.get("version")
            except Exception:
                pass

            # Get collections count
            try:
                collections_response = await client.get(
                    f"{url}/collections", timeout=5.0
                )
                if collections_response.status_code == 200:
                    data = collections_response.json()
                    result["details"]["collections_count"] = len(
                        data.get("result", {}).get("collections", [])
                    )
            except Exception:
                pass

    except Exception as e:
        result["status"] = "unhealthy"
        result["error"] = str(e)

    return result


# =============================================================================
# Main
# =============================================================================


async def run_health_checks(verbose: bool = False) -> dict[str, Any]:
    """Run all health checks."""
    start_time = time.perf_counter()

    results = {
        "timestamp": datetime.now().isoformat(),
        "overall_status": "healthy",
        "checks": [],
        "duration_ms": 0,
    }

    # Run checks in parallel
    checks = await asyncio.gather(
        check_postgresql(),
        check_redis(),
        check_qdrant(),
        return_exceptions=True,
    )

    for check in checks:
        if isinstance(check, Exception):
            results["checks"].append(
                {
                    "name": "Unknown",
                    "status": "error",
                    "error": str(check),
                }
            )
            results["overall_status"] = "unhealthy"
        else:
            results["checks"].append(check)
            if check["status"] != "healthy":
                results["overall_status"] = "unhealthy"

    results["duration_ms"] = round((time.perf_counter() - start_time) * 1000, 2)

    return results


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="MedeX Infrastructure Health Check")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--json", "-j", action="store_true", help="JSON output")
    args = parser.parse_args()

    # Run checks
    results = asyncio.run(run_health_checks(verbose=args.verbose))

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print()
        print(f"{Colors.BOLD}MedeX Infrastructure Health Check{Colors.END}")
        print("=" * 40)
        print()

        for check in results["checks"]:
            details = []
            if check.get("version"):
                details.append(f"v{check['version']}")
            if check.get("latency_ms"):
                details.append(f"{check['latency_ms']}ms")
            if check.get("error"):
                details.append(f"Error: {check['error']}")

            print_status(
                check["name"], check["status"], " | ".join(details) if details else ""
            )

        print()
        print("-" * 40)

        if results["overall_status"] == "healthy":
            print(
                f"{Colors.GREEN}{Colors.BOLD}Overall: All systems operational ✓{Colors.END}"
            )
        else:
            print(
                f"{Colors.RED}{Colors.BOLD}Overall: Some systems are unhealthy ✗{Colors.END}"
            )

        print(f"Completed in {results['duration_ms']}ms")
        print()

    # Exit with appropriate code
    sys.exit(0 if results["overall_status"] == "healthy" else 1)


if __name__ == "__main__":
    main()
