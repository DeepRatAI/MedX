"""
Scientific Search Module for MedeX Deep Research
=================================================
Real scientific literature search using PubMed and Semantic Scholar APIs.
Provides evidence-based medical research with proper citations.
"""

import asyncio
import aiohttp
import re
import xml.etree.ElementTree as ET
from typing import Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


# ==============================================================================
# DATA CLASSES
# ==============================================================================


class EvidenceLevel(Enum):
    """GRADE-style evidence levels."""

    LEVEL_1A = ("1a", "Meta-análisis/Revisiones sistemáticas de ECAs", "Alta")
    LEVEL_1B = ("1b", "Ensayo clínico aleatorizado individual", "Alta")
    LEVEL_2A = ("2a", "Revisión sistemática de estudios de cohorte", "Moderada")
    LEVEL_2B = ("2b", "Estudio de cohorte individual", "Moderada")
    LEVEL_3A = ("3a", "Revisión sistemática de casos y controles", "Baja")
    LEVEL_3B = ("3b", "Estudio de casos y controles individual", "Baja")
    LEVEL_4 = ("4", "Serie de casos", "Muy baja")
    LEVEL_5 = ("5", "Opinión de expertos", "Muy baja")
    UNKNOWN = ("?", "Nivel no determinado", "Desconocido")

    @property
    def code(self):
        return self.value[0]

    @property
    def description(self):
        return self.value[1]

    @property
    def quality(self):
        return self.value[2]


@dataclass
class ScientificArticle:
    """A scientific article from PubMed or Semantic Scholar."""

    pmid: str = ""
    doi: str = ""
    title: str = ""
    authors: list = field(default_factory=list)
    journal: str = ""
    year: int = 0
    abstract: str = ""
    mesh_terms: list = field(default_factory=list)
    article_type: str = ""
    url: str = ""
    evidence_level: EvidenceLevel = EvidenceLevel.UNKNOWN
    citation_count: int = 0
    source_api: str = ""  # "pubmed" or "semantic_scholar"

    @property
    def authors_short(self) -> str:
        """Return authors in short format (First et al.)"""
        if not self.authors:
            return "Unknown"
        if len(self.authors) == 1:
            return self.authors[0]
        return f"{self.authors[0]} et al."

    @property
    def citation_vancouver(self) -> str:
        """Return citation in Vancouver style."""
        authors_str = ", ".join(self.authors[:3])
        if len(self.authors) > 3:
            authors_str += " et al"
        return f"{authors_str}. {self.title}. {self.journal}. {self.year}"

    @property
    def citation_apa(self) -> str:
        """Return citation in APA style."""
        if len(self.authors) > 2:
            authors_str = f"{self.authors[0]} et al."
        else:
            authors_str = " & ".join(self.authors)
        return f"{authors_str} ({self.year}). {self.title}. {self.journal}"


@dataclass
class ScientificResearchContext:
    """Complete research context with scientific sources."""

    query: str
    sub_questions: list = field(default_factory=list)
    articles: list = field(default_factory=list)  # List of ScientificArticle
    web_results: list = field(default_factory=list)  # Backup web results
    synthesized_content: str = ""
    evidence_summary: dict = field(default_factory=dict)
    search_stats: dict = field(default_factory=dict)
    timestamp: str = ""


# ==============================================================================
# PUBMED API CLIENT
# ==============================================================================


class PubMedClient:
    """
    Client for NCBI PubMed E-utilities API.
    Free API, no key required (rate limited to 3 requests/second).
    """

    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

    def __init__(self):
        self.timeout = aiohttp.ClientTimeout(total=15)

    async def search(
        self, query: str, max_results: int = 10, sort: str = "relevance"
    ) -> list[str]:
        """
        Search PubMed and return list of PMIDs.

        Args:
            query: Search query
            max_results: Maximum number of results
            sort: Sort order ("relevance" or "date")

        Returns:
            List of PubMed IDs (PMIDs)
        """
        # Build medical-focused query
        search_query = f"({query})"

        params = {
            "db": "pubmed",
            "term": search_query,
            "retmax": max_results,
            "sort": sort,
            "retmode": "json",
        }

        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(
                    f"{self.BASE_URL}/esearch.fcgi", params=params
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("esearchresult", {}).get("idlist", [])
        except Exception as e:
            print(f"PubMed search error: {e}")

        return []

    async def fetch_articles(self, pmids: list[str]) -> list[ScientificArticle]:
        """
        Fetch article details for given PMIDs.

        Args:
            pmids: List of PubMed IDs

        Returns:
            List of ScientificArticle objects
        """
        if not pmids:
            return []

        params = {"db": "pubmed", "id": ",".join(pmids), "retmode": "xml"}

        articles = []

        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(
                    f"{self.BASE_URL}/efetch.fcgi", params=params
                ) as response:
                    if response.status == 200:
                        xml_text = await response.text()
                        articles = self._parse_pubmed_xml(xml_text)
        except Exception as e:
            print(f"PubMed fetch error: {e}")

        return articles

    def _parse_pubmed_xml(self, xml_text: str) -> list[ScientificArticle]:
        """Parse PubMed XML response into ScientificArticle objects."""
        articles = []

        try:
            root = ET.fromstring(xml_text)

            for article_elem in root.findall(".//PubmedArticle"):
                article = ScientificArticle(source_api="pubmed")

                # PMID
                pmid_elem = article_elem.find(".//PMID")
                if pmid_elem is not None:
                    article.pmid = pmid_elem.text
                    article.url = f"https://pubmed.ncbi.nlm.nih.gov/{article.pmid}/"

                # Title
                title_elem = article_elem.find(".//ArticleTitle")
                if title_elem is not None:
                    article.title = "".join(title_elem.itertext())

                # Authors
                authors = []
                for author in article_elem.findall(".//Author"):
                    lastname = author.find("LastName")
                    initials = author.find("Initials")
                    if lastname is not None:
                        name = lastname.text
                        if initials is not None:
                            name += f" {initials.text}"
                        authors.append(name)
                article.authors = authors[:10]  # Limit to 10 authors

                # Journal
                journal_elem = article_elem.find(".//Journal/Title")
                if journal_elem is not None:
                    article.journal = journal_elem.text

                # Year
                year_elem = article_elem.find(".//PubDate/Year")
                if year_elem is not None:
                    try:
                        article.year = int(year_elem.text)
                    except:
                        article.year = 0

                # Abstract
                abstract_parts = []
                for abstract_text in article_elem.findall(".//AbstractText"):
                    label = abstract_text.get("Label", "")
                    text = "".join(abstract_text.itertext())
                    if label:
                        abstract_parts.append(f"{label}: {text}")
                    else:
                        abstract_parts.append(text)
                article.abstract = " ".join(abstract_parts)

                # MeSH terms
                mesh_terms = []
                for mesh in article_elem.findall(".//MeshHeading/DescriptorName"):
                    mesh_terms.append(mesh.text)
                article.mesh_terms = mesh_terms[:10]

                # Article type
                pub_types = []
                for pub_type in article_elem.findall(".//PublicationType"):
                    pub_types.append(pub_type.text)
                article.article_type = "; ".join(pub_types[:3])

                # DOI
                doi_elem = article_elem.find(".//ArticleId[@IdType='doi']")
                if doi_elem is not None:
                    article.doi = doi_elem.text

                # Classify evidence level
                article.evidence_level = self._classify_evidence(
                    pub_types, article.title
                )

                articles.append(article)

        except Exception as e:
            print(f"XML parsing error: {e}")

        return articles

    def _classify_evidence(self, pub_types: list[str], title: str) -> EvidenceLevel:
        """Classify article evidence level based on publication type."""
        pub_types_lower = [pt.lower() for pt in pub_types]
        title_lower = title.lower()

        # Level 1a: Systematic reviews and meta-analyses
        if any(
            t in " ".join(pub_types_lower)
            for t in ["meta-analysis", "systematic review"]
        ):
            return EvidenceLevel.LEVEL_1A
        if "meta-analysis" in title_lower or "systematic review" in title_lower:
            return EvidenceLevel.LEVEL_1A

        # Level 1b: Randomized controlled trials
        if "randomized controlled trial" in " ".join(pub_types_lower):
            return EvidenceLevel.LEVEL_1B
        if "randomized" in title_lower and "trial" in title_lower:
            return EvidenceLevel.LEVEL_1B

        # Level 2a: Cohort study reviews
        if "cohort" in title_lower and (
            "review" in title_lower or "systematic" in title_lower
        ):
            return EvidenceLevel.LEVEL_2A

        # Level 2b: Individual cohort studies
        if (
            "cohort" in title_lower
            or "prospective" in title_lower
            or "longitudinal" in title_lower
        ):
            return EvidenceLevel.LEVEL_2B

        # Level 3: Case-control studies
        if "case-control" in title_lower or "case control" in title_lower:
            return EvidenceLevel.LEVEL_3B

        # Level 4: Case series/reports
        if any(t in " ".join(pub_types_lower) for t in ["case report", "case series"]):
            return EvidenceLevel.LEVEL_4
        if "case report" in title_lower or "case series" in title_lower:
            return EvidenceLevel.LEVEL_4

        # Level 5: Expert opinion, editorials, etc.
        if any(
            t in " ".join(pub_types_lower)
            for t in ["editorial", "comment", "letter", "opinion"]
        ):
            return EvidenceLevel.LEVEL_5

        # Clinical trials (not specified as randomized)
        if "clinical trial" in " ".join(pub_types_lower):
            return EvidenceLevel.LEVEL_2B

        return EvidenceLevel.UNKNOWN


# ==============================================================================
# SEMANTIC SCHOLAR API CLIENT
# ==============================================================================


class SemanticScholarClient:
    """
    Client for Semantic Scholar API.
    Free API with generous rate limits.
    """

    BASE_URL = "https://api.semanticscholar.org/graph/v1"

    def __init__(self):
        self.timeout = aiohttp.ClientTimeout(total=15)

    async def search(
        self, query: str, max_results: int = 10
    ) -> list[ScientificArticle]:
        """
        Search Semantic Scholar for academic papers.

        Args:
            query: Search query
            max_results: Maximum number of results

        Returns:
            List of ScientificArticle objects
        """
        # Add medical/clinical focus
        search_query = f"{query} medicine clinical"

        params = {
            "query": search_query,
            "limit": max_results,
            "fields": "paperId,title,authors,year,abstract,citationCount,journal,externalIds,publicationTypes",
        }

        articles = []

        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(
                    f"{self.BASE_URL}/paper/search", params=params
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        for paper in data.get("data", []):
                            article = self._parse_paper(paper)
                            if article:
                                articles.append(article)
        except Exception as e:
            print(f"Semantic Scholar search error: {e}")

        return articles

    def _parse_paper(self, paper: dict) -> Optional[ScientificArticle]:
        """Parse Semantic Scholar paper into ScientificArticle."""
        try:
            article = ScientificArticle(source_api="semantic_scholar")

            article.title = paper.get("title", "")
            if not article.title:
                return None

            # Authors
            authors = paper.get("authors", [])
            article.authors = [a.get("name", "") for a in authors if a.get("name")][:10]

            # Year
            article.year = paper.get("year", 0) or 0

            # Abstract
            article.abstract = paper.get("abstract", "") or ""

            # Citation count
            article.citation_count = paper.get("citationCount", 0) or 0

            # Journal
            journal_info = paper.get("journal")
            if journal_info and isinstance(journal_info, dict):
                article.journal = journal_info.get("name", "")

            # External IDs (DOI, PMID)
            ext_ids = paper.get("externalIds", {}) or {}
            article.doi = ext_ids.get("DOI", "")
            article.pmid = ext_ids.get("PubMed", "")

            # URL
            if article.doi:
                article.url = f"https://doi.org/{article.doi}"
            elif article.pmid:
                article.url = f"https://pubmed.ncbi.nlm.nih.gov/{article.pmid}/"
            else:
                paper_id = paper.get("paperId", "")
                article.url = f"https://www.semanticscholar.org/paper/{paper_id}"

            # Publication types
            pub_types = paper.get("publicationTypes", []) or []
            article.article_type = "; ".join(pub_types[:3])

            # Evidence level (based on title and types)
            article.evidence_level = self._classify_evidence(pub_types, article.title)

            return article

        except Exception as e:
            print(f"Paper parsing error: {e}")
            return None

    def _classify_evidence(self, pub_types: list[str], title: str) -> EvidenceLevel:
        """Classify evidence level based on publication type."""
        pub_types_lower = [pt.lower() for pt in (pub_types or [])]
        title_lower = title.lower()

        # Meta-analysis
        if "meta-analysis" in title_lower or "metaanalysis" in title_lower:
            return EvidenceLevel.LEVEL_1A
        if "systematic review" in title_lower:
            return EvidenceLevel.LEVEL_1A

        # RCT
        if "review" in pub_types_lower and "clinical" in title_lower:
            return EvidenceLevel.LEVEL_1A
        if "randomized" in title_lower and "trial" in title_lower:
            return EvidenceLevel.LEVEL_1B

        # Cohort
        if "cohort" in title_lower:
            return EvidenceLevel.LEVEL_2B

        # Case-control
        if "case-control" in title_lower:
            return EvidenceLevel.LEVEL_3B

        # Case report/series
        if "case report" in title_lower or "case series" in title_lower:
            return EvidenceLevel.LEVEL_4

        return EvidenceLevel.UNKNOWN


# ==============================================================================
# MAIN RESEARCH ENGINE
# ==============================================================================


async def perform_scientific_research(
    query: str,
    on_progress: Callable = None,
    max_pubmed: int = 10,
    max_semantic: int = 5,
    include_web_fallback: bool = True,
) -> ScientificResearchContext:
    """
    Perform comprehensive scientific literature research.

    Args:
        query: Research query
        on_progress: Async callback for progress updates (progress%, message)
        max_pubmed: Maximum articles from PubMed
        max_semantic: Maximum articles from Semantic Scholar
        include_web_fallback: Whether to include DuckDuckGo fallback

    Returns:
        ScientificResearchContext with all gathered information
    """
    context = ScientificResearchContext(
        query=query, timestamp=datetime.now().isoformat()
    )

    pubmed = PubMedClient()
    semantic = SemanticScholarClient()

    all_articles = []
    search_stats = {
        "pubmed_found": 0,
        "semantic_scholar_found": 0,
        "web_found": 0,
        "high_evidence": 0,
        "moderate_evidence": 0,
        "low_evidence": 0,
    }

    # Step 1: Generate research sub-questions
    if on_progress:
        await on_progress(5, "Analizando consulta de investigación...")

    context.sub_questions = _generate_medical_subquestions(query)

    # Step 2: Search PubMed (main API for medical literature)
    if on_progress:
        await on_progress(10, "Buscando en PubMed (literatura médica indexada)...")

    try:
        # Main query
        pmids = await pubmed.search(query, max_results=max_pubmed)
        if pmids:
            articles = await pubmed.fetch_articles(pmids)
            all_articles.extend(articles)
            search_stats["pubmed_found"] = len(articles)

        await asyncio.sleep(0.4)  # Rate limit respect

        # Search most relevant sub-questions
        for i, sub_q in enumerate(context.sub_questions[:2]):
            if on_progress:
                await on_progress(15 + i * 5, f"PubMed: {sub_q[:40]}...")

            sub_pmids = await pubmed.search(sub_q, max_results=5)
            if sub_pmids:
                sub_articles = await pubmed.fetch_articles(sub_pmids)
                all_articles.extend(sub_articles)
                search_stats["pubmed_found"] += len(sub_articles)

            await asyncio.sleep(0.4)

    except Exception as e:
        print(f"PubMed search failed: {e}")

    # Step 3: Search Semantic Scholar (broader academic coverage)
    if on_progress:
        await on_progress(30, "Buscando en Semantic Scholar (artículos académicos)...")

    try:
        ss_articles = await semantic.search(query, max_results=max_semantic)
        all_articles.extend(ss_articles)
        search_stats["semantic_scholar_found"] = len(ss_articles)
    except Exception as e:
        print(f"Semantic Scholar search failed: {e}")

    # Step 4: Fallback to web search if few results
    if include_web_fallback and len(all_articles) < 5:
        if on_progress:
            await on_progress(40, "Complementando con fuentes web médicas...")

        try:
            from .web_search import search_duckduckgo, prioritize_medical_sources

            web_results = search_duckduckgo(f"{query} clinical evidence", max_results=8)
            web_results = prioritize_medical_sources(web_results)
            context.web_results = [
                {
                    "title": r.title,
                    "url": r.url,
                    "snippet": r.snippet,
                    "source": r.source,
                }
                for r in web_results
            ]
            search_stats["web_found"] = len(web_results)
        except Exception as e:
            print(f"Web search fallback failed: {e}")

    # Step 5: Deduplicate and prioritize articles
    if on_progress:
        await on_progress(50, "Procesando y clasificando evidencia científica...")

    # Deduplicate by DOI or PMID
    seen_ids = set()
    unique_articles = []
    for article in all_articles:
        article_id = article.doi or article.pmid or article.title.lower()[:50]
        if article_id and article_id not in seen_ids:
            seen_ids.add(article_id)
            unique_articles.append(article)

    # Sort by evidence level and recency
    unique_articles = _sort_by_evidence(unique_articles)
    context.articles = unique_articles[:20]  # Limit to 20 best articles

    # Step 6: Calculate evidence statistics
    for article in context.articles:
        level = article.evidence_level
        if level in [EvidenceLevel.LEVEL_1A, EvidenceLevel.LEVEL_1B]:
            search_stats["high_evidence"] += 1
        elif level in [EvidenceLevel.LEVEL_2A, EvidenceLevel.LEVEL_2B]:
            search_stats["moderate_evidence"] += 1
        else:
            search_stats["low_evidence"] += 1

    context.search_stats = search_stats

    # Step 7: Build evidence summary
    if on_progress:
        await on_progress(60, "Generando resumen de evidencia...")

    context.evidence_summary = _build_evidence_summary(context.articles)

    # Step 8: Synthesize content for LLM
    if on_progress:
        await on_progress(70, "Sintetizando literatura científica...")

    context.synthesized_content = _synthesize_articles(
        context.articles, context.web_results
    )

    if on_progress:
        await on_progress(75, "Preparando análisis final...")

    return context


def _generate_medical_subquestions(query: str) -> list[str]:
    """Generate medically-relevant sub-questions for research."""
    return [
        f"{query} systematic review meta-analysis",
        f"{query} randomized controlled trial RCT",
        f"{query} clinical guidelines recommendations",
        f"{query} treatment therapy efficacy",
        f"{query} diagnosis criteria differential",
        f"{query} pathophysiology mechanism",
        f"{query} prognosis outcomes survival",
    ][:5]


def _sort_by_evidence(articles: list[ScientificArticle]) -> list[ScientificArticle]:
    """Sort articles by evidence level (highest first) and recency."""

    def get_sort_key(article: ScientificArticle):
        # Evidence level priority (lower = better)
        level_priority = {
            EvidenceLevel.LEVEL_1A: 0,
            EvidenceLevel.LEVEL_1B: 1,
            EvidenceLevel.LEVEL_2A: 2,
            EvidenceLevel.LEVEL_2B: 3,
            EvidenceLevel.LEVEL_3A: 4,
            EvidenceLevel.LEVEL_3B: 5,
            EvidenceLevel.LEVEL_4: 6,
            EvidenceLevel.LEVEL_5: 7,
            EvidenceLevel.UNKNOWN: 8,
        }

        evidence_score = level_priority.get(article.evidence_level, 8)

        # Recency bonus (more recent = lower score = better)
        current_year = datetime.now().year
        recency_score = max(0, current_year - article.year) if article.year else 10

        # Citation bonus for Semantic Scholar articles
        citation_score = -min(article.citation_count / 100, 5)  # Capped at 5 bonus

        return (evidence_score, recency_score, citation_score)

    return sorted(articles, key=get_sort_key)


def _build_evidence_summary(articles: list[ScientificArticle]) -> dict:
    """Build a summary of evidence levels found."""
    summary = {
        "total_articles": len(articles),
        "by_level": {},
        "by_source": {"pubmed": 0, "semantic_scholar": 0},
        "recent_articles": 0,  # Last 5 years
        "high_impact": 0,  # >100 citations
    }

    current_year = datetime.now().year

    for article in articles:
        # By level
        level_name = article.evidence_level.code
        summary["by_level"][level_name] = summary["by_level"].get(level_name, 0) + 1

        # By source
        if article.source_api in summary["by_source"]:
            summary["by_source"][article.source_api] += 1

        # Recent
        if article.year and (current_year - article.year) <= 5:
            summary["recent_articles"] += 1

        # High impact
        if article.citation_count > 100:
            summary["high_impact"] += 1

    return summary


def _synthesize_articles(
    articles: list[ScientificArticle], web_results: list[dict] = None
) -> str:
    """Synthesize articles into content for LLM analysis."""
    parts = []

    # Scientific articles
    for i, article in enumerate(articles[:15], 1):
        evidence_tag = f"[{article.evidence_level.quality}]"
        parts.append(
            f"[Ref {i}] {evidence_tag}\n"
            f"Título: {article.title}\n"
            f"Autores: {article.authors_short}\n"
            f"Revista: {article.journal} ({article.year})\n"
            f"Tipo: {article.article_type}\n"
            f"Nivel de evidencia: {article.evidence_level.code} - {article.evidence_level.description}\n"
            f"Abstract: {article.abstract[:500]}...\n"
            f"URL: {article.url}\n"
        )

    # Web results as supplementary
    if web_results:
        parts.append("\n--- FUENTES WEB COMPLEMENTARIAS ---\n")
        for i, result in enumerate(web_results[:5], len(articles) + 1):
            parts.append(
                f"[Web {i}] {result['title']}\n"
                f"Fuente: {result['source']}\n"
                f"Contenido: {result['snippet']}\n"
            )

    return "\n---\n".join(parts)


def build_scientific_research_prompt(
    context: ScientificResearchContext, user_preferences: dict = None
) -> str:
    """
    Build a comprehensive research prompt with scientific context and user preferences.

    This function generates a SOTA-level prompt for academic/doctoral quality research,
    adapting to user's specified format, evidence level, and focus areas.

    Args:
        context: ScientificResearchContext with articles
        user_preferences: Optional dict with user's research preferences:
            - format: "comprehensive" | "clinical" | "summary"
            - include_references: bool
            - evidence_focus: "all" | "high" | "clinical_trials"
            - clarification_answers: dict with specific focus areas

    Returns:
        Prompt string for LLM optimized for academic-quality output
    """
    if user_preferences is None:
        user_preferences = {}

    stats = context.search_stats
    evidence = context.evidence_summary

    # Extract user preferences
    format_pref = user_preferences.get("format", "comprehensive")
    include_refs = user_preferences.get("include_references", True)
    evidence_focus = user_preferences.get("evidence_focus", "all")
    clarification = user_preferences.get("clarification_answers", {})

    # Build evidence quality header
    evidence_header = f"""═══════════════════════════════════════════════════════════════
                    RESUMEN DE BÚSQUEDA CIENTÍFICA
═══════════════════════════════════════════════════════════════
Bases de datos consultadas:
  • PubMed/MEDLINE: {stats.get("pubmed_found", 0)} artículos identificados
  • Semantic Scholar: {stats.get("semantic_scholar_found", 0)} artículos identificados
  • Fuentes web complementarias: {stats.get("web_found", 0)} documentos

Distribución por nivel de evidencia (clasificación Oxford/GRADE):
  • ALTA (Nivel 1a-1b): {stats.get("high_evidence", 0)} estudios
    (Meta-análisis, revisiones sistemáticas, ECAs de alta calidad)
  • MODERADA (Nivel 2a-2b): {stats.get("moderate_evidence", 0)} estudios
    (Estudios de cohorte, ECAs de menor calidad metodológica)
  • BAJA/OTRA (Nivel 3-5): {stats.get("low_evidence", 0)} estudios
    (Casos y controles, series de casos, opinión de expertos)
═══════════════════════════════════════════════════════════════
"""

    # Format-specific instructions
    if format_pref == "comprehensive":
        format_instructions = """
FORMATO SOLICITADO: INFORME ACADÉMICO COMPLETO (Nivel Doctoral)
Extensión mínima: 4000 palabras
Estilo: Académico-científico riguroso, similar a una revisión sistemática publicable
Estructura: Secciones numeradas con subsecciones detalladas
Referencias: Citación in-text obligatoria [Ref N] para cada afirmación empírica
"""
        structure = """
## 1. RESUMEN EJECUTIVO
(Abstract estructurado: Antecedentes, Objetivos, Métodos, Resultados, Conclusiones)
(300-400 palabras)

## 2. INTRODUCCIÓN Y JUSTIFICACIÓN
### 2.1 Definición y Conceptos Fundamentales
### 2.2 Epidemiología Global y Regional
### 2.3 Relevancia Clínica y de Salud Pública
### 2.4 Objetivos de esta Revisión

## 3. METODOLOGÍA DE BÚSQUEDA
### 3.1 Estrategia de Búsqueda
### 3.2 Criterios de Inclusión y Exclusión
### 3.3 Evaluación de Calidad de la Evidencia
### 3.4 Limitaciones Metodológicas

## 4. FISIOPATOLOGÍA Y MECANISMOS
### 4.1 Bases Moleculares y Celulares
### 4.2 Factores Genéticos y Epigenéticos
### 4.3 Interacciones Ambientales
### 4.4 Modelos Fisiopatológicos Actuales

## 5. REVISIÓN CRÍTICA DE LA EVIDENCIA
### 5.1 Meta-análisis y Revisiones Sistemáticas
(Análisis detallado de estudios Nivel 1a)
### 5.2 Ensayos Clínicos Aleatorizados
(Análisis de ECAs principales con tamaño de efecto y NNT cuando aplique)
### 5.3 Estudios Observacionales
(Cohortes y casos-controles relevantes)
### 5.4 Guías de Práctica Clínica
(Recomendaciones de sociedades científicas: AHA, ESC, WHO, etc.)
### 5.5 Síntesis de la Evidencia
(Tabla resumen de hallazgos principales con niveles de evidencia)

## 6. APROXIMACIÓN DIAGNÓSTICA
### 6.1 Criterios Diagnósticos Actuales
### 6.2 Pruebas Diagnósticas: Sensibilidad, Especificidad, VPP, VPN
### 6.3 Algoritmos Diagnósticos Recomendados
### 6.4 Biomarcadores Emergentes

## 7. MANEJO TERAPÉUTICO BASADO EN EVIDENCIA
### 7.1 Tratamiento de Primera Línea
### 7.2 Alternativas Terapéuticas
### 7.3 Terapias Emergentes e Investigacionales
### 7.4 Medicina Personalizada/Precisión
### 7.5 Consideraciones Especiales (poblaciones específicas)

## 8. PRONÓSTICO Y SEGUIMIENTO
### 8.1 Factores Pronósticos Validados
### 8.2 Escalas de Estratificación de Riesgo
### 8.3 Datos de Supervivencia y Outcomes
### 8.4 Protocolos de Seguimiento Recomendados

## 9. DISCUSIÓN CRÍTICA
### 9.1 Síntesis de Hallazgos Principales
### 9.2 Comparación con Revisiones Previas
### 9.3 Heterogeneidad y Calidad de la Evidencia
### 9.4 Áreas de Controversia Actual
### 9.5 Gaps de Conocimiento Identificados

## 10. CONCLUSIONES Y RECOMENDACIONES
### 10.1 Conclusiones Basadas en la Evidencia
### 10.2 Recomendaciones Graduadas (Fuerza A/B/C/D)
### 10.3 Direcciones Futuras de Investigación

## 11. REFERENCIAS BIBLIOGRÁFICAS
(Formato Vancouver, ordenadas por aparición, con DOI/PMID cuando disponible)
"""
    elif format_pref == "clinical":
        format_instructions = """
FORMATO SOLICITADO: SÍNTESIS CLÍNICA PRÁCTICA
Extensión: 2000-2500 palabras
Estilo: Orientado a la toma de decisiones clínicas, tipo UpToDate
Énfasis: Recomendaciones prácticas, algoritmos, tablas de dosificación
"""
        structure = """
## PUNTOS CLAVE (Key Points)
(5-7 bullets con los mensajes más importantes para la práctica)

## DEFINICIÓN Y CLASIFICACIÓN
(Conciso, orientado a la práctica)

## CUÁNDO SOSPECHAR / INDICACIONES
(Red flags, criterios de sospecha)

## EVALUACIÓN DIAGNÓSTICA
### Abordaje Inicial
### Estudios Recomendados
### Diagnóstico Diferencial

## MANEJO
### Tratamiento de Primera Línea
### Alternativas
### Criterios de Referencia a Especialista
### Situaciones Especiales

## SEGUIMIENTO
### Monitorización Recomendada
### Pronóstico

## REFERENCIAS CLAVE
(Solo las 10-15 más relevantes)
"""
    else:  # summary
        format_instructions = """
FORMATO SOLICITADO: RESUMEN EJECUTIVO
Extensión: 800-1200 palabras
Estilo: Bullets y tablas, información condensada
Énfasis: Solo conclusiones principales y recomendaciones clave
"""
        structure = """
## RESUMEN EN UNA ORACIÓN
(La conclusión más importante)

## HALLAZGOS PRINCIPALES
(Bullets con los 5-8 hallazgos más relevantes)

## RECOMENDACIONES CLAVE
(Qué hacer en la práctica, basado en la mejor evidencia)

## ÁREAS DE INCERTIDUMBRE
(Qué no sabemos aún)

## REFERENCIAS
(Top 5 más importantes)
"""

    # Evidence focus instructions
    evidence_instructions = ""
    if evidence_focus == "high":
        evidence_instructions = """
FILTRO DE EVIDENCIA: SOLO ALTA CALIDAD
Prioriza exclusivamente:
- Meta-análisis Cochrane y de alta calidad metodológica
- Ensayos clínicos aleatorizados multicéntricos
- Revisiones sistemáticas con análisis GRADE
Ignora o minimiza: Series de casos, reportes de casos, opiniones de expertos
"""
    elif evidence_focus == "clinical_trials":
        evidence_instructions = """
FILTRO DE EVIDENCIA: ENFOQUE EN ENSAYOS CLÍNICOS
Prioriza:
- Resultados de ECAs (fases II-IV)
- Datos de eficacia y seguridad de estudios pivotales
- Análisis de subgrupos cuando sean relevantes
Incluye: Número de participantes, duración, outcomes primarios y secundarios
"""

    # Build specific focus areas from clarification answers
    focus_areas = []
    if "treatment_focus" in clarification:
        focus_areas.append(f"Enfoque terapéutico: {clarification['treatment_focus']}")
    if "diagnostic_focus" in clarification:
        focus_areas.append(f"Enfoque diagnóstico: {clarification['diagnostic_focus']}")
    if "prognosis_focus" in clarification:
        focus_areas.append(f"Enfoque pronóstico: {clarification['prognosis_focus']}")

    focus_section = ""
    if focus_areas:
        focus_section = f"""
ÁREAS DE ENFOQUE ESPECÍFICAS SOLICITADAS:
{chr(10).join(f"• {area}" for area in focus_areas)}
"""

    # Reference instructions
    ref_instructions = ""
    if include_refs:
        ref_instructions = """
CITACIÓN OBLIGATORIA:
- Cada afirmación empírica debe ir acompañada de [Ref N]
- Incluir DOI o PMID cuando estén disponibles
- Formato Vancouver para la bibliografía final
- Indicar nivel de evidencia junto a hallazgos importantes: [Ref N, Evidencia 1a]
"""
    else:
        ref_instructions = """
REFERENCIAS: Minimizadas, solo mencionar fuentes principales en texto
"""

    # Final comprehensive prompt
    prompt = f"""═══════════════════════════════════════════════════════════════
     SISTEMA DE INVESTIGACIÓN MÉDICA AVANZADA - MedeX Alpha
             Análisis Sistemático de Literatura Científica
═══════════════════════════════════════════════════════════════

Eres un investigador médico senior con formación doctoral y experiencia en:
- Metodología de revisiones sistemáticas (Cochrane, PRISMA)
- Evaluación crítica de literatura médica (GRADE, Oxford CEBM)
- Medicina basada en evidencia
- Redacción científica de alto nivel

TEMA DE INVESTIGACIÓN:
"{context.query}"

{evidence_header}
{format_instructions}
{evidence_instructions}
{focus_section}
{ref_instructions}

═══════════════════════════════════════════════════════════════
                    LITERATURA RECOPILADA
═══════════════════════════════════════════════════════════════
{context.synthesized_content}

═══════════════════════════════════════════════════════════════
              SUB-PREGUNTAS DE INVESTIGACIÓN
═══════════════════════════════════════════════════════════════
{chr(10).join(f"• {q}" for q in context.sub_questions)}

═══════════════════════════════════════════════════════════════
                ESTRUCTURA DEL INFORME
═══════════════════════════════════════════════════════════════
{structure}

═══════════════════════════════════════════════════════════════
             ESTÁNDARES DE CALIDAD OBLIGATORIOS
═══════════════════════════════════════════════════════════════
1. RIGOR CIENTÍFICO: Usa terminología médica precisa y actual
2. HONESTIDAD EPISTÉMICA: Indica explícitamente cuando la evidencia es:
   - Limitada o insuficiente
   - Contradictoria o heterogénea
   - Basada en estudios de baja calidad
3. EQUILIBRIO: Presenta múltiples perspectivas cuando exista controversia
4. ACTUALIDAD: Prioriza literatura de los últimos 5 años cuando sea relevante
5. APLICABILIDAD: Indica la generalizabilidad de los hallazgos
6. NO inventes datos, cifras o referencias
7. NO uses emojis, símbolos decorativos ni lenguaje coloquial
8. Mantén tono científico-académico consistente

═══════════════════════════════════════════════════════════════
                    GENERA EL INFORME
═══════════════════════════════════════════════════════════════
"""

    return prompt


def format_scientific_sources(articles: list[ScientificArticle]) -> list[dict]:
    """Format articles for UI display with evidence indicators."""
    formatted = []

    for i, article in enumerate(articles, 1):
        # Evidence badge color
        level = article.evidence_level
        if level in [EvidenceLevel.LEVEL_1A, EvidenceLevel.LEVEL_1B]:
            badge_color = "#22c55e"  # Green
            badge_text = "Alta"
        elif level in [EvidenceLevel.LEVEL_2A, EvidenceLevel.LEVEL_2B]:
            badge_color = "#eab308"  # Yellow
            badge_text = "Moderada"
        elif level in [
            EvidenceLevel.LEVEL_3A,
            EvidenceLevel.LEVEL_3B,
            EvidenceLevel.LEVEL_4,
        ]:
            badge_color = "#f97316"  # Orange
            badge_text = "Baja"
        else:
            badge_color = "#6b7280"  # Gray
            badge_text = "N/D"

        formatted.append(
            {
                "number": i,
                "title": article.title[:100],
                "authors": article.authors_short,
                "journal": article.journal or "N/A",
                "year": article.year or "N/A",
                "url": article.url,
                "evidence_level": level.code,
                "evidence_description": level.description,
                "evidence_quality": badge_text,
                "badge_color": badge_color,
                "citation_vancouver": article.citation_vancouver,
                "source_api": article.source_api.upper(),
                "pmid": article.pmid,
                "doi": article.doi,
                "citation_count": article.citation_count,
            }
        )

    return formatted
