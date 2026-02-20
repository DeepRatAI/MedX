# =============================================================================
# MedeX - RAG System Package
# =============================================================================
"""
Retrieval-Augmented Generation (RAG) System for MedeX V2.

This package provides a complete RAG pipeline for medical knowledge retrieval:

Architecture:
- models.py: Data models (Document, Chunk, Embedding, SearchResult, RAGContext)
- chunker.py: Text chunking with medical-aware strategies
- embedder.py: Embedding generation (local + cloud options)
- vector_store.py: Qdrant-based vector storage and search
- reranker.py: Result reranking (BM25, cross-encoder, medical-aware)
- service.py: RAGService facade for unified access

Usage:
    from medex.rag import RAGService, Document, DocumentType

    # Initialize service
    service = RAGService()
    await service.initialize()

    # Ingest documents
    doc = Document(
        title="Guía de Neumonía",
        content="...",
        doc_type=DocumentType.GUIDELINE,
    )
    await service.ingest_document(doc)

    # Query
    context = await service.query("¿Tratamiento para neumonía adquirida?")
    print(context.context_text)

Features:
- Medical-domain optimized chunking
- Multilingual embedding support
- Hybrid retrieval (semantic + lexical)
- Evidence-aware reranking
- Token-aware context building
- $0 cost with local models
"""

from .chunker import (
    BaseChunker,
    ChunkerConfig,
    ChunkerType,
    MedicalChunker,
    SemanticChunker,
    create_chunker,
)
from .embedder import (
    BaseEmbedder,
    EmbedderConfig,
    EmbedderType,
    FreeEmbedder,
    OpenAIEmbedder,
    SentenceTransformerEmbedder,
    create_embedder,
)
from .models import (
    Chunk,
    ChunkType,
    Document,
    DocumentType,
    Embedding,
    RAGContext,
    RAGQuery,
    RelevanceLevel,
    SearchResult,
)
from .reranker import (
    BaseReranker,
    BM25Reranker,
    CrossEncoderReranker,
    EnsembleReranker,
    MedicalReranker,
    RerankerConfig,
    RerankerType,
    create_reranker,
)
from .service import (
    RAGService,
    RAGServiceConfig,
    get_rag_service,
    shutdown_rag_service,
)
from .vector_store import (
    VectorStore,
    VectorStoreConfig,
    create_vector_store,
)

__all__ = [
    # Models
    "Document",
    "DocumentType",
    "Chunk",
    "ChunkType",
    "Embedding",
    "SearchResult",
    "RelevanceLevel",
    "RAGContext",
    "RAGQuery",
    # Chunker
    "BaseChunker",
    "SemanticChunker",
    "MedicalChunker",
    "ChunkerConfig",
    "ChunkerType",
    "create_chunker",
    # Embedder
    "BaseEmbedder",
    "SentenceTransformerEmbedder",
    "OpenAIEmbedder",
    "FreeEmbedder",
    "EmbedderConfig",
    "EmbedderType",
    "create_embedder",
    # Vector Store
    "VectorStore",
    "VectorStoreConfig",
    "create_vector_store",
    # Reranker
    "BaseReranker",
    "CrossEncoderReranker",
    "BM25Reranker",
    "MedicalReranker",
    "EnsembleReranker",
    "RerankerConfig",
    "RerankerType",
    "create_reranker",
    # Service
    "RAGService",
    "RAGServiceConfig",
    "get_rag_service",
    "shutdown_rag_service",
]

__version__ = "2.0.0"
