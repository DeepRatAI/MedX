#!/usr/bin/env python3
"""
MedeX Configuration Module
Handles API keys and configuration for different deployment environments
"""

import os
from pathlib import Path
from typing import Optional


class MedeXConfig:
    """Configuration manager for MedeX system"""

    def __init__(self):
        self.project_root = Path(__file__).parent
        self.api_key_file = self.project_root / "api_key.txt"

    def get_kimi_api_key(self) -> str:
        """
        Get Kimi API key from multiple sources in order of priority:
        1. Environment variable KIMI_API_KEY (for HF Spaces and production)
        2. api_key.txt file (for local development)
        3. Hardcoded default key (fallback for demo)
        """

        # Try environment variable first (HF Spaces secrets)
        api_key = os.getenv("KIMI_API_KEY")
        if api_key and api_key.strip():
            print("✅ Using API key from environment variable")
            return api_key.strip()

        # Try api_key.txt file
        if self.api_key_file.exists():
            try:
                with open(self.api_key_file, "r") as f:
                    api_key = f.read().strip()
                    if api_key:
                        print("✅ Using API key from api_key.txt")
                        return api_key
            except Exception as e:
                print(f"⚠️ Could not read api_key.txt: {e}")

        # Fallback to hardcoded key (for demo purposes)
        default_key = "YOUR_API_KEY_HERE"
        print("⚠️ Using default API key (demo mode)")
        return default_key

    def get_moonshot_base_url(self) -> str:
        """Get Moonshot AI API base URL"""
        return os.getenv("MOONSHOT_BASE_URL", "https://api.moonshot.ai/v1")

    def is_production(self) -> bool:
        """Check if running in production environment (HF Spaces)"""
        return bool(os.getenv("SPACE_ID")) or bool(os.getenv("KIMI_API_KEY"))

    def get_rag_cache_dir(self) -> Path:
        """Get RAG cache directory"""
        cache_dir = self.project_root / "rag_cache"
        cache_dir.mkdir(exist_ok=True)
        return cache_dir

    def get_logs_dir(self) -> Path:
        """Get logs directory"""
        logs_dir = self.project_root / "logs"
        logs_dir.mkdir(exist_ok=True)
        return logs_dir


# Global config instance
config = MedeXConfig()
