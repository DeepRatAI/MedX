# 🛠️ MedeX Tools Roadmap - Implementación Sin Costo

> **Fecha de creación**: 2026-01-06  
> **Estado**: Planificación aprobada  
> **Costo total**: $0

---

## 📋 RESUMEN EJECUTIVO

| Categoría                   | Cantidad | Costo  |
| --------------------------- | -------- | ------ |
| RAG sobre KB existente      | 1        | $0     |
| Wrappers sobre KB existente | 3        | $0     |
| Calculadoras clínicas       | 15+      | $0     |
| APIs médicas públicas       | 6        | $0     |
| **TOTAL**                   | **25+**  | **$0** |

---

## ✅ TIER 1 - Gratis y Alto Impacto (Fase 1: 1-2 días)

### Herramientas basadas en KB existente

| #   | Herramienta                  | Recurso                                       | Archivo Fuente                     | Prioridad |
| --- | ---------------------------- | --------------------------------------------- | ---------------------------------- | --------- |
| 1   | `kb_search`                  | Qdrant (self-hosted) + HuggingFace embeddings | 46K líneas de KB                   | 🔴 ALTA   |
| 2   | `check_drug_interactions`    | Diccionario de interacciones                  | `medications_database.py`          | 🔴 ALTA   |
| 3   | `get_icd10_code`             | Catálogo ICD-10 completo                      | `icd10_catalog.py` (13,516 líneas) | 🔴 ALTA   |
| 4   | `get_differential_diagnosis` | Módulo DDx existente                          | `differential_diagnosis.py`        | 🔴 ALTA   |

### Calculadoras básicas (fórmulas matemáticas)

| #   | Herramienta                      | Fórmula                  | Complejidad |
| --- | -------------------------------- | ------------------------ | ----------- |
| 5   | `calculate_creatinine_clearance` | Cockcroft-Gault, CKD-EPI | Baja        |
| 6   | `calculate_bmi`                  | peso / altura²           | Trivial     |
| 7   | `calculate_body_surface_area`    | Du Bois                  | Baja        |

---

## ✅ TIER 2 - APIs Públicas Gratuitas (Fase 2: 2-3 días)

| #   | Herramienta              | API                | Límites                                   | Documentación                                |
| --- | ------------------------ | ------------------ | ----------------------------------------- | -------------------------------------------- |
| 8   | `pubmed_search`          | NCBI E-utilities   | 3 req/s sin key, 10/s con key gratis      | https://www.ncbi.nlm.nih.gov/books/NBK25501/ |
| 9   | `rxnorm_lookup`          | NIH RxNorm         | Sin límites                               | https://lhncbc.nlm.nih.gov/RxNav/APIs/       |
| 10  | `get_drug_info_fda`      | openFDA            | 1000/día sin key, 120K/día con key gratis | https://open.fda.gov/apis/                   |
| 11  | `snomed_lookup`          | SNOMED Browser     | Gratis uso educativo                      | https://browser.ihtsdotools.org/             |
| 12  | `loinc_lookup`           | LOINC FHIR         | Registro gratuito requerido               | https://loinc.org/fhir/                      |
| 13  | `clinical_trials_search` | ClinicalTrials.gov | Sin límites                               | https://clinicaltrials.gov/api/              |

---

## ✅ TIER 3 - Calculadoras Clínicas Avanzadas (Fase 3: 1 semana)

### Scores de Severidad/Pronóstico

| #   | Calculadora            | Variables                        | Uso Clínico                  |
| --- | ---------------------- | -------------------------------- | ---------------------------- |
| 14  | `calculate_apache_ii`  | 12 variables                     | UCI - mortalidad             |
| 15  | `calculate_meld`       | Bilirrubina, INR, Creatinina, Na | Hepatología - trasplante     |
| 16  | `calculate_child_pugh` | 5 variables                      | Cirrosis - pronóstico        |
| 17  | `calculate_sofa`       | 6 sistemas                       | Sepsis - disfunción orgánica |

### Scores Cardiovasculares

| #   | Calculadora              | Variables                        | Uso Clínico                       |
| --- | ------------------------ | -------------------------------- | --------------------------------- |
| 18  | `calculate_cha2ds2_vasc` | 7 variables                      | FA - riesgo embólico              |
| 19  | `calculate_hasbled`      | 9 variables                      | Anticoagulación - riesgo sangrado |
| 20  | `calculate_framingham`   | Edad, colesterol, PA, tabaco, DM | Riesgo cardiovascular 10 años     |
| 21  | `calculate_heart_score`  | 5 variables                      | SCA - estratificación             |

### Scores Respiratorios/Infecciosos

| #   | Calculadora          | Variables    | Uso Clínico               |
| --- | -------------------- | ------------ | ------------------------- |
| 22  | `calculate_curb65`   | 5 variables  | Neumonía - severidad      |
| 23  | `calculate_psi_port` | 20 variables | Neumonía - mortalidad     |
| 24  | `calculate_qsofa`    | 3 variables  | Sepsis - screening rápido |

### Scores Tromboembolismo

| #   | Calculadora           | Variables   | Uso Clínico        |
| --- | --------------------- | ----------- | ------------------ |
| 25  | `calculate_wells_dvt` | Checklist   | TVP - probabilidad |
| 26  | `calculate_wells_pe`  | Checklist   | TEP - probabilidad |
| 27  | `calculate_perc`      | 8 criterios | TEP - rule-out     |

### Correcciones de Laboratorio

| #   | Calculadora                   | Fórmula                | Uso Clínico         |
| --- | ----------------------------- | ---------------------- | ------------------- |
| 28  | `calculate_anion_gap`         | Na - (Cl + HCO3)       | Acidosis metabólica |
| 29  | `calculate_corrected_calcium` | Payne                  | Hipoalbuminemia     |
| 30  | `calculate_corrected_sodium`  | Por glucosa            | Hiperglucemia       |
| 31  | `calculate_osmolar_gap`       | Osm medida - calculada | Intoxicaciones      |

### Pediatría/Dosificación

| #   | Calculadora                 | Fórmula           | Uso Clínico           |
| --- | --------------------------- | ----------------- | --------------------- |
| 32  | `pediatric_dose_calculator` | Clark, Young, BSA | Ajuste pediátrico     |
| 33  | `ideal_body_weight`         | Devine            | Dosificación fármacos |
| 34  | `adjusted_body_weight`      | IBW + factor      | Obesidad              |

---

## ❌ EXCLUIDAS (Requieren pago)

| Herramienta                    | Razón                  | Alternativa Gratuita          |
| ------------------------------ | ---------------------- | ----------------------------- |
| `web_search` (Tavily/Serper)   | APIs de pago           | DuckDuckGo scraping (frágil)  |
| `guidelines_search` (UpToDate) | Suscripción ~$500/año  | PubMed + WHO                  |
| `epocrates_lookup`             | Suscripción            | openFDA + RxNorm              |
| `analyze_ecg` (visión)         | Modelos cloud de pago  | HF gratuitos (menos precisos) |
| `analyze_xray` (visión)        | Modelos especializados | Limitado gratis               |

---

## 🚀 PLAN DE IMPLEMENTACIÓN

### Fase 1 (1-2 días) - Wrappers sobre KB existente

- [ ] `get_icd10_code`
- [ ] `check_drug_interactions`
- [ ] `get_differential_diagnosis`
- [ ] Calculadoras básicas (BMI, Creatinina, BSA)

### Fase 2 (2-3 días) - RAG real

- [ ] Configurar Qdrant local
- [ ] Indexar KB con sentence-transformers
- [ ] Implementar `kb_search`

### Fase 3 (1 semana) - APIs externas

- [ ] `pubmed_search` (NCBI)
- [ ] `rxnorm_lookup` (NIH)
- [ ] `get_drug_info_fda` (openFDA)

### Fase 4 (1 semana) - Calculadoras avanzadas

- [ ] Scores de severidad (APACHE, MELD, SOFA)
- [ ] Scores cardiovasculares (CHA2DS2-VASc, Framingham)
- [ ] Scores respiratorios (CURB-65, qSOFA)
- [ ] Correcciones de laboratorio

---

## 📝 NOTAS TÉCNICAS

### Arquitectura de Tools

- Cada tool debe implementar interface común para todos los LLMs
- Tools deben funcionar con: Kimi K2, Qwen, DeepSeek, Llama
- Formato de entrada/salida JSON Schema compatible

### Dependencias gratuitas

- **Qdrant**: `pip install qdrant-client` (o Docker)
- **Embeddings**: `sentence-transformers` (HuggingFace, gratis)
- **HTTP**: `httpx` o `aiohttp` para APIs externas

---

_Documento generado automáticamente - MedeX Tools Planning_
