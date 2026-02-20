#!/usr/bin/env python3
"""
Modulo de Diagnostico Diferencial - MedeX
==========================================

Permite ingresar sintomas del paciente y genera:
1. Lista de diagnósticos diferenciales ordenados por probabilidad
2. Estudios de laboratorio/imagen necesarios para cada diagnóstico
3. Criterios clave para confirmar o descartar cada entidad

Basado en: UpToDate, Harrison's Principles, ACP Clinical Decision Support
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum


class Urgency(Enum):
    """Nivel de urgencia del diagnóstico."""

    EMERGENT = "Emergente"  # Requiere atención inmediata (minutos)
    URGENT = "Urgente"  # Requiere atención en horas
    SEMI_URGENT = "Semi-urgente"  # Puede esperar 24-48h
    ELECTIVE = "Electivo"  # Puede manejarse ambulatorio


@dataclass
class DiagnosticTest:
    """Estudio diagnóstico recomendado."""

    name: str
    category: str  # Laboratorio, Imagen, Procedimiento, Funcional
    purpose: str  # Qué busca confirmar/descartar
    expected_findings: str  # Hallazgo esperado si diagnóstico correcto
    priority: int = 1  # 1 = inicial, 2 = si inicial negativo, 3 = especializado


@dataclass
class DifferentialDiagnosis:
    """Un diagnóstico diferencial con su evaluación."""

    icd10_code: str
    name: str
    probability: str  # Alta, Moderada, Baja
    key_features: List[str]  # Características que lo apoyan
    against_features: List[str]  # Características que lo hacen menos probable
    tests: List[DiagnosticTest]  # Estudios para confirmar/descartar
    urgency: Urgency
    red_flags: List[str]  # Signos de alarma específicos


# ==============================================================================
# BASE DE SÍNTOMAS → DIAGNÓSTICOS DIFERENCIALES
# ==============================================================================

SYMPTOM_DIFFERENTIALS: Dict[str, Dict] = {
    # =========================================================================
    # DOLOR TORÁCICO
    # =========================================================================
    "dolor torácico": {
        "category": "Cardiovascular/Respiratorio/GI",
        "key_questions": [
            "¿Carácter del dolor? (opresivo, pleurítico, urente)",
            "¿Irradiación? (brazo, mandíbula, espalda)",
            "¿Factores desencadenantes? (esfuerzo, comida, respiración)",
            "¿Síntomas asociados? (disnea, sudoración, náuseas)",
            "¿Antecedentes? (HTA, DM, tabaquismo, TVP previa)",
        ],
        "differentials": [
            DifferentialDiagnosis(
                icd10_code="I21.9",
                name="Síndrome Coronario Agudo",
                probability="Alta si: dolor opresivo, irradiación, disnea, sudoración, factores de riesgo CV",
                key_features=[
                    "Dolor opresivo retroesternal",
                    "Irradiación a brazo izquierdo, mandíbula, espalda",
                    "Disnea, sudoración fría, náuseas",
                    "Factores de riesgo: HTA, DM, tabaquismo, dislipidemia",
                    "Antecedente de enfermedad coronaria",
                ],
                against_features=[
                    "Dolor pleurítico (aumenta con respiración)",
                    "Dolor puntiforme reproducible a palpación",
                    "Duración <1 minuto o >24 horas sin cambios",
                ],
                tests=[
                    DiagnosticTest(
                        "Troponina I/T ultrasensible",
                        "Laboratorio",
                        "Necrosis miocárdica",
                        "Elevación >percentil 99",
                        1,
                    ),
                    DiagnosticTest(
                        "ECG 12 derivaciones",
                        "Funcional",
                        "Isquemia/lesión",
                        "ST elevado/deprimido, ondas T invertidas, Q patológicas",
                        1,
                    ),
                    DiagnosticTest(
                        "Ecocardiograma",
                        "Imagen",
                        "Alteraciones de motilidad",
                        "Hipoquinesia/aquinesia segmentaria",
                        1,
                    ),
                    DiagnosticTest(
                        "Angiografía coronaria",
                        "Procedimiento",
                        "Lesiones coronarias",
                        "Estenosis >70% en coronaria principal",
                        2,
                    ),
                ],
                urgency=Urgency.EMERGENT,
                red_flags=[
                    "Dolor en reposo >20 min",
                    "Hipotensión",
                    "Síncope",
                    "Sudoración profusa",
                ],
            ),
            DifferentialDiagnosis(
                icd10_code="I26.9",
                name="Embolia Pulmonar",
                probability="Alta si: dolor pleurítico, disnea súbita, factores de riesgo TEP, antecedente TVP",
                key_features=[
                    "Dolor pleurítico súbito",
                    "Disnea desproporcionada",
                    "Taquicardia, taquipnea",
                    "Hemoptisis",
                    "Factores de riesgo: inmovilización, cirugía reciente, cáncer, ACO",
                ],
                against_features=[
                    "Dolor opresivo típico coronario",
                    "Sin factores de riesgo para TEP",
                    "Ortopnea clara (más sugestiva de ICC)",
                ],
                tests=[
                    DiagnosticTest(
                        "Dímero-D",
                        "Laboratorio",
                        "Activación coagulación",
                        ">500 ng/mL (sensible, no específico)",
                        1,
                    ),
                    DiagnosticTest(
                        "Angio-TC pulmonar",
                        "Imagen",
                        "Trombo en arterias pulmonares",
                        "Defecto de llenado en arterias pulmonares",
                        1,
                    ),
                    DiagnosticTest(
                        "Gasometría arterial",
                        "Laboratorio",
                        "Hipoxemia",
                        "PaO2 baja, gradiente A-a aumentado",
                        1,
                    ),
                    DiagnosticTest(
                        "Ecocardiograma",
                        "Imagen",
                        "Sobrecarga VD",
                        "Dilatación VD, movimiento paradójico septum",
                        2,
                    ),
                ],
                urgency=Urgency.EMERGENT,
                red_flags=["Hipotensión", "Síncope", "SpO2 <90%", "Signos de TVP"],
            ),
            DifferentialDiagnosis(
                icd10_code="I30.9",
                name="Pericarditis Aguda",
                probability="Moderada si: dolor que mejora al inclinarse adelante, frote pericárdico, fiebre",
                key_features=[
                    "Dolor agudo, pleurítico",
                    "Mejora al inclinarse hacia adelante",
                    "Empeora con decúbito e inspiración",
                    "Fiebre, antecedente viral reciente",
                    "Frote pericárdico a la auscultación",
                ],
                against_features=[
                    "Irradiación a brazo típica de SCA",
                    "Dolor con esfuerzo típico",
                    "Sin síndrome febril",
                ],
                tests=[
                    DiagnosticTest(
                        "ECG",
                        "Funcional",
                        "Cambios pericardíticos",
                        "Elevación difusa ST cóncava, depresión PR",
                        1,
                    ),
                    DiagnosticTest(
                        "Ecocardiograma",
                        "Imagen",
                        "Derrame pericárdico",
                        "Derrame pericárdico, descartar taponamiento",
                        1,
                    ),
                    DiagnosticTest(
                        "Troponina",
                        "Laboratorio",
                        "Miopericarditis",
                        "Puede estar levemente elevada",
                        1,
                    ),
                    DiagnosticTest(
                        "PCR, VSG", "Laboratorio", "Inflamación", "Elevados", 1
                    ),
                ],
                urgency=Urgency.URGENT,
                red_flags=[
                    "Hipotensión (taponamiento)",
                    "Ingurgitación yugular",
                    "Pulso paradójico",
                ],
            ),
            DifferentialDiagnosis(
                icd10_code="K21.0",
                name="Enfermedad por Reflujo Gastroesofágico",
                probability="Moderada si: pirosis, regurgitación, relación con comidas, mejora con antiácidos",
                key_features=[
                    "Dolor urente retroesternal",
                    "Pirosis, regurgitación ácida",
                    "Empeora postprandial y al acostarse",
                    "Mejora con antiácidos o IBP",
                    "Sin síntomas de alarma cardiovascular",
                ],
                against_features=[
                    "Dolor con esfuerzo físico",
                    "Irradiación a brazo/mandíbula",
                    "Disnea asociada",
                    "Factores de riesgo CV sin control",
                ],
                tests=[
                    DiagnosticTest(
                        "Prueba terapéutica con IBP",
                        "Funcional",
                        "Respuesta a supresión ácida",
                        "Mejoría en 1-2 semanas",
                        1,
                    ),
                    DiagnosticTest(
                        "Endoscopia digestiva alta",
                        "Procedimiento",
                        "Esofagitis, Barrett",
                        "Erosiones esofágicas, metaplasia",
                        2,
                    ),
                    DiagnosticTest(
                        "pH-metría 24h",
                        "Funcional",
                        "Exposición ácida patológica",
                        "% tiempo pH<4 elevado",
                        3,
                    ),
                ],
                urgency=Urgency.ELECTIVE,
                red_flags=["Disfagia progresiva", "Pérdida de peso", "Hematemesis"],
            ),
            DifferentialDiagnosis(
                icd10_code="R07.4",
                name="Dolor Musculoesquelético de Pared Torácica",
                probability="Alta si: dolor reproducible a palpación, relación con movimiento, sin síntomas sistémicos",
                key_features=[
                    "Dolor reproducible a la palpación",
                    "Relación clara con movimiento o posición",
                    "Sin síntomas cardiovasculares ni respiratorios",
                    "Antecedente de trauma o esfuerzo físico",
                    "Dolor localizado en área específica",
                ],
                against_features=[
                    "Dolor opresivo no reproducible",
                    "Síntomas sistémicos",
                    "Factores de riesgo CV significativos",
                ],
                tests=[
                    DiagnosticTest(
                        "Ninguno inicialmente",
                        "Clínico",
                        "Diagnóstico clínico",
                        "Dolor reproducible, resto normal",
                        1,
                    ),
                    DiagnosticTest(
                        "Rx tórax",
                        "Imagen",
                        "Descartar fractura costal",
                        "Normal o fractura visible",
                        2,
                    ),
                ],
                urgency=Urgency.ELECTIVE,
                red_flags=[
                    "Síntomas sistémicos nuevos",
                    "Cambio de características del dolor",
                ],
            ),
        ],
    },
    # =========================================================================
    # DISNEA
    # =========================================================================
    "disnea": {
        "category": "Cardiopulmonar",
        "key_questions": [
            "¿Inicio agudo o progresivo?",
            "¿En reposo o con esfuerzo?",
            "¿Ortopnea, DPN?",
            "¿Síntomas asociados? (tos, fiebre, dolor torácico, edemas)",
            "¿Antecedentes? (cardiopatía, EPOC, asma)",
        ],
        "differentials": [
            DifferentialDiagnosis(
                icd10_code="I50.9",
                name="Insuficiencia Cardíaca Aguda/Descompensada",
                probability="Alta si: ortopnea, DPN, edemas, ingurgitación yugular, antecedente cardíaco",
                key_features=[
                    "Disnea de esfuerzo progresiva",
                    "Ortopnea (disnea al acostarse)",
                    "Disnea paroxística nocturna",
                    "Edema de miembros inferiores",
                    "Ingurgitación yugular",
                    "Crepitantes pulmonares basales",
                ],
                against_features=[
                    "Inicio súbito sin antecedente cardíaco",
                    "Fiebre alta (pensar neumonía)",
                    "Sibilancias prominentes (pensar asma/EPOC)",
                ],
                tests=[
                    DiagnosticTest(
                        "BNP/NT-proBNP",
                        "Laboratorio",
                        "Estrés miocárdico",
                        "BNP >400 pg/mL, NT-proBNP >900 pg/mL",
                        1,
                    ),
                    DiagnosticTest(
                        "Rx tórax",
                        "Imagen",
                        "Congestión pulmonar",
                        "Redistribución vascular, edema intersticial/alveolar, cardiomegalia",
                        1,
                    ),
                    DiagnosticTest(
                        "Ecocardiograma",
                        "Imagen",
                        "Función ventricular",
                        "FE reducida, disfunción diastólica, valvulopatías",
                        1,
                    ),
                    DiagnosticTest(
                        "ECG",
                        "Funcional",
                        "Arritmias, isquemia",
                        "FA, bloqueos, signos de hipertrofia",
                        1,
                    ),
                ],
                urgency=Urgency.EMERGENT,
                red_flags=[
                    "SpO2 <90%",
                    "Hipotensión",
                    "Confusión",
                    "Disnea en reposo severa",
                ],
            ),
            DifferentialDiagnosis(
                icd10_code="J44.1",
                name="EPOC Exacerbado",
                probability="Alta si: antecedente EPOC, aumento disnea/tos/esputo, exposición a desencadenantes",
                key_features=[
                    "Antecedente de EPOC o tabaquismo intenso",
                    "Aumento de disnea sobre basal",
                    "Cambio en cantidad/purulencia de esputo",
                    "Tos productiva crónica",
                    "Sibilancias, uso de músculos accesorios",
                ],
                against_features=[
                    "Inicio súbito (pensar TEP, neumotórax)",
                    "Fiebre alta sin cambio de esputo",
                    "Edema periférico prominente (pensar ICC)",
                ],
                tests=[
                    DiagnosticTest(
                        "Rx tórax",
                        "Imagen",
                        "Descartar neumonía, neumotórax",
                        "Hiperinsuflación, sin consolidación",
                        1,
                    ),
                    DiagnosticTest(
                        "Gasometría arterial",
                        "Laboratorio",
                        "Insuficiencia respiratoria",
                        "Hipoxemia ± hipercapnia",
                        1,
                    ),
                    DiagnosticTest(
                        "Hemograma, PCR",
                        "Laboratorio",
                        "Infección",
                        "Leucocitosis, PCR elevada si infección",
                        1,
                    ),
                    DiagnosticTest(
                        "Espirometría",
                        "Funcional",
                        "Obstrucción",
                        "FEV1/FVC <0.7 (basal)",
                        2,
                    ),
                ],
                urgency=Urgency.URGENT,
                red_flags=[
                    "Confusión",
                    "Cianosis",
                    "SpO2 <88%",
                    "Acidosis respiratoria",
                ],
            ),
            DifferentialDiagnosis(
                icd10_code="J18.9",
                name="Neumonía Adquirida en la Comunidad",
                probability="Alta si: fiebre, tos productiva, crepitantes localizados, leucocitosis",
                key_features=[
                    "Fiebre, escalofríos",
                    "Tos productiva (esputo purulento)",
                    "Dolor pleurítico",
                    "Crepitantes focales a la auscultación",
                    "Disnea de instalación relativamente aguda",
                ],
                against_features=[
                    "Sin fiebre (no descarta, pero menos típico)",
                    "Ortopnea clara (pensar ICC)",
                    "Historia típica de asma/EPOC sin infección",
                ],
                tests=[
                    DiagnosticTest(
                        "Rx tórax",
                        "Imagen",
                        "Consolidación pulmonar",
                        "Infiltrado lobar o bronconeumónico",
                        1,
                    ),
                    DiagnosticTest(
                        "Hemograma, PCR, Procalcitonina",
                        "Laboratorio",
                        "Infección bacteriana",
                        "Leucocitosis, neutrofilia, PCT >0.25 ng/mL",
                        1,
                    ),
                    DiagnosticTest(
                        "Hemocultivos x 2",
                        "Laboratorio",
                        "Bacteriemia",
                        "Identificación de patógeno",
                        1,
                    ),
                    DiagnosticTest(
                        "Antígeno urinario Legionella y Neumococo",
                        "Laboratorio",
                        "Identificación rápida",
                        "Positivo según etiología",
                        2,
                    ),
                ],
                urgency=Urgency.URGENT,
                red_flags=[
                    "Confusión",
                    "PA <90/60",
                    "FR >30",
                    "SpO2 <90%",
                    "Multilobar",
                ],
            ),
            DifferentialDiagnosis(
                icd10_code="J45.9",
                name="Asma Bronquial / Crisis Asmática",
                probability="Alta si: sibilancias, antecedente asma, exposición a desencadenante, reversibilidad",
                key_features=[
                    "Sibilancias espiratorias difusas",
                    "Antecedente de asma o atopia",
                    "Exposición a alérgeno, infección viral, ejercicio",
                    "Opresión torácica",
                    "Tos seca, peor nocturna",
                    "Respuesta a broncodilatadores",
                ],
                against_features=[
                    "Fiebre alta (pensar infección)",
                    "Esputo purulento abundante",
                    "Edema periférico",
                ],
                tests=[
                    DiagnosticTest(
                        "Peak flow / Espirometría",
                        "Funcional",
                        "Obstrucción reversible",
                        "FEV1 reducido, mejora >12% post-BD",
                        1,
                    ),
                    DiagnosticTest(
                        "Gasometría arterial (si severa)",
                        "Laboratorio",
                        "Gravedad",
                        "PaO2 baja, PaCO2 normal→baja→alta (agotamiento)",
                        1,
                    ),
                    DiagnosticTest(
                        "Rx tórax",
                        "Imagen",
                        "Descartar complicaciones",
                        "Hiperinsuflación, descartar neumotórax",
                        2,
                    ),
                ],
                urgency=Urgency.URGENT,
                red_flags=[
                    "Silencio auscultatorio",
                    "Uso de músculos accesorios",
                    "Confusión",
                    "Cianosis",
                ],
            ),
        ],
    },
    # =========================================================================
    # CEFALEA
    # =========================================================================
    "cefalea": {
        "category": "Neurología",
        "key_questions": [
            "¿Primera vez o cefalea crónica?",
            "¿Inicio súbito (trueno) o gradual?",
            "¿Síntomas neurológicos asociados?",
            "¿Fiebre, rigidez de nuca?",
            "¿Antecedentes de migraña, trauma reciente?",
        ],
        "differentials": [
            DifferentialDiagnosis(
                icd10_code="I60.9",
                name="Hemorragia Subaracnoidea",
                probability="Alta si: cefalea 'la peor de mi vida', inicio súbito, rigidez nuca, alt. conciencia",
                key_features=[
                    "Cefalea en trueno (máxima intensidad en segundos)",
                    "'La peor cefalea de mi vida'",
                    "Rigidez de nuca, signos meníngeos",
                    "Náuseas, vómitos",
                    "Alteración del nivel de conciencia",
                    "Fotofobia",
                ],
                against_features=[
                    "Cefalea que mejora espontáneamente en minutos",
                    "Historia típica de migraña sin cambios",
                    "Instalación gradual",
                ],
                tests=[
                    DiagnosticTest(
                        "TC cráneo sin contraste",
                        "Imagen",
                        "Sangre subaracnoidea",
                        "Hiperdensidad en cisternas, surcos",
                        1,
                    ),
                    DiagnosticTest(
                        "Punción lumbar (si TC negativa)",
                        "Procedimiento",
                        "Xantocromía",
                        "LCR hemorrágico o xantocrómico",
                        1,
                    ),
                    DiagnosticTest(
                        "Angio-TC o Angio-RM",
                        "Imagen",
                        "Aneurisma",
                        "Aneurisma cerebral roto",
                        2,
                    ),
                ],
                urgency=Urgency.EMERGENT,
                red_flags=[
                    "Inicio en trueno",
                    "Alt. conciencia",
                    "Déficit neurológico",
                    "Convulsiones",
                ],
            ),
            DifferentialDiagnosis(
                icd10_code="G03.9",
                name="Meningitis",
                probability="Alta si: fiebre, cefalea, rigidez de nuca, alt. conciencia, signos meníngeos",
                key_features=[
                    "Tríada: fiebre + cefalea + rigidez de nuca",
                    "Alteración del nivel de conciencia",
                    "Fotofobia",
                    "Náuseas, vómitos",
                    "Signos de Kernig, Brudzinski positivos",
                    "Rash petequial (meningococo)",
                ],
                against_features=[
                    "Sin fiebre (no descarta viral)",
                    "Cefalea típica de migraña sin síntomas sistémicos",
                ],
                tests=[
                    DiagnosticTest(
                        "Punción lumbar",
                        "Procedimiento",
                        "Análisis LCR",
                        "Pleocitosis, glucosa baja, proteínas altas (bacteriana)",
                        1,
                    ),
                    DiagnosticTest(
                        "Hemocultivos x 2",
                        "Laboratorio",
                        "Bacteriemia",
                        "Identificación de patógeno",
                        1,
                    ),
                    DiagnosticTest(
                        "TC cráneo (previo a PL si indicado)",
                        "Imagen",
                        "Descartar masa, hidrocefalia",
                        "Antes de PL si alt. conciencia, déficit focal",
                        1,
                    ),
                    DiagnosticTest(
                        "Procalcitonina, PCR",
                        "Laboratorio",
                        "Infección bacteriana",
                        "Elevadas en bacteriana",
                        1,
                    ),
                ],
                urgency=Urgency.EMERGENT,
                red_flags=["Rash petequial", "Shock", "Convulsiones", "Coma"],
            ),
            DifferentialDiagnosis(
                icd10_code="G43.9",
                name="Migraña",
                probability="Alta si: cefalea recurrente, unilateral pulsátil, náuseas, foto/fonofobia, aura",
                key_features=[
                    "Cefalea unilateral, pulsátil",
                    "Intensidad moderada-severa",
                    "Duración 4-72 horas",
                    "Náuseas, vómitos",
                    "Fotofobia, fonofobia",
                    "Aura visual previa (en 25%)",
                    "Empeora con actividad física",
                ],
                against_features=[
                    "Primera cefalea en persona >50 años",
                    "Inicio en trueno",
                    "Fiebre, rigidez de nuca",
                    "Déficit neurológico persistente",
                ],
                tests=[
                    DiagnosticTest(
                        "Ninguno en migraña típica",
                        "Clínico",
                        "Diagnóstico clínico",
                        "Criterios ICHD-3",
                        1,
                    ),
                    DiagnosticTest(
                        "RM cerebral (si atípica)",
                        "Imagen",
                        "Descartar lesiones estructurales",
                        "Normal",
                        2,
                    ),
                ],
                urgency=Urgency.ELECTIVE,
                red_flags=[
                    "Primera migraña >50 años",
                    "Cambio de patrón",
                    "Aura prolongada",
                    "Déficit focal",
                ],
            ),
            DifferentialDiagnosis(
                icd10_code="G44.2",
                name="Cefalea Tensional",
                probability="Alta si: cefalea bilateral, opresiva, leve-moderada, sin síntomas asociados",
                key_features=[
                    "Cefalea bilateral",
                    "Carácter opresivo/constrictivo ('como banda')",
                    "Intensidad leve a moderada",
                    "No empeora con actividad física",
                    "Sin náuseas significativas",
                    "Puede tener foto o fonofobia (no ambas)",
                ],
                against_features=[
                    "Dolor unilateral pulsátil severo",
                    "Náuseas/vómitos prominentes",
                    "Inicio súbito",
                ],
                tests=[
                    DiagnosticTest(
                        "Ninguno",
                        "Clínico",
                        "Diagnóstico clínico",
                        "Criterios ICHD-3",
                        1,
                    )
                ],
                urgency=Urgency.ELECTIVE,
                red_flags=[
                    "Cambio de patrón",
                    "Síntomas neurológicos",
                    "Inicio >50 años",
                ],
            ),
        ],
    },
    # =========================================================================
    # DOLOR ABDOMINAL
    # =========================================================================
    "dolor abdominal": {
        "category": "Gastrointestinal",
        "key_questions": [
            "¿Localización del dolor?",
            "¿Inicio agudo o progresivo?",
            "¿Relación con comidas?",
            "¿Síntomas asociados? (náuseas, vómitos, fiebre, diarrea)",
            "¿Antecedentes quirúrgicos?",
        ],
        "differentials": [
            DifferentialDiagnosis(
                icd10_code="K35.9",
                name="Apendicitis Aguda",
                probability="Alta si: dolor periumbilical→FID, anorexia, fiebre, defensa en FID",
                key_features=[
                    "Dolor periumbilical que migra a FID",
                    "Anorexia",
                    "Náuseas, vómitos (después del dolor)",
                    "Febrícula",
                    "Signo de McBurney positivo",
                    "Defensa/rebote en FID",
                ],
                against_features=[
                    "Diarrea profusa desde el inicio",
                    "Dolor en hipocondrio derecho",
                    "Síntomas urinarios prominentes",
                ],
                tests=[
                    DiagnosticTest(
                        "Hemograma",
                        "Laboratorio",
                        "Leucocitosis",
                        ">10,000/mm³, neutrofilia",
                        1,
                    ),
                    DiagnosticTest("PCR", "Laboratorio", "Inflamación", "Elevada", 1),
                    DiagnosticTest(
                        "TC abdomen-pelvis con contraste",
                        "Imagen",
                        "Apéndice inflamado",
                        "Diámetro >6mm, grasa periapendicular, apendicolito",
                        1,
                    ),
                    DiagnosticTest(
                        "Ecografía (embarazadas, niños)",
                        "Imagen",
                        "Apéndice no compresible",
                        "Diámetro >6mm, dolor focal",
                        1,
                    ),
                ],
                urgency=Urgency.EMERGENT,
                red_flags=[
                    "Peritonitis generalizada",
                    "Masa palpable (absceso)",
                    "Shock",
                ],
            ),
            DifferentialDiagnosis(
                icd10_code="K56.6",
                name="Obstrucción Intestinal",
                probability="Alta si: dolor cólico, distensión, vómitos, ausencia de gases/deposiciones",
                key_features=[
                    "Dolor abdominal cólico",
                    "Distensión abdominal progresiva",
                    "Vómitos (fecaloideos si bajo)",
                    "Ausencia de eliminación de gases y heces",
                    "Antecedente de cirugía abdominal (bridas)",
                    "RHA aumentados (metálicos) o ausentes",
                ],
                against_features=[
                    "Diarrea abundante",
                    "Dolor localizado en un cuadrante",
                    "Fiebre alta desde el inicio",
                ],
                tests=[
                    DiagnosticTest(
                        "Rx abdomen simple",
                        "Imagen",
                        "Niveles hidroaéreos",
                        "Asas dilatadas, niveles hidroaéreos",
                        1,
                    ),
                    DiagnosticTest(
                        "TC abdomen con contraste",
                        "Imagen",
                        "Sitio y causa de obstrucción",
                        "Punto de transición, causa",
                        1,
                    ),
                    DiagnosticTest(
                        "Hemograma, electrolitos",
                        "Laboratorio",
                        "Deshidratación",
                        "Hemoconcentración, alteraciones electrolíticas",
                        1,
                    ),
                ],
                urgency=Urgency.EMERGENT,
                red_flags=[
                    "Fiebre + taquicardia (estrangulación)",
                    "Peritonismo",
                    "Shock",
                ],
            ),
            DifferentialDiagnosis(
                icd10_code="K80.2",
                name="Colecistitis Aguda",
                probability="Alta si: dolor en HD, signo Murphy+, fiebre, leucocitosis, cálculos biliares",
                key_features=[
                    "Dolor en hipocondrio derecho, continuo (>6 horas)",
                    "Signo de Murphy positivo",
                    "Fiebre",
                    "Náuseas, vómitos",
                    "Relación con comida grasa",
                    "Antecedente de cólicos biliares",
                ],
                against_features=[
                    "Dolor en FID",
                    "Diarrea prominente",
                    "Ictericia marcada (pensar coledocolitiasis)",
                ],
                tests=[
                    DiagnosticTest(
                        "Ecografía abdominal",
                        "Imagen",
                        "Signos de colecistitis",
                        "Engrosamiento pared >3mm, Murphy ecográfico, cálculos",
                        1,
                    ),
                    DiagnosticTest(
                        "Hemograma, PCR",
                        "Laboratorio",
                        "Inflamación",
                        "Leucocitosis, PCR elevada",
                        1,
                    ),
                    DiagnosticTest(
                        "Perfil hepático",
                        "Laboratorio",
                        "Colestasis",
                        "Bilirrubina, FA, GGT elevadas si coledocolitiasis",
                        1,
                    ),
                ],
                urgency=Urgency.URGENT,
                red_flags=[
                    "Fiebre alta con escalofríos (colangitis)",
                    "Ictericia",
                    "Peritonitis",
                ],
            ),
            DifferentialDiagnosis(
                icd10_code="K85.9",
                name="Pancreatitis Aguda",
                probability="Alta si: dolor epigástrico intenso irradiado a espalda, lipasa elevada >3x, náuseas",
                key_features=[
                    "Dolor epigástrico intenso, en barra",
                    "Irradiación a espalda",
                    "Alivia al inclinarse hacia adelante",
                    "Náuseas, vómitos intensos",
                    "Antecedente de alcohol o cálculos biliares",
                ],
                against_features=[
                    "Dolor localizado en FID",
                    "Diarrea sanguinolenta",
                    "Mejora con antiácidos",
                ],
                tests=[
                    DiagnosticTest(
                        "Lipasa sérica",
                        "Laboratorio",
                        "Pancreatitis",
                        ">3x límite superior normal",
                        1,
                    ),
                    DiagnosticTest(
                        "Amilasa sérica",
                        "Laboratorio",
                        "Pancreatitis",
                        "Elevada (menos específica que lipasa)",
                        1,
                    ),
                    DiagnosticTest(
                        "TC abdomen con contraste (48-72h)",
                        "Imagen",
                        "Necrosis, complicaciones",
                        "Inflamación pancreática, necrosis, colecciones",
                        2,
                    ),
                    DiagnosticTest(
                        "Ecografía abdominal",
                        "Imagen",
                        "Etiología biliar",
                        "Cálculos biliares, dilatación colédoco",
                        1,
                    ),
                ],
                urgency=Urgency.EMERGENT,
                red_flags=[
                    "Shock",
                    "Insuficiencia respiratoria",
                    "Oliguria",
                    "Signos de Cullen/Grey-Turner",
                ],
            ),
        ],
    },
    # =========================================================================
    # FIEBRE
    # =========================================================================
    "fiebre": {
        "category": "Infeccioso/Sistémico",
        "key_questions": [
            "¿Duración de la fiebre?",
            "¿Síntomas acompañantes? (tos, disuria, cefalea, rash)",
            "¿Viajes recientes?",
            "¿Contacto con enfermos?",
            "¿Inmunosupresión?",
        ],
        "differentials": [
            DifferentialDiagnosis(
                icd10_code="J06.9",
                name="Infección Respiratoria Alta Viral",
                probability="Alta si: rinorrea, odinofagia, tos, mialgias, contacto con enfermo",
                key_features=[
                    "Fiebre baja-moderada (37.5-38.5°C)",
                    "Rinorrea, congestión nasal",
                    "Odinofagia leve",
                    "Tos seca",
                    "Mialgias, malestar general",
                    "Duración autolimitada 5-7 días",
                ],
                against_features=[
                    "Fiebre >39°C persistente",
                    "Síntomas focales severos",
                    "Inmunosupresión",
                ],
                tests=[
                    DiagnosticTest(
                        "Ninguno (diagnóstico clínico)",
                        "Clínico",
                        "Cuadro viral típico",
                        "Resolución espontánea",
                        1,
                    ),
                    DiagnosticTest(
                        "Test rápido influenza/COVID (si epidemia)",
                        "Laboratorio",
                        "Etiología específica",
                        "Positivo según virus",
                        2,
                    ),
                ],
                urgency=Urgency.ELECTIVE,
                red_flags=[
                    "Disnea",
                    "Fiebre >5 días",
                    "Empeoramiento tras mejoría inicial",
                ],
            ),
            DifferentialDiagnosis(
                icd10_code="N39.0",
                name="Infección del Tracto Urinario",
                probability="Alta si: disuria, polaquiuria, dolor suprapúbico, orina turbia",
                key_features=[
                    "Disuria (dolor al orinar)",
                    "Polaquiuria, urgencia miccional",
                    "Dolor suprapúbico",
                    "Orina turbia o maloliente",
                    "Fiebre baja (ITU baja) o alta (pielonefritis)",
                ],
                against_features=[
                    "Sin síntomas urinarios",
                    "Dolor lumbar sin síntomas urinarios",
                ],
                tests=[
                    DiagnosticTest(
                        "Uroanálisis con tira reactiva",
                        "Laboratorio",
                        "Piuria, nitritos",
                        "Leucocitos +, nitritos +",
                        1,
                    ),
                    DiagnosticTest(
                        "Urocultivo",
                        "Laboratorio",
                        "Identificación bacteriana",
                        ">100,000 UFC/mL",
                        1,
                    ),
                    DiagnosticTest(
                        "Hemograma, creatinina",
                        "Laboratorio",
                        "Severidad",
                        "Leucocitosis si complicada",
                        1,
                    ),
                ],
                urgency=Urgency.URGENT,
                red_flags=[
                    "Fiebre alta con escalofríos (pielonefritis)",
                    "Dolor lumbar intenso",
                    "Náuseas/vómitos",
                ],
            ),
            DifferentialDiagnosis(
                icd10_code="A09.9",
                name="Gastroenteritis Aguda",
                probability="Alta si: fiebre + diarrea + náuseas/vómitos, alimento sospechoso",
                key_features=[
                    "Diarrea aguda (>3 deposiciones/día)",
                    "Náuseas, vómitos",
                    "Dolor abdominal cólico",
                    "Fiebre baja-moderada",
                    "Antecedente de alimento sospechoso",
                ],
                against_features=[
                    "Diarrea con sangre abundante",
                    "Fiebre muy alta >39.5°C prolongada",
                    "Síntomas >7 días",
                ],
                tests=[
                    DiagnosticTest(
                        "Ninguno inicialmente",
                        "Clínico",
                        "Cuadro autolimitado",
                        "Mejoría en 48-72h",
                        1,
                    ),
                    DiagnosticTest(
                        "Coprocultivo (si severa)",
                        "Laboratorio",
                        "Identificación patógeno",
                        "Salmonella, Shigella, Campylobacter",
                        2,
                    ),
                ],
                urgency=Urgency.SEMI_URGENT,
                red_flags=[
                    "Deshidratación severa",
                    "Sangre en heces",
                    "Fiebre >39.5°C",
                    "Inmunosupresión",
                ],
            ),
            DifferentialDiagnosis(
                icd10_code="A41.9",
                name="Sepsis",
                probability="Alta si: fiebre + taquicardia + taquipnea + hipotensión + foco infeccioso",
                key_features=[
                    "Fiebre alta o hipotermia",
                    "Taquicardia >90 lpm",
                    "Taquipnea >20/min",
                    "Alteración del estado mental",
                    "Hipotensión (PAS <100)",
                    "Foco infeccioso identificable",
                ],
                against_features=[
                    "Signos vitales normales",
                    "Buen estado general",
                    "Sin foco infeccioso",
                ],
                tests=[
                    DiagnosticTest(
                        "Hemocultivos x 2",
                        "Laboratorio",
                        "Bacteriemia",
                        "Identificación de patógeno",
                        1,
                    ),
                    DiagnosticTest(
                        "Lactato sérico", "Laboratorio", "Hipoperfusión", ">2 mmol/L", 1
                    ),
                    DiagnosticTest(
                        "Procalcitonina",
                        "Laboratorio",
                        "Infección bacteriana",
                        ">0.5 ng/mL",
                        1,
                    ),
                    DiagnosticTest(
                        "Hemograma, creatinina, bilirrubina",
                        "Laboratorio",
                        "Disfunción orgánica",
                        "Leucocitosis/leucopenia, falla orgánica",
                        1,
                    ),
                ],
                urgency=Urgency.EMERGENT,
                red_flags=[
                    "Hipotensión refractaria",
                    "Lactato >4",
                    "Alteración conciencia",
                    "Falla multiorgánica",
                ],
            ),
        ],
    },
    # =========================================================================
    # TOS
    # =========================================================================
    "tos": {
        "category": "Respiratorio",
        "key_questions": [
            "¿Aguda (<3 semanas) o crónica?",
            "¿Productiva o seca?",
            "¿Síntomas asociados? (fiebre, disnea, sibilancias)",
            "¿Tabaquismo?",
            "¿Medicamentos? (IECA)",
        ],
        "differentials": [
            DifferentialDiagnosis(
                icd10_code="J06.9",
                name="Infección Respiratoria Alta",
                probability="Alta si: tos aguda + rinorrea + odinofagia, sin disnea",
                key_features=[
                    "Tos aguda <3 semanas",
                    "Rinorrea, congestión",
                    "Odinofagia",
                    "Febrícula",
                    "Sin disnea significativa",
                ],
                against_features=[
                    "Disnea en reposo",
                    "Fiebre alta persistente",
                    "Tos >3 semanas",
                ],
                tests=[
                    DiagnosticTest(
                        "Ninguno",
                        "Clínico",
                        "Diagnóstico clínico",
                        "Cuadro autolimitado",
                        1,
                    )
                ],
                urgency=Urgency.ELECTIVE,
                red_flags=["Disnea progresiva", "Hemoptisis", "Fiebre >5 días"],
            ),
            DifferentialDiagnosis(
                icd10_code="J18.9",
                name="Neumonía",
                probability="Alta si: tos productiva + fiebre + disnea + crepitantes localizados",
                key_features=[
                    "Tos productiva (esputo purulento)",
                    "Fiebre, escalofríos",
                    "Disnea",
                    "Dolor pleurítico",
                    "Crepitantes a la auscultación",
                ],
                against_features=[
                    "Tos seca sin fiebre",
                    "Auscultación normal",
                    "Buen estado general",
                ],
                tests=[
                    DiagnosticTest(
                        "Rx tórax", "Imagen", "Consolidación", "Infiltrado pulmonar", 1
                    ),
                    DiagnosticTest(
                        "Hemograma, PCR",
                        "Laboratorio",
                        "Infección",
                        "Leucocitosis, PCR elevada",
                        1,
                    ),
                    DiagnosticTest(
                        "Saturación O2", "Funcional", "Hipoxemia", "<94%", 1
                    ),
                ],
                urgency=Urgency.URGENT,
                red_flags=["SpO2 <90%", "Confusión", "Hipotensión", "FR >30"],
            ),
            DifferentialDiagnosis(
                icd10_code="J45.9",
                name="Asma",
                probability="Alta si: tos nocturna + sibilancias + antecedente atopia, reversible con BD",
                key_features=[
                    "Tos predominantemente nocturna",
                    "Sibilancias espiratorias",
                    "Opresión torácica",
                    "Desencadenantes: alérgenos, ejercicio, frío",
                    "Antecedente personal/familiar de atopia",
                ],
                against_features=[
                    "Esputo purulento abundante",
                    "Fiebre alta",
                    "Sin sibilancias",
                ],
                tests=[
                    DiagnosticTest(
                        "Espirometría con BD",
                        "Funcional",
                        "Obstrucción reversible",
                        "FEV1 mejora >12%",
                        1,
                    ),
                    DiagnosticTest(
                        "Peak flow seriado",
                        "Funcional",
                        "Variabilidad",
                        ">20% variabilidad diurna",
                        1,
                    ),
                ],
                urgency=Urgency.SEMI_URGENT,
                red_flags=[
                    "Uso músculos accesorios",
                    "Silencio auscultatorio",
                    "Cianosis",
                ],
            ),
            DifferentialDiagnosis(
                icd10_code="J44.9",
                name="EPOC / Bronquitis Crónica",
                probability="Alta si: tos crónica + expectoración + tabaquismo >10 paq/año",
                key_features=[
                    "Tos crónica >3 meses/año por 2 años",
                    "Expectoración matutina",
                    "Tabaquismo significativo",
                    "Disnea de esfuerzo progresiva",
                    "Sibilancias, espiración prolongada",
                ],
                against_features=[
                    "No fumador sin exposición",
                    "Tos aguda autolimitada",
                    "Menor de 40 años sin factores",
                ],
                tests=[
                    DiagnosticTest(
                        "Espirometría",
                        "Funcional",
                        "Obstrucción no reversible",
                        "FEV1/FVC <0.7 post-BD",
                        1,
                    ),
                    DiagnosticTest(
                        "Rx tórax",
                        "Imagen",
                        "Hiperinsuflación",
                        "Aplanamiento diafragmático",
                        1,
                    ),
                ],
                urgency=Urgency.SEMI_URGENT,
                red_flags=[
                    "Exacerbación con disnea severa",
                    "Cianosis",
                    "Edemas (cor pulmonale)",
                ],
            ),
        ],
    },
    # =========================================================================
    # NÁUSEAS Y VÓMITOS
    # =========================================================================
    "náuseas": {
        "category": "Gastrointestinal/Sistémico",
        "key_questions": [
            "¿Agudos o crónicos?",
            "¿Relación con alimentos?",
            "¿Dolor abdominal asociado?",
            "¿Medicamentos nuevos?",
            "¿Embarazo posible?",
        ],
        "differentials": [
            DifferentialDiagnosis(
                icd10_code="A09.9",
                name="Gastroenteritis Aguda",
                probability="Alta si: vómitos + diarrea + dolor cólico, autolimitado",
                key_features=[
                    "Vómitos agudos",
                    "Diarrea asociada",
                    "Dolor abdominal cólico difuso",
                    "Fiebre baja",
                    "Contacto con enfermo o alimento sospechoso",
                ],
                against_features=[
                    "Sin diarrea",
                    "Dolor abdominal focalizado severo",
                    "Vómitos crónicos",
                ],
                tests=[
                    DiagnosticTest(
                        "Ninguno inicialmente",
                        "Clínico",
                        "Cuadro autolimitado",
                        "Mejoría 48-72h",
                        1,
                    )
                ],
                urgency=Urgency.SEMI_URGENT,
                red_flags=["Deshidratación severa", "Vómitos en proyectil", "Sangre"],
            ),
            DifferentialDiagnosis(
                icd10_code="K21.0",
                name="ERGE / Gastropatía",
                probability="Alta si: náuseas postprandiales + pirosis + mejora con IBP",
                key_features=[
                    "Náuseas postprandiales",
                    "Pirosis, regurgitación",
                    "Saciedad precoz",
                    "Mejora con antiácidos/IBP",
                    "Relación con comidas grasas",
                ],
                against_features=[
                    "Vómitos biliosos",
                    "Dolor abdominal severo",
                    "Pérdida de peso",
                ],
                tests=[
                    DiagnosticTest(
                        "Prueba con IBP",
                        "Funcional",
                        "Respuesta terapéutica",
                        "Mejoría en 2 semanas",
                        1,
                    ),
                    DiagnosticTest(
                        "Endoscopia (si alarma)",
                        "Procedimiento",
                        "Lesiones mucosas",
                        "Gastritis, úlcera, esofagitis",
                        2,
                    ),
                ],
                urgency=Urgency.ELECTIVE,
                red_flags=[
                    "Pérdida de peso",
                    "Disfagia",
                    "Anemia",
                    "Edad >55 años nuevo",
                ],
            ),
            DifferentialDiagnosis(
                icd10_code="H81.0",
                name="Vértigo / Síndrome Vestibular",
                probability="Alta si: náuseas + vértigo rotatorio + nistagmo",
                key_features=[
                    "Náuseas intensas con vómitos",
                    "Vértigo rotatorio",
                    "Nistagmo",
                    "Empeora con movimientos cefálicos",
                    "Sin cefalea severa ni déficit neurológico",
                ],
                against_features=[
                    "Cefalea severa",
                    "Déficit neurológico focal",
                    "Alteración de conciencia",
                ],
                tests=[
                    DiagnosticTest(
                        "Maniobra de Dix-Hallpike",
                        "Clínico",
                        "VPPB",
                        "Nistagmo posicional",
                        1,
                    ),
                    DiagnosticTest(
                        "Test HINTS (si central)",
                        "Clínico",
                        "Diferenciar periférico vs central",
                        "Patrón periférico vs central",
                        1,
                    ),
                ],
                urgency=Urgency.URGENT,
                red_flags=[
                    "Cefalea intensa",
                    "Diplopía",
                    "Disartria",
                    "Ataxia de tronco",
                ],
            ),
            DifferentialDiagnosis(
                icd10_code="O21.0",
                name="Náuseas del Embarazo / Hiperémesis",
                probability="Alta si: mujer en edad fértil + amenorrea + náuseas matutinas",
                key_features=[
                    "Náuseas matutinas predominantes",
                    "Amenorrea o retraso menstrual",
                    "Edad fértil",
                    "Vómitos sin sangre ni bilis",
                    "Aversión a olores",
                ],
                against_features=[
                    "Test embarazo negativo",
                    "Dolor abdominal severo",
                    "Sangrado vaginal",
                ],
                tests=[
                    DiagnosticTest(
                        "Test de embarazo",
                        "Laboratorio",
                        "Confirmar gestación",
                        "β-hCG positivo",
                        1,
                    ),
                    DiagnosticTest(
                        "Ecografía (si positivo)",
                        "Imagen",
                        "Viabilidad, descartar molar",
                        "Saco gestacional, embrión",
                        2,
                    ),
                ],
                urgency=Urgency.SEMI_URGENT,
                red_flags=["Deshidratación severa", "Cetonuria", "Pérdida peso >5%"],
            ),
        ],
    },
    # =========================================================================
    # DIARREA
    # =========================================================================
    "diarrea": {
        "category": "Gastrointestinal",
        "key_questions": [
            "¿Aguda (<14 días) o crónica?",
            "¿Con sangre o moco?",
            "¿Fiebre asociada?",
            "¿Viaje reciente?",
            "¿Antibióticos recientes?",
        ],
        "differentials": [
            DifferentialDiagnosis(
                icd10_code="A09.9",
                name="Diarrea Infecciosa Aguda",
                probability="Alta si: diarrea aguda + fiebre + dolor cólico, contacto epidemiológico",
                key_features=[
                    "Diarrea acuosa aguda",
                    "Dolor abdominal cólico",
                    "Fiebre baja-moderada",
                    "Náuseas, vómitos",
                    "Duración <7 días típicamente",
                ],
                against_features=[
                    "Diarrea >14 días",
                    "Sangre abundante",
                    "Síntomas nocturnos",
                ],
                tests=[
                    DiagnosticTest(
                        "Ninguno inicialmente",
                        "Clínico",
                        "Cuadro autolimitado",
                        "Mejoría espontánea",
                        1,
                    ),
                    DiagnosticTest(
                        "Coprocultivo (si severa)",
                        "Laboratorio",
                        "Patógeno",
                        "Salmonella, Shigella, Campylobacter",
                        2,
                    ),
                ],
                urgency=Urgency.SEMI_URGENT,
                red_flags=[
                    "Deshidratación severa",
                    "Sangre en heces",
                    "Fiebre >39°C",
                    "Inmunosupresión",
                ],
            ),
            DifferentialDiagnosis(
                icd10_code="A04.7",
                name="Colitis por Clostridioides difficile",
                probability="Alta si: diarrea + antibióticos recientes + hospitalización",
                key_features=[
                    "Diarrea acuosa profusa",
                    "Uso reciente de antibióticos (clindamicina, fluoroquinolonas, cefalosporinas)",
                    "Hospitalización reciente",
                    "Dolor abdominal bajo",
                    "Fiebre, leucocitosis",
                ],
                against_features=[
                    "Sin exposición a antibióticos",
                    "Diarrea con sangre franca",
                    "Ambulatorio sin factores de riesgo",
                ],
                tests=[
                    DiagnosticTest(
                        "Toxina C. difficile en heces",
                        "Laboratorio",
                        "Confirmar infección",
                        "Toxina A/B positiva",
                        1,
                    ),
                    DiagnosticTest(
                        "PCR C. difficile",
                        "Laboratorio",
                        "Detección gen toxina",
                        "Positivo",
                        1,
                    ),
                    DiagnosticTest(
                        "Hemograma",
                        "Laboratorio",
                        "Severidad",
                        "Leucocitosis >15,000",
                        1,
                    ),
                ],
                urgency=Urgency.URGENT,
                red_flags=[
                    "Megacolon tóxico",
                    "Leucocitosis >30,000",
                    "Hipotensión",
                    "Íleo",
                ],
            ),
            DifferentialDiagnosis(
                icd10_code="K58.0",
                name="Síndrome de Intestino Irritable",
                probability="Alta si: diarrea crónica + dolor que mejora al defecar + sin alarmas",
                key_features=[
                    "Diarrea crónica intermitente",
                    "Dolor abdominal que mejora al defecar",
                    "Distensión, meteorismo",
                    "Sin sangre ni pérdida de peso",
                    "Síntomas relacionados con estrés",
                ],
                against_features=[
                    "Sangre en heces",
                    "Pérdida de peso",
                    "Fiebre",
                    "Síntomas nocturnos que despiertan",
                ],
                tests=[
                    DiagnosticTest(
                        "Hemograma, VSG, PCR",
                        "Laboratorio",
                        "Descartar inflamación",
                        "Normales",
                        1,
                    ),
                    DiagnosticTest(
                        "Calprotectina fecal",
                        "Laboratorio",
                        "Descartar EII",
                        "<50 μg/g",
                        1,
                    ),
                    DiagnosticTest(
                        "Serología celíaca",
                        "Laboratorio",
                        "Descartar celiaquía",
                        "IgA anti-TG negativo",
                        1,
                    ),
                ],
                urgency=Urgency.ELECTIVE,
                red_flags=[
                    "Sangre en heces",
                    "Pérdida de peso",
                    "Inicio >50 años",
                    "Anemia",
                ],
            ),
            DifferentialDiagnosis(
                icd10_code="K50.9",
                name="Enfermedad Inflamatoria Intestinal",
                probability="Alta si: diarrea crónica con sangre/moco + dolor + pérdida peso + joven",
                key_features=[
                    "Diarrea crónica con sangre y/o moco",
                    "Dolor abdominal recurrente",
                    "Pérdida de peso",
                    "Fiebre intermitente",
                    "Manifestaciones extraintestinales (artritis, uveítis)",
                    "Edad típica: 15-35 años",
                ],
                against_features=[
                    "Sin sangre ni moco",
                    "Síntomas <4 semanas autolimitados",
                    "Sin pérdida de peso",
                ],
                tests=[
                    DiagnosticTest(
                        "Calprotectina fecal",
                        "Laboratorio",
                        "Inflamación intestinal",
                        ">200 μg/g",
                        1,
                    ),
                    DiagnosticTest(
                        "Colonoscopia con biopsias",
                        "Procedimiento",
                        "Confirmar diagnóstico",
                        "Úlceras, granulomas, patrón inflamatorio",
                        1,
                    ),
                    DiagnosticTest(
                        "Hemograma, VSG, PCR, albúmina",
                        "Laboratorio",
                        "Actividad inflamatoria",
                        "Anemia, PCR elevada, hipoalbuminemia",
                        1,
                    ),
                ],
                urgency=Urgency.URGENT,
                red_flags=[
                    "Hemorragia masiva",
                    "Megacolon tóxico",
                    "Perforación",
                    "Obstrucción",
                ],
            ),
        ],
    },
    # =========================================================================
    # MAREO / VÉRTIGO
    # =========================================================================
    "mareo": {
        "category": "Neurología/Otología",
        "key_questions": [
            "¿Vértigo rotatorio o inestabilidad?",
            "¿Síntomas auditivos? (hipoacusia, tinnitus)",
            "¿Síntomas neurológicos?",
            "¿Posicional?",
            "¿Medicamentos?",
        ],
        "differentials": [
            DifferentialDiagnosis(
                icd10_code="H81.1",
                name="Vértigo Posicional Paroxístico Benigno (VPPB)",
                probability="Alta si: vértigo breve con cambios posición, Dix-Hallpike positivo",
                key_features=[
                    "Vértigo rotatorio breve (<1 minuto)",
                    "Desencadenado por cambios de posición",
                    "Nistagmo posicional característico",
                    "Sin síntomas auditivos",
                    "Sin síntomas neurológicos",
                ],
                against_features=[
                    "Vértigo continuo horas/días",
                    "Hipoacusia asociada",
                    "Déficit neurológico",
                ],
                tests=[
                    DiagnosticTest(
                        "Maniobra de Dix-Hallpike",
                        "Clínico",
                        "VPPB canal posterior",
                        "Nistagmo torsional con latencia",
                        1,
                    ),
                    DiagnosticTest(
                        "Maniobra de Epley (terapéutica)",
                        "Clínico",
                        "Reposición canalicular",
                        "Resolución de síntomas",
                        1,
                    ),
                ],
                urgency=Urgency.ELECTIVE,
                red_flags=["Cefalea intensa", "Diplopía", "Disartria", "Ataxia severa"],
            ),
            DifferentialDiagnosis(
                icd10_code="H81.0",
                name="Enfermedad de Ménière",
                probability="Alta si: vértigo + hipoacusia fluctuante + tinnitus + plenitud ótica",
                key_features=[
                    "Crisis de vértigo rotatorio (20 min - horas)",
                    "Hipoacusia neurosensorial fluctuante",
                    "Tinnitus unilateral",
                    "Sensación de plenitud ótica",
                    "Episodios recurrentes",
                ],
                against_features=[
                    "Vértigo posicional breve",
                    "Sin síntomas auditivos",
                    "Déficit neurológico",
                ],
                tests=[
                    DiagnosticTest(
                        "Audiometría",
                        "Funcional",
                        "Hipoacusia neurosensorial",
                        "Caída en frecuencias graves",
                        1,
                    ),
                    DiagnosticTest(
                        "RM cerebral con gadolinio",
                        "Imagen",
                        "Descartar schwannoma",
                        "Normal o hidrops endolinfático",
                        2,
                    ),
                ],
                urgency=Urgency.SEMI_URGENT,
                red_flags=["Hipoacusia súbita severa", "Síntomas neurológicos"],
            ),
            DifferentialDiagnosis(
                icd10_code="H81.3",
                name="Neuritis Vestibular",
                probability="Alta si: vértigo agudo continuo + náuseas + nistagmo horizontal, sin hipoacusia",
                key_features=[
                    "Vértigo rotatorio agudo, continuo (días)",
                    "Náuseas, vómitos intensos",
                    "Nistagmo horizontal-torsional",
                    "Sin hipoacusia",
                    "Test de impulso cefálico positivo",
                    "Antecedente viral reciente",
                ],
                against_features=[
                    "Vértigo posicional breve",
                    "Hipoacusia asociada",
                    "Síntomas neurológicos focales",
                ],
                tests=[
                    DiagnosticTest(
                        "Test HINTS",
                        "Clínico",
                        "Diferenciar periférico vs central",
                        "Patrón periférico",
                        1,
                    ),
                    DiagnosticTest(
                        "Audiometría",
                        "Funcional",
                        "Descartar laberintitis",
                        "Normal",
                        1,
                    ),
                ],
                urgency=Urgency.URGENT,
                red_flags=["Test HINTS central", "Ataxia de tronco", "Diplopía"],
            ),
            DifferentialDiagnosis(
                icd10_code="I63.9",
                name="ACV de Fosa Posterior / Vértigo Central",
                probability="Alta si: vértigo + HINTS central + factores de riesgo CV",
                key_features=[
                    "Vértigo con HINTS patrón central",
                    "Nistagmo vertical o cambiante",
                    "Ataxia de tronco/marcha",
                    "Diplopía, disartria, disfagia",
                    "Factores de riesgo cardiovascular",
                    "Cefalea occipital",
                ],
                against_features=[
                    "HINTS patrón periférico",
                    "Sin factores de riesgo CV",
                    "Vértigo posicional clásico",
                ],
                tests=[
                    DiagnosticTest(
                        "RM cerebral urgente (DWI)",
                        "Imagen",
                        "Isquemia cerebelosa/tronco",
                        "Restricción difusión",
                        1,
                    ),
                    DiagnosticTest(
                        "Angio-TC/Angio-RM",
                        "Imagen",
                        "Disección vertebral",
                        "Estenosis u oclusión",
                        1,
                    ),
                ],
                urgency=Urgency.EMERGENT,
                red_flags=[
                    "HINTS central",
                    "Ataxia severa",
                    "Disartria",
                    "Déficit neurológico",
                ],
            ),
        ],
    },
    # =========================================================================
    # LUMBALGIA
    # =========================================================================
    "lumbalgia": {
        "category": "Musculoesquelético",
        "key_questions": [
            "¿Mecánica o inflamatoria?",
            "¿Irradiación a piernas? (ciática)",
            "¿Red flags? (trauma, cáncer, fiebre, pérdida peso)",
            "¿Déficit neurológico?",
            "¿Retención urinaria?",
        ],
        "differentials": [
            DifferentialDiagnosis(
                icd10_code="M54.5",
                name="Lumbalgia Mecánica Inespecífica",
                probability="Alta si: dolor lumbar sin irradiación, sin red flags, relacionado con esfuerzo",
                key_features=[
                    "Dolor lumbar localizado",
                    "Relacionado con esfuerzo o postura",
                    "Mejora con reposo relativo",
                    "Sin irradiación por debajo de rodilla",
                    "Examen neurológico normal",
                    "Sin red flags",
                ],
                against_features=[
                    "Irradiación ciática clara",
                    "Déficit neurológico",
                    "Red flags presentes",
                ],
                tests=[
                    DiagnosticTest(
                        "Ninguno inicialmente",
                        "Clínico",
                        "Diagnóstico clínico",
                        "Mejoría en 4-6 semanas",
                        1,
                    ),
                    DiagnosticTest(
                        "Rx lumbar (si >6 sem)",
                        "Imagen",
                        "Descartar patología estructural",
                        "Cambios degenerativos",
                        2,
                    ),
                ],
                urgency=Urgency.ELECTIVE,
                red_flags=[
                    "Déficit neurológico progresivo",
                    "Retención urinaria",
                    "Anestesia en silla de montar",
                ],
            ),
            DifferentialDiagnosis(
                icd10_code="M51.1",
                name="Hernia Discal con Radiculopatía",
                probability="Alta si: dolor lumbar + ciática + Lasègue positivo + distribución dermatómica",
                key_features=[
                    "Dolor lumbar irradiado a pierna",
                    "Distribución dermatómica (L4, L5, S1)",
                    "Signo de Lasègue positivo",
                    "Parestesias en dermatoma",
                    "Posible debilidad focal",
                    "Empeora con Valsalva",
                ],
                against_features=[
                    "Dolor difuso no radicular",
                    "Lasègue negativo",
                    "Dolor solo lumbar sin irradiación",
                ],
                tests=[
                    DiagnosticTest(
                        "RM columna lumbar",
                        "Imagen",
                        "Hernia discal",
                        "Protrusión/extrusión disco, compresión raíz",
                        1,
                    ),
                    DiagnosticTest(
                        "EMG/VCN (si duda)",
                        "Funcional",
                        "Confirmar radiculopatía",
                        "Denervación en miotoma específico",
                        2,
                    ),
                ],
                urgency=Urgency.SEMI_URGENT,
                red_flags=[
                    "Síndrome cauda equina",
                    "Déficit motor progresivo",
                    "Retención urinaria",
                ],
            ),
            DifferentialDiagnosis(
                icd10_code="G83.4",
                name="Síndrome de Cauda Equina",
                probability="Alta si: lumbalgia + retención urinaria + anestesia en silla de montar",
                key_features=[
                    "Dolor lumbar severo",
                    "Retención urinaria o incontinencia",
                    "Anestesia en silla de montar",
                    "Debilidad bilateral MMII",
                    "Arreflexia aquílea bilateral",
                    "Pérdida tono esfínter anal",
                ],
                against_features=[
                    "Función vesical normal",
                    "Sensibilidad perianal conservada",
                    "Fuerza conservada",
                ],
                tests=[
                    DiagnosticTest(
                        "RM columna URGENTE",
                        "Imagen",
                        "Compresión cauda equina",
                        "Hernia masiva, tumor, hematoma",
                        1,
                    ),
                    DiagnosticTest(
                        "Residuo postmiccional",
                        "Funcional",
                        "Retención urinaria",
                        ">100 mL",
                        1,
                    ),
                ],
                urgency=Urgency.EMERGENT,
                red_flags=[
                    "EMERGENCIA QUIRÚRGICA",
                    "Retención urinaria",
                    "Anestesia perianal",
                ],
            ),
            DifferentialDiagnosis(
                icd10_code="M46.4",
                name="Espondilodiscitis / Osteomielitis Vertebral",
                probability="Alta si: lumbalgia + fiebre + VSG elevada + diabetes/inmunosupresión",
                key_features=[
                    "Dolor lumbar constante, nocturno",
                    "Fiebre, escalofríos",
                    "Dolor a percusión espinosa",
                    "Factores riesgo: DM, drogas IV, inmunosupresión",
                    "VSG/PCR muy elevadas",
                ],
                against_features=[
                    "Dolor solo mecánico",
                    "Sin fiebre ni inflamación",
                    "Joven sano sin factores",
                ],
                tests=[
                    DiagnosticTest(
                        "RM columna con contraste",
                        "Imagen",
                        "Infección disco/vértebra",
                        "Edema vertebral, realce discal",
                        1,
                    ),
                    DiagnosticTest(
                        "Hemocultivos x 2",
                        "Laboratorio",
                        "Bacteriemia",
                        "S. aureus más frecuente",
                        1,
                    ),
                    DiagnosticTest(
                        "VSG, PCR", "Laboratorio", "Inflamación", "Muy elevadas", 1
                    ),
                ],
                urgency=Urgency.EMERGENT,
                red_flags=["Déficit neurológico", "Absceso epidural", "Sepsis"],
            ),
        ],
    },
    # =========================================================================
    # SÍNCOPE
    # =========================================================================
    "síncope": {
        "category": "Cardiovascular/Neurología",
        "key_questions": [
            "¿Pródromos? (náuseas, sudoración, visión borrosa)",
            "¿Posición al inicio?",
            "¿Testigos? (movimientos, duración)",
            "¿Recuperación rápida o confusión?",
            "¿Antecedentes cardíacos?",
        ],
        "differentials": [
            DifferentialDiagnosis(
                icd10_code="R55",
                name="Síncope Vasovagal (Neurocardiogénico)",
                probability="Alta si: pródromos típicos + desencadenante + recuperación rápida",
                key_features=[
                    "Pródromos: náuseas, sudoración, calor, visión en túnel",
                    "Desencadenante identificable (bipedestación, dolor, calor)",
                    "Posición de pie o sentado",
                    "Recuperación rápida y completa",
                    "Sin cardiopatía estructural",
                    "Palidez durante episodio",
                ],
                against_features=[
                    "Sin pródromos (síncope súbito)",
                    "Cardiopatía estructural conocida",
                    "Síncope durante ejercicio",
                    "Historia familiar de muerte súbita",
                ],
                tests=[
                    DiagnosticTest(
                        "ECG 12 derivaciones",
                        "Funcional",
                        "Descartar arritmia",
                        "Normal",
                        1,
                    ),
                    DiagnosticTest(
                        "Ortostatismo activo",
                        "Funcional",
                        "Hipotensión ortostática",
                        "Caída PAS >20 o PAD >10",
                        1,
                    ),
                    DiagnosticTest(
                        "Tilt test (si recurrente)",
                        "Funcional",
                        "Confirmar vasovagal",
                        "Respuesta cardioinhibitoria o vasodepresora",
                        2,
                    ),
                ],
                urgency=Urgency.SEMI_URGENT,
                red_flags=[
                    "Sin pródromos",
                    "Durante ejercicio",
                    "Cardiopatía conocida",
                ],
            ),
            DifferentialDiagnosis(
                icd10_code="I49.9",
                name="Síncope Arrítmico",
                probability="Alta si: síncope súbito sin pródromos + cardiopatía + ECG anormal",
                key_features=[
                    "Síncope súbito sin pródromos",
                    "Durante ejercicio o reposo",
                    "Cardiopatía estructural conocida",
                    "ECG anormal (QT largo, Brugada, bloqueos)",
                    "Historia familiar de muerte súbita",
                    "Palpitaciones previas",
                ],
                against_features=[
                    "Pródromos vasovagales típicos",
                    "Desencadenante claro postural",
                    "Corazón estructuralmente normal",
                ],
                tests=[
                    DiagnosticTest(
                        "ECG 12 derivaciones",
                        "Funcional",
                        "Arritmias, canalopatías",
                        "QT largo, Brugada, WPW, bloqueos",
                        1,
                    ),
                    DiagnosticTest(
                        "Ecocardiograma",
                        "Imagen",
                        "Cardiopatía estructural",
                        "MCH, displasia VD, valvulopatía",
                        1,
                    ),
                    DiagnosticTest(
                        "Holter 24-48h",
                        "Funcional",
                        "Arritmias paroxísticas",
                        "Taquiarritmias, bradiarritmias",
                        1,
                    ),
                    DiagnosticTest(
                        "Estudio electrofisiológico",
                        "Procedimiento",
                        "Arritmias inducibles",
                        "TV inducible",
                        2,
                    ),
                ],
                urgency=Urgency.EMERGENT,
                red_flags=[
                    "Cardiopatía estructural",
                    "ECG anormal",
                    "Síncope de esfuerzo",
                    "Muerte súbita familiar",
                ],
            ),
            DifferentialDiagnosis(
                icd10_code="I95.1",
                name="Hipotensión Ortostática",
                probability="Alta si: síncope al ponerse de pie + caída PA documentada + factores de riesgo",
                key_features=[
                    "Síncope/presíncope al levantarse",
                    "Caída PA >20/10 mmHg al ortostatismo",
                    "Uso de antihipertensivos, diuréticos",
                    "Deshidratación",
                    "Neuropatía autonómica (DM, Parkinson)",
                    "Ancianos",
                ],
                against_features=[
                    "Síncope en decúbito",
                    "Síncope durante ejercicio",
                    "Pródromos vasovagales típicos",
                ],
                tests=[
                    DiagnosticTest(
                        "PA decúbito y bipedestación",
                        "Funcional",
                        "Hipotensión ortostática",
                        "Caída PAS >20 o PAD >10 en 3 min",
                        1,
                    ),
                    DiagnosticTest(
                        "Hemograma, glucosa, creatinina",
                        "Laboratorio",
                        "Causas secundarias",
                        "Anemia, deshidratación",
                        1,
                    ),
                ],
                urgency=Urgency.SEMI_URGENT,
                red_flags=["Caídas frecuentes con trauma", "Anemia severa"],
            ),
            DifferentialDiagnosis(
                icd10_code="G40.9",
                name="Crisis Epiléptica (diagnóstico diferencial)",
                probability="Moderada si: movimientos tónico-clónicos + confusión postcrítica + mordedura lengua",
                key_features=[
                    "Movimientos tónico-clónicos durante pérdida de conciencia",
                    "Duración >30 segundos",
                    "Confusión postcrítica prolongada",
                    "Mordedura de lengua lateral",
                    "Incontinencia urinaria",
                    "Período postictal con cefalea, mialgias",
                ],
                against_features=[
                    "Recuperación rápida completa",
                    "Pródromos vasovagales",
                    "Sin movimientos o mioclonías breves",
                ],
                tests=[
                    DiagnosticTest(
                        "EEG",
                        "Funcional",
                        "Actividad epileptiforme",
                        "Descargas epileptiformes",
                        1,
                    ),
                    DiagnosticTest(
                        "RM cerebral",
                        "Imagen",
                        "Lesión epileptógena",
                        "Normal o lesión estructural",
                        1,
                    ),
                    DiagnosticTest(
                        "Prolactina postcrítica",
                        "Laboratorio",
                        "Diferencial con pseudocrisis",
                        "Elevada 2x basal a 20 min",
                        2,
                    ),
                ],
                urgency=Urgency.URGENT,
                red_flags=[
                    "Status epilepticus",
                    "Primera crisis",
                    "Déficit neurológico focal",
                ],
            ),
        ],
    },
    # =========================================================================
    # PALPITACIONES
    # =========================================================================
    "palpitaciones": {
        "category": "Cardiovascular",
        "key_questions": [
            "¿Regulares o irregulares?",
            "¿Inicio y fin súbito o gradual?",
            "¿Síntomas asociados? (síncope, disnea, dolor torácico)",
            "¿Desencadenantes? (café, ejercicio, estrés)",
            "¿Antecedentes cardíacos?",
        ],
        "differentials": [
            DifferentialDiagnosis(
                icd10_code="R00.2",
                name="Palpitaciones por Ansiedad / Extrasístoles",
                probability="Alta si: palpitaciones irregulares + ansiedad + sin síntomas de alarma",
                key_features=[
                    "Sensación de latido extra o pausa",
                    "Irregulares, esporádicas",
                    "Asociadas a estrés o ansiedad",
                    "Sin síncope ni disnea severa",
                    "ECG normal o extrasístoles aisladas",
                    "Mejoría con relajación",
                ],
                against_features=[
                    "Palpitaciones regulares rápidas sostenidas",
                    "Síncope asociado",
                    "Cardiopatía estructural",
                ],
                tests=[
                    DiagnosticTest(
                        "ECG 12 derivaciones",
                        "Funcional",
                        "Descartar arritmia",
                        "Normal o EV aisladas",
                        1,
                    ),
                    DiagnosticTest(
                        "TSH", "Laboratorio", "Descartar hipertiroidismo", "Normal", 1
                    ),
                    DiagnosticTest(
                        "Holter (si frecuentes)",
                        "Funcional",
                        "Correlación síntoma-ritmo",
                        "Extrasístoles benignas",
                        2,
                    ),
                ],
                urgency=Urgency.ELECTIVE,
                red_flags=[
                    "Síncope",
                    "Disnea severa",
                    "Dolor torácico",
                    "Cardiopatía conocida",
                ],
            ),
            DifferentialDiagnosis(
                icd10_code="I48.9",
                name="Fibrilación Auricular",
                probability="Alta si: palpitaciones irregulares sostenidas + pulso arrítmico + ECG diagnóstico",
                key_features=[
                    "Palpitaciones irregulares",
                    "Pulso arrítmico, déficit de pulso",
                    "Disnea de esfuerzo",
                    "Fatiga",
                    "Factores de riesgo: HTA, edad >65, valvulopatía",
                    "ECG: ausencia onda P, RR irregular",
                ],
                against_features=[
                    "Palpitaciones regulares",
                    "ECG con ritmo sinusal",
                    "Joven sin factores de riesgo",
                ],
                tests=[
                    DiagnosticTest(
                        "ECG 12 derivaciones",
                        "Funcional",
                        "Confirmar FA",
                        "Ausencia ondas P, RR irregular",
                        1,
                    ),
                    DiagnosticTest(
                        "Ecocardiograma",
                        "Imagen",
                        "Cardiopatía estructural",
                        "Tamaño AI, función VI, valvulopatía",
                        1,
                    ),
                    DiagnosticTest(
                        "TSH",
                        "Laboratorio",
                        "Descartar hipertiroidismo",
                        "Normal o bajo (FA tirotóxica)",
                        1,
                    ),
                    DiagnosticTest(
                        "CHA2DS2-VASc score",
                        "Clínico",
                        "Riesgo tromboembólico",
                        "≥2 indica anticoagulación",
                        1,
                    ),
                ],
                urgency=Urgency.URGENT,
                red_flags=[
                    "FA con respuesta ventricular rápida >150",
                    "Inestabilidad hemodinámica",
                    "ACV/AIT",
                ],
            ),
            DifferentialDiagnosis(
                icd10_code="I47.1",
                name="Taquicardia Supraventricular Paroxística",
                probability="Alta si: palpitaciones regulares rápidas + inicio/fin súbito + joven sano",
                key_features=[
                    "Palpitaciones regulares, muy rápidas (150-250 lpm)",
                    "Inicio y terminación súbitos",
                    "Duración minutos a horas",
                    "Puede terminar con maniobras vagales",
                    "Generalmente corazón estructuralmente normal",
                    "Más frecuente en mujeres jóvenes",
                ],
                against_features=[
                    "Palpitaciones irregulares",
                    "Cardiopatía estructural severa",
                    "Inicio gradual",
                ],
                tests=[
                    DiagnosticTest(
                        "ECG durante episodio",
                        "Funcional",
                        "Documentar arritmia",
                        "Taquicardia regular QRS angosto 150-250 lpm",
                        1,
                    ),
                    DiagnosticTest(
                        "ECG basal",
                        "Funcional",
                        "Preexcitación",
                        "WPW: PR corto, onda delta",
                        1,
                    ),
                    DiagnosticTest(
                        "Estudio electrofisiológico",
                        "Procedimiento",
                        "Diagnóstico y ablación",
                        "Vía accesoria o doble conducción nodal",
                        2,
                    ),
                ],
                urgency=Urgency.URGENT,
                red_flags=[
                    "Inestabilidad hemodinámica",
                    "Preexcitación + FA",
                    "Síncope",
                ],
            ),
            DifferentialDiagnosis(
                icd10_code="E05.9",
                name="Hipertiroidismo",
                probability="Alta si: palpitaciones + pérdida peso + temblor + intolerancia calor",
                key_features=[
                    "Palpitaciones frecuentes",
                    "Pérdida de peso con buen apetito",
                    "Temblor fino",
                    "Intolerancia al calor, sudoración",
                    "Ansiedad, irritabilidad",
                    "Bocio, exoftalmos (Graves)",
                ],
                against_features=[
                    "Ganancia de peso",
                    "Intolerancia al frío",
                    "TSH normal",
                ],
                tests=[
                    DiagnosticTest(
                        "TSH, T4 libre",
                        "Laboratorio",
                        "Confirmar hipertiroidismo",
                        "TSH suprimida, T4L elevada",
                        1,
                    ),
                    DiagnosticTest(
                        "Anticuerpos tiroideos",
                        "Laboratorio",
                        "Etiología autoinmune",
                        "Anti-TSI positivo (Graves)",
                        1,
                    ),
                    DiagnosticTest(
                        "Gammagrafía tiroidea",
                        "Imagen",
                        "Diferenciar causas",
                        "Captación difusa vs nodular vs baja",
                        2,
                    ),
                ],
                urgency=Urgency.SEMI_URGENT,
                red_flags=[
                    "Tormenta tiroidea",
                    "FA descompensada",
                    "Insuficiencia cardíaca",
                ],
            ),
        ],
    },
    # =========================================================================
    # EDEMA DE MIEMBROS INFERIORES
    # =========================================================================
    "edema": {
        "category": "Cardiovascular/Renal/Hepático",
        "key_questions": [
            "¿Unilateral o bilateral?",
            "¿Doloroso?",
            "¿Síntomas asociados? (disnea, ortopnea)",
            "¿Medicamentos? (calcioantagonistas, AINEs)",
            "¿Antecedentes? (ICC, cirrosis, ERC)",
        ],
        "differentials": [
            DifferentialDiagnosis(
                icd10_code="I50.9",
                name="Insuficiencia Cardíaca",
                probability="Alta si: edema bilateral + disnea + ortopnea + ingurgitación yugular",
                key_features=[
                    "Edema bilateral, simétrico",
                    "Disnea de esfuerzo, ortopnea, DPN",
                    "Ingurgitación yugular",
                    "Crepitantes pulmonares",
                    "Cardiomegalia",
                    "Antecedente cardíaco",
                ],
                against_features=["Edema unilateral", "Sin disnea", "Corazón normal"],
                tests=[
                    DiagnosticTest(
                        "BNP/NT-proBNP",
                        "Laboratorio",
                        "Estrés miocárdico",
                        "Elevado >400 pg/mL",
                        1,
                    ),
                    DiagnosticTest(
                        "Ecocardiograma",
                        "Imagen",
                        "Función cardíaca",
                        "FE reducida, disfunción diastólica",
                        1,
                    ),
                    DiagnosticTest(
                        "Rx tórax",
                        "Imagen",
                        "Congestión",
                        "Cardiomegalia, edema pulmonar",
                        1,
                    ),
                ],
                urgency=Urgency.URGENT,
                red_flags=["Disnea en reposo", "Hipoxemia", "Hipotensión"],
            ),
            DifferentialDiagnosis(
                icd10_code="I80.2",
                name="Trombosis Venosa Profunda (TVP)",
                probability="Alta si: edema unilateral + dolor + asimetría >3cm + factores riesgo TEV",
                key_features=[
                    "Edema UNILATERAL",
                    "Dolor a la palpación de pantorrilla",
                    "Diferencia de perímetro >3 cm",
                    "Eritema, calor local",
                    "Signo de Homans (poco sensible)",
                    "Factores de riesgo: inmovilización, cirugía, cáncer, ACO",
                ],
                against_features=[
                    "Edema bilateral simétrico",
                    "Disnea con ortopnea",
                    "Sin factores de riesgo TEV",
                ],
                tests=[
                    DiagnosticTest(
                        "Dímero-D",
                        "Laboratorio",
                        "Activación coagulación",
                        "<500 ng/mL descarta (baja probabilidad)",
                        1,
                    ),
                    DiagnosticTest(
                        "Ecografía Doppler venoso",
                        "Imagen",
                        "Trombo venoso",
                        "Vena no compresible, trombo visible",
                        1,
                    ),
                    DiagnosticTest(
                        "Wells score TVP",
                        "Clínico",
                        "Estratificación riesgo",
                        "Score >2: alta probabilidad",
                        1,
                    ),
                ],
                urgency=Urgency.EMERGENT,
                red_flags=[
                    "Disnea asociada (TEP)",
                    "Edema masivo (phlegmasia)",
                    "Cianosis",
                ],
            ),
            DifferentialDiagnosis(
                icd10_code="N18.9",
                name="Síndrome Nefrótico / ERC",
                probability="Alta si: edema + proteinuria masiva + hipoalbuminemia",
                key_features=[
                    "Edema blando, facial matutino, MMII vespertino",
                    "Proteinuria >3.5 g/día",
                    "Hipoalbuminemia <3 g/dL",
                    "Hiperlipidemia",
                    "Orina espumosa",
                    "HTA asociada frecuente",
                ],
                against_features=[
                    "Edema unilateral",
                    "Proteinuria mínima",
                    "Albúmina normal",
                ],
                tests=[
                    DiagnosticTest(
                        "Uroanálisis + proteinuria 24h",
                        "Laboratorio",
                        "Proteinuria",
                        ">3.5 g/24h",
                        1,
                    ),
                    DiagnosticTest(
                        "Albúmina sérica",
                        "Laboratorio",
                        "Hipoalbuminemia",
                        "<3 g/dL",
                        1,
                    ),
                    DiagnosticTest(
                        "Creatinina, BUN",
                        "Laboratorio",
                        "Función renal",
                        "Elevados en ERC",
                        1,
                    ),
                    DiagnosticTest(
                        "Biopsia renal (según caso)",
                        "Procedimiento",
                        "Etiología",
                        "Glomerulopatía específica",
                        2,
                    ),
                ],
                urgency=Urgency.URGENT,
                red_flags=["Anasarca", "Trombosis", "IRA"],
            ),
            DifferentialDiagnosis(
                icd10_code="K74.6",
                name="Cirrosis Hepática",
                probability="Alta si: edema + ascitis + estigmas hepáticos + hepatopatía conocida",
                key_features=[
                    "Edema MMII con ascitis",
                    "Estigmas hepáticos (arañas vasculares, eritema palmar)",
                    "Ictericia",
                    "Esplenomegalia",
                    "Antecedente de hepatopatía, alcohol",
                    "Hipoalbuminemia",
                ],
                against_features=[
                    "Sin ascitis",
                    "Función hepática normal",
                    "Sin estigmas hepáticos",
                ],
                tests=[
                    DiagnosticTest(
                        "Perfil hepático + albúmina",
                        "Laboratorio",
                        "Función hepática",
                        "Bilirrubina elevada, albúmina baja, INR prolongado",
                        1,
                    ),
                    DiagnosticTest(
                        "Ecografía abdominal",
                        "Imagen",
                        "Hepatopatía crónica",
                        "Hígado nodular, ascitis, esplenomegalia",
                        1,
                    ),
                    DiagnosticTest(
                        "Child-Pugh score", "Clínico", "Severidad", "A, B o C", 1
                    ),
                ],
                urgency=Urgency.URGENT,
                red_flags=["Encefalopatía hepática", "Hemorragia variceal", "PBE"],
            ),
        ],
    },
    # =========================================================================
    # DISURIA
    # =========================================================================
    "disuria": {
        "category": "Urología/Ginecología",
        "key_questions": [
            "¿Polaquiuria, urgencia?",
            "¿Dolor suprapúbico o lumbar?",
            "¿Fiebre?",
            "¿Secreción uretral o vaginal?",
            "¿Conductas de riesgo sexual?",
        ],
        "differentials": [
            DifferentialDiagnosis(
                icd10_code="N30.0",
                name="Cistitis Aguda",
                probability="Alta si: disuria + polaquiuria + urgencia + sin fiebre",
                key_features=[
                    "Disuria (dolor al orinar)",
                    "Polaquiuria, urgencia miccional",
                    "Dolor suprapúbico",
                    "Orina turbia o maloliente",
                    "Sin fiebre ni dolor lumbar",
                ],
                against_features=[
                    "Fiebre alta",
                    "Dolor lumbar (pielonefritis)",
                    "Secreción uretral",
                ],
                tests=[
                    DiagnosticTest(
                        "Uroanálisis con tira reactiva",
                        "Laboratorio",
                        "ITU",
                        "Leucocitos +, nitritos +",
                        1,
                    ),
                    DiagnosticTest(
                        "Urocultivo (si complicada)",
                        "Laboratorio",
                        "Identificación patógeno",
                        ">100,000 UFC/mL E. coli típico",
                        2,
                    ),
                ],
                urgency=Urgency.SEMI_URGENT,
                red_flags=["Fiebre", "Dolor lumbar", "ITU recurrente", "Embarazo"],
            ),
            DifferentialDiagnosis(
                icd10_code="N10",
                name="Pielonefritis Aguda",
                probability="Alta si: disuria + fiebre alta + dolor lumbar + escalofríos",
                key_features=[
                    "Fiebre alta con escalofríos",
                    "Dolor lumbar unilateral",
                    "Puñopercusión lumbar positiva",
                    "Síntomas urinarios bajos",
                    "Náuseas, vómitos",
                    "Leucocitosis",
                ],
                against_features=[
                    "Sin fiebre",
                    "Solo síntomas urinarios bajos",
                    "Dolor suprapúbico aislado",
                ],
                tests=[
                    DiagnosticTest(
                        "Uroanálisis y urocultivo",
                        "Laboratorio",
                        "ITU alta",
                        "Piuria, bacteriuria significativa",
                        1,
                    ),
                    DiagnosticTest(
                        "Hemograma, PCR",
                        "Laboratorio",
                        "Infección sistémica",
                        "Leucocitosis, PCR elevada",
                        1,
                    ),
                    DiagnosticTest(
                        "Ecografía renal",
                        "Imagen",
                        "Complicaciones",
                        "Absceso, obstrucción",
                        2,
                    ),
                ],
                urgency=Urgency.EMERGENT,
                red_flags=[
                    "Sepsis",
                    "Obstrucción urinaria",
                    "Absceso renal",
                    "Embarazo",
                ],
            ),
            DifferentialDiagnosis(
                icd10_code="A56.0",
                name="Uretritis / ITS",
                probability="Alta si: disuria + secreción uretral + conducta de riesgo sexual",
                key_features=[
                    "Disuria con secreción uretral",
                    "Secreción purulenta o mucoide",
                    "Sin polaquiuria marcada",
                    "Contacto sexual de riesgo",
                    "Pareja con síntomas",
                    "Hombres: secreción matutina",
                ],
                against_features=[
                    "Sin secreción",
                    "Polaquiuria marcada",
                    "Fiebre alta",
                ],
                tests=[
                    DiagnosticTest(
                        "PCR para Chlamydia/Gonorrea",
                        "Laboratorio",
                        "Identificar patógeno",
                        "Positivo",
                        1,
                    ),
                    DiagnosticTest(
                        "Gram de secreción",
                        "Laboratorio",
                        "Diplococos gram negativos",
                        "Gonococo",
                        1,
                    ),
                    DiagnosticTest(
                        "Serología VIH, sífilis, hepatitis",
                        "Laboratorio",
                        "Otras ITS",
                        "Screening completo",
                        1,
                    ),
                ],
                urgency=Urgency.URGENT,
                red_flags=["Epididimitis", "EPI (mujeres)", "Diseminación gonocócica"],
            ),
            DifferentialDiagnosis(
                icd10_code="N76.0",
                name="Vaginitis / Vulvovaginitis",
                probability="Alta si: disuria externa + flujo vaginal + prurito + sin polaquiuria",
                key_features=[
                    "Disuria 'externa' (ardor al contacto orina-vulva)",
                    "Flujo vaginal anormal",
                    "Prurito vulvar",
                    "Dispareunia",
                    "Sin polaquiuria ni urgencia marcadas",
                ],
                against_features=["Polaquiuria marcada", "Sin flujo vaginal", "Fiebre"],
                tests=[
                    DiagnosticTest(
                        "Examen en fresco flujo vaginal",
                        "Laboratorio",
                        "Identificar patógeno",
                        "Trichomona, levaduras, células clave",
                        1,
                    ),
                    DiagnosticTest(
                        "pH vaginal",
                        "Clínico",
                        "Orientar etiología",
                        ">4.5 sugestivo VB/Trichomona",
                        1,
                    ),
                    DiagnosticTest(
                        "Cultivo vaginal",
                        "Laboratorio",
                        "Candida recurrente",
                        "Especie de Candida",
                        2,
                    ),
                ],
                urgency=Urgency.ELECTIVE,
                red_flags=["Dolor pélvico (EPI)", "Fiebre", "Embarazo"],
            ),
        ],
    },
    # =========================================================================
    # ARTRALGIA / DOLOR ARTICULAR
    # =========================================================================
    "artralgia": {
        "category": "Reumatología/Musculoesquelético",
        "key_questions": [
            "¿Monoarticular o poliarticular?",
            "¿Aguda o crónica?",
            "¿Inflamatoria (rigidez matutina) o mecánica?",
            "¿Fiebre?",
            "¿Antecedentes? (gota, AR, psoriasis)",
        ],
        "differentials": [
            DifferentialDiagnosis(
                icd10_code="M10.9",
                name="Gota / Artritis Gotosa",
                probability="Alta si: monoartritis aguda + 1ª MTF + hiperuricemia + cristales",
                key_features=[
                    "Monoartritis aguda, muy dolorosa",
                    "Primera metatarsofalángica (podagra)",
                    "Eritema, calor, tumefacción intensa",
                    "Resolución en días-semanas",
                    "Hiperuricemia",
                    "Antecedente de episodios similares",
                ],
                against_features=[
                    "Poliartritis simétrica",
                    "Rigidez matutina prolongada",
                    "Afectación de pequeñas articulaciones manos",
                ],
                tests=[
                    DiagnosticTest(
                        "Artrocentesis con análisis líquido",
                        "Procedimiento",
                        "Cristales de UMS",
                        "Cristales en aguja, birrefringencia negativa",
                        1,
                    ),
                    DiagnosticTest(
                        "Ácido úrico sérico",
                        "Laboratorio",
                        "Hiperuricemia",
                        ">7 mg/dL (puede ser normal en crisis)",
                        1,
                    ),
                    DiagnosticTest(
                        "Rx articulación",
                        "Imagen",
                        "Cambios crónicos",
                        "Erosiones en sacabocado, tofos",
                        2,
                    ),
                ],
                urgency=Urgency.URGENT,
                red_flags=[
                    "Fiebre alta (descartar séptica)",
                    "Poliarticular con fiebre",
                ],
            ),
            DifferentialDiagnosis(
                icd10_code="M00.9",
                name="Artritis Séptica",
                probability="Alta si: monoartritis aguda + fiebre + factores riesgo",
                key_features=[
                    "Monoartritis aguda",
                    "Fiebre, escalofríos",
                    "Articulación caliente, muy dolorosa",
                    "Limitación severa de movilidad",
                    "Factores riesgo: DM, AR, prótesis, IVDU",
                    "Puerta de entrada (infección cutánea)",
                ],
                against_features=[
                    "Sin fiebre",
                    "Poliarticular simétrica",
                    "Rigidez matutina sin inflamación aguda",
                ],
                tests=[
                    DiagnosticTest(
                        "Artrocentesis URGENTE",
                        "Procedimiento",
                        "Líquido purulento",
                        ">50,000 leucos/mm³, cultivo positivo",
                        1,
                    ),
                    DiagnosticTest(
                        "Hemocultivos",
                        "Laboratorio",
                        "Bacteriemia",
                        "S. aureus más frecuente",
                        1,
                    ),
                    DiagnosticTest(
                        "PCR, VSG",
                        "Laboratorio",
                        "Inflamación sistémica",
                        "Muy elevadas",
                        1,
                    ),
                ],
                urgency=Urgency.EMERGENT,
                red_flags=["EMERGENCIA ORTOPÉDICA", "Sepsis", "Prótesis articular"],
            ),
            DifferentialDiagnosis(
                icd10_code="M06.9",
                name="Artritis Reumatoide",
                probability="Alta si: poliartritis simétrica + rigidez matutina >1h + pequeñas articulaciones",
                key_features=[
                    "Poliartritis simétrica",
                    "Pequeñas articulaciones (MCF, IFP, muñecas)",
                    "Rigidez matutina >1 hora",
                    "Evolución crónica (>6 semanas)",
                    "Factor reumatoide y/o anti-CCP positivos",
                    "Nódulos reumatoides",
                ],
                against_features=[
                    "Monoartritis aguda",
                    "Afectación IFD (pensar psoriásica)",
                    "Sin rigidez matutina",
                ],
                tests=[
                    DiagnosticTest(
                        "Factor reumatoide, Anti-CCP",
                        "Laboratorio",
                        "Autoanticuerpos",
                        "FR +, anti-CCP + (más específico)",
                        1,
                    ),
                    DiagnosticTest(
                        "VSG, PCR",
                        "Laboratorio",
                        "Actividad inflamatoria",
                        "Elevadas",
                        1,
                    ),
                    DiagnosticTest(
                        "Rx manos y pies",
                        "Imagen",
                        "Erosiones",
                        "Osteopenia periarticular, erosiones",
                        1,
                    ),
                    DiagnosticTest(
                        "Ecografía articular",
                        "Imagen",
                        "Sinovitis",
                        "Sinovitis, tenosinovitis, erosiones tempranas",
                        2,
                    ),
                ],
                urgency=Urgency.SEMI_URGENT,
                red_flags=[
                    "Vasculitis reumatoide",
                    "Afectación pulmonar",
                    "Síndrome de Felty",
                ],
            ),
            DifferentialDiagnosis(
                icd10_code="M15.9",
                name="Osteoartritis / Artrosis",
                probability="Alta si: dolor mecánico + rigidez breve + articulaciones de carga + edad >50",
                key_features=[
                    "Dolor que empeora con actividad",
                    "Rigidez breve (<30 min)",
                    "Articulaciones de carga (rodillas, caderas)",
                    "IFD (nódulos de Heberden)",
                    "Crepitación articular",
                    "Edad >50 años, sobrepeso",
                ],
                against_features=[
                    "Rigidez matutina prolongada",
                    "Inflamación articular marcada",
                    "Elevación de reactantes de fase aguda",
                ],
                tests=[
                    DiagnosticTest(
                        "Rx articulación afectada",
                        "Imagen",
                        "Cambios degenerativos",
                        "Pinzamiento, osteofitos, esclerosis",
                        1,
                    ),
                    DiagnosticTest(
                        "VSG, PCR (normales)",
                        "Laboratorio",
                        "Descartar inflamatorio",
                        "Normales",
                        1,
                    ),
                ],
                urgency=Urgency.ELECTIVE,
                red_flags=[
                    "Derrame articular agudo",
                    "Dolor nocturno severo",
                    "Pérdida de peso",
                ],
            ),
        ],
    },
    # =========================================================================
    # ODINOFAGIA / DOLOR DE GARGANTA
    # =========================================================================
    "odinofagia": {
        "category": "ORL/Infeccioso",
        "key_questions": [
            "¿Fiebre asociada?",
            "¿Exudado amigdalar?",
            "¿Adenopatías cervicales?",
            "¿Dificultad para tragar/respirar?",
            "¿Vacunación?",
        ],
        "differentials": [
            DifferentialDiagnosis(
                icd10_code="J02.9",
                name="Faringitis Viral",
                probability="Alta si: odinofagia + síntomas catarrales + sin exudado",
                key_features=[
                    "Odinofagia leve-moderada",
                    "Rinorrea, congestión nasal",
                    "Tos",
                    "Febrícula o afebril",
                    "Faringe eritematosa sin exudado",
                    "Duración 3-5 días autolimitada",
                ],
                against_features=[
                    "Exudado amigdalar",
                    "Fiebre alta sin síntomas catarrales",
                    "Adenopatías cervicales dolorosas",
                ],
                tests=[
                    DiagnosticTest(
                        "Ninguno",
                        "Clínico",
                        "Diagnóstico clínico",
                        "Cuadro viral típico",
                        1,
                    )
                ],
                urgency=Urgency.ELECTIVE,
                red_flags=["Dificultad respiratoria", "Estridor", "Babeo"],
            ),
            DifferentialDiagnosis(
                icd10_code="J03.0",
                name="Faringoamigdalitis Estreptocócica",
                probability="Alta si: fiebre + exudado amigdalar + adenopatías + SIN tos (Centor 3-4)",
                key_features=[
                    "Odinofagia intensa, inicio súbito",
                    "Fiebre >38.5°C",
                    "Exudado amigdalar",
                    "Adenopatías cervicales anteriores dolorosas",
                    "AUSENCIA de tos (importante)",
                    "Petequias en paladar",
                ],
                against_features=[
                    "Tos, rinorrea (sugiere viral)",
                    "Sin fiebre",
                    "Sin adenopatías",
                ],
                tests=[
                    DiagnosticTest(
                        "Test rápido estreptococo (Strep A)",
                        "Laboratorio",
                        "Detección antígeno",
                        "Positivo",
                        1,
                    ),
                    DiagnosticTest(
                        "Cultivo faríngeo (si test rápido negativo)",
                        "Laboratorio",
                        "Confirmar GAS",
                        "Streptococcus pyogenes",
                        2,
                    ),
                    DiagnosticTest(
                        "Centor/McIsaac score",
                        "Clínico",
                        "Estratificar riesgo",
                        "≥3 puntos: tratar o testear",
                        1,
                    ),
                ],
                urgency=Urgency.SEMI_URGENT,
                red_flags=[
                    "Trismus",
                    "Desviación úvula (absceso)",
                    "Compromiso respiratorio",
                ],
            ),
            DifferentialDiagnosis(
                icd10_code="J36",
                name="Absceso Periamigdalino",
                probability="Alta si: odinofagia severa unilateral + trismus + voz de papa caliente",
                key_features=[
                    "Odinofagia severa, unilateral",
                    "Trismus (dificultad para abrir boca)",
                    "Voz de 'papa caliente'",
                    "Desviación úvula al lado sano",
                    "Abombamiento periamigdalino",
                    "Fiebre alta, mal estado general",
                ],
                against_features=[
                    "Odinofagia bilateral simétrica",
                    "Sin trismus",
                    "Sin abombamiento",
                ],
                tests=[
                    DiagnosticTest(
                        "Examen ORL directo",
                        "Clínico",
                        "Abombamiento periamigdalino",
                        "Desviación úvula, asimetría",
                        1,
                    ),
                    DiagnosticTest(
                        "TC cuello con contraste",
                        "Imagen",
                        "Confirmar absceso",
                        "Colección con realce en anillo",
                        1,
                    ),
                    DiagnosticTest(
                        "Punción aspiración (diagnóstica/terapéutica)",
                        "Procedimiento",
                        "Drenaje",
                        "Pus",
                        1,
                    ),
                ],
                urgency=Urgency.EMERGENT,
                red_flags=[
                    "Compromiso vía aérea",
                    "Extensión a espacio parafaríngeo",
                    "Sepsis",
                ],
            ),
            DifferentialDiagnosis(
                icd10_code="B27.9",
                name="Mononucleosis Infecciosa",
                probability="Alta si: odinofagia + fatiga marcada + esplenomegalia + linfocitos atípicos",
                key_features=[
                    "Odinofagia intensa con exudado",
                    "Fiebre prolongada",
                    "Fatiga marcada, astenia",
                    "Adenopatías generalizadas",
                    "Esplenomegalia",
                    "Linfocitosis con atípicos",
                    "Adolescentes/jóvenes adultos",
                ],
                against_features=[
                    "Cuadro corto autolimitado",
                    "Sin adenopatías generalizadas",
                    "Sin fatiga marcada",
                ],
                tests=[
                    DiagnosticTest(
                        "Monotest (Paul-Bunnell)",
                        "Laboratorio",
                        "Anticuerpos heterófilos",
                        "Positivo",
                        1,
                    ),
                    DiagnosticTest(
                        "Hemograma con frotis",
                        "Laboratorio",
                        "Linfocitosis atípica",
                        ">10% linfocitos atípicos",
                        1,
                    ),
                    DiagnosticTest(
                        "Serología EBV (si monotest negativo)",
                        "Laboratorio",
                        "Confirmar EBV",
                        "IgM VCA positivo",
                        2,
                    ),
                    DiagnosticTest(
                        "Ecografía abdominal",
                        "Imagen",
                        "Esplenomegalia",
                        "Bazo aumentado",
                        2,
                    ),
                ],
                urgency=Urgency.SEMI_URGENT,
                red_flags=[
                    "Obstrucción vía aérea",
                    "Rotura esplénica",
                    "Hepatitis severa",
                ],
            ),
        ],
    },
    # =========================================================================
    # FATIGA / ASTENIA
    # =========================================================================
    "fatiga": {
        "category": "Medicina General/Sistémico",
        "key_questions": [
            "¿Duración?",
            "¿Pérdida de peso?",
            "¿Síntomas depresivos?",
            "¿Calidad del sueño?",
            "¿Medicamentos?",
        ],
        "differentials": [
            DifferentialDiagnosis(
                icd10_code="D50.9",
                name="Anemia",
                probability="Alta si: fatiga + palidez + disnea de esfuerzo + Hb baja",
                key_features=[
                    "Fatiga progresiva",
                    "Palidez cutáneo-mucosa",
                    "Disnea de esfuerzo",
                    "Taquicardia",
                    "Pica, coiloniquia (ferropénica)",
                    "Glositis (B12/folato)",
                ],
                against_features=[
                    "Hemograma normal",
                    "Sin palidez",
                    "Fatiga solo matutina",
                ],
                tests=[
                    DiagnosticTest(
                        "Hemograma completo",
                        "Laboratorio",
                        "Anemia",
                        "Hb baja, evaluar VCM",
                        1,
                    ),
                    DiagnosticTest(
                        "Ferritina, hierro, TIBC",
                        "Laboratorio",
                        "Ferropénica",
                        "Ferritina baja, hierro bajo, TIBC alta",
                        1,
                    ),
                    DiagnosticTest(
                        "B12, ácido fólico",
                        "Laboratorio",
                        "Megaloblástica",
                        "Niveles bajos",
                        1,
                    ),
                    DiagnosticTest(
                        "Reticulocitos",
                        "Laboratorio",
                        "Respuesta medular",
                        "Bajos en arregenerativa",
                        1,
                    ),
                ],
                urgency=Urgency.SEMI_URGENT,
                red_flags=["Hb <7 g/dL", "Síntomas de isquemia", "Sangrado activo"],
            ),
            DifferentialDiagnosis(
                icd10_code="E03.9",
                name="Hipotiroidismo",
                probability="Alta si: fatiga + intolerancia frío + ganancia peso + estreñimiento",
                key_features=[
                    "Fatiga, somnolencia",
                    "Intolerancia al frío",
                    "Ganancia de peso",
                    "Estreñimiento",
                    "Piel seca, cabello quebradizo",
                    "Bradicardia",
                    "Edema facial, mixedema",
                ],
                against_features=[
                    "Pérdida de peso",
                    "Intolerancia al calor",
                    "Taquicardia",
                ],
                tests=[
                    DiagnosticTest(
                        "TSH",
                        "Laboratorio",
                        "Hipotiroidismo primario",
                        "TSH elevada",
                        1,
                    ),
                    DiagnosticTest(
                        "T4 libre", "Laboratorio", "Confirmar", "T4L baja", 1
                    ),
                    DiagnosticTest(
                        "Anticuerpos antitiroideos",
                        "Laboratorio",
                        "Etiología autoinmune",
                        "Anti-TPO positivo (Hashimoto)",
                        2,
                    ),
                ],
                urgency=Urgency.SEMI_URGENT,
                red_flags=["Coma mixedematoso", "Bradicardia severa", "Hipotermia"],
            ),
            DifferentialDiagnosis(
                icd10_code="F32.9",
                name="Depresión Mayor",
                probability="Alta si: fatiga + ánimo deprimido + anhedonia + alt. sueño/apetito",
                key_features=[
                    "Fatiga persistente",
                    "Ánimo deprimido la mayor parte del día",
                    "Anhedonia (pérdida de interés)",
                    "Alteración del sueño (insomnio o hipersomnia)",
                    "Cambios en apetito/peso",
                    "Dificultad para concentrarse",
                    "Ideas de muerte o suicidio",
                ],
                against_features=[
                    "Causa orgánica clara",
                    "Fatiga solo física sin síntomas afectivos",
                    "Duración <2 semanas",
                ],
                tests=[
                    DiagnosticTest(
                        "PHQ-9",
                        "Clínico",
                        "Screening depresión",
                        "≥10 puntos: probable depresión",
                        1,
                    ),
                    DiagnosticTest(
                        "TSH (descartar hipotiroidismo)",
                        "Laboratorio",
                        "Causa orgánica",
                        "Normal",
                        1,
                    ),
                    DiagnosticTest(
                        "Hemograma, glucosa",
                        "Laboratorio",
                        "Descartar otras causas",
                        "Normales",
                        1,
                    ),
                ],
                urgency=Urgency.SEMI_URGENT,
                red_flags=[
                    "Ideación suicida activa",
                    "Síntomas psicóticos",
                    "Incapacidad funcional severa",
                ],
            ),
            DifferentialDiagnosis(
                icd10_code="E11.9",
                name="Diabetes Mellitus",
                probability="Alta si: fatiga + poliuria + polidipsia + pérdida peso + glucosa elevada",
                key_features=[
                    "Fatiga persistente",
                    "Poliuria, polidipsia",
                    "Pérdida de peso inexplicada",
                    "Visión borrosa",
                    "Infecciones recurrentes",
                    "Glucosa elevada",
                ],
                against_features=[
                    "Glucosa normal",
                    "Sin poliuria ni polidipsia",
                    "Ganancia de peso",
                ],
                tests=[
                    DiagnosticTest(
                        "Glucosa en ayunas", "Laboratorio", "Diabetes", "≥126 mg/dL", 1
                    ),
                    DiagnosticTest(
                        "HbA1c", "Laboratorio", "Control glucémico", "≥6.5%", 1
                    ),
                    DiagnosticTest(
                        "Glucosa 2h post-carga",
                        "Laboratorio",
                        "Intolerancia/diabetes",
                        "≥200 mg/dL",
                        2,
                    ),
                ],
                urgency=Urgency.SEMI_URGENT,
                red_flags=["CAD", "Estado hiperosmolar", "Hipoglucemia severa"],
            ),
        ],
    },
    # =========================================================================
    # EXANTEMA / RASH CUTÁNEO
    # =========================================================================
    "exantema": {
        "category": "Dermatología/Infeccioso",
        "key_questions": [
            "¿Distribución? (localizado vs generalizado)",
            "¿Prurito?",
            "¿Fiebre asociada?",
            "¿Medicamentos nuevos?",
            "¿Exposición a contactos enfermos?",
        ],
        "differentials": [
            DifferentialDiagnosis(
                icd10_code="L50.9",
                name="Urticaria",
                probability="Alta si: ronchas eritematosas + prurito intenso + evanescentes <24h",
                key_features=[
                    "Ronchas eritematosas, sobreelevadas",
                    "Prurito intenso",
                    "Lesiones evanescentes (<24 horas)",
                    "Distribución variable",
                    "Angioedema asociado (labios, párpados)",
                    "Desencadenante identificable (fármaco, alimento)",
                ],
                against_features=["Lesiones fijas >24h", "Púrpura", "Ampollas"],
                tests=[
                    DiagnosticTest(
                        "Clínico (historia + examen)",
                        "Clínico",
                        "Diagnóstico clínico",
                        "Lesiones típicas, evanescentes",
                        1,
                    ),
                    DiagnosticTest(
                        "IgE específica / prick test (si sospecha alergia)",
                        "Laboratorio",
                        "Identificar alergeno",
                        "Positivo para alergeno específico",
                        2,
                    ),
                ],
                urgency=Urgency.URGENT,
                red_flags=[
                    "Angioedema facial/laríngeo",
                    "Anafilaxia",
                    "Compromiso vía aérea",
                ],
            ),
            DifferentialDiagnosis(
                icd10_code="L27.0",
                name="Exantema Medicamentoso",
                probability="Alta si: rash morbiliforme + medicamento nuevo 7-14 días previos",
                key_features=[
                    "Exantema maculopapular (morbiliforme)",
                    "Inicio 7-14 días post-inicio fármaco",
                    "Prurito variable",
                    "Generalizado, simétrico",
                    "Fármacos frecuentes: ATB, AINEs, anticonvulsivantes",
                    "Sin compromiso mucoso",
                ],
                against_features=[
                    "Sin exposición a fármacos",
                    "Compromiso mucoso severo (pensar SJS/TEN)",
                ],
                tests=[
                    DiagnosticTest(
                        "Historia farmacológica detallada",
                        "Clínico",
                        "Cronología",
                        "Correlación temporal con fármaco",
                        1,
                    ),
                    DiagnosticTest(
                        "Hemograma, función hepática/renal",
                        "Laboratorio",
                        "DRESS (eosinofilia, hepatitis)",
                        "Descartar reacción severa",
                        1,
                    ),
                ],
                urgency=Urgency.URGENT,
                red_flags=[
                    "Compromiso mucoso (SJS)",
                    "Fiebre + eosinofilia (DRESS)",
                    "Ampollas extensas (TEN)",
                ],
            ),
            DifferentialDiagnosis(
                icd10_code="B09",
                name="Exantema Viral Inespecífico",
                probability="Alta si: rash + fiebre + síntomas prodrómicos + niños/jóvenes",
                key_features=[
                    "Exantema maculopapular difuso",
                    "Fiebre, malestar general",
                    "Síntomas respiratorios/GI prodrómicos",
                    "Adenopatías",
                    "Más común en niños",
                    "Autolimitado",
                ],
                against_features=[
                    "Sin fiebre ni pródromos",
                    "Lesiones fijas, no evanescentes",
                    "Adulto sin exposición viral",
                ],
                tests=[
                    DiagnosticTest(
                        "Clínico",
                        "Clínico",
                        "Diagnóstico clínico",
                        "Cuadro viral típico",
                        1,
                    ),
                    DiagnosticTest(
                        "Serologías virales (si necesario)",
                        "Laboratorio",
                        "Identificar virus",
                        "EBV, CMV, enterovirus, etc.",
                        2,
                    ),
                ],
                urgency=Urgency.ELECTIVE,
                red_flags=[
                    "Petequias (meningococcemia)",
                    "Púrpura palpable (vasculitis)",
                    "Compromiso sistémico",
                ],
            ),
            DifferentialDiagnosis(
                icd10_code="L30.9",
                name="Dermatitis / Eccema",
                probability="Alta si: placas eritematosas + descamación + prurito + localización típica",
                key_features=[
                    "Placas eritematosas con descamación",
                    "Prurito",
                    "Distribución típica (pliegues en atópica)",
                    "Curso crónico con exacerbaciones",
                    "Antecedente atópico personal/familiar",
                    "Xerosis cutánea",
                ],
                against_features=[
                    "Lesiones evanescentes",
                    "Fiebre alta",
                    "Sin prurito",
                ],
                tests=[
                    DiagnosticTest(
                        "Clínico",
                        "Clínico",
                        "Diagnóstico clínico",
                        "Morfología y distribución típica",
                        1,
                    ),
                    DiagnosticTest(
                        "Biopsia cutánea (casos atípicos)",
                        "Procedimiento",
                        "Histopatología",
                        "Espongiosis, infiltrado linfocítico",
                        2,
                    ),
                ],
                urgency=Urgency.ELECTIVE,
                red_flags=["Eritrodermia", "Sobreinfección", "Eccema herpético"],
            ),
        ],
    },
    # =========================================================================
    # ICTERICIA
    # =========================================================================
    "ictericia": {
        "category": "Gastroenterología/Hepático",
        "key_questions": [
            "¿Color de orina y heces?",
            "¿Dolor abdominal?",
            "¿Fiebre y escalofríos?",
            "¿Consumo de alcohol?",
            "¿Medicamentos o tóxicos?",
        ],
        "differentials": [
            DifferentialDiagnosis(
                icd10_code="K80.5",
                name="Coledocolitiasis / Obstrucción Biliar",
                probability="Alta si: ictericia + dolor cólico HD + coluria + acolia",
                key_features=[
                    "Ictericia obstructiva",
                    "Dolor cólico en hipocondrio derecho",
                    "Coluria (orina oscura)",
                    "Acolia (heces claras)",
                    "Antecedente de litiasis biliar",
                    "Prurito (colestasis)",
                    "Bilirrubina directa elevada",
                ],
                against_features=[
                    "Heces de color normal",
                    "Sin dolor abdominal",
                    "Predominio bilirrubina indirecta",
                ],
                tests=[
                    DiagnosticTest(
                        "Bilirrubinas total y fraccionada",
                        "Laboratorio",
                        "Patrón obstructivo",
                        "BD > BI",
                        1,
                    ),
                    DiagnosticTest(
                        "FA, GGT", "Laboratorio", "Colestasis", "Muy elevadas", 1
                    ),
                    DiagnosticTest(
                        "Ecografía abdominal",
                        "Imagen",
                        "Dilatación vía biliar, cálculos",
                        "Vía biliar dilatada, coledocolitiasis",
                        1,
                    ),
                    DiagnosticTest(
                        "ColangioRM / CPRE",
                        "Imagen/Procedimiento",
                        "Confirmar obstrucción",
                        "Cálculo en colédoco",
                        2,
                    ),
                ],
                urgency=Urgency.EMERGENT,
                red_flags=[
                    "Colangitis (Charcot: fiebre + ictericia + dolor)",
                    "Pancreatitis biliar",
                    "Sepsis",
                ],
            ),
            DifferentialDiagnosis(
                icd10_code="B15.9",
                name="Hepatitis Aguda",
                probability="Alta si: ictericia + transaminasas muy elevadas + síntomas prodrómicos",
                key_features=[
                    "Ictericia hepatocelular",
                    "Transaminasas muy elevadas (>10x)",
                    "Síntomas prodrómicos (astenia, náuseas)",
                    "Hepatomegalia dolorosa",
                    "Factores de riesgo (viajes, drogas IV, sexual)",
                    "Bilirrubina mixta",
                ],
                against_features=[
                    "Acolia completa",
                    "Vía biliar dilatada",
                    "Transaminasas normales",
                ],
                tests=[
                    DiagnosticTest(
                        "Transaminasas (ALT, AST)",
                        "Laboratorio",
                        "Daño hepatocelular",
                        "Muy elevadas (>1000 U/L)",
                        1,
                    ),
                    DiagnosticTest(
                        "Serologías hepatitis (HAV, HBV, HCV)",
                        "Laboratorio",
                        "Etiología viral",
                        "IgM anti-HAV, HBsAg, anti-HCV",
                        1,
                    ),
                    DiagnosticTest(
                        "INR, albúmina",
                        "Laboratorio",
                        "Función sintética",
                        "INR prolongado = mal pronóstico",
                        1,
                    ),
                    DiagnosticTest(
                        "Ecografía abdominal",
                        "Imagen",
                        "Descartar obstrucción",
                        "Vía biliar no dilatada",
                        1,
                    ),
                ],
                urgency=Urgency.EMERGENT,
                red_flags=[
                    "Encefalopatía (falla hepática fulminante)",
                    "INR >2",
                    "Hipoglucemia",
                ],
            ),
            DifferentialDiagnosis(
                icd10_code="D59.1",
                name="Hemólisis",
                probability="Alta si: ictericia + anemia + bilirrubina indirecta + reticulocitosis",
                key_features=[
                    "Ictericia con palidez (anemia)",
                    "Bilirrubina INDIRECTA predominante",
                    "Heces y orina de color normal",
                    "Reticulocitosis",
                    "LDH elevada, haptoglobina baja",
                    "Esplenomegalia",
                    "Sin prurito (no colestasis)",
                ],
                against_features=[
                    "Coluria y acolia",
                    "Bilirrubina directa elevada",
                    "Vía biliar dilatada",
                ],
                tests=[
                    DiagnosticTest(
                        "Bilirrubinas (indirecta elevada)",
                        "Laboratorio",
                        "Hemólisis",
                        "BI >> BD",
                        1,
                    ),
                    DiagnosticTest(
                        "Reticulocitos",
                        "Laboratorio",
                        "Respuesta medular",
                        "Elevados (>2%)",
                        1,
                    ),
                    DiagnosticTest(
                        "LDH, haptoglobina",
                        "Laboratorio",
                        "Marcadores hemólisis",
                        "LDH alta, haptoglobina baja/indetectable",
                        1,
                    ),
                    DiagnosticTest(
                        "Coombs directo",
                        "Laboratorio",
                        "Hemólisis autoinmune",
                        "Positivo en AHAI",
                        1,
                    ),
                    DiagnosticTest(
                        "Frotis de sangre periférica",
                        "Laboratorio",
                        "Morfología GR",
                        "Esferocitos, esquistocitos, etc.",
                        1,
                    ),
                ],
                urgency=Urgency.URGENT,
                red_flags=["Anemia severa", "Hemoglobinuria", "Insuficiencia renal"],
            ),
            DifferentialDiagnosis(
                icd10_code="K74.6",
                name="Cirrosis Descompensada",
                probability="Alta si: ictericia + ascitis + estigmas hepáticos + hepatopatía crónica",
                key_features=[
                    "Ictericia progresiva",
                    "Ascitis",
                    "Estigmas hepáticos crónicos",
                    "Encefalopatía hepática",
                    "Várices esofágicas",
                    "Hipoalbuminemia, coagulopatía",
                    "Antecedente de hepatopatía",
                ],
                against_features=[
                    "Hígado normal en imagen",
                    "Función hepática normal",
                    "Inicio agudo sin enfermedad previa",
                ],
                tests=[
                    DiagnosticTest(
                        "Perfil hepático completo",
                        "Laboratorio",
                        "Función hepática",
                        "Bilirrubina elevada, albúmina baja, INR prolongado",
                        1,
                    ),
                    DiagnosticTest(
                        "Ecografía con Doppler",
                        "Imagen",
                        "Cirrosis, hipertensión portal",
                        "Hígado nodular, esplenomegalia, ascitis",
                        1,
                    ),
                    DiagnosticTest(
                        "MELD score",
                        "Clínico",
                        "Pronóstico/trasplante",
                        "Score para lista de trasplante",
                        1,
                    ),
                ],
                urgency=Urgency.EMERGENT,
                red_flags=[
                    "Encefalopatía grado III-IV",
                    "Hemorragia variceal",
                    "Síndrome hepatorrenal",
                ],
            ),
        ],
    },
    # =========================================================================
    # HEMATURIA
    # =========================================================================
    "hematuria": {
        "category": "Urología/Nefrología",
        "key_questions": [
            "¿Macroscópica o microscópica?",
            "¿Dolor asociado?",
            "¿Coágulos?",
            "¿Edad y factores de riesgo (tabaco)?",
            "¿Síntomas urinarios asociados?",
        ],
        "differentials": [
            DifferentialDiagnosis(
                icd10_code="N20.0",
                name="Litiasis Urinaria",
                probability="Alta si: hematuria + dolor cólico intenso + antecedente litiásico",
                key_features=[
                    "Dolor cólico severo (flanco → ingle)",
                    "Hematuria (micro o macroscópica)",
                    "Náuseas, vómitos",
                    "Inquietud, posición antiálgica variable",
                    "Antecedente de cálculos",
                    "Cristaluria",
                ],
                against_features=[
                    "Sin dolor",
                    "Coágulos grandes",
                    "Síntomas sistémicos",
                ],
                tests=[
                    DiagnosticTest(
                        "Uroanálisis",
                        "Laboratorio",
                        "Hematuria, cristales",
                        "GR elevados, posibles cristales",
                        1,
                    ),
                    DiagnosticTest(
                        "TC abdomen sin contraste",
                        "Imagen",
                        "Localizar cálculo",
                        "Cálculo ureteral/renal",
                        1,
                    ),
                    DiagnosticTest(
                        "Creatinina",
                        "Laboratorio",
                        "Función renal",
                        "Descartar obstrucción bilateral/monorreno",
                        1,
                    ),
                ],
                urgency=Urgency.URGENT,
                red_flags=[
                    "Fiebre (litiasis infectada)",
                    "Anuria",
                    "Riñón único obstruido",
                ],
            ),
            DifferentialDiagnosis(
                icd10_code="C67.9",
                name="Cáncer de Vejiga",
                probability="Alta si: hematuria macroscópica indolora + >50 años + tabaquismo",
                key_features=[
                    "Hematuria macroscópica INDOLORA",
                    "Intermitente",
                    "Coágulos posibles",
                    "Edad >50 años",
                    "Tabaquismo (factor de riesgo principal)",
                    "Exposición ocupacional (colorantes, cauchos)",
                ],
                against_features=[
                    "Dolor cólico típico",
                    "Paciente joven sin factores de riesgo",
                    "Solo hematuria microscópica transitoria",
                ],
                tests=[
                    DiagnosticTest(
                        "Citología urinaria",
                        "Laboratorio",
                        "Células malignas",
                        "Atipias, células tumorales",
                        1,
                    ),
                    DiagnosticTest(
                        "Cistoscopia",
                        "Procedimiento",
                        "Visualización directa",
                        "Tumor vesical",
                        1,
                    ),
                    DiagnosticTest(
                        "TC urografía",
                        "Imagen",
                        "Masa vesical, tracto superior",
                        "Lesión en vejiga o urotelio",
                        1,
                    ),
                ],
                urgency=Urgency.URGENT,
                red_flags=[
                    "Hematuria persistente",
                    "Obstrucción urinaria",
                    "Masa palpable",
                ],
            ),
            DifferentialDiagnosis(
                icd10_code="N02.9",
                name="Glomerulonefritis",
                probability="Alta si: hematuria + proteinuria + cilindros hemáticos + edema/HTA",
                key_features=[
                    "Hematuria con GR dismórficos",
                    "Cilindros hemáticos",
                    "Proteinuria asociada",
                    "Edema, HTA",
                    "Orina color 'coca-cola'",
                    "Creatinina elevada",
                    "Posible infección reciente (post-estreptocócica)",
                ],
                against_features=[
                    "GR normales, sin dismorfismo",
                    "Sin proteinuria",
                    "Dolor cólico típico",
                ],
                tests=[
                    DiagnosticTest(
                        "Uroanálisis con sedimento",
                        "Laboratorio",
                        "GR dismórficos, cilindros",
                        "Hematuria glomerular",
                        1,
                    ),
                    DiagnosticTest(
                        "Proteinuria 24h / índice Prot/Creat",
                        "Laboratorio",
                        "Daño glomerular",
                        "Proteinuria significativa",
                        1,
                    ),
                    DiagnosticTest(
                        "Creatinina, BUN",
                        "Laboratorio",
                        "Función renal",
                        "IRA posible",
                        1,
                    ),
                    DiagnosticTest(
                        "Complemento (C3, C4)",
                        "Laboratorio",
                        "Etiología",
                        "Bajo en post-infecciosa, lúpica",
                        1,
                    ),
                    DiagnosticTest(
                        "Biopsia renal",
                        "Procedimiento",
                        "Diagnóstico definitivo",
                        "Patrón histológico específico",
                        2,
                    ),
                ],
                urgency=Urgency.URGENT,
                red_flags=[
                    "IRA rápidamente progresiva",
                    "Hemoptisis (Goodpasture)",
                    "Anasarca",
                ],
            ),
            DifferentialDiagnosis(
                icd10_code="N30.0",
                name="ITU / Cistitis Hemorrágica",
                probability="Alta si: hematuria + disuria + polaquiuria + piuria",
                key_features=[
                    "Hematuria con síntomas urinarios bajos",
                    "Disuria, polaquiuria, urgencia",
                    "Dolor suprapúbico",
                    "Piuria en uroanálisis",
                    "Sin fiebre (cistitis simple)",
                ],
                against_features=[
                    "Sin síntomas urinarios",
                    "Hematuria indolora aislada",
                    "GR dismórficos",
                ],
                tests=[
                    DiagnosticTest(
                        "Uroanálisis",
                        "Laboratorio",
                        "ITU",
                        "Leucocitos, nitritos, GR",
                        1,
                    ),
                    DiagnosticTest(
                        "Urocultivo",
                        "Laboratorio",
                        "Confirmar ITU",
                        ">100,000 UFC/mL",
                        1,
                    ),
                ],
                urgency=Urgency.SEMI_URGENT,
                red_flags=[
                    "Fiebre (pielonefritis)",
                    "Hematuria persistente post-tratamiento",
                ],
            ),
        ],
    },
    # =========================================================================
    # PÉRDIDA DE PESO INVOLUNTARIA
    # =========================================================================
    "perdida de peso": {
        "category": "Medicina General/Oncología",
        "key_questions": [
            "¿Cuánto peso en cuánto tiempo?",
            "¿Apetito conservado o disminuido?",
            "¿Síntomas asociados? (fiebre, sudoración nocturna)",
            "¿Síntomas GI? (disfagia, cambio hábito intestinal)",
            "¿Comorbilidades? (DM, hipertiroidismo)",
        ],
        "differentials": [
            DifferentialDiagnosis(
                icd10_code="C80.1",
                name="Neoplasia Oculta",
                probability="Alta si: pérdida peso >5% en 6m + edad avanzada + síntomas constitucionales",
                key_features=[
                    "Pérdida de peso involuntaria significativa (>5%)",
                    "Anorexia, astenia",
                    "Sudoración nocturna",
                    "Edad avanzada",
                    "Tabaquismo (pulmón)",
                    "Sin otra causa identificada",
                ],
                against_features=[
                    "Causa evidente (dieta, enfermedad conocida)",
                    "Ganancia de apetito",
                    "Joven sin factores de riesgo",
                ],
                tests=[
                    DiagnosticTest(
                        "Hemograma, VSG, PCR",
                        "Laboratorio",
                        "Inflamación/anemia",
                        "Anemia, VSG elevada",
                        1,
                    ),
                    DiagnosticTest(
                        "Perfil hepático, LDH",
                        "Laboratorio",
                        "Metástasis hepáticas",
                        "Alterados si infiltración",
                        1,
                    ),
                    DiagnosticTest(
                        "Rx o TC tórax", "Imagen", "Masa pulmonar", "Nódulo/masa", 1
                    ),
                    DiagnosticTest(
                        "TC abdomen-pelvis",
                        "Imagen",
                        "Masas abdominales",
                        "Masa, adenopatías",
                        1,
                    ),
                    DiagnosticTest(
                        "Marcadores tumorales según sospecha",
                        "Laboratorio",
                        "Orientar",
                        "CEA, CA 19-9, PSA, etc.",
                        2,
                    ),
                ],
                urgency=Urgency.URGENT,
                red_flags=["Masa palpable", "Adenopatías", "Sangrado GI"],
            ),
            DifferentialDiagnosis(
                icd10_code="E05.9",
                name="Hipertiroidismo",
                probability="Alta si: pérdida peso + apetito conservado/aumentado + taquicardia + temblor",
                key_features=[
                    "Pérdida de peso CON APETITO CONSERVADO",
                    "Taquicardia, palpitaciones",
                    "Temblor fino",
                    "Intolerancia al calor, sudoración",
                    "Nerviosismo, irritabilidad",
                    "Bocio, oftalmopatía (Graves)",
                ],
                against_features=["Anorexia", "Bradicardia", "Intolerancia al frío"],
                tests=[
                    DiagnosticTest(
                        "TSH",
                        "Laboratorio",
                        "Hipertiroidismo",
                        "TSH suprimida (<0.1)",
                        1,
                    ),
                    DiagnosticTest(
                        "T4L, T3L", "Laboratorio", "Confirmar", "Elevadas", 1
                    ),
                    DiagnosticTest(
                        "Anticuerpos tiroideos (TRAb)",
                        "Laboratorio",
                        "Etiología",
                        "TRAb + en Graves",
                        2,
                    ),
                ],
                urgency=Urgency.URGENT,
                red_flags=["Crisis tirotóxica", "FA rápida", "Insuficiencia cardíaca"],
            ),
            DifferentialDiagnosis(
                icd10_code="E11.9",
                name="Diabetes Mellitus Descompensada",
                probability="Alta si: pérdida peso + poliuria + polidipsia + glucosa muy elevada",
                key_features=[
                    "Pérdida de peso involuntaria",
                    "Poliuria, polidipsia",
                    "Polifagia paradójica",
                    "Glucosa muy elevada",
                    "Visión borrosa",
                    "Puede ser debut DM1 o DM2 descompensada",
                ],
                against_features=[
                    "Glucosa normal",
                    "Sin síntomas cardinales de DM",
                    "Hipoglucemia",
                ],
                tests=[
                    DiagnosticTest(
                        "Glucosa en ayunas",
                        "Laboratorio",
                        "Hiperglucemia",
                        "Muy elevada",
                        1,
                    ),
                    DiagnosticTest(
                        "HbA1c", "Laboratorio", "Control crónico", ">8-9%", 1
                    ),
                    DiagnosticTest(
                        "Cetonemia/cetonuria",
                        "Laboratorio",
                        "CAD",
                        "Cetonas positivas",
                        1,
                    ),
                ],
                urgency=Urgency.URGENT,
                red_flags=["CAD", "Estado hiperosmolar", "Deshidratación severa"],
            ),
            DifferentialDiagnosis(
                icd10_code="F50.0",
                name="Trastorno de Conducta Alimentaria",
                probability="Alta si: pérdida peso + restricción calórica intencional + imagen corporal distorsionada",
                key_features=[
                    "Pérdida de peso intencional excesiva",
                    "Restricción alimentaria severa",
                    "Miedo a ganar peso",
                    "Imagen corporal distorsionada",
                    "Adolescentes/adultos jóvenes",
                    "Amenorrea (mujeres)",
                    "Conductas compensatorias (purga)",
                ],
                against_features=[
                    "Apetito conservado sin restricción",
                    "Síntomas orgánicos claros",
                    "Edad avanzada",
                ],
                tests=[
                    DiagnosticTest(
                        "IMC, signos vitales",
                        "Clínico",
                        "Desnutrición",
                        "IMC <18.5, bradicardia, hipotensión",
                        1,
                    ),
                    DiagnosticTest(
                        "Electrolitos",
                        "Laboratorio",
                        "Alteraciones por purga",
                        "Hipopotasemia, hipocloremia",
                        1,
                    ),
                    DiagnosticTest(
                        "Evaluación psiquiátrica",
                        "Clínico",
                        "Confirmar diagnóstico",
                        "Criterios DSM-5",
                        1,
                    ),
                ],
                urgency=Urgency.URGENT,
                red_flags=[
                    "IMC <15",
                    "Bradicardia severa",
                    "Alteraciones electrolíticas graves",
                    "Ideación suicida",
                ],
            ),
        ],
    },
    # =========================================================================
    # CONSTIPACIÓN
    # =========================================================================
    "constipacion": {
        "category": "Gastroenterología",
        "key_questions": [
            "¿Duración? (aguda vs crónica)",
            "¿Signos de alarma? (sangre, pérdida peso)",
            "¿Medicamentos?",
            "¿Cambio reciente de hábito intestinal?",
            "¿Dieta y actividad física?",
        ],
        "differentials": [
            DifferentialDiagnosis(
                icd10_code="K59.0",
                name="Constipación Funcional / Crónica",
                probability="Alta si: constipación crónica + sin signos alarma + dieta pobre en fibra",
                key_features=[
                    "Constipación crónica (>3 meses)",
                    "Esfuerzo defecatorio",
                    "Heces duras o escasas",
                    "Sensación de evacuación incompleta",
                    "Dieta pobre en fibra",
                    "Sedentarismo",
                    "Sin pérdida de peso ni sangrado",
                ],
                against_features=[
                    "Inicio agudo reciente",
                    "Pérdida de peso",
                    "Sangrado rectal",
                    "Obstrucción",
                ],
                tests=[
                    DiagnosticTest(
                        "Historia dietética y de hábitos",
                        "Clínico",
                        "Identificar factores",
                        "Baja fibra, poco líquido",
                        1,
                    ),
                    DiagnosticTest(
                        "TSH (descartar hipotiroidismo)",
                        "Laboratorio",
                        "Causa secundaria",
                        "Normal",
                        1,
                    ),
                ],
                urgency=Urgency.ELECTIVE,
                red_flags=["Inicio >50 años", "Pérdida de peso", "Sangrado", "Anemia"],
            ),
            DifferentialDiagnosis(
                icd10_code="C18.9",
                name="Cáncer Colorrectal",
                probability="Alta si: cambio hábito intestinal + >50 años + sangrado + pérdida peso",
                key_features=[
                    "Cambio en hábito intestinal reciente",
                    "Constipación alternando con diarrea",
                    "Sangrado rectal u oculto",
                    "Pérdida de peso involuntaria",
                    "Anemia ferropénica inexplicada",
                    "Masa palpable o dolor abdominal",
                    "Antecedente familiar de CCR",
                ],
                against_features=[
                    "Constipación crónica estable desde juventud",
                    "Sin signos de alarma",
                    "Joven sin factores de riesgo",
                ],
                tests=[
                    DiagnosticTest(
                        "Colonoscopía",
                        "Procedimiento",
                        "Visualización directa",
                        "Masa, pólipo, estenosis",
                        1,
                    ),
                    DiagnosticTest(
                        "Hemograma (anemia)",
                        "Laboratorio",
                        "Anemia ferropénica",
                        "Hb baja, VCM bajo",
                        1,
                    ),
                    DiagnosticTest(
                        "CEA",
                        "Laboratorio",
                        "Seguimiento (no screening)",
                        "Puede estar elevado",
                        2,
                    ),
                    DiagnosticTest(
                        "TC abdomen-pelvis",
                        "Imagen",
                        "Estadificación",
                        "Masa, metástasis hepáticas",
                        2,
                    ),
                ],
                urgency=Urgency.URGENT,
                red_flags=["Obstrucción intestinal", "Sangrado masivo", "Perforación"],
            ),
            DifferentialDiagnosis(
                icd10_code="E03.9",
                name="Hipotiroidismo",
                probability="Alta si: constipación + fatiga + intolerancia frío + ganancia peso",
                key_features=[
                    "Constipación de inicio gradual",
                    "Fatiga, somnolencia",
                    "Intolerancia al frío",
                    "Piel seca, cabello quebradizo",
                    "Ganancia de peso",
                    "Bradicardia",
                    "Edema facial",
                ],
                against_features=["Hiperactividad", "Pérdida de peso", "Taquicardia"],
                tests=[
                    DiagnosticTest(
                        "TSH", "Laboratorio", "Hipotiroidismo", "TSH elevada", 1
                    ),
                    DiagnosticTest(
                        "T4 libre", "Laboratorio", "Confirmar", "T4L baja", 1
                    ),
                ],
                urgency=Urgency.SEMI_URGENT,
                red_flags=["Bradicardia severa", "Hipotermia", "Coma mixedematoso"],
            ),
            DifferentialDiagnosis(
                icd10_code="K56.6",
                name="Obstrucción Intestinal",
                probability="Alta si: constipación aguda + distensión + vómitos + ausencia de flatos",
                key_features=[
                    "Constipación AGUDA completa",
                    "Ausencia de flatos",
                    "Distensión abdominal progresiva",
                    "Vómitos (tardíos: fecaloideos)",
                    "Dolor abdominal cólico",
                    "Ruidos hidroaéreos aumentados → abolidos",
                    "Cirugía abdominal previa (adherencias)",
                ],
                against_features=[
                    "Constipación crónica estable",
                    "Eliminación de flatos",
                    "Sin distensión",
                ],
                tests=[
                    DiagnosticTest(
                        "Rx abdomen (de pie)",
                        "Imagen",
                        "Niveles hidroaéreos",
                        "Dilatación asas, niveles",
                        1,
                    ),
                    DiagnosticTest(
                        "TC abdomen",
                        "Imagen",
                        "Sitio y causa obstrucción",
                        "Punto de transición, causa",
                        1,
                    ),
                    DiagnosticTest(
                        "Electrolitos",
                        "Laboratorio",
                        "Deshidratación",
                        "Alteraciones hidroelectrolíticas",
                        1,
                    ),
                ],
                urgency=Urgency.EMERGENT,
                red_flags=[
                    "EMERGENCIA QUIRÚRGICA",
                    "Estrangulación",
                    "Peritonitis",
                    "Shock",
                ],
            ),
        ],
    },
    # =========================================================================
    # ANSIEDAD
    # =========================================================================
    "ansiedad": {
        "category": "Psiquiatría/Medicina General",
        "key_questions": [
            "¿Episodios de pánico?",
            "¿Ansiedad generalizada o situacional?",
            "¿Síntomas físicos asociados?",
            "¿Sustancias (cafeína, estimulantes)?",
            "¿Descartadas causas orgánicas?",
        ],
        "differentials": [
            DifferentialDiagnosis(
                icd10_code="F41.0",
                name="Trastorno de Pánico",
                probability="Alta si: ataques recurrentes + miedo a nuevos ataques + síntomas físicos intensos",
                key_features=[
                    "Ataques de pánico recurrentes e inesperados",
                    "Pico en minutos",
                    "Palpitaciones, sudoración, temblor",
                    "Sensación de ahogo o falta de aire",
                    "Dolor torácico",
                    "Miedo a morir o perder el control",
                    "Preocupación persistente por nuevos ataques",
                ],
                against_features=[
                    "Ansiedad solo situacional",
                    "Síntomas graduales (no en pico)",
                    "Causa orgánica identificada",
                ],
                tests=[
                    DiagnosticTest(
                        "Evaluación clínica (criterios DSM-5)",
                        "Clínico",
                        "Confirmar diagnóstico",
                        "Criterios de trastorno de pánico",
                        1,
                    ),
                    DiagnosticTest(
                        "TSH", "Laboratorio", "Descartar hipertiroidismo", "Normal", 1
                    ),
                    DiagnosticTest(
                        "ECG",
                        "Cardiología",
                        "Descartar arritmia",
                        "Normal o cambios inespecíficos",
                        1,
                    ),
                    DiagnosticTest(
                        "Glucosa", "Laboratorio", "Descartar hipoglucemia", "Normal", 1
                    ),
                ],
                urgency=Urgency.SEMI_URGENT,
                red_flags=[
                    "Ideación suicida",
                    "Abuso de sustancias comórbido",
                    "Agorafobia severa",
                ],
            ),
            DifferentialDiagnosis(
                icd10_code="F41.1",
                name="Trastorno de Ansiedad Generalizada (TAG)",
                probability="Alta si: preocupación excesiva >6 meses + tensión muscular + fatiga + insomnio",
                key_features=[
                    "Preocupación excesiva la mayoría de días",
                    "Duración >6 meses",
                    "Dificultad para controlar la preocupación",
                    "Tensión muscular",
                    "Fatiga",
                    "Dificultad para concentrarse",
                    "Insomnio o sueño no reparador",
                ],
                against_features=[
                    "Ataques de pánico discretos",
                    "Ansiedad solo en situaciones específicas",
                    "Síntomas <6 meses",
                ],
                tests=[
                    DiagnosticTest(
                        "GAD-7",
                        "Clínico",
                        "Screening ansiedad",
                        "≥10 puntos: ansiedad moderada-severa",
                        1,
                    ),
                    DiagnosticTest(
                        "TSH, glucosa, hemograma",
                        "Laboratorio",
                        "Descartar causas orgánicas",
                        "Normales",
                        1,
                    ),
                ],
                urgency=Urgency.SEMI_URGENT,
                red_flags=[
                    "Depresión comórbida",
                    "Ideación suicida",
                    "Abuso de benzodiacepinas",
                ],
            ),
            DifferentialDiagnosis(
                icd10_code="E05.9",
                name="Hipertiroidismo (manifestación ansiosa)",
                probability="Alta si: ansiedad + taquicardia + pérdida peso + intolerancia calor",
                key_features=[
                    "Ansiedad, nerviosismo",
                    "Taquicardia, palpitaciones",
                    "Pérdida de peso con apetito conservado",
                    "Temblor fino",
                    "Intolerancia al calor, sudoración",
                    "Bocio posible",
                ],
                against_features=[
                    "Síntomas solo emocionales sin físicos",
                    "Bradicardia",
                    "Ganancia de peso",
                ],
                tests=[
                    DiagnosticTest(
                        "TSH", "Laboratorio", "Hipertiroidismo", "TSH suprimida", 1
                    ),
                    DiagnosticTest(
                        "T4L, T3L", "Laboratorio", "Hormonas tiroideas", "Elevadas", 1
                    ),
                ],
                urgency=Urgency.URGENT,
                red_flags=["Crisis tirotóxica", "Arritmias", "Pérdida de peso marcada"],
            ),
            DifferentialDiagnosis(
                icd10_code="F10.2",
                name="Abstinencia de Sustancias",
                probability="Alta si: ansiedad aguda + suspensión reciente alcohol/benzodiacepinas/opioides",
                key_features=[
                    "Ansiedad severa de inicio agudo",
                    "Suspensión reciente de sustancia",
                    "Temblor, sudoración",
                    "Taquicardia, HTA",
                    "Insomnio severo",
                    "Alcohol: puede progresar a delirium tremens",
                    "Benzodiacepinas: riesgo convulsivo",
                ],
                against_features=[
                    "Sin historia de uso de sustancias",
                    "Ansiedad crónica gradual",
                    "Sin síntomas autonómicos",
                ],
                tests=[
                    DiagnosticTest(
                        "Historia de uso de sustancias detallada",
                        "Clínico",
                        "Cronología de uso y suspensión",
                        "Correlación temporal",
                        1,
                    ),
                    DiagnosticTest(
                        "Toxicología en orina",
                        "Laboratorio",
                        "Confirmar uso reciente",
                        "Positivo para sustancia",
                        1,
                    ),
                    DiagnosticTest(
                        "Perfil hepático, GGT",
                        "Laboratorio",
                        "Daño por alcohol",
                        "Elevados si uso crónico",
                        1,
                    ),
                    DiagnosticTest(
                        "CIWA-Ar (abstinencia alcohólica)",
                        "Clínico",
                        "Severidad abstinencia",
                        "Score para guiar tratamiento",
                        1,
                    ),
                ],
                urgency=Urgency.EMERGENT,
                red_flags=["Convulsiones", "Delirium tremens", "Alucinaciones"],
            ),
        ],
    },
    # =========================================================================
    # OTALGIA / DOLOR DE OÍDO
    # =========================================================================
    "otalgia": {
        "category": "ORL",
        "key_questions": [
            "¿Unilateral o bilateral?",
            "¿Fiebre?",
            "¿Secreción ótica?",
            "¿Síntomas de vía aérea superior?",
            "¿Natación o manipulación reciente?",
        ],
        "differentials": [
            DifferentialDiagnosis(
                icd10_code="H66.9",
                name="Otitis Media Aguda (OMA)",
                probability="Alta si: otalgia + fiebre + IVRS previa + membrana timpánica abombada",
                key_features=[
                    "Otalgia intensa, inicio agudo",
                    "Fiebre",
                    "Infección de vías respiratorias superiores previa",
                    "Membrana timpánica abombada, eritematosa",
                    "Hipoacusia conductiva",
                    "Más frecuente en niños",
                    "Otorrea si perforación",
                ],
                against_features=[
                    "CAE edematoso y doloroso (OE)",
                    "Membrana timpánica normal",
                    "Sin síntomas sistémicos",
                ],
                tests=[
                    DiagnosticTest(
                        "Otoscopia",
                        "Clínico",
                        "Membrana timpánica",
                        "MT abombada, opaca, eritematosa",
                        1,
                    ),
                    DiagnosticTest(
                        "Timpanometría (si disponible)",
                        "Clínico",
                        "Efusión",
                        "Curva plana tipo B",
                        2,
                    ),
                ],
                urgency=Urgency.SEMI_URGENT,
                red_flags=[
                    "Mastoiditis (dolor retroauricular, desplazamiento pabellón)",
                    "Meningitis",
                    "Parálisis facial",
                ],
            ),
            DifferentialDiagnosis(
                icd10_code="H60.9",
                name="Otitis Externa",
                probability="Alta si: otalgia + prurito CAE + secreción + dolor a tracción pabellón",
                key_features=[
                    "Otalgia que empeora al masticar o traccionar pabellón",
                    "Prurito en CAE",
                    "Secreción ótica",
                    "CAE eritematoso, edematoso",
                    "Antecedente de natación/manipulación",
                    "Membrana timpánica difícil de visualizar pero normal si se ve",
                ],
                against_features=[
                    "Fiebre alta",
                    "Membrana timpánica abombada",
                    "Sin dolor a tracción",
                ],
                tests=[
                    DiagnosticTest(
                        "Otoscopia",
                        "Clínico",
                        "CAE",
                        "Edema, eritema, debris en CAE",
                        1,
                    ),
                    DiagnosticTest(
                        "Cultivo de secreción (si no responde)",
                        "Laboratorio",
                        "Identificar patógeno",
                        "Pseudomonas, Staphylococcus",
                        2,
                    ),
                ],
                urgency=Urgency.SEMI_URGENT,
                red_flags=[
                    "OE maligna (diabético, inmunosuprimido)",
                    "Celulitis periauricular",
                    "Afectación ósea",
                ],
            ),
            DifferentialDiagnosis(
                icd10_code="K08.8",
                name="Otalgia Referida (Dental/TMJ)",
                probability="Alta si: otalgia + examen ótico normal + patología dental o TMJ evidente",
                key_features=[
                    "Otalgia sin hallazgos otológicos",
                    "Examen otoscópico NORMAL",
                    "Dolor mandibular, bruxismo",
                    "Clic o crepitación ATM",
                    "Patología dental visible",
                    "Dolor referido por V3 (trigémino)",
                ],
                against_features=[
                    "Membrana timpánica anormal",
                    "Secreción ótica",
                    "Fiebre",
                ],
                tests=[
                    DiagnosticTest(
                        "Otoscopia (normal)",
                        "Clínico",
                        "Descartar OMA/OE",
                        "CAE y MT normales",
                        1,
                    ),
                    DiagnosticTest(
                        "Examen dental/ATM",
                        "Clínico",
                        "Identificar origen",
                        "Patología dental, disfunción ATM",
                        1,
                    ),
                    DiagnosticTest(
                        "Rx panorámica dental (si indicado)",
                        "Imagen",
                        "Patología dental",
                        "Caries, absceso, impactación",
                        2,
                    ),
                ],
                urgency=Urgency.ELECTIVE,
                red_flags=["Absceso dental", "Trismus", "Fiebre"],
            ),
            DifferentialDiagnosis(
                icd10_code="H92.0",
                name="Tapón de Cerumen Impactado",
                probability="Alta si: otalgia leve + hipoacusia + cerumen visible ocluyendo CAE",
                key_features=[
                    "Otalgia leve o molestia",
                    "Hipoacusia conductiva",
                    "Sensación de oído tapado",
                    "Cerumen impactado visible",
                    "Sin fiebre ni inflamación",
                ],
                against_features=[
                    "Fiebre",
                    "Dolor severo",
                    "Secreción purulenta",
                    "CAE inflamado",
                ],
                tests=[
                    DiagnosticTest(
                        "Otoscopia",
                        "Clínico",
                        "Cerumen impactado",
                        "Tapón de cerumen ocluyendo CAE",
                        1,
                    )
                ],
                urgency=Urgency.ELECTIVE,
                red_flags=["Perforación timpánica", "Dolor intenso post-extracción"],
            ),
        ],
    },
    # =========================================================================
    # VÉRTIGO
    # =========================================================================
    "vertigo": {
        "category": "ORL/Neurología",
        "key_questions": [
            "¿Sensación de giro?",
            "¿Posicional o constante?",
            "¿Hipoacusia o tinnitus asociado?",
            "¿Síntomas neurológicos?",
            "¿Duración de los episodios?",
        ],
        "differentials": [
            DifferentialDiagnosis(
                icd10_code="H81.1",
                name="Vértigo Posicional Paroxístico Benigno (VPPB)",
                probability="Alta si: vértigo breve (<1 min) + posicional + Dix-Hallpike positivo",
                key_features=[
                    "Vértigo intenso de corta duración (<1 minuto)",
                    "Desencadenado por cambios de posición",
                    "Nistagmo torsional con Dix-Hallpike",
                    "Sin hipoacusia ni tinnitus",
                    "Examen neurológico NORMAL",
                    "Episodios recurrentes",
                ],
                against_features=[
                    "Vértigo constante >1 hora",
                    "Hipoacusia",
                    "Síntomas neurológicos focales",
                ],
                tests=[
                    DiagnosticTest(
                        "Maniobra Dix-Hallpike",
                        "Clínico",
                        "Confirmar VPPB",
                        "Nistagmo torsional, vértigo, latencia",
                        1,
                    ),
                    DiagnosticTest(
                        "Examen neurológico",
                        "Clínico",
                        "Descartar central",
                        "Normal",
                        1,
                    ),
                ],
                urgency=Urgency.SEMI_URGENT,
                red_flags=[
                    "Nistagmo vertical puro",
                    "Síntomas neurológicos",
                    "No mejora con maniobras",
                ],
            ),
            DifferentialDiagnosis(
                icd10_code="H81.0",
                name="Enfermedad de Ménière",
                probability="Alta si: vértigo episódico (20min-12h) + hipoacusia fluctuante + tinnitus + plenitud ótica",
                key_features=[
                    "Vértigo episódico de 20 min a horas",
                    "Hipoacusia neurosensorial fluctuante (frecuencias bajas)",
                    "Tinnitus unilateral",
                    "Plenitud aural",
                    "Tríada clásica: vértigo + hipoacusia + tinnitus",
                    "Sin síntomas neurológicos",
                ],
                against_features=[
                    "Vértigo constante días",
                    "Audición normal",
                    "Síntomas neurológicos",
                ],
                tests=[
                    DiagnosticTest(
                        "Audiometría",
                        "Clínico",
                        "Hipoacusia neurosensorial",
                        "Patrón de bajas frecuencias",
                        1,
                    ),
                    DiagnosticTest(
                        "RM cerebral con énfasis en CAI",
                        "Imagen",
                        "Descartar schwannoma vestibular",
                        "Normal",
                        2,
                    ),
                    DiagnosticTest(
                        "Pruebas vestibulares",
                        "Clínico",
                        "Función vestibular",
                        "Hipofunción unilateral",
                        2,
                    ),
                ],
                urgency=Urgency.SEMI_URGENT,
                red_flags=[
                    "Hipoacusia progresiva severa",
                    "Síntomas bilaterales rápidos",
                ],
            ),
            DifferentialDiagnosis(
                icd10_code="H81.2",
                name="Neuritis Vestibular",
                probability="Alta si: vértigo severo constante días + nistagmo unidireccional + sin hipoacusia",
                key_features=[
                    "Vértigo severo de inicio agudo",
                    "Duración días (constante, luego mejora gradual)",
                    "Nistagmo horizontal unidireccional",
                    "Náuseas, vómitos intensos",
                    "SIN hipoacusia (a diferencia de laberintitis)",
                    "Head impulse test positivo",
                    "Posible antecedente viral",
                ],
                against_features=[
                    "Vértigo posicional breve",
                    "Hipoacusia (= laberintitis)",
                    "Síntomas neurológicos focales",
                ],
                tests=[
                    DiagnosticTest(
                        "Head impulse test (HIT)",
                        "Clínico",
                        "Disfunción vestibular periférica",
                        "Sacada de refijación correctiva",
                        1,
                    ),
                    DiagnosticTest(
                        "HINTS exam",
                        "Clínico",
                        "Diferenciar periférico vs central",
                        "Patrón periférico benigno",
                        1,
                    ),
                    DiagnosticTest(
                        "Audiometría",
                        "Clínico",
                        "Confirmar audición normal",
                        "Normal (si hipoacusia: laberintitis)",
                        1,
                    ),
                    DiagnosticTest(
                        "RM cerebral (si duda)", "Imagen", "Descartar ACV", "Normal", 2
                    ),
                ],
                urgency=Urgency.URGENT,
                red_flags=[
                    "HINTS central (nistagmo cambiante, HIT normal, skew)",
                    "Síntomas neurológicos",
                ],
            ),
            DifferentialDiagnosis(
                icd10_code="I63.9",
                name="ACV de Fosa Posterior / Vértigo Central",
                probability="Alta si: vértigo + síntomas neurológicos + HINTS central + factores riesgo vascular",
                key_features=[
                    "Vértigo con síntomas neurológicos",
                    "Nistagmo vertical o cambiante de dirección",
                    "Ataxia de tronco severa",
                    "Disartria, disfagia",
                    "Diplopía, hemianopsia",
                    "Head impulse test NORMAL (ominoso)",
                    "Factores de riesgo cardiovascular",
                ],
                against_features=[
                    "Examen neurológico completamente normal",
                    "HINTS periférico",
                    "Joven sin factores de riesgo",
                ],
                tests=[
                    DiagnosticTest(
                        "HINTS exam URGENTE",
                        "Clínico",
                        "Patrón central",
                        "HI normal + Nistagmo cambiante + Skew deviation",
                        1,
                    ),
                    DiagnosticTest(
                        "RM cerebral con difusión",
                        "Imagen",
                        "ACV cerebeloso/tronco",
                        "Restricción en difusión",
                        1,
                    ),
                    DiagnosticTest(
                        "AngioTC/AngioRM",
                        "Imagen",
                        "Disección vertebral",
                        "Oclusión, disección",
                        1,
                    ),
                ],
                urgency=Urgency.EMERGENT,
                red_flags=[
                    "EMERGENCIA NEUROLÓGICA",
                    "ACV cerebeloso puede comprimir tronco",
                    "Ventana terapéutica limitada",
                ],
            ),
        ],
    },
}


def get_differential_for_symptom(symptom: str) -> Optional[Dict]:
    """
    Busca el diagnóstico diferencial para un síntoma dado.

    Args:
        symptom: Síntoma principal del paciente

    Returns:
        Diccionario con los diagnósticos diferenciales o None
    """
    symptom_lower = symptom.lower().strip()

    # Buscar coincidencia exacta
    if symptom_lower in SYMPTOM_DIFFERENTIALS:
        return SYMPTOM_DIFFERENTIALS[symptom_lower]

    # Buscar coincidencia parcial
    for key, value in SYMPTOM_DIFFERENTIALS.items():
        if symptom_lower in key or key in symptom_lower:
            return value
        # Buscar en categoría
        if symptom_lower in value.get("category", "").lower():
            return value

    return None


def format_differential_report(symptom: str, data: Dict) -> str:
    """
    Genera un reporte formateado del diagnóstico diferencial.

    Args:
        symptom: Síntoma principal
        data: Datos del diagnóstico diferencial

    Returns:
        Reporte en formato markdown
    """
    report = []
    report.append(f"## Diagnóstico Diferencial: {symptom.title()}\n")
    report.append(f"**Categoría:** {data['category']}\n")

    report.append("\n### Preguntas Clave para la Historia Clínica")
    for q in data["key_questions"]:
        report.append(f"- {q}")

    report.append("\n### Diagnósticos Diferenciales\n")

    for i, dx in enumerate(data["differentials"], 1):
        urgency_marker = {
            Urgency.EMERGENT: "[CRITICAL]",
            Urgency.URGENT: "[URGENT]",
            Urgency.SEMI_URGENT: "[MODERATE]",
            Urgency.ELECTIVE: "[ROUTINE]",
        }.get(dx.urgency, "[--]")

        report.append(
            f"#### {i}. {dx.name} ({dx.icd10_code}) {urgency_marker} {dx.urgency.value}"
        )
        report.append(f"\n**Probabilidad:** {dx.probability}\n")

        report.append("**A favor:**")
        for feat in dx.key_features[:5]:
            report.append(f"  - {feat}")

        report.append("\n**En contra:**")
        for feat in dx.against_features[:3]:
            report.append(f"  - {feat}")

        report.append("\n**Estudios diagnósticos:**")
        report.append("| Estudio | Categoría | Hallazgo esperado |")
        report.append("|---------|-----------|-------------------|")
        for test in dx.tests[:4]:
            report.append(
                f"| {test.name} | {test.category} | {test.expected_findings} |"
            )

        if dx.red_flags:
            report.append(f"\n**[!] Red Flags:** {', '.join(dx.red_flags)}")

        report.append("\n---\n")

    return "\n".join(report)


def get_available_symptoms() -> List[str]:
    """Retorna lista de síntomas disponibles en la base."""
    return list(SYMPTOM_DIFFERENTIALS.keys())


if __name__ == "__main__":
    print("Módulo de Diagnóstico Diferencial - MedeX")
    print("=" * 50)
    print("\nSíntomas disponibles:")
    for symptom in get_available_symptoms():
        print(f"  - {symptom}")

    # Ejemplo de uso
    print("\n" + "=" * 50)
    print("\nEjemplo: Dolor Torácico")
    print("=" * 50)

    data = get_differential_for_symptom("dolor torácico")
    if data:
        print(format_differential_report("dolor torácico", data))
