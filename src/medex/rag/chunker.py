# =============================================================================
# MedeX - RAG System: Text Chunker
# =============================================================================
"""
Advanced text chunking for medical documents.

This module provides:
- Semantic-aware chunking (respects section boundaries)
- Overlap-based chunking for context preservation
- Medical-specific chunking strategies
- Metadata extraction during chunking

Chunking strategies:
1. Fixed-size: Simple character/token-based splits
2. Semantic: Respects paragraph and section boundaries
3. Recursive: Hierarchical splitting with fallbacks
4. Medical: Specialized for clinical documents

Design:
- Preserves medical context (dosages, procedures, etc.)
- Maintains section headers for context
- Handles tables, lists, and special formats
- Configurable overlap for retrieval quality
"""

from __future__ import annotations

import logging
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass

from .models import Chunk, ChunkType, Document

logger = logging.getLogger(__name__)


# =============================================================================
# Chunker Configuration
# =============================================================================


@dataclass
class ChunkerConfig:
    """Configuration for text chunking."""

    # Size parameters
    chunk_size: int = 512  # Target chunk size in characters
    chunk_overlap: int = 50  # Overlap between chunks
    min_chunk_size: int = 100  # Minimum chunk size
    max_chunk_size: int = 1500  # Maximum chunk size

    # Behavior
    preserve_sentences: bool = True  # Don't break mid-sentence
    preserve_paragraphs: bool = True  # Prefer paragraph boundaries
    extract_headers: bool = True  # Extract section headers
    include_metadata: bool = True  # Include chunk metadata

    # Medical-specific
    preserve_dosages: bool = True  # Don't break dosage information
    preserve_tables: bool = True  # Keep tables as single chunks
    preserve_lists: bool = True  # Keep lists together when possible


# =============================================================================
# Base Chunker
# =============================================================================


class BaseChunker(ABC):
    """Abstract base class for text chunkers."""

    def __init__(self, config: ChunkerConfig | None = None) -> None:
        """Initialize chunker with configuration."""
        self.config = config or ChunkerConfig()

    @abstractmethod
    def chunk(self, document: Document) -> list[Chunk]:
        """
        Split document into chunks.

        Args:
            document: Document to chunk

        Returns:
            List of Chunk objects
        """
        pass

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count (rough: 1 token ≈ 4 chars for Spanish)."""
        return len(text) // 4


# =============================================================================
# Semantic Chunker
# =============================================================================


class SemanticChunker(BaseChunker):
    """
    Semantic-aware chunker that respects document structure.

    This chunker:
    1. Identifies section headers
    2. Splits on paragraph boundaries
    3. Respects sentence boundaries
    4. Handles special elements (tables, lists)
    """

    # Patterns for section detection
    HEADER_PATTERNS = [
        r"^#{1,6}\s+(.+)$",  # Markdown headers
        r"^([A-ZÁÉÍÓÚ][^.]{0,60}):\s*$",  # Spanish section headers
        r"^\d+\.\s*([A-ZÁÉÍÓÚ][^.]{0,60})$",  # Numbered sections
        r"^[IVX]+\.\s+(.+)$",  # Roman numeral sections
    ]

    # Sentence-ending patterns (Spanish-aware)
    SENTENCE_END = re.compile(r"(?<=[.!?])\s+(?=[A-ZÁÉÍÓÚ¿¡])")

    # Medical patterns to preserve
    DOSAGE_PATTERN = re.compile(
        r"\b\d+(?:\.\d+)?\s*(?:mg|g|mcg|µg|ml|mL|UI|U|mEq|mmol)"
        r"(?:/(?:kg|día|día|h|hora|dosis))?\b"
    )

    def __init__(self, config: ChunkerConfig | None = None) -> None:
        """Initialize semantic chunker."""
        super().__init__(config)
        self._header_re = [re.compile(p, re.MULTILINE) for p in self.HEADER_PATTERNS]

    def chunk(self, document: Document) -> list[Chunk]:
        """
        Chunk document using semantic boundaries.

        Args:
            document: Document to chunk

        Returns:
            List of semantically coherent chunks
        """
        chunks: list[Chunk] = []
        content = document.content

        # Split into sections first
        sections = self._split_into_sections(content)

        char_offset = 0
        for section_idx, (header, section_content) in enumerate(sections):
            section_chunks = self._chunk_section(
                section_content,
                document_id=document.id,
                section_title=header,
                base_index=len(chunks),
                char_offset=char_offset,
            )
            chunks.extend(section_chunks)
            char_offset += len(header) + len(section_content) + 2  # +2 for newlines

        logger.debug(f"Created {len(chunks)} chunks from document {document.id}")
        return chunks

    def _split_into_sections(self, content: str) -> list[tuple[str, str]]:
        """Split content into (header, content) tuples."""
        sections: list[tuple[str, str]] = []

        # Find all headers
        header_positions: list[tuple[int, int, str]] = []
        for pattern in self._header_re:
            for match in pattern.finditer(content):
                header_positions.append(
                    (match.start(), match.end(), match.group(1).strip())
                )

        # Sort by position
        header_positions.sort(key=lambda x: x[0])

        if not header_positions:
            # No headers found, treat as single section
            return [("", content)]

        # Extract sections
        for i, (start, end, header) in enumerate(header_positions):
            if i == 0 and start > 0:
                # Content before first header
                sections.append(("", content[:start].strip()))

            # Find section end
            next_start = (
                header_positions[i + 1][0]
                if i + 1 < len(header_positions)
                else len(content)
            )
            section_content = content[end:next_start].strip()

            if section_content:
                sections.append((header, section_content))

        return sections

    def _chunk_section(
        self,
        content: str,
        document_id: str,
        section_title: str,
        base_index: int,
        char_offset: int,
    ) -> list[Chunk]:
        """Chunk a section respecting size limits."""
        chunks: list[Chunk] = []

        if len(content) <= self.config.chunk_size:
            # Section fits in one chunk
            chunks.append(
                Chunk(
                    content=content,
                    document_id=document_id,
                    chunk_type=self._detect_chunk_type(content),
                    index=base_index,
                    section_title=section_title,
                    start_char=char_offset,
                    end_char=char_offset + len(content),
                )
            )
            return chunks

        # Split into paragraphs
        paragraphs = self._split_paragraphs(content)

        current_chunk = ""
        current_start = char_offset

        for para in paragraphs:
            # Check if adding paragraph exceeds limit
            if len(current_chunk) + len(para) + 2 > self.config.chunk_size:
                if current_chunk:
                    # Save current chunk
                    chunks.append(
                        Chunk(
                            content=current_chunk.strip(),
                            document_id=document_id,
                            chunk_type=self._detect_chunk_type(current_chunk),
                            index=base_index + len(chunks),
                            section_title=section_title,
                            start_char=current_start,
                            end_char=current_start + len(current_chunk),
                        )
                    )

                    # Handle overlap
                    if self.config.chunk_overlap > 0:
                        overlap_text = self._get_overlap_text(current_chunk)
                        current_chunk = overlap_text + "\n\n" + para
                    else:
                        current_chunk = para

                    current_start = char_offset + len(content) - len(current_chunk)
                else:
                    # Single paragraph exceeds limit, split by sentences
                    para_chunks = self._split_long_paragraph(
                        para,
                        document_id,
                        section_title,
                        base_index + len(chunks),
                        current_start,
                    )
                    chunks.extend(para_chunks)
                    current_chunk = ""
                    current_start = char_offset + len(content)
            else:
                if current_chunk:
                    current_chunk += "\n\n" + para
                else:
                    current_chunk = para

        # Don't forget the last chunk
        if current_chunk.strip():
            chunks.append(
                Chunk(
                    content=current_chunk.strip(),
                    document_id=document_id,
                    chunk_type=self._detect_chunk_type(current_chunk),
                    index=base_index + len(chunks),
                    section_title=section_title,
                    start_char=current_start,
                    end_char=current_start + len(current_chunk),
                )
            )

        return chunks

    def _split_paragraphs(self, content: str) -> list[str]:
        """Split content into paragraphs."""
        paragraphs = re.split(r"\n\s*\n", content)
        return [p.strip() for p in paragraphs if p.strip()]

    def _split_long_paragraph(
        self,
        paragraph: str,
        document_id: str,
        section_title: str,
        base_index: int,
        char_offset: int,
    ) -> list[Chunk]:
        """Split a paragraph that exceeds chunk size."""
        chunks: list[Chunk] = []

        # Split by sentences
        sentences = self.SENTENCE_END.split(paragraph)

        current_chunk = ""
        current_start = char_offset

        for sentence in sentences:
            if len(current_chunk) + len(sentence) + 1 > self.config.chunk_size:
                if current_chunk:
                    chunks.append(
                        Chunk(
                            content=current_chunk.strip(),
                            document_id=document_id,
                            chunk_type=ChunkType.PARAGRAPH,
                            index=base_index + len(chunks),
                            section_title=section_title,
                            start_char=current_start,
                        )
                    )
                    current_start += len(current_chunk)
                current_chunk = sentence
            else:
                current_chunk += " " + sentence if current_chunk else sentence

        if current_chunk.strip():
            chunks.append(
                Chunk(
                    content=current_chunk.strip(),
                    document_id=document_id,
                    chunk_type=ChunkType.PARAGRAPH,
                    index=base_index + len(chunks),
                    section_title=section_title,
                    start_char=current_start,
                )
            )

        return chunks

    def _get_overlap_text(self, text: str) -> str:
        """Extract overlap text from end of chunk."""
        if len(text) <= self.config.chunk_overlap:
            return text

        # Try to find sentence boundary in overlap region
        overlap_start = len(text) - self.config.chunk_overlap
        overlap_text = text[overlap_start:]

        # Find first sentence start
        match = re.search(r"(?<=[.!?])\s+", overlap_text)
        if match:
            return overlap_text[match.end() :]

        return overlap_text

    def _detect_chunk_type(self, content: str) -> ChunkType:
        """Detect the type of chunk based on content."""
        content_lower = content.lower().strip()

        # Table detection
        if "|" in content and content.count("|") >= 4:
            return ChunkType.TABLE

        # List detection
        if re.match(r"^[\-\*•]\s", content) or re.match(r"^\d+\.\s", content):
            if content.count("\n") >= 2:
                return ChunkType.LIST

        # Procedure detection
        procedure_keywords = [
            "paso",
            "procedimiento",
            "técnica",
            "realizar",
            "administrar",
        ]
        if any(kw in content_lower for kw in procedure_keywords):
            if re.search(r"\d+\.\s", content):
                return ChunkType.PROCEDURE

        # Definition detection
        if ":" in content[:100] and len(content.split("\n")[0]) < 100:
            return ChunkType.DEFINITION

        return ChunkType.PARAGRAPH


# =============================================================================
# Medical Chunker
# =============================================================================


class MedicalChunker(SemanticChunker):
    """
    Specialized chunker for medical documents.

    Extends SemanticChunker with medical-specific handling:
    - Preserves dosage information
    - Keeps drug interaction warnings together
    - Handles clinical protocols
    - Preserves differential diagnosis lists
    """

    # Medical section indicators
    MEDICAL_SECTIONS = [
        r"tratamiento",
        r"diagnóstico",
        r"posología",
        r"dosis",
        r"contraindicaciones",
        r"efectos adversos",
        r"interacciones",
        r"precauciones",
        r"indicaciones",
    ]

    # Critical information patterns (don't split)
    CRITICAL_PATTERNS = [
        # Dosage blocks
        r"(?:Dosis|Posología):\s*[^\n]+(?:\n\s*[-•]\s*[^\n]+)+",
        # Warning blocks
        r"(?:⚠️|🚨|ADVERTENCIA|PRECAUCIÓN)[^\n]+(?:\n[^\n]+){0,3}",
        # Contraindication blocks
        r"(?:Contraindicaciones?):\s*(?:\n\s*[-•]\s*[^\n]+)+",
    ]

    def __init__(self, config: ChunkerConfig | None = None) -> None:
        """Initialize medical chunker."""
        config = config or ChunkerConfig()
        config.preserve_dosages = True
        config.preserve_lists = True
        super().__init__(config)

        self._critical_re = [
            re.compile(p, re.IGNORECASE | re.MULTILINE) for p in self.CRITICAL_PATTERNS
        ]

    def chunk(self, document: Document) -> list[Chunk]:
        """
        Chunk medical document with domain-specific handling.

        Args:
            document: Medical document to chunk

        Returns:
            List of medically coherent chunks
        """
        # Pre-process to protect critical sections
        protected_content, markers = self._protect_critical_sections(document.content)

        # Create temporary document with protected content
        temp_doc = Document(
            id=document.id,
            title=document.title,
            content=protected_content,
            doc_type=document.doc_type,
            source=document.source,
            metadata=document.metadata,
        )

        # Use parent chunking
        chunks = super().chunk(temp_doc)

        # Restore protected sections
        for chunk in chunks:
            chunk.content = self._restore_critical_sections(chunk.content, markers)

        # Add medical metadata
        for chunk in chunks:
            chunk.metadata["is_medical"] = True
            chunk.metadata["has_dosage"] = bool(
                self.DOSAGE_PATTERN.search(chunk.content)
            )

        return chunks

    def _protect_critical_sections(self, content: str) -> tuple[str, dict[str, str]]:
        """Replace critical sections with markers to prevent splitting."""
        markers: dict[str, str] = {}
        protected = content

        for pattern in self._critical_re:
            for match in pattern.finditer(content):
                marker = f"[[PROTECTED_{len(markers)}]]"
                markers[marker] = match.group(0)
                protected = protected.replace(match.group(0), marker)

        return protected, markers

    def _restore_critical_sections(self, content: str, markers: dict[str, str]) -> str:
        """Restore protected sections from markers."""
        restored = content
        for marker, original in markers.items():
            restored = restored.replace(marker, original)
        return restored


# =============================================================================
# Chunker Factory
# =============================================================================


class ChunkerType(str):
    """Chunker type constants."""

    SEMANTIC = "semantic"
    MEDICAL = "medical"
    FIXED = "fixed"


def create_chunker(
    chunker_type: str = ChunkerType.MEDICAL,
    config: ChunkerConfig | None = None,
) -> BaseChunker:
    """
    Factory function to create chunker instances.

    Args:
        chunker_type: Type of chunker to create
        config: Optional chunker configuration

    Returns:
        Configured chunker instance
    """
    chunkers = {
        ChunkerType.SEMANTIC: SemanticChunker,
        ChunkerType.MEDICAL: MedicalChunker,
    }

    chunker_class = chunkers.get(chunker_type, MedicalChunker)
    return chunker_class(config)
