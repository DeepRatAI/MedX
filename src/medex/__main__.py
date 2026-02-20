#!/usr/bin/env python3
# =============================================================================
# MedeX - CLI Entry Point
# =============================================================================
"""
Command-line interface for MedeX.

Usage:
    python -m medex                    # Start server
    python -m medex --help             # Show help
    python -m medex serve              # Start API server
    python -m medex query "question"   # Single query
    python -m medex health             # Check health
"""

from __future__ import annotations

import argparse
import asyncio
import sys


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        prog="medex",
        description="MedeX - Asistente Médico Educativo con IA",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m medex                     Start the API server
  python -m medex serve --port 8080   Start on custom port
  python -m medex query "¿Qué es la diabetes?"
  python -m medex health              Check system health
        """,
    )

    parser.add_argument(
        "--version",
        "-v",
        action="store_true",
        help="Show version and exit",
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Serve command
    serve_parser = subparsers.add_parser("serve", help="Start API server")
    serve_parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind to (default: 0.0.0.0)",
    )
    serve_parser.add_argument(
        "--port",
        "-p",
        type=int,
        default=8000,
        help="Port to bind to (default: 8000)",
    )
    serve_parser.add_argument(
        "--workers",
        "-w",
        type=int,
        default=1,
        help="Number of workers (default: 1)",
    )

    # Query command
    query_parser = subparsers.add_parser("query", help="Execute a single query")
    query_parser.add_argument(
        "question",
        help="The medical question to ask",
    )
    query_parser.add_argument(
        "--user-type",
        "-t",
        choices=["educational", "professional", "research"],
        default="educational",
        help="User type (default: educational)",
    )
    query_parser.add_argument(
        "--stream",
        "-s",
        action="store_true",
        help="Stream the response",
    )

    # Health command
    subparsers.add_parser("health", help="Check system health")

    # Config command
    config_parser = subparsers.add_parser("config", help="Show configuration")
    config_parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate configuration",
    )

    return parser.parse_args()


async def cmd_serve(args: argparse.Namespace) -> int:
    """Start the API server."""
    from medex.main import MedeXApplication

    app = MedeXApplication()
    await app.run()
    return 0


async def cmd_query(args: argparse.Namespace) -> int:
    """Execute a single query."""
    from medex.main import MedeXApplication

    app = MedeXApplication()
    await app.startup()

    try:
        if args.stream:
            print("Streaming not implemented in CLI yet")
            response = await app.query(args.question, args.user_type)
        else:
            response = await app.query(args.question, args.user_type)

        print("\n" + "=" * 60)
        print("RESPUESTA:")
        print("=" * 60)
        print(response.get("response", "Sin respuesta"))
        print("=" * 60)

        if response.get("sources"):
            print("\nFuentes:")
            for src in response["sources"]:
                print(f"  - {src.get('title', 'N/A')}")

    finally:
        await app.shutdown()

    return 0


async def cmd_health(args: argparse.Namespace) -> int:
    """Check system health."""
    from medex.main import MedeXApplication

    app = MedeXApplication()
    await app.startup()

    try:
        health = await app.health()

        print("\n" + "=" * 40)
        print("ESTADO DEL SISTEMA")
        print("=" * 40)
        print(f"  Estado: {health['status']}")
        print(f"  Listo: {'Sí' if health['ready'] else 'No'}")
        print(f"  Uptime: {health['uptime_seconds']:.2f}s")
        print("=" * 40)

        return 0 if health["status"] == "healthy" else 1

    finally:
        await app.shutdown()


async def cmd_config(args: argparse.Namespace) -> int:
    """Show or validate configuration."""
    from medex.config import load_config

    config = load_config()

    if args.validate:
        errors = config.validate()
        if errors:
            print("Errores de configuración:")
            for error in errors:
                print(f"  ✗ {error}")
            return 1
        else:
            print("✓ Configuración válida")
            return 0

    # Show config
    import json

    print(json.dumps(config.to_dict(), indent=2))
    return 0


async def main_async(args: argparse.Namespace) -> int:
    """Async main entry point."""
    if args.version:
        from medex import __version__

        print(f"MedeX v{__version__}")
        return 0

    if args.command is None or args.command == "serve":
        return await cmd_serve(args)
    elif args.command == "query":
        return await cmd_query(args)
    elif args.command == "health":
        return await cmd_health(args)
    elif args.command == "config":
        return await cmd_config(args)
    else:
        print(f"Unknown command: {args.command}")
        return 1


def main() -> None:
    """Main entry point."""
    args = parse_args()

    try:
        exit_code = asyncio.run(main_async(args))
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\nInterrumpido por el usuario")
        sys.exit(130)
    except Exception as e:
        print(f"Error: {e}")
        if args.debug:
            import traceback

            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
