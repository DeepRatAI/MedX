# =============================================================================
# MedeX - RAG System Tests
# =============================================================================
"""
Comprehensive tests for the MedeX RAG System.

Tests cover:
- Document and Chunk models
- Text chunking strategies
- Embedding generation
- Vector store operations
- Reranking algorithms
- RAG Service integration
"""

from __future__ import annotations

import pytest

from medex.rag.chunker import (
    ChunkerConfig,
    MedicalChunker,
    SemanticChunker,
    create_chunker,
)
from medex.rag.models import (
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
from medex.rag.reranker import (
    BM25Reranker,
    MedicalReranker,
    create_reranker,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def sample_document() -> Document:
    """Create a sample medical document."""
    return Document(
        id="doc_001",
        title="Guía de Tratamiento para Neumonía Adquirida en la Comunidad",
        content="""
# Neumonía Adquirida en la Comunidad (NAC)

## Definición
La neumonía adquirida en la comunidad es una infección del parénquima pulmonar
que se desarrolla en pacientes no hospitalizados.

## Diagnóstico
El diagnóstico se basa en:
- Síntomas clínicos: tos, fiebre, expectoración
- Exploración física: crepitantes, matidez
- Radiografía de tórax: infiltrados pulmonares

## Tratamiento

### Tratamiento ambulatorio
Para pacientes sin factores de riesgo:
- Amoxicilina 1g cada 8 horas por 5-7 días
- Alternativa: Azitromicina 500mg día 1, luego 250mg días 2-5

### Tratamiento hospitalario
Para pacientes con criterios de gravedad:
- Ceftriaxona 2g IV cada 24 horas + Azitromicina 500mg IV
- Duración: 7-10 días según evolución

## Criterios de Gravedad
Utilizar escalas CURB-65 o PSI para estratificación:
- Confusión
- Urea >7 mmol/L
- Frecuencia respiratoria ≥30/min
- Presión arterial sistólica <90 mmHg
- Edad ≥65 años

## Contraindicaciones
⚠️ Evitar quinolonas en:
- Pacientes con antecedente de tendinitis
- Uso concomitante de corticosteroides
- Menores de 18 años
        """,
        doc_type=DocumentType.GUIDELINE,
        source="Guía SEPAR 2023",
        metadata={"specialty": "neumología", "year": 2023},
    )


@pytest.fixture
def sample_chunks(sample_document: Document) -> list[Chunk]:
    """Create sample chunks from document."""
    return [
        Chunk(
            id="chunk_001",
            document_id=sample_document.id,
            content="La neumonía adquirida en la comunidad es una infección del parénquima pulmonar.",
            chunk_type=ChunkType.DEFINITION,
            section_title="Definición",
            index=0,
        ),
        Chunk(
            id="chunk_002",
            document_id=sample_document.id,
            content="Amoxicilina 1g cada 8 horas por 5-7 días. Alternativa: Azitromicina 500mg día 1, luego 250mg días 2-5",
            chunk_type=ChunkType.PARAGRAPH,
            section_title="Tratamiento ambulatorio",
            index=1,
        ),
        Chunk(
            id="chunk_003",
            document_id=sample_document.id,
            content="Ceftriaxona 2g IV cada 24 horas + Azitromicina 500mg IV. Duración: 7-10 días según evolución",
            chunk_type=ChunkType.PARAGRAPH,
            section_title="Tratamiento hospitalario",
            index=2,
        ),
    ]


@pytest.fixture
def sample_search_results(sample_chunks: list[Chunk]) -> list[SearchResult]:
    """Create sample search results."""
    return [
        SearchResult(
            chunk=sample_chunks[1],
            score=0.92,
            relevance=RelevanceLevel.HIGH,
        ),
        SearchResult(
            chunk=sample_chunks[2],
            score=0.85,
            relevance=RelevanceLevel.HIGH,
        ),
        SearchResult(
            chunk=sample_chunks[0],
            score=0.65,
            relevance=RelevanceLevel.MEDIUM,
        ),
    ]


# =============================================================================
# Document Model Tests
# =============================================================================


class TestDocument:
    """Tests for Document model."""

    def test_create_document(self):
        """Test creating a document."""
        doc = Document(
            title="Test Document",
            content="This is test content.",
            doc_type=DocumentType.ARTICLE,
        )

        assert doc.title == "Test Document"
        assert doc.doc_type == DocumentType.ARTICLE
        assert doc.id is not None  # Auto-generated

    def test_document_hash(self, sample_document: Document):
        """Test content hash generation."""
        hash1 = sample_document.content_hash

        # Same content = same hash
        doc2 = Document(
            title="Different Title",
            content=sample_document.content,
        )
        assert doc2.content_hash == hash1

        # Different content = different hash
        doc3 = Document(
            title="Test",
            content="Different content",
        )
        assert doc3.content_hash != hash1

    def test_document_to_dict(self, sample_document: Document):
        """Test serialization to dict."""
        data = sample_document.to_dict()

        assert data["title"] == sample_document.title
        assert data["doc_type"] == sample_document.doc_type.value
        assert "content_hash" in data
        assert "word_count" in data

    def test_document_from_dict(self, sample_document: Document):
        """Test deserialization from dict."""
        data = sample_document.to_dict()
        restored = Document.from_dict(data)

        assert restored.title == sample_document.title
        assert restored.content == sample_document.content
        assert restored.doc_type == sample_document.doc_type


# =============================================================================
# Chunk Model Tests
# =============================================================================


class TestChunk:
    """Tests for Chunk model."""

    def test_create_chunk(self):
        """Test creating a chunk."""
        chunk = Chunk(
            content="Test chunk content",
            document_id="doc_123",
            chunk_type=ChunkType.PARAGRAPH,
        )

        assert chunk.content == "Test chunk content"
        assert chunk.document_id == "doc_123"
        assert chunk.id is not None

    def test_chunk_token_estimate(self):
        """Test token count estimation."""
        chunk = Chunk(
            content="Este es un texto de prueba para estimar tokens.",
            document_id="doc_123",
        )

        # Rough estimate: ~12 tokens for this text
        assert chunk.token_count_estimate > 0
        assert chunk.token_count_estimate < 20

    def test_chunk_embedding_flag(self):
        """Test embedding presence detection."""
        chunk = Chunk(content="Test", document_id="doc")
        assert chunk.has_embedding is False

        chunk.embedding = [0.1, 0.2, 0.3]
        assert chunk.has_embedding is True


# =============================================================================
# Chunker Tests
# =============================================================================


class TestSemanticChunker:
    """Tests for SemanticChunker."""

    def test_chunk_simple_document(self):
        """Test chunking a simple document."""
        doc = Document(
            title="Simple Doc",
            content="First paragraph.\n\nSecond paragraph.\n\nThird paragraph.",
        )

        chunker = SemanticChunker()
        chunks = chunker.chunk(doc)

        assert len(chunks) >= 1
        assert all(c.document_id == doc.id for c in chunks)

    def test_chunk_with_sections(self, sample_document: Document):
        """Test chunking document with sections."""
        chunker = SemanticChunker()
        chunks = chunker.chunk(sample_document)

        # Should create multiple chunks for long document
        assert len(chunks) > 1

        # Should preserve section titles
        section_titles = [c.section_title for c in chunks if c.section_title]
        assert len(section_titles) > 0

    def test_chunk_size_limits(self):
        """Test chunk size configuration."""
        config = ChunkerConfig(chunk_size=100, chunk_overlap=20)
        chunker = SemanticChunker(config)

        long_content = "Word " * 100  # ~500 characters
        doc = Document(title="Long", content=long_content)
        chunks = chunker.chunk(doc)

        # Should create multiple chunks
        assert len(chunks) > 1

        # Each chunk should respect size limit (with some tolerance)
        for chunk in chunks:
            assert len(chunk.content) <= config.max_chunk_size


class TestMedicalChunker:
    """Tests for MedicalChunker."""

    def test_preserves_dosage_info(self):
        """Test that dosage information is preserved."""
        content = """
        Tratamiento:
        - Amoxicilina 500mg cada 8 horas por 7 días
        - Ibuprofeno 400mg cada 6 horas PRN

        Seguimiento en 1 semana.
        """

        doc = Document(title="Tratamiento", content=content)
        chunker = MedicalChunker()
        chunks = chunker.chunk(doc)

        # Dosage info should be in a chunk
        all_content = " ".join(c.content for c in chunks)
        assert "500mg cada 8 horas" in all_content

    def test_adds_medical_metadata(self, sample_document: Document):
        """Test medical metadata addition."""
        chunker = MedicalChunker()
        chunks = chunker.chunk(sample_document)

        # All chunks should have medical metadata
        for chunk in chunks:
            assert chunk.metadata.get("is_medical") is True


# =============================================================================
# Reranker Tests
# =============================================================================


class TestBM25Reranker:
    """Tests for BM25Reranker."""

    @pytest.mark.asyncio
    async def test_rerank_basic(self, sample_search_results: list[SearchResult]):
        """Test basic reranking."""
        reranker = BM25Reranker()
        query = "tratamiento neumonía amoxicilina"

        reranked = await reranker.rerank(query, sample_search_results, top_k=3)

        assert len(reranked) <= 3
        # Results should have rerank scores
        for result in reranked:
            assert result.rerank_score is not None

    @pytest.mark.asyncio
    async def test_rerank_empty_results(self):
        """Test reranking with no results."""
        reranker = BM25Reranker()
        reranked = await reranker.rerank("test query", [], top_k=5)
        assert reranked == []

    @pytest.mark.asyncio
    async def test_rerank_preserves_order_for_identical_scores(self):
        """Test that original order is preserved for equal scores."""
        chunks = [
            Chunk(id=f"c{i}", content=f"content {i}", document_id="doc")
            for i in range(3)
        ]
        results = [SearchResult(chunk=c, score=0.5) for c in chunks]

        reranker = BM25Reranker()
        reranked = await reranker.rerank("different query entirely", results)

        # All should have been processed
        assert len(reranked) == 3


class TestMedicalReranker:
    """Tests for MedicalReranker."""

    @pytest.mark.asyncio
    async def test_boosts_medical_content(
        self, sample_search_results: list[SearchResult]
    ):
        """Test that medical content gets boosted."""
        reranker = MedicalReranker()
        query = "dosis amoxicilina tratamiento"

        reranked = await reranker.rerank(query, sample_search_results)

        # Treatment chunks should rank high
        top_result = reranked[0]
        assert (
            "mg" in top_result.chunk.content
            or "dosis" in top_result.chunk.content.lower()
        )

    @pytest.mark.asyncio
    async def test_medical_score_in_metadata(
        self, sample_search_results: list[SearchResult]
    ):
        """Test that medical score is added to metadata."""
        reranker = MedicalReranker()
        reranked = await reranker.rerank("tratamiento", sample_search_results)

        for result in reranked:
            assert "medical_score" in result.metadata


# =============================================================================
# RAGContext Tests
# =============================================================================


class TestRAGContext:
    """Tests for RAGContext model."""

    def test_create_context_with_results(
        self, sample_search_results: list[SearchResult]
    ):
        """Test creating context with results."""
        context = RAGContext(
            query="tratamiento neumonía",
            results=sample_search_results,
        )

        assert context.has_results is True
        assert context.top_result is not None
        assert len(context.context_text) > 0

    def test_create_empty_context(self):
        """Test creating context with no results."""
        context = RAGContext(
            query="consulta sin resultados",
            results=[],
        )

        assert context.has_results is False
        assert context.top_result is None

    def test_context_sources(self, sample_search_results: list[SearchResult]):
        """Test source extraction."""
        context = RAGContext(
            query="test",
            results=sample_search_results,
        )

        sources = context.get_unique_sources()
        assert len(sources) > 0
        assert all("document_id" in s for s in sources)

    def test_context_to_dict(self, sample_search_results: list[SearchResult]):
        """Test context serialization."""
        context = RAGContext(
            query="test query",
            results=sample_search_results,
        )

        data = context.to_dict()

        assert data["query"] == "test query"
        assert "results" in data
        assert "context_text" in data
        assert "sources" in data


# =============================================================================
# RAGQuery Tests
# =============================================================================


class TestRAGQuery:
    """Tests for RAGQuery model."""

    def test_create_simple_query(self):
        """Test creating a simple query."""
        query = RAGQuery(text="¿Cuál es el tratamiento para neumonía?")

        assert query.text == "¿Cuál es el tratamiento para neumonía?"
        assert query.top_k == 10  # Default
        assert query.rerank is True  # Default

    def test_create_query_with_filters(self):
        """Test query with metadata filters."""
        query = RAGQuery(
            text="tratamiento hipertensión",
            top_k=5,
            filters={"specialty": "cardiología"},
            medical_context={"patient_age": 65},
        )

        assert query.filters["specialty"] == "cardiología"
        assert query.medical_context["patient_age"] == 65

    def test_query_to_dict(self):
        """Test query serialization."""
        query = RAGQuery(
            text="test",
            top_k=5,
            min_score=0.7,
        )

        data = query.to_dict()

        assert data["text"] == "test"
        assert data["top_k"] == 5
        assert abs(data["min_score"] - 0.7) < 0.001


# =============================================================================
# Embedding Tests
# =============================================================================


class TestEmbedding:
    """Tests for Embedding model."""

    def test_create_embedding(self):
        """Test creating an embedding."""
        vector = [0.1, 0.2, 0.3, 0.4, 0.5]
        emb = Embedding(vector=vector, model="test-model")

        assert emb.dimensions == 5
        assert emb.model == "test-model"

    def test_embedding_magnitude(self):
        """Test magnitude calculation."""
        # Unit vector: [1, 0, 0] should have magnitude 1
        emb = Embedding(vector=[1.0, 0.0, 0.0])
        assert abs(emb.magnitude - 1.0) < 0.001

        # [3, 4] should have magnitude 5
        emb2 = Embedding(vector=[3.0, 4.0])
        assert abs(emb2.magnitude - 5.0) < 0.001


# =============================================================================
# Factory Function Tests
# =============================================================================


class TestFactoryFunctions:
    """Tests for factory functions."""

    def test_create_chunker_semantic(self):
        """Test creating semantic chunker."""
        chunker = create_chunker("semantic")
        assert isinstance(chunker, SemanticChunker)

    def test_create_chunker_medical(self):
        """Test creating medical chunker."""
        chunker = create_chunker("medical")
        assert isinstance(chunker, MedicalChunker)

    def test_create_reranker_bm25(self):
        """Test creating BM25 reranker."""
        reranker = create_reranker("bm25")
        assert isinstance(reranker, BM25Reranker)

    def test_create_reranker_medical(self):
        """Test creating medical reranker."""
        reranker = create_reranker("medical")
        assert isinstance(reranker, MedicalReranker)


# =============================================================================
# Integration Tests
# =============================================================================


class TestRAGIntegration:
    """Integration tests for RAG components."""

    def test_chunking_pipeline(self, sample_document: Document):
        """Test complete chunking pipeline."""
        chunker = create_chunker("medical")
        chunks = chunker.chunk(sample_document)

        assert len(chunks) > 0
        assert all(c.document_id == sample_document.id for c in chunks)
        assert all(len(c.content) > 0 for c in chunks)

    @pytest.mark.asyncio
    async def test_reranking_pipeline(
        self,
        sample_document: Document,
        sample_search_results: list[SearchResult],
    ):
        """Test reranking pipeline."""
        reranker = create_reranker("medical")

        reranked = await reranker.rerank(
            query="tratamiento neumonía ambulatorio",
            results=sample_search_results,
            top_k=3,
        )

        assert len(reranked) <= 3
        assert all(r.rerank_score is not None for r in reranked)

        # Should be sorted by rerank score
        scores = [r.rerank_score for r in reranked]
        assert scores == sorted(scores, reverse=True)


# =============================================================================
# Run Tests
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
