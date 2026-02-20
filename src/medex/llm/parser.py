# =============================================================================
# MedeX - Response Parser
# =============================================================================
"""
Intelligent response parsing and validation for medical AI responses.

Features:
- JSON extraction and validation
- Medical report structure parsing
- CIE-10 code extraction
- Drug/dosage extraction
- Structured data normalization
- Error recovery and fallback
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from medex.llm.models import LLMResponse


logger = logging.getLogger(__name__)


# =============================================================================
# Enumerations
# =============================================================================


class ParsedContentType(str, Enum):
    """Types of parsed content."""

    TEXT = "text"
    JSON = "json"
    MEDICAL_REPORT = "medical_report"
    DIAGNOSTIC = "diagnostic"
    TREATMENT_PLAN = "treatment_plan"
    LAB_INTERPRETATION = "lab_interpretation"
    TRIAGE = "triage"


class UrgencyLevel(str, Enum):
    """Medical urgency levels."""

    EMERGENCY = "emergency"
    URGENT = "urgent"
    ROUTINE = "routine"
    EDUCATIONAL = "educational"


# =============================================================================
# Parsed Result Models
# =============================================================================


@dataclass
class DrugInfo:
    """Extracted drug information."""

    name: str
    dose: str = ""
    frequency: str = ""
    duration: str = ""
    route: str = ""
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "dose": self.dose,
            "frequency": self.frequency,
            "duration": self.duration,
            "route": self.route,
            "notes": self.notes,
        }


@dataclass
class DiagnosticInfo:
    """Extracted diagnostic information."""

    diagnosis: str
    cie10_code: str = ""
    probability: str = ""
    supporting_criteria: list[str] = field(default_factory=list)
    next_steps: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "diagnosis": self.diagnosis,
            "cie10_code": self.cie10_code,
            "probability": self.probability,
            "supporting_criteria": self.supporting_criteria,
            "next_steps": self.next_steps,
        }


@dataclass
class ParsedMedicalReport:
    """Structured medical report parsed from LLM response."""

    # Basic info
    diagnosis: str = ""
    cie10_code: str = ""
    specialty: str = ""
    modality: str = ""

    # Clinical content
    case_summary: str = ""
    differential_diagnoses: list[DiagnosticInfo] = field(default_factory=list)
    diagnostic_plan: list[str] = field(default_factory=list)
    treatment_plan: list[DrugInfo] = field(default_factory=list)
    treatment_notes: list[str] = field(default_factory=list)

    # Alerts
    alarm_criteria: list[str] = field(default_factory=list)
    contraindications: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    # Metadata
    urgency: UrgencyLevel = UrgencyLevel.ROUTINE
    sources: list[str] = field(default_factory=list)
    raw_content: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "diagnosis": self.diagnosis,
            "cie10_code": self.cie10_code,
            "specialty": self.specialty,
            "modality": self.modality,
            "case_summary": self.case_summary,
            "differential_diagnoses": [
                d.to_dict() for d in self.differential_diagnoses
            ],
            "diagnostic_plan": self.diagnostic_plan,
            "treatment_plan": [t.to_dict() for t in self.treatment_plan],
            "treatment_notes": self.treatment_notes,
            "alarm_criteria": self.alarm_criteria,
            "contraindications": self.contraindications,
            "warnings": self.warnings,
            "urgency": self.urgency.value,
            "sources": self.sources,
        }


@dataclass
class ParsedResponse:
    """Generic parsed response container."""

    content_type: ParsedContentType
    raw_content: str
    parsed_content: Any = None

    # Extracted data
    medical_report: ParsedMedicalReport | None = None
    json_data: dict[str, Any] | None = None

    # Metadata
    parse_success: bool = True
    parse_errors: list[str] = field(default_factory=list)
    extracted_entities: dict[str, list[str]] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "content_type": self.content_type.value,
            "raw_content": self.raw_content,
            "parse_success": self.parse_success,
            "parse_errors": self.parse_errors,
            "extracted_entities": self.extracted_entities,
            "medical_report": self.medical_report.to_dict()
            if self.medical_report
            else None,
            "json_data": self.json_data,
        }


# =============================================================================
# Extraction Patterns
# =============================================================================

# CIE-10 code pattern
CIE10_PATTERN = re.compile(
    r"\b([A-Z]\d{2}(?:\.\d{1,2})?)\b",
    re.IGNORECASE,
)

# Drug dosage patterns
DRUG_PATTERNS = {
    "dose": re.compile(
        r"(\d+(?:[.,]\d+)?)\s*(mg|g|mcg|µg|ml|mL|UI|U|IU)",
        re.IGNORECASE,
    ),
    "frequency": re.compile(
        r"cada\s+(\d+)\s*(horas?|h|días?|d)|"
        r"(\d+)\s*(?:veces?|x)\s*(?:al\s+)?día|"
        r"(diario|bid|tid|qid|prn|stat|qd|qod)",
        re.IGNORECASE,
    ),
    "duration": re.compile(
        r"(?:por|durante|x)\s*(\d+)\s*(días?|semanas?|meses?)",
        re.IGNORECASE,
    ),
    "route": re.compile(
        r"\b(VO|IV|IM|SC|SL|tópico|inhalado|oral|intravenoso|intramuscular)\b",
        re.IGNORECASE,
    ),
}

# Medical urgency indicators
EMERGENCY_KEYWORDS = {
    "emergencia",
    "urgente",
    "inmediato",
    "critical",
    "emergency",
    "stat",
    "código",
    "shock",
    "paro",
    "infarto",
    "ictus",
    "stroke",
    "hemorragia",
}

URGENT_KEYWORDS = {
    "urgencia",
    "pronto",
    "rápido",
    "urgent",
    "soon",
    "prioridad",
    "atención",
}


# =============================================================================
# Response Parser
# =============================================================================


@dataclass
class ParserConfig:
    """Configuration for response parser."""

    extract_cie10: bool = True
    extract_drugs: bool = True
    extract_urgency: bool = True
    validate_json: bool = True
    strict_mode: bool = False


class ResponseParser:
    """Parser for LLM responses."""

    def __init__(self, config: ParserConfig | None = None) -> None:
        """Initialize parser."""
        self.config = config or ParserConfig()

    def parse(
        self,
        response: LLMResponse | str,
        expected_type: ParsedContentType = ParsedContentType.TEXT,
    ) -> ParsedResponse:
        """Parse LLM response."""
        content = response.content if isinstance(response, LLMResponse) else response

        result = ParsedResponse(
            content_type=expected_type,
            raw_content=content,
        )

        try:
            # Attempt to parse based on expected type
            if expected_type == ParsedContentType.JSON:
                result = self._parse_json(content, result)

            elif expected_type == ParsedContentType.MEDICAL_REPORT:
                result = self._parse_medical_report(content, result)

            elif expected_type == ParsedContentType.DIAGNOSTIC:
                result = self._parse_diagnostic(content, result)

            elif expected_type == ParsedContentType.TREATMENT_PLAN:
                result = self._parse_treatment(content, result)

            else:
                result = self._parse_text(content, result)

            # Always extract entities
            result.extracted_entities = self._extract_entities(content)

        except Exception as e:
            logger.error(f"Parse error: {e}")
            result.parse_success = False
            result.parse_errors.append(str(e))

        return result

    def _parse_json(self, content: str, result: ParsedResponse) -> ParsedResponse:
        """Parse JSON from response."""
        # Try to extract JSON from markdown code block
        json_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", content)
        json_str = json_match.group(1) if json_match else content

        # Try to find JSON object or array
        if not json_match:
            # Look for JSON-like structure
            brace_match = re.search(r"(\{[\s\S]*\}|\[[\s\S]*\])", json_str)
            if brace_match:
                json_str = brace_match.group(1)

        try:
            result.json_data = json.loads(json_str)
            result.parsed_content = result.json_data
        except json.JSONDecodeError as e:
            result.parse_success = False
            result.parse_errors.append(f"JSON parse error: {e}")
            # Return raw content as fallback
            result.parsed_content = content

        return result

    def _parse_medical_report(
        self,
        content: str,
        result: ParsedResponse,
    ) -> ParsedResponse:
        """Parse structured medical report."""
        report = ParsedMedicalReport(raw_content=content)

        # Extract diagnosis and CIE-10
        diag_match = re.search(
            r"DIAGNÓSTICO[^:]*:\s*[–-]?\s*(.+?)(?:\n|$)",
            content,
            re.IGNORECASE,
        )
        if diag_match:
            report.diagnosis = diag_match.group(1).strip()

        # Extract CIE-10 code
        cie10_match = re.search(
            r"(?:CIE-?10|Código)[^:]*:\s*([A-Z]\d{2}(?:\.\d{1,2})?)",
            content,
            re.IGNORECASE,
        )
        if cie10_match:
            report.cie10_code = cie10_match.group(1).upper()

        # Extract specialty
        specialty_match = re.search(
            r"(?:Especialidad|Modalidad)[^:]*:\s*(.+?)(?:\n|$)",
            content,
            re.IGNORECASE,
        )
        if specialty_match:
            report.specialty = specialty_match.group(1).strip()

        # Extract case summary (section 1)
        summary_match = re.search(
            r"(?:SÍNTESIS|RESUMEN)[^:]*[\s\S]*?(?=###|\Z)",
            content,
            re.IGNORECASE,
        )
        if summary_match:
            report.case_summary = summary_match.group(0).strip()

        # Extract differential diagnoses from table
        report.differential_diagnoses = self._extract_differentials(content)

        # Extract diagnostic plan
        diag_plan_match = re.search(
            r"(?:PLAN DIAGNÓSTICO|ESTUDIOS)[^:]*:([\s\S]*?)(?=###|\Z)",
            content,
            re.IGNORECASE,
        )
        if diag_plan_match:
            report.diagnostic_plan = self._extract_list_items(diag_plan_match.group(1))

        # Extract treatment plan
        report.treatment_plan = self._extract_medications(content)

        # Extract alarm criteria
        alarm_match = re.search(
            r"(?:CRITERIOS DE ALARMA|SIGNOS DE ALARMA|CRITERIOS DE INTERNACIÓN)"
            r"[^:]*:([\s\S]*?)(?=###|\Z)",
            content,
            re.IGNORECASE,
        )
        if alarm_match:
            report.alarm_criteria = self._extract_list_items(alarm_match.group(1))

        # Extract sources
        sources_match = re.search(
            r"(?:FUENTES|REFERENCIAS|EVIDENCIA)[^:]*:([\s\S]*?)(?=---|\Z)",
            content,
            re.IGNORECASE,
        )
        if sources_match:
            report.sources = self._extract_list_items(sources_match.group(1))

        # Determine urgency
        report.urgency = self._determine_urgency(content)

        result.medical_report = report
        result.parsed_content = report
        return result

    def _parse_diagnostic(self, content: str, result: ParsedResponse) -> ParsedResponse:
        """Parse diagnostic-focused response."""
        # Use medical report parser as base
        result = self._parse_medical_report(content, result)
        result.content_type = ParsedContentType.DIAGNOSTIC
        return result

    def _parse_treatment(self, content: str, result: ParsedResponse) -> ParsedResponse:
        """Parse treatment-focused response."""
        result = self._parse_medical_report(content, result)
        result.content_type = ParsedContentType.TREATMENT_PLAN
        return result

    def _parse_text(self, content: str, result: ParsedResponse) -> ParsedResponse:
        """Parse plain text response."""
        result.parsed_content = content

        # Still extract any medical entities
        result.extracted_entities = self._extract_entities(content)

        return result

    def _extract_differentials(self, content: str) -> list[DiagnosticInfo]:
        """Extract differential diagnoses from content."""
        differentials = []

        # Look for table rows
        table_pattern = re.compile(
            r"\|\s*(?:Alta|Moderada|Baja|Muy baja|High|Moderate|Low)?\s*"
            r"(?:\([^)]+\))?\s*\|\s*\*?\*?([^|]+)\*?\*?\s*\|",
            re.IGNORECASE,
        )

        for match in table_pattern.finditer(content):
            diagnosis = match.group(1).strip()
            if diagnosis and len(diagnosis) > 3:
                # Extract CIE-10 if present
                cie10 = ""
                cie10_match = CIE10_PATTERN.search(diagnosis)
                if cie10_match:
                    cie10 = cie10_match.group(1).upper()

                differentials.append(
                    DiagnosticInfo(
                        diagnosis=diagnosis,
                        cie10_code=cie10,
                    )
                )

        return differentials

    def _extract_medications(self, content: str) -> list[DrugInfo]:
        """Extract medication information from content."""
        medications = []

        # Pattern for medication lines
        med_pattern = re.compile(
            r"(?:\*\*|-)?\s*([A-Za-záéíóúñÁÉÍÓÚÑ]+(?:\s+[A-Za-záéíóúñÁÉÍÓÚÑ]+)?)"
            r"\s*:?\s*(\d+(?:[.,]\d+)?)\s*(mg|g|mcg|ml|UI)",
            re.IGNORECASE,
        )

        for match in med_pattern.finditer(content):
            name = match.group(1).strip()
            dose = f"{match.group(2)} {match.group(3)}"

            # Skip common non-drug words
            skip_words = {"hemoglobina", "creatinina", "glucosa", "colesterol", "hb"}
            if name.lower() in skip_words:
                continue

            # Extract frequency if nearby
            freq = ""
            freq_match = DRUG_PATTERNS["frequency"].search(
                content[match.end() : match.end() + 50]
            )
            if freq_match:
                freq = freq_match.group(0)

            # Extract duration if nearby
            duration = ""
            dur_match = DRUG_PATTERNS["duration"].search(
                content[match.end() : match.end() + 80]
            )
            if dur_match:
                duration = dur_match.group(0)

            # Extract route if nearby
            route = ""
            route_match = DRUG_PATTERNS["route"].search(
                content[match.start() - 20 : match.end() + 30]
            )
            if route_match:
                route = route_match.group(1)

            medications.append(
                DrugInfo(
                    name=name,
                    dose=dose,
                    frequency=freq,
                    duration=duration,
                    route=route,
                )
            )

        return medications

    def _extract_list_items(self, text: str) -> list[str]:
        """Extract list items from text."""
        items = []

        # Match bullet points, numbers, or dashes
        pattern = re.compile(r"(?:^|\n)\s*(?:[-•*]|\d+\.)\s*(.+?)(?=\n|$)")

        for match in pattern.finditer(text):
            item = match.group(1).strip()
            if item and len(item) > 2:
                items.append(item)

        return items

    def _extract_entities(self, content: str) -> dict[str, list[str]]:
        """Extract medical entities from content."""
        entities: dict[str, list[str]] = {
            "cie10_codes": [],
            "medications": [],
            "lab_values": [],
        }

        # Extract CIE-10 codes
        if self.config.extract_cie10:
            cie10_matches = CIE10_PATTERN.findall(content)
            entities["cie10_codes"] = list(set(c.upper() for c in cie10_matches))

        # Extract drug mentions
        if self.config.extract_drugs:
            meds = self._extract_medications(content)
            entities["medications"] = [m.name for m in meds]

        # Extract lab values (simplified pattern)
        lab_pattern = re.compile(
            r"(\w+)\s*:\s*(\d+(?:[.,]\d+)?)\s*(g/dL|mg/dL|mmol/L|U/L|%|fL)",
            re.IGNORECASE,
        )
        for match in lab_pattern.finditer(content):
            lab_name = match.group(1)
            lab_value = match.group(2)
            lab_unit = match.group(3)
            entities["lab_values"].append(f"{lab_name}: {lab_value} {lab_unit}")

        return entities

    def _determine_urgency(self, content: str) -> UrgencyLevel:
        """Determine urgency level from content."""
        if not self.config.extract_urgency:
            return UrgencyLevel.ROUTINE

        content_lower = content.lower()

        # Check for emergency keywords
        for keyword in EMERGENCY_KEYWORDS:
            if keyword in content_lower:
                return UrgencyLevel.EMERGENCY

        # Check for urgent keywords
        for keyword in URGENT_KEYWORDS:
            if keyword in content_lower:
                return UrgencyLevel.URGENT

        # Check for educational mode indicators
        if "educativo" in content_lower or "educational" in content_lower:
            return UrgencyLevel.EDUCATIONAL

        return UrgencyLevel.ROUTINE

    def extract_json(self, content: str) -> dict[str, Any] | None:
        """Extract JSON from content, with fallback strategies."""
        # Strategy 1: Look for code block
        json_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", content)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # Strategy 2: Look for raw JSON object
        brace_match = re.search(r"(\{[\s\S]*\})", content)
        if brace_match:
            try:
                return json.loads(brace_match.group(1))
            except json.JSONDecodeError:
                pass

        # Strategy 3: Look for raw JSON array
        bracket_match = re.search(r"(\[[\s\S]*\])", content)
        if bracket_match:
            try:
                return {"data": json.loads(bracket_match.group(1))}
            except json.JSONDecodeError:
                pass

        return None


# =============================================================================
# Factory Functions
# =============================================================================


def create_parser(config: ParserConfig | None = None) -> ResponseParser:
    """Create response parser with configuration."""
    return ResponseParser(config)


def get_parser() -> ResponseParser:
    """Get default parser instance."""
    return ResponseParser()
