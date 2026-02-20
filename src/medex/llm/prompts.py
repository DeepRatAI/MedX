# =============================================================================
# MedeX - Prompt Manager
# =============================================================================
"""
Advanced prompt management system for medical AI assistant.

Features:
- Template-based prompt generation
- Multi-language support (Spanish/English)
- Dynamic context injection
- Medical domain optimization
- Role-based prompts (educational/professional)
- Token-aware truncation
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from medex.llm.models import Message, MessageRole


# =============================================================================
# Enumerations
# =============================================================================


class PromptType(str, Enum):
    """Types of prompts."""

    SYSTEM = "system"
    USER = "user"
    MEDICAL_TRIAGE = "medical_triage"
    DIAGNOSTIC = "diagnostic"
    TREATMENT = "treatment"
    EDUCATIONAL = "educational"
    PROFESSIONAL = "professional"
    SUMMARY = "summary"
    TOOL_USE = "tool_use"


class UserMode(str, Enum):
    """User interaction mode."""

    EDUCATIONAL = "educational"
    PROFESSIONAL = "professional"


class Language(str, Enum):
    """Supported languages."""

    SPANISH = "es"
    ENGLISH = "en"


# =============================================================================
# Configuration
# =============================================================================


@dataclass
class PromptConfig:
    """Configuration for prompt generation."""

    language: Language = Language.SPANISH
    user_mode: UserMode = UserMode.EDUCATIONAL
    include_disclaimer: bool = True
    include_sources: bool = True
    max_context_tokens: int = 4000
    date_format: str = "%d-%m-%Y %H:%M"

    # Medical specifics
    include_cie10: bool = True
    include_drug_interactions: bool = True
    include_contraindications: bool = True


# =============================================================================
# Prompt Templates
# =============================================================================

SYSTEM_PROMPTS = {
    # Educational mode - Spanish
    (
        "educational",
        "es",
    ): """Eres MedeX, un asistente de educación médica de nivel SOTA diseñado para estudiantes de medicina y profesionales de la salud en formación.

## Tu Audiencia
- **ESTUDIANTES DE MEDICINA** y residentes en formación
- Profesionales de salud que buscan actualizar conocimientos
- NO son pacientes - son colegas en formación académica

## Tu Rol
- Profesor universitario de medicina con amplia experiencia clínica y docente
- Explicas con rigor científico pero de forma didáctica y accesible
- Respondes en español con terminología médica apropiada para estudiantes
- Proporcionas información educativa profunda, como una clase magistral
- Tus respuestas deben ser EXTENSAS y COMPLETAS, propias de educación universitaria

## Directrices Académicas
1. **Extensión**: Respuestas largas y completas (mínimo 500-800 palabras para temas complejos)
2. **Rigor**: Usa terminología médica correcta explicando conceptos cuando sea necesario
3. **Fisiopatología**: Explica los mecanismos subyacentes, no solo los hechos
4. **Estructura**: Organiza como una clase: introducción, desarrollo, conclusiones
5. **Contexto clínico**: Incluye casos prácticos, diagnósticos diferenciales, correlación clínico-patológica
6. **Evidencia**: Menciona guías clínicas, clasificaciones y criterios diagnósticos relevantes
7. **Integración**: Relaciona conceptos con otras áreas médicas cuando aplique

## Formato de Respuesta Educativa
Tu respuesta debe incluir (cuando aplique):
1. **Definición y Epidemiología** - Conceptos fundamentales y datos epidemiológicos
2. **Fisiopatología** - Mecanismos biológicos subyacentes
3. **Manifestaciones Clínicas** - Signos, síntomas, formas de presentación
4. **Diagnóstico** - Criterios, estudios de laboratorio e imagen, diagnóstico diferencial
5. **Tratamiento** - Abordaje terapéutico según guías actuales
6. **Complicaciones y Pronóstico** - Evolución natural, complicaciones potenciales
7. **Puntos Clave** - Conceptos esenciales para el examen y la práctica clínica

## Estilo Profesional
- Usa Markdown para estructurar con encabezados claros
- Incluye tablas comparativas cuando aplique (diagnóstico diferencial, clasificaciones)
- NO uses emojis - mantén estilo académico profesional
- Usa viñetas y numeración para organizar información
- Cita clasificaciones y criterios por su nombre (ej: Criterios de Jones, Clasificación de NYHA)
- NO incluyas disclaimers ni advertencias legales al final (el sistema los agrega automáticamente)

## Fecha actual: {current_date}
## Versión: MedeX v25.83 - Modo Educativo""",
    # Professional mode - Spanish
    (
        "professional",
        "es",
    ): """Eres MedeX, un sistema de soporte a la decisión clínica (CDSS) de nivel SOTA para profesionales de la salud.

## Tu Audiencia
- **MÉDICOS PROFESIONALES** graduados y especialistas
- Personal de salud con formación clínica completa
- Profesionales que requieren soporte basado en evidencia para decisiones clínicas
- NO son pacientes ni estudiantes - son colegas clínicos

## Tu Rol
- Consultor clínico experto que proporciona información basada en evidencia
- Generas análisis estructurados siguiendo estándares médicos internacionales
- Integras información de guías clínicas, protocolos y literatura científica actualizada
- Apoyas el razonamiento diagnóstico y terapéutico con rigor académico

## Capacidades
1. **Análisis clínico**: Síntesis de casos, diagnósticos diferenciales jerarquizados por probabilidad
2. **Farmacología clínica**: Interacciones, dosificación, ajustes por función renal/hepática, contraindicaciones
3. **Guías clínicas**: Referencia a protocolos actualizados (AHA, ESC, IDSA, etc.)
4. **Codificación**: CIE-10, CIE-11, SNOMED-CT cuando aplique
5. **Medicina de laboratorio**: Interpretación contextualizada de resultados

## Formato de Respuesta Clínica
Estructura tu respuesta usando Markdown con la siguiente organización:

**ENCABEZADO:**
## ANÁLISIS CLÍNICO
- **Diagnóstico más probable**: [DIAGNÓSTICO]
- **Código CIE-10**: [código]
- **Fecha**: [fecha]
- **Modalidad**: [especialidad] – [ambulatorio/hospitalario]

**SECCIONES REQUERIDAS:**

### 1. SÍNTESIS DEL CASO
Resumen estructurado del cuadro clínico

### 2. DIAGNÓSTICOS DIFERENCIALES JERARQUIZADOS
Tabla con columnas: Probabilidad | Diagnóstico | Criterios de apoyo | Próximos pasos

### 3. PLAN DIAGNÓSTICO
Estudios recomendados con justificación clínica

### 4. PLAN TERAPÉUTICO
Tratamiento con dosis específicas, vía, frecuencia, duración

### 5. CRITERIOS DE ALARMA
Signos de deterioro que requieren reevaluación o escalamiento

### 6. SEGUIMIENTO
Parámetros a monitorizar, cronograma de reevaluación

## Estilo Profesional
- Usa Markdown estructurado con encabezados claros
- Incluye tablas para información comparativa
- NO uses emojis - mantén formato clínico profesional
- Cita guías y referencias cuando sea pertinente
- Sé conciso pero completo - el médico necesita información accionable

## IMPORTANTE
- NO incluyas disclaimers ni advertencias legales al final de tu respuesta
- El sistema agrega automáticamente los disclaimers necesarios
- Valida dosis con guías locales y protocolos institucionales
- Considera comorbilidades y contraindicaciones individuales
- Este sistema es de soporte, no sustituye el juicio clínico

## Fecha actual: {current_date}
## Versión: MedeX v25.83 - Modo Profesional""",
    # Educational mode - English
    (
        "educational",
        "en",
    ): """You are MedeX, a SOTA-level educational medical assistant designed to provide clear, accurate, and accessible health information.

## Your Role
- Medical educator explaining health concepts in understandable terms
- Use analogies and everyday examples to facilitate understanding
- Respond in English with terminology adapted for the general public
- NEVER provide diagnoses or prescriptions - educational information only

## Guidelines
1. **Clarity**: Use simple language, avoid unnecessary medical jargon
2. **Analogies**: Explain complex concepts with familiar comparisons
3. **Structure**: Organize responses with headings, lists, and tables
4. **Prevention**: Emphasize healthy habits and warning signs
5. **Referral**: Always recommend consulting healthcare professionals

## Current date: {current_date}
## Version: MedeX v25.83""",
    # Professional mode - English
    (
        "professional",
        "en",
    ): """You are MedeX, a SOTA-level Clinical Decision Support System (CDSS) for healthcare professionals.

## Your Role
- Clinical assistant providing evidence-based information
- Generate structured analyses following medical standards
- Integrate information from clinical guidelines, protocols, and scientific literature
- Support diagnostic and therapeutic reasoning

## Current date: {current_date}
## Version: MedeX v25.83 - Professional Mode""",
}


# =============================================================================
# Prompt Templates for Specific Tasks
# =============================================================================

TASK_PROMPTS = {
    "triage": """## Instrucciones de Triaje
Analiza la consulta y determina:
1. **Nivel de urgencia**: Emergencia / Urgente / Rutinario / Educativo
2. **Especialidad sugerida**: Área médica más relevante
3. **Acción recomendada**: Qué debe hacer el usuario

## Consulta del usuario:
{query}

## Contexto RAG (si disponible):
{context}""",
    "diagnostic": """## Análisis Diagnóstico
Realiza un análisis clínico estructurado del siguiente caso:

## Datos del paciente:
{patient_data}

## Motivo de consulta:
{chief_complaint}

## Historia clínica:
{clinical_history}

## Examen físico:
{physical_exam}

## Estudios complementarios:
{lab_results}

## Contexto RAG:
{context}

Genera un análisis siguiendo el formato de respuesta clínica establecido.""",
    "treatment": """## Plan Terapéutico
Genera un plan de tratamiento para:

## Diagnóstico establecido:
{diagnosis}

## Datos del paciente:
- Edad: {age}
- Peso: {weight} kg
- Alergias: {allergies}
- Medicación actual: {current_medications}
- Comorbilidades: {comorbidities}

## Contexto RAG:
{context}

Incluye:
1. Tratamiento farmacológico con dosis específicas
2. Medidas no farmacológicas
3. Criterios de seguimiento
4. Signos de alarma""",
    "drug_interaction": """## Verificación de Interacciones Farmacológicas
Analiza las siguientes medicaciones:

## Medicamentos a evaluar:
{medications}

## Medicación actual del paciente:
{current_medications}

## Comorbilidades relevantes:
{comorbidities}

Identifica:
1. Interacciones medicamentosas (gravedad, mecanismo)
2. Contraindicaciones
3. Ajustes de dosis necesarios
4. Alternativas terapéuticas si aplica""",
    "lab_interpretation": """## Interpretación de Laboratorio
Analiza los siguientes resultados:

## Resultados de laboratorio:
{lab_results}

## Valores de referencia:
{reference_values}

## Contexto clínico:
{clinical_context}

Genera:
1. Interpretación de cada parámetro alterado
2. Patrones diagnósticos identificados
3. Estudios adicionales sugeridos
4. Correlación clínico-laboratorial""",
}


# =============================================================================
# Disclaimers
# =============================================================================

DISCLAIMERS = {
    "educational_es": """---

**Nota**: Esta información es de carácter educativo y formativo. Siempre correlacionar con la clínica del paciente y validar con fuentes primarias y protocolos institucionales.""",
    "professional_es": """---

**IMPORTANTE**: Esta información es de soporte clínico educacional, no sustituye la evaluación médica presencial ni el juicio clínico profesional.

**EMERGENCIAS**: En situaciones de emergencia real, activar protocolos hospitalarios y contactar servicios de emergencia inmediatamente.

**VALIDACIÓN**: Validar dosis y esquemas con guías locales, protocolos institucionales, comorbilidades y contraindicaciones del paciente.""",
    "educational_en": """---

**Note**: This information is for educational and training purposes. Always correlate with patient's clinical picture and validate with primary sources and institutional protocols.""",
    "professional_en": """---

**IMPORTANT**: This information is for clinical educational support and does not replace in-person medical evaluation or professional clinical judgment.

**EMERGENCIES**: In real emergency situations, activate hospital protocols and contact emergency services immediately.

**VALIDATION**: Validate doses and regimens with local guidelines, institutional protocols, comorbidities, and patient contraindications.""",
}


# =============================================================================
# Prompt Manager Class
# =============================================================================


@dataclass
class PromptManager:
    """Manages prompt generation and formatting."""

    config: PromptConfig = field(default_factory=PromptConfig)

    # Cache for compiled templates
    _template_cache: dict[str, str] = field(default_factory=dict)

    def get_system_prompt(
        self,
        user_mode: UserMode | None = None,
        language: Language | None = None,
        **kwargs: Any,
    ) -> Message:
        """Get system prompt for given mode and language."""
        mode = user_mode or self.config.user_mode
        lang = language or self.config.language

        key = (mode.value, lang.value)
        template = SYSTEM_PROMPTS.get(key, SYSTEM_PROMPTS[("educational", "es")])

        # Format with current date and any additional kwargs
        formatted = template.format(
            current_date=datetime.now().strftime(self.config.date_format),
            **kwargs,
        )

        return Message.system(formatted)

    def get_task_prompt(
        self,
        task: str,
        **kwargs: Any,
    ) -> str:
        """Get task-specific prompt template."""
        template = TASK_PROMPTS.get(task, "")
        if not template:
            return ""

        # Replace placeholders with provided values or empty string
        def replace_placeholder(match: re.Match) -> str:
            key = match.group(1)
            return str(kwargs.get(key, f"[{key} no proporcionado]"))

        formatted = re.sub(r"\{(\w+)\}", replace_placeholder, template)
        return formatted

    def build_user_message(
        self,
        query: str,
        context: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Message:
        """Build user message with optional context."""
        content = query

        if context:
            content = f"""## Consulta:
{query}

## Contexto de conocimiento médico (RAG):
{context}"""

        return Message.user(content, metadata=metadata or {})

    def build_messages(
        self,
        query: str,
        context: str | None = None,
        history: list[Message] | None = None,
        user_mode: UserMode | None = None,
        **kwargs: Any,
    ) -> list[Message]:
        """Build complete message list for LLM request."""
        messages: list[Message] = []

        # System prompt
        messages.append(self.get_system_prompt(user_mode=user_mode, **kwargs))

        # Add history if provided
        if history:
            messages.extend(history)

        # User message with context
        messages.append(self.build_user_message(query, context))

        return messages

    def add_disclaimer(
        self,
        response: str,
        user_mode: UserMode | None = None,
        language: Language | None = None,
    ) -> str:
        """Add appropriate disclaimer to response."""
        if not self.config.include_disclaimer:
            return response

        mode = user_mode or self.config.user_mode
        lang = language or self.config.language

        key = f"{mode.value}_{lang.value}"
        disclaimer = DISCLAIMERS.get(key, DISCLAIMERS["educational_es"])

        return f"{response}\n{disclaimer}"

    def format_sources(
        self,
        sources: list[dict[str, Any]],
        language: Language | None = None,
    ) -> str:
        """Format RAG sources for inclusion in response."""
        if not sources or not self.config.include_sources:
            return ""

        lang = language or self.config.language

        header = "📚 **FUENTES:**" if lang == Language.SPANISH else "📚 **SOURCES:**"

        formatted = [header]
        for i, source in enumerate(sources, 1):
            title = source.get("title", "Fuente desconocida")
            doc_type = source.get("doc_type", "documento")
            formatted.append(f"{i}. {title} ({doc_type})")

        return "\n".join(formatted)

    def truncate_context(
        self,
        context: str,
        max_tokens: int | None = None,
    ) -> str:
        """Truncate context to fit token limit."""
        limit = max_tokens or self.config.max_context_tokens

        # Rough estimate: 1 token ≈ 4 characters for Spanish
        max_chars = limit * 4

        if len(context) <= max_chars:
            return context

        # Truncate with ellipsis
        truncated = context[: max_chars - 100]

        # Try to truncate at sentence boundary
        last_period = truncated.rfind(".")
        if last_period > max_chars * 0.8:
            truncated = truncated[: last_period + 1]

        return truncated + "\n\n[... contexto truncado por límite de tokens ...]"

    def format_medical_data(
        self,
        data: dict[str, Any],
        template: str = "diagnostic",
    ) -> str:
        """Format medical data for prompt inclusion."""
        prompt = self.get_task_prompt(template, **data)
        return prompt


# =============================================================================
# Factory Functions
# =============================================================================


def create_prompt_manager(
    language: str = "es",
    user_mode: str = "educational",
    **kwargs: Any,
) -> PromptManager:
    """Create prompt manager with specified configuration."""
    config = PromptConfig(
        language=Language(language),
        user_mode=UserMode(user_mode),
        **kwargs,
    )
    return PromptManager(config=config)


def get_prompt_manager() -> PromptManager:
    """Get default prompt manager instance."""
    return create_prompt_manager()
