# =============================================================================
# MedeX - RAG System: Service (Facade)
# =============================================================================
"""
RAG Service - Unified interface for the RAG pipeline.

This module provides:
- Complete RAG pipeline orchestration
- Document ingestion workflow
- Semantic search with reranking
- Context generation for LLM
- Metrics and monitoring

The RAGService is the primary interface for the rest of MedeX
to interact with the retrieval-augmented generation system.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any

from .chunker import BaseChunker, ChunkerConfig, MedicalChunker, create_chunker
from .embedder import BaseEmbedder, EmbedderConfig, create_embedder
from .models import Chunk, Document, DocumentType, RAGContext, RAGQuery, SearchResult
from .reranker import BaseReranker, RerankerConfig, create_reranker
from .vector_store import VectorStore, VectorStoreConfig, create_vector_store

if TYPE_CHECKING:
    from redis.asyncio import Redis

logger = logging.getLogger(__name__)


# =============================================================================
# Configuration
# =============================================================================


@dataclass
class RAGServiceConfig:
    """Configuration for the RAG service."""

    # Component configs
    chunker_config: ChunkerConfig = field(default_factory=ChunkerConfig)
    embedder_config: EmbedderConfig = field(default_factory=EmbedderConfig)
    vector_store_config: VectorStoreConfig = field(default_factory=VectorStoreConfig)
    reranker_config: RerankerConfig = field(default_factory=RerankerConfig)

    # Service settings
    default_top_k: int = 5
    default_min_score: float = 0.5
    enable_reranking: bool = True
    max_context_tokens: int = 4000

    # Context formatting
    include_sources: bool = True
    include_section_titles: bool = True


# =============================================================================
# RAG Service
# =============================================================================


class RAGService:
    """
    Unified service for Retrieval-Augmented Generation.

    The RAGService orchestrates the complete RAG pipeline:
    1. Document ingestion (chunking + embedding + indexing)
    2. Query processing (embedding + search + reranking)
    3. Context generation (formatting + truncation)

    Example:
        service = RAGService(config)
        await service.initialize()

        # Ingest documents
        await service.ingest_document(document)

        # Query
        context = await service.query("¿Cuál es el tratamiento para neumonía?")

        # Use context in LLM prompt
        response = await llm.generate(context.context_text)
    """

    def __init__(
        self,
        config: RAGServiceConfig | None = None,
        cache_client: Redis | None = None,
    ) -> None:
        """
        Initialize RAG service.

        Args:
            config: Service configuration
            cache_client: Optional Redis client for caching
        """
        self.config = config or RAGServiceConfig()
        self._cache = cache_client

        # Components (initialized lazily)
        self._chunker: BaseChunker | None = None
        self._embedder: BaseEmbedder | None = None
        self._vector_store: VectorStore | None = None
        self._reranker: BaseReranker | None = None

        # State
        self._initialized = False

        # Metrics
        self._metrics = {
            "documents_ingested": 0,
            "chunks_indexed": 0,
            "queries_processed": 0,
            "avg_query_time_ms": 0.0,
        }

        logger.info("RAGService created")

    async def initialize(self) -> None:
        """
        Initialize all RAG components.

        This must be called before using the service.
        """
        if self._initialized:
            return

        logger.info("Initializing RAG service...")

        # Initialize components
        self._chunker = create_chunker("medical", self.config.chunker_config)

        self._embedder = create_embedder("free", self.config.embedder_config)
        if self._cache:
            self._embedder.set_cache(self._cache)

        self._vector_store = await create_vector_store(self.config.vector_store_config)

        self._reranker = create_reranker("medical", self.config.reranker_config)

        self._initialized = True
        logger.info("RAG service initialized successfully")

    async def shutdown(self) -> None:
        """Shutdown and cleanup resources."""
        if self._vector_store:
            await self._vector_store.close()

        self._initialized = False
        logger.info("RAG service shutdown complete")

    def _ensure_initialized(self) -> None:
        """Ensure service is initialized."""
        if not self._initialized:
            raise RuntimeError("RAGService not initialized. Call initialize() first.")

    # =========================================================================
    # Document Ingestion
    # =========================================================================

    async def ingest_document(
        self,
        document: Document,
        chunk_overlap: int | None = None,
    ) -> int:
        """
        Ingest a document into the knowledge base.

        Pipeline:
        1. Chunk document into fragments
        2. Generate embeddings for chunks
        3. Store chunks in vector database

        Args:
            document: Document to ingest
            chunk_overlap: Optional override for chunk overlap

        Returns:
            Number of chunks indexed
        """
        self._ensure_initialized()

        logger.info(f"Ingesting document: {document.title} ({document.id})")

        # Override chunk overlap if specified
        if chunk_overlap is not None:
            self._chunker.config.chunk_overlap = chunk_overlap

        # Step 1: Chunk
        chunks = self._chunker.chunk(document)
        logger.debug(f"Created {len(chunks)} chunks")

        # Step 2: Embed
        chunks = await self._embedder.embed_chunks(chunks)
        logger.debug(f"Generated embeddings for {len(chunks)} chunks")

        # Step 3: Index
        await self._vector_store.upsert_chunks(chunks)
        logger.debug(f"Indexed {len(chunks)} chunks")

        # Update metrics
        self._metrics["documents_ingested"] += 1
        self._metrics["chunks_indexed"] += len(chunks)

        return len(chunks)

    async def ingest_documents(
        self,
        documents: list[Document],
        batch_size: int = 10,
    ) -> int:
        """
        Ingest multiple documents.

        Args:
            documents: Documents to ingest
            batch_size: Documents to process before indexing

        Returns:
            Total chunks indexed
        """
        self._ensure_initialized()

        total_chunks = 0

        for doc in documents:
            try:
                chunks = await self.ingest_document(doc)
                total_chunks += chunks
            except Exception as e:
                logger.error(f"Failed to ingest document {doc.id}: {e}")

        return total_chunks

    async def delete_document(self, document_id: str) -> int:
        """
        Delete a document and its chunks.

        Args:
            document_id: Document ID to delete

        Returns:
            Number of chunks deleted
        """
        self._ensure_initialized()

        deleted = await self._vector_store.delete_by_document(document_id)
        logger.info(f"Deleted {deleted} chunks for document {document_id}")

        return deleted

    # =========================================================================
    # Query and Retrieval
    # =========================================================================

    async def query(
        self,
        query: str | RAGQuery,
        top_k: int | None = None,
        min_score: float | None = None,
        rerank: bool | None = None,
        filters: dict[str, Any] | None = None,
    ) -> RAGContext:
        """
        Query the knowledge base and build context.

        Pipeline:
        1. Embed query
        2. Search vector store
        3. Rerank results (optional)
        4. Build context for LLM

        Args:
            query: Query text or RAGQuery object
            top_k: Number of results to return
            min_score: Minimum similarity threshold
            rerank: Whether to apply reranking
            filters: Metadata filters

        Returns:
            RAGContext with results and formatted context
        """
        self._ensure_initialized()

        start_time = datetime.now()

        # Normalize query
        if isinstance(query, str):
            query = RAGQuery(
                text=query,
                top_k=top_k or self.config.default_top_k,
                min_score=min_score or self.config.default_min_score,
                rerank=rerank if rerank is not None else self.config.enable_reranking,
                filters=filters or {},
            )

        logger.debug(f"Processing query: {query.text[:100]}...")

        # Step 1: Embed query
        query_embedding = await self._embedder.embed_text(query.text)

        # Step 2: Search
        results = await self._vector_store.search(
            query_embedding=query_embedding.vector,
            top_k=query.top_k * 2
            if query.rerank
            else query.top_k,  # Over-retrieve for reranking
            score_threshold=query.min_score,
            filters=query.filters,
        )

        # Step 3: Rerank
        if query.rerank and results:
            results = await self._reranker.rerank(
                query=query.text,
                results=results,
                top_k=query.top_k,
            )

        # Step 4: Build context
        context = self._build_context(query.text, results)

        # Update metrics
        elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000
        self._metrics["queries_processed"] += 1
        self._metrics["avg_query_time_ms"] = (
            self._metrics["avg_query_time_ms"]
            * (self._metrics["queries_processed"] - 1)
            + elapsed_ms
        ) / self._metrics["queries_processed"]

        logger.info(
            f"Query completed in {elapsed_ms:.1f}ms with {len(results)} results"
        )

        return context

    async def search(
        self,
        query: str,
        top_k: int = 10,
        filters: dict[str, Any] | None = None,
    ) -> list[SearchResult]:
        """
        Simple search without context building.

        Args:
            query: Query text
            top_k: Number of results
            filters: Metadata filters

        Returns:
            List of SearchResult objects
        """
        self._ensure_initialized()

        # Embed query
        query_embedding = await self._embedder.embed_text(query)

        # Search
        results = await self._vector_store.search(
            query_embedding=query_embedding.vector,
            top_k=top_k,
            filters=filters,
        )

        return results

    # =========================================================================
    # Context Building
    # =========================================================================

    def _build_context(
        self,
        query: str,
        results: list[SearchResult],
    ) -> RAGContext:
        """
        Build RAGContext from search results.

        Args:
            query: Original query
            results: Search results

        Returns:
            Formatted RAGContext
        """
        if not results:
            return RAGContext(
                query=query,
                results=[],
                context_text="No se encontró información relevante.",
            )

        # Build context text with token limit
        context_parts = []
        total_tokens = 0
        included_results = []

        for i, result in enumerate(results, 1):
            chunk = result.chunk

            # Format chunk
            if self.config.include_section_titles and chunk.section_title:
                part = f"**[Fuente {i}: {chunk.section_title}]**\n{chunk.content}"
            else:
                part = f"**[Fuente {i}]**\n{chunk.content}"

            # Estimate tokens
            part_tokens = len(part) // 4

            if total_tokens + part_tokens > self.config.max_context_tokens:
                break

            context_parts.append(part)
            included_results.append(result)
            total_tokens += part_tokens

        context_text = "\n\n---\n\n".join(context_parts)

        # Build sources list
        sources = []
        if self.config.include_sources:
            for result in included_results:
                sources.append(
                    {
                        "document_id": result.chunk.document_id,
                        "section": result.chunk.section_title,
                        "relevance": result.relevance.value,
                        "score": round(result.final_score, 3),
                    }
                )

        return RAGContext(
            query=query,
            results=included_results,
            context_text=context_text,
            total_tokens=total_tokens,
            sources=sources,
            metadata={
                "original_result_count": len(results),
                "included_result_count": len(included_results),
                "truncated": len(included_results) < len(results),
            },
        )

    # =========================================================================
    # Utility Methods
    # =========================================================================

    async def get_collection_info(self) -> dict[str, Any]:
        """Get vector store collection information."""
        self._ensure_initialized()
        return await self._vector_store.get_collection_info()

    def get_metrics(self) -> dict[str, Any]:
        """Get service metrics."""
        return self._metrics.copy()

    async def health_check(self) -> dict[str, Any]:
        """Check service health."""
        try:
            self._ensure_initialized()
            info = await self._vector_store.get_collection_info()

            return {
                "status": "healthy",
                "initialized": self._initialized,
                "vector_store": info.get("status", "unknown"),
                "indexed_chunks": info.get("points_count", 0),
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
            }


# =============================================================================
# Factory Function
# =============================================================================

_rag_service: RAGService | None = None


async def get_rag_service(
    config: RAGServiceConfig | None = None,
    cache_client: Redis | None = None,
) -> RAGService:
    """
    Get or create the global RAGService instance.

    Args:
        config: Optional configuration
        cache_client: Optional Redis client

    Returns:
        Initialized RAGService instance
    """
    global _rag_service

    if _rag_service is None:
        _rag_service = RAGService(config, cache_client)
        await _rag_service.initialize()

    return _rag_service


async def shutdown_rag_service() -> None:
    """Shutdown the global RAGService instance."""
    global _rag_service

    if _rag_service:
        await _rag_service.shutdown()
        _rag_service = None
