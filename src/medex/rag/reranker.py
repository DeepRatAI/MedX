# =============================================================================
# MedeX - RAG System: Reranker
# =============================================================================
"""
Result reranking for improved retrieval quality.

This module provides:
- Cross-encoder reranking
- BM25 hybrid scoring
- Medical-specific relevance boosting
- Query-document similarity refinement

Reranking strategies:
1. Cross-encoder: Uses encoder model for query-document pairs
2. BM25 hybrid: Combines semantic + lexical scores
3. Medical boost: Boosts results with medical relevance signals

Design:
- Two-stage retrieval (fast retrieval → accurate reranking)
- Configurable fusion weights
- Medical domain awareness
- Efficient batch processing
"""

from __future__ import annotations

import asyncio
import logging
import math
import re
from abc import ABC, abstractmethod
from collections import Counter
from dataclasses import dataclass

from .models import RelevanceLevel, SearchResult

logger = logging.getLogger(__name__)


# =============================================================================
# Configuration
# =============================================================================


@dataclass
class RerankerConfig:
    """Configuration for reranking."""

    # Model settings
    model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    max_length: int = 512

    # Scoring
    top_k: int = 10
    min_score: float = 0.3

    # Fusion weights (must sum to 1.0)
    semantic_weight: float = 0.6
    lexical_weight: float = 0.2
    medical_weight: float = 0.2

    # Medical boosting
    medical_boost_enabled: bool = True
    medical_boost_factor: float = 1.2


# =============================================================================
# Base Reranker
# =============================================================================


class BaseReranker(ABC):
    """Abstract base class for rerankers."""

    def __init__(self, config: RerankerConfig | None = None) -> None:
        """Initialize reranker."""
        self.config = config or RerankerConfig()

    @abstractmethod
    async def rerank(
        self,
        query: str,
        results: list[SearchResult],
        top_k: int | None = None,
    ) -> list[SearchResult]:
        """
        Rerank search results based on query.

        Args:
            query: Original query text
            results: Initial search results
            top_k: Number of results to return

        Returns:
            Reranked results with updated scores
        """
        pass


# =============================================================================
# Cross-Encoder Reranker
# =============================================================================


class CrossEncoderReranker(BaseReranker):
    """
    Reranker using cross-encoder models.

    Cross-encoders jointly encode query and document,
    providing more accurate relevance scores than bi-encoders.
    """

    def __init__(self, config: RerankerConfig | None = None) -> None:
        """Initialize cross-encoder reranker."""
        super().__init__(config)
        self._model = None
        self._lock = asyncio.Lock()

    async def _get_model(self):
        """Lazy-load cross-encoder model."""
        if self._model is None:
            async with self._lock:
                if self._model is None:
                    from sentence_transformers import CrossEncoder

                    self._model = CrossEncoder(self.config.model_name)
                    logger.info(f"Loaded cross-encoder: {self.config.model_name}")
        return self._model

    async def rerank(
        self,
        query: str,
        results: list[SearchResult],
        top_k: int | None = None,
    ) -> list[SearchResult]:
        """Rerank using cross-encoder scores."""
        if not results:
            return []

        top_k = top_k or self.config.top_k

        # Prepare query-document pairs
        pairs = [(query, r.chunk.content) for r in results]

        # Get cross-encoder scores
        model = await self._get_model()
        loop = asyncio.get_event_loop()

        scores = await loop.run_in_executor(None, lambda: model.predict(pairs))

        # Normalize scores to [0, 1]
        min_score = min(scores)
        max_score = max(scores)
        score_range = max_score - min_score if max_score > min_score else 1

        normalized_scores = [(s - min_score) / score_range for s in scores]

        # Update results with rerank scores
        for result, rerank_score in zip(results, normalized_scores, strict=False):
            result.rerank_score = float(rerank_score)
            result.relevance = self._score_to_relevance(rerank_score)

        # Sort by rerank score
        results.sort(key=lambda r: r.rerank_score or 0, reverse=True)

        return results[:top_k]

    def _score_to_relevance(self, score: float) -> RelevanceLevel:
        """Map score to relevance level."""
        if score >= 0.8:
            return RelevanceLevel.HIGH
        elif score >= 0.5:
            return RelevanceLevel.MEDIUM
        elif score >= 0.3:
            return RelevanceLevel.LOW
        else:
            return RelevanceLevel.IRRELEVANT


# =============================================================================
# BM25 Reranker (Hybrid)
# =============================================================================


class BM25Reranker(BaseReranker):
    """
    Hybrid reranker combining semantic and BM25 lexical scores.

    BM25 is effective for keyword matching while semantic scores
    handle paraphrase and concept matching. Fusion provides best of both.
    """

    # BM25 parameters
    K1 = 1.5
    B = 0.75

    def __init__(self, config: RerankerConfig | None = None) -> None:
        """Initialize BM25 hybrid reranker."""
        super().__init__(config)

        # Medical term boosting
        self._medical_terms: set[str] = set()
        self._load_medical_terms()

    def _load_medical_terms(self) -> None:
        """Load medical terminology for boosting."""
        # Common medical terms that indicate relevance
        self._medical_terms = {
            # Symptoms
            "dolor",
            "fiebre",
            "tos",
            "disnea",
            "fatiga",
            "náusea",
            "vómito",
            "diarrea",
            "cefalea",
            "mareo",
            "edema",
            # Diagnósticos
            "diabetes",
            "hipertensión",
            "anemia",
            "neumonía",
            "infección",
            "insuficiencia",
            "síndrome",
            "enfermedad",
            "trastorno",
            # Tratamientos
            "tratamiento",
            "dosis",
            "medicamento",
            "fármaco",
            "terapia",
            "antibiótico",
            "analgésico",
            "antiinflamatorio",
            # Procedimientos
            "cirugía",
            "biopsia",
            "endoscopia",
            "radiografía",
            "ecografía",
            # Anatomía
            "hígado",
            "riñón",
            "corazón",
            "pulmón",
            "cerebro",
            "estómago",
        }

    async def rerank(
        self,
        query: str,
        results: list[SearchResult],
        top_k: int | None = None,
    ) -> list[SearchResult]:
        """Rerank using hybrid BM25 + semantic scores."""
        if not results:
            return []

        top_k = top_k or self.config.top_k

        # Calculate BM25 scores
        query_terms = self._tokenize(query)
        documents = [r.chunk.content for r in results]

        bm25_scores = self._calculate_bm25(query_terms, documents)

        # Calculate medical boost scores
        medical_scores = [self._calculate_medical_score(doc) for doc in documents]

        # Fusion scoring
        for i, result in enumerate(results):
            semantic_score = result.score
            lexical_score = bm25_scores[i]
            medical_score = medical_scores[i]

            # Weighted fusion
            fusion_score = (
                self.config.semantic_weight * semantic_score
                + self.config.lexical_weight * lexical_score
                + self.config.medical_weight * medical_score
            )

            result.rerank_score = fusion_score
            result.metadata["bm25_score"] = lexical_score
            result.metadata["medical_score"] = medical_score
            result.relevance = self._score_to_relevance(fusion_score)

        # Sort by fusion score
        results.sort(key=lambda r: r.rerank_score or 0, reverse=True)

        return results[:top_k]

    def _tokenize(self, text: str) -> list[str]:
        """Tokenize text for BM25."""
        # Simple whitespace tokenization with lowercasing
        text = text.lower()
        # Remove punctuation
        text = re.sub(r"[^\w\s]", " ", text)
        tokens = text.split()
        # Remove stopwords (basic Spanish)
        stopwords = {
            "de",
            "la",
            "el",
            "en",
            "y",
            "a",
            "que",
            "es",
            "un",
            "una",
            "los",
            "las",
            "por",
            "con",
            "para",
        }
        return [t for t in tokens if t not in stopwords and len(t) > 2]

    def _calculate_bm25(
        self, query_terms: list[str], documents: list[str]
    ) -> list[float]:
        """Calculate BM25 scores for documents."""
        if not documents:
            return []

        # Document lengths and average
        doc_tokens = [self._tokenize(doc) for doc in documents]
        doc_lengths = [len(tokens) for tokens in doc_tokens]
        avg_length = sum(doc_lengths) / len(doc_lengths) if doc_lengths else 1

        # Document frequencies
        df: dict[str, int] = Counter()
        for tokens in doc_tokens:
            for term in set(tokens):
                df[term] += 1

        n_docs = len(documents)
        scores = []

        for i, tokens in enumerate(doc_tokens):
            score = 0.0
            term_freqs = Counter(tokens)

            for term in query_terms:
                if term in term_freqs:
                    tf = term_freqs[term]
                    doc_freq = df.get(term, 0)

                    # IDF component
                    idf = math.log((n_docs - doc_freq + 0.5) / (doc_freq + 0.5) + 1)

                    # TF component with length normalization
                    tf_norm = (tf * (self.K1 + 1)) / (
                        tf
                        + self.K1 * (1 - self.B + self.B * doc_lengths[i] / avg_length)
                    )

                    score += idf * tf_norm

            scores.append(score)

        # Normalize to [0, 1]
        max_score = max(scores) if scores else 1
        if max_score > 0:
            scores = [s / max_score for s in scores]

        return scores

    def _calculate_medical_score(self, document: str) -> float:
        """Calculate medical relevance score based on term presence."""
        if not self.config.medical_boost_enabled:
            return 0.5  # Neutral

        tokens = set(self._tokenize(document))
        medical_matches = len(tokens.intersection(self._medical_terms))

        # Normalize: assume 5+ medical terms is max relevance
        return min(medical_matches / 5.0, 1.0)

    def _score_to_relevance(self, score: float) -> RelevanceLevel:
        """Map fusion score to relevance level."""
        if score >= 0.7:
            return RelevanceLevel.HIGH
        elif score >= 0.5:
            return RelevanceLevel.MEDIUM
        elif score >= 0.3:
            return RelevanceLevel.LOW
        else:
            return RelevanceLevel.IRRELEVANT


# =============================================================================
# Medical-Aware Reranker
# =============================================================================


class MedicalReranker(BM25Reranker):
    """
    Specialized reranker for medical content.

    Extends BM25Reranker with:
    - Medical entity recognition boost
    - Clinical guideline priority
    - Evidence level scoring
    """

    # Patterns for medical content identification
    EVIDENCE_PATTERNS = [
        (
            r"\b(?:nivel|grado)\s*(?:de\s+)?(?:evidencia|recomendación)\s*[A-D1-4]\b",
            0.2,
        ),
        (r"\b(?:ensayo|estudio)\s+(?:clínico|aleatorizado)\b", 0.15),
        (r"\b(?:meta-?análisis|revisión\s+sistemática)\b", 0.15),
        (r"\b(?:guía|protocolo|consenso)\s+(?:clínic[oa]|práctica)\b", 0.1),
    ]

    # Drug/dosage patterns
    DOSAGE_PATTERNS = [
        (r"\b\d+(?:\.\d+)?\s*(?:mg|g|mcg|ml|UI)/(?:kg|día|dosis)\b", 0.1),
        (r"\b(?:cada|c/)\s*\d+\s*(?:h|horas?)\b", 0.1),
    ]

    def __init__(self, config: RerankerConfig | None = None) -> None:
        """Initialize medical reranker."""
        config = config or RerankerConfig()
        config.medical_boost_enabled = True
        config.medical_weight = 0.25  # Increase medical weight
        super().__init__(config)

        # Compile patterns
        self._evidence_patterns = [
            (re.compile(p, re.IGNORECASE), boost) for p, boost in self.EVIDENCE_PATTERNS
        ]
        self._dosage_patterns = [
            (re.compile(p, re.IGNORECASE), boost) for p, boost in self.DOSAGE_PATTERNS
        ]

    def _calculate_medical_score(self, document: str) -> float:
        """Enhanced medical relevance scoring."""
        base_score = super()._calculate_medical_score(document)

        # Evidence boost
        evidence_boost = 0.0
        for pattern, boost in self._evidence_patterns:
            if pattern.search(document):
                evidence_boost += boost

        # Dosage information boost
        dosage_boost = 0.0
        for pattern, boost in self._dosage_patterns:
            if pattern.search(document):
                dosage_boost += boost

        # Combine scores (cap at 1.0)
        total_score = min(base_score + evidence_boost + dosage_boost, 1.0)

        return total_score


# =============================================================================
# Ensemble Reranker
# =============================================================================


class EnsembleReranker(BaseReranker):
    """
    Ensemble reranker combining multiple reranking strategies.

    Uses weighted voting from multiple rerankers for robust scoring.
    """

    def __init__(
        self,
        rerankers: list[tuple[BaseReranker, float]] | None = None,
        config: RerankerConfig | None = None,
    ) -> None:
        """
        Initialize ensemble reranker.

        Args:
            rerankers: List of (reranker, weight) tuples
            config: Configuration
        """
        super().__init__(config)

        if rerankers:
            self._rerankers = rerankers
        else:
            # Default ensemble
            self._rerankers = [
                (BM25Reranker(config), 0.5),
                (MedicalReranker(config), 0.5),
            ]

    async def rerank(
        self,
        query: str,
        results: list[SearchResult],
        top_k: int | None = None,
    ) -> list[SearchResult]:
        """Rerank using ensemble voting."""
        if not results:
            return []

        top_k = top_k or self.config.top_k

        # Collect scores from all rerankers
        all_scores: dict[str, list[float]] = {r.chunk.id: [] for r in results}
        weights: list[float] = []

        for reranker, weight in self._rerankers:
            # Create copies to avoid mutation issues
            results_copy = [
                SearchResult(
                    chunk=r.chunk,
                    score=r.score,
                    relevance=r.relevance,
                )
                for r in results
            ]

            reranked = await reranker.rerank(query, results_copy, top_k=len(results))

            for r in reranked:
                all_scores[r.chunk.id].append(r.rerank_score or r.score)

            weights.append(weight)

        # Weighted average scores
        total_weight = sum(weights)
        for result in results:
            chunk_scores = all_scores[result.chunk.id]
            if chunk_scores:
                weighted_score = (
                    sum(s * w for s, w in zip(chunk_scores, weights, strict=False))
                    / total_weight
                )
                result.rerank_score = weighted_score
                result.relevance = self._score_to_relevance(weighted_score)

        # Sort by ensemble score
        results.sort(key=lambda r: r.rerank_score or 0, reverse=True)

        return results[:top_k]

    def _score_to_relevance(self, score: float) -> RelevanceLevel:
        """Map ensemble score to relevance level."""
        if score >= 0.75:
            return RelevanceLevel.HIGH
        elif score >= 0.5:
            return RelevanceLevel.MEDIUM
        elif score >= 0.3:
            return RelevanceLevel.LOW
        else:
            return RelevanceLevel.IRRELEVANT


# =============================================================================
# Factory Function
# =============================================================================


class RerankerType(str):
    """Reranker type constants."""

    CROSS_ENCODER = "cross_encoder"
    BM25 = "bm25"
    MEDICAL = "medical"
    ENSEMBLE = "ensemble"


def create_reranker(
    reranker_type: str = RerankerType.MEDICAL,
    config: RerankerConfig | None = None,
) -> BaseReranker:
    """
    Factory function to create reranker instances.

    Args:
        reranker_type: Type of reranker to create
        config: Optional configuration

    Returns:
        Configured reranker instance
    """
    rerankers = {
        RerankerType.CROSS_ENCODER: CrossEncoderReranker,
        RerankerType.BM25: BM25Reranker,
        RerankerType.MEDICAL: MedicalReranker,
        RerankerType.ENSEMBLE: EnsembleReranker,
    }

    reranker_class = rerankers.get(reranker_type, MedicalReranker)
    return reranker_class(config)
