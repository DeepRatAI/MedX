# MedeX - Technical Documentation

**Version:** 25.83  
**Last Updated:** January 2026  
**Status:** Production Ready

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Architecture](#2-architecture)
3. [Knowledge Base Module](#3-knowledge-base-module)
4. [Medical Ontology](#4-medical-ontology)
5. [RAG SOTA Implementation](#5-rag-sota-implementation)
6. [User Interface](#6-user-interface)
7. [API Reference](#7-api-reference)
8. [Configuration](#8-configuration)
9. [Testing](#9-testing)
10. [Deployment](#10-deployment)

---

## 1. System Overview

MedeX is a professional medical AI assistant system designed for healthcare professionals and medical education. The system combines:

- **Intelligent User Detection**: Automatic classification of queries as professional or educational
- **Emergency Recognition**: Real-time detection of urgent medical situations
- **Medical Knowledge Base**: 38 clinical conditions across 6 specialties
- **Medical Ontology**: 1,856+ mapped terms for query expansion
- **RAG SOTA Architecture**: State-of-the-art retrieval-augmented generation

### 1.1 Key Metrics

| Component             | Count | Coverage                                |
| --------------------- | ----- | --------------------------------------- |
| Medical Conditions    | 38    | 6 specialties                           |
| Medications           | 29    | 7 therapeutic categories                |
| Ontology Terms        | 1,856 | Symptoms, conditions, drugs, procedures |
| Symptom Synonyms      | 68    | Spanish medical terminology             |
| Condition Synonyms    | 77    | ICD-10 aligned                          |
| Medication Synonyms   | 136   | ATC classified                          |
| Medical Abbreviations | 150   | Clinical acronyms                       |
| Anatomical Terms      | 44    | Body systems                            |
| Procedure Terms       | 74    | Diagnostic and therapeutic              |

### 1.2 Standards Compliance

- **ICD-10-CM 2026**: International Classification of Diseases
- **WHO ATC**: Anatomical Therapeutic Chemical Classification
- **SNOMED-CT**: Systematized Nomenclature of Medicine

---

## 2. Architecture

### 2.1 Component Diagram

```
+------------------+     +-------------------+     +------------------+
|   Streamlit UI   |---->|   MedeX Engine    |---->|   LLM Provider   |
|  (streamlit_app) |     |  (MEDEX_FINAL)    |     | (Moonshot/HF)    |
+------------------+     +-------------------+     +------------------+
         |                        |
         v                        v
+------------------+     +-------------------+
| Knowledge Base   |     | Medical Ontology  |
|   (knowledge/)   |     | (medical_ontology)|
+------------------+     +-------------------+
         |                        |
         v                        v
+------------------+     +-------------------+
|  RAG SOTA Layer  |<----|  Query Expansion  |
| (medical_rag_sota)|    |   (Synonyms)      |
+------------------+     +-------------------+
```

### 2.2 File Structure

```
MedeX/
├── MEDEX_FINAL.py           # Main engine (MedeXv2583)
├── medical_ontology.py      # Medical terminology ontology
├── medical_rag_sota.py      # RAG SOTA implementation
├── streamlit_app.py         # Web interface
├── knowledge/               # Medical knowledge base
│   ├── __init__.py          # Integration module
│   ├── conditions_cardiovascular.py
│   ├── conditions_respiratory.py
│   ├── conditions_gastrointestinal.py
│   ├── conditions_infectious.py
│   ├── conditions_emergency.py
│   ├── conditions_neurological.py
│   └── medications_database.py
├── medex/                   # Provider system
│   └── providers/
│       ├── manager.py
│       ├── moonshot.py
│       └── huggingface.py
├── tests/                   # Test suite
│   ├── test_detection.py
│   └── test_engine.py
└── docs/                    # Documentation
```

### 2.3 Data Flow

1. **User Input** → Streamlit UI receives query
2. **User Detection** → Classify as Professional/Educational
3. **Emergency Detection** → Check for urgent keywords
4. **Query Expansion** → Ontology expands with synonyms
5. **Knowledge Retrieval** → RAG retrieves relevant context
6. **Response Generation** → LLM generates response
7. **Post-Processing** → Format and present to user

---

## 3. Knowledge Base Module

### 3.1 Module Location

```
knowledge/
├── __init__.py
├── conditions_cardiovascular.py
├── conditions_respiratory.py
├── conditions_gastrointestinal.py
├── conditions_infectious.py
├── conditions_emergency.py
├── conditions_neurological.py
└── medications_database.py
```

### 3.2 Condition Data Model

```python
@dataclass
class MedicalCondition:
    name: str                    # Condition name
    icd10_code: str              # ICD-10-CM code
    category: str                # Medical specialty
    description: str             # Clinical description
    symptoms: list[str]          # Common symptoms
    red_flags: list[str]         # Warning signs
    differential_diagnosis: list[str]  # DDx list
    initial_workup: list[str]    # Diagnostic studies
    treatment_principles: list[str]    # Management
    medications: list[str]       # Common medications
    complications: list[str]     # Potential complications
    patient_education: list[str] # Patient guidance
```

### 3.3 Medication Data Model

```python
@dataclass
class Medication:
    generic_name: str            # Generic name
    brand_names: list[str]       # Trade names
    drug_class: str              # Therapeutic class
    atc_code: str                # ATC classification
    mechanism: str               # Mechanism of action
    indications: list[str]       # Approved uses
    contraindications: list[str] # Contraindications
    dosing: dict                 # Dosing information
    side_effects: list[str]      # Adverse effects
    interactions: list[str]      # Drug interactions
    monitoring: list[str]        # Required monitoring
    special_populations: dict    # Pregnancy, renal, hepatic
```

### 3.4 Conditions by Specialty

| Specialty        | Count | Example Conditions                 |
| ---------------- | ----- | ---------------------------------- |
| Cardiovascular   | 6     | ICC, FA, TEP, TVP, Endocarditis    |
| Respiratory      | 7     | EPOC, Asma, IRA, NAC, TB           |
| Gastrointestinal | 7     | Apendicitis, Colecistitis, HDA     |
| Infectious       | 7     | Sepsis, ITU, Meningitis, COVID-19  |
| Emergency        | 5     | Paro cardíaco, Anafilaxia, CAD     |
| Neurological     | 6     | ACV, Epilepsia, Parkinson, Migraña |

### 3.5 API Functions

```python
# Get all conditions
from knowledge import get_all_conditions
conditions = get_all_conditions()

# Search by text
from knowledge import search_conditions
results = search_conditions("diabetes")

# Get by ICD-10 code
from knowledge import get_condition_by_icd10
condition = get_condition_by_icd10("I50.9")

# Filter by category
from knowledge import get_conditions_by_category
cardio = get_conditions_by_category("Cardiovascular")

# Search medications
from knowledge.medications_database import search_medications
meds = search_medications("metformina")
```

---

## 4. Medical Ontology

### 4.1 Overview

The Medical Ontology module (`medical_ontology.py`) provides comprehensive Spanish medical terminology mapping for query expansion and normalization.

### 4.2 Ontology Categories

| Category             | Terms | Purpose                           |
| -------------------- | ----- | --------------------------------- |
| `symptom_synonyms`   | 68    | Map colloquial to medical terms   |
| `condition_synonyms` | 77    | Disease name variations           |
| `drug_synonyms`      | 136   | Medication name mappings          |
| `abbreviations`      | 150   | Medical acronym expansion         |
| `anatomy_synonyms`   | 44    | Body structure terms              |
| `procedure_synonyms` | 74    | Diagnostic/therapeutic procedures |
| `emergency_keywords` | 42    | Urgent situation detection        |

### 4.3 Key Methods

```python
from medical_ontology import MedicalOntology

ontology = MedicalOntology()

# Expand query with synonyms
expanded = ontology.expand_query("dolor de pecho", max_expansions=5)
# Returns: ["dolor de pecho", "dolor torácico", "dolor precordial", ...]

# Get synonyms for a term
synonyms = ontology.get_synonyms("hipertensión")
# Returns: ["HTA", "presión alta", "tensión arterial elevada"]

# Check for emergency
is_emergency, keywords = ontology.is_emergency("no puedo respirar")
# Returns: (True, ["no puedo respirar", "dificultad para respirar"])

# Get ICD-10 codes
codes = ontology.get_related_icd10("diabetes")
# Returns: ["E11", "E10", ...]
```

### 4.4 Symptom Categories

- **Pain (Dolor)**: 12 types including precordial, abdominal, headache
- **Respiratory**: Dyspnea, cough, wheezing, hemoptysis
- **Cardiovascular**: Palpitations, edema, syncope
- **Gastrointestinal**: Nausea, vomiting, diarrhea, constipation
- **Neurological**: Vertigo, seizures, weakness, numbness
- **Urinary**: Dysuria, hematuria, frequency
- **Dermatological**: Rash, pruritus, lesions
- **Constitutional**: Fever, fatigue, weight changes

### 4.5 Emergency Detection

The ontology includes 42 emergency keywords organized by system:

- **Respiratory**: "no puedo respirar", "asfixia", "cianosis"
- **Cardiovascular**: "infarto", "paro cardíaco", "arritmia grave"
- **Neurological**: "derrame", "convulsión", "parálisis súbita"
- **Trauma/Shock**: "hemorragia", "shock", "trauma grave"
- **Expressions**: "me estoy muriendo", "urgente", "insoportable"

---

## 5. RAG SOTA Implementation

### 5.1 Architecture

The RAG (Retrieval-Augmented Generation) State-of-the-Art implementation combines:

1. **Query Enhancement**: Ontology-based expansion
2. **Semantic Retrieval**: Embedding-based search
3. **Context Ranking**: Relevance scoring
4. **Response Generation**: LLM with retrieved context

### 5.2 Query Enhancement Pipeline

```python
# 1. Original query
query = "paciente con dolor de pecho y disnea"

# 2. Ontology expansion
expanded_terms = ontology.expand_query(query)
# ["dolor de pecho", "dolor torácico", "precordialgia",
#  "disnea", "dificultad respiratoria", "falta de aire"]

# 3. Abbreviation expansion
"IAM" → "infarto agudo de miocardio"
"TEP" → "tromboembolismo pulmonar"

# 4. Colloquial normalization
"me duele el pecho" → "dolor torácico"
```

### 5.3 Retrieval Strategy

```python
class RAGSOTAEngine:
    def retrieve_context(self, query: str) -> list[Context]:
        # 1. Expand query with ontology
        expanded = self.ontology.expand_query(query)

        # 2. Search knowledge base
        conditions = search_conditions(query)
        medications = search_medications(query)

        # 3. Score and rank results
        ranked = self.rank_by_relevance(conditions, query)

        # 4. Return top-k contexts
        return ranked[:self.config.top_k]
```

### 5.4 Response Generation

The system uses a context-aware prompt template:

```python
PROFESSIONAL_TEMPLATE = """
Based on the following medical knowledge:
{context}

Patient Query: {query}

Provide a professional medical response including:
1. Clinical assessment
2. Differential diagnosis
3. Recommended workup
4. Treatment considerations
5. Red flags to monitor
"""
```

---

## 6. User Interface

### 6.1 Streamlit Application

The UI (`streamlit_app.py`) provides:

- **Chat Interface**: Real-time medical consultation
- **Knowledge Explorer**: Browse conditions and medications
- **Query Expansion Viewer**: See how queries are enhanced
- **Session Statistics**: Track query patterns

### 6.2 Main Components

| Component                     | Function           | Location   |
| ----------------------------- | ------------------ | ---------- |
| `render_header()`             | Application header | Main area  |
| `render_sidebar()`            | Settings and stats | Sidebar    |
| `render_knowledge_explorer()` | Compact KB browser | Sidebar    |
| `render_knowledge_tab()`      | Full KB explorer   | Tab        |
| `process_medical_query()`     | Query processing   | Main logic |

### 6.3 Tab Structure

```
+------------------+--------------------+
|      Chat        |   Knowledge Base   |
+------------------+--------------------+
| - Chat history   | - Statistics       |
| - User badges    | - Search Conditions|
| - Query input    | - Search Medications|
| - Streaming resp | - Query Expansion  |
+------------------+--------------------+
```

### 6.4 User Detection Badges

- **PROFESSIONAL**: Healthcare provider queries
- **EDUCATIONAL**: General learning queries
- **EMERGENCY**: Urgent medical situations

---

## 7. API Reference

### 7.1 MedeXv2583 Engine

```python
from MEDEX_FINAL import MedeXv2583

# Initialize
medex = MedeXv2583()

# Detect user type
user_type = medex.detect_user_type(query)
# Returns: "Professional" | "Educational"

# Detect emergency
is_emergency = medex.detect_emergency(query)
# Returns: bool

# Generate response (async)
response = await medex.generate_response(query)
# Returns: str

# Stream response (async generator)
async for chunk in medex.generate_response_stream(query):
    print(chunk, end="")
```

### 7.2 MedicalOntology

```python
from medical_ontology import MedicalOntology

ontology = MedicalOntology()

# Core methods
expand_query(query: str, max_expansions: int = 3) -> list[str]
get_synonyms(term: str) -> list[str]
is_emergency(text: str) -> tuple[bool, list[str]]
get_related_icd10(term: str) -> list[str]
expand_abbreviation(abbr: str) -> str
```

### 7.3 Knowledge Base

```python
from knowledge import (
    ALL_CONDITIONS,
    get_all_conditions,
    search_conditions,
    get_condition_by_icd10,
    get_conditions_by_category,
    STATS
)

from knowledge.medications_database import (
    ALL_MEDICATIONS,
    get_medication,
    search_medications
)
```

---

## 8. Configuration

### 8.1 Environment Variables

| Variable           | Description           | Default |
| ------------------ | --------------------- | ------- |
| `HF_TOKEN`         | HuggingFace API token | None    |
| `MOONSHOT_API_KEY` | Moonshot API key      | None    |
| `MEDEX_MODEL`      | Default model         | Kimi K2 |
| `MEDEX_DEBUG`      | Enable debug mode     | False   |

### 8.2 File-based Configuration

```
.hf_token          # HuggingFace token
api_key.txt        # Moonshot API key
```

### 8.3 Model Configuration

```python
MODEL_OPTIONS = {
    "Moonshot Kimi K2": "Primary (requires credit)",
    "HuggingFace Gemma 9B": "Free fallback",
    "HuggingFace Gemma 2B": "Fast free model",
    "HuggingFace Llama 3.2 3B": "Meta model",
    "HuggingFace Qwen Coder": "Structured output"
}
```

---

## 9. Testing

### 9.1 Test Suite

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_detection.py -v

# Run with coverage
python -m pytest tests/ --cov=. --cov-report=html
```

### 9.2 Test Categories

| Test File           | Coverage                               |
| ------------------- | -------------------------------------- |
| `test_detection.py` | User type and emergency detection      |
| `test_engine.py`    | MedeX engine configuration and prompts |

### 9.3 Current Test Status

- **Total Tests**: 33
- **Passing**: 33 (100%)
- **Coverage**: Core functionality

---

## 10. Deployment

### 10.1 Local Development

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run application
streamlit run streamlit_app.py --server.port 8501
```

### 10.2 HuggingFace Spaces

The application is designed for deployment on HuggingFace Spaces:

1. Push to HuggingFace repository
2. Configure secrets (HF_TOKEN)
3. Application auto-deploys

### 10.3 Docker Deployment

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "streamlit_app.py"]
```

---

## Appendix A: Medical Abbreviations Reference

| Abbreviation | Expansion                               |
| ------------ | --------------------------------------- |
| IAM          | Infarto agudo de miocardio              |
| ACV          | Accidente cerebrovascular               |
| HTA          | Hipertensión arterial                   |
| DM           | Diabetes mellitus                       |
| ICC          | Insuficiencia cardíaca congestiva       |
| EPOC         | Enfermedad pulmonar obstructiva crónica |
| TEP          | Tromboembolismo pulmonar                |
| TVP          | Trombosis venosa profunda               |
| NAC          | Neumonía adquirida en comunidad         |
| ITU          | Infección del tracto urinario           |

_Full list: 150 abbreviations in `medical_ontology.py`_

---

## Appendix B: ICD-10 Codes Reference

| Code    | Condition                |
| ------- | ------------------------ |
| I50.9   | Insuficiencia cardíaca   |
| I48.91  | Fibrilación auricular    |
| I26.99  | Tromboembolismo pulmonar |
| J44.9   | EPOC                     |
| J18.9   | Neumonía                 |
| K35.80  | Apendicitis aguda        |
| A41.9   | Sepsis                   |
| I63.9   | ACV isquémico            |
| E11.9   | Diabetes mellitus tipo 2 |
| G40.909 | Epilepsia                |

_Full list: 38 conditions with ICD-10 codes_

---

**Document Control**

| Version | Date     | Author     | Changes               |
| ------- | -------- | ---------- | --------------------- |
| 1.0     | Jan 2026 | MedeX Team | Initial documentation |

---

_This documentation is part of the MedeX Medical AI System._
