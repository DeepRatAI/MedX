# =============================================================================
# MedeX - RAG System: Data Models
# =============================================================================
"""
Data models for the RAG (Retrieval-Augmented Generation) system.

This module defines:
- Document: Source document representation
- Chunk: Text fragment with metadata
- Embedding: Vector representation
- SearchResult: Retrieved chunk with score
- RAGContext: Context for LLM generation

Design principles:
- Immutable data structures where possible
- Rich metadata for traceability
- Medical-domain specific attributes
- Serialization support for caching
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4

logger = logging.getLogger(__name__)


# =============================================================================
# Enums
# =============================================================================


class DocumentType(str, Enum):
    """Types of medical documents."""

    GUIDELINE = "guideline"  # Clinical practice guidelines
    PROTOCOL = "protocol"  # Hospital protocols
    ARTICLE = "article"  # Journal articles
    TEXTBOOK = "textbook"  # Medical textbooks
    DRUG_INFO = "drug_info"  # Drug information sheets
    PATIENT_ED = "patient_education"  # Patient education materials
    CASE_STUDY = "case_study"  # Clinical case studies
    REFERENCE = "reference"  # Quick reference materials
    UNKNOWN = "unknown"


class ChunkType(str, Enum):
    """Types of text chunks."""

    PARAGRAPH = "paragraph"
    SECTION = "section"
    TABLE = "table"
    LIST = "list"
    CODE = "code"  # For dosage calculations, formulas
    DEFINITION = "definition"
    PROCEDURE = "procedure"
    HEADER = "header"


class RelevanceLevel(str, Enum):
    """Relevance classification for search results."""

    HIGH = "high"  # Directly answers the query
    MEDIUM = "medium"  # Related and useful
    LOW = "low"  # Tangentially related
    IRRELEVANT = "irrelevant"


# =============================================================================
# Document Model
# =============================================================================


@dataclass
class Document:
    """
    Represents a source document in the knowledge base.

    Attributes:
        id: Unique document identifier
        title: Document title
        content: Full text content
        doc_type: Type of medical document
        source: Origin of the document (journal, institution, etc.)
        metadata: Additional structured metadata
        created_at: Ingestion timestamp
        updated_at: Last update timestamp
    """

    title: str
    content: str
    doc_type: DocumentType = DocumentType.UNKNOWN
    source: str = ""
    id: str = field(default_factory=lambda: str(uuid4()))
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        """Compute content hash for deduplication."""
        self._content_hash = self._compute_hash()

    def _compute_hash(self) -> str:
        """Compute SHA-256 hash of content."""
        return hashlib.sha256(self.content.encode()).hexdigest()[:16]

    @property
    def content_hash(self) -> str:
        """Get content hash."""
        return self._content_hash

    @property
    def word_count(self) -> int:
        """Get approximate word count."""
        return len(self.content.split())

    @property
    def char_count(self) -> int:
        """Get character count."""
        return len(self.content)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "doc_type": self.doc_type.value,
            "source": self.source,
            "metadata": self.metadata,
            "content_hash": self.content_hash,
            "word_count": self.word_count,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Document:
        """Create from dictionary."""
        return cls(
            id=data.get("id", str(uuid4())),
            title=data["title"],
            content=data["content"],
            doc_type=DocumentType(data.get("doc_type", "unknown")),
            source=data.get("source", ""),
            metadata=data.get("metadata", {}),
            created_at=datetime.fromisoformat(data["created_at"])
            if "created_at" in data
            else datetime.now(),
            updated_at=datetime.fromisoformat(data["updated_at"])
            if data.get("updated_at")
            else None,
        )


# =============================================================================
# Chunk Model
# =============================================================================


@dataclass
class Chunk:
    """
    Represents a text fragment extracted from a document.

    Chunks are the atomic units for embedding and retrieval.
    Each chunk maintains a reference to its source document
    and includes rich metadata for context reconstruction.

    Attributes:
        id: Unique chunk identifier
        document_id: Parent document ID
        content: Chunk text content
        chunk_type: Type of chunk (paragraph, table, etc.)
        index: Position in document (0-indexed)
        metadata: Additional metadata (headers, page, etc.)
        embedding: Optional pre-computed embedding
    """

    content: str
    document_id: str
    chunk_type: ChunkType = ChunkType.PARAGRAPH
    index: int = 0
    id: str = field(default_factory=lambda: str(uuid4()))
    metadata: dict[str, Any] = field(default_factory=dict)
    embedding: list[float] | None = None

    # Contextual information
    section_title: str = ""
    page_number: int | None = None
    start_char: int = 0
    end_char: int = 0

    def __post_init__(self) -> None:
        """Validate and set derived fields."""
        if self.end_char == 0:
            self.end_char = self.start_char + len(self.content)

    @property
    def token_count_estimate(self) -> int:
        """Estimate token count (rough: 1 token ≈ 4 chars for Spanish)."""
        return len(self.content) // 4

    @property
    def has_embedding(self) -> bool:
        """Check if embedding is pre-computed."""
        return self.embedding is not None and len(self.embedding) > 0

    def to_dict(self, include_embedding: bool = False) -> dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "id": self.id,
            "document_id": self.document_id,
            "content": self.content,
            "chunk_type": self.chunk_type.value,
            "index": self.index,
            "metadata": self.metadata,
            "section_title": self.section_title,
            "page_number": self.page_number,
            "start_char": self.start_char,
            "end_char": self.end_char,
            "token_count_estimate": self.token_count_estimate,
        }
        if include_embedding and self.embedding:
            result["embedding"] = self.embedding
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Chunk:
        """Create from dictionary."""
        return cls(
            id=data.get("id", str(uuid4())),
            document_id=data["document_id"],
            content=data["content"],
            chunk_type=ChunkType(data.get("chunk_type", "paragraph")),
            index=data.get("index", 0),
            metadata=data.get("metadata", {}),
            embedding=data.get("embedding"),
            section_title=data.get("section_title", ""),
            page_number=data.get("page_number"),
            start_char=data.get("start_char", 0),
            end_char=data.get("end_char", 0),
        )


# =============================================================================
# Embedding Model
# =============================================================================


@dataclass
class Embedding:
    """
    Vector embedding representation.

    Attributes:
        vector: The embedding vector
        model: Model used to generate embedding
        dimensions: Vector dimensionality
        normalized: Whether vector is L2-normalized
    """

    vector: list[float]
    model: str = "default"
    dimensions: int = 0
    normalized: bool = True

    def __post_init__(self) -> None:
        """Set dimensions from vector."""
        if self.dimensions == 0:
            self.dimensions = len(self.vector)

    def to_list(self) -> list[float]:
        """Get vector as list."""
        return self.vector

    @property
    def magnitude(self) -> float:
        """Compute vector magnitude."""
        import math

        return math.sqrt(sum(x * x for x in self.vector))


# =============================================================================
# Search Result Model
# =============================================================================


@dataclass
class SearchResult:
    """
    Represents a search result from the vector store.

    Attributes:
        chunk: The retrieved chunk
        score: Similarity/relevance score (0-1)
        relevance: Classified relevance level
        rerank_score: Optional reranking score
        metadata: Additional result metadata
    """

    chunk: Chunk
    score: float
    relevance: RelevanceLevel = RelevanceLevel.MEDIUM
    rerank_score: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def final_score(self) -> float:
        """Get final score (rerank if available, else similarity)."""
        return self.rerank_score if self.rerank_score is not None else self.score

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "chunk": self.chunk.to_dict(),
            "score": self.score,
            "relevance": self.relevance.value,
            "rerank_score": self.rerank_score,
            "final_score": self.final_score,
            "metadata": self.metadata,
        }


# =============================================================================
# RAG Context Model
# =============================================================================


@dataclass
class RAGContext:
    """
    Context assembled for LLM generation.

    This is the final output of the RAG pipeline, containing
    all retrieved and processed information ready for the LLM.

    Attributes:
        query: Original user query
        results: Retrieved and ranked search results
        context_text: Formatted context string for LLM
        total_tokens: Estimated token count
        sources: Unique source documents
        metadata: Additional context metadata
    """

    query: str
    results: list[SearchResult]
    context_text: str = ""
    total_tokens: int = 0
    sources: list[dict[str, str]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self) -> None:
        """Generate context text if not provided."""
        if not self.context_text and self.results:
            self.context_text = self._format_context()
        if self.total_tokens == 0:
            self.total_tokens = len(self.context_text) // 4

    def _format_context(self) -> str:
        """Format results into context string."""
        if not self.results:
            return ""

        sections = []
        for i, result in enumerate(self.results, 1):
            chunk = result.chunk
            section = (
                f"[Fuente {i}] {chunk.section_title or 'Documento'}\n{chunk.content}"
            )
            sections.append(section)

        return "\n\n---\n\n".join(sections)

    @property
    def has_results(self) -> bool:
        """Check if any results were found."""
        return len(self.results) > 0

    @property
    def top_result(self) -> SearchResult | None:
        """Get highest scoring result."""
        return self.results[0] if self.results else None

    @property
    def high_relevance_count(self) -> int:
        """Count of high-relevance results."""
        return sum(1 for r in self.results if r.relevance == RelevanceLevel.HIGH)

    def get_unique_sources(self) -> list[dict[str, str]]:
        """Get unique source documents."""
        seen = set()
        sources = []
        for result in self.results:
            doc_id = result.chunk.document_id
            if doc_id not in seen:
                seen.add(doc_id)
                sources.append(
                    {
                        "document_id": doc_id,
                        "section": result.chunk.section_title,
                        "relevance": result.relevance.value,
                    }
                )
        return sources

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "query": self.query,
            "results": [r.to_dict() for r in self.results],
            "context_text": self.context_text,
            "total_tokens": self.total_tokens,
            "sources": self.get_unique_sources(),
            "metadata": self.metadata,
            "has_results": self.has_results,
            "high_relevance_count": self.high_relevance_count,
            "created_at": self.created_at.isoformat(),
        }

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


# =============================================================================
# Query Model
# =============================================================================


@dataclass
class RAGQuery:
    """
    Represents a RAG query with configuration.

    Attributes:
        text: Query text
        top_k: Number of results to retrieve
        min_score: Minimum similarity threshold
        filters: Metadata filters
        rerank: Whether to apply reranking
        expand_query: Whether to expand query
    """

    text: str
    top_k: int = 10
    min_score: float = 0.5
    filters: dict[str, Any] = field(default_factory=dict)
    rerank: bool = True
    expand_query: bool = False
    medical_context: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "text": self.text,
            "top_k": self.top_k,
            "min_score": self.min_score,
            "filters": self.filters,
            "rerank": self.rerank,
            "expand_query": self.expand_query,
            "medical_context": self.medical_context,
        }
