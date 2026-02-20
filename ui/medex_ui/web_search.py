"""
Web Search Module for MedeX Deep Research
==========================================
Real web search using DuckDuckGo for medical research.
"""

import asyncio
from typing import Optional
from dataclasses import dataclass, field
import re

try:
    from duckduckgo_search import DDGS

    HAS_DDGS = True
except ImportError:
    HAS_DDGS = False


@dataclass
class SearchResult:
    """A single search result."""

    title: str
    url: str
    snippet: str
    source: str = ""


@dataclass
class ResearchContext:
    """Accumulated research context."""

    query: str
    sub_questions: list = field(default_factory=list)
    search_results: list = field(default_factory=list)
    synthesized_content: str = ""
    sources: list = field(default_factory=list)


def clean_text(text: str) -> str:
    """Clean text for use in prompts."""
    # Remove excessive whitespace
    text = re.sub(r"\s+", " ", text)
    # Remove special characters that might break prompts
    text = re.sub(r"[^\w\s\.,;:!?\-\(\)\'\"áéíóúñüÁÉÍÓÚÑÜ]", "", text)
    return text.strip()


def search_duckduckgo(query: str, max_results: int = 8) -> list[SearchResult]:
    """
    Search DuckDuckGo for medical information.

    Args:
        query: Search query
        max_results: Maximum number of results

    Returns:
        List of SearchResult objects
    """
    if not HAS_DDGS:
        return []

    results = []
    try:
        with DDGS() as ddgs:
            # Search with medical focus
            search_results = ddgs.text(
                f"{query} medical clinical evidence",
                max_results=max_results,
                region="wt-wt",  # Worldwide
                safesearch="moderate",
            )

            for r in search_results:
                result = SearchResult(
                    title=r.get("title", ""),
                    url=r.get("href", r.get("link", "")),
                    snippet=clean_text(r.get("body", r.get("snippet", ""))),
                    source=extract_domain(r.get("href", r.get("link", ""))),
                )
                results.append(result)
    except Exception as e:
        print(f"DuckDuckGo search error: {e}")

    return results


def extract_domain(url: str) -> str:
    """Extract domain from URL."""
    try:
        from urllib.parse import urlparse

        parsed = urlparse(url)
        domain = parsed.netloc
        # Remove www. prefix
        if domain.startswith("www."):
            domain = domain[4:]
        return domain
    except:
        return url


def generate_sub_questions(query: str) -> list[str]:
    """
    Generate sub-questions for comprehensive research.

    Args:
        query: Main research query

    Returns:
        List of sub-questions to explore
    """
    # Medical research sub-question templates
    sub_questions = [
        f"{query} definition and overview",
        f"{query} pathophysiology mechanism",
        f"{query} clinical guidelines 2024 2025",
        f"{query} treatment protocol evidence",
        f"{query} differential diagnosis",
        f"{query} prognosis outcomes",
        f"{query} recent research studies",
        f"{query} complications risk factors",
    ]

    return sub_questions[:5]  # Limit to 5 sub-questions


def prioritize_medical_sources(results: list[SearchResult]) -> list[SearchResult]:
    """
    Prioritize results from authoritative medical sources.

    Args:
        results: List of search results

    Returns:
        Sorted list with medical sources first
    """
    # High-priority medical domains
    priority_domains = [
        "pubmed.ncbi.nlm.nih.gov",
        "ncbi.nlm.nih.gov",
        "who.int",
        "cdc.gov",
        "nih.gov",
        "mayoclinic.org",
        "uptodate.com",
        "medscape.com",
        "nejm.org",
        "thelancet.com",
        "bmj.com",
        "jamanetwork.com",
        "cochrane.org",
        "clinicaltrials.gov",
        "drugs.com",
        "webmd.com",
        "healthline.com",
        "msdmanuals.com",
    ]

    def get_priority(result: SearchResult) -> int:
        source = result.source.lower()
        for i, domain in enumerate(priority_domains):
            if domain in source:
                return i
        return len(priority_domains) + 1

    return sorted(results, key=get_priority)


async def perform_research(query: str, on_progress: callable = None) -> ResearchContext:
    """
    Perform comprehensive medical research.

    Args:
        query: Research query
        on_progress: Optional callback for progress updates

    Returns:
        ResearchContext with all gathered information
    """
    context = ResearchContext(query=query)

    # Step 1: Generate sub-questions
    if on_progress:
        await on_progress(10, "Generando sub-preguntas de investigación...")

    context.sub_questions = generate_sub_questions(query)

    # Step 2: Search for each sub-question
    all_results = []
    total_searches = len(context.sub_questions) + 1  # +1 for main query

    # Search main query first
    if on_progress:
        await on_progress(15, f"Buscando: {query[:50]}...")

    main_results = search_duckduckgo(query, max_results=5)
    all_results.extend(main_results)

    # Small delay to avoid rate limiting
    await asyncio.sleep(0.5)

    # Search sub-questions
    for i, sub_q in enumerate(context.sub_questions):
        progress = 20 + int((i / total_searches) * 40)
        if on_progress:
            await on_progress(progress, f"Investigando: {sub_q[:40]}...")

        results = search_duckduckgo(sub_q, max_results=3)
        all_results.extend(results)

        # Small delay between searches
        await asyncio.sleep(0.3)

    # Step 3: Deduplicate and prioritize results
    if on_progress:
        await on_progress(65, "Procesando y priorizando fuentes...")

    # Deduplicate by URL
    seen_urls = set()
    unique_results = []
    for r in all_results:
        if r.url not in seen_urls:
            seen_urls.add(r.url)
            unique_results.append(r)

    # Prioritize medical sources
    context.search_results = prioritize_medical_sources(unique_results)[:15]

    # Build sources list
    context.sources = [
        {"title": r.title, "url": r.url, "type": "Web", "domain": r.source}
        for r in context.search_results
    ]

    # Step 4: Synthesize content for LLM
    if on_progress:
        await on_progress(70, "Sintetizando información recopilada...")

    synthesis_parts = []
    for i, r in enumerate(context.search_results[:10], 1):
        synthesis_parts.append(
            f"[Fuente {i}: {r.source}]\nTítulo: {r.title}\nContenido: {r.snippet}\n"
        )

    context.synthesized_content = "\n---\n".join(synthesis_parts)

    return context


def build_research_prompt(context: ResearchContext) -> str:
    """
    Build a comprehensive research prompt with gathered context.

    Args:
        context: ResearchContext with search results

    Returns:
        Prompt string for LLM
    """
    prompt = f"""Eres un investigador médico experto realizando una investigación exhaustiva.

TEMA DE INVESTIGACIÓN: {context.query}

INFORMACIÓN RECOPILADA DE FUENTES MÉDICAS CONFIABLES:
{context.synthesized_content}

SUB-PREGUNTAS EXPLORADAS:
{chr(10).join(f"- {q}" for q in context.sub_questions)}

INSTRUCCIONES:
Basándote en la información recopilada y tu conocimiento médico, genera un informe de investigación completo y estructurado.

El informe DEBE incluir:

## 1. RESUMEN EJECUTIVO
(2-3 párrafos con los hallazgos más importantes)

## 2. CONTEXTO Y ANTECEDENTES
(Historia, definición, epidemiología)

## 3. FISIOPATOLOGÍA / MECANISMO
(Explicación del proceso subyacente)

## 4. EVIDENCIA CIENTÍFICA ACTUAL
(Estudios relevantes, guías clínicas, niveles de evidencia)

## 5. MANIFESTACIONES CLÍNICAS
(Signos, síntomas, presentación)

## 6. DIAGNÓSTICO
(Criterios, pruebas, diagnóstico diferencial)

## 7. TRATAMIENTO
(Opciones terapéuticas, protocolos, algoritmos)

## 8. PRONÓSTICO Y COMPLICACIONES
(Evolución esperada, factores de riesgo)

## 9. CONSIDERACIONES ESPECIALES
(Poblaciones específicas, interacciones, precauciones)

## 10. CONCLUSIONES Y RECOMENDACIONES
(Síntesis final, puntos clave para la práctica)

## 11. REFERENCIAS
(Menciona las fuentes consultadas por número)

IMPORTANTE:
- Escribe un análisis EXTENSO y DETALLADO (mínimo 2000 palabras)
- Usa terminología médica precisa con rigor académico
- Cita las fuentes usando [Fuente X] donde corresponda
- NO incluyas emojis ni símbolos decorativos
- Mantén un tono profesional y objetivo
- Si hay controversias o información limitada, indícalo claramente"""

    return prompt


def format_sources_for_display(sources: list) -> list[dict]:
    """
    Format sources for UI display.

    Args:
        sources: List of source dictionaries

    Returns:
        Formatted list for display
    """
    formatted = []
    for i, source in enumerate(sources, 1):
        formatted.append(
            {
                "number": i,
                "title": source.get("title", "Fuente desconocida")[:80],
                "url": source.get("url", ""),
                "domain": source.get("domain", "Web"),
                "type": source.get("type", "Web"),
            }
        )
    return formatted
