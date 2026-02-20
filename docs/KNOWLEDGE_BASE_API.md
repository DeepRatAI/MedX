# Knowledge Base API Reference

**Module:** `knowledge`  
**Version:** 1.0  
**Last Updated:** January 2026

---

## Overview

The Knowledge Base module provides structured medical information for 38 clinical conditions and 29 medications, organized by medical specialty with ICD-10 and ATC classification compliance.

---

## Module Structure

```
knowledge/
├── __init__.py                    # Main integration module
├── conditions_cardiovascular.py   # 6 cardiovascular conditions
├── conditions_respiratory.py      # 7 respiratory conditions
├── conditions_gastrointestinal.py # 7 GI conditions
├── conditions_infectious.py       # 7 infectious conditions
├── conditions_emergency.py        # 5 emergency conditions
├── conditions_neurological.py     # 6 neurological conditions
└── medications_database.py        # 29 essential medications
```

---

## Data Models

### MedicalCondition

```python
from dataclasses import dataclass

@dataclass
class MedicalCondition:
    name: str                        # Condition name (Spanish)
    icd10_code: str                  # ICD-10-CM 2026 code
    category: str                    # Medical specialty
    description: str                 # Clinical description
    symptoms: list[str]              # Common presenting symptoms
    red_flags: list[str]             # Warning signs requiring urgent action
    differential_diagnosis: list[str] # Alternative diagnoses to consider
    initial_workup: list[str]        # Recommended diagnostic studies
    treatment_principles: list[str]  # General management approach
    medications: list[str]           # Common medications used
    complications: list[str]         # Potential complications
    patient_education: list[str]     # Key patient teaching points
```

### Medication

```python
@dataclass
class Medication:
    generic_name: str                # International nonproprietary name
    brand_names: list[str]           # Trade names (region-specific)
    drug_class: str                  # Therapeutic classification
    atc_code: str                    # WHO ATC code
    mechanism: str                   # Mechanism of action
    indications: list[str]           # Approved clinical uses
    contraindications: list[str]     # Absolute/relative contraindications
    dosing: dict                     # Dosing information by indication
    side_effects: list[str]          # Common adverse effects
    interactions: list[str]          # Significant drug interactions
    monitoring: list[str]            # Required laboratory monitoring
    special_populations: dict        # Pregnancy, renal, hepatic adjustments
```

---

## API Functions

### Conditions API

#### get_all_conditions()

Returns all medical conditions as a dictionary.

```python
from knowledge import get_all_conditions

conditions = get_all_conditions()
# Returns: dict[str, MedicalCondition]
# Key: ICD-10 code
# Value: MedicalCondition object

# Example
for code, condition in conditions.items():
    print(f"{code}: {condition.name}")
```

#### search_conditions(query: str)

Search conditions by name or description text.

```python
from knowledge import search_conditions

results = search_conditions("diabetes")
# Returns: list[MedicalCondition]

for condition in results:
    print(f"{condition.name} ({condition.icd10_code})")
    print(f"  Category: {condition.category}")
    print(f"  Description: {condition.description[:100]}...")
```

**Parameters:**

- `query` (str): Search term (case-insensitive)

**Returns:**

- List of matching MedicalCondition objects

#### get_condition_by_icd10(code: str)

Retrieve a specific condition by ICD-10 code.

```python
from knowledge import get_condition_by_icd10

condition = get_condition_by_icd10("I50.9")
# Returns: MedicalCondition | None

if condition:
    print(f"Name: {condition.name}")
    print(f"Symptoms: {', '.join(condition.symptoms[:5])}")
    print(f"Red Flags: {', '.join(condition.red_flags)}")
```

**Parameters:**

- `code` (str): ICD-10-CM code (e.g., "I50.9", "J44.9")

**Returns:**

- MedicalCondition object or None if not found

#### get_conditions_by_category(category: str)

Filter conditions by medical specialty.

```python
from knowledge import get_conditions_by_category

cardio = get_conditions_by_category("Cardiovascular")
# Returns: list[MedicalCondition]

print(f"Cardiovascular conditions: {len(cardio)}")
for c in cardio:
    print(f"  - {c.name}")
```

**Parameters:**

- `category` (str): Category name (case-insensitive partial match)

**Valid Categories:**

- Cardiovascular
- Respiratory
- Gastrointestinal
- Infectious
- Emergency
- Neurological

**Returns:**

- List of matching MedicalCondition objects

---

### Medications API

#### get_medication(name: str)

Retrieve a medication by generic name.

```python
from knowledge.medications_database import get_medication

med = get_medication("Metformina")
# Returns: Medication | None

if med:
    print(f"Name: {med.generic_name}")
    print(f"Class: {med.drug_class}")
    print(f"ATC: {med.atc_code}")
    print(f"Mechanism: {med.mechanism}")
```

**Parameters:**

- `name` (str): Generic medication name (case-insensitive)

**Returns:**

- Medication object or None if not found

#### search_medications(query: str)

Search medications by name, class, or indication.

```python
from knowledge.medications_database import search_medications

results = search_medications("anticoagulante")
# Returns: list[Medication]

for med in results:
    print(f"{med.generic_name} ({med.drug_class})")
    print(f"  Indications: {', '.join(med.indications[:3])}")
```

**Parameters:**

- `query` (str): Search term (searches name, class, mechanism, indications)

**Returns:**

- List of matching Medication objects

---

## Constants

### ALL_CONDITIONS

Dictionary containing all medical conditions.

```python
from knowledge import ALL_CONDITIONS

print(f"Total conditions: {len(ALL_CONDITIONS)}")
# Output: Total conditions: 38
```

### ALL_MEDICATIONS

Dictionary containing all medications.

```python
from knowledge.medications_database import ALL_MEDICATIONS

print(f"Total medications: {len(ALL_MEDICATIONS)}")
# Output: Total medications: 29
```

### STATS

Statistics about the knowledge base.

```python
from knowledge import STATS

print(STATS)
# Output:
# {
#     "total_conditions": 38,
#     "cardiovascular": 6,
#     "respiratory": 7,
#     "gastrointestinal": 7,
#     "infectious": 7,
#     "emergency": 5,
#     "neurological": 6
# }
```

---

## Condition Categories Detail

### Cardiovascular (6 conditions)

| ICD-10 | Condition                         |
| ------ | --------------------------------- |
| I50.9  | Insuficiencia Cardíaca Congestiva |
| I48.91 | Fibrilación Auricular             |
| I26.99 | Tromboembolismo Pulmonar          |
| I82.40 | Trombosis Venosa Profunda         |
| I33.0  | Endocarditis Infecciosa           |
| I30.9  | Pericarditis Aguda                |

### Respiratory (7 conditions)

| ICD-10  | Condition                        |
| ------- | -------------------------------- |
| J44.9   | EPOC                             |
| J45.909 | Asma                             |
| J96.00  | Insuficiencia Respiratoria Aguda |
| J18.9   | Neumonía Adquirida en Comunidad  |
| A15.0   | Tuberculosis Pulmonar            |
| J80     | SDRA                             |
| J93.9   | Neumotórax                       |

### Gastrointestinal (7 conditions)

| ICD-10 | Condition                 |
| ------ | ------------------------- |
| K35.80 | Apendicitis Aguda         |
| K80.00 | Colecistitis Aguda        |
| K25.9  | Úlcera Péptica            |
| K92.2  | Hemorragia Digestiva Alta |
| K56.60 | Obstrucción Intestinal    |
| K85.90 | Pancreatitis Aguda        |
| K74.60 | Cirrosis Hepática         |

### Infectious (7 conditions)

| ICD-10 | Condition                     |
| ------ | ----------------------------- |
| A41.9  | Sepsis                        |
| N39.0  | Infección del Tracto Urinario |
| G00.9  | Meningitis Bacteriana         |
| J02.9  | Faringoamigdalitis            |
| A09.9  | Gastroenteritis Aguda         |
| U07.1  | COVID-19                      |
| B20    | VIH/SIDA                      |

### Emergency (5 conditions)

| ICD-10 | Condition                |
| ------ | ------------------------ |
| I46.9  | Paro Cardiorrespiratorio |
| T78.2  | Choque Anafiláctico      |
| E10.10 | Cetoacidosis Diabética   |
| E87.0  | Estado Hiperosmolar      |
| T40.9  | Intoxicación Aguda       |

### Neurological (6 conditions)

| ICD-10  | Condition               |
| ------- | ----------------------- |
| I63.9   | ACV Isquémico           |
| I61.9   | ACV Hemorrágico         |
| G40.909 | Epilepsia               |
| G20     | Enfermedad de Parkinson |
| G43.909 | Migraña                 |
| G35     | Esclerosis Múltiple     |

---

## Medication Categories Detail

### Analgesics and Anti-inflammatories (4)

- Paracetamol (Acetaminofén)
- Ibuprofeno
- Ketorolaco
- Tramadol

### Cardiovascular (6)

- Enalapril
- Losartán
- Metoprolol
- Amlodipino
- Furosemida
- Espironolactona

### Antibiotics (5)

- Amoxicilina
- Amoxicilina/Clavulanato
- Azitromicina
- Ciprofloxacino
- Ceftriaxona

### Antidiabetics (3)

- Metformina
- Insulina NPH
- Insulina Regular

### Respiratory (3)

- Salbutamol
- Budesonida
- Prednisona

### Gastrointestinal (4)

- Omeprazol
- Metoclopramida
- Ondansetrón
- Loperamida

### Emergency and Specialized (4)

- Heparina
- Enoxaparina
- Warfarina
- Epinefrina

---

## Usage Examples

### Example 1: Building a Differential Diagnosis

```python
from knowledge import search_conditions

# Patient presents with chest pain
results = search_conditions("dolor torácico")

print("Differential Diagnosis for Chest Pain:")
for condition in results:
    print(f"\n{condition.name} ({condition.icd10_code})")
    print(f"  Red Flags: {', '.join(condition.red_flags[:3])}")
    print(f"  Workup: {', '.join(condition.initial_workup[:3])}")
```

### Example 2: Medication Lookup for Treatment

```python
from knowledge.medications_database import get_medication

# Get antihypertensive details
enalapril = get_medication("Enalapril")

if enalapril:
    print(f"Medication: {enalapril.generic_name}")
    print(f"Class: {enalapril.drug_class}")
    print(f"\nDosing:")
    for indication, dose in enalapril.dosing.items():
        print(f"  {indication}: {dose}")
    print(f"\nContraindications:")
    for ci in enalapril.contraindications:
        print(f"  - {ci}")
```

### Example 3: Category-Based Education

```python
from knowledge import get_conditions_by_category

# Get all emergency conditions for training
emergencies = get_conditions_by_category("Emergency")

print("Emergency Medicine Review:")
for condition in emergencies:
    print(f"\n=== {condition.name} ===")
    print(f"Key Symptoms: {', '.join(condition.symptoms[:5])}")
    print(f"Immediate Actions: {', '.join(condition.treatment_principles[:3])}")
```

---

## Error Handling

```python
from knowledge import get_condition_by_icd10, search_conditions

# Handle not found
condition = get_condition_by_icd10("INVALID")
if condition is None:
    print("Condition not found")

# Handle empty search
results = search_conditions("xyznonexistent")
if not results:
    print("No matching conditions found")
```

---

## Performance Notes

- All data is loaded at module import time
- Dictionary lookups are O(1)
- Search operations are O(n) where n = number of items
- Memory footprint: approximately 500KB for full dataset

---

## Version History

| Version | Date     | Changes                                            |
| ------- | -------- | -------------------------------------------------- |
| 1.0     | Jan 2026 | Initial release with 38 conditions, 29 medications |

---

_This documentation is part of the MedeX Medical AI System._
