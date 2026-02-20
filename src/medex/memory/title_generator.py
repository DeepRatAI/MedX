# =============================================================================
# MedeX - Title Generator
# =============================================================================
"""
Automatic conversation title generation for MedeX V2.

This module provides:
- Extractive title generation from first user message
- LLM-based abstractive titles (optional)
- Medical topic detection for better titles
- Fallback mechanisms for edge cases

Design:
- Fast extractive method by default
- Optional LLM call for higher quality
- Medical terminology awareness
"""

from __future__ import annotations

import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)


# =============================================================================
# Title Generator
# =============================================================================


class TitleGenerator:
    """
    Generate conversation titles automatically.

    Uses extractive methods by default for speed,
    with optional LLM enhancement for quality.
    """

    # Medical keywords that indicate topic
    MEDICAL_KEYWORDS = {
        # Symptoms
        "dolor": "Dolor",
        "fiebre": "Fiebre",
        "tos": "Tos",
        "náusea": "Náusea",
        "vómito": "Vómito",
        "diarrea": "Diarrea",
        "fatiga": "Fatiga",
        "mareo": "Mareo",
        "cefalea": "Cefalea",
        "disnea": "Disnea",
        # Conditions
        "diabetes": "Diabetes",
        "hipertensión": "Hipertensión",
        "asma": "Asma",
        "artritis": "Artritis",
        "cáncer": "Cáncer",
        "covid": "COVID-19",
        "neumonía": "Neumonía",
        "infección": "Infección",
        "alergia": "Alergia",
        "anemia": "Anemia",
        # Medications
        "ibuprofeno": "Ibuprofeno",
        "paracetamol": "Paracetamol",
        "aspirina": "Aspirina",
        "antibiótico": "Antibióticos",
        "insulina": "Insulina",
        "medicamento": "Medicamentos",
        # Body parts
        "cabeza": "Cabeza",
        "pecho": "Pecho",
        "estómago": "Estómago",
        "espalda": "Espalda",
        "corazón": "Corazón",
        "pulmón": "Pulmones",
        "riñón": "Riñones",
        "hígado": "Hígado",
        # General medical
        "síntoma": "Síntomas",
        "diagnóstico": "Diagnóstico",
        "tratamiento": "Tratamiento",
        "dosis": "Dosificación",
        "interacción": "Interacciones",
        "efecto": "Efectos",
        "embarazo": "Embarazo",
        "paciente": "Caso clínico",
    }

    # Question patterns
    QUESTION_PATTERNS = [
        (r"^¿?qué\s+(?:es|son)\s+(.+?)\??$", "Consulta sobre {0}"),
        (r"^¿?cómo\s+(?:se\s+)?(?:trata|tratar)\s+(.+?)\??$", "Tratamiento de {0}"),
        (
            r"^¿?cuál(?:es)?\s+(?:es|son)\s+(?:los?\s+)?síntomas?\s+(?:de|del)\s+(.+?)\??$",
            "Síntomas de {0}",
        ),
        (r"^¿?(?:puedo|puede)\s+(.+?)\??$", "Consulta: {0}"),
        (
            r"^¿?(?:qué|que)\s+(?:pasa|sucede)\s+(?:si|cuando)\s+(.+?)\??$",
            "Consulta: {0}",
        ),
    ]

    # Maximum title length
    MAX_TITLE_LENGTH = 60

    def __init__(self):
        """Initialize title generator."""
        self._compiled_patterns = [
            (re.compile(pattern, re.IGNORECASE), template)
            for pattern, template in self.QUESTION_PATTERNS
        ]

    def generate_from_message(
        self,
        message: str,
        max_length: int = MAX_TITLE_LENGTH,
    ) -> str:
        """
        Generate title from first user message.

        Args:
            message: First user message content
            max_length: Maximum title length

        Returns:
            Generated title string
        """
        if not message or not message.strip():
            return "Nueva conversación"

        # Clean message
        clean = self._clean_message(message)

        # Try pattern matching first
        title = self._try_pattern_match(clean)
        if title:
            return self._truncate(title, max_length)

        # Try medical keyword detection
        title = self._try_medical_keywords(clean)
        if title:
            return self._truncate(title, max_length)

        # Fall back to extractive method
        title = self._extractive_title(clean)
        return self._truncate(title, max_length)

    def _clean_message(self, message: str) -> str:
        """Clean and normalize message for title extraction."""
        # Remove markdown formatting
        text = re.sub(r"\*\*(.+?)\*\*", r"\1", message)
        text = re.sub(r"\*(.+?)\*", r"\1", text)
        text = re.sub(r"`(.+?)`", r"\1", text)
        text = re.sub(r"\[(.+?)\]\(.+?\)", r"\1", text)

        # Remove extra whitespace
        text = re.sub(r"\s+", " ", text).strip()

        # Take first sentence/line if very long
        if len(text) > 200:
            # Split by sentence
            sentences = re.split(r"[.!?]\s+", text)
            if sentences:
                text = sentences[0]

        return text

    def _try_pattern_match(self, message: str) -> Optional[str]:
        """Try to match message against question patterns."""
        for pattern, template in self._compiled_patterns:
            match = pattern.match(message)
            if match:
                captured = match.group(1).strip()
                # Capitalize first letter
                captured = captured[0].upper() + captured[1:] if captured else captured
                return template.format(captured)
        return None

    def _try_medical_keywords(self, message: str) -> Optional[str]:
        """Detect medical keywords and generate appropriate title."""
        message_lower = message.lower()

        # Find all matching keywords
        found_keywords = []
        for keyword, display in self.MEDICAL_KEYWORDS.items():
            if keyword in message_lower:
                found_keywords.append(display)

        if not found_keywords:
            return None

        # Take top 2 keywords
        top_keywords = found_keywords[:2]

        # Check if it's a question
        is_question = message.strip().startswith("¿") or "?" in message

        if is_question:
            if len(top_keywords) == 1:
                return f"Consulta: {top_keywords[0]}"
            return f"Consulta: {' y '.join(top_keywords)}"
        else:
            # Likely a case description
            if len(top_keywords) == 1:
                return f"Caso: {top_keywords[0]}"
            return f"Caso: {' + '.join(top_keywords)}"

    def _extractive_title(self, message: str) -> str:
        """Extract title from message using heuristics."""
        # If short enough, use as-is
        if len(message) <= self.MAX_TITLE_LENGTH:
            # Capitalize first letter
            if message:
                return message[0].upper() + message[1:]
            return message

        # Find a natural break point
        # Prefer breaking at punctuation
        for separator in [". ", ", ", " - ", ": ", " "]:
            if separator in message[: self.MAX_TITLE_LENGTH]:
                idx = message[: self.MAX_TITLE_LENGTH].rfind(separator)
                if idx > 20:  # Ensure minimum length
                    title = message[:idx].strip()
                    return title[0].upper() + title[1:] if title else title

        # Last resort: truncate at word boundary
        words = message[: self.MAX_TITLE_LENGTH].split()
        if words:
            title = " ".join(words[:-1])  # Drop last partial word
            return title[0].upper() + title[1:] if title else "Consulta médica"

        return "Consulta médica"

    def _truncate(self, title: str, max_length: int) -> str:
        """Truncate title to max length with ellipsis if needed."""
        if len(title) <= max_length:
            return title

        # Find word boundary
        truncated = title[: max_length - 3]
        last_space = truncated.rfind(" ")

        if last_space > max_length // 2:
            truncated = truncated[:last_space]

        return truncated.rstrip(".,;:") + "..."

    async def generate_with_llm(
        self,
        message: str,
        llm_client: any,
        max_length: int = MAX_TITLE_LENGTH,
    ) -> str:
        """
        Generate title using LLM for higher quality.

        Args:
            message: First user message
            llm_client: LLM client for generation
            max_length: Maximum title length

        Returns:
            LLM-generated title
        """
        prompt = f"""Genera un título corto y descriptivo (máximo {max_length} caracteres) para una conversación médica que comienza con este mensaje:

Mensaje: "{message[:500]}"

Reglas:
- Máximo {max_length} caracteres
- Sin comillas en el título
- Usar español
- Ser específico sobre el tema médico
- No incluir "Consulta sobre" si no es necesario

Título:"""

        try:
            response = await llm_client.generate(prompt, max_tokens=50)
            title = response.strip().strip("\"'")
            return self._truncate(title, max_length)
        except Exception as e:
            logger.warning(f"LLM title generation failed: {e}")
            return self.generate_from_message(message, max_length)


# =============================================================================
# Singleton Instance
# =============================================================================

_generator: Optional[TitleGenerator] = None


def get_title_generator() -> TitleGenerator:
    """Get or create title generator instance."""
    global _generator
    if _generator is None:
        _generator = TitleGenerator()
    return _generator
