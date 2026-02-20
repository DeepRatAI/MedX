# 📚 Plan de Expansión de Base de Conocimiento Médico - MedeX

## 🎯 Objetivo

Transformar la base de conocimiento médico de MedeX de un estado básico (5 condiciones, 3 medicamentos)
a una base robusta que cubra las necesidades de atención primaria, urgencias y consulta médica general.

---

## 📊 Análisis del Estado Actual

### Inventario Actual

| Categoría              | Cantidad Actual | Objetivo |
| ---------------------- | --------------- | -------- |
| Condiciones médicas    | 5               | 50+      |
| Medicamentos           | 3               | 40+      |
| Procedimientos         | 2               | 15+      |
| Protocolos clínicos    | 2               | 20+      |
| Valores de laboratorio | 4               | 30+      |

### Gaps Identificados

1. **Especialidades sin cobertura**: Gastroenterología, Urología, Ginecología, Dermatología, Traumatología, Psiquiatría, Pediatría, Oftalmología, ORL
2. **Emergencias incompletas**: Falta shock, sepsis, intoxicaciones, trauma, quemaduras
3. **Medicamentos limitados**: Solo 3 de los ~500 esenciales WHO
4. **Sin valores de laboratorio completos**: Falta hemograma, química, coagulación

---

## 🔬 Fuentes de Referencia

### Clasificaciones Estándar

- **ICD-10-CM 2026**: Clasificación Internacional de Enfermedades (CMS oficial)
- **SNOMED-CT**: Terminología clínica sistematizada
- **ATC/WHO**: Clasificación Anatómica Terapéutica Química de medicamentos

### Guías Clínicas

- **WHO Essential Medicines List 2023**: 502 medicamentos esenciales
- **AWaRe Antibiotics**: Clasificación de antibióticos (Access/Watch/Reserve)
- **AHA/ACC**: Guías cardiovasculares
- **ADA**: Guías de diabetes

### Fuentes de Evidencia

- **UpToDate**: Referencia clínica basada en evidencia
- **Cochrane Library**: Revisiones sistemáticas
- **PubMed/MEDLINE**: Literatura médica indexada

---

## 🏗️ Arquitectura de la Base de Conocimiento

### Taxonomía Propuesta

```
CONOCIMIENTO MÉDICO
│
├── CONDICIONES (ICD-10)
│   ├── Cardiovascular (I00-I99)
│   ├── Respiratorio (J00-J99)
│   ├── Digestivo (K00-K93)
│   ├── Endocrino (E00-E89)
│   ├── Neurológico (G00-G99)
│   ├── Infeccioso (A00-B99)
│   ├── Musculoesquelético (M00-M99)
│   ├── Genitourinario (N00-N99)
│   ├── Dermatológico (L00-L99)
│   ├── Psiquiátrico (F00-F99)
│   ├── Hematológico (D50-D89)
│   ├── Oncológico (C00-D49)
│   └── Traumatismos (S00-T98)
│
├── MEDICAMENTOS (ATC)
│   ├── Sistema Cardiovascular (C)
│   ├── Sistema Nervioso (N)
│   ├── Antiinfecciosos (J)
│   ├── Sistema Digestivo (A)
│   ├── Sistema Respiratorio (R)
│   ├── Sistema Musculoesquelético (M)
│   ├── Hormonas (H)
│   ├── Dermatológicos (D)
│   └── Varios (V)
│
├── PROCEDIMIENTOS
│   ├── Diagnósticos
│   │   ├── Laboratorio
│   │   ├── Imagen
│   │   └── Funcionales
│   └── Terapéuticos
│       ├── Invasivos
│       └── No invasivos
│
├── PROTOCOLOS
│   ├── Emergencias
│   ├── Atención Primaria
│   └── Especialidades
│
└── VALORES DE REFERENCIA
    ├── Signos Vitales
    ├── Hemograma
    ├── Química Sanguínea
    ├── Función Hepática
    ├── Función Renal
    ├── Perfil Lipídico
    ├── Coagulación
    └── Hormonas
```

---

## 📋 Plan de Implementación por Fases

### FASE 1: Condiciones Médicas de Alto Impacto (Prioridad Crítica)

#### 1.1 Cardiovascular (8 condiciones)

- [x] I21 - Síndrome Coronario Agudo
- [x] I10 - Hipertensión Arterial
- [ ] I50 - Insuficiencia Cardíaca
- [ ] I48 - Fibrilación Auricular
- [ ] I63 - Infarto Cerebral (ACV isquémico)
- [ ] I61 - Hemorragia Intracerebral
- [ ] I26 - Embolia Pulmonar
- [ ] I80 - Trombosis Venosa Profunda

#### 1.2 Respiratorio (8 condiciones)

- [x] J18 - Neumonía
- [ ] J44 - EPOC
- [ ] J45 - Asma
- [ ] J06 - Infección Respiratoria Alta
- [ ] J20 - Bronquitis Aguda
- [ ] J96 - Insuficiencia Respiratoria
- [ ] J80 - SDRA (Distrés Respiratorio)
- [ ] J12 - Neumonía viral

#### 1.3 Gastrointestinal (8 condiciones)

- [ ] K25 - Úlcera Gástrica
- [ ] K26 - Úlcera Duodenal
- [ ] K29 - Gastritis
- [ ] K35 - Apendicitis Aguda
- [ ] K80 - Colelitiasis
- [ ] K81 - Colecistitis
- [ ] K85 - Pancreatitis Aguda
- [ ] K57 - Diverticulitis

#### 1.4 Endocrino-Metabólico (6 condiciones)

- [x] E11 - Diabetes Tipo 2
- [ ] E10 - Diabetes Tipo 1
- [ ] E03 - Hipotiroidismo
- [ ] E05 - Hipertiroidismo
- [ ] E87 - Trastornos Electrolíticos
- [ ] E16 - Hipoglucemia

#### 1.5 Infeccioso (8 condiciones)

- [ ] A41 - Sepsis
- [ ] N39 - Infección Urinaria
- [ ] A09 - Gastroenteritis Aguda
- [ ] B34 - Infección Viral (COVID, Influenza)
- [ ] A46 - Erisipela/Celulitis
- [ ] L03 - Celulitis
- [ ] A40 - Sepsis Estreptocócica
- [ ] N10 - Pielonefritis

#### 1.6 Neurológico (6 condiciones)

- [x] G43 - Migraña
- [ ] G40 - Epilepsia
- [ ] G20 - Parkinson
- [ ] G30 - Alzheimer
- [ ] G35 - Esclerosis Múltiple
- [ ] R56 - Convulsiones

#### 1.7 Musculoesquelético (4 condiciones)

- [ ] M54 - Lumbalgia
- [ ] M79 - Fibromialgia
- [ ] M17 - Osteoartritis de Rodilla
- [ ] M81 - Osteoporosis

#### 1.8 Emergencias/Trauma (6 condiciones)

- [ ] T78.2 - Shock Anafiláctico
- [ ] T36-T50 - Intoxicaciones
- [ ] T30 - Quemaduras
- [ ] S06 - Traumatismo Craneoencefálico
- [ ] R57 - Shock
- [ ] T68 - Hipotermia

### FASE 2: Medicamentos Esenciales (40+)

#### Por Sistema

- **Cardiovascular**: Losartán, Amlodipino, Furosemida, Atorvastatina, Bisoprolol, Warfarina, Enoxaparina
- **Antiinfecciosos**: Amoxicilina, Azitromicina, Ciprofloxacino, Ceftriaxona, Metronidazol, Fluconazol
- **Analgésicos**: Paracetamol, Ibuprofeno, Tramadol, Morfina, Ketorolaco
- **Sistema Nervioso**: Diazepam, Lorazepam, Sertralina, Escitalopram, Levodopa
- **Respiratorio**: Salbutamol, Budesonida, Ipratropio, Prednisona
- **Endocrino**: Metformina, Insulina, Levotiroxina, Hidrocortisona
- **Gastrointestinal**: Omeprazol, Ranitidina, Metoclopramida, Loperamida

### FASE 3: Procedimientos y Protocolos

#### Procedimientos (15+)

- ECG, Rx Tórax, Hemograma, Química sanguínea
- Ecografía abdominal, Ecocardiograma
- TAC cerebral, TAC toraco-abdominal
- Punción lumbar, Toracocentesis
- Gasometría arterial
- Uroanálisis, Cultivos

#### Protocolos (20+)

- Dolor torácico, Disnea aguda
- Fiebre en adulto/pediátrico
- Manejo de HTA/DM
- Sepsis (Surviving Sepsis)
- Shock (tipos y manejo)
- Intoxicaciones comunes
- Reanimación cardiopulmonar
- Manejo de crisis convulsivas

### FASE 4: Valores de Referencia Completos

- Hemograma completo (Hb, Hto, leucocitos, plaquetas, diferencial)
- Química sanguínea (glucosa, creatinina, BUN, electrolitos)
- Función hepática (AST, ALT, FA, bilirrubinas, albúmina)
- Perfil lipídico (colesterol total, HDL, LDL, triglicéridos)
- Coagulación (TP, TTP, INR, fibrinógeno)
- Marcadores cardíacos (troponinas, CK-MB, BNP)
- Gasometría arterial
- Uroanálisis

---

## ✅ Criterios de Calidad

### Para cada Condición Médica

1. Código ICD-10 correcto y actualizado
2. Descripción clara y concisa
3. Síntomas con frecuencia (común/ocasional/raro)
4. Factores de riesgo basados en evidencia
5. Criterios diagnósticos según guías actuales
6. Diagnóstico diferencial relevante
7. Tratamiento basado en guías vigentes
8. Signos de alarma/emergencia claramente definidos
9. Pronóstico realista
10. Seguimiento apropiado

### Para cada Medicamento

1. Nombre genérico y comerciales comunes
2. Clasificación ATC
3. Indicaciones aprobadas
4. Contraindicaciones absolutas y relativas
5. Dosis por vía y población (adulto/pediátrico/geriátrico)
6. Efectos adversos por frecuencia
7. Interacciones clínicamente significativas
8. Monitoreo requerido
9. Categoría en embarazo
10. Ajuste en insuficiencia renal/hepática

---

## 📅 Cronograma

| Fase | Contenido                 | Tiempo Estimado |
| ---- | ------------------------- | --------------- |
| 1.1  | Cardiovascular            | Inmediato       |
| 1.2  | Respiratorio              | Inmediato       |
| 1.3  | Gastrointestinal          | Inmediato       |
| 1.4  | Endocrino                 | Inmediato       |
| 1.5  | Infeccioso                | Siguiente       |
| 1.6  | Neurológico               | Siguiente       |
| 1.7  | Musculoesquelético        | Siguiente       |
| 1.8  | Emergencias               | Siguiente       |
| 2    | Medicamentos              | Continuo        |
| 3    | Procedimientos/Protocolos | Continuo        |
| 4    | Valores de Referencia     | Final           |

---

## 🎯 Métricas de Éxito

1. **Cobertura**: ≥80% de diagnósticos más frecuentes en atención primaria/urgencias
2. **Precisión**: 100% de códigos ICD-10 correctos
3. **Actualización**: Basado en guías ≤2 años de antigüedad
4. **Utilidad**: Información suficiente para orientar decisiones clínicas
5. **Búsqueda**: ≥90% de queries encuentran información relevante

---

_Documento creado: 2 de enero de 2026_
_Versión: 1.0_
