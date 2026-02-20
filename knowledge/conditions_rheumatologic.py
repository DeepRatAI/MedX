#!/usr/bin/env python3
"""
🦴 Condiciones Reumatológicas y Musculoesqueléticas
Basado en: ICD-10-CM 2026, ACR/EULAR Guidelines

Cobertura:
- Artritis Reumatoide (M05-M06)
- Lupus Eritematoso Sistémico (M32)
- Osteoartritis (M15-M19)
- Gota (M10)
- Fibromialgia (M79.7)
- Espondilitis Anquilosante (M45)
- Polimialgia Reumática (M35.3)
- Síndrome de Sjögren (M35.0)
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


RHEUMATOLOGIC_CONDITIONS = {
    # =========================================================================
    # ARTRITIS REUMATOIDE (M06.9)
    # =========================================================================
    "M06.9": MedicalCondition(
        icd10_code="M06.9",
        name="Artritis Reumatoide",
        category="Reumatología",
        description="Enfermedad autoinmune sistémica caracterizada por sinovitis crónica erosiva, principalmente de articulaciones pequeñas de manos y pies. Puede afectar múltiples órganos.",
        symptoms=[
            "Poliartritis simétrica (MCF, IFP, muñecas)",
            "Rigidez matutina >1 hora",
            "Hinchazón y dolor articular",
            "Tenosinovitis",
            "Nódulos reumatoideos (codos)",
            "Fatiga, malestar general",
            "Fiebre baja",
            "Manifestaciones extraarticulares: pulmón, ojo, pericardio",
        ],
        risk_factors=[
            "Sexo femenino (3:1)",
            "Edad 30-60 años",
            "Historia familiar",
            "Tabaquismo (factor principal modificable)",
            "HLA-DR4",
            "Obesidad",
        ],
        complications=[
            "Destrucción articular, deformidades (boutonnière, cuello de cisne)",
            "Osteoporosis secundaria",
            "Enfermedad pulmonar intersticial",
            "Enfermedad cardiovascular prematura",
            "Síndrome de Felty (esplenomegalia, neutropenia)",
            "Amiloidosis secundaria",
        ],
        diagnostic_criteria=[
            "Criterios ACR/EULAR 2010 (≥6 puntos):",
            "Artritis de ≥1 articulación",
            "Número y tipo de articulaciones afectadas (0-5 puntos)",
            "FR y/o anti-CCP positivos (0-3 puntos)",
            "Reactantes de fase aguda (VSG, PCR) elevados (0-1 punto)",
            "Duración ≥6 semanas (1 punto)",
        ],
        differential_diagnosis=[
            "Osteoartritis",
            "Lupus eritematoso sistémico",
            "Artritis psoriásica",
            "Gota poliarticular",
            "Artritis viral",
            "Polimialgia reumática",
        ],
        treatment_protocol=[
            "INICIO TEMPRANO (<3 meses del diagnóstico)",
            "DMARDs convencionales 1ª línea: Metotrexato 15-25 mg/semana",
            "Ácido fólico 5 mg/semana (no el día de MTX)",
            "Alternativas: Leflunomida, Sulfasalazina, Hidroxicloroquina",
            "DMARDs biológicos si falla MTX: Anti-TNF (Adalimumab, Etanercept)",
            "Otros biológicos: Tocilizumab (anti-IL6), Rituximab (anti-CD20)",
            "Inhibidores JAK: Tofacitinib, Upadacitinib",
            "Corticoides en dosis bajas como puente (<7.5 mg prednisona)",
        ],
        emergency_signs=[
            "Subluxación atlantoaxoidea (dolor cervical, mielopatía)",
            "Escleritis/uveítis",
            "Derrame pericárdico sintomático",
            "Vasculitis reumatoidea",
        ],
        prognosis="Sin tratamiento: destrucción articular progresiva. Con DMARDs tempranos: remisión posible en 30-50%. Objetivo: DAS28 <2.6.",
        follow_up=[
            "DAS28 cada 3-6 meses",
            "Hemograma, función hepática, renal con MTX cada 3 meses",
            "Radiografías manos/pies basales y anuales",
            "Screening TB antes de biológicos",
            "Densitometría ósea",
        ],
    ),
    # =========================================================================
    # LUPUS ERITEMATOSO SISTÉMICO (M32)
    # =========================================================================
    "M32": MedicalCondition(
        icd10_code="M32",
        name="Lupus Eritematoso Sistémico (LES)",
        category="Reumatología",
        description="Enfermedad autoinmune multisistémica con autoanticuerpos contra componentes nucleares. Afecta piel, articulaciones, riñón, sistema nervioso, series hematológicas.",
        symptoms=[
            "Eritema malar (mariposa)",
            "Fotosensibilidad",
            "Úlceras orales/nasales",
            "Artritis no erosiva",
            "Serositis (pleuritis, pericarditis)",
            "Afección renal (proteinuria, hematuria)",
            "Síntomas neuropsiquiátricos",
            "Citopenias (anemia, leucopenia, trombocitopenia)",
            "Fatiga severa",
            "Fenómeno de Raynaud",
            "Alopecia",
        ],
        risk_factors=[
            "Sexo femenino (9:1)",
            "Edad fértil (15-45 años)",
            "Afrodescendientes, asiáticos, hispanos",
            "Historia familiar de LES",
            "Deficiencias de complemento (C2, C4)",
            "Fármacos inductores (hidralazina, procainamida, isoniazida)",
        ],
        complications=[
            "Nefritis lúpica → ERC",
            "Lupus neuropsiquiátrico (psicosis, convulsiones)",
            "Síndrome antifosfolípido (trombosis)",
            "Enfermedad cardiovascular prematura",
            "Embarazo de alto riesgo",
            "Infecciones (inmunosupresión)",
        ],
        diagnostic_criteria=[
            "Criterios EULAR/ACR 2019:",
            "ANA ≥1:80 como criterio de entrada",
            "Puntaje ≥10 con criterios de 7 dominios clínicos + 3 inmunológicos",
            "Clínicos: constitucionales, piel, articulaciones, serosas, renal, neurológico, hematológico",
            "Inmunológicos: Anti-dsDNA, Anti-Smith, Antifosfolípidos, complemento bajo",
        ],
        differential_diagnosis=[
            "Artritis reumatoide",
            "Enfermedad mixta del tejido conectivo",
            "Dermatomiositis",
            "Vasculitis",
            "Fibromialgia",
            "Infección viral crónica",
        ],
        treatment_protocol=[
            "TODOS: Hidroxicloroquina 200-400 mg/día (reduce brotes, mortalidad)",
            "Protección solar estricta",
            "LEVE: AINEs, hidroxicloroquina, corticoides tópicos",
            "MODERADO: Corticoides orales, Metotrexato, Azatioprina",
            "SEVERO (renal, neurológico): Micofenolato, Ciclofosfamida",
            "Belimumab (anti-BLyS): aprobado para LES activo",
            "Voclosporina, Anifrolumab para nefritis lúpica",
        ],
        emergency_signs=[
            "Brote severo con afección multiorgánica",
            "Nefritis lúpica rápidamente progresiva",
            "Lupus neuropsiquiátrico (convulsiones, psicosis)",
            "Hemorragia alveolar",
            "Trombosis (síndrome antifosfolípido catastrófico)",
        ],
        prognosis="Supervivencia a 10 años >90% en países desarrollados. Nefritis lúpica clase IV sigue siendo la complicación más grave.",
        follow_up=[
            "SLEDAI o BILAG para actividad cada visita",
            "Creatinina, uroanálisis cada visita",
            "Complemento (C3, C4) y anti-dsDNA cada 3-6 meses",
            "Biopsia renal si proteinuria significativa",
            "Perfil lipídico y PA (riesgo CV)",
            "Fondo de ojo anual con hidroxicloroquina",
        ],
    ),
    # =========================================================================
    # OSTEOARTRITIS (M17.9 - RODILLA)
    # =========================================================================
    "M17.9": MedicalCondition(
        icd10_code="M17.9",
        name="Osteoartritis de Rodilla",
        category="Reumatología",
        description="Enfermedad articular degenerativa caracterizada por pérdida progresiva de cartílago articular, remodelación ósea subcondral y sinovitis secundaria. Causa más común de discapacidad en adultos mayores.",
        symptoms=[
            "Dolor articular con actividad, mejora con reposo",
            "Rigidez matutina <30 minutos",
            "Crepitación con movimiento",
            "Limitación del rango de movimiento",
            "Inestabilidad articular",
            "Derrame articular ocasional",
            "Deformidades (genu varo/valgo)",
            "Atrofia muscular periarticular",
        ],
        risk_factors=[
            "Edad >50 años (principal factor)",
            "Sexo femenino (postmenopausia)",
            "Obesidad",
            "Trauma articular previo",
            "Ocupación con sobrecarga articular",
            "Historia familiar",
            "Malalneamiento (varo/valgo)",
        ],
        complications=[
            "Discapacidad funcional progresiva",
            "Deformidad articular",
            "Inmovilidad → sarcopenia",
            "Dolor crónico refractario",
            "Necesidad de reemplazo articular",
        ],
        diagnostic_criteria=[
            "CLÍNICO (ACR):",
            "Dolor de rodilla + ≥3 de: edad >50 años, rigidez <30 min, crepitación",
            "RADIOLÓGICO: estrechamiento del espacio articular, osteofitos",
            "Clasificación Kellgren-Lawrence (0-4)",
            "RM si sospecha de lesión meniscal u otras causas",
        ],
        differential_diagnosis=[
            "Artritis reumatoide",
            "Gota",
            "Artritis séptica",
            "Bursitis anserina",
            "Lesión meniscal",
            "Condromalacia rotuliana",
        ],
        treatment_protocol=[
            "NO FARMACOLÓGICO (1ª línea):",
            "Pérdida de peso si IMC >25",
            "Ejercicio: fortalecimiento cuádriceps, aeróbico de bajo impacto",
            "Fisioterapia",
            "Bastón o rodillera",
            "FARMACOLÓGICO:",
            "Paracetamol hasta 3 g/día",
            "AINEs tópicos (diclofenaco gel)",
            "AINEs orales ciclos cortos (con gastroprotección)",
            "Duloxetina para dolor crónico",
            "Infiltraciones: corticoides (alivio temporal), ácido hialurónico",
            "CIRUGÍA: artroplastia total de rodilla si refractario",
        ],
        emergency_signs=[
            "Artritis séptica (fiebre, articulación caliente, dolor severo)",
            "Hemartros post-traumático",
        ],
        prognosis="Curso lentamente progresivo. Artroplastia: excelentes resultados en 90%, duración prótesis 15-20 años.",
        follow_up=[
            "Evaluación funcional (WOMAC) periódica",
            "Control de peso",
            "Radiografías si cambio de síntomas",
            "Referencia a cirugía si no responde a tratamiento conservador",
        ],
    ),
    # =========================================================================
    # GOTA (M10)
    # =========================================================================
    "M10": MedicalCondition(
        icd10_code="M10",
        name="Gota",
        category="Reumatología",
        description="Artritis inflamatoria por depósito de cristales de urato monosódico en articulaciones y tejidos blandos. Asociada a hiperuricemia. Afecta clásicamente 1ª MTF (podagra).",
        symptoms=[
            "Artritis monoarticular aguda (1ª MTF clásica)",
            "Dolor intenso, inicio súbito (frecuente nocturno)",
            "Hinchazón, eritema, calor",
            "Descamación cutánea post-brote",
            "Resolución espontánea en 7-14 días",
            "Tofos (gota crónica tofácea)",
            "Poliartritis en gota avanzada",
        ],
        risk_factors=[
            "Hiperuricemia (>6.8 mg/dL)",
            "Sexo masculino",
            "Dieta rica en purinas (carne roja, mariscos)",
            "Alcohol (cerveza, licores)",
            "Obesidad, síndrome metabólico",
            "Diuréticos (tiazidas, furosemida)",
            "ERC",
            "Trasplante de órganos (ciclosporina)",
        ],
        complications=[
            "Gota tofácea crónica",
            "Artropatía destructiva",
            "Nefrolitiasis por ácido úrico",
            "Nefropatía por urato",
            "Enfermedad cardiovascular asociada",
        ],
        diagnostic_criteria=[
            "GOLD STANDARD: Cristales de UMS en líquido sinovial/tofo",
            "Cristales en forma de aguja, birrefringencia negativa",
            "CLASIFICACIÓN ACR/EULAR 2015: ≥8 puntos",
            "Clínico + laboratorio + imágenes",
            "Ácido úrico sérico: elevado (puede ser normal durante brote)",
        ],
        differential_diagnosis=[
            "Artritis séptica (SIEMPRE descartar)",
            "Pseudogota (cristales de pirofosfato cálcico)",
            "Artritis reactiva",
            "Celulitis",
            "Artritis reumatoide",
        ],
        treatment_protocol=[
            "BROTE AGUDO (primeras 24 horas):",
            "AINEs dosis altas: Indometacina 50 mg c/8h, Naproxeno 500 mg c/12h",
            "Colchicina: 1.2 mg inicial, luego 0.6 mg en 1 hora (máx 1.8 mg/día)",
            "Corticoides: Prednisona 30-40 mg/día x 5 días (si AINEs contraindicados)",
            "Infiltración intraarticular",
            "REDUCCIÓN URICEMIA (NO iniciar durante brote):",
            "Indicado si ≥2 brotes/año, tofos, nefrolitiasis, ERC",
            "Alopurinol 100-800 mg/día (iniciar dosis bajas)",
            "Objetivo: ácido úrico <6 mg/dL (<5 mg/dL si tofos)",
            "Febuxostat alternativa si intolerancia a alopurinol",
            "Profilaxis con colchicina 0.6 mg/día al iniciar hipouricemiante x 6 meses",
        ],
        emergency_signs=[
            "Artritis séptica (no se puede descartar sin artrocentesis)",
            "Fiebre alta con artritis (descartar infección)",
            "Gota poliarticular severa",
        ],
        prognosis="Excelente con control de uricemia. Sin tratamiento: brotes más frecuentes y tofos. Tofos pueden resolverse con uricemia <6 mg/dL.",
        follow_up=[
            "Ácido úrico cada 2-4 semanas al titular hipouricemiante",
            "Cada 6-12 meses una vez estable",
            "Función renal anual",
            "Educación sobre dieta y alcohol",
        ],
    ),
    # =========================================================================
    # FIBROMIALGIA (M79.7)
    # =========================================================================
    "M79.7": MedicalCondition(
        icd10_code="M79.7",
        name="Fibromialgia",
        category="Reumatología",
        description="Síndrome de dolor crónico generalizado con hiperalgesia y alodinia, acompañado de fatiga, trastornos del sueño y síntomas cognitivos. No hay daño tisular identificable.",
        symptoms=[
            "Dolor difuso generalizado >3 meses",
            "Fatiga persistente",
            "Sueño no reparador",
            "Disfunción cognitiva (fibro-niebla)",
            "Rigidez matutina",
            "Cefaleas tensionales o migraña",
            "Síndrome de intestino irritable",
            "Síntomas depresivos y ansiosos",
            "Parestesias",
            "Sensibilidad a ruidos, luces, temperatura",
        ],
        risk_factors=[
            "Sexo femenino (7:1)",
            "Edad 30-50 años",
            "Historia familiar de fibromialgia",
            "Trauma físico o emocional",
            "Trastornos del sueño",
            "Otras enfermedades reumáticas",
            "Infecciones previas",
        ],
        complications=[
            "Discapacidad laboral",
            "Depresión severa",
            "Aislamiento social",
            "Polifarmacia",
            "Uso excesivo de servicios de salud",
        ],
        diagnostic_criteria=[
            "Criterios ACR 2010/2016:",
            "Dolor generalizado (≥4/5 regiones)",
            "Síntomas presentes ≥3 meses",
            "WPI (Índice de Dolor Generalizado) ≥7 + SS (Severidad de Síntomas) ≥5",
            "O: WPI 4-6 + SS ≥9",
            "No explicado por otro diagnóstico",
            "Laboratorio y estudios de imagen normales",
        ],
        differential_diagnosis=[
            "Hipotiroidismo",
            "Polimialgia reumática",
            "Artritis reumatoide inicial",
            "Lupus eritematoso sistémico",
            "Espondiloartritis",
            "Miopatías",
            "Depresión mayor con síntomas somáticos",
        ],
        treatment_protocol=[
            "MULTIMODAL - no hay monoterapia eficaz:",
            "EDUCACIÓN: explicar el diagnóstico, validar síntomas",
            "EJERCICIO aeróbico gradual (evidencia más fuerte)",
            "TCC (Terapia Cognitivo-Conductual)",
            "FARMACOLÓGICO:",
            "Duloxetina 30-60 mg/día (aprobado FDA)",
            "Pregabalina 150-450 mg/día (aprobado FDA)",
            "Milnacipran 50-200 mg/día",
            "Amitriptilina 10-50 mg noche (evidencia histórica)",
            "Ciclobenzaprina 10-40 mg noche",
            "EVITAR: opioides (ineficaces, riesgo de abuso), AINEs crónicos",
        ],
        emergency_signs=[
            "Ideación suicida",
            "Síntomas que sugieren otra patología grave",
            "Deterioro funcional completo",
        ],
        prognosis="Crónico. Con tratamiento multimodal: 25-50% mejoran significativamente. Remisión completa rara.",
        follow_up=[
            "Seguimiento regular (cada 2-3 meses inicial)",
            "FIQ (Fibromyalgia Impact Questionnaire)",
            "Monitoreo de efectos adversos medicación",
            "Evaluar adherencia a ejercicio",
            "Screening de depresión/ansiedad",
        ],
    ),
    # =========================================================================
    # ESPONDILITIS ANQUILOSANTE (M45)
    # =========================================================================
    "M45": MedicalCondition(
        icd10_code="M45",
        name="Espondilitis Anquilosante",
        category="Reumatología",
        description="Espondiloartropatía inflamatoria crónica que afecta principalmente el esqueleto axial (sacroilíacas, columna). Asociada a HLA-B27. Evoluciona a anquilosis.",
        symptoms=[
            "Dolor lumbar inflamatorio (rigidez matutina >30 min, mejora con ejercicio)",
            "Dolor nalgas alternante (sacroileítis)",
            "Rigidez axial progresiva",
            "Disminución de expansión torácica",
            "Artritis periférica (caderas, rodillas)",
            "Entesitis (talón, rodilla)",
            "Uveítis anterior aguda (25%)",
            "Fatiga",
        ],
        risk_factors=[
            "HLA-B27 positivo (90%)",
            "Sexo masculino (3:1)",
            "Edad de inicio <45 años",
            "Historia familiar de espondiloartritis",
        ],
        complications=[
            "Anquilosis vertebral (columna en bambú)",
            "Cifosis",
            "Fractura vertebral (hueso frágil anquilosado)",
            "Insuficiencia aórtica",
            "Fibrosis pulmonar apical",
            "Amiloidosis secundaria",
            "Síndrome de cola de caballo",
        ],
        diagnostic_criteria=[
            "Criterios ASAS para espondiloartritis axial:",
            "Dolor lumbar ≥3 meses, inicio <45 años",
            "Sacroileítis en imagen (RM o Rx) + ≥1 característica de SpA",
            "O: HLA-B27 + ≥2 características de SpA",
            "Características: artritis, entesitis, uveítis, dactilitis, psoriasis, EII, respuesta a AINEs, historia familiar, HLA-B27, PCR elevada",
        ],
        differential_diagnosis=[
            "Dolor lumbar mecánico",
            "Hernia discal",
            "Artritis reactiva",
            "Artritis psoriásica",
            "Enfermedad inflamatoria intestinal con espondilitis",
            "Hiperostosis esquelética difusa idiopática (DISH)",
        ],
        treatment_protocol=[
            "AINEs (1ª línea, uso continuo si es efectivo):",
            "Indometacina, Naproxeno, Etoricoxib",
            "EJERCICIO diario (fundamental): movilidad axial, natación",
            "FISIOTERAPIA",
            "DMARDs convencionales: NO eficaces para enfermedad axial",
            "Sulfasalazina solo si artritis periférica",
            "BIOLÓGICOS (falla a ≥2 AINEs):",
            "Anti-TNF: Adalimumab, Etanercept, Infliximab, Golimumab, Certolizumab",
            "Anti-IL17: Secukinumab, Ixekizumab",
            "Inhibidor JAK: Upadacitinib",
        ],
        emergency_signs=[
            "Fractura vertebral (trauma menor, dolor agudo)",
            "Síndrome de cola de caballo",
            "Uveítis anterior (ojo rojo, dolor, fotofobia)",
        ],
        prognosis="Variable. Muchos mantienen buena función con tratamiento. Anquilosis completa ocurre en minoría. Biológicos han cambiado pronóstico.",
        follow_up=[
            "BASDAI, ASDAS cada visita",
            "Radiografía columna cada 2 años (monitorear progresión)",
            "RM sacroilíacas si cambio clínico",
            "Evaluación oftalmológica si síntomas oculares",
            "Screening de osteoporosis",
        ],
    ),
    # =========================================================================
    # POLIMIALGIA REUMÁTICA (M35.3)
    # =========================================================================
    "M35.3": MedicalCondition(
        icd10_code="M35.3",
        name="Polimialgia Reumática",
        category="Reumatología",
        description="Síndrome inflamatorio del adulto mayor caracterizado por dolor y rigidez de cinturas (hombros, caderas). Frecuentemente asociada a arteritis de células gigantes.",
        symptoms=[
            "Dolor y rigidez bilateral de hombros (siempre)",
            "Dolor y rigidez de cintura pélvica/caderas",
            "Rigidez matutina >45-60 minutos",
            "Síntomas constitucionales: fatiga, malestar, pérdida de peso",
            "Febrícula",
            "Depresión",
            "Dificultad para levantar brazos, levantarse de silla",
            "NO hay debilidad muscular real",
        ],
        risk_factors=[
            "Edad >50 años (media 70 años)",
            "Sexo femenino (2:1)",
            "Raza caucásica (más común Europa norte)",
            "Historia familiar",
        ],
        complications=[
            "Arteritis de células gigantes (15-20%): EMERGENCIA",
            "Aortitis",
            "Aneurisma de aorta torácica",
            "Efectos adversos de corticoides prolongados",
        ],
        diagnostic_criteria=[
            "Criterios ACR/EULAR 2012 (sin ecografía ≥4 puntos, con ecografía ≥5):",
            "Rigidez matutina >45 min (2 puntos)",
            "Dolor/limitación cadera (1 punto)",
            "VSG >40 mm/h (1 punto)",
            "Ausencia FR y anti-CCP (2 puntos)",
            "Ecografía: bursitis (1-2 puntos)",
            "Respuesta dramática a corticoides apoya diagnóstico",
        ],
        differential_diagnosis=[
            "Artritis reumatoide de inicio tardío",
            "Polimiositis",
            "Fibromialgia",
            "Hipotiroidismo",
            "Neoplasia oculta",
            "Infección crónica",
            "Espondiloartritis de inicio tardío",
        ],
        treatment_protocol=[
            "CORTICOIDES (respuesta rápida y dramática):",
            "Prednisona 12.5-25 mg/día (dosis inicial)",
            "Respuesta en 24-72 horas (si no responde, reconsiderar diagnóstico)",
            "Reducción gradual: disminuir 2.5 mg cada 2-4 semanas hasta 10 mg",
            "Luego reducción lenta 1 mg cada mes",
            "Duración total: 1-2 años (algunos más)",
            "Metotrexato si recaídas frecuentes o dificultad para reducir corticoides",
            "Prevenir osteoporosis: calcio, vitamina D, bifosfonatos",
        ],
        emergency_signs=[
            "Síntomas de arteritis de células gigantes:",
            "Cefalea de inicio reciente",
            "Claudicación mandibular",
            "Alteraciones visuales (EMERGENCIA: riesgo de ceguera)",
            "Dolor arterias temporales, pulso disminuido",
        ],
        prognosis="Excelente con tratamiento. Mayoría logra remisión, aunque pueden requerir corticoides prolongados. Vigilar efectos adversos de esteroides.",
        follow_up=[
            "Clínico cada 2-4 semanas al inicio, luego cada 2-3 meses",
            "VSG/PCR para monitorear actividad",
            "Glucemia (riesgo diabetes por corticoides)",
            "Densitometría ósea",
            "Evaluar síntomas de arteritis en cada visita",
        ],
    ),
    # =========================================================================
    # SÍNDROME DE SJÖGREN (M35.0)
    # =========================================================================
    "M35.0": MedicalCondition(
        icd10_code="M35.0",
        name="Síndrome de Sjögren",
        category="Reumatología",
        description="Enfermedad autoinmune caracterizada por infiltración linfocitaria de glándulas exocrinas, principalmente salivales y lagrimales, causando sequedad. Puede ser primario o secundario.",
        symptoms=[
            "Xeroftalmía (ojo seco): sensación arenilla, ardor, fotofobia",
            "Xerostomía (boca seca): dificultad tragar, caries dental",
            "Aumento parótidas (30%)",
            "Fatiga severa",
            "Artralgias/artritis",
            "Fenómeno de Raynaud (30%)",
            "Sequedad vaginal",
            "Neuropatía periférica",
            "Manifestaciones sistémicas en 30-40%",
        ],
        risk_factors=[
            "Sexo femenino (9:1)",
            "Edad 40-60 años",
            "Otras enfermedades autoinmunes (AR, LES) → Sjögren secundario",
            "Historia familiar de autoinmunidad",
        ],
        complications=[
            "Linfoma (riesgo 5-10%, tipo MALT principalmente)",
            "Enfermedad pulmonar intersticial",
            "Nefritis intersticial, ATR tipo I",
            "Neuropatía periférica",
            "Vasculitis crioglobulinémica",
            "Caries dental severa",
        ],
        diagnostic_criteria=[
            "Criterios ACR/EULAR 2016 (≥4 puntos):",
            "Biopsia glándula salival: sialoadenitis linfocítica (3 puntos)",
            "Anti-SSA/Ro positivo (3 puntos)",
            "Puntuación tinción ocular ≥5 (1 punto)",
            "Test Schirmer ≤5 mm/5 min (1 punto)",
            "Flujo salival no estimulado ≤0.1 mL/min (1 punto)",
        ],
        differential_diagnosis=[
            "Síndrome sicca por fármacos (anticolinérgicos)",
            "Radioterapia cabeza/cuello",
            "Hepatitis C",
            "VIH",
            "Sarcoidosis",
            "Amiloidosis",
            "Enfermedad relacionada con IgG4",
        ],
        treatment_protocol=[
            "SEQUEDAD OCULAR:",
            "Lágrimas artificiales frecuentes",
            "Ciclosporina tópica 0.05% (Restasis)",
            "Lifitegrast (Xiidra)",
            "Oclusión puntos lagrimales",
            "SEQUEDAD ORAL:",
            "Sorbos frecuentes de agua",
            "Sustitutos de saliva",
            "Pilocarpina 5 mg c/6-8h (sialogogo)",
            "Cevimelina 30 mg c/8h",
            "Cuidado dental intensivo",
            "MANIFESTACIONES SISTÉMICAS:",
            "Hidroxicloroquina para fatiga y artralgias",
            "Metotrexato, Azatioprina para artritis",
            "Rituximab para manifestaciones severas (vasculitis, pulmonar)",
        ],
        emergency_signs=[
            "Parotidomegalia rápida o persistente (riesgo linfoma)",
            "Adenopatías, esplenomegalia",
            "Púrpura palpable (vasculitis)",
        ],
        prognosis="Crónico. Supervivencia similar a población general en Sjögren primario no complicado. Vigilancia por linfoma.",
        follow_up=[
            "Evaluación de sequedad y síntomas cada 3-6 meses",
            "Hemograma, creatinina, sedimento urinario periódico",
            "Gammaglobulinas (hipergammaglobulinemia)",
            "Examen dental cada 6 meses",
            "Biopsia si sospecha de linfoma (parotidomegalia persistente)",
        ],
    ),
}

# Estadísticas del módulo
RHEUMATOLOGIC_STATS = {
    "total": len(RHEUMATOLOGIC_CONDITIONS),
    "category": "Reumatología y Musculoesquelético",
}

if __name__ == "__main__":
    print(f"Condiciones Reumatológicas: {RHEUMATOLOGIC_STATS['total']} cargadas")
    for code, cond in RHEUMATOLOGIC_CONDITIONS.items():
        print(f"  {code}: {cond.name}")
