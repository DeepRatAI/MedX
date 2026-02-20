"""
MedeX Model Providers.

Abstraction layer for multiple AI model providers with automatic fallback.
"""

from medex.providers.base import ModelProvider, ProviderConfig
from medex.providers.moonshot import MoonshotProvider
from medex.providers.huggingface import HuggingFaceProvider
from medex.providers.manager import ProviderManager

__all__ = [
    "ModelProvider",
    "ProviderConfig", 
    "MoonshotProvider",
    "HuggingFaceProvider",
    "ProviderManager",
]
