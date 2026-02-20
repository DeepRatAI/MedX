#!/usr/bin/env python3
"""
MedeX UI - Run Script
=====================
Script to run the MedeX Reflex UI application.

Usage:
    python run.py              # Development mode
    python run.py --prod       # Production mode
    python run.py --init       # Initialize Reflex
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Run MedeX Reflex UI")
    parser.add_argument("--prod", action="store_true", help="Production mode")
    parser.add_argument("--init", action="store_true", help="Initialize Reflex")
    parser.add_argument("--port", type=int, default=3000, help="Frontend port")
    parser.add_argument("--backend-port", type=int, default=8001, help="Backend port")
    args = parser.parse_args()

    # Change to UI directory
    ui_dir = Path(__file__).parent
    os.chdir(ui_dir)

    if args.init:
        print("🔧 Initializing Reflex...")
        subprocess.run([sys.executable, "-m", "reflex", "init"], check=True)
        print("✅ Reflex initialized!")
        return

    # Set environment
    env = os.environ.copy()
    env["REFLEX_ENV"] = "prod" if args.prod else "dev"

    # Build command
    cmd = [sys.executable, "-m", "reflex", "run"]

    if args.prod:
        cmd.extend(["--env", "prod"])

    cmd.extend(["--frontend-port", str(args.port)])
    cmd.extend(["--backend-port", str(args.backend_port)])

    print(f"""
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║   🏥 MedeX UI - Reflex Application                               ║
║                                                                  ║
║   Mode: {"Production" if args.prod else "Development"}                                          ║
║   Frontend: http://localhost:{args.port}                              ║
║   Backend:  http://localhost:{args.backend_port}                              ║
║                                                                  ║
║   API Server: http://localhost:8000                              ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
    """)

    subprocess.run(cmd, env=env)


if __name__ == "__main__":
    main()
