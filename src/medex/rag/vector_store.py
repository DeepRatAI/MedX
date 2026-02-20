# =============================================================================
# MedeX - RAG System: Vector Store
# =============================================================================
"""
Vector storage and retrieval using Qdrant.

This module provides:
- Qdrant client wrapper
- Collection management
- Vector indexing and search
- Metadata filtering
- Batch operations

Design:
- Async-first API
- Automatic collection creation
- Configurable similarity metrics
- Medical-specific filtering
- High availability support
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from .models import Chunk, RelevanceLevel, SearchResult

if TYPE_CHECKING:
    from qdrant_client import QdrantClient

logger = logging.getLogger(__name__)


# =============================================================================
# Configuration
# =============================================================================


@dataclass
class VectorStoreConfig:
    """Configuration for vector store."""

    # Connection
    host: str = "localhost"
    port: int = 6333
    grpc_port: int = 6334
    prefer_grpc: bool = True
    api_key: str | None = None

    # Collection settings
    collection_name: str = "medex_knowledge"
    vector_size: int = 384  # Match embedder dimensions
    distance: str = "Cosine"  # Cosine, Euclid, Dot

    # Search defaults
    default_limit: int = 10
    score_threshold: float = 0.5

    # Performance
    on_disk: bool = False
    hnsw_ef_construct: int = 100
    hnsw_m: int = 16


# =============================================================================
# Vector Store Implementation
# =============================================================================


class VectorStore:
    """
    Qdrant-backed vector store for semantic search.

    This class provides a high-level interface for:
    - Storing document chunks with embeddings
    - Semantic similarity search
    - Metadata filtering
    - Batch operations

    Example:
        store = VectorStore(config)
        await store.initialize()

        # Index chunks
        await store.upsert_chunks(chunks)

        # Search
        results = await store.search(query_embedding, top_k=5)
    """

    def __init__(self, config: VectorStoreConfig | None = None) -> None:
        """Initialize vector store."""
        self.config = config or VectorStoreConfig()
        self._client: QdrantClient | None = None
        self._initialized = False

    async def initialize(self) -> None:
        """
        Initialize connection and ensure collection exists.

        This method must be called before using the store.
        """
        if self._initialized:
            return

        from qdrant_client import QdrantClient
        from qdrant_client.models import Distance, VectorParams

        # Create client
        self._client = QdrantClient(
            host=self.config.host,
            port=self.config.port,
            grpc_port=self.config.grpc_port,
            prefer_grpc=self.config.prefer_grpc,
            api_key=self.config.api_key,
        )

        # Check/create collection
        distance_map = {
            "Cosine": Distance.COSINE,
            "Euclid": Distance.EUCLID,
            "Dot": Distance.DOT,
        }

        collections = self._client.get_collections().collections
        collection_names = [c.name for c in collections]

        if self.config.collection_name not in collection_names:
            self._client.create_collection(
                collection_name=self.config.collection_name,
                vectors_config=VectorParams(
                    size=self.config.vector_size,
                    distance=distance_map.get(self.config.distance, Distance.COSINE),
                    on_disk=self.config.on_disk,
                ),
            )
            logger.info(f"Created collection: {self.config.collection_name}")
        else:
            logger.info(f"Using existing collection: {self.config.collection_name}")

        self._initialized = True

    async def close(self) -> None:
        """Close the client connection."""
        if self._client:
            self._client.close()
            self._client = None
            self._initialized = False

    @property
    def client(self) -> QdrantClient:
        """Get Qdrant client."""
        if not self._client:
            raise RuntimeError("VectorStore not initialized")
        return self._client

    # =========================================================================
    # Indexing Operations
    # =========================================================================

    async def upsert_chunk(self, chunk: Chunk) -> str:
        """
        Insert or update a single chunk.

        Args:
            chunk: Chunk with embedding to store

        Returns:
            Point ID
        """
        if not chunk.embedding:
            raise ValueError(f"Chunk {chunk.id} has no embedding")

        from qdrant_client.models import PointStruct

        point = PointStruct(
            id=chunk.id,
            vector=chunk.embedding,
            payload=self._chunk_to_payload(chunk),
        )

        # Run in thread pool (qdrant-client is sync)
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: self.client.upsert(
                collection_name=self.config.collection_name,
                points=[point],
            ),
        )

        logger.debug(f"Upserted chunk: {chunk.id}")
        return chunk.id

    async def upsert_chunks(
        self, chunks: list[Chunk], batch_size: int = 100
    ) -> list[str]:
        """
        Insert or update multiple chunks.

        Args:
            chunks: Chunks with embeddings to store
            batch_size: Number of chunks per batch

        Returns:
            List of point IDs
        """
        if not chunks:
            return []

        from qdrant_client.models import PointStruct

        points = []
        for chunk in chunks:
            if not chunk.embedding:
                logger.warning(f"Skipping chunk {chunk.id} - no embedding")
                continue

            points.append(
                PointStruct(
                    id=chunk.id,
                    vector=chunk.embedding,
                    payload=self._chunk_to_payload(chunk),
                )
            )

        # Batch upsert
        loop = asyncio.get_event_loop()
        for i in range(0, len(points), batch_size):
            batch = points[i : i + batch_size]
            await loop.run_in_executor(
                None,
                lambda b=batch: self.client.upsert(
                    collection_name=self.config.collection_name,
                    points=b,
                ),
            )

        logger.info(f"Upserted {len(points)} chunks")
        return [p.id for p in points]

    async def delete_chunk(self, chunk_id: str) -> bool:
        """Delete a chunk by ID."""
        from qdrant_client.models import PointIdsList

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: self.client.delete(
                collection_name=self.config.collection_name,
                points_selector=PointIdsList(points=[chunk_id]),
            ),
        )
        return True

    async def delete_by_document(self, document_id: str) -> int:
        """
        Delete all chunks belonging to a document.

        Args:
            document_id: Document ID to delete chunks for

        Returns:
            Number of deleted chunks
        """
        from qdrant_client.models import FieldCondition, Filter, MatchValue

        # First count
        loop = asyncio.get_event_loop()
        count_result = await loop.run_in_executor(
            None,
            lambda: self.client.count(
                collection_name=self.config.collection_name,
                count_filter=Filter(
                    must=[
                        FieldCondition(
                            key="document_id",
                            match=MatchValue(value=document_id),
                        )
                    ]
                ),
            ),
        )

        # Delete
        await loop.run_in_executor(
            None,
            lambda: self.client.delete(
                collection_name=self.config.collection_name,
                points_selector=Filter(
                    must=[
                        FieldCondition(
                            key="document_id",
                            match=MatchValue(value=document_id),
                        )
                    ]
                ),
            ),
        )

        return count_result.count

    # =========================================================================
    # Search Operations
    # =========================================================================

    async def search(
        self,
        query_embedding: list[float],
        top_k: int | None = None,
        score_threshold: float | None = None,
        filters: dict[str, Any] | None = None,
    ) -> list[SearchResult]:
        """
        Search for similar chunks.

        Args:
            query_embedding: Query vector
            top_k: Number of results to return
            score_threshold: Minimum similarity score
            filters: Metadata filters

        Returns:
            List of SearchResult objects
        """
        top_k = top_k or self.config.default_limit
        score_threshold = score_threshold or self.config.score_threshold

        # Build filter
        query_filter = self._build_filter(filters) if filters else None

        # Execute search
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(
            None,
            lambda: self.client.search(
                collection_name=self.config.collection_name,
                query_vector=query_embedding,
                limit=top_k,
                score_threshold=score_threshold,
                query_filter=query_filter,
                with_payload=True,
            ),
        )

        # Convert to SearchResult
        search_results = []
        for point in results:
            chunk = self._payload_to_chunk(point.id, point.payload)
            relevance = self._score_to_relevance(point.score)

            search_results.append(
                SearchResult(
                    chunk=chunk,
                    score=point.score,
                    relevance=relevance,
                )
            )

        return search_results

    async def search_with_rerank(
        self,
        query_embedding: list[float],
        query_text: str,
        top_k: int = 10,
        rerank_top_k: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> list[SearchResult]:
        """
        Search with semantic reranking.

        First retrieves more results, then reranks based on query.

        Args:
            query_embedding: Query vector
            query_text: Original query text (for reranking)
            top_k: Initial retrieval count
            rerank_top_k: Final result count after reranking
            filters: Metadata filters

        Returns:
            Reranked SearchResult list
        """
        # Get initial results (retrieve more than needed)
        initial_results = await self.search(
            query_embedding=query_embedding,
            top_k=top_k * 2,  # Over-retrieve for reranking
            filters=filters,
        )

        if not initial_results:
            return []

        # Reranking will be done by the Reranker component
        # For now, just return top results
        return initial_results[:rerank_top_k]

    # =========================================================================
    # Collection Management
    # =========================================================================

    async def get_collection_info(self) -> dict[str, Any]:
        """Get collection statistics."""
        loop = asyncio.get_event_loop()
        info = await loop.run_in_executor(
            None, lambda: self.client.get_collection(self.config.collection_name)
        )

        return {
            "name": self.config.collection_name,
            "vectors_count": info.vectors_count,
            "points_count": info.points_count,
            "indexed_vectors_count": info.indexed_vectors_count,
            "status": info.status.name,
            "config": {
                "vector_size": self.config.vector_size,
                "distance": self.config.distance,
            },
        }

    async def clear_collection(self) -> None:
        """Delete all points in collection."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None, lambda: self.client.delete_collection(self.config.collection_name)
        )

        # Recreate
        self._initialized = False
        await self.initialize()

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _chunk_to_payload(self, chunk: Chunk) -> dict[str, Any]:
        """Convert chunk to Qdrant payload."""
        return {
            "document_id": chunk.document_id,
            "content": chunk.content,
            "chunk_type": chunk.chunk_type.value,
            "index": chunk.index,
            "section_title": chunk.section_title,
            "page_number": chunk.page_number,
            "start_char": chunk.start_char,
            "end_char": chunk.end_char,
            "metadata": chunk.metadata,
        }

    def _payload_to_chunk(self, point_id: str, payload: dict[str, Any]) -> Chunk:
        """Convert Qdrant payload to Chunk."""
        from .models import ChunkType

        return Chunk(
            id=str(point_id),
            document_id=payload.get("document_id", ""),
            content=payload.get("content", ""),
            chunk_type=ChunkType(payload.get("chunk_type", "paragraph")),
            index=payload.get("index", 0),
            section_title=payload.get("section_title", ""),
            page_number=payload.get("page_number"),
            start_char=payload.get("start_char", 0),
            end_char=payload.get("end_char", 0),
            metadata=payload.get("metadata", {}),
        )

    def _build_filter(self, filters: dict[str, Any]):
        """Build Qdrant filter from dict."""
        from qdrant_client.models import FieldCondition, Filter, MatchValue

        conditions = []
        for key, value in filters.items():
            if value is not None:
                conditions.append(
                    FieldCondition(
                        key=key,
                        match=MatchValue(value=value),
                    )
                )

        return Filter(must=conditions) if conditions else None

    def _score_to_relevance(self, score: float) -> RelevanceLevel:
        """Convert similarity score to relevance level."""
        if score >= 0.85:
            return RelevanceLevel.HIGH
        elif score >= 0.70:
            return RelevanceLevel.MEDIUM
        elif score >= 0.50:
            return RelevanceLevel.LOW
        else:
            return RelevanceLevel.IRRELEVANT


# =============================================================================
# Factory Function
# =============================================================================


async def create_vector_store(
    config: VectorStoreConfig | None = None,
) -> VectorStore:
    """
    Create and initialize a vector store.

    Args:
        config: Optional configuration

    Returns:
        Initialized VectorStore instance
    """
    store = VectorStore(config)
    await store.initialize()
    return store
