# ADR-0004: Deep Research Gap Analysis — Estado Actual vs Arquitectura CDR

**Fecha:** 2025-01-XX  
**Estado:** Draft  
**Autor:** Claude (análisis técnico)  
**Contexto:** Auditoría completa del módulo Deep Research en MedeX para identificar brechas con la arquitectura CDR objetivo.

---

## 1. Executive Summary

La implementación actual de Deep Research en MedeX es funcional pero **fundamentalmente diferente** de la arquitectura CDR (Clinical Deep Research) propuesta. El sistema actual es un **buscador con síntesis LLM**, mientras que CDR es un **sistema de investigación estructurado con trazabilidad total**.

### Veredicto

| Aspecto                 | Actual                                       | CDR Target                                 | Gap        |
| ----------------------- | -------------------------------------------- | ------------------------------------------ | ---------- |
| Arquitectura            | Monolítica, un paso                          | 11 capas orquestadas                       | 🔴 Crítico |
| Trazabilidad            | Ninguna (afirmaciones sin fuente específica) | Total (cada claim con snippet verificable) | 🔴 Crítico |
| Extracción estructurada | No existe                                    | StudyCards con PICO                        | 🔴 Crítico |
| Evaluación de sesgo     | No existe                                    | RoB2 formal                                | 🔴 Crítico |
| Verificación            | No existe                                    | Capa de verificación obligatoria           | 🔴 Crítico |
| Orquestación            | Secuencial simple                            | Grafo con estados y gates                  | 🔴 Crítico |
| Fuentes                 | PubMed + Semantic Scholar                    | PubMed + ClinicalTrials.gov + Full-text    | 🟡 Parcial |
| Retrieval               | Keyword simple                               | Hybrid (BM25 + Dense + Rerank)             | 🔴 Crítico |
| Output                  | Texto libre del LLM                          | Report estructurado con claims verificados | 🔴 Crítico |

**Conclusión:** Se requiere una **reimplementación completa**, preservando solo algunos componentes básicos de retrieval como punto de partida.

---

## 2. Análisis Detallado por Componente

### 2.1 Capa de Orquestación

#### Estado Actual

```
scientific_search.py → perform_scientific_research()
│
├── PubMedClient.search() → PMIDs
├── PubMedClient.fetch_articles() → XML parsing
├── SemanticScholarClient.search()
├── [Optional] DuckDuckGo fallback
├── Deduplicate + Sort by evidence
└── Build prompt → Call LLM → Return text

state.py → start_research()
│
├── Llama a perform_scientific_research()
├── Construye prompt con build_scientific_research_prompt()
├── POST a /api/v1/query
└── Muestra resultado como texto
```

**Problemas:**

- Flujo secuencial sin checkpoints
- Sin estado persistente entre pasos
- Sin capacidad de retry/rollback
- Sin gates de validación
- Sin paralelización controlada

#### Arquitectura CDR Requerida (LangGraph)

```
                    ┌─────────────────┐
                    │   INTERFACE     │
                    │  (Question In)  │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
            ┌──────►│  ORCHESTRATION  │◄──────┐
            │       │   (LangGraph)   │       │
            │       └────────┬────────┘       │
            │                │                │
            │       ┌────────▼────────┐       │
            │       │  PICO GATE ✓    │       │
            │       └────────┬────────┘       │
       RETRY│                │                │VERIFY
            │       ┌────────▼────────┐       │FAIL
            │       │    RETRIEVAL    │       │
            │       │ BM25+Dense+Rerank│      │
            │       └────────┬────────┘       │
            │                │                │
            │       ┌────────▼────────┐       │
            │       │   SCREENING     │       │
            │       │  (In/Exclude)   │       │
            │       └────────┬────────┘       │
            │                │                │
            │       ┌────────▼────────┐       │
            │       │    PARSING      │       │
            │       │ (Snippet Extract)│      │
            │       └────────┬────────┘       │
            │                │                │
            │       ┌────────▼────────┐       │
            │       │   STUDYCARDS    │       │
            │       │ (PICO Extract)  │       │
            │       └────────┬────────┘       │
            │                │                │
            │       ┌────────▼────────┐       │
            │       │     ROB2        │       │
            │       │ (Bias Assess)   │       │
            │       └────────┬────────┘       │
            │                │                │
            │       ┌────────▼────────┐       │
            │       │    SKEPTIC      │       │
            │       │ (Challenge)     │       │
            │       └────────┬────────┘       │
            │                │                │
            │       ┌────────▼────────┐       │
            │       │   SYNTHESIS     │       │
            │       │ (Generate Claims)│      │
            │       └────────┬────────┘       │
            │                │                │
            │       ┌────────▼────────┐       │
            └───────│  VERIFICATION   │───────┘
                    │  (Fact Check)   │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │   PUBLISHER     │
                    │ (Report + Traces)│
                    └─────────────────┘
```

**Gap:** 🔴 CRÍTICO — No existe orquestación. Flujo lineal sin estados.

---

### 2.2 Capa de Retrieval

#### Estado Actual

**PubMedClient (scientific_search.py:109-275)**

```python
class PubMedClient:
    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

    async def search(query, max_results=10) -> list[str]:  # PMIDs
        # Simple keyword search
        params = {"db": "pubmed", "term": query, "retmax": max_results}

    async def fetch_articles(pmids) -> list[ScientificArticle]:
        # XML parsing of abstracts only
```

**Problemas:**

- Solo keyword search, no query expansion
- No BM25 scoring
- No embeddings/vector search
- No reranking
- No full-text retrieval (solo abstracts)
- No ClinicalTrials.gov
- No MeSH term expansion

#### Arquitectura CDR Requerida

```python
class HybridRetriever:
    """Retrieval pipeline: BM25 + Dense + Reranker"""

    def __init__(self):
        self.bm25 = BM25Index()
        self.dense = DenseRetriever(model="PubMedBERT")
        self.reranker = CrossEncoder("ms-marco-MiniLM")

    async def retrieve(self, query: str, pico: PICOQuery) -> list[Record]:
        # 1. Expand query with MeSH terms
        expanded = await self.mesh_expand(query)

        # 2. BM25 retrieval (title + abstract)
        bm25_results = self.bm25.search(expanded, k=100)

        # 3. Dense retrieval (semantic similarity)
        dense_results = self.dense.search(query, k=100)

        # 4. Fusion (RRF or weighted)
        fused = self.reciprocal_rank_fusion(bm25_results, dense_results)

        # 5. Rerank top candidates
        reranked = self.reranker.rerank(query, fused[:50])

        return reranked[:20]  # Top 20 with scores
```

**Gap:** 🔴 CRÍTICO — Solo keyword search, sin hybrid retrieval.

---

### 2.3 Modelo de Datos

#### Estado Actual (scientific_search.py)

```python
@dataclass
class ScientificArticle:
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
    source_api: str = ""
```

**Problemas:**

- No hay estructura PICO
- No hay snippets con posición
- No hay scoring de retrieval
- No hay hash para deduplicación confiable
- No hay NCT IDs para clinical trials
- No hay distinction entre record y study card

#### Arquitectura CDR Requerida (Pydantic)

```python
from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum

class Record(BaseModel):
    """Raw retrieved record before processing"""
    record_id: str = Field(..., description="Unique ID: PMID, NCT, or DOI")
    title: str
    authors: list[str]
    year: int
    doi: Optional[str] = None
    pmid: Optional[str] = None
    nct_id: Optional[str] = None
    abstract: str
    full_text: Optional[str] = None
    url: str
    source: Literal["pubmed", "clinicaltrials", "semantic_scholar"]
    hash: str = Field(..., description="SHA256 of title+abstract for dedup")
    retrieval_scores: dict[str, float] = Field(
        default_factory=dict,
        description="bm25_score, dense_score, rerank_score"
    )

class Snippet(BaseModel):
    """Extracted text fragment with location"""
    text: str
    record_id: str
    location: str  # "abstract:sentence_3" or "fulltext:section_methods:para_2"
    char_start: int
    char_end: int

class StudyCard(BaseModel):
    """Structured extraction from a study"""
    record_id: str
    study_type: StudyType  # RCT, Cohort, CaseControl, etc.

    # PICO extracted
    population: str
    intervention: str
    comparator: Optional[str]
    outcomes: list[str]

    # Results
    sample_size: Optional[int]
    follow_up: Optional[str]
    primary_endpoint: Optional[str]
    effect_size: Optional[str]
    confidence_interval: Optional[str]
    p_value: Optional[str]

    # Supporting evidence
    supporting_snippets: list[Snippet]

    # Quality
    evidence_level: EvidenceLevel
    rob2_result: Optional[RoB2Result]

class EvidenceClaim(BaseModel):
    """A claim with mandatory source attribution"""
    claim_text: str
    source_refs: list[str]  # List of record_ids
    supporting_snippets: list[Snippet]
    confidence: float  # 0-1
    uncertainty_note: Optional[str]

class CDRState(BaseModel):
    """Complete state of a CDR session"""
    session_id: str
    question: str
    pico: Optional[PICOQuery]
    search_plan: Optional[SearchPlan]
    retrieved_records: list[Record] = []
    screened: ScreeningResult = None
    study_cards: list[StudyCard] = []
    rob2_results: list[RoB2Result] = []
    claims: list[EvidenceClaim] = []
    answer: Optional[str] = None
    report: Optional[str] = None
    traces: list[TraceEntry] = []

    # Metadata
    created_at: datetime
    updated_at: datetime
    status: SessionStatus
```

**Gap:** 🔴 CRÍTICO — Modelo de datos plano sin estructura PICO, sin snippets, sin claims verificables.

---

### 2.4 Extracción Estructurada (StudyCards)

#### Estado Actual

**NO EXISTE.** Los artículos se pasan como texto plano al LLM que genera un resumen libre.

```python
# scientific_search.py línea ~720
def _synthesize_articles(articles, web_results):
    """Synthesize articles into content for LLM analysis."""
    parts = []
    for i, article in enumerate(articles[:15], 1):
        parts.append(
            f"[Ref {i}] {evidence_tag}\n"
            f"Título: {article.title}\n"
            f"Abstract: {article.abstract[:500]}...\n"  # TRUNCADO!
        )
    return "\n---\n".join(parts)
```

**Problemas:**

- Abstracts truncados a 500 chars
- Sin extracción de PICO
- Sin extracción de resultados numéricos
- Sin identificación de endpoints
- Sin vinculación snippet→claim

#### Arquitectura CDR Requerida (DSPy)

```python
import dspy

class StudyCardExtractor(dspy.Signature):
    """Extract structured study information from abstract/full-text."""

    text: str = dspy.InputField()
    study_type: str = dspy.OutputField(desc="RCT, Cohort, CaseControl, etc.")
    population: str = dspy.OutputField(desc="Study population characteristics")
    intervention: str = dspy.OutputField(desc="Main intervention/exposure")
    comparator: str = dspy.OutputField(desc="Control/comparison group")
    outcomes: list[str] = dspy.OutputField(desc="Measured outcomes")
    sample_size: int = dspy.OutputField(desc="Number of participants")
    main_finding: str = dspy.OutputField(desc="Primary result with numbers")

class ExtractorModule(dspy.Module):
    def __init__(self):
        self.extractor = dspy.ChainOfThought(StudyCardExtractor)

    def forward(self, record: Record) -> StudyCard:
        result = self.extractor(text=record.abstract)
        return StudyCard(
            record_id=record.record_id,
            study_type=result.study_type,
            population=result.population,
            intervention=result.intervention,
            # ... etc
        )
```

**Gap:** 🔴 CRÍTICO — No existe extracción estructurada.

---

### 2.5 Evaluación de Sesgo (RoB2)

#### Estado Actual

```python
# Clasificación básica por tipo de publicación (líneas 278-330)
def _classify_evidence(self, pub_types: list[str], title: str) -> EvidenceLevel:
    """Classify article evidence level based on publication type."""
    if any(t in " ".join(pub_types_lower) for t in ["meta-analysis", "systematic review"]):
        return EvidenceLevel.LEVEL_1A
    if "randomized controlled trial" in " ".join(pub_types_lower):
        return EvidenceLevel.LEVEL_1B
    # ... heurísticas simples basadas en keywords
```

**Problemas:**

- Solo usa tipo de publicación y título
- No evalúa riesgo de sesgo real
- No sigue metodología Cochrane RoB2
- No considera dominios de sesgo específicos

#### Arquitectura CDR Requerida

```python
class RoB2Domain(str, Enum):
    RANDOMIZATION = "D1: Randomization process"
    DEVIATIONS = "D2: Deviations from intended interventions"
    MISSING_DATA = "D3: Missing outcome data"
    MEASUREMENT = "D4: Measurement of the outcome"
    SELECTION = "D5: Selection of the reported result"

class RoB2Assessment(BaseModel):
    domain: RoB2Domain
    judgment: Literal["low", "some_concerns", "high"]
    support_text: str
    supporting_quotes: list[Snippet]

class RoB2Result(BaseModel):
    record_id: str
    domain_assessments: list[RoB2Assessment]
    overall_risk: Literal["low", "some_concerns", "high"]
    justification: str

class RoB2Assessor(dspy.Module):
    """Assess risk of bias following Cochrane RoB2 methodology."""

    def assess_domain(self, study_card: StudyCard, domain: RoB2Domain) -> RoB2Assessment:
        # Structured prompting for each domain
        pass

    def assess_overall(self, study_card: StudyCard) -> RoB2Result:
        assessments = [self.assess_domain(study_card, d) for d in RoB2Domain]
        # Overall = highest risk among domains
        pass
```

**Gap:** 🔴 CRÍTICO — No existe evaluación de sesgo formal.

---

### 2.6 Capa de Verificación

#### Estado Actual

**NO EXISTE.** El LLM genera texto libre sin verificación.

```python
# El resultado final es simplemente lo que devuelve el LLM
response = await client.post(
    f"{self.api_url}/api/v1/query",
    json={"query": research_prompt, ...}
)
self.research_result = data.get("response", "")  # Texto sin verificar
```

#### Arquitectura CDR Requerida

```python
class Verifier:
    """Verify that each claim has supporting evidence."""

    def verify_claim(self, claim: EvidenceClaim, study_cards: list[StudyCard]) -> VerificationResult:
        # 1. Find supporting snippets
        supporting = self.find_supporting_evidence(claim, study_cards)

        # 2. Check consistency
        consistent = self.check_consistency(claim.claim_text, supporting)

        # 3. Check numerical accuracy
        numbers_ok = self.verify_numbers(claim, supporting)

        return VerificationResult(
            claim=claim,
            verified=consistent and numbers_ok,
            supporting_evidence=supporting,
            issues=self.collect_issues()
        )

    def verify_all(self, claims: list[EvidenceClaim], study_cards: list[StudyCard]) -> list[VerificationResult]:
        results = [self.verify_claim(c, study_cards) for c in claims]
        # Gate: Si >20% claims no verificados, FAIL
        verified_ratio = sum(1 for r in results if r.verified) / len(results)
        if verified_ratio < 0.8:
            raise VerificationGateFailure(f"Only {verified_ratio:.0%} claims verified")
        return results
```

**Gap:** 🔴 CRÍTICO — No existe verificación de afirmaciones.

---

### 2.7 Capa de Síntesis

#### Estado Actual

```python
# El prompt pide al LLM generar todo el contenido (líneas 750-1000)
prompt = f"""
...
TEMA DE INVESTIGACIÓN:
"{context.query}"

LITERATURA RECOPILADA:
{context.synthesized_content}

ESTRUCTURA DEL INFORME:
{structure}  # Secciones sugeridas

GENERA EL INFORME
"""
# El LLM genera TODAS las afirmaciones sin constraint de trazabilidad
```

**Problemas:**

- El LLM puede inventar información
- No hay vinculación obligatoria claim→source
- No hay cuantificación de incertidumbre
- No hay síntesis jerárquica (por outcome)

#### Arquitectura CDR Requerida

```python
class ClaimGenerator(dspy.Module):
    """Generate evidence-backed claims with mandatory citations."""

    def generate_claim(
        self,
        question: str,
        study_cards: list[StudyCard],
        outcome: str
    ) -> EvidenceClaim:
        # Solo puede generar claims basados en snippets existentes
        relevant_cards = [c for c in study_cards if outcome in c.outcomes]

        if not relevant_cards:
            return EvidenceClaim(
                claim_text=f"No se encontró evidencia sobre {outcome}",
                source_refs=[],
                supporting_snippets=[],
                confidence=0.0,
                uncertainty_note="Sin estudios identificados"
            )

        # Synthesize with mandatory attribution
        claim = self.synthesize_with_citations(relevant_cards)
        claim.supporting_snippets = self.extract_supporting_snippets(relevant_cards)

        return claim

class Synthesizer:
    """Orchestrate claim generation and assembly."""

    def synthesize(self, state: CDRState) -> list[EvidenceClaim]:
        # 1. Identify outcomes to address
        outcomes = self.identify_outcomes(state.pico, state.study_cards)

        # 2. Generate claim per outcome
        claims = []
        for outcome in outcomes:
            claim = self.claim_generator.generate_claim(
                state.question, state.study_cards, outcome
            )
            claims.append(claim)

        # 3. Add uncertainty and limitations
        claims = self.add_uncertainty_notes(claims)

        return claims
```

**Gap:** 🔴 CRÍTICO — Síntesis libre sin trazabilidad.

---

### 2.8 Output/Publisher

#### Estado Actual

```python
# PDF export básico (pdf_export.py)
def generate_research_pdf(query, result, sources, steps, user_mode):
    # Genera PDF con el texto libre del LLM
    # No hay estructura de claims verificados
    # No hay traces de decisiones
```

**Problemas:**

- Output es texto libre
- No hay PRISMA flow diagram
- No hay tabla de evidencia estructurada
- No hay sección de traces/auditoría

#### Arquitectura CDR Requerida

```python
class ReportPublisher:
    """Generate final report with full traceability."""

    def generate_report(self, state: CDRState) -> Report:
        return Report(
            title=f"Systematic Review: {state.question}",
            sections=[
                self.generate_abstract(state),
                self.generate_methods(state),
                self.generate_prisma_diagram(state),
                self.generate_evidence_table(state),
                self.generate_findings(state.claims),
                self.generate_discussion(state),
                self.generate_conclusions(state),
                self.generate_references(state),
                self.generate_appendix_traces(state),
            ],
            metadata=ReportMetadata(
                generated_at=datetime.now(),
                search_date=state.search_plan.executed_at,
                databases_searched=state.search_plan.sources,
                total_records=len(state.retrieved_records),
                included_studies=len(state.study_cards),
            )
        )

    def generate_evidence_table(self, state: CDRState) -> Section:
        """Table with Study, PICO, Findings, RoB2 per study."""
        rows = []
        for card in state.study_cards:
            rows.append({
                "study": f"{card.authors[0]} {card.year}",
                "design": card.study_type,
                "n": card.sample_size,
                "intervention": card.intervention,
                "comparator": card.comparator,
                "outcome": card.primary_endpoint,
                "result": card.effect_size,
                "rob2": card.rob2_result.overall_risk if card.rob2_result else "N/A"
            })
        return Section(type="evidence_table", data=rows)
```

**Gap:** 🔴 CRÍTICO — Output no estructurado sin tabla de evidencia ni traces.

---

## 3. Componentes Reutilizables vs Reescribir

### 3.1 Reutilizable (con modificaciones)

| Componente          | Archivo                | Adaptación Necesaria                  |
| ------------------- | ---------------------- | ------------------------------------- |
| PubMed API client   | `scientific_search.py` | Añadir MeSH expansion, batch fetching |
| Evidence level enum | `scientific_search.py` | Expandir con más tipos                |
| DuckDuckGo fallback | `web_search.py`        | Mantener como fallback tier-3         |
| PDF export base     | `pdf_export.py`        | Adaptar para estructura de Report     |
| UI research panel   | `app.py`               | Refactorizar para nuevos estados      |

### 3.2 Descartar y Reescribir

| Componente                           | Razón                                          |
| ------------------------------------ | ---------------------------------------------- |
| `ScientificArticle` dataclass        | Reemplazar con `Record` + `StudyCard` Pydantic |
| `ScientificResearchContext`          | Reemplazar con `CDRState`                      |
| `perform_scientific_research()`      | Reemplazar con LangGraph orchestration         |
| `build_scientific_research_prompt()` | No aplica en nueva arquitectura                |
| `_synthesize_articles()`             | Reemplazar con extracción estructurada         |
| `start_research()` en state.py       | Adaptar para invocar nuevo engine              |

---

## 4. Tecnologías Faltantes (Instalación Requerida)

```bash
# Core orchestration
pip install langgraph langchain-core

# Hybrid retrieval
pip install rank-bm25 faiss-cpu sentence-transformers

# Structured extraction
pip install dspy-ai

# Evaluation
pip install ragas

# Clinical sources
pip install biopython  # For enhanced NCBI access

# Tracing/observability
pip install opentelemetry-api opentelemetry-sdk
```

---

## 5. Plan de Implementación Propuesto

### Fase 1: Foundation (Semana 1-2)

- [ ] Definir Pydantic schemas (`Record`, `StudyCard`, `EvidenceClaim`, `CDRState`)
- [ ] Configurar LangGraph base con estados mínimos
- [ ] Implementar `PICOExtractor` con DSPy
- [ ] Tests unitarios de schemas

### Fase 2: Retrieval (Semana 2-3)

- [ ] Implementar BM25 index
- [ ] Integrar PubMedBERT embeddings
- [ ] Implementar reranker (cross-encoder)
- [ ] Añadir ClinicalTrials.gov connector
- [ ] Tests de retrieval quality

### Fase 3: Extraction (Semana 3-4)

- [ ] Implementar `StudyCardExtractor` con DSPy
- [ ] Implementar `SnippetExtractor`
- [ ] Implementar `RoB2Assessor`
- [ ] Tests de extracción

### Fase 4: Synthesis & Verification (Semana 4-5)

- [ ] Implementar `ClaimGenerator`
- [ ] Implementar `Verifier` con gates
- [ ] Implementar `Skeptic` layer
- [ ] Tests de verificación

### Fase 5: Integration (Semana 5-6)

- [ ] Integrar todas las capas en LangGraph
- [ ] Implementar `ReportPublisher`
- [ ] Conectar con UI existente
- [ ] End-to-end tests

### Fase 6: Observability & Polish (Semana 6-7)

- [ ] Añadir OpenTelemetry tracing
- [ ] Implementar RAGAs evaluation
- [ ] Optimizar prompts
- [ ] Documentation

---

## 6. Riesgos y Mitigaciones

| Riesgo                   | Probabilidad | Impacto | Mitigación                               |
| ------------------------ | ------------ | ------- | ---------------------------------------- |
| LangGraph learning curve | Media        | Alto    | Empezar con grafo simple, iterar         |
| DSPy instability         | Media        | Medio   | Tener fallback a prompts manuales        |
| PubMed rate limits       | Baja         | Medio   | Implementar caching agresivo             |
| Latencia end-to-end      | Alta         | Alto    | Paralelizar donde sea posible, streaming |
| Costo de embeddings      | Media        | Bajo    | Usar modelos open-source                 |

---

## 7. Decisión

**Propuesta:** Reimplementación completa del módulo Deep Research siguiendo la arquitectura CDR, preservando solo los conectores de API básicos y la estructura de UI.

**Justificación técnica:**

1. La arquitectura actual es fundamentalmente incompatible con los requisitos de trazabilidad
2. El costo de adaptar supera el de reescribir
3. Las nuevas dependencias (LangGraph, DSPy) requieren patrones diferentes
4. La calidad SOTA requiere foundation sólido, no parches

**Próximos pasos:**

1. Aprobar este análisis
2. Definir prioridad de fases
3. Comenzar con Fase 1 (schemas + LangGraph base)

---

## Apéndice A: Archivos Actuales Analizados

```
ui/medex_ui/
├── scientific_search.py  (1092 líneas) - PubMed + Semantic Scholar clients
├── web_search.py         (343 líneas)  - DuckDuckGo fallback
├── state.py              (2935 líneas) - start_research(), clarification flow
├── app.py                (3844 líneas) - research_panel() UI
└── pdf_export.py         (~700 líneas) - PDF generation
```

## Apéndice B: Arquitectura CDR Target (resumen visual)

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CDR ARCHITECTURE                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  User Question ──► PICO Gate ──► Search Plan ──► Hybrid Retrieval  │
│                         │                              │            │
│                         ▼                              ▼            │
│                    [Fails if              BM25 + Dense + Rerank    │
│                     not PICO]                     │                │
│                                                   ▼                │
│                                              Screening             │
│                                                   │                │
│                                                   ▼                │
│                                           StudyCard Extract        │
│                                           (PICO, Results, N)       │
│                                                   │                │
│                                                   ▼                │
│                                              RoB2 Assess           │
│                                                   │                │
│                                                   ▼                │
│                                               Skeptic              │
│                                          (Challenge findings)      │
│                                                   │                │
│                                                   ▼                │
│                                              Synthesis             │
│                                         (Claims + Snippets)        │
│                                                   │                │
│                                                   ▼                │
│                                            Verification            │
│                                         (Fact check claims)        │
│                                                   │                │
│                                                   ▼                │
│                                              Publisher              │
│                                    (Report + Evidence Table +      │
│                                     PRISMA + Traces)               │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

_Documento generado durante auditoría de código. Sujeto a revisión y aprobación._
