# Medical Ontology Reference

**Module:** `medical_ontology`  
**Class:** `MedicalOntology`  
**Version:** 1.0  
**Last Updated:** January 2026

---

## Overview

The Medical Ontology module provides comprehensive Spanish medical terminology mapping for query expansion, synonym resolution, and emergency detection. It enables the RAG system to understand colloquial expressions, medical abbreviations, and professional terminology.

---

## Statistics

| Category           | Term Count | Description                                  |
| ------------------ | ---------- | -------------------------------------------- |
| Symptom Synonyms   | 68         | Pain types, respiratory, CV, GI, neuro, etc. |
| Condition Synonyms | 77         | Disease name variations by specialty         |
| Drug Synonyms      | 136        | Medication names and classes                 |
| Abbreviations      | 150        | Medical acronyms and expansions              |
| Anatomy Synonyms   | 44         | Body systems and structures                  |
| Procedure Synonyms | 74         | Diagnostic and therapeutic procedures        |
| Emergency Keywords | 42         | Urgent situation detection terms             |
| **Total**          | **~1,856** | **Mapped terms**                             |

---

## Class Reference

### MedicalOntology

```python
from medical_ontology import MedicalOntology

# Singleton pattern - initialize once
ontology = MedicalOntology()
```

---

## Core Methods

### expand_query()

Expands a query string with medical synonyms for improved retrieval.

```python
def expand_query(self, query: str, max_expansions: int = 3) -> list[str]
```

**Parameters:**

- `query` (str): Original query text
- `max_expansions` (int): Maximum synonym expansions per term (default: 3)

**Returns:**

- list[str]: List of expanded query variations

**Example:**

```python
ontology = MedicalOntology()

# Expand chest pain query
expanded = ontology.expand_query("dolor de pecho", max_expansions=5)
print(expanded)
# Output:
# ['dolor de pecho', 'dolor torácico', 'dolor precordial',
#  'angina', 'opresión torácica']

# Expand professional query
expanded = ontology.expand_query("paciente con IAM y disnea")
print(expanded)
# Output:
# ['paciente con IAM y disnea',
#  'paciente con infarto agudo de miocardio y disnea',
#  'paciente con IAM y dificultad respiratoria',
#  ...]
```

### get_synonyms()

Retrieves synonyms for a specific medical term.

```python
def get_synonyms(self, term: str) -> list[str]
```

**Parameters:**

- `term` (str): Medical term to look up (case-insensitive)

**Returns:**

- list[str]: List of synonyms, empty list if none found

**Example:**

```python
synonyms = ontology.get_synonyms("hipertensión")
print(synonyms)
# Output: ['HTA', 'presión alta', 'tensión arterial elevada',
#          'presión arterial alta']

synonyms = ontology.get_synonyms("metformina")
print(synonyms)
# Output: ['Glucophage', 'biguanida', 'antidiabético oral']
```

### is_emergency()

Detects if a text contains emergency-related keywords.

```python
def is_emergency(self, text: str) -> tuple[bool, list[str]]
```

**Parameters:**

- `text` (str): Text to analyze for emergency indicators

**Returns:**

- tuple[bool, list[str]]: (is_emergency, list of matched keywords)

**Example:**

```python
is_emerg, keywords = ontology.is_emergency("no puedo respirar")
print(f"Emergency: {is_emerg}")  # True
print(f"Keywords: {keywords}")    # ['no puedo respirar']

is_emerg, keywords = ontology.is_emergency("tengo dolor de cabeza leve")
print(f"Emergency: {is_emerg}")  # False
print(f"Keywords: {keywords}")    # []
```

### get_related_icd10()

Retrieves related ICD-10 codes for a medical term.

```python
def get_related_icd10(self, term: str) -> list[str]
```

**Parameters:**

- `term` (str): Medical term or condition name

**Returns:**

- list[str]: List of related ICD-10 codes

**Example:**

```python
codes = ontology.get_related_icd10("diabetes")
print(codes)  # ['E11.9', 'E10.9', 'E13.9']

codes = ontology.get_related_icd10("insuficiencia cardíaca")
print(codes)  # ['I50.9', 'I50.1', 'I50.20']
```

### expand_abbreviation()

Expands a medical abbreviation to its full form.

```python
def expand_abbreviation(self, abbr: str) -> str
```

**Parameters:**

- `abbr` (str): Medical abbreviation (case-sensitive)

**Returns:**

- str: Full expansion or original abbreviation if not found

**Example:**

```python
print(ontology.expand_abbreviation("IAM"))
# Output: "infarto agudo de miocardio"

print(ontology.expand_abbreviation("HTA"))
# Output: "hipertensión arterial"

print(ontology.expand_abbreviation("UNKNOWN"))
# Output: "UNKNOWN"  (returns original if not found)
```

---

## Ontology Dictionaries

### symptom_synonyms

Maps colloquial symptom descriptions to medical terms.

**Categories:**

| Category         | Examples                                    |
| ---------------- | ------------------------------------------- |
| Pain (Dolor)     | dolor de pecho, cefalea, dolor abdominal    |
| Respiratory      | disnea, tos, sibilancias, hemoptisis        |
| Cardiovascular   | palpitaciones, edema, síncope               |
| Gastrointestinal | náusea, vómito, diarrea, estreñimiento      |
| Neurological     | vértigo, convulsión, debilidad, parestesias |
| Urinary          | disuria, hematuria, polaquiuria             |
| Dermatological   | erupción, prurito, lesiones                 |
| Constitutional   | fiebre, fatiga, pérdida de peso             |

**Example Mappings:**

```python
"dolor de pecho": ["dolor torácico", "dolor precordial", "angina",
                   "opresión torácica", "malestar torácico"]

"dificultad para respirar": ["disnea", "falta de aire", "ahogo",
                              "sofocación", "dificultad respiratoria"]

"mareo": ["vértigo", "inestabilidad", "sensación de giro",
          "mareos", "lipotimia"]
```

### condition_synonyms

Maps condition names to alternative names and classifications.

**Specialties Covered:**

- Cardiovascular (15 conditions)
- Respiratory (12 conditions)
- Endocrine (10 conditions)
- Neurological (10 conditions)
- Gastrointestinal (8 conditions)
- Infectious (8 conditions)
- Renal (6 conditions)
- Musculoskeletal (4 conditions)
- Hematologic (4 conditions)
- Oncologic (4 conditions)
- Psychiatric (6 conditions)

**Example Mappings:**

```python
"infarto": ["IAM", "infarto agudo de miocardio", "IAMCEST",
            "ataque cardíaco", "síndrome coronario agudo"]

"diabetes": ["DM", "diabetes mellitus", "DM2", "DM1",
             "hiperglucemia crónica"]

"EPOC": ["enfermedad pulmonar obstructiva crónica", "bronquitis crónica",
         "enfisema", "limitación crónica al flujo aéreo"]
```

### drug_synonyms

Maps medication generic names to brand names and classes.

**Categories:**

- Analgesics (15 medications)
- Cardiovascular (25 medications)
- Antibiotics (20 medications)
- Antidiabetics (12 medications)
- Respiratory (10 medications)
- Gastrointestinal (12 medications)
- Neurological/Psychiatric (18 medications)
- Emergency (8 medications)

**Example Mappings:**

```python
"metformina": ["Glucophage", "biguanida", "antidiabético oral",
               "Glafornil", "Dabex"]

"omeprazol": ["Prilosec", "inhibidor de bomba de protones", "IBP",
              "Losec", "antiulceroso"]

"enalapril": ["Vasotec", "IECA", "inhibidor de ECA",
              "antihipertensivo"]
```

### abbreviations

Maps 150 medical abbreviations to full expansions.

**Categories:**

| Category           | Count | Examples                |
| ------------------ | ----- | ----------------------- |
| Diagnoses          | 35    | IAM, ACV, HTA, DM, EPOC |
| Diagnostic Studies | 30    | ECG, TAC, RMN, EGO, BH  |
| Treatment/Routes   | 25    | VO, IV, IM, SC, PRN     |
| Vital Signs        | 15    | FC, FR, TA, SatO2, T°   |
| Services/Units     | 20    | UCI, UCIN, SU, QX, MI   |
| Clinical Terms     | 25    | Dx, Tx, Rx, Hx, PMH     |

**Example Mappings:**

```python
"IAM": "infarto agudo de miocardio"
"IAMCEST": "infarto agudo de miocardio con elevación ST"
"ACV": "accidente cerebrovascular"
"HTA": "hipertensión arterial"
"DM2": "diabetes mellitus tipo 2"
"EPOC": "enfermedad pulmonar obstructiva crónica"
"TEP": "tromboembolismo pulmonar"
"TVP": "trombosis venosa profunda"
"NAC": "neumonía adquirida en comunidad"
"ITU": "infección del tracto urinario"
```

### anatomy_synonyms

Maps anatomical structures to related terms.

**Body Systems:**

- Cardiovascular (heart, arteries, veins)
- Respiratory (lungs, bronchi, trachea)
- Digestive (liver, stomach, intestines)
- Urinary (kidneys, bladder, ureters)
- Nervous (brain, spinal cord, nerves)
- Musculoskeletal (bones, joints, muscles)
- Integumentary (skin, nails, hair)
- Endocrine (thyroid, adrenal, pituitary)
- Sensory (eyes, ears)
- Lymphatic (lymph nodes, spleen)

**Example Mappings:**

```python
"corazón": ["cardíaco", "cardiovascular", "miocardio",
            "pericardio", "cardio"]

"pulmones": ["pulmonar", "respiratorio", "bronquios",
             "alvéolos", "pleura"]

"riñones": ["renal", "nefro", "glomérulo", "túbulo renal"]
```

### procedure_synonyms

Maps procedures to synonyms and abbreviations.

**Categories:**

- Imaging Studies (17 procedures)
- Laboratory Tests (20 procedures)
- Diagnostic Procedures (12 procedures)
- Cardiac Procedures (8 procedures)
- Surgical Procedures (12 procedures)
- Emergency Procedures (8 procedures)
- Neurological Procedures (3 procedures)

**Example Mappings:**

```python
"tomografía": ["TAC", "TC", "CT scan", "escáner",
               "tomografía computarizada"]

"electrocardiograma": ["ECG", "EKG", "trazado cardíaco",
                       "electrocardiografía"]

"cateterismo": ["angiografía", "coronariografía",
                "cateterismo cardíaco"]
```

### emergency_keywords

List of 42 keywords indicating urgent medical situations.

**Categories:**

| Category       | Keywords                                             |
| -------------- | ---------------------------------------------------- |
| Respiratory    | no puedo respirar, asfixia, cianosis, labios morados |
| Cardiovascular | infarto, paro cardíaco, arritmia grave               |
| Neurological   | derrame, convulsión, inconsciencia, parálisis súbita |
| Trauma/Shock   | hemorragia, sangrado abundante, shock, trauma grave  |
| Other          | envenenamiento, sobredosis, anafilaxia, sepsis       |
| Expressions    | me estoy muriendo, urgente, insoportable             |

---

## Query Expansion Algorithm

The `expand_query()` method uses the following algorithm:

```
1. Normalize input (lowercase, strip)
2. Detect and expand abbreviations
3. For each word in query:
   a. Check symptom_synonyms
   b. Check condition_synonyms
   c. Check drug_synonyms
   d. Check anatomy_synonyms
   e. Check procedure_synonyms
4. Generate expansion combinations
5. Limit to max_expansions
6. Return unique expansions
```

**Performance:**

- O(n \* m) where n = words in query, m = synonym dict size
- Typical latency: < 5ms for standard queries

---

## Emergency Detection Algorithm

The `is_emergency()` method:

```
1. Normalize input (lowercase)
2. Check for exact matches in emergency_keywords
3. Check for partial matches (substring)
4. Check colloquial_emergency dictionary
5. Return (is_emergency, matched_keywords)
```

**Sensitivity:** High (prioritizes detection over false negatives)

---

## Usage Examples

### Example 1: Enhancing Search Queries

```python
from medical_ontology import MedicalOntology

ontology = MedicalOntology()

def enhanced_search(query: str, search_function):
    """Search with query expansion for better recall."""
    expanded = ontology.expand_query(query, max_expansions=5)

    all_results = []
    for term in expanded:
        results = search_function(term)
        all_results.extend(results)

    # Deduplicate and return
    return list(set(all_results))
```

### Example 2: Emergency Triage

```python
from medical_ontology import MedicalOntology

ontology = MedicalOntology()

def triage_query(query: str) -> dict:
    """Classify query urgency for triage."""
    is_emergency, keywords = ontology.is_emergency(query)

    return {
        "query": query,
        "is_emergency": is_emergency,
        "matched_keywords": keywords,
        "priority": "CRITICAL" if is_emergency else "ROUTINE"
    }

# Example
result = triage_query("paciente con dolor torácico intenso y disnea")
print(result)
# {
#     "query": "paciente con dolor torácico intenso y disnea",
#     "is_emergency": True,
#     "matched_keywords": ["dolor torácico", "disnea"],
#     "priority": "CRITICAL"
# }
```

### Example 3: Abbreviation Normalization

```python
from medical_ontology import MedicalOntology
import re

ontology = MedicalOntology()

def normalize_clinical_text(text: str) -> str:
    """Expand all abbreviations in clinical text."""
    words = text.split()
    normalized = []

    for word in words:
        # Check if it's an abbreviation (all caps, 2-5 chars)
        if re.match(r'^[A-Z]{2,5}$', word):
            expanded = ontology.expand_abbreviation(word)
            normalized.append(f"{expanded} ({word})")
        else:
            normalized.append(word)

    return ' '.join(normalized)

# Example
text = "Paciente con IAM y HTA, requiere ECG urgente"
print(normalize_clinical_text(text))
# "Paciente con infarto agudo de miocardio (IAM) y
#  hipertensión arterial (HTA), requiere
#  electrocardiograma (ECG) urgente"
```

---

## Integration with RAG

The ontology integrates with the RAG system:

```python
from medical_ontology import MedicalOntology
from knowledge import search_conditions

ontology = MedicalOntology()

def rag_retrieve(query: str) -> list:
    """RAG retrieval with ontology enhancement."""

    # 1. Expand query
    expanded = ontology.expand_query(query)

    # 2. Search with all variations
    results = []
    for term in expanded:
        results.extend(search_conditions(term))

    # 3. Deduplicate by ICD-10 code
    seen = set()
    unique = []
    for r in results:
        if r.icd10_code not in seen:
            seen.add(r.icd10_code)
            unique.append(r)

    return unique
```

---

## Version History

| Version | Date     | Changes                                 |
| ------- | -------- | --------------------------------------- |
| 1.0     | Jan 2026 | Initial release with 1,856 mapped terms |

---

_This documentation is part of the MedeX Medical AI System._
