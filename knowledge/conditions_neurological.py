"""
Condiciones Neurológicas - Base de Conocimiento Médico Expandida
================================================================

Módulo de condiciones neurológicas basado en:
- Guías AHA/ASA 2019-2024 para ACV
- Guías de la International League Against Epilepsy (ILAE)
- Movement Disorder Society (MDS) para Parkinson
- International Headache Society (IHS) ICHD-3

ICD-10-CM 2026 Capítulo VI: Enfermedades del Sistema Nervioso (G00-G99)
"""

from dataclasses import dataclass
from typing import List, Dict, Optional


@dataclass
class MedicalCondition:
    """Estructura estandarizada para condiciones médicas."""

    icd10_code: str
    name: str
    category: str
    description: str
    symptoms: List[str]
    risk_factors: List[str]
    complications: List[str]
    diagnostic_criteria: List[str]
    differential_diagnosis: List[str]
    treatment_protocol: Dict[str, any]
    emergency_signs: List[str]
    prognosis: str
    follow_up: str


# =============================================================================
# CONDICIONES NEUROLÓGICAS
# =============================================================================

NEUROLOGICAL_CONDITIONS: Dict[str, MedicalCondition] = {
    # -------------------------------------------------------------------------
    # ACCIDENTE CEREBROVASCULAR ISQUÉMICO
    # -------------------------------------------------------------------------
    "I63": MedicalCondition(
        icd10_code="I63",
        name="Accidente Cerebrovascular Isquémico",
        category="Neurología - Enfermedad Cerebrovascular",
        description="""
        Infarto cerebral por oclusión arterial que causa déficit neurológico focal.
        Constituye el 85% de todos los ACV. El tiempo es crítico: 'tiempo es cerebro'.
        Cada minuto sin tratamiento se pierden 1.9 millones de neuronas.
        Ventana terapéutica para trombolisis: 4.5 horas desde inicio de síntomas.
        Ventana para trombectomía mecánica: hasta 24 horas en casos seleccionados.
        """,
        symptoms=[
            "Debilidad facial unilateral (parálisis facial central)",
            "Debilidad o parálisis de brazo/pierna (hemiparesia/hemiplejia)",
            "Alteración del habla (afasia, disartria)",
            "Confusión o alteración del nivel de consciencia",
            "Pérdida visual (hemianopsia, amaurosis fugax)",
            "Diplopía",
            "Vértigo severo con nistagmo",
            "Ataxia, incoordinación",
            "Cefalea súbita intensa (especialmente en ACV de circulación posterior)",
            "Disfagia",
            "Negligencia espacial (en lesiones de hemisferio no dominante)",
        ],
        risk_factors=[
            "Hipertensión arterial (principal factor modificable)",
            "Fibrilación auricular",
            "Diabetes mellitus",
            "Dislipidemia",
            "Tabaquismo",
            "Obesidad",
            "Sedentarismo",
            "ACV o AIT previo",
            "Enfermedad carotídea",
            "Cardiopatía (IAM, ICC, valvulopatías)",
            "Síndrome de apnea del sueño",
            "Anticonceptivos orales + tabaquismo",
            "Edad avanzada",
            "Historia familiar de ACV",
        ],
        complications=[
            "Edema cerebral maligno",
            "Transformación hemorrágica",
            "Neumonía aspirativa",
            "Trombosis venosa profunda/TEP",
            "Infecciones urinarias",
            "Úlceras por presión",
            "Espasticidad",
            "Depresión post-ACV (30-50% de pacientes)",
            "Deterioro cognitivo vascular",
            "Epilepsia post-ACV",
            "Dolor central post-ACV",
            "Disfagia persistente",
        ],
        diagnostic_criteria=[
            "ESCALA NIHSS (National Institutes of Health Stroke Scale):",
            "  - Evalúa: consciencia, mirada, campos visuales, parálisis facial",
            "  - Evalúa: función motora extremidades, ataxia, sensibilidad",
            "  - Evalúa: lenguaje, disartria, extinción/negligencia",
            "  - Puntuación 0-42 (mayor = más severo)",
            "  - NIHSS <5: ACV menor, 5-15: moderado, >15: severo",
            "",
            "CRITERIOS DIAGNÓSTICOS:",
            "  1. Déficit neurológico focal de inicio súbito",
            "  2. TC cerebral sin contraste: descarta hemorragia",
            "  3. RM-DWI: confirma isquemia aguda (gold standard)",
            "",
            "ESTUDIOS REQUERIDOS:",
            "  - TC cerebral sin contraste STAT (puerta-TC <25 min)",
            "  - Glucemia capilar (descartar hipoglucemia)",
            "  - ECG (detectar FA)",
            "  - Laboratorio: hemograma, coagulación, función renal",
            "  - Angio-TC o Angio-RM si candidato a trombectomía",
        ],
        differential_diagnosis=[
            "Hipoglucemia (simula cualquier déficit focal)",
            "Migraña con aura",
            "Crisis epiléptica con parálisis de Todd",
            "Hemorragia intracerebral",
            "Tumor cerebral",
            "Encefalopatía hipertensiva",
            "Esclerosis múltiple",
            "Conversión/trastorno funcional",
            "Encefalopatía metabólica",
            "Absceso cerebral",
        ],
        treatment_protocol={
            "prehospitalario": [
                "Reconocimiento rápido: FAST (Face, Arms, Speech, Time)",
                "Activar código ictus",
                "Mantener vía aérea permeable",
                "Oxígeno si SatO2 <94%",
                "No reducir PA agresivamente en prehospitalario",
                "Glucemia capilar",
                "Traslado a centro con capacidad de trombectomía",
            ],
            "trombolisis_iv": {
                "indicaciones": [
                    "ACV isquémico agudo",
                    "Inicio de síntomas <4.5 horas",
                    "Edad ≥18 años",
                    "NIHSS evaluable",
                ],
                "contraindicaciones_absolutas": [
                    "Hemorragia intracraneal en TC",
                    "ACV isquémico o TCE severo en últimos 3 meses",
                    "Cirugía intracraneal/espinal reciente",
                    "Historia de hemorragia intracraneal",
                    "Neoplasia intracraneal, MAV o aneurisma",
                    "PA >185/110 mmHg persistente",
                    "Hemorragia interna activa",
                    "Plaquetas <100,000/μL",
                    "INR >1.7 o uso de anticoagulantes directos",
                ],
                "protocolo": [
                    "Alteplasa (rtPA) 0.9 mg/kg (máx 90 mg)",
                    "10% en bolo IV en 1 min",
                    "90% restante en infusión IV en 60 min",
                    "Meta puerta-aguja <60 min (ideal <45 min)",
                    "Monitoreo neurológico cada 15 min durante infusión",
                    "Control PA cada 15 min x 2h, luego cada 30 min x 6h",
                    "Mantener PA <180/105 mmHg post-trombolisis",
                ],
            },
            "trombectomia_mecanica": {
                "indicaciones": [
                    "Oclusión de gran vaso (ACI, M1, M2 proximal, basilar)",
                    "NIHSS ≥6",
                    "ASPECTS ≥6 (en ventana temprana)",
                    "Ventana 0-6h: beneficio establecido",
                    "Ventana 6-24h: según DAWN/DEFUSE-3 (mismatch clínico-imagen)",
                ],
                "meta_tiempos": [
                    "Puerta-punción arterial <60 min",
                    "Punción-reperfusión <60 min",
                ],
            },
            "cuidados_generales": [
                "Monitorización continua en unidad de ictus",
                "Posición cabecera 30°",
                "Glucemia 140-180 mg/dL",
                "Temperatura <37.5°C (tratar fiebre agresivamente)",
                "Profilaxis TVP: compresión neumática, HBPM a las 24-48h",
                "Evaluación disfagia antes de iniciar vía oral",
                "Prevención úlceras por presión",
                "Rehabilitación temprana (primeras 24-48h)",
            ],
            "prevencion_secundaria": [
                "Antiagregación: AAS 81-325 mg/día (iniciar 24h post-trombolisis)",
                "Estatinas alta intensidad: Atorvastatina 40-80 mg",
                "Control PA: meta <130/80 mmHg",
                "Control glucémico: HbA1c <7%",
                "Anticoagulación si FA (iniciar 1-12 días según tamaño infarto)",
                "Endarterectomía carotídea si estenosis sintomática ≥70%",
            ],
        },
        emergency_signs=[
            "Deterioro neurológico >4 puntos NIHSS",
            "Cefalea súbita intensa (posible transformación hemorrágica)",
            "Vómitos o alteración consciencia (edema cerebral)",
            "Anisocoria o postura de descerebración",
            "PA >220/120 mmHg",
            "Convulsiones",
            "Fiebre alta persistente",
        ],
        prognosis="""
        Variable según severidad, tiempo a tratamiento y reperfusión lograda.
        Con trombectomía exitosa: 46% independencia funcional a 90 días.
        Sin reperfusión: 26% independencia funcional.
        Mortalidad a 30 días: 10-15%.
        40% requieren rehabilitación prolongada.
        Riesgo de recurrencia: 5-15% primer año.
        """,
        follow_up="""
        - Alta con plan de prevención secundaria completo
        - Neurología: 1-2 semanas post-alta
        - Ecocardiograma y Holter si etiología no clara
        - Rehabilitación: fisioterapia, terapia ocupacional, fonoaudiología
        - Control factores de riesgo cada 3 meses
        - Screening depresión y deterioro cognitivo
        - Evaluación para retorno laboral y conducción
        """,
    ),
    # -------------------------------------------------------------------------
    # EPILEPSIA
    # -------------------------------------------------------------------------
    "G40": MedicalCondition(
        icd10_code="G40",
        name="Epilepsia",
        category="Neurología - Trastornos Paroxísticos",
        description="""
        Trastorno cerebral caracterizado por predisposición a generar crisis 
        epilépticas recurrentes. Afecta a ~1% de la población mundial.
        Clasificación ILAE 2017: Focal, Generalizada, Combinada, Desconocida.
        70% de pacientes logran control con FAEs apropiados.
        """,
        symptoms=[
            "CRISIS FOCALES:",
            "  - Con consciencia preservada (auras): déjà vu, sensación epigástrica",
            "  - Con alteración de consciencia: automatismos, confusión",
            "  - Focal a bilateral tónico-clónica",
            "",
            "CRISIS GENERALIZADAS:",
            "  - Tónico-clónicas: pérdida consciencia, rigidez, convulsiones",
            "  - Ausencias: desconexión breve, parpadeo, automatismos orales",
            "  - Mioclónicas: sacudidas breves, matutinas",
            "  - Atónicas: pérdida súbita del tono, caídas",
            "",
            "SÍNTOMAS POSTICTALES:",
            "  - Confusión, somnolencia",
            "  - Cefalea",
            "  - Parálisis de Todd (debilidad transitoria)",
            "  - Amnesia del evento",
        ],
        risk_factors=[
            "Historia familiar de epilepsia",
            "Lesiones cerebrales (TCE, ACV, tumores)",
            "Infecciones del SNC (meningitis, encefalitis)",
            "Malformaciones del desarrollo cortical",
            "Esclerosis mesial temporal",
            "Anomalías genéticas",
            "Privación de sueño",
            "Uso/abstinencia de alcohol y drogas",
            "Trastornos metabólicos",
            "Prematuridad y complicaciones perinatales",
        ],
        complications=[
            "Status epilepticus",
            "Muerte súbita en epilepsia (SUDEP)",
            "Traumatismos durante crisis",
            "Aspiración",
            "Efectos adversos de FAEs",
            "Deterioro cognitivo",
            "Trastornos psiquiátricos comórbidos (30-40%)",
            "Limitaciones laborales y sociales",
            "Restricciones para conducción",
        ],
        diagnostic_criteria=[
            "DEFINICIÓN ILAE 2014 - Diagnóstico de Epilepsia:",
            "  1. Dos crisis no provocadas separadas por >24h, O",
            "  2. Una crisis no provocada + probabilidad de recurrencia ≥60%, O",
            "  3. Diagnóstico de síndrome epiléptico",
            "",
            "EVALUACIÓN REQUERIDA:",
            "  - Historia clínica detallada (descripción de testigos)",
            "  - EEG (interictal e ictal si posible)",
            "  - RM cerebral protocolo epilepsia (3T, cortes finos)",
            "",
            "CLASIFICACIÓN:",
            "  - Tipo de crisis: focal, generalizada, desconocida",
            "  - Tipo de epilepsia: focal, generalizada, combinada",
            "  - Síndrome epiléptico (si identificable)",
            "  - Etiología: estructural, genética, infecciosa, metabólica, inmune",
        ],
        differential_diagnosis=[
            "Síncope (vasovagal, cardiogénico)",
            "Crisis psicógenas no epilépticas (CPNE)",
            "Trastornos del movimiento paroxísticos",
            "Migraña con aura",
            "Ataques isquémicos transitorios",
            "Parasomnias",
            "Hipoglucemia",
            "Intoxicaciones",
            "Trastornos de pánico",
            "Cataplexia",
        ],
        treatment_protocol={
            "principios_generales": [
                "Iniciar tratamiento tras diagnóstico de epilepsia",
                "Monoterapia inicial en 50-70% de casos",
                "Titular gradualmente hasta dosis efectiva",
                "Selección según tipo de crisis, comorbilidades, interacciones",
                "Objetivo: control total de crisis sin efectos adversos",
            ],
            "faes_primera_linea": {
                "crisis_focales": [
                    "Levetiracetam 500-1500 mg c/12h",
                    "Lamotrigina 100-200 mg c/12h",
                    "Carbamazepina 200-600 mg c/12h (no en ancianos)",
                    "Oxcarbazepina 300-1200 mg c/12h",
                    "Lacosamida 100-200 mg c/12h",
                ],
                "crisis_generalizadas": [
                    "Valproato 500-1500 mg c/12h (evitar en mujeres fértiles)",
                    "Levetiracetam 500-1500 mg c/12h",
                    "Lamotrigina 100-200 mg c/12h (precaución en mioclónicas)",
                ],
                "ausencias": [
                    "Etosuximida 250-500 mg c/12h",
                    "Valproato 500-1500 mg c/12h",
                ],
            },
            "epilepsia_refractaria": [
                "Definición: falla de 2 FAEs apropiados",
                "Referir a centro de epilepsia",
                "Evaluar para cirugía de epilepsia",
                "Considerar: VNS, DBS, dieta cetogénica",
            ],
            "poblaciones_especiales": {
                "embarazo": [
                    "Planificación preconcepcional",
                    "Ácido fólico 4-5 mg/día desde antes de concepción",
                    "Evitar valproato (teratogenicidad)",
                    "Preferir: Levetiracetam, Lamotrigina",
                    "Monitoreo de niveles durante embarazo",
                ],
                "ancianos": [
                    "Iniciar dosis bajas, titular lento",
                    "Preferir: Levetiracetam, Lamotrigina, Lacosamida",
                    "Evitar: inductores enzimáticos (CBZ, PHT)",
                ],
            },
            "suspension_faes": [
                "Considerar tras 2-5 años sin crisis",
                "Factores favorables: EEG normal, RM normal, etiología benigna",
                "Reducir gradualmente en 3-6 meses",
                "Riesgo recurrencia: 30-40%",
            ],
        },
        emergency_signs=[
            "Status epilepticus (crisis >5 min o crisis repetidas)",
            "Crisis en cluster (múltiples en 24h)",
            "Trauma durante crisis",
            "Primera crisis en adulto",
            "Crisis en embarazo",
            "Crisis con fiebre alta en adultos",
            "Déficit neurológico persistente post-ictal",
        ],
        prognosis="""
        60-70% logran control de crisis con FAEs.
        20-30% desarrollan epilepsia refractaria.
        Cirugía: 60-70% libres de crisis en epilepsia temporal mesial.
        SUDEP: 1:1000 pacientes/año (mayor riesgo en refractarios).
        Mortalidad 2-3 veces mayor que población general.
        """,
        follow_up="""
        - Neurología cada 3-6 meses inicialmente
        - Niveles de FAEs según medicamento
        - Función hepática y hemograma anual
        - RM de control si cambio clínico
        - Educación: seguridad, conducción, embarazo
        - Screening depresión/ansiedad
        - Diario de crisis
        """,
    ),
    # -------------------------------------------------------------------------
    # ENFERMEDAD DE PARKINSON
    # -------------------------------------------------------------------------
    "G20": MedicalCondition(
        icd10_code="G20",
        name="Enfermedad de Parkinson",
        category="Neurología - Trastornos del Movimiento",
        description="""
        Trastorno neurodegenerativo progresivo por pérdida de neuronas 
        dopaminérgicas en la sustancia nigra. Segunda enfermedad 
        neurodegenerativa más común. Edad media de inicio: 60 años.
        Afecta 1-2% de mayores de 60 años.
        """,
        symptoms=[
            "SÍNTOMAS MOTORES CARDINALES:",
            "  - Bradicinesia (lentitud de movimientos) - REQUERIDO",
            "  - Temblor de reposo (4-6 Hz, 'cuenta monedas')",
            "  - Rigidez (en rueda dentada)",
            "  - Inestabilidad postural (tardía)",
            "",
            "SÍNTOMAS MOTORES ADICIONALES:",
            "  - Hipomimia (facies de máscara)",
            "  - Hipofonía, disartria",
            "  - Micrografía",
            "  - Marcha festinante, congelamiento",
            "  - Reducción del braceo",
            "",
            "SÍNTOMAS NO MOTORES:",
            "  - Hiposmia (frecuentemente premotor)",
            "  - Constipación crónica",
            "  - Trastorno de conducta del sueño REM",
            "  - Depresión, apatía, ansiedad",
            "  - Deterioro cognitivo (20-40%)",
            "  - Hipotensión ortostática",
            "  - Disfunción urinaria",
            "  - Dolor, fatiga",
        ],
        risk_factors=[
            "Edad avanzada (principal factor)",
            "Historia familiar (10-15%)",
            "Mutaciones genéticas (LRRK2, GBA, PRKN, PINK1, SNCA)",
            "Sexo masculino (1.5:1)",
            "Exposición a pesticidas",
            "Traumatismo craneal",
            "Consumo de agua de pozo rural",
            "FACTORES PROTECTORES: cafeína, tabaco, ejercicio físico",
        ],
        complications=[
            "Fluctuaciones motoras (wearing-off, on-off)",
            "Discinesias inducidas por levodopa",
            "Demencia por enfermedad de Parkinson",
            "Psicosis (alucinaciones, delirios)",
            "Caídas y fracturas",
            "Disfagia con riesgo de aspiración",
            "Síndrome de desregulación dopaminérgica",
            "Depresión resistente",
            "Trastornos del control de impulsos",
        ],
        diagnostic_criteria=[
            "CRITERIOS MDS 2015 - Parkinson Clínicamente Establecido:",
            "",
            "1. PARKINSONISMO:",
            "   - Bradicinesia + Temblor de reposo O Rigidez",
            "",
            "2. CRITERIOS DE SOPORTE (≥2):",
            "   - Respuesta clara y dramática a terapia dopaminérgica",
            "   - Discinesias inducidas por levodopa",
            "   - Temblor de reposo de una extremidad",
            "   - Pérdida olfatoria o denervación cardíaca simpática",
            "",
            "3. AUSENCIA DE CRITERIOS DE EXCLUSIÓN:",
            "   - Signos cerebelosos",
            "   - Parálisis supranuclear de mirada vertical",
            "   - Diagnóstico de DFT o APP",
            "   - Parkinsonismo limitado a MMII por >3 años",
            "   - Tratamiento con bloqueadores dopaminérgicos",
            "",
            "4. AUSENCIA DE RED FLAGS:",
            "   - Progresión rápida",
            "   - Ausencia de progresión en 5 años",
            "   - Disfunción bulbar temprana",
            "   - Insuficiencia respiratoria",
            "   - Disautonomía severa temprana",
        ],
        differential_diagnosis=[
            "Temblor esencial",
            "Parkinsonismo farmacológico",
            "Parkinsonismo vascular",
            "Parálisis supranuclear progresiva (PSP)",
            "Atrofia multisistémica (AMS)",
            "Degeneración corticobasal (DCB)",
            "Demencia con cuerpos de Lewy",
            "Hidrocefalia normotensiva",
            "Enfermedad de Wilson",
        ],
        treatment_protocol={
            "principios": [
                "Tratamiento individualizado según edad, síntomas, comorbilidades",
                "Inicio cuando síntomas afectan calidad de vida",
                "Levodopa es el más efectivo pero considerar complicaciones",
                "Ejercicio físico regular es fundamental",
                "Abordaje multidisciplinario",
            ],
            "enfermedad_temprana": {
                "pacientes_jovenes": [
                    "Agonistas dopaminérgicos: Pramipexol 0.25-1 mg c/8h, Ropinirol 2-8 mg c/8h",
                    "Inhibidores MAO-B: Rasagilina 1 mg/día, Selegilina 5 mg c/12h",
                    "Retrasar levodopa para minimizar discinesias",
                ],
                "pacientes_mayores": [
                    "Levodopa/Carbidopa desde inicio (mejor tolerada)",
                    "Iniciar 100/25 mg c/8h, titular según respuesta",
                    "Evitar agonistas por riesgo de alucinaciones/confusión",
                ],
            },
            "enfermedad_avanzada": {
                "fluctuaciones_motoras": [
                    "Fraccionar dosis de levodopa",
                    "Agregar inhibidor COMT: Entacapona 200 mg c/dosis",
                    "Agregar inhibidor MAO-B",
                    "Agregar agonista dopaminérgico",
                    "Levodopa de liberación prolongada nocturna",
                ],
                "discinesias": [
                    "Reducir dosis de levodopa",
                    "Amantadina 100 mg c/8-12h",
                ],
                "terapias_avanzadas": [
                    "Estimulación cerebral profunda (DBS) - NST o GPi",
                    "Bomba de apomorfina subcutánea",
                    "Infusión duodenal de levodopa (Duodopa)",
                ],
            },
            "sintomas_no_motores": {
                "depresion": "ISRS, Pramipexol (efecto antidepresivo)",
                "deterioro_cognitivo": "Rivastigmina (única aprobada en PD)",
                "psicosis": "Clozapina, Pimavanserina, Quetiapina",
                "hipotension_ortostatica": "Fludrocortisona, Midodrina, medidas posturales",
                "constipacion": "Fibra, laxantes, polietilenglicol",
                "trastorno_rem": "Melatonina, Clonazepam a dosis bajas",
            },
            "rehabilitacion": [
                "Fisioterapia: marcha, equilibrio, prevención caídas",
                "Terapia ocupacional: AVD, adaptaciones",
                "Fonoaudiología: voz (LSVT), deglución",
                "Ejercicio aeróbico regular (30-60 min, 5 días/semana)",
            ],
        },
        emergency_signs=[
            "Síndrome neuroléptico maligno (rigidez severa, fiebre, alteración consciencia)",
            "Crisis acinética (acinesia severa por suspensión brusca de medicación)",
            "Psicosis aguda con agitación",
            "Disfagia severa con aspiración",
            "Caídas con trauma significativo",
            "Discinesias incapacitantes",
        ],
        prognosis="""
        Enfermedad progresiva sin cura actual.
        Respuesta inicial a levodopa excelente ('luna de miel' 3-5 años).
        Fluctuaciones motoras: 50% a los 5 años, 80% a los 10 años.
        Demencia: 40% a los 10 años, 80% a los 20 años.
        Esperanza de vida reducida 1-2 años respecto a población general.
        Calidad de vida puede mantenerse con tratamiento óptimo.
        """,
        follow_up="""
        - Neurología cada 3-6 meses
        - Ajuste progresivo de medicación
        - Evaluación función cognitiva anual (MoCA)
        - Screening depresión y psicosis
        - Fisioterapia y ejercicio continuos
        - Evaluación nutricional y peso
        - Planificación avanzada de cuidados
        - Considerar DBS cuando indicado
        """,
    ),
    # -------------------------------------------------------------------------
    # MIGRAÑA
    # -------------------------------------------------------------------------
    "G43": MedicalCondition(
        icd10_code="G43",
        name="Migraña",
        category="Neurología - Cefaleas Primarias",
        description="""
        Cefalea primaria recurrente caracterizada por ataques de dolor 
        moderado-severo con características específicas. Afecta a 12% de 
        la población. Más frecuente en mujeres (3:1). Clasificación ICHD-3:
        sin aura, con aura, crónica.
        """,
        symptoms=[
            "FASE PRODRÓMICA (horas-días antes):",
            "  - Cambios de ánimo, irritabilidad",
            "  - Fatiga, bostezos",
            "  - Antojos alimentarios",
            "  - Rigidez cervical",
            "",
            "AURA (15-30% de pacientes):",
            "  - Visual: escotomas, fotopsias, espectro de fortificación",
            "  - Sensorial: parestesias progresivas",
            "  - Lenguaje: disfasia transitoria",
            "  - Motor: debilidad (migraña hemipléjica)",
            "  - Duración típica: 5-60 minutos",
            "",
            "FASE DE CEFALEA:",
            "  - Dolor unilateral (60%), puede ser bilateral",
            "  - Pulsátil, de intensidad moderada-severa",
            "  - Duración: 4-72 horas sin tratamiento",
            "  - Agravado por actividad física rutinaria",
            "",
            "SÍNTOMAS ACOMPAÑANTES:",
            "  - Náuseas y/o vómitos",
            "  - Fotofobia y fonofobia",
            "  - Osmofobia",
            "",
            "FASE POSTDRÓMICA:",
            "  - Fatiga, dificultad concentración",
            "  - 'Resaca migrañosa'",
        ],
        risk_factors=[
            "Historia familiar (70% tienen familiar afectado)",
            "Sexo femenino",
            "Cambios hormonales (menstruación, anticonceptivos)",
            "Edad (pico 35-39 años)",
            "",
            "DESENCADENANTES:",
            "  - Estrés o relajación post-estrés",
            "  - Ayuno, saltarse comidas",
            "  - Privación o exceso de sueño",
            "  - Cambios de clima/presión",
            "  - Alimentos: vino tinto, quesos curados, chocolate",
            "  - Luces brillantes, ruidos, olores",
            "  - Deshidratación",
        ],
        complications=[
            "Migraña crónica (≥15 días/mes por >3 meses)",
            "Cefalea por abuso de medicamentos",
            "Status migrañosus (>72 horas)",
            "Infarto migrañoso (raro)",
            "Aura persistente (>1 semana)",
            "Depresión y ansiedad comórbidas",
            "Afectación calidad de vida y productividad",
        ],
        diagnostic_criteria=[
            "CRITERIOS ICHD-3 - MIGRAÑA SIN AURA:",
            "A. Al menos 5 ataques cumpliendo criterios B-D",
            "B. Cefalea 4-72 horas (sin tratamiento)",
            "C. Al menos 2 de:",
            "   - Localización unilateral",
            "   - Cualidad pulsátil",
            "   - Intensidad moderada-severa",
            "   - Agravada por actividad física rutinaria",
            "D. Durante la cefalea al menos 1 de:",
            "   - Náuseas y/o vómitos",
            "   - Fotofobia y fonofobia",
            "E. No atribuible a otro trastorno",
            "",
            "MIGRAÑA CON AURA:",
            "  - Síntomas visuales, sensoriales o del lenguaje",
            "  - Completamente reversibles",
            "  - Desarrollo gradual ≥5 min",
            "  - Duración 5-60 minutos",
            "  - Cefalea sigue al aura (o durante)",
        ],
        differential_diagnosis=[
            "Cefalea tensional",
            "Cefalea en racimos",
            "Cefalea secundaria (tumor, hemorragia, infección)",
            "Arteritis de células gigantes (>50 años)",
            "Hipertensión intracraneal idiopática",
            "Disección arterial cervical",
            "Malformación de Chiari",
            "Trombosis venosa cerebral",
        ],
        treatment_protocol={
            "tratamiento_agudo": {
                "leve_moderado": [
                    "AINEs: Ibuprofeno 400-800 mg, Naproxeno 500-825 mg",
                    "Acetaminofén 1000 mg",
                    "Combinación con cafeína",
                    "Tomar temprano (dentro de 1 hora del inicio)",
                ],
                "moderado_severo": [
                    "Triptanes (agonistas 5-HT1B/1D):",
                    "  - Sumatriptán 50-100 mg VO, 6 mg SC, nasal",
                    "  - Rizatriptán 10 mg (puede repetir a las 2h)",
                    "  - Eletriptán 40 mg",
                    "  - Zolmitriptán 2.5-5 mg",
                    "Gepantes (antagonistas CGRP):",
                    "  - Ubrogepant 50-100 mg",
                    "  - Rimegepant 75 mg (también preventivo)",
                    "Ditanes (agonista 5-HT1F):",
                    "  - Lasmiditan 50-100 mg (evitar conducir)",
                ],
                "rescate": [
                    "Metoclopramida 10 mg IV + Ketorolaco 30 mg IV",
                    "Dexametasona 4-10 mg IV (reduce recurrencia)",
                    "Valproato sódico 500-1000 mg IV",
                    "Sulfato de magnesio 1-2 g IV",
                ],
            },
            "tratamiento_preventivo": {
                "indicaciones": [
                    "≥4 días de migraña/mes",
                    "Ataques incapacitantes a pesar de tratamiento agudo",
                    "Contraindicación o falla de agudos",
                    "Preferencia del paciente",
                    "Migraña hemipléjica o con aura prolongada",
                ],
                "primera_linea": [
                    "Propranolol 40-160 mg/día",
                    "Metoprolol 50-200 mg/día",
                    "Topiramato 50-100 mg/día",
                    "Valproato 500-1500 mg/día (evitar en mujeres fértiles)",
                    "Amitriptilina 25-75 mg noche",
                    "Venlafaxina 75-150 mg/día",
                ],
                "anticuerpos_anti_cgrp": [
                    "Erenumab 70-140 mg SC mensual",
                    "Fremanezumab 225 mg SC mensual o 675 mg trimestral",
                    "Galcanezumab 240 mg carga, luego 120 mg mensual",
                    "Eptinezumab 100-300 mg IV trimestral",
                ],
                "toxina_botulinica": [
                    "Onabotulinumtoxin A para migraña crónica",
                    "155-195 U en 31-39 sitios",
                    "Repetir cada 12 semanas",
                ],
            },
            "medidas_no_farmacologicas": [
                "Identificar y evitar desencadenantes",
                "Higiene del sueño",
                "Ejercicio aeróbico regular",
                "Técnicas de relajación, mindfulness",
                "Biofeedback",
                "Acupuntura",
                "Dieta regular, hidratación adecuada",
            ],
        },
        emergency_signs=[
            "Cefalea en trueno (máxima intensidad en segundos)",
            "Cefalea diferente a patrón habitual",
            "Primera migraña >50 años",
            "Fiebre, rigidez de nuca",
            "Déficit neurológico persistente",
            "Alteración de consciencia",
            "Papiledema",
            "Síntomas sistémicos (pérdida de peso, fiebre)",
        ],
        prognosis="""
        Curso crónico con remisiones y exacerbaciones.
        30-40% experimentan remisión prolongada con la edad.
        Migraña puede mejorar en menopausia (hormonal).
        Cronificación si abuso de analgésicos.
        Preventivos reducen 50% la frecuencia en 50% de pacientes.
        Anti-CGRP: 50% reducción en 50-70% de pacientes.
        """,
        follow_up="""
        - Neurología: 4-8 semanas tras inicio de preventivo
        - Diario de cefaleas (días, intensidad, medicación)
        - Evaluar días de cefalea/mes y discapacidad (MIDAS, HIT-6)
        - Ajustar preventivo si <50% reducción en 2-3 meses
        - Vigilar abuso de medicación (≥10-15 días/mes)
        - Screening comorbilidades: depresión, ansiedad, insomnio
        """,
    ),
    # -------------------------------------------------------------------------
    # ESCLEROSIS MÚLTIPLE
    # -------------------------------------------------------------------------
    "G35": MedicalCondition(
        icd10_code="G35",
        name="Esclerosis Múltiple",
        category="Neurología - Enfermedades Desmielinizantes",
        description="""
        Enfermedad inflamatoria crónica desmielinizante del SNC.
        Principal causa de discapacidad neurológica no traumática en adultos 
        jóvenes. Edad típica de inicio: 20-40 años. Más frecuente en mujeres (3:1).
        Formas: Recurrente-Remitente (85%), Primaria Progresiva (15%).
        """,
        symptoms=[
            "SÍNTOMAS COMUNES DE BROTE:",
            "  - Neuritis óptica (dolor ocular, pérdida visual)",
            "  - Debilidad de extremidades",
            "  - Parestesias, hipoestesia",
            "  - Diplopía",
            "  - Vértigo, ataxia",
            "  - Signo de Lhermitte (descarga eléctrica al flexionar cuello)",
            "  - Disfunción vesical (urgencia, retención)",
            "",
            "SÍNTOMAS CRÓNICOS:",
            "  - Fatiga (80% de pacientes)",
            "  - Espasticidad",
            "  - Disfunción cognitiva (40-70%)",
            "  - Depresión (50%)",
            "  - Dolor neuropático",
            "  - Disfunción sexual",
            "  - Sensibilidad al calor (fenómeno de Uhthoff)",
        ],
        risk_factors=[
            "Sexo femenino",
            "Edad 20-40 años",
            "Raza caucásica",
            "Latitud alta (menos exposición solar)",
            "Deficiencia de vitamina D",
            "Infección por virus Epstein-Barr",
            "Historia familiar (10-15x riesgo si familiar primer grado)",
            "Tabaquismo (acelera progresión)",
            "Obesidad en adolescencia",
        ],
        complications=[
            "Progresión de discapacidad (EDSS)",
            "Forma secundaria progresiva (50% a 15 años)",
            "Deterioro cognitivo",
            "Depresión y ansiedad",
            "Infecciones urinarias recurrentes",
            "Úlceras por presión",
            "Osteoporosis (inmovilidad, corticoides)",
            "Caídas y fracturas",
            "Neumonía aspirativa",
        ],
        diagnostic_criteria=[
            "CRITERIOS McDONALD 2017:",
            "",
            "1. DISEMINACIÓN EN ESPACIO (DIS):",
            "   - Lesiones en ≥2 regiones típicas del SNC:",
            "     * Periventricular (≥3 lesiones)",
            "     * Cortical/yuxtacortical (≥1)",
            "     * Infratentorial (≥1)",
            "     * Médula espinal (≥1)",
            "",
            "2. DISEMINACIÓN EN TIEMPO (DIT):",
            "   - Lesiones simultáneas con y sin realce de gadolinio, O",
            "   - Nueva lesión T2 o con realce en RM de seguimiento, O",
            "   - Presencia de bandas oligoclonales en LCR",
            "",
            "3. FORMAS CLÍNICAS:",
            "   - EMRR: ≥2 ataques clínicos + DIS",
            "   - 1 ataque + evidencia objetiva + DIS + DIT",
            "   - EMPP: ≥1 año de progresión + 2/3 criterios adicionales",
            "",
            "ESTUDIOS:",
            "  - RM cerebral y médula con gadolinio",
            "  - LCR: bandas oligoclonales, índice IgG",
            "  - Potenciales evocados visuales",
        ],
        differential_diagnosis=[
            "Neuromielitis óptica (NMOSD)",
            "MOGAD (anti-MOG)",
            "Lupus eritematoso sistémico neurológico",
            "Síndrome de Sjögren",
            "Enfermedad de Behçet",
            "Neurosarcoidosis",
            "Déficit de vitamina B12",
            "Vasculitis del SNC",
            "CADASIL",
            "Encefalomielitis aguda diseminada (ADEM)",
        ],
        treatment_protocol={
            "tratamiento_brotes": [
                "Metilprednisolona 1 g IV diario x 3-5 días",
                "Opción oral: Prednisona 1250 mg diarios x 3-5 días",
                "Plasmaféresis si brote severo refractario a esteroides",
                "Profilaxis gástrica durante esteroides",
            ],
            "terapias_modificadoras_emrr": {
                "eficacia_moderada": [
                    "Interferón beta-1a (Avonex 30 μg IM semanal, Rebif 44 μg SC 3x/sem)",
                    "Interferón beta-1b (Betaseron 250 μg SC cada 48h)",
                    "Acetato de glatiramer 20 mg SC diario o 40 mg 3x/sem",
                    "Teriflunomida 14 mg VO diario",
                    "Fumaratos: Dimetil fumarato 240 mg c/12h",
                ],
                "alta_eficacia": [
                    "Natalizumab 300 mg IV mensual (riesgo LMP si JCV+)",
                    "Fingolimod 0.5 mg VO diario (1ª dosis monitorizada)",
                    "Ocrelizumab 600 mg IV cada 6 meses (anti-CD20)",
                    "Ofatumumab 20 mg SC mensual",
                    "Alemtuzumab 12 mg IV x 5 días, luego 12 mg x 3 días al año",
                    "Cladribina 3.5 mg/kg dividido en 2 años",
                ],
            },
            "empp": [
                "Ocrelizumab (único aprobado para EMPP)",
                "300 mg IV en semanas 0 y 2, luego 600 mg cada 6 meses",
            ],
            "manejo_sintomas": {
                "fatiga": "Amantadina 100 mg c/12h, modafinilo, ejercicio",
                "espasticidad": "Baclofeno 5-20 mg c/8h, tizanidina, fisioterapia",
                "dolor_neuropatico": "Gabapentina, pregabalina, duloxetina, amitriptilina",
                "vejiga": "Oxibutinina, mirabegron, autocateterismo",
                "depresion": "ISRS, terapia cognitivo-conductual",
                "deterioro_cognitivo": "Rehabilitación cognitiva",
            },
            "rehabilitacion": [
                "Fisioterapia: fuerza, equilibrio, marcha",
                "Terapia ocupacional",
                "Rehabilitación cognitiva",
                "Ejercicio aeróbico y resistencia (beneficio demostrado)",
            ],
        },
        emergency_signs=[
            "Brote severo con déficit neurológico significativo",
            "Mielitis transversa con paraplejia",
            "Neuritis óptica bilateral",
            "Afectación troncoencefálica con disfagia/respiratoria",
            "Deterioro cognitivo agudo",
            "Sospecha de LMP (si en natalizumab)",
        ],
        prognosis="""
        Variable, difícil predecir curso individual.
        EMRR: 50% pasan a EMSP a los 15-20 años sin tratamiento.
        Con TMEs modernas, pronóstico significativamente mejor.
        Factores favorables: sexo femenino, inicio joven, síntomas sensitivos.
        Factores desfavorables: inicio motor, alta carga lesional, progresión temprana.
        Esperanza de vida reducida 7-10 años respecto a población general.
        """,
        follow_up="""
        - Neurología cada 3-6 meses
        - RM cerebral anual (o ante sospecha de brote)
        - Monitoreo según TME (labs, riesgo LMP, vacunas)
        - EDSS anual para documentar progresión
        - Screening función cognitiva (BICAMS)
        - Vitamina D (mantener >40 ng/mL)
        - Vacunación (evitar vacunas vivas si inmunosuprimido)
        - Planificación familiar (muchos TMEs contraindicados en embarazo)
        """,
    ),
    # -------------------------------------------------------------------------
    # DEMENCIA (ENFERMEDAD DE ALZHEIMER)
    # -------------------------------------------------------------------------
    "G30": MedicalCondition(
        icd10_code="G30",
        name="Enfermedad de Alzheimer",
        category="Neurología - Enfermedades Neurodegenerativas",
        description="""
        Enfermedad neurodegenerativa progresiva caracterizada por deterioro 
        cognitivo y demencia. Principal causa de demencia (60-70%).
        Patología: depósitos de amiloide-beta y ovillos neurofibrilares de tau.
        Afecta a 5-10% de >65 años, 30-50% de >85 años.
        """,
        symptoms=[
            "DETERIORO COGNITIVO:",
            "  - Memoria episódica (síntoma inicial típico)",
            "  - Desorientación temporal y espacial",
            "  - Disfunción ejecutiva",
            "  - Alteración del lenguaje (anomia, afasia)",
            "  - Apraxia (dificultad para tareas aprendidas)",
            "  - Agnosia (dificultad para reconocer objetos/personas)",
            "  - Alteración visuoespacial",
            "",
            "SÍNTOMAS CONDUCTUALES Y PSICOLÓGICOS:",
            "  - Apatía (más frecuente)",
            "  - Depresión",
            "  - Ansiedad",
            "  - Agitación, irritabilidad",
            "  - Delirios (paranoides)",
            "  - Alucinaciones (más en etapas avanzadas)",
            "  - Alteración del sueño",
            "  - Desinhibición",
            "  - Conducta motora aberrante (vagabundeo)",
        ],
        risk_factors=[
            "Edad avanzada (principal factor)",
            "Historia familiar",
            "Genotipo APOE ε4 (1 alelo: 3x riesgo, 2 alelos: 12x)",
            "Síndrome de Down",
            "Traumatismo craneal previo",
            "Bajo nivel educativo",
            "Factores vasculares: HTA, DM, dislipidemia, obesidad",
            "Sedentarismo",
            "Aislamiento social",
            "Depresión",
            "Pérdida auditiva",
        ],
        complications=[
            "Pérdida progresiva de independencia",
            "Caídas y fracturas",
            "Desnutrición, deshidratación",
            "Infecciones (urinarias, respiratorias)",
            "Disfagia con aspiración",
            "Úlceras por presión",
            "Agotamiento del cuidador",
            "Institutionalización",
            "Muerte (neumonía, infecciones, falla orgánica)",
        ],
        diagnostic_criteria=[
            "CRITERIOS NIA-AA 2011/2018:",
            "",
            "1. DEMENCIA:",
            "   - Síntomas cognitivos/conductuales que:",
            "     * Interfieren con trabajo o actividades habituales",
            "     * Representan declive del nivel previo",
            "     * No se explican por delirium o trastorno psiquiátrico",
            "   - Deterioro en ≥2 dominios cognitivos",
            "",
            "2. DEMENCIA PROBABLE POR ALZHEIMER:",
            "   - Inicio insidioso (meses-años)",
            "   - Historia clara de empeoramiento progresivo",
            "   - Patrón amnésico típico (más común)",
            "   - Sin evidencia de otra etiología",
            "",
            "BIOMARCADORES (confirman patología):",
            "   - PET amiloide o tau positivo",
            "   - LCR: Aβ42 bajo, tau y p-tau elevados",
            "   - RM: atrofia temporal medial (escala Scheltens)",
            "",
            "EVALUACIÓN:",
            "   - Mini-Mental (MMSE), MoCA",
            "   - Evaluación neuropsicológica formal",
            "   - RM cerebral",
            "   - Laboratorio: TSH, B12, folato, función hepática/renal",
            "   - Considerar LCR/PET si diagnóstico incierto",
        ],
        differential_diagnosis=[
            "Deterioro cognitivo leve (DCL)",
            "Demencia vascular",
            "Demencia con cuerpos de Lewy",
            "Demencia frontotemporal",
            "Enfermedad de Parkinson con demencia",
            "Hidrocefalia normotensiva (reversible)",
            "Déficit de vitamina B12 (reversible)",
            "Hipotiroidismo (reversible)",
            "Depresión (pseudodemencia)",
            "Efectos de medicamentos",
        ],
        treatment_protocol={
            "inhibidores_colinesterasa": {
                "indicacion": "EA leve-moderada",
                "opciones": [
                    "Donepezilo 5-10 mg/día (bien tolerado)",
                    "Rivastigmina 3-12 mg/día VO o parche 4.6-13.3 mg/24h",
                    "Galantamina 8-24 mg/día",
                ],
                "efectos_adversos": "Náuseas, diarrea, bradicardia",
                "contraindicaciones": "Bradicardia severa, bloqueo AV, asma severa",
            },
            "memantina": {
                "indicacion": "EA moderada-severa (o combinada con ICE)",
                "dosis": "5-20 mg/día (titulación semanal)",
                "mecanismo": "Antagonista NMDA",
            },
            "nuevos_tratamientos": [
                "Anticuerpos anti-amiloide (terapias modificadoras):",
                "  - Lecanemab (aprobado FDA 2023): 10 mg/kg IV cada 2 sem",
                "  - Donanemab: en evaluación",
                "Requieren confirmación de amiloide y monitoreo ARIA",
            ],
            "manejo_sintomas_conductuales": {
                "no_farmacologico_primero": [
                    "Identificar desencadenantes",
                    "Establecer rutinas",
                    "Ambiente seguro y tranquilo",
                    "Musicoterapia, aromaterapia",
                    "Actividades significativas",
                ],
                "farmacologico": {
                    "depresion": "ISRS (Sertralina, Citalopram ≤20 mg)",
                    "agitacion_leve": "Trazodona 25-100 mg",
                    "agitacion_severa": "Risperidona 0.25-1 mg (FDA black box)",
                    "insomnio": "Trazodona, melatonina (evitar benzodiacepinas)",
                },
            },
            "medidas_generales": [
                "Ejercicio físico regular",
                "Estimulación cognitiva",
                "Nutrición adecuada",
                "Control de factores de riesgo vascular",
                "Seguridad en el hogar",
                "Planificación legal y financiera temprana",
                "Apoyo al cuidador",
            ],
        },
        emergency_signs=[
            "Delirium (cambio agudo de consciencia/cognición)",
            "Agitación severa con riesgo de daño",
            "Caídas con trauma",
            "Deterioro cognitivo rápido (pensar en otra causa)",
            "Fiebre en paciente institucionalizado",
            "Disfagia severa con aspiración",
            "Negativa a comer/beber",
        ],
        prognosis="""
        Enfermedad progresiva e irreversible.
        Supervivencia media desde diagnóstico: 4-8 años.
        Variable según edad de inicio y comorbilidades.
        Fases: leve (2-4 años), moderada (2-10 años), severa (1-3 años).
        Nuevas terapias anti-amiloide pueden enlentecer progresión.
        Causa de muerte: neumonía, infecciones, complicaciones de inmovilidad.
        """,
        follow_up="""
        - Neurología/Geriatría cada 6 meses
        - Reevaluación cognitiva anual (MMSE, MoCA)
        - Ajuste de medicación según tolerancia y progresión
        - Evaluación nutricional y peso
        - Screening depresión y trastornos conductuales
        - Educación y apoyo al cuidador
        - Planificación avanzada de cuidados
        - Referencia a grupos de apoyo
        - Considerar cuidados paliativos en etapas avanzadas
        """,
    ),
}


# =============================================================================
# FUNCIONES DE ACCESO
# =============================================================================


def get_neurological_conditions() -> Dict[str, MedicalCondition]:
    """Retorna todas las condiciones neurológicas."""
    return NEUROLOGICAL_CONDITIONS


def get_condition_by_code(icd10_code: str) -> Optional[MedicalCondition]:
    """Busca una condición por código ICD-10."""
    return NEUROLOGICAL_CONDITIONS.get(icd10_code)


def search_conditions(query: str) -> List[MedicalCondition]:
    """Busca condiciones por nombre o descripción."""
    query_lower = query.lower()
    results = []
    for condition in NEUROLOGICAL_CONDITIONS.values():
        if (
            query_lower in condition.name.lower()
            or query_lower in condition.description.lower()
            or query_lower in condition.category.lower()
        ):
            results.append(condition)
    return results


# =============================================================================
# INFORMACIÓN DEL MÓDULO
# =============================================================================

MODULE_INFO = {
    "name": "Condiciones Neurológicas",
    "version": "1.0.0",
    "conditions_count": len(NEUROLOGICAL_CONDITIONS),
    "icd10_chapter": "VI - Enfermedades del Sistema Nervioso (G00-G99)",
    "sources": [
        "AHA/ASA Stroke Guidelines 2019-2024",
        "International League Against Epilepsy (ILAE) 2017",
        "Movement Disorder Society (MDS) 2015",
        "International Headache Society ICHD-3 2018",
        "McDonald Criteria for MS 2017",
        "NIA-AA Alzheimer Criteria 2011/2018",
    ],
}


if __name__ == "__main__":
    print(f"Módulo: {MODULE_INFO['name']}")
    print(f"Condiciones: {MODULE_INFO['conditions_count']}")
    print("\nCondiciones incluidas:")
    for code, cond in NEUROLOGICAL_CONDITIONS.items():
        print(f"  {code}: {cond.name}")
