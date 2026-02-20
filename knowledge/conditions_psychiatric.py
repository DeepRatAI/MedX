#!/usr/bin/env python3
"""
🧠 Condiciones Psiquiátricas - Base de Conocimiento Expandida
Basado en: DSM-5-TR, ICD-10-CM 2026, APA Practice Guidelines

Cobertura:
- Trastornos Depresivos (F32-F33)
- Trastornos de Ansiedad (F40-F41)
- Trastorno Bipolar (F31)
- Esquizofrenia (F20)
- TEPT (F43.1)
- TOC (F42)
- TDAH (F90)
- Trastornos de Personalidad
"""

from dataclasses import dataclass
from typing import List


try:
    from medical_knowledge_base import MedicalCondition
except ImportError:

    @dataclass
    class MedicalCondition:
        icd10_code: str
        name: str
        category: str
        description: str
        symptoms: List[str]
        risk_factors: List[str]
        complications: List[str]
        diagnostic_criteria: List[str]
        differential_diagnosis: List[str]
        treatment_protocol: List[str]
        emergency_signs: List[str]
        prognosis: str
        follow_up: List[str]


PSYCHIATRIC_CONDITIONS = {
    # =========================================================================
    # TRASTORNO DEPRESIVO MAYOR (F32)
    # =========================================================================
    "F32": MedicalCondition(
        icd10_code="F32",
        name="Trastorno Depresivo Mayor (Episodio Único)",
        category="Psiquiatría",
        description="Trastorno del estado de ánimo caracterizado por episodio de ánimo deprimido o anhedonia, con síntomas cognitivos, somáticos y conductuales durante al menos 2 semanas.",
        symptoms=[
            "Ánimo deprimido la mayor parte del día",
            "Anhedonia (pérdida de interés/placer)",
            "Cambios de peso/apetito (>5% en un mes)",
            "Insomnio o hipersomnia",
            "Agitación o enlentecimiento psicomotor",
            "Fatiga o pérdida de energía",
            "Sentimientos de inutilidad o culpa excesiva",
            "Dificultad para concentrarse",
            "Pensamientos de muerte o ideación suicida",
        ],
        risk_factors=[
            "Historia familiar de depresión",
            "Episodios depresivos previos",
            "Eventos vitales estresantes",
            "Trauma infantil",
            "Enfermedades crónicas",
            "Sexo femenino (2:1)",
            "Aislamiento social",
            "Abuso de sustancias",
        ],
        complications=[
            "Suicidio - EMERGENCIA",
            "Autolesiones",
            "Deterioro funcional (laboral, social, familiar)",
            "Abuso de sustancias comórbido",
            "Empeoramiento enfermedades médicas",
            "Cronificación → depresión recurrente",
        ],
        diagnostic_criteria=[
            "≥5 síntomas durante ≥2 semanas (DSM-5)",
            "Debe incluir ánimo deprimido O anhedonia",
            "Causar malestar o deterioro significativo",
            "No atribuible a sustancias ni otra condición médica",
            "PHQ-9 ≥10: probable depresión",
            "Escala HAM-D o MADRS para severidad",
        ],
        differential_diagnosis=[
            "Trastorno bipolar (descartar manía)",
            "Distimia (trastorno depresivo persistente)",
            "Trastorno de adaptación con ánimo deprimido",
            "Duelo no complicado",
            "Hipotiroidismo",
            "Depresión secundaria (Parkinson, ACV)",
            "Abuso de sustancias",
        ],
        treatment_protocol=[
            "LEVE: Psicoterapia (TCC, interpersonal) como 1ª línea",
            "MODERADA-SEVERA: Antidepresivo + psicoterapia",
            "ISRS 1ª línea: Sertralina 50-200 mg/día, Escitalopram 10-20 mg/día",
            "Alternativas: IRSN (Venlafaxina, Duloxetina), Bupropion, Mirtazapina",
            "Respuesta esperada: 4-6 semanas",
            "Duración: ≥6-12 meses tras remisión (1er episodio)",
            "REFRACTARIA: Potenciación (litio, aripiprazol), TEC, ketamina/esketamina",
        ],
        emergency_signs=[
            "Ideación suicida con plan",
            "Intento de suicidio reciente",
            "Síntomas psicóticos (alucinaciones, delirios)",
            "Incapacidad para cuidado personal",
            "Riesgo de daño a otros",
        ],
        prognosis="50-60% remisión con tratamiento adecuado. 50% riesgo de recurrencia tras primer episodio, aumenta con cada episodio.",
        follow_up=[
            "Seguimiento semanal-bisemanal al inicio",
            "Evaluación de efectos adversos",
            "PHQ-9 cada visita para monitorear respuesta",
            "Evaluación de ideación suicida cada visita",
            "Psicoeducación sobre adherencia y efectos",
        ],
    ),
    # =========================================================================
    # TRASTORNO DE ANSIEDAD GENERALIZADA (F41.1)
    # =========================================================================
    "F41.1": MedicalCondition(
        icd10_code="F41.1",
        name="Trastorno de Ansiedad Generalizada",
        category="Psiquiatría",
        description="Ansiedad y preocupación excesivas, difíciles de controlar, sobre múltiples áreas de la vida, la mayoría de los días durante al menos 6 meses.",
        symptoms=[
            "Preocupación excesiva, difícil de controlar",
            "Inquietud o sensación de nerviosismo",
            "Fatigabilidad fácil",
            "Dificultad para concentrarse",
            "Irritabilidad",
            "Tensión muscular",
            "Alteraciones del sueño (dificultad para iniciar/mantener)",
        ],
        risk_factors=[
            "Historia familiar de trastornos de ansiedad",
            "Temperamento inhibido/evitativo",
            "Eventos vitales adversos",
            "Enfermedades crónicas",
            "Sexo femenino (2:1)",
            "Otros trastornos de ansiedad comórbidos",
            "Depresión comórbida",
        ],
        complications=[
            "Depresión comórbida (60%)",
            "Otros trastornos de ansiedad",
            "Trastorno por uso de sustancias",
            "Deterioro funcional significativo",
            "Somatización",
            "Síndrome de intestino irritable",
        ],
        diagnostic_criteria=[
            "Ansiedad y preocupación excesivas ≥6 meses",
            "≥3 de 6 síntomas asociados (DSM-5)",
            "Malestar o deterioro significativo",
            "No atribuible a sustancias ni otra condición médica",
            "GAD-7 ≥10: probable TAG",
        ],
        differential_diagnosis=[
            "Trastorno de pánico",
            "Fobia social",
            "TOC",
            "TEPT",
            "Hipertiroidismo",
            "Abuso de cafeína/estimulantes",
            "Abstinencia de sustancias",
            "Feocromocitoma",
        ],
        treatment_protocol=[
            "PSICOTERAPIA: TCC (1ª línea, eficacia comparable a fármacos)",
            "FARMACOTERAPIA:",
            "ISRS 1ª línea: Escitalopram 10-20 mg, Sertralina 50-200 mg",
            "IRSN: Venlafaxina XR 75-225 mg, Duloxetina 60-120 mg",
            "Buspirona 15-60 mg/día (no sedante, sin dependencia)",
            "BENZODIACEPINAS: solo corto plazo (2-4 semanas) por riesgo dependencia",
            "Pregabalina 150-600 mg/día (alternativa)",
        ],
        emergency_signs=[
            "Ideación suicida",
            "Incapacidad funcional severa",
            "Síntomas psicóticos",
            "Abuso de sustancias comórbido severo",
        ],
        prognosis="Curso crónico y fluctuante. Con tratamiento, 50-60% mejoran significativamente. Remisión completa en 30-40%.",
        follow_up=[
            "Evaluación de respuesta cada 2-4 semanas al inicio",
            "GAD-7 periódico",
            "Monitoreo efectos adversos de medicación",
            "TCC: 12-20 sesiones típicamente",
            "Mantenimiento largo plazo frecuente",
        ],
    ),
    # =========================================================================
    # TRASTORNO DE PÁNICO (F41.0)
    # =========================================================================
    "F41.0": MedicalCondition(
        icd10_code="F41.0",
        name="Trastorno de Pánico",
        category="Psiquiatría",
        description="Ataques de pánico recurrentes e inesperados con preocupación persistente por nuevos ataques o cambio conductual desadaptativo relacionado.",
        symptoms=[
            "ATAQUE DE PÁNICO (pico en minutos, ≥4 síntomas):",
            "Palpitaciones, taquicardia",
            "Sudoración",
            "Temblor",
            "Sensación de falta de aire",
            "Opresión torácica",
            "Náuseas, molestias abdominales",
            "Mareo, inestabilidad",
            "Parestesias",
            "Escalofríos o oleadas de calor",
            "Despersonalización/desrealización",
            "Miedo a perder el control o morir",
            "Ansiedad anticipatoria entre ataques",
            "Conductas de evitación",
        ],
        risk_factors=[
            "Historia familiar de trastorno de pánico",
            "Ansiedad por separación en infancia",
            "Tabaquismo",
            "Eventos vitales estresantes",
            "Sexo femenino (2:1)",
            "Prolapso válvula mitral (asociación)",
        ],
        complications=[
            "Agorafobia (30-50%)",
            "Depresión comórbida",
            "Abuso de alcohol/benzodiacepinas",
            "Deterioro funcional severo",
            "Ideación suicida",
            "Uso excesivo de servicios de urgencias",
        ],
        diagnostic_criteria=[
            "Ataques de pánico inesperados recurrentes",
            "≥1 mes de preocupación por ataques o cambio conductual",
            "≥4 síntomas durante el ataque",
            "Pico de intensidad en minutos",
            "Descartar causas médicas y sustancias",
            "PDSS (Panic Disorder Severity Scale) para severidad",
        ],
        differential_diagnosis=[
            "Trastornos cardíacos (arritmias, SCA)",
            "Hipertiroidismo",
            "Feocromocitoma",
            "Hipoglucemia",
            "Intoxicación por cafeína/estimulantes",
            "Abstinencia de sustancias",
            "Crisis asmática",
            "Epilepsia del lóbulo temporal",
        ],
        treatment_protocol=[
            "FARMACOTERAPIA 1ª línea:",
            "ISRS: Sertralina 50-200 mg, Paroxetina 20-60 mg, Fluoxetina 20-60 mg",
            "Iniciar dosis bajas (riesgo de activación inicial)",
            "IRSN: Venlafaxina XR 75-225 mg",
            "BENZODIACEPINAS: uso transitorio al inicio o PRN (Clonazepam, Alprazolam)",
            "PSICOTERAPIA: TCC (exposición interoceptiva), eficacia alta",
            "Combinación fármaco + TCC: mejor resultado",
            "Duración tratamiento: ≥12 meses tras remisión",
        ],
        emergency_signs=[
            "Ideación suicida",
            "Abuso de benzodiacepinas/alcohol",
            "Deterioro funcional severo con aislamiento",
            "Síntomas que requieren descartar causa médica urgente",
        ],
        prognosis="70-90% mejoran con tratamiento. 30% logran remisión completa a largo plazo. Curso frecuentemente crónico con recaídas.",
        follow_up=[
            "Seguimiento cada 2-4 semanas al inicio",
            "Monitoreo de frecuencia de ataques",
            "Evaluación de conductas de evitación",
            "TCC: 12-16 sesiones típicamente",
            "Reducción gradual de benzodiacepinas si usadas",
        ],
    ),
    # =========================================================================
    # TRASTORNO BIPOLAR I (F31)
    # =========================================================================
    "F31": MedicalCondition(
        icd10_code="F31",
        name="Trastorno Bipolar I",
        category="Psiquiatría",
        description="Trastorno del estado de ánimo caracterizado por episodios de manía (≥7 días) que pueden alternar con episodios depresivos. Alta carga de enfermedad.",
        symptoms=[
            "MANÍA (≥7 días, ≥3 síntomas):",
            "Ánimo elevado, expansivo o irritable",
            "Grandiosidad o autoestima exagerada",
            "Disminución de necesidad de sueño",
            "Verborrea, presión del habla",
            "Fuga de ideas, pensamiento acelerado",
            "Distraibilidad",
            "Aumento de actividad dirigida a metas",
            "Conductas de riesgo (gastos, sexuales, negocios)",
            "DEPRESIÓN BIPOLAR: igual que depresión unipolar",
            "Hipomanía: síntomas menos severos, ≥4 días, sin hospitalización",
        ],
        risk_factors=[
            "Historia familiar fuerte (heredabilidad 60-85%)",
            "Eventos vitales estresantes",
            "Alteraciones del sueño",
            "Uso de sustancias",
            "Antidepresivos (pueden precipitar manía)",
        ],
        complications=[
            "Suicidio (15-20% intentan, 6% mueren por suicidio)",
            "Abuso de sustancias (40-60%)",
            "Deterioro funcional significativo",
            "Problemas legales/financieros en manía",
            "Hospitalización psiquiátrica",
            "Síntomas psicóticos",
        ],
        diagnostic_criteria=[
            "≥1 episodio maníaco (DSM-5)",
            "Manía: ≥7 días de ánimo elevado/irritable + ≥3 síntomas",
            "Deterioro funcional marcado u hospitalización",
            "No atribuible a sustancias",
            "MDQ (Mood Disorder Questionnaire) para screening",
            "YMRS para severidad de manía",
        ],
        differential_diagnosis=[
            "Trastorno depresivo mayor (sin manía)",
            "Trastorno bipolar II (solo hipomanía)",
            "Trastorno esquizoafectivo",
            "Trastorno de personalidad límite",
            "Manía secundaria (corticoides, estimulantes, hipertiroidismo)",
            "TDAH en adultos",
        ],
        treatment_protocol=[
            "MANÍA AGUDA:",
            "Estabilizadores: Litio 900-1800 mg/día (nivel 0.8-1.2 mEq/L), Valproato 750-3000 mg/día",
            "Antipsicóticos atípicos: Quetiapina, Olanzapina, Risperidona, Aripiprazol",
            "Suspender antidepresivos",
            "DEPRESIÓN BIPOLAR:",
            "Quetiapina monoterapia (1ª línea)",
            "Lamotrigina (prevención recaídas depresivas)",
            "Lurasidona",
            "EVITAR antidepresivos solos (riesgo de switch)",
            "MANTENIMIENTO: Litio (reduce suicidio), valproato, lamotrigina, antipsicóticos",
        ],
        emergency_signs=[
            "Manía severa con psicosis",
            "Ideación/conducta suicida",
            "Conductas de alto riesgo (agresividad, gastos, sexual)",
            "Incapacidad para cuidado personal",
            "Síndrome neuroléptico maligno o toxicidad por litio",
        ],
        prognosis="Crónico con episodios recurrentes. Con tratamiento, muchos logran estabilidad. Sin tratamiento: deterioro progresivo.",
        follow_up=[
            "Niveles de litio cada 3 meses (estable), más frecuente al inicio",
            "Función renal y tiroidea cada 6-12 meses con litio",
            "Hemograma y hepático con valproato",
            "Peso y perfil metabólico con antipsicóticos",
            "Psicoeducación sobre pródromos y adherencia",
        ],
    ),
    # =========================================================================
    # ESQUIZOFRENIA (F20)
    # =========================================================================
    "F20": MedicalCondition(
        icd10_code="F20",
        name="Esquizofrenia",
        category="Psiquiatría",
        description="Trastorno psicótico crónico caracterizado por síntomas positivos (delirios, alucinaciones), negativos (aplanamiento, abulia) y deterioro cognitivo y funcional.",
        symptoms=[
            "SÍNTOMAS POSITIVOS:",
            "Delirios (persecución, referencia, grandeza, control)",
            "Alucinaciones (auditivas más comunes)",
            "Pensamiento desorganizado",
            "Conducta desorganizada o catatónica",
            "SÍNTOMAS NEGATIVOS:",
            "Aplanamiento afectivo",
            "Alogia (pobreza del habla)",
            "Abulia (falta de motivación)",
            "Anhedonia",
            "Aislamiento social",
            "DETERIORO COGNITIVO: memoria, atención, funciones ejecutivas",
        ],
        risk_factors=[
            "Historia familiar (10x riesgo si padre/hermano afectado)",
            "Complicaciones perinatales",
            "Migración/urbanicidad",
            "Uso de cannabis en adolescencia",
            "Trauma infantil",
            "Edad de inicio: 18-25 (hombres), 25-35 (mujeres)",
        ],
        complications=[
            "Suicidio (5-10% mueren por suicidio)",
            "Abuso de sustancias comórbido (50%)",
            "Síndrome metabólico (antipsicóticos)",
            "Mortalidad prematura (15-20 años menos de expectativa)",
            "Desempleo, pobreza",
            "Problemas legales",
        ],
        diagnostic_criteria=[
            "≥2 síntomas característicos durante ≥1 mes (1 debe ser delirio, alucinación o pensamiento desorganizado)",
            "Disfunción continua ≥6 meses",
            "Deterioro funcional significativo",
            "Descartar trastorno afectivo con psicosis",
            "No atribuible a sustancias ni otra condición médica",
            "PANSS para severidad de síntomas",
        ],
        differential_diagnosis=[
            "Trastorno psicótico breve",
            "Trastorno esquizofreniforme",
            "Trastorno esquizoafectivo",
            "Trastorno delirante",
            "Psicosis por sustancias",
            "Psicosis secundaria a condición médica",
            "Trastorno bipolar con síntomas psicóticos",
        ],
        treatment_protocol=[
            "ANTIPSICÓTICOS obligatorios (reducen recaídas 60-70%):",
            "2ª generación preferidos: Risperidona 2-6 mg, Olanzapina 10-20 mg, Quetiapina 400-800 mg, Aripiprazol 10-30 mg",
            "1ª generación: Haloperidol 5-20 mg si no disponibles atípicos",
            "REFRACTARIA (≥2 antipsicóticos fallidos): Clozapina (único con evidencia)",
            "Long-acting injectables (LAI) para adherencia",
            "REHABILITACIÓN PSICOSOCIAL: fundamental",
            "Terapia ocupacional, apoyo empleo, entrenamiento habilidades sociales",
            "Intervención familiar",
        ],
        emergency_signs=[
            "Psicosis aguda con agitación",
            "Ideación/conducta suicida",
            "Catatonia (inmovilidad, mutismo)",
            "Síndrome neuroléptico maligno",
            "Incapacidad para cuidado básico",
        ],
        prognosis="Variable. 20% buen pronóstico con recuperación funcional. 60% curso crónico con recaídas. 20% curso severo deteriorante.",
        follow_up=[
            "Seguimiento mensual inicialmente, luego cada 1-3 meses",
            "Monitoreo de síntomas y funcionamiento",
            "Peso, glucosa, lípidos, PA cada 3-6 meses (síndrome metabólico)",
            "Con clozapina: hemograma semanal x 6 meses, luego quincenal",
            "Densitometría ósea (hiperprolactinemia)",
        ],
    ),
    # =========================================================================
    # TRASTORNO POR ESTRÉS POSTRAUMÁTICO (F43.1)
    # =========================================================================
    "F43.1": MedicalCondition(
        icd10_code="F43.1",
        name="Trastorno por Estrés Postraumático (TEPT)",
        category="Psiquiatría",
        description="Trastorno que se desarrolla tras exposición a evento traumático, con síntomas de reexperimentación, evitación, alteraciones cognitivas/afectivas e hiperactivación.",
        symptoms=[
            "REEXPERIMENTACIÓN:",
            "Recuerdos intrusivos recurrentes",
            "Pesadillas del evento",
            "Flashbacks (disociativos)",
            "Malestar intenso ante recordatorios",
            "EVITACIÓN:",
            "Evitación de recuerdos, pensamientos, sentimientos",
            "Evitación de recordatorios externos (lugares, personas)",
            "ALTERACIONES COGNITIVAS/AFECTIVAS:",
            "Amnesia disociativa del trauma",
            "Creencias negativas persistentes sobre sí mismo/mundo",
            "Emociones negativas persistentes (culpa, vergüenza)",
            "Anhedonia, desapego",
            "HIPERACTIVACIÓN:",
            "Hipervigilancia",
            "Respuesta de sobresalto exagerada",
            "Irritabilidad, conducta temeraria",
            "Alteraciones del sueño",
        ],
        risk_factors=[
            "Tipo de trauma (interpersonal peor que accidentes)",
            "Gravedad y duración del trauma",
            "Trauma previo",
            "Historia psiquiátrica previa",
            "Falta de apoyo social post-trauma",
            "Sexo femenino (2:1)",
            "Disociación peritraumática",
        ],
        complications=[
            "Depresión comórbida (50%)",
            "Abuso de sustancias",
            "Suicidio",
            "Dolor crónico, somatización",
            "Deterioro funcional severo",
            "TEPT complejo (trauma repetido)",
        ],
        diagnostic_criteria=[
            "Exposición a trauma (directo, testigo, enterarse de familiar cercano)",
            "≥1 síntoma de reexperimentación",
            "≥1 síntoma de evitación",
            "≥2 alteraciones cognitivas/afectivas",
            "≥2 síntomas de hiperactivación",
            "Duración >1 mes",
            "Malestar o deterioro significativo",
            "PCL-5 para screening y severidad",
        ],
        differential_diagnosis=[
            "Trastorno de estrés agudo (<1 mes)",
            "Trastorno de adaptación",
            "Trastorno de ansiedad",
            "Depresión mayor",
            "Trastorno disociativo",
            "TEC (trauma craneoencefálico)",
        ],
        treatment_protocol=[
            "PSICOTERAPIA enfocada en trauma (1ª línea):",
            "Terapia de procesamiento cognitivo (CPT)",
            "Exposición prolongada (PE)",
            "EMDR (Eye Movement Desensitization and Reprocessing)",
            "FARMACOTERAPIA:",
            "ISRS: Sertralina 50-200 mg, Paroxetina 20-60 mg (aprobados FDA)",
            "IRSN: Venlafaxina",
            "Prazosina 1-15 mg noche para pesadillas",
            "EVITAR benzodiacepinas (pueden empeorar pronóstico)",
        ],
        emergency_signs=[
            "Ideación/conducta suicida",
            "Disociación severa",
            "Abuso de sustancias con intoxicación",
            "Agresividad/violencia",
        ],
        prognosis="50% se recuperan en 3 meses sin tratamiento. 30% curso crónico. Tratamiento mejora significativamente el pronóstico.",
        follow_up=[
            "Seguimiento regular durante psicoterapia",
            "PCL-5 para monitorear respuesta",
            "Evaluación de ideación suicida",
            "Monitoreo de efectos adversos de medicación",
            "Tratamiento de comorbilidades",
        ],
    ),
    # =========================================================================
    # TRASTORNO OBSESIVO-COMPULSIVO (F42)
    # =========================================================================
    "F42": MedicalCondition(
        icd10_code="F42",
        name="Trastorno Obsesivo-Compulsivo (TOC)",
        category="Psiquiatría",
        description="Presencia de obsesiones (pensamientos intrusivos, imágenes, impulsos) y/o compulsiones (conductas repetitivas para reducir ansiedad) que causan malestar significativo.",
        symptoms=[
            "OBSESIONES (pensamientos intrusivos, persistentes):",
            "Contaminación (gérmenes, suciedad)",
            "Duda patológica (¿cerré la puerta?)",
            "Simetría/orden",
            "Pensamientos agresivos, sexuales o religiosos intrusivos",
            "Miedo a causar daño",
            "COMPULSIONES (conductas repetitivas):",
            "Lavado excesivo de manos",
            "Verificación repetida",
            "Ordenar, contar",
            "Rituales mentales (rezar, contar)",
            "Búsqueda de reaseguramiento",
        ],
        risk_factors=[
            "Historia familiar de TOC",
            "Eventos vitales estresantes",
            "Trauma",
            "PANDAS (post-estreptocócico en niños)",
            "Personalidad perfeccionista",
            "Trastornos de tics comórbidos",
        ],
        complications=[
            "Depresión comórbida (60%)",
            "Otros trastornos de ansiedad",
            "Deterioro funcional severo",
            "Aislamiento social",
            "Dermatitis por lavado excesivo",
            "Tricotilomanía, trastorno de excoriación",
        ],
        diagnostic_criteria=[
            "Presencia de obsesiones y/o compulsiones",
            "Consumen tiempo (>1 hora/día) o causan malestar/deterioro",
            "No atribuibles a sustancias",
            "No mejor explicado por otro trastorno",
            "Y-BOCS (Yale-Brown Obsessive Compulsive Scale) para severidad",
        ],
        differential_diagnosis=[
            "TAG (preocupaciones más realistas)",
            "Trastorno de ansiedad por enfermedad",
            "Trastorno dismórfico corporal",
            "Tricotilomanía",
            "Trastorno de acumulación",
            "Espectro esquizofrenia (ideas delirantes vs obsesiones)",
            "Trastorno de tics",
        ],
        treatment_protocol=[
            "PSICOTERAPIA 1ª línea:",
            "Exposición y Prevención de Respuesta (EPR) - eficacia alta",
            "12-20 sesiones típicamente",
            "FARMACOTERAPIA:",
            "ISRS en dosis altas: Fluoxetina 40-80 mg, Fluvoxamina 200-300 mg",
            "Sertralina 100-200 mg, Paroxetina 40-60 mg",
            "Clomipramina 150-250 mg (eficaz pero más efectos adversos)",
            "Respuesta más lenta que en depresión (8-12 semanas)",
            "REFRACTARIO: Potenciación con antipsicóticos (Risperidona, Aripiprazol)",
        ],
        emergency_signs=[
            "Ideación suicida",
            "Obsesiones agresivas con riesgo de acción",
            "Deterioro funcional completo",
            "Autolesiones por compulsiones",
        ],
        prognosis="Crónico sin tratamiento. Con EPR + ISRS: 60-70% mejoran significativamente. Remisión completa en 20-30%.",
        follow_up=[
            "Seguimiento durante EPR",
            "Y-BOCS periódico para evaluar respuesta",
            "Monitoreo de efectos adversos de ISRS",
            "Tratamiento largo plazo frecuentemente necesario",
        ],
    ),
    # =========================================================================
    # TDAH (F90)
    # =========================================================================
    "F90": MedicalCondition(
        icd10_code="F90",
        name="Trastorno por Déficit de Atención e Hiperactividad (TDAH)",
        category="Psiquiatría",
        description="Trastorno del neurodesarrollo caracterizado por patrón persistente de inatención y/o hiperactividad-impulsividad que interfiere con el funcionamiento.",
        symptoms=[
            "INATENCIÓN:",
            "Dificultad para mantener atención",
            "No parece escuchar cuando se le habla",
            "No sigue instrucciones, no termina tareas",
            "Dificultad para organizar tareas",
            "Evita tareas que requieren esfuerzo mental sostenido",
            "Pierde objetos frecuentemente",
            "Se distrae fácilmente",
            "Olvidadizo en actividades diarias",
            "HIPERACTIVIDAD-IMPULSIVIDAD:",
            "Se mueve en exceso, no puede quedarse quieto",
            "Corre o trepa en situaciones inapropiadas",
            "Habla en exceso",
            "Responde antes de que terminen la pregunta",
            "Dificultad para esperar turno",
            "Interrumpe o se entromete",
        ],
        risk_factors=[
            "Historia familiar de TDAH (heredabilidad 70-80%)",
            "Prematuridad, bajo peso al nacer",
            "Exposición prenatal a tabaco, alcohol",
            "Trauma craneoencefálico",
            "Exposición a plomo",
        ],
        complications=[
            "Fracaso escolar/académico",
            "Dificultades laborales",
            "Problemas en relaciones",
            "Accidentes (conducción riesgosa)",
            "Trastorno de conducta, trastorno oposicionista",
            "Abuso de sustancias",
            "Depresión, ansiedad comórbidos",
        ],
        diagnostic_criteria=[
            "≥6 síntomas de inatención y/o hiperactividad-impulsividad (niños)",
            "≥5 síntomas en adultos (>17 años)",
            "Presentes antes de los 12 años",
            "En ≥2 entornos (casa, escuela, trabajo)",
            "Deterioro significativo del funcionamiento",
            "Presentaciones: predominio inatento, hiperactivo-impulsivo, combinado",
            "Escalas: ASRS (adultos), Vanderbilt, Conners (niños)",
        ],
        differential_diagnosis=[
            "Variantes normales del desarrollo",
            "Trastorno de ansiedad",
            "Trastorno del humor",
            "Trastornos del aprendizaje",
            "Trastorno del espectro autista",
            "Abuso de sustancias",
            "Trastornos del sueño",
            "Discapacidad intelectual",
        ],
        treatment_protocol=[
            "MULTIMODAL: Farmacoterapia + intervenciones conductuales/ambientales",
            "ESTIMULANTES (1ª línea, eficacia 70-80%):",
            "Metilfenidato 0.5-1 mg/kg/día (liberación inmediata o prolongada)",
            "Lisdexanfetamina 30-70 mg/día",
            "NO ESTIMULANTES:",
            "Atomoxetina 1.2 mg/kg/día (efecto en semanas)",
            "Viloxazina, Guanfacina, Clonidina (liberación prolongada)",
            "INTERVENCIONES CONDUCTUALES:",
            "Entrenamiento a padres",
            "Terapia conductual",
            "Adaptaciones escolares/laborales",
            "Coaching para adultos",
        ],
        emergency_signs=[
            "Abuso de estimulantes",
            "Ideación suicida (especialmente con comorbilidades)",
            "Conducta temeraria grave",
            "Efectos cardiovasculares adversos",
        ],
        prognosis="Crónico: 50-60% persiste en adultos (muchos como inatención). Con tratamiento, mejora significativa del funcionamiento.",
        follow_up=[
            "Seguimiento cada 1-3 meses",
            "Monitoreo de crecimiento en niños",
            "PA y FC con estimulantes",
            "Evaluar respuesta con escalas",
            "Ajuste de dosis según respuesta",
            "Vacaciones de medicación (debatido)",
        ],
    ),
    # =========================================================================
    # TRASTORNO LÍMITE DE LA PERSONALIDAD (F60.3)
    # =========================================================================
    "F60.3": MedicalCondition(
        icd10_code="F60.3",
        name="Trastorno Límite de la Personalidad",
        category="Psiquiatría",
        description="Patrón persistente de inestabilidad en relaciones interpersonales, autoimagen y afectos, con marcada impulsividad. Alta carga de sufrimiento y uso de servicios.",
        symptoms=[
            "Esfuerzos frenéticos para evitar abandono real o imaginado",
            "Relaciones intensas e inestables (idealización/devaluación)",
            "Alteración de la identidad (autoimagen inestable)",
            "Impulsividad en ≥2 áreas potencialmente dañinas (gastos, sexo, sustancias, conducción)",
            "Conductas suicidas recurrentes, autolesiones",
            "Inestabilidad afectiva (disforia episódica, irritabilidad)",
            "Sentimientos crónicos de vacío",
            "Ira inapropiada, dificultad para controlarla",
            "Ideación paranoide o síntomas disociativos transitorios",
        ],
        risk_factors=[
            "Trauma infantil (abuso físico, sexual, emocional, negligencia)",
            "Apego inseguro",
            "Historia familiar de trastornos de personalidad",
            "Temperamento impulsivo",
            "Invalidación emocional en infancia",
        ],
        complications=[
            "Intentos de suicidio (70% intentan, 8-10% mueren)",
            "Autolesiones no suicidas",
            "Trastorno por uso de sustancias",
            "Trastornos alimentarios",
            "Depresión comórbida",
            "Hospitalizaciones frecuentes",
            "Dificultades laborales y relacionales severas",
        ],
        diagnostic_criteria=[
            "≥5 de 9 criterios DSM-5, patrón persistente desde adulto joven",
            "Presente en diversos contextos",
            "No mejor explicado por otro trastorno mental",
            "No debido a efectos de sustancias o condición médica",
            "Escalas: ZAN-BPD, BSL-23",
        ],
        differential_diagnosis=[
            "Trastorno bipolar (episodios más largos, menos reactivos)",
            "Depresión mayor",
            "TEPT complejo",
            "Otros trastornos de personalidad",
            "Trastorno disociativo",
        ],
        treatment_protocol=[
            "PSICOTERAPIA (1ª línea, ÚNICA con evidencia robusta):",
            "DBT (Terapia Dialéctico Conductual): más evidencia, reduce autolesiones y suicidio",
            "MBT (Terapia basada en Mentalización)",
            "TFP (Psicoterapia Focalizada en Transferencia)",
            "FARMACOTERAPIA: solo síntomas específicos, NO personalidad:",
            "ISRS: disforia, irritabilidad",
            "Estabilizadores (valproato, lamotrigina): impulsividad",
            "Antipsicóticos atípicos en dosis bajas: síntomas disociativos, paranoides",
            "EVITAR benzodiacepinas (riesgo de abuso y desinhibición)",
        ],
        emergency_signs=[
            "Ideación suicida activa con plan",
            "Intento de suicidio reciente",
            "Autolesiones severas",
            "Psicosis transitoria",
            "Agresividad hacia otros",
        ],
        prognosis="Mejora con la edad: 85% ya no cumplen criterios a los 10 años de seguimiento. DBT acelera recuperación.",
        follow_up=[
            "Psicoterapia estructurada regular (semanal)",
            "Plan de crisis establecido",
            "Coordinación entre profesionales",
            "Evaluación de ideación suicida",
            "Tratamiento de comorbilidades",
        ],
    ),
}

# Estadísticas del módulo
PSYCHIATRIC_STATS = {"total": len(PSYCHIATRIC_CONDITIONS), "category": "Psiquiatría"}

if __name__ == "__main__":
    print(f"Condiciones Psiquiátricas: {PSYCHIATRIC_STATS['total']} cargadas")
    for code, cond in PSYCHIATRIC_CONDITIONS.items():
        print(f"  {code}: {cond.name}")
