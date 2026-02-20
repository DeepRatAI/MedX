"""
MedeX UI - Reflex Configuration
================================
Production-grade configuration for MedeX Reflex application.
"""

import reflex as rx

config = rx.Config(
    app_name="medex_ui",
    title="MedeX - Asistente Médico IA",
    description="Sistema de asistencia médica educativa potenciado por IA",
    # Frontend configuration
    frontend_port=3001,
    backend_port=8002,
    # Disable sitemap plugin warning
    disable_plugins=["reflex.plugins.sitemap.SitemapPlugin"],
    # Theme
    tailwind={
        "theme": {
            "extend": {
                "colors": {
                    "medex": {
                        "primary": "#3b8e72",
                        "primary-light": "#90ceb1",
                        "primary-dark": "#2d6b56",
                        "secondary": "#1a1a2e",
                        "accent": "#ff751f",
                        "emergency": "#ef4444",
                        "success": "#22c55e",
                        "warning": "#f59e0b",
                    }
                },
                "fontFamily": {
                    "sans": ["Inter", "system-ui", "sans-serif"],
                    "medical": ["Roboto", "Arial", "sans-serif"],
                },
            }
        },
        "plugins": [],
    },
    # Environment
    env=rx.Env.DEV,
)
