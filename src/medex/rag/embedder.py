# =============================================================================
# MedeX - RAG System: Embedder
# =============================================================================
"""
Text embedding generation for semantic search.

This module provides:
- Multiple embedding model support
- Batch embedding generation
- Caching for efficiency
- Normalization and preprocessing

Supported backends:
- OpenAI embeddings (text-embedding-3-small)
- HuggingFace sentence-transformers
- Local models (for privacy/cost)

Design:
- Async-first for non-blocking operations
- Automatic batching for efficiency
- L2 normalization for cosine similarity
- Model-agnostic interface
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import numpy as np

from .models import Chunk, Embedding

if TYPE_CHECKING:
    from redis.asyncio import Redis

logger = logging.getLogger(__name__)


# =============================================================================
# Configuration
# =============================================================================


@dataclass
class EmbedderConfig:
    """Configuration for embedding generation."""

    # Model settings
    model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    dimensions: int = 384
    normalize: bool = True

    # Performance
    batch_size: int = 32
    max_tokens: int = 512
    timeout: float = 30.0

    # Caching
    cache_enabled: bool = True
    cache_ttl: int = 86400 * 7  # 7 days

    # Preprocessing
    lowercase: bool = False
    strip_newlines: bool = True


# =============================================================================
# Base Embedder
# =============================================================================


class BaseEmbedder(ABC):
    """Abstract base class for text embedders."""

    def __init__(self, config: EmbedderConfig | None = None) -> None:
        """Initialize embedder with configuration."""
        self.config = config or EmbedderConfig()
        self._cache: Redis | None = None

    def set_cache(self, cache_client: Redis) -> None:
        """Set Redis cache client."""
        self._cache = cache_client

    @abstractmethod
    async def embed_text(self, text: str) -> Embedding:
        """
        Generate embedding for a single text.

        Args:
            text: Text to embed

        Returns:
            Embedding object
        """
        pass

    @abstractmethod
    async def embed_texts(self, texts: list[str]) -> list[Embedding]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of Embedding objects
        """
        pass

    async def embed_chunk(self, chunk: Chunk) -> Chunk:
        """
        Generate embedding for a chunk and attach it.

        Args:
            chunk: Chunk to embed

        Returns:
            Chunk with embedding attached
        """
        embedding = await self.embed_text(chunk.content)
        chunk.embedding = embedding.vector
        return chunk

    async def embed_chunks(self, chunks: list[Chunk]) -> list[Chunk]:
        """
        Generate embeddings for multiple chunks.

        Args:
            chunks: Chunks to embed

        Returns:
            Chunks with embeddings attached
        """
        texts = [c.content for c in chunks]
        embeddings = await self.embed_texts(texts)

        for chunk, embedding in zip(chunks, embeddings):
            chunk.embedding = embedding.vector

        return chunks

    def _preprocess(self, text: str) -> str:
        """Preprocess text before embedding."""
        if self.config.strip_newlines:
            text = " ".join(text.split())
        if self.config.lowercase:
            text = text.lower()
        return text.strip()

    def _get_cache_key(self, text: str) -> str:
        """Generate cache key for text."""
        text_hash = hashlib.sha256(text.encode()).hexdigest()[:16]
        return f"emb:{self.config.model_name}:{text_hash}"

    async def _get_cached(self, text: str) -> list[float] | None:
        """Get cached embedding if available."""
        if not self._cache or not self.config.cache_enabled:
            return None

        try:
            import json

            key = self._get_cache_key(text)
            cached = await self._cache.get(key)
            if cached:
                return json.loads(cached)
        except Exception as e:
            logger.warning(f"Cache read error: {e}")

        return None

    async def _set_cached(self, text: str, embedding: list[float]) -> None:
        """Cache embedding."""
        if not self._cache or not self.config.cache_enabled:
            return

        try:
            import json

            key = self._get_cache_key(text)
            await self._cache.setex(
                key,
                self.config.cache_ttl,
                json.dumps(embedding),
            )
        except Exception as e:
            logger.warning(f"Cache write error: {e}")


# =============================================================================
# Sentence Transformer Embedder
# =============================================================================


class SentenceTransformerEmbedder(BaseEmbedder):
    """
    Embedder using sentence-transformers library.

    This is the recommended embedder for local/privacy-focused deployments.
    Uses multilingual models optimized for semantic similarity.
    """

    def __init__(self, config: EmbedderConfig | None = None) -> None:
        """Initialize with sentence-transformers model."""
        super().__init__(config)
        self._model = None
        self._lock = asyncio.Lock()

    async def _get_model(self):
        """Lazy-load the model."""
        if self._model is None:
            async with self._lock:
                if self._model is None:
                    # Import here to avoid loading at module import
                    from sentence_transformers import SentenceTransformer

                    self._model = SentenceTransformer(self.config.model_name)
                    logger.info(f"Loaded embedding model: {self.config.model_name}")
        return self._model

    async def embed_text(self, text: str) -> Embedding:
        """Generate embedding for single text."""
        # Check cache first
        cached = await self._get_cached(text)
        if cached:
            return Embedding(
                vector=cached,
                model=self.config.model_name,
                dimensions=len(cached),
            )

        # Generate embedding
        processed = self._preprocess(text)
        model = await self._get_model()

        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        vector = await loop.run_in_executor(
            None,
            lambda: model.encode(
                processed, normalize_embeddings=self.config.normalize
            ).tolist(),
        )

        # Cache result
        await self._set_cached(text, vector)

        return Embedding(
            vector=vector,
            model=self.config.model_name,
            dimensions=len(vector),
            normalized=self.config.normalize,
        )

    async def embed_texts(self, texts: list[str]) -> list[Embedding]:
        """Generate embeddings for multiple texts."""
        if not texts:
            return []

        # Check cache for all texts
        embeddings: list[Embedding | None] = [None] * len(texts)
        uncached_indices: list[int] = []
        uncached_texts: list[str] = []

        for i, text in enumerate(texts):
            cached = await self._get_cached(text)
            if cached:
                embeddings[i] = Embedding(
                    vector=cached,
                    model=self.config.model_name,
                    dimensions=len(cached),
                )
            else:
                uncached_indices.append(i)
                uncached_texts.append(self._preprocess(text))

        # Generate embeddings for uncached texts
        if uncached_texts:
            model = await self._get_model()

            # Process in batches
            all_vectors = []
            for batch_start in range(0, len(uncached_texts), self.config.batch_size):
                batch = uncached_texts[
                    batch_start : batch_start + self.config.batch_size
                ]

                loop = asyncio.get_event_loop()
                batch_vectors = await loop.run_in_executor(
                    None,
                    lambda b=batch: model.encode(
                        b, normalize_embeddings=self.config.normalize
                    ).tolist(),
                )
                all_vectors.extend(batch_vectors)

            # Fill in results and cache
            for idx, vector in zip(uncached_indices, all_vectors):
                embeddings[idx] = Embedding(
                    vector=vector,
                    model=self.config.model_name,
                    dimensions=len(vector),
                    normalized=self.config.normalize,
                )
                await self._set_cached(texts[idx], vector)

        return embeddings  # type: ignore


# =============================================================================
# OpenAI Embedder
# =============================================================================


class OpenAIEmbedder(BaseEmbedder):
    """
    Embedder using OpenAI's embedding API.

    Uses text-embedding-3-small by default (1536 dimensions).
    Requires OPENAI_API_KEY environment variable.
    """

    def __init__(
        self,
        config: EmbedderConfig | None = None,
        api_key: str | None = None,
    ) -> None:
        """Initialize with OpenAI client."""
        config = config or EmbedderConfig()
        config.model_name = config.model_name or "text-embedding-3-small"
        config.dimensions = config.dimensions or 1536
        super().__init__(config)

        self._api_key = api_key
        self._client = None

    async def _get_client(self):
        """Lazy-load OpenAI client."""
        if self._client is None:
            import os
            from openai import AsyncOpenAI

            api_key = self._api_key or os.getenv("OPENAI_API_KEY")
            self._client = AsyncOpenAI(api_key=api_key)

        return self._client

    async def embed_text(self, text: str) -> Embedding:
        """Generate embedding using OpenAI API."""
        # Check cache
        cached = await self._get_cached(text)
        if cached:
            return Embedding(
                vector=cached,
                model=self.config.model_name,
                dimensions=len(cached),
            )

        client = await self._get_client()
        processed = self._preprocess(text)

        response = await client.embeddings.create(
            model=self.config.model_name,
            input=processed,
        )

        vector = response.data[0].embedding

        # Normalize if needed
        if self.config.normalize:
            vector = self._normalize(vector)

        # Cache
        await self._set_cached(text, vector)

        return Embedding(
            vector=vector,
            model=self.config.model_name,
            dimensions=len(vector),
            normalized=self.config.normalize,
        )

    async def embed_texts(self, texts: list[str]) -> list[Embedding]:
        """Generate embeddings for multiple texts."""
        if not texts:
            return []

        # Check cache
        embeddings: list[Embedding | None] = [None] * len(texts)
        uncached_indices: list[int] = []
        uncached_texts: list[str] = []

        for i, text in enumerate(texts):
            cached = await self._get_cached(text)
            if cached:
                embeddings[i] = Embedding(
                    vector=cached,
                    model=self.config.model_name,
                    dimensions=len(cached),
                )
            else:
                uncached_indices.append(i)
                uncached_texts.append(self._preprocess(text))

        # Generate for uncached
        if uncached_texts:
            client = await self._get_client()

            # Process in batches (OpenAI limit is 2048)
            all_vectors = []
            for batch_start in range(
                0, len(uncached_texts), min(self.config.batch_size, 100)
            ):
                batch = uncached_texts[batch_start : batch_start + 100]

                response = await client.embeddings.create(
                    model=self.config.model_name,
                    input=batch,
                )

                batch_vectors = [d.embedding for d in response.data]
                all_vectors.extend(batch_vectors)

            # Fill results
            for idx, vector in zip(uncached_indices, all_vectors):
                if self.config.normalize:
                    vector = self._normalize(vector)

                embeddings[idx] = Embedding(
                    vector=vector,
                    model=self.config.model_name,
                    dimensions=len(vector),
                    normalized=self.config.normalize,
                )
                await self._set_cached(texts[idx], vector)

        return embeddings  # type: ignore

    def _normalize(self, vector: list[float]) -> list[float]:
        """L2 normalize vector."""
        arr = np.array(vector)
        norm = np.linalg.norm(arr)
        if norm > 0:
            arr = arr / norm
        return arr.tolist()


# =============================================================================
# Free/Local Model Embedder (for $0 cost)
# =============================================================================


class FreeEmbedder(SentenceTransformerEmbedder):
    """
    Free embedder using open-source models.

    Recommended models for medical Spanish:
    - paraphrase-multilingual-MiniLM-L12-v2 (384d, fast)
    - paraphrase-multilingual-mpnet-base-v2 (768d, better quality)
    - distiluse-base-multilingual-cased-v2 (512d, good balance)
    """

    RECOMMENDED_MODELS = {
        "fast": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        "balanced": "sentence-transformers/distiluse-base-multilingual-cased-v2",
        "quality": "sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
    }

    def __init__(
        self,
        quality: str = "fast",
        config: EmbedderConfig | None = None,
    ) -> None:
        """
        Initialize with quality preset.

        Args:
            quality: One of "fast", "balanced", "quality"
            config: Optional configuration override
        """
        config = config or EmbedderConfig()
        config.model_name = self.RECOMMENDED_MODELS.get(
            quality, self.RECOMMENDED_MODELS["fast"]
        )

        # Set dimensions based on model
        if "MiniLM" in config.model_name:
            config.dimensions = 384
        elif "mpnet" in config.model_name:
            config.dimensions = 768
        else:
            config.dimensions = 512

        super().__init__(config)
        logger.info(
            f"Initialized free embedder with {quality} quality: {config.model_name}"
        )


# =============================================================================
# Factory Function
# =============================================================================


class EmbedderType(str):
    """Embedder type constants."""

    SENTENCE_TRANSFORMER = "sentence_transformer"
    OPENAI = "openai"
    FREE = "free"


def create_embedder(
    embedder_type: str = EmbedderType.FREE,
    config: EmbedderConfig | None = None,
    **kwargs: Any,
) -> BaseEmbedder:
    """
    Factory function to create embedder instances.

    Args:
        embedder_type: Type of embedder to create
        config: Optional embedder configuration
        **kwargs: Additional arguments for specific embedders

    Returns:
        Configured embedder instance
    """
    if embedder_type == EmbedderType.OPENAI:
        return OpenAIEmbedder(config, api_key=kwargs.get("api_key"))
    elif embedder_type == EmbedderType.FREE:
        return FreeEmbedder(quality=kwargs.get("quality", "fast"), config=config)
    else:
        return SentenceTransformerEmbedder(config)
