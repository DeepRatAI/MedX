#!/usr/bin/env python3
"""
🧬 Medical Ontology System - Sistema de Ontologías Médicas
===========================================================================

Implementa mapeos de terminología médica basados en:
- SNOMED-CT (Systematized Nomenclature of Medicine)
- ICD-10 (International Classification of Diseases)
- MeSH (Medical Subject Headings)
- UMLS (Unified Medical Language System)
- Terminología médica hispana

FUNCIONALIDADES:
- Expansión de sinónimos médicos
- Mapeo de términos coloquiales a técnicos
- Jerarquías anatómicas
- Relaciones farmacológicas
- Abreviaciones médicas

Author: MedeX AI Team
Version: 1.0.0
"""

from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass, field
import re


@dataclass
class MedicalConcept:
    """Concepto médico con relaciones"""

    canonical: str  # Nombre canónico
    synonyms: List[str]  # Sinónimos
    related: List[str]  # Conceptos relacionados
    parent: Optional[str]  # Concepto padre (jerarquía)
    children: List[str]  # Conceptos hijos
    icd10_codes: List[str]  # Códigos ICD-10
    snomed_codes: List[str]  # Códigos SNOMED-CT
    category: str  # Categoría (condition, symptom, drug, procedure, anatomy)


class MedicalOntology:
    """Sistema de ontologías médicas para expansión de queries"""

    def __init__(self):
        # Inicializar diccionarios
        self._init_symptom_synonyms()
        self._init_condition_synonyms()
        self._init_drug_synonyms()
        self._init_anatomy_synonyms()
        self._init_procedure_synonyms()
        self._init_abbreviations()
        self._init_colloquial_to_medical()
        self._init_emergency_terms()

    def _init_symptom_synonyms(self):
        """Sinónimos de síntomas - EXPANDIDO"""
        self.symptom_synonyms = {
            # ===== DOLOR =====
            "dolor de cabeza": [
                "cefalea",
                "cefalalgia",
                "migraña",
                "jaqueca",
                "dolor cefálico",
                "hemicránea",
            ],
            "cefalea": [
                "dolor de cabeza",
                "cefalalgia",
                "migraña",
                "jaqueca",
                "cefalea tensional",
                "cefalea en racimos",
            ],
            "dolor de pecho": [
                "dolor torácico",
                "dolor precordial",
                "opresión torácica",
                "angina",
                "dolor retrosternal",
            ],
            "dolor torácico": [
                "dolor de pecho",
                "dolor precordial",
                "angina pectoris",
                "toracalgia",
                "dolor esternal",
            ],
            "dolor abdominal": [
                "dolor de estómago",
                "dolor de barriga",
                "dolor epigástrico",
                "cólico",
                "dolor visceral",
            ],
            "dolor de espalda": [
                "lumbalgia",
                "dorsalgia",
                "cervicalgia",
                "dolor lumbar",
                "lumbago",
                "ciática",
            ],
            "dolor articular": [
                "artralgia",
                "dolor de articulaciones",
                "dolor en las coyunturas",
            ],
            "dolor muscular": [
                "mialgia",
                "dolor de músculos",
                "contractura",
                "calambre",
            ],
            "dolor de garganta": [
                "odinofagia",
                "faringitis",
                "amigdalitis",
                "irritación faríngea",
            ],
            "dolor de oído": ["otalgia", "dolor auricular", "otitis"],
            "dolor de muelas": ["odontalgia", "dolor dental"],
            "dolor pélvico": [
                "dolor en la pelvis",
                "dolor bajo vientre",
                "dismenorrea",
            ],
            # ===== RESPIRATORIO =====
            "falta de aire": [
                "disnea",
                "dificultad respiratoria",
                "ahogo",
                "sensación de asfixia",
                "sofocación",
            ],
            "falta el aire": [
                "disnea",
                "dificultad respiratoria",
                "ahogo",
                "disnea de esfuerzo",
            ],
            "me falta el aire": ["disnea", "dificultad respiratoria", "ortopnea"],
            "no puedo respirar": [
                "disnea severa",
                "dificultad respiratoria",
                "asfixia",
                "insuficiencia respiratoria",
            ],
            "disnea": [
                "falta de aire",
                "dificultad respiratoria",
                "ahogo",
                "jadeo",
                "taquipnea",
            ],
            "tos": [
                "expectoración",
                "tos productiva",
                "tos seca",
                "tos crónica",
                "tos nocturna",
            ],
            "tos con sangre": ["hemoptisis", "esputo hemoptoico", "tos sanguinolenta"],
            "sibilancias": [
                "silbidos al respirar",
                "pitos",
                "broncoespasmo",
                "ruidos respiratorios",
            ],
            "ronquera": ["disfonía", "voz ronca", "afonía", "cambio de voz"],
            "estornudos": ["rinorrea", "congestión nasal", "coriza"],
            "congestión nasal": ["nariz tapada", "obstrucción nasal", "rinitis"],
            # ===== CARDIOVASCULAR =====
            "palpitaciones": [
                "taquicardia",
                "latidos rápidos",
                "corazón acelerado",
                "arritmia",
                "extrasístoles",
            ],
            "mareo": [
                "vértigo",
                "inestabilidad",
                "sensación de desmayo",
                "presíncope",
                "aturdimiento",
            ],
            "desmayo": [
                "síncope",
                "pérdida de conocimiento",
                "lipotimia",
                "desvanecimiento",
            ],
            "hinchazón de piernas": [
                "edema de miembros inferiores",
                "piernas hinchadas",
                "edema podal",
            ],
            "cianosis": ["labios morados", "color azulado", "uñas moradas"],
            # ===== GASTROINTESTINAL =====
            "náuseas": [
                "ganas de vomitar",
                "arcadas",
                "malestar estomacal",
                "sensación nauseosa",
            ],
            "vómito": ["emesis", "vómitos", "regurgitación", "vómito en proyectil"],
            "vómito con sangre": ["hematemesis", "vómito sanguinolento"],
            "diarrea": [
                "deposiciones líquidas",
                "heces sueltas",
                "gastroenteritis",
                "diarrea acuosa",
            ],
            "diarrea con sangre": [
                "hematoquecia",
                "disentería",
                "sangrado rectal",
                "rectorragia",
            ],
            "estreñimiento": [
                "constipación",
                "dificultad para evacuar",
                "tránsito lento",
            ],
            "acidez": ["pirosis", "agruras", "reflujo", "ardor estomacal", "ERGE"],
            "distensión abdominal": [
                "hinchazón abdominal",
                "meteorismo",
                "gases",
                "flatulencia",
            ],
            "pérdida de apetito": ["anorexia", "hiporexia", "inapetencia"],
            "dificultad para tragar": [
                "disfagia",
                "atragantamiento",
                "sensación de globo",
            ],
            "ictericia": [
                "color amarillo",
                "ojos amarillos",
                "piel amarilla",
                "coloración ictérica",
            ],
            # ===== NEUROLÓGICO =====
            "debilidad": [
                "astenia",
                "fatiga",
                "cansancio",
                "adinamia",
                "debilidad generalizada",
            ],
            "debilidad de un lado": [
                "hemiparesia",
                "hemiplejia",
                "parálisis unilateral",
            ],
            "adormecimiento": [
                "parestesia",
                "hormigueo",
                "entumecimiento",
                "hipoestesia",
            ],
            "convulsiones": [
                "crisis epiléptica",
                "espasmos",
                "ataques",
                "crisis convulsiva",
                "epilepsia",
            ],
            "temblor": ["temblores", "tremor", "sacudidas involuntarias"],
            "dificultad para hablar": [
                "afasia",
                "disartria",
                "problemas del lenguaje",
                "habla arrastrada",
            ],
            "confusión": [
                "desorientación",
                "alteración mental",
                "obnubilación",
                "estado confusional",
            ],
            "pérdida de memoria": [
                "amnesia",
                "olvidos",
                "deterioro cognitivo",
                "fallas de memoria",
            ],
            "visión borrosa": [
                "alteración visual",
                "visión doble",
                "diplopía",
                "disminución agudeza visual",
            ],
            "pérdida de visión": ["amaurosis", "ceguera", "escotoma", "hemianopsia"],
            # ===== URINARIO =====
            "dolor al orinar": ["disuria", "ardor al orinar", "micción dolorosa"],
            "sangre en orina": ["hematuria", "orina con sangre", "orina roja"],
            "orina frecuente": [
                "polaquiuria",
                "frecuencia urinaria",
                "urgencia urinaria",
            ],
            "incontinencia": [
                "incontinencia urinaria",
                "escape de orina",
                "pérdida de control vesical",
            ],
            "retención urinaria": [
                "dificultad para orinar",
                "no puede orinar",
                "anuria",
            ],
            # ===== PIEL =====
            "erupción": ["rash", "exantema", "lesiones cutáneas", "sarpullido"],
            "picazón": ["prurito", "comezón", "escozor", "picor"],
            "hinchazón": ["edema", "inflamación", "tumefacción", "tumefacción"],
            "moretones": ["equimosis", "hematomas", "contusiones", "cardenales"],
            "palidez": ["piel pálida", "anemia", "hipoperfusión"],
            "sudoración": ["diaforesis", "sudoración profusa", "hiperhidrosis"],
            # ===== GENERAL =====
            "fiebre": [
                "hipertermia",
                "temperatura elevada",
                "pirexia",
                "calentura",
                "febrícula",
            ],
            "escalofríos": ["temblor por frío", "calofríos", "rigidez"],
            "pérdida de peso": ["adelgazamiento", "baja de peso", "caquexia"],
            "aumento de peso": ["obesidad", "sobrepeso", "ganancia ponderal"],
            "insomnio": [
                "dificultad para dormir",
                "trastorno del sueño",
                "no puedo dormir",
            ],
            "somnolencia": ["sueño excesivo", "letargia", "sopor", "hipersomnia"],
            "ansiedad": ["nerviosismo", "angustia", "inquietud", "crisis de ansiedad"],
            "depresión": ["tristeza", "ánimo bajo", "melancolía", "estado depresivo"],
            # ===== OFTALMOLÓGICO =====
            "ojo rojo": [
                "hiperemia conjuntival",
                "conjuntivitis",
                "inyección conjuntival",
                "ojo irritado",
            ],
            "lagrimeo": ["epífora", "ojos llorosos", "secreción lagrimal"],
            "fotofobia": [
                "sensibilidad a la luz",
                "intolerancia a luz",
                "molestia con luz",
            ],
            "dolor ocular": ["oftalmalgia", "dolor de ojo", "dolor periocular"],
            "visión de moscas volantes": [
                "miodesopsias",
                "flotadores",
                "puntos en la visión",
            ],
            "visión de halos": [
                "halos alrededor de luces",
                "arcoíris alrededor de luces",
            ],
            "pérdida súbita de visión": [
                "amaurosis fugax",
                "ceguera súbita",
                "pérdida visual aguda",
            ],
            "ojo seco": ["xeroftalmía", "sequedad ocular", "síndrome de ojo seco"],
            "secreción ocular": [
                "legañas",
                "conjuntivitis purulenta",
                "secreción purulenta",
            ],
            "ptosis": ["párpado caído", "caída del párpado"],
            # ===== AUDITIVO =====
            "pérdida de audición": [
                "hipoacusia",
                "sordera",
                "disminución auditiva",
                "audición reducida",
            ],
            "zumbido en oídos": ["tinnitus", "acúfenos", "ruido en oídos", "pitido"],
            "vértigo rotatorio": [
                "vértigo verdadero",
                "sensación de giro",
                "mareo rotatorio",
            ],
            "otorrea": ["secreción del oído", "supuración ótica", "oído que supura"],
            # ===== GINECOLÓGICO/OBSTÉTRICO =====
            "dolor menstrual": ["dismenorrea", "cólicos menstruales", "dolor de regla"],
            "sangrado menstrual abundante": [
                "menorragia",
                "hipermenorrea",
                "regla abundante",
            ],
            "ausencia de menstruación": ["amenorrea", "falta de regla", "no me baja"],
            "sangrado entre periodos": [
                "metrorragia",
                "sangrado intermenstrual",
                "spotting",
            ],
            "dolor durante relaciones": [
                "dispareunia",
                "dolor coital",
                "dolor al tener relaciones",
            ],
            "flujo vaginal anormal": [
                "leucorrea",
                "descarga vaginal",
                "flujo patológico",
            ],
            "dolor pélvico crónico": [
                "dolor bajo vientre crónico",
                "dolor ginecológico",
            ],
            "bochornos": [
                "sofocos",
                "oleadas de calor",
                "síntomas vasomotores",
                "calores",
            ],
            "sangrado postmenopáusico": [
                "metrorragia postmenopáusica",
                "sangrado después de menopausia",
            ],
            # ===== MASCULINO/UROLÓGICO =====
            "dificultad para orinar": [
                "disuria",
                "chorro débil",
                "esfuerzo miccional",
                "hesitancia",
            ],
            "goteo terminal": ["goteo postmiccional", "escurrimiento"],
            "micción nocturna": ["nicturia", "levantarse a orinar", "orinar de noche"],
            "dolor testicular": ["orquialgia", "dolor de testículo"],
            "masa testicular": ["nódulo testicular", "bulto en testículo"],
            "disfunción eréctil": ["impotencia", "DE", "dificultad para erección"],
            "eyaculación precoz": ["EP", "eyaculación prematura"],
            "sangre en semen": ["hematospermia", "semen con sangre"],
            # ===== INMUNOLÓGICO =====
            "ganglios inflamados": [
                "adenopatía",
                "linfadenopatía",
                "ganglios grandes",
                "bolas en cuello",
            ],
            "debilidad inmune": [
                "inmunosupresión",
                "infecciones recurrentes",
                "inmunidad baja",
            ],
            "reacción alérgica": ["alergia", "hipersensibilidad", "anafilaxis leve"],
            "urticaria": ["ronchas", "habones", "erupción urticarial"],
            "angioedema": [
                "hinchazón de labios",
                "edema de labios",
                "inflamación de cara",
            ],
            # ===== NUTRICIONAL =====
            "sed excesiva": ["polidipsia", "mucha sed", "sed intensa"],
            "hambre excesiva": ["polifagia", "mucha hambre", "apetito aumentado"],
            "fatiga crónica": [
                "cansancio persistente",
                "agotamiento crónico",
                "astenia crónica",
            ],
            "calambres": ["espasmos musculares", "contracturas", "calambres nocturnos"],
            "debilidad muscular": ["miopatía", "hipotonía", "fuerza disminuida"],
        }

    def _init_condition_synonyms(self):
        """Sinónimos de condiciones médicas - EXPANDIDO"""
        self.condition_synonyms = {
            # ===== CARDIOVASCULAR =====
            "infarto": [
                "IAM",
                "infarto agudo de miocardio",
                "ataque cardíaco",
                "ataque al corazón",
                "STEMI",
                "NSTEMI",
                "síndrome coronario agudo",
                "SCA",
                "necrosis miocárdica",
            ],
            "hipertensión": [
                "presión alta",
                "HTA",
                "hipertensión arterial",
                "tensión alta",
                "presión arterial elevada",
                "hipertensión esencial",
            ],
            "insuficiencia cardíaca": [
                "falla cardíaca",
                "IC",
                "corazón débil",
                "ICC",
                "insuficiencia cardíaca congestiva",
                "fallo cardíaco",
            ],
            "arritmia": [
                "irregularidad cardíaca",
                "fibrilación",
                "taquicardia",
                "bradicardia",
                "extrasístoles",
                "flutter",
                "FA",
                "fibrilación auricular",
            ],
            "angina": [
                "angina de pecho",
                "angina pectoris",
                "dolor anginoso",
                "isquemia miocárdica",
            ],
            "endocarditis": ["endocarditis infecciosa", "EI", "infección valvular"],
            "pericarditis": [
                "inflamación pericardio",
                "pericarditis aguda",
                "derrame pericárdico",
            ],
            "miocarditis": ["inflamación miocardio", "miocardiopatía inflamatoria"],
            "trombosis venosa": [
                "TVP",
                "trombosis venosa profunda",
                "coágulo en pierna",
                "tromboflebitis",
            ],
            "embolia pulmonar": [
                "TEP",
                "tromboembolismo pulmonar",
                "embolia de pulmón",
                "EP",
            ],
            # ===== RESPIRATORIO =====
            "asma": [
                "broncoespasmo",
                "hiperreactividad bronquial",
                "asma bronquial",
                "crisis asmática",
            ],
            "neumonía": [
                "pulmonía",
                "infección pulmonar",
                "neumonitis",
                "NAC",
                "neumonía adquirida en comunidad",
            ],
            "EPOC": [
                "enfermedad pulmonar obstructiva crónica",
                "enfisema",
                "bronquitis crónica",
                "COPD",
                "limitación crónica flujo aéreo",
            ],
            "bronquitis": [
                "bronquitis aguda",
                "inflamación bronquial",
                "bronquitis crónica",
            ],
            "tuberculosis": [
                "TB",
                "TBC",
                "enfermedad de Koch",
                "tuberculosis pulmonar",
            ],
            "neumotórax": ["colapso pulmonar", "aire en pleura", "pulmón colapsado"],
            "derrame pleural": ["líquido en pleura", "pleuresía", "hidrotórax"],
            "fibrosis pulmonar": [
                "enfermedad pulmonar intersticial",
                "EPI",
                "pulmón fibrosado",
            ],
            "apnea del sueño": [
                "SAHOS",
                "SAOS",
                "apnea obstructiva",
                "ronquidos patológicos",
            ],
            # ===== ENDOCRINO =====
            "diabetes": [
                "DM",
                "diabetes mellitus",
                "azúcar alta",
                "hiperglucemia crónica",
                "DM2",
                "DM1",
                "diabetes tipo 2",
                "diabetes tipo 1",
            ],
            "hipotiroidismo": [
                "tiroides baja",
                "función tiroidea baja",
                "mixedema",
                "tiroiditis de Hashimoto",
            ],
            "hipertiroidismo": [
                "tiroides alta",
                "tirotoxicosis",
                "enfermedad de Graves",
                "bocio tóxico",
            ],
            "cetoacidosis diabética": [
                "CAD",
                "DKA",
                "crisis hiperglucémica",
                "descompensación diabética",
            ],
            "hipoglucemia": ["azúcar baja", "baja de azúcar", "glucosa baja"],
            "síndrome metabólico": [
                "resistencia a insulina",
                "síndrome X",
                "prediabetes",
            ],
            "obesidad": ["sobrepeso", "adiposidad", "IMC elevado"],
            # ===== NEUROLÓGICO =====
            "ACV": [
                "accidente cerebrovascular",
                "derrame cerebral",
                "ictus",
                "stroke",
                "infarto cerebral",
                "hemorragia cerebral",
                "EVC",
                "evento vascular cerebral",
            ],
            "epilepsia": [
                "trastorno convulsivo",
                "crisis epilépticas",
                "convulsiones recurrentes",
            ],
            "alzheimer": [
                "demencia",
                "deterioro cognitivo",
                "enfermedad de Alzheimer",
                "EA",
            ],
            "parkinson": [
                "enfermedad de Parkinson",
                "EP",
                "parkinsonismo",
                "temblor parkinsoniano",
            ],
            "migraña": [
                "jaqueca",
                "cefalea migrañosa",
                "hemicránea",
                "migraña con aura",
            ],
            "esclerosis múltiple": ["EM", "MS", "enfermedad desmielinizante"],
            "meningitis": [
                "infección meníngea",
                "meningoencefalitis",
                "inflamación meninges",
            ],
            "neuropatía": ["neuropatía periférica", "daño nervioso", "polineuropatía"],
            "ciática": ["radiculopatía lumbar", "dolor ciático", "lumbociatalgia"],
            # ===== GASTROINTESTINAL =====
            "gastritis": ["inflamación gástrica", "irritación estomacal", "dispepsia"],
            "úlcera péptica": [
                "úlcera gástrica",
                "úlcera duodenal",
                "enfermedad ulcerosa",
            ],
            "reflujo": [
                "ERGE",
                "reflujo gastroesofágico",
                "acidez",
                "esofagitis por reflujo",
            ],
            "pancreatitis": [
                "inflamación páncreas",
                "pancreatitis aguda",
                "pancreatitis crónica",
            ],
            "colecistitis": [
                "inflamación vesícula",
                "cólico biliar",
                "piedras en vesícula",
            ],
            "apendicitis": ["inflamación apéndice", "apéndice inflamado"],
            "hepatitis": [
                "inflamación hígado",
                "hepatitis viral",
                "hepatitis alcohólica",
            ],
            "cirrosis": [
                "cirrosis hepática",
                "enfermedad hepática crónica",
                "fibrosis hepática",
            ],
            "colitis": [
                "colitis ulcerosa",
                "enfermedad inflamatoria intestinal",
                "EII",
            ],
            "crohn": ["enfermedad de Crohn", "enteritis regional", "ileitis"],
            "hemorragia digestiva": [
                "HDA",
                "HDB",
                "sangrado GI",
                "melena",
                "hematoquecia",
            ],
            # ===== INFECCIOSO =====
            "COVID-19": [
                "coronavirus",
                "SARS-CoV-2",
                "covid",
                "infección por coronavirus",
            ],
            "influenza": ["gripe", "flu", "infección viral respiratoria", "gripa"],
            "sepsis": ["septicemia", "infección generalizada", "shock séptico", "SIRS"],
            "infección urinaria": ["ITU", "cistitis", "infección de orina", "IVU"],
            "pielonefritis": ["infección renal", "infección de riñón"],
            "celulitis": ["infección de piel", "celulitis infecciosa"],
            "faringitis": [
                "anginas",
                "dolor de garganta",
                "amigdalitis",
                "faringoamigdalitis",
            ],
            "gastroenteritis": ["infección intestinal", "diarrea infecciosa", "GEA"],
            "VIH": [
                "SIDA",
                "virus inmunodeficiencia humana",
                "HIV",
                "infección por VIH",
            ],
            # ===== RENAL =====
            "insuficiencia renal": [
                "falla renal",
                "IRC",
                "ERC",
                "enfermedad renal crónica",
                "IRA",
            ],
            "nefrolitiasis": [
                "piedras en riñón",
                "cálculos renales",
                "litiasis renal",
                "cólico renal",
            ],
            "nefritis": ["glomerulonefritis", "inflamación renal"],
            # ===== MUSCULOESQUELÉTICO =====
            "artritis": [
                "inflamación articular",
                "artritis reumatoide",
                "AR",
                "poliartritis",
            ],
            "osteoartritis": [
                "artrosis",
                "desgaste articular",
                "OA",
                "artritis degenerativa",
            ],
            "osteoporosis": ["huesos frágiles", "descalcificación", "pérdida ósea"],
            "lumbalgia": ["dolor lumbar", "lumbago", "dolor de espalda baja"],
            "hernia discal": ["hernia de disco", "protrusión discal", "disco herniado"],
            "fibromialgia": ["dolor muscular crónico", "síndrome fibromiálgico"],
            "gota": ["artritis gotosa", "hiperuricemia", "ácido úrico alto"],
            # ===== HEMATOLÓGICO =====
            "anemia": [
                "sangre baja",
                "hemoglobina baja",
                "glóbulos rojos bajos",
                "anemia ferropénica",
            ],
            "leucemia": ["cáncer de sangre", "neoplasia hematológica"],
            "linfoma": ["cáncer linfático", "enfermedad de Hodgkin"],
            "trombocitopenia": ["plaquetas bajas", "sangrado fácil"],
            # ===== ONCOLÓGICO =====
            "cáncer": [
                "neoplasia",
                "tumor maligno",
                "carcinoma",
                "malignidad",
                "neoplasia maligna",
            ],
            "cáncer de mama": [
                "carcinoma mamario",
                "tumor de mama",
                "neoplasia mamaria",
            ],
            "cáncer de pulmón": [
                "carcinoma pulmonar",
                "tumor pulmonar",
                "carcinoma broncogénico",
            ],
            "cáncer de colon": ["carcinoma colorrectal", "CCR", "tumor de colon"],
            # ===== PSIQUIÁTRICO =====
            "depresión": [
                "trastorno depresivo",
                "TDM",
                "depresión mayor",
                "estado depresivo",
            ],
            "ansiedad": [
                "trastorno de ansiedad",
                "TAG",
                "ansiedad generalizada",
                "crisis de ansiedad",
            ],
            "esquizofrenia": ["psicosis", "trastorno psicótico"],
            "trastorno bipolar": ["bipolaridad", "enfermedad maníaco-depresiva"],
            # ===== DERMATOLÓGICO =====
            "psoriasis": [
                "psoriasis vulgar",
                "psoriasis en placas",
                "psoriasis guttata",
            ],
            "eccema": ["dermatitis atópica", "dermatitis", "eccema atópico"],
            "acné": ["acné vulgar", "acné juvenil", "granos", "espinillas"],
            "urticaria crónica": ["urticaria idiopática", "ronchas crónicas"],
            "dermatitis de contacto": ["alergia de piel", "dermatitis alérgica"],
            "rosácea": ["cuperosis", "acné rosácea"],
            "vitiligo": ["despigmentación", "manchas blancas en piel"],
            "alopecia": ["caída de cabello", "pérdida de cabello", "calvicie"],
            "herpes zóster": ["culebrilla", "herpes zona", "shingles"],
            "impétigo": ["infección cutánea bacteriana", "pioderma"],
            # ===== OFTALMOLÓGICO =====
            "glaucoma": [
                "presión ocular alta",
                "hipertensión ocular",
                "glaucoma de ángulo abierto",
            ],
            "cataratas": ["opacidad del cristalino", "nube en el ojo"],
            "degeneración macular": [
                "DMAE",
                "maculopatía",
                "degeneración macular relacionada con edad",
            ],
            "retinopatía diabética": [
                "daño retina por diabetes",
                "complicación ocular DM",
            ],
            "conjuntivitis": ["ojo rojo", "infección ocular", "conjuntivitis viral"],
            "uveítis": ["inflamación uvea", "iritis", "ciclitis"],
            "blefaritis": ["inflamación párpado", "párpados inflamados"],
            "ojo seco": [
                "síndrome de ojo seco",
                "queratoconjuntivitis seca",
                "xeroftalmía",
            ],
            # ===== OTORRINOLARINGOLÓGICO =====
            "otitis media": ["infección de oído", "otitis", "otitis media aguda"],
            "sinusitis": [
                "infección de senos paranasales",
                "sinusitis aguda",
                "rinosinusitis",
            ],
            "rinitis alérgica": [
                "alergia nasal",
                "fiebre del heno",
                "rinitis estacional",
            ],
            "vértigo posicional": ["VPPB", "vértigo posicional benigno"],
            "enfermedad de Ménière": ["Ménière", "hidrops endolinfático"],
            "pérdida auditiva": ["hipoacusia", "sordera", "déficit auditivo"],
            "amigdalitis": ["anginas", "tonsilitis", "inflamación de amígdalas"],
            "laringitis": ["inflamación laringe", "voz ronca", "disfonía"],
            # ===== GINECOLÓGICO/OBSTÉTRICO =====
            "endometriosis": [
                "endometrioma",
                "adenomiosis",
                "tejido endometrial ectópico",
            ],
            "síndrome ovario poliquístico": ["SOP", "PCOS", "ovarios poliquísticos"],
            "mioma uterino": ["fibroma", "leiomioma", "fibroma uterino"],
            "vaginitis": [
                "vaginosis bacteriana",
                "candidiasis vaginal",
                "infección vaginal",
            ],
            "menopausia": ["climaterio", "perimenopausia", "síndrome climatérico"],
            "preeclampsia": [
                "toxemia del embarazo",
                "preeclampsia severa",
                "eclampsia",
            ],
            "embarazo ectópico": ["embarazo tubárico", "gestación ectópica"],
            "aborto espontáneo": ["pérdida gestacional", "aborto natural"],
            # ===== PEDIÁTRICO =====
            "varicela": ["chickenpox", "infección varicela-zóster"],
            "sarampión": ["measles", "rubeola", "exantema viral"],
            "rubéola": ["sarampión alemán", "rubella"],
            "paperas": ["parotiditis", "inflamación parótida"],
            "escarlatina": ["fiebre escarlata", "infección estreptocócica"],
            "mononucleosis": ["mono", "enfermedad del beso", "infección por EBV"],
            "crup": ["laringotraqueítis", "tos de foca"],
            "bronquiolitis": ["infección bronquiolar", "VRS en niños"],
            # ===== AUTOINMUNE =====
            "lupus": ["LES", "lupus eritematoso sistémico", "lupus eritematoso"],
            "síndrome de Sjögren": ["Sjögren", "síndrome seco"],
            "escleroderma": ["esclerosis sistémica", "esclerodermia"],
            "vasculitis": ["inflamación vascular", "angeítis"],
            "enfermedad de Behcet": ["Behcet", "síndrome de Behcet"],
            "polimiositis": ["miositis", "dermatomiositis"],
            "artritis psoriásica": ["APs", "artritis en psoriasis"],
            # ===== METABÓLICO =====
            "dislipidemia": [
                "colesterol alto",
                "hiperlipidemia",
                "triglicéridos altos",
            ],
            "hiperuricemia": ["ácido úrico elevado", "gota metabólica"],
            "síndrome de Cushing": ["Cushing", "hipercortisolismo"],
            "enfermedad de Addison": ["insuficiencia suprarrenal", "hipoadrenalismo"],
            "hiperaldosteronismo": ["aldosteronismo", "síndrome de Conn"],
            "feocromocitoma": ["tumor suprarrenal", "tumor de médula adrenal"],
        }

    def _init_drug_synonyms(self):
        """Sinónimos de medicamentos - EXPANDIDO"""
        self.drug_synonyms = {
            # ===== ANALGÉSICOS =====
            "paracetamol": ["acetaminofén", "tylenol", "acetaminofeno", "apiretal"],
            "ibuprofeno": ["advil", "motrin", "brufen", "nurofen", "AINE"],
            "aspirina": ["ácido acetilsalicílico", "AAS", "ASA", "ecotrin"],
            "diclofenaco": ["voltaren", "cataflam", "AINE", "antiinflamatorio"],
            "naproxeno": ["aleve", "naprosyn", "AINE"],
            "tramadol": ["tramal", "ultram", "opioide menor"],
            "morfina": ["opiáceo", "opioide", "analgésico narcótico", "MS contin"],
            "codeína": ["opioide menor", "antitusivo opioide"],
            "oxicodona": ["oxycontin", "opioide mayor"],
            "fentanilo": ["duragesic", "opioide potente", "parche de fentanilo"],
            "ketorolaco": ["toradol", "AINE inyectable"],
            "metamizol": ["dipirona", "nolotil"],
            # ===== CARDIOVASCULARES =====
            "enalapril": ["renitec", "IECA", "inhibidor de la ECA", "vasotec"],
            "lisinopril": ["zestril", "IECA", "prinivil"],
            "losartán": ["cozaar", "ARA II", "bloqueador de angiotensina"],
            "valsartán": ["diovan", "ARA II"],
            "amlodipino": ["norvasc", "bloqueador de calcio", "antagonista calcio"],
            "nifedipino": ["adalat", "procardia", "BCC"],
            "metoprolol": ["lopressor", "betabloqueador", "BB"],
            "carvedilol": ["coreg", "betabloqueador", "alfa-betabloqueador"],
            "propranolol": ["inderal", "betabloqueador no selectivo"],
            "atenolol": ["tenormin", "betabloqueador"],
            "bisoprolol": ["concor", "betabloqueador selectivo"],
            "atorvastatina": ["lipitor", "estatina", "inhibidor HMG-CoA"],
            "rosuvastatina": ["crestor", "estatina"],
            "simvastatina": ["zocor", "estatina"],
            "clopidogrel": ["plavix", "antiagregante", "antiplaquetario"],
            "warfarina": ["coumadin", "anticoagulante", "cumarínico"],
            "heparina": ["anticoagulante", "HBPM", "enoxaparina"],
            "enoxaparina": [
                "clexane",
                "lovenox",
                "HBPM",
                "heparina bajo peso molecular",
            ],
            "rivaroxabán": ["xarelto", "DOAC", "anticoagulante oral directo"],
            "apixabán": ["eliquis", "DOAC", "anticoagulante oral"],
            "furosemida": ["lasix", "diurético de asa"],
            "hidroclorotiazida": ["HCTZ", "diurético tiazídico"],
            "espironolactona": ["aldactone", "diurético ahorrador de potasio"],
            "digoxina": ["lanoxin", "digitálico", "cardiotónico"],
            "nitroglicerina": ["NTG", "nitrato", "trinitrina"],
            "amiodarona": ["cordarone", "antiarrítmico"],
            # ===== ANTIBIÓTICOS =====
            "amoxicilina": ["amoxil", "penicilina", "betalactámico"],
            "ampicilina": ["penicilina", "betalactámico"],
            "penicilina": ["penicilina G", "penicilina V", "betalactámico"],
            "azitromicina": ["zithromax", "macrólido", "azitromicina Z-pack"],
            "claritromicina": ["biaxin", "macrólido"],
            "eritromicina": ["macrólido", "E-mycin"],
            "ciprofloxacino": ["cipro", "fluoroquinolona", "quinolona"],
            "levofloxacino": ["levaquin", "fluoroquinolona"],
            "moxifloxacino": ["avelox", "fluoroquinolona"],
            "metronidazol": ["flagyl", "nitroimidazol"],
            "clindamicina": ["cleocin", "lincosamida"],
            "vancomicina": ["vancocin", "glucopéptido"],
            "ceftriaxona": ["rocephin", "cefalosporina 3G"],
            "cefuroxima": ["zinacef", "cefalosporina 2G"],
            "cefalexina": ["keflex", "cefalosporina 1G"],
            "trimetoprim-sulfametoxazol": ["TMP-SMX", "bactrim", "cotrimoxazol"],
            "doxiciclina": ["vibramicina", "tetraciclina"],
            "gentamicina": ["aminoglucósido", "garamicina"],
            "piperacilina-tazobactam": ["zosyn", "pip-tazo", "betalactámico"],
            "meropenem": ["merrem", "carbapenem"],
            "imipenem": ["primaxin", "carbapenem"],
            # ===== ANTIDIABÉTICOS =====
            "metformina": ["glucophage", "biguanida", "antidiabético oral"],
            "glibenclamida": ["sulfonilurea", "daonil", "diabeta"],
            "glimepirida": ["amaryl", "sulfonilurea"],
            "sitagliptina": ["januvia", "inhibidor DPP-4", "gliptina"],
            "linagliptina": ["tradjenta", "inhibidor DPP-4"],
            "empagliflozina": ["jardiance", "inhibidor SGLT2", "gliflozina"],
            "dapagliflozina": ["forxiga", "inhibidor SGLT2"],
            "canagliflozina": ["invokana", "inhibidor SGLT2"],
            "liraglutida": ["victoza", "saxenda", "agonista GLP-1"],
            "semaglutida": ["ozempic", "wegovy", "agonista GLP-1"],
            "insulina": [
                "insulina regular",
                "insulina NPH",
                "insulina glargina",
                "lantus",
            ],
            "insulina glargina": ["lantus", "toujeo", "insulina basal"],
            "insulina lispro": ["humalog", "insulina rápida"],
            "insulina aspart": ["novorapid", "novolog", "insulina ultrarrápida"],
            # ===== RESPIRATORIO =====
            "salbutamol": ["albuterol", "ventolin", "broncodilatador", "SABA"],
            "ipratropio": ["atrovent", "anticolinérgico", "SAMA"],
            "tiotropio": ["spiriva", "LAMA", "anticolinérgico de larga acción"],
            "salmeterol": ["serevent", "LABA", "beta agonista larga acción"],
            "formoterol": ["foradil", "LABA"],
            "budesonida": ["pulmicort", "corticoide inhalado", "ICS"],
            "fluticasona": ["flovent", "flixotide", "corticoide inhalado"],
            "beclometasona": ["qvar", "corticoide inhalado"],
            "montelukast": ["singulair", "antileucotrieno"],
            "teofilina": ["aminofilina", "metilxantina"],
            "prednisona": ["deltasone", "corticoide sistémico", "esteroide"],
            "dexametasona": ["decadron", "corticoide", "esteroide potente"],
            "metilprednisolona": ["solu-medrol", "medrol", "corticoide"],
            # ===== GASTROINTESTINAL =====
            "omeprazol": ["prilosec", "IBP", "inhibidor de bomba de protones"],
            "esomeprazol": ["nexium", "IBP"],
            "pantoprazol": ["protonix", "IBP"],
            "lansoprazol": ["prevacid", "IBP"],
            "ranitidina": ["zantac", "antihistamínico H2", "anti-H2"],
            "famotidina": ["pepcid", "antihistamínico H2"],
            "metoclopramida": ["reglan", "procinético", "antiemético"],
            "ondansetrón": ["zofran", "antiemético", "anti-5HT3"],
            "loperamida": ["imodium", "antidiarreico"],
            "lactulosa": ["laxante osmótico", "duphalac"],
            "bisacodilo": ["dulcolax", "laxante estimulante"],
            "sucralfato": ["carafate", "protector gástrico"],
            # ===== NEUROLÓGICO/PSIQUIÁTRICO =====
            "levetiracetam": ["keppra", "antiepiléptico", "anticonvulsivante"],
            "fenitoína": ["dilantin", "antiepiléptico"],
            "carbamazepina": ["tegretol", "antiepiléptico"],
            "valproato": ["depakene", "depakote", "ácido valproico", "antiepiléptico"],
            "gabapentina": ["neurontin", "antiepiléptico", "dolor neuropático"],
            "pregabalina": ["lyrica", "antiepiléptico", "dolor neuropático"],
            "lamotrigina": ["lamictal", "antiepiléptico"],
            "levodopa": ["sinemet", "antiparkinsoniano", "levodopa-carbidopa"],
            "sumatriptán": ["imitrex", "triptán", "antimigrañoso"],
            "fluoxetina": ["prozac", "ISRS", "antidepresivo"],
            "sertralina": ["zoloft", "ISRS", "antidepresivo"],
            "escitalopram": ["lexapro", "ISRS", "antidepresivo"],
            "paroxetina": ["paxil", "ISRS", "antidepresivo"],
            "venlafaxina": ["effexor", "IRSN", "antidepresivo"],
            "duloxetina": ["cymbalta", "IRSN", "antidepresivo"],
            "amitriptilina": ["elavil", "tricíclico", "antidepresivo tricíclico"],
            "bupropión": ["wellbutrin", "antidepresivo atípico"],
            "trazodona": ["desyrel", "antidepresivo", "hipnótico"],
            "mirtazapina": ["remeron", "antidepresivo atípico"],
            "alprazolam": ["xanax", "benzodiazepina", "ansiolítico"],
            "lorazepam": ["ativan", "benzodiazepina", "ansiolítico"],
            "diazepam": ["valium", "benzodiazepina"],
            "clonazepam": ["klonopin", "rivotril", "benzodiazepina"],
            "zolpidem": ["ambien", "hipnótico no benzodiazepínico"],
            "quetiapina": ["seroquel", "antipsicótico atípico"],
            "risperidona": ["risperdal", "antipsicótico atípico"],
            "olanzapina": ["zyprexa", "antipsicótico atípico"],
            "haloperidol": ["haldol", "antipsicótico típico", "neuroléptico"],
            # ===== EMERGENCIA =====
            "epinefrina": ["adrenalina", "catecolamina", "epipen"],
            "atropina": ["anticolinérgico", "antimuscarínico"],
            "naloxona": ["narcan", "antagonista opioide", "antídoto opioides"],
            "flumazenil": ["romazicon", "antagonista benzodiazepinas"],
            "alteplasa": ["activase", "rtPA", "trombolítico"],
            "adenosina": ["adenocard", "antiarrítmico"],
            "norepinefrina": ["noradrenalina", "levophed", "vasopresor"],
            "dopamina": ["intropin", "vasopresor", "inotrópico"],
            "dobutamina": ["dobutrex", "inotrópico"],
            "vasopresina": ["pitressin", "ADH", "vasopresor"],
            # ===== DERMATOLÓGICOS =====
            "isotretinoína": ["accutane", "roaccutane", "retinoide oral"],
            "adapaleno": ["differin", "retinoide tópico"],
            "tretinoína": ["retin-A", "retinoide tópico", "ácido retinoico"],
            "minociclina": ["minocin", "tetraciclina", "antibiótico acné"],
            "doxiciclina": ["vibramicina", "tetraciclina", "antibiótico"],
            "mupirocina": ["bactroban", "antibiótico tópico"],
            "clotrimazol": ["canesten", "antimicótico tópico"],
            "ketoconazol": ["nizoral", "antimicótico"],
            "fluconazol": ["diflucan", "antimicótico sistémico"],
            "clobetasol": ["temovate", "corticoide tópico potente"],
            "betametasona": ["diprosone", "corticoide tópico"],
            # ===== OFTALMOLÓGICOS =====
            "latanoprost": ["xalatan", "análogo prostaglandina", "antiglaucoma"],
            "timolol": ["timoptic", "betabloqueador ocular"],
            "dorzolamida": ["trusopt", "inhibidor anhidrasa carbónica"],
            "brimonidina": ["alphagan", "alfa-agonista ocular"],
            "pilocarpina": ["isopto carpine", "miótico"],
            "ciclosporina_oftalmica": ["restasis", "inmunomodulador ocular"],
            "prednisolona_oftal": ["pred forte", "corticoide ocular"],
            "moxifloxacino_oftal": ["vigamox", "antibiótico ocular"],
            # ===== OTORRINOLARINGOLÓGICOS =====
            "pseudoefedrina": ["sudafed", "descongestionante"],
            "fenilefrina_nasal": ["neo-sinefrina", "descongestionante nasal"],
            "oximetazolina": ["afrin", "descongestionante nasal"],
            "fluticasona_nasal": ["flonase", "corticoide nasal"],
            "mometasona_nasal": ["nasonex", "corticoide nasal"],
            "cetirizina": ["zyrtec", "antihistamínico"],
            "loratadina": ["claritin", "antihistamínico no sedante"],
            "fexofenadina": ["allegra", "antihistamínico"],
            "difenhidramina": ["benadryl", "antihistamínico sedante"],
            # ===== GINECOLÓGICOS =====
            "medroxiprogesterona": ["provera", "progestina"],
            "etinilestradiol": ["estrógeno", "anticonceptivo"],
            "levonorgestrel": ["plan B", "anticonceptivo emergencia"],
            "clomifeno": ["clomid", "inductor ovulación"],
            "letrozol": ["femara", "inhibidor aromatasa"],
            "misoprostol": ["cytotec", "prostaglandina"],
            "dinoprostona": ["cervidil", "prostaglandina cervical"],
            "oxitocina": ["pitocin", "oxitócico"],
            # ===== REUMATOLÓGICOS =====
            "metotrexato": ["MTX", "trexall", "antimetabolito", "DMARD"],
            "hidroxicloroquina": ["plaquenil", "antimalárico", "DMARD"],
            "sulfasalazina": ["azulfidine", "DMARD"],
            "leflunomida": ["arava", "DMARD"],
            "adalimumab": ["humira", "anti-TNF", "biológico"],
            "etanercept": ["enbrel", "anti-TNF", "biológico"],
            "infliximab": ["remicade", "anti-TNF", "biológico"],
            "tocilizumab": ["actemra", "anti-IL6", "biológico"],
            "colchicina": ["colcrys", "antigotoso"],
            "alopurinol": ["zyloprim", "inhibidor xantina oxidasa"],
            "febuxostat": ["uloric", "inhibidor xantina oxidasa"],
            # ===== ANESTÉSICOS =====
            "lidocaína": ["xylocaína", "anestésico local"],
            "bupivacaína": ["marcaine", "anestésico local larga duración"],
            "ropivacaína": ["naropin", "anestésico local"],
            "propofol": ["diprivan", "anestésico IV"],
            "ketamina": ["ketalar", "anestésico disociativo"],
            "midazolam": ["versed", "benzodiazepina IV"],
            "fentanilo_anest": ["sublimaze", "opioide anestésico"],
            "rocuronio": ["zemuron", "relajante muscular"],
            "succinilcolina": ["anectine", "relajante muscular despolarizante"],
        }

    def _init_anatomy_synonyms(self):
        """Sinónimos anatómicos - EXPANDIDO"""
        self.anatomy_synonyms = {
            # ===== SISTEMA CARDIOVASCULAR =====
            "corazón": [
                "cardíaco",
                "cardiovascular",
                "miocardio",
                "pericardio",
                "cardio",
            ],
            "arterias": ["arterial", "vascular", "aorta", "arteria coronaria"],
            "venas": ["venoso", "vascular", "flebitis"],
            "sangre": ["hemático", "sanguíneo", "hematológico", "hemo"],
            # ===== SISTEMA RESPIRATORIO =====
            "pulmones": ["pulmonar", "respiratorio", "bronquios", "alvéolos", "pleura"],
            "bronquios": ["bronquial", "bronquiolar", "árbol bronquial"],
            "tráquea": ["traqueal", "vía aérea superior"],
            "laringe": ["laríngeo", "cuerdas vocales", "glotis"],
            "nariz": ["nasal", "fosas nasales", "senos paranasales"],
            # ===== SISTEMA DIGESTIVO =====
            "hígado": ["hepático", "hepato", "hepatobiliar"],
            "vesícula biliar": ["biliar", "colecisto", "vías biliares"],
            "páncreas": ["pancreático", "insulina", "páncreas exocrino"],
            "estómago": ["gástrico", "gastro", "fondo gástrico", "antro"],
            "intestino delgado": ["entérico", "duodeno", "yeyuno", "íleon"],
            "intestino grueso": ["colon", "colónico", "ciego", "recto", "sigma"],
            "esófago": ["esofágico", "cardias", "unión gastroesofágica"],
            "recto": ["rectal", "anal", "anorrectal"],
            # ===== SISTEMA URINARIO =====
            "riñones": ["renal", "nefro", "glomérulo", "túbulo renal"],
            "vejiga": ["vesical", "urinario", "cistitis"],
            "uretra": ["uretral", "meato"],
            "uréteres": ["ureteral", "pieloureteral"],
            "próstata": ["prostático", "adenoma prostático"],
            # ===== SISTEMA NERVIOSO =====
            "cerebro": ["cerebral", "encéfalo", "neurológico", "SNC", "corteza"],
            "médula espinal": ["medular", "espinal", "raquídeo"],
            "nervios": ["nervioso", "neural", "neuritis", "neuropatía"],
            "meninges": ["meníngeo", "duramadre", "aracnoides", "piamadre"],
            # ===== SISTEMA MUSCULOESQUELÉTICO =====
            "huesos": ["óseo", "esquelético", "ortopédico", "médula ósea"],
            "articulaciones": ["articular", "sinovial", "cápsula articular"],
            "músculos": ["muscular", "miopatía", "músculo esquelético"],
            "columna vertebral": [
                "vertebral",
                "espinal",
                "lumbar",
                "cervical",
                "torácica",
            ],
            "cadera": ["coxal", "coxofemoral", "acetábulo"],
            "rodilla": ["rotuliano", "menisco", "ligamento cruzado"],
            "hombro": ["escapular", "glenohumeral", "manguito rotador"],
            # ===== PIEL Y TEGUMENTOS =====
            "piel": ["cutáneo", "dérmico", "epidérmico", "tegumentario"],
            "uñas": ["ungueal", "onicomicosis"],
            "pelo": ["capilar", "folículo piloso"],
            # ===== SISTEMA ENDOCRINO =====
            "tiroides": ["tiroideo", "hormona tiroidea", "glándula tiroides"],
            "glándula suprarrenal": ["adrenal", "suprarrenal", "cortisol"],
            "hipófisis": ["pituitaria", "adenohipófisis", "neurohipófisis"],
            # ===== ÓRGANOS DE LOS SENTIDOS =====
            "ojos": ["ocular", "oftálmico", "retina", "córnea"],
            "oídos": ["ótico", "auditivo", "coclear", "vestibular"],
            # ===== OTROS =====
            "ganglios linfáticos": ["linfático", "adenopatía", "linfonodos"],
            "bazo": ["esplénico", "esplenomegalia"],
            "timo": ["tímico", "inmunológico"],
            # ===== SISTEMA REPRODUCTOR FEMENINO =====
            "útero": ["uterino", "endometrio", "miometrio", "matriz"],
            "ovarios": ["ovárico", "folículo", "cuerpo lúteo"],
            "trompas de Falopio": ["tubárico", "salpinge", "trompa uterina"],
            "vagina": ["vaginal", "canal vaginal"],
            "cuello uterino": ["cérvix", "cervical", "cervicouterino"],
            "vulva": ["vulvar", "labios mayores", "labios menores"],
            "mamas": ["mamario", "glándula mamaria", "seno"],
            # ===== SISTEMA REPRODUCTOR MASCULINO =====
            "testículos": ["testicular", "gónadas masculinas", "escroto"],
            "epidídimo": ["epididimario", "conducto espermático"],
            "conducto deferente": ["deferente", "vas deferens"],
            "vesículas seminales": ["seminal", "glándulas seminales"],
            "pene": ["peniano", "cuerpo cavernoso", "glande"],
            # ===== SISTEMA LINFÁTICO E INMUNE =====
            "médula ósea": ["hematopoyético", "mieloide", "producción sanguínea"],
            "amígdalas": ["tonsilar", "adenoides", "tejido linfoide"],
            "apéndice": ["apendicular", "apendiceal"],
            # ===== CABEZA Y CUELLO =====
            "cráneo": ["craneal", "calvaria", "base de cráneo"],
            "mandíbula": ["mandibular", "maxilar inferior"],
            "maxilar": ["maxilar superior", "palatino"],
            "órbita": ["orbitario", "cavidad orbitaria"],
            "cuello": ["cervical", "región cervical"],
            "faringe": ["faríngeo", "orofaringe", "nasofaringe", "hipofaringe"],
            # ===== TÓRAX =====
            "costillas": ["costal", "parrilla costal", "arcos costales"],
            "esternón": ["esternal", "manubrio", "xifoides"],
            "diafragma": ["diafragmático", "músculo respiratorio"],
            "mediastino": ["mediastínico", "espacio mediastinal"],
            # ===== EXTREMIDADES =====
            "mano": ["carpo", "metacarpo", "falanges"],
            "pie": ["tarso", "metatarso", "falanges del pie"],
            "codo": ["cubital", "olécranon", "epitróclea"],
            "muñeca": ["carpiano", "túnel carpiano"],
            "tobillo": ["maleolar", "articulación tibiotarsiana"],
            "fémur": ["femoral", "hueso del muslo"],
            "tibia": ["tibial", "hueso de la pierna"],
            "húmero": ["humeral", "hueso del brazo"],
        }

    def _init_procedure_synonyms(self):
        """Sinónimos de procedimientos - EXPANDIDO"""
        self.procedure_synonyms = {
            # ===== ESTUDIOS DE IMAGEN =====
            "radiografía": ["rayos X", "RX", "placa", "estudio radiológico"],
            "tomografía": [
                "TAC",
                "TC",
                "CT scan",
                "escáner",
                "tomografía computarizada",
            ],
            "resonancia magnética": [
                "RMN",
                "RM",
                "MRI",
                "resonancia",
                "estudio por resonancia",
            ],
            "ecografía": ["ultrasonido", "eco", "US", "sonografía", "USG"],
            "electrocardiograma": [
                "ECG",
                "EKG",
                "trazado cardíaco",
                "electrocardiografía",
            ],
            "ecocardiograma": [
                "eco cardíaco",
                "ecocardio",
                "ultrasonido cardíaco",
                "eco transtorácico",
            ],
            "gammagrafía": ["medicina nuclear", "estudio isotópico", "centellograma"],
            "PET-CT": ["PET", "tomografía por emisión de positrones", "estudio PET"],
            "angiografía": ["arteriografía", "venografía", "estudio vascular"],
            "doppler": ["ultrasonido doppler", "eco doppler", "flujometría"],
            "mamografía": ["mastografía", "estudio mamario"],
            "densitometría ósea": ["DEXA", "DXA", "densitometría"],
            "fluoroscopia": ["fluoroscopía", "estudio fluoroscópico"],
            # ===== LABORATORIO GENERAL =====
            "análisis de sangre": [
                "hemograma",
                "BH",
                "biometría hemática",
                "citometría hemática",
            ],
            "glucosa": [
                "glucemia",
                "azúcar en sangre",
                "glicemia",
                "glucosa en ayunas",
            ],
            "hemoglobina glicosilada": [
                "HbA1c",
                "A1C",
                "hemoglobina A1c",
                "glucosilada",
            ],
            "colesterol": [
                "perfil lipídico",
                "lípidos",
                "panel lipídico",
                "triglicéridos",
            ],
            "función renal": [
                "creatinina",
                "BUN",
                "urea",
                "depuración de creatinina",
                "tasa de filtración glomerular",
            ],
            "función hepática": [
                "transaminasas",
                "TGO",
                "TGP",
                "ALT",
                "AST",
                "pruebas hepáticas",
                "PFH",
            ],
            "electrolitos": [
                "ionograma",
                "Na",
                "K",
                "sodio",
                "potasio",
                "cloro",
                "magnesio",
            ],
            "tiempos de coagulación": [
                "TP",
                "TPT",
                "INR",
                "tiempo de protrombina",
                "tiempo de tromboplastina",
            ],
            "gasometría arterial": [
                "gases arteriales",
                "gasometría",
                "AGA",
                "pH sanguíneo",
            ],
            "pruebas tiroideas": [
                "TSH",
                "T3",
                "T4",
                "perfil tiroideo",
                "función tiroidea",
            ],
            "examen general de orina": [
                "EGO",
                "urinálisis",
                "uroanálisis",
                "análisis de orina",
            ],
            "urocultivo": ["cultivo de orina", "cultivo urinario"],
            "hemocultivo": ["cultivo de sangre", "cultivo sanguíneo"],
            "coprocultivo": ["cultivo de heces", "coproparasitoscópico"],
            "procalcitonina": ["PCT", "marcador de infección"],
            "dímero D": ["D-dímero", "productos de degradación de fibrina"],
            "troponinas": ["troponina I", "troponina T", "marcadores cardíacos"],
            "BNP": ["péptido natriurético", "proBNP", "NT-proBNP"],
            "ferritina": ["hierro sérico", "saturación de transferrina", "TIBC"],
            # ===== PROCEDIMIENTOS DIAGNÓSTICOS =====
            "biopsia": ["toma de muestra", "punción", "obtención de tejido"],
            "endoscopia": [
                "gastroscopia",
                "esofagogastroduodenoscopia",
                "EGD",
                "panendoscopia",
            ],
            "colonoscopia": ["videocolonoscopia", "estudio del colon"],
            "broncoscopia": ["fibrobroncoscopia", "endoscopia bronquial"],
            "cistoscopia": ["endoscopia vesical", "uretroscopia"],
            "laparoscopia diagnóstica": [
                "laparoscopía",
                "cirugía mínimamente invasiva diagnóstica",
            ],
            "artroscopia diagnóstica": ["artroscopía", "endoscopia articular"],
            "punción lumbar": ["PL", "rachicentesis", "estudio de LCR"],
            "toracocentesis": ["punción pleural", "drenaje pleural"],
            "paracentesis": ["punción abdominal", "drenaje ascítico"],
            "aspirado de médula ósea": ["AMO", "mielograma", "biopsia de médula"],
            # ===== PROCEDIMIENTOS CARDIOLÓGICOS =====
            "cateterismo": ["angiografía", "coronariografía", "cateterismo cardíaco"],
            "angioplastia": [
                "ICP",
                "intervención coronaria percutánea",
                "PTCA",
                "stent",
            ],
            "marcapasos": ["implante de marcapasos", "estimulación cardíaca"],
            "cardioversión": [
                "cardioversión eléctrica",
                "choque eléctrico sincronizado",
            ],
            "ablación cardíaca": [
                "ablación por radiofrecuencia",
                "ablación de arritmias",
            ],
            "ecocardiograma transesofágico": ["ETE", "eco transesofágico"],
            "holter": ["monitoreo holter", "ECG de 24 horas", "monitoreo ambulatorio"],
            "prueba de esfuerzo": [
                "ergometría",
                "test de esfuerzo",
                "prueba de estrés",
            ],
            # ===== CIRUGÍAS =====
            "cirugía": [
                "operación",
                "intervención quirúrgica",
                "procedimiento quirúrgico",
            ],
            "apendicectomía": [
                "extirpación de apéndice",
                "apendicectomía laparoscópica",
            ],
            "colecistectomía": [
                "extirpación de vesícula",
                "colecistectomía laparoscópica",
            ],
            "herniorrafia": ["reparación de hernia", "plastía de hernia"],
            "laparotomía": ["laparotomía exploradora", "cirugía abdominal abierta"],
            "toracotomía": ["cirugía torácica abierta"],
            "craneotomía": ["cirugía craneal", "apertura de cráneo"],
            "bypass coronario": [
                "CABG",
                "revascularización coronaria",
                "puentes coronarios",
            ],
            "reemplazo valvular": ["cambio de válvula", "prótesis valvular"],
            "nefrectomía": ["extirpación de riñón", "nefrectomía parcial"],
            "gastrectomía": ["resección gástrica", "cirugía de estómago"],
            "tiroidectomía": ["extirpación de tiroides", "tiroidectomía total/parcial"],
            # ===== PROCEDIMIENTOS DE URGENCIA =====
            "intubación": ["intubación orotraqueal", "IOT", "manejo de vía aérea"],
            "RCP": ["reanimación cardiopulmonar", "resucitación", "maniobras de RCP"],
            "desfibrilación": ["choque eléctrico", "desfibrilador"],
            "ventilación mecánica": ["VM", "soporte ventilatorio", "respirador"],
            "traqueostomía": ["traqueotomía", "vía aérea quirúrgica"],
            "drenaje torácico": ["sello de agua", "tubo de tórax", "pleurostomía"],
            "línea central": ["catéter venoso central", "CVC", "vía central"],
            "línea arterial": ["catéter arterial", "monitoreo invasivo"],
            # ===== PROCEDIMIENTOS NEUROLÓGICOS =====
            "electroencefalograma": ["EEG", "estudio de ondas cerebrales"],
            "electromiografía": ["EMG", "estudio de conducción nerviosa"],
            "potenciales evocados": ["PE", "estudio de potenciales"],
            # ===== PROCEDIMIENTOS OFTALMOLÓGICOS =====
            "facoemulsificación": ["cirugía de catarata", "extracción de catarata"],
            "trabeculectomía": ["cirugía de glaucoma", "filtración glaucoma"],
            "vitrectomía": ["cirugía vítrea", "vitrectomía posterior"],
            "fotocoagulación láser": ["láser retiniano", "panfotocoagulación"],
            "inyección intravítrea": ["anti-VEGF intravítreo", "inyección ocular"],
            "LASIK": ["cirugía refractiva", "corrección láser"],
            "crosslinking corneal": ["CXL", "entrecruzamiento corneal"],
            # ===== PROCEDIMIENTOS GINECOLÓGICOS =====
            "histerectomía": ["extirpación de útero", "histerectomía total/subtotal"],
            "ooforectomía": ["extirpación de ovario", "ovariectomía"],
            "cesárea": ["operación cesárea", "parto por cesárea"],
            "legrado uterino": ["curetaje", "LUI", "AMEU"],
            "colposcopia": ["examen colposcópico", "biopsia cervical"],
            "histeroscopia": ["endoscopia uterina", "cirugía histeroscópica"],
            "laparoscopia ginecológica": ["cirugía laparoscópica pélvica"],
            "miomectomía": ["extirpación de miomas", "cirugía de fibromas"],
            "conización": ["cono cervical", "LEEP", "escisión electroquirúrgica"],
            # ===== PROCEDIMIENTOS UROLÓGICOS =====
            "cistoscopia": ["endoscopia vesical", "uretrocistoscopia"],
            "prostatectomía": ["extirpación de próstata", "RTU prostática"],
            "litotricia": ["LEOC", "fragmentación de cálculos"],
            "nefrostomía": ["drenaje renal percutáneo"],
            "ureteroscopia": ["endoscopia ureteral", "URS"],
            "orquidectomía": ["extirpación testicular", "orquiectomía"],
            "vasectomía": ["esterilización masculina", "ligadura de deferentes"],
            "circuncisión": ["postectomía", "fimosis cirugía"],
            # ===== PROCEDIMIENTOS ORTOPÉDICOS =====
            "artroscopia": ["cirugía artroscópica", "endoscopia articular"],
            "artroplastia": ["reemplazo articular", "prótesis articular"],
            "osteosíntesis": ["fijación de fractura", "reducción abierta"],
            "artrodesis": ["fusión articular", "fijación espinal"],
            "discectomía": ["extirpación de disco", "cirugía de hernia discal"],
            "laminectomía": ["descompresión espinal", "cirugía de estenosis"],
            "meniscectomía": ["resección de menisco", "cirugía de menisco"],
            "ligamentoplastia": ["reconstrucción de ligamento", "LCA cirugía"],
            # ===== PROCEDIMIENTOS DERMATOLÓGICOS =====
            "biopsia de piel": ["biopsia cutánea", "punch biopsia"],
            "escisión de lesión": ["extirpación de lesión", "resección cutánea"],
            "curetaje y electrofulguración": ["C y E", "electrodesecación"],
            "crioterapia": ["criocirugía", "congelación con nitrógeno"],
            "dermoabrasión": ["microdermoabrasión", "rejuvenecimiento"],
            "injerto de piel": ["autoinjerto", "injerto cutáneo"],
            # ===== PROCEDIMIENTOS ONCOLÓGICOS =====
            "quimioterapia": ["QT", "tratamiento quimioterápico", "ciclo de QT"],
            "radioterapia": ["RT", "tratamiento con radiación", "irradiación"],
            "braquiterapia": ["radioterapia interna", "semillas radioactivas"],
            "inmunoterapia": ["IO", "inhibidores checkpoint", "terapia biológica"],
            "terapia dirigida": ["terapia molecular", "inhibidores de tirosina kinasa"],
            "trasplante de médula ósea": ["TMO", "trasplante de células madre", "TCPH"],
        }

    def _init_abbreviations(self):
        """Abreviaciones médicas comunes - EXPANDIDO"""
        self.abbreviations = {
            # ===== DIAGNÓSTICOS =====
            "IAM": "infarto agudo de miocardio",
            "IAMCEST": "infarto agudo de miocardio con elevación ST",
            "IAMSEST": "infarto agudo de miocardio sin elevación ST",
            "ACV": "accidente cerebrovascular",
            "EVC": "evento vascular cerebral",
            "HTA": "hipertensión arterial",
            "DM": "diabetes mellitus",
            "DM1": "diabetes mellitus tipo 1",
            "DM2": "diabetes mellitus tipo 2",
            "IC": "insuficiencia cardíaca",
            "ICC": "insuficiencia cardíaca congestiva",
            "ICFEr": "insuficiencia cardíaca con fracción de eyección reducida",
            "ICFEp": "insuficiencia cardíaca con fracción de eyección preservada",
            "IRC": "insuficiencia renal crónica",
            "ERC": "enfermedad renal crónica",
            "IRA": "insuficiencia renal aguda",
            "LRA": "lesión renal aguda",
            "EPOC": "enfermedad pulmonar obstructiva crónica",
            "TVP": "trombosis venosa profunda",
            "TEP": "tromboembolismo pulmonar",
            "SCA": "síndrome coronario agudo",
            "FA": "fibrilación auricular",
            "FEVI": "fracción de eyección ventricular izquierda",
            "NAC": "neumonía adquirida en comunidad",
            "NIH": "neumonía intrahospitalaria",
            "NAVM": "neumonía asociada a ventilación mecánica",
            "ITU": "infección del tracto urinario",
            "IVU": "infección de vías urinarias",
            "EII": "enfermedad inflamatoria intestinal",
            "ERGE": "enfermedad por reflujo gastroesofágico",
            "HDA": "hemorragia digestiva alta",
            "HDB": "hemorragia digestiva baja",
            "CAD": "cetoacidosis diabética",
            "EHH": "estado hiperosmolar hiperglucémico",
            "SDRA": "síndrome de distrés respiratorio agudo",
            "SRIS": "síndrome de respuesta inflamatoria sistémica",
            "SIRS": "síndrome de respuesta inflamatoria sistémica",
            "TEV": "tromboembolismo venoso",
            "EM": "esclerosis múltiple",
            "EP": "enfermedad de Parkinson",
            "EA": "enfermedad de Alzheimer",
            "AR": "artritis reumatoide",
            "LES": "lupus eritematoso sistémico",
            "VIH": "virus de inmunodeficiencia humana",
            "SIDA": "síndrome de inmunodeficiencia adquirida",
            # ===== ESTUDIOS DIAGNÓSTICOS =====
            "ECG": "electrocardiograma",
            "EKG": "electrocardiograma",
            "TAC": "tomografía axial computarizada",
            "TC": "tomografía computarizada",
            "RMN": "resonancia magnética nuclear",
            "RM": "resonancia magnética",
            "RX": "radiografía",
            "US": "ultrasonido",
            "ECO": "ecocardiograma",
            "ETT": "ecocardiograma transtorácico",
            "ETE": "ecocardiograma transesofágico",
            "BH": "biometría hemática",
            "HC": "hemograma completo",
            "QS": "química sanguínea",
            "PFH": "pruebas de función hepática",
            "PFR": "pruebas de función renal",
            "PFT": "pruebas de función tiroidea",
            "EGO": "examen general de orina",
            "TP": "tiempo de protrombina",
            "TTP": "tiempo de tromboplastina parcial",
            "INR": "índice normalizado internacional",
            "BNP": "péptido natriurético cerebral",
            "PCR": "proteína C reactiva",
            "VSG": "velocidad de sedimentación globular",
            "HbA1c": "hemoglobina glucosilada",
            "LDL": "lipoproteína de baja densidad",
            "HDL": "lipoproteína de alta densidad",
            "TG": "triglicéridos",
            "TSH": "hormona estimulante de tiroides",
            "T4L": "tiroxina libre",
            "PSA": "antígeno prostático específico",
            "EEG": "electroencefalograma",
            "EMG": "electromiografía",
            "PL": "punción lumbar",
            "LCR": "líquido cefalorraquídeo",
            "GS": "gases sanguíneos",
            "GSA": "gasometría arterial",
            # ===== TRATAMIENTO Y VÍAS =====
            "VO": "vía oral",
            "IV": "intravenoso",
            "IM": "intramuscular",
            "SC": "subcutáneo",
            "SL": "sublingual",
            "ID": "intradérmico",
            "PR": "por recto",
            "INH": "inhalado",
            "TOP": "tópico",
            "PRN": "según sea necesario",
            "BID": "dos veces al día",
            "TID": "tres veces al día",
            "QID": "cuatro veces al día",
            "QD": "una vez al día",
            "QOD": "cada otro día",
            "HS": "hora de sueño",
            "AC": "antes de comidas",
            "PC": "después de comidas",
            "STAT": "inmediatamente",
            "SOS": "si es necesario",
            "NPO": "nada por boca",
            "SF": "solución fisiológica",
            "SG": "solución glucosada",
            "SSN": "solución salina normal",
            # ===== SIGNOS VITALES =====
            "PA": "presión arterial",
            "PAS": "presión arterial sistólica",
            "PAD": "presión arterial diastólica",
            "PAM": "presión arterial media",
            "FC": "frecuencia cardíaca",
            "FR": "frecuencia respiratoria",
            "T°": "temperatura",
            "SpO2": "saturación de oxígeno",
            "SatO2": "saturación de oxígeno",
            "TA": "tensión arterial",
            "GC": "gasto cardíaco",
            "PVC": "presión venosa central",
            # ===== SERVICIOS Y UNIDADES =====
            "UCI": "unidad de cuidados intensivos",
            "UTI": "unidad de terapia intensiva",
            "UCIC": "unidad de cuidados intensivos coronarios",
            "URG": "urgencias",
            "SU": "servicio de urgencias",
            "QX": "quirófano",
            "CE": "consulta externa",
            "HOS": "hospitalización",
            # ===== OTROS ACRÓNIMOS CLÍNICOS =====
            "Dx": "diagnóstico",
            "DDx": "diagnóstico diferencial",
            "Tx": "tratamiento",
            "Rx": "prescripción",
            "Hx": "historia",
            "Sx": "síntomas",
            "Px": "pronóstico",
            "Fx": "fractura",
            "Ax": "axilar",
            "CX": "cirugía",
            "AHF": "antecedentes heredofamiliares",
            "APP": "antecedentes personales patológicos",
            "APNP": "antecedentes personales no patológicos",
            "AGO": "antecedentes ginecoobstétricos",
            "EF": "exploración física",
            "PA": "padecimiento actual",
            "MC": "motivo de consulta",
            "SOFA": "sequential organ failure assessment",
            "GCS": "escala de coma de Glasgow",
            "NIHSS": "national institutes of health stroke scale",
            "APACHE": "acute physiology and chronic health evaluation",
            "CURB-65": "confusion urea respiratory rate blood pressure 65",
            "CHADS2": "congestive heart failure hypertension age diabetes stroke",
            "MELD": "model for end-stage liver disease",
            "CHILD": "child-turcotte-pugh score",
            # ===== ABREVIATURAS DE ESPECIALIDADES =====
            "ORL": "otorrinolaringología",
            "OFT": "oftalmología",
            "URO": "urología",
            "GI": "gastroenterología",
            "NEURO": "neurología",
            "CARDIO": "cardiología",
            "ONCO": "oncología",
            "HEMA": "hematología",
            "REUM": "reumatología",
            "NEFRO": "nefrología",
            "ENDO": "endocrinología",
            "DERM": "dermatología",
            "TRAUMA": "traumatología",
            "PSIQ": "psiquiatría",
            "ANEST": "anestesiología",
            "UCI": "unidad de cuidados intensivos",
            "UCIN": "unidad de cuidados intensivos neonatales",
            "UCIP": "unidad de cuidados intensivos pediátricos",
            "SU": "sala de urgencias",
            "QX": "quirófano",
            # ===== ABREVIATURAS DE MEDICACIÓN =====
            "VO": "vía oral",
            "IV": "intravenoso",
            "IM": "intramuscular",
            "SC": "subcutáneo",
            "SL": "sublingual",
            "TD": "transdérmico",
            "TOP": "tópico",
            "INH": "inhalado",
            "NEB": "nebulización",
            "PRN": "según necesidad (pro re nata)",
            "QD": "una vez al día",
            "BID": "dos veces al día",
            "TID": "tres veces al día",
            "QID": "cuatro veces al día",
            "QHS": "al acostarse",
            "AC": "antes de las comidas",
            "PC": "después de las comidas",
            "STAT": "inmediatamente",
            "NPO": "nada por vía oral",
            "SOS": "si es necesario",
            # ===== ABREVIATURAS DE SIGNOS VITALES =====
            "TA": "tensión arterial",
            "TAS": "tensión arterial sistólica",
            "TAD": "tensión arterial diastólica",
            "TAM": "tensión arterial media",
            "FC": "frecuencia cardíaca",
            "FR": "frecuencia respiratoria",
            "SpO2": "saturación de oxígeno",
            "FiO2": "fracción inspirada de oxígeno",
            "GC": "gasto cardíaco",
            "PVC": "presión venosa central",
            "PIC": "presión intracraneal",
            "PCP": "presión capilar pulmonar",
            # ===== ABREVIATURAS DE ESCALAS Y SCORES =====
            "EVA": "escala visual análoga",
            "NRS": "numerical rating scale",
            "MMSE": "mini mental state examination",
            "MoCA": "montreal cognitive assessment",
            "APGAR": "appearance pulse grimace activity respiration",
            "BISHOP": "score de bishop cervical",
            "ASA": "american society of anesthesiologists score",
            "TNM": "tumor nódulo metástasis",
            "NYHA": "new york heart association",
            "CCS": "canadian cardiovascular society",
            "EDSS": "expanded disability status scale",
        }

    def _init_colloquial_to_medical(self):
        """Mapeo de términos coloquiales a médicos"""
        self.colloquial_to_medical = {
            # Síntomas coloquiales
            "me duele la cabeza": "cefalea",
            "me duele el pecho": "dolor torácico",
            "me falta el aire": "disnea",
            "no puedo respirar": "dificultad respiratoria severa",
            "me late rápido el corazón": "taquicardia",
            "se me duerme la mano": "parestesia en extremidad superior",
            "veo borroso": "alteración visual",
            "me zumban los oídos": "tinnitus",
            "tengo calentura": "fiebre",
            "estoy hinchado": "edema",
            "me pica": "prurito",
            "no puedo dormir": "insomnio",
            "estoy muy cansado": "astenia",
            # Condiciones coloquiales
            "ataque al corazón": "infarto agudo de miocardio",
            "derrame cerebral": "accidente cerebrovascular",
            "presión alta": "hipertensión arterial",
            "azúcar alta": "hiperglucemia",
            "colesterol alto": "hiperlipidemia",
            "piedras en el riñón": "nefrolitiasis",
            "piedras en la vesícula": "colelitiasis",
            "hernia de disco": "hernia discal",
            # Términos de medicamentos coloquiales
            "pastillas para la presión": "antihipertensivos",
            "pastillas para el azúcar": "antidiabéticos orales",
            "pastillas para dormir": "hipnóticos",
            "pastillas para la ansiedad": "ansiolíticos",
            "antibióticos": "antimicrobianos",
            # ===== SÍNTOMAS COLOQUIALES ADICIONALES =====
            "me arde al orinar": "disuria",
            "orino mucho": "poliuria",
            "orino poco": "oliguria",
            "no puedo orinar": "retención urinaria",
            "tengo ganas de vomitar": "náuseas",
            "vomité sangre": "hematemesis",
            "sangro por la nariz": "epistaxis",
            "me sangran las encías": "gingivorragia",
            "me sale sangre en la orina": "hematuria",
            "hago popó negro": "melena",
            "hago popó con sangre": "rectorragia",
            "estoy amarillo": "ictericia",
            "me tiemblan las manos": "temblor en extremidades",
            "me mareo": "vértigo",
            "siento que me desmayo": "presíncope",
            "me desmayé": "síncope",
            "se me cae el pelo": "alopecia",
            "me duele la barriga": "dolor abdominal",
            "me duele la espalda": "lumbalgia",
            "me duele el cuello": "cervicalgia",
            "me duele la rodilla": "gonalgia",
            "me duele el hombro": "omalgia",
            "me duele la muñeca": "dolor en muñeca",
            "me duele el tobillo": "dolor en tobillo",
            "tengo los ojos rojos": "hiperemia conjuntival",
            "me lloran los ojos": "epífora",
            "no escucho bien": "hipoacusia",
            "me tapo de la nariz": "congestión nasal",
            "tengo mocos": "rinorrea",
            "estornudo mucho": "estornudos frecuentes",
            "me pica la garganta": "faringitis",
            "me duele al tragar": "odinofagia",
            "tengo agruras": "pirosis",
            "me siento lleno": "plenitud postprandial",
            "tengo gases": "flatulencia",
            "estoy estreñido": "constipación",
            "tengo diarrea": "deposiciones líquidas",
            "me da comezón": "prurito generalizado",
            "me salió un sarpullido": "exantema",
            "me salieron ronchas": "urticaria",
            "tengo granos": "acné",
            "me duelen los huesos": "artralgias",
            "me duelen los músculos": "mialgias",
            "me siento débil": "debilidad generalizada",
            "no tengo hambre": "hiporexia",
            "tengo mucha hambre": "polifagia",
            "tengo mucha sed": "polidipsia",
            "subí de peso": "aumento de peso",
            "bajé de peso": "pérdida de peso",
            "sudo mucho": "hiperhidrosis",
            "no sudo": "anhidrosis",
            "me duele la cabeza de un lado": "hemicránea",
            "veo lucecitas": "fotopsias",
            "veo manchas": "miodesopsias",
            # ===== CONDICIONES COLOQUIALES ADICIONALES =====
            "tengo azúcar": "diabetes mellitus",
            "me dio un infarto": "infarto de miocardio",
            "me dio una embolia": "accidente cerebrovascular",
            "tengo la tiroides alta": "hipertiroidismo",
            "tengo la tiroides baja": "hipotiroidismo",
            "tengo el ácido úrico alto": "hiperuricemia",
            "tengo gota": "artritis gotosa",
            "tengo anemia": "anemia",
            "me da asma": "asma bronquial",
            "tengo alergia": "reacción alérgica",
            "soy alérgico": "antecedente de alergia",
            "me da migraña": "migraña",
            "tengo epilepsia": "epilepsia",
            "me dan convulsiones": "crisis convulsivas",
            "tengo artritis": "artritis",
            "tengo artrosis": "osteoartritis",
            "tengo varices": "insuficiencia venosa",
            "tengo hemorroides": "enfermedad hemorroidal",
            "tengo gastritis": "gastritis",
            "tengo úlcera": "enfermedad ulcerosa péptica",
            "tengo reflujo": "enfermedad por reflujo gastroesofágico",
            "tengo hernia": "hernia",
            "tengo quiste": "lesión quística",
            "tengo tumor": "neoplasia",
            "me operaron del apéndice": "antecedente de apendicectomía",
            "me operaron de la vesícula": "antecedente de colecistectomía",
            "me operaron del corazón": "antecedente de cirugía cardíaca",
        }

    def _init_emergency_terms(self):
        """Términos que indican emergencia médica"""
        self.emergency_indicators = {
            # Síntomas de emergencia
            "dolor de pecho severo": ["posible infarto", "síndrome coronario agudo"],
            "dificultad respiratoria severa": [
                "insuficiencia respiratoria",
                "emergencia",
            ],
            "pérdida de conciencia": ["síncope", "posible ACV", "emergencia"],
            "debilidad súbita de un lado": ["posible ACV", "código ictus"],
            "dificultad para hablar súbita": ["posible ACV", "afasia aguda"],
            "convulsiones prolongadas": ["estado epiléptico", "emergencia"],
            "sangrado abundante": ["hemorragia", "shock hipovolémico posible"],
            "dolor abdominal severo": [
                "abdomen agudo",
                "posible emergencia quirúrgica",
            ],
            "fiebre muy alta": ["hiperpirexia", "posible sepsis"],
            "reacción alérgica severa": ["anafilaxia", "emergencia"],
        }

        # Palabras clave de emergencia
        self.emergency_keywords = [
            # Respiratorio
            "no puedo respirar",
            "dificultad para respirar",
            "me ahogo",
            "asfixia",
            "cianosis",
            "labios morados",
            "me falta el aire",
            "falta de aire",
            "me falta aire",
            "no me entra el aire",
            # Cardiovascular
            "infarto",
            "paro cardíaco",
            "arritmia grave",
            "dolor de pecho muy fuerte",
            "taquicardia extrema",
            "me duele el pecho",
            "dolor de pecho",
            "dolor en el pecho",
            "opresión en el pecho",
            "me aprieta el pecho",
            # Neurológico
            "derrame",
            "convulsión",
            "convulsiones",
            "estado epiléptico",
            "desmayo",
            "pérdida de conocimiento",
            "inconsciencia",
            "inconsciente",
            "parálisis súbita",
            "no puede hablar",
            "confusión aguda",
            "peor dolor de mi vida",
            "el peor dolor",
            "dolor más fuerte que he tenido",
            "cefalea súbita",
            "dolor de cabeza súbito",
            "rigidez de nuca",
            # Trauma/Shock
            "sangre",
            "sangrado abundante",
            "hemorragia",
            "shock",
            "trauma grave",
            "accidente grave",
            # Otros
            "envenenamiento",
            "sobredosis",
            "intoxicación",
            "reacción alérgica severa",
            "anafilaxia",
            "fiebre muy alta",
            "sepsis",
            # Expresiones de urgencia
            "me estoy muriendo",
            "urgente",
            "grave",
            "severo",
            "muy fuerte",
            "insoportable",
            "me voy a morir",
            # ===== EMERGENCIAS CARDIOVASCULARES ADICIONALES =====
            "dolor torácico opresivo",
            "dolor precordial",
            "síndrome coronario",
            "fibrilación ventricular",
            "taquicardia ventricular",
            "paro cardiorrespiratorio",
            "bradicardia severa",
            "taponamiento cardíaco",
            "disección aórtica",
            "tromboembolismo pulmonar",
            "embolia pulmonar",
            # ===== EMERGENCIAS NEUROLÓGICAS ADICIONALES =====
            "accidente cerebrovascular",
            "ictus",
            "código ictus",
            "hemorragia cerebral",
            "hematoma subdural",
            "hematoma epidural",
            "meningitis",
            "encefalitis",
            "hipertensión intracraneal",
            "herniación cerebral",
            "status epilepticus",
            # ===== EMERGENCIAS RESPIRATORIAS ADICIONALES =====
            "insuficiencia respiratoria aguda",
            "edema pulmonar agudo",
            "neumotórax a tensión",
            "hemotórax",
            "obstrucción de vía aérea",
            "broncoespasmo severo",
            "crisis asmática severa",
            "SDRA",
            "síndrome de distrés respiratorio",
            # ===== EMERGENCIAS ABDOMINALES =====
            "abdomen agudo",
            "peritonitis",
            "perforación intestinal",
            "isquemia mesentérica",
            "obstrucción intestinal",
            "hemorragia digestiva alta",
            "hemorragia digestiva baja",
            "rotura de aneurisma",
            "pancreatitis severa",
            # ===== EMERGENCIAS OBSTÉTRICAS =====
            "eclampsia",
            "preeclampsia severa",
            "desprendimiento de placenta",
            "hemorragia postparto",
            "rotura uterina",
            "sufrimiento fetal",
            "prolapso de cordón",
            # ===== EMERGENCIAS METABÓLICAS =====
            "cetoacidosis diabética",
            "coma hiperosmolar",
            "hipoglucemia severa",
            "crisis addisoniana",
            "tormenta tiroidea",
            "crisis hipercalcémica",
            # ===== EMERGENCIAS PEDIÁTRICAS =====
            "epiglotitis",
            "croup severo",
            "bronquiolitis severa",
            "deshidratación severa",
            "intususcepción",
            "maltrato infantil",
            # ===== TRAUMA Y SHOCK =====
            "politraumatismo",
            "trauma craneoencefálico",
            "lesión medular",
            "amputación traumática",
            "quemadura grave",
            "shock séptico",
            "shock cardiogénico",
            "shock anafiláctico",
            "shock hemorrágico",
            "shock hipovolémico",
            # ===== VARIANTES CONJUGADAS COMUNES =====
            "me desmayé",
            "se desmayó",
            "desmayarse",
            "me caí",
            "perdí el conocimiento",
            "perdió el conocimiento",
            "me sangra",
            "sangra mucho",
            "sangrando",
            "me corté",
            "herida abierta",
            "herida profunda",
            "me quemé",
            "me ahogo",
            "se ahoga",
            "ahogándose",
            "me asfixio",
            "no respira",
            "dejó de respirar",
            "vomitando sangre",
            "vomité sangre",
            "orinando sangre",
            "convulsionando",
            "está convulsionando",
            "tuvo convulsiones",
        ]

    def expand_query(self, query: str, max_expansions: int = 3) -> List[str]:
        """
        Expande una query con sinónimos médicos.

        Args:
            query: Query original
            max_expansions: Máximo número de expansiones

        Returns:
            Lista de queries expandidas (incluyendo original)
        """
        queries = [query]
        query_lower = query.lower()

        # Buscar en todos los diccionarios de sinónimos
        all_synonyms = [
            self.symptom_synonyms,
            self.condition_synonyms,
            self.drug_synonyms,
            self.anatomy_synonyms,
            self.procedure_synonyms,
        ]

        for synonym_dict in all_synonyms:
            for term, synonyms in synonym_dict.items():
                # Usar regex para matching de palabras/frases completas
                pattern = r"\b" + re.escape(term) + r"\b"
                if re.search(pattern, query_lower):
                    # Añadir expansiones con sinónimos
                    for syn in synonyms[:2]:  # Máximo 2 sinónimos por término
                        expanded = re.sub(pattern, syn, query_lower)
                        if expanded not in queries and expanded != query_lower:
                            queries.append(expanded)
                            if len(queries) >= max_expansions + 1:
                                return queries

                # También buscar si algún sinónimo está en la query
                for syn in synonyms:
                    syn_pattern = r"\b" + re.escape(syn.lower()) + r"\b"
                    if re.search(syn_pattern, query_lower):
                        expanded = re.sub(syn_pattern, term, query_lower)
                        if expanded not in queries and expanded != query_lower:
                            queries.append(expanded)
                            if len(queries) >= max_expansions + 1:
                                return queries

        # Expandir abreviaciones (matching exacto de palabra)
        for abbrev, full in self.abbreviations.items():
            abbrev_pattern = r"\b" + re.escape(abbrev) + r"\b"
            if re.search(abbrev_pattern, query, re.IGNORECASE):
                expanded = re.sub(abbrev_pattern, full, query, flags=re.IGNORECASE)
                if expanded not in queries:
                    queries.append(expanded)

        return queries[: max_expansions + 1]

    def normalize_to_medical(self, text: str) -> str:
        """
        Normaliza texto coloquial a terminología médica.

        Args:
            text: Texto con posibles términos coloquiales

        Returns:
            Texto con términos médicos normalizados
        """
        result = text.lower()

        for colloquial, medical in self.colloquial_to_medical.items():
            if colloquial in result:
                result = result.replace(colloquial, medical)

        return result

    def expand_abbreviations(self, text: str) -> str:
        """
        Expande abreviaciones médicas en el texto.

        Args:
            text: Texto con posibles abreviaciones

        Returns:
            Texto con abreviaciones expandidas
        """
        result = text

        for abbrev, full in self.abbreviations.items():
            # Buscar abreviación como palabra completa
            pattern = r"\b" + re.escape(abbrev) + r"\b"
            result = re.sub(pattern, f"{abbrev} ({full})", result)

        return result

    def get_synonyms(self, term: str) -> List[str]:
        """
        Obtiene todos los sinónimos de un término.

        Args:
            term: Término médico

        Returns:
            Lista de sinónimos
        """
        term_lower = term.lower()
        synonyms = set()

        # Buscar en todos los diccionarios
        all_dicts = [
            self.symptom_synonyms,
            self.condition_synonyms,
            self.drug_synonyms,
            self.anatomy_synonyms,
            self.procedure_synonyms,
        ]

        for d in all_dicts:
            if term_lower in d:
                synonyms.update(d[term_lower])

            # Buscar si el término es un sinónimo
            for key, values in d.items():
                if term_lower in [v.lower() for v in values]:
                    synonyms.add(key)
                    synonyms.update(values)

        # Remover el término original si está
        synonyms.discard(term_lower)
        synonyms.discard(term)

        return list(synonyms)

    def is_emergency(self, text: str) -> Tuple[bool, List[str]]:
        """
        Detecta si el texto indica una emergencia médica.

        Args:
            text: Texto a analizar

        Returns:
            Tuple de (es_emergencia, razones)
        """
        text_lower = text.lower()
        reasons = []

        # Buscar palabras clave de emergencia
        for keyword in self.emergency_keywords:
            if keyword in text_lower:
                reasons.append(f"Palabra clave: '{keyword}'")

        # Buscar patrones de emergencia
        for pattern, implications in self.emergency_indicators.items():
            if pattern in text_lower:
                reasons.extend(implications)

        return (len(reasons) > 0, reasons)

    def get_related_icd10(self, term: str) -> List[str]:
        """
        Obtiene códigos ICD-10 relacionados con un término.
        Mapeo básico sin base de datos externa.
        """
        icd10_map = {
            "infarto": ["I21", "I22"],
            "hipertensión": ["I10", "I11", "I12", "I13"],
            "diabetes": ["E10", "E11", "E13", "E14"],
            "neumonía": ["J12", "J13", "J14", "J15", "J18"],
            "asma": ["J45", "J46"],
            "ACV": ["I60", "I61", "I62", "I63", "I64"],
            "anemia": ["D50", "D51", "D52", "D53"],
            "artritis": ["M05", "M06", "M13"],
        }

        term_lower = term.lower()
        for key, codes in icd10_map.items():
            if key in term_lower:
                return codes

        return []


# ============================================================================
# TESTS
# ============================================================================


def test_ontology():
    """Test del sistema de ontologías"""

    print("🧪 TESTING MEDICAL ONTOLOGY")
    print("=" * 60)

    ontology = MedicalOntology()

    # Test 1: Expansión de query
    print("\n🔍 TEST 1: Expansión de queries")
    print("-" * 40)

    test_queries = [
        "dolor de cabeza intenso",
        "me duele el pecho",
        "paciente con HTA y DM2",
        "infarto agudo",
    ]

    for query in test_queries:
        expansions = ontology.expand_query(query)
        print(f"\n  Query: '{query}'")
        print(f"  Expansiones: {expansions}")

    # Test 2: Normalización coloquial
    print("\n🔍 TEST 2: Normalización coloquial → médico")
    print("-" * 40)

    colloquial_texts = [
        "me duele la cabeza y me falta el aire",
        "tengo calentura y estoy muy cansado",
        "me late rápido el corazón",
    ]

    for text in colloquial_texts:
        normalized = ontology.normalize_to_medical(text)
        print(f"\n  Coloquial: '{text}'")
        print(f"  Médico: '{normalized}'")

    # Test 3: Detección de emergencias
    print("\n🔍 TEST 3: Detección de emergencias")
    print("-" * 40)

    emergency_texts = [
        "dolor de pecho muy fuerte y no puedo respirar",
        "me duele un poco la cabeza",
        "pérdida de conciencia súbita",
        "tengo gripe leve",
    ]

    for text in emergency_texts:
        is_emerg, reasons = ontology.is_emergency(text)
        print(f"\n  Texto: '{text}'")
        print(f"  Emergencia: {'SÍ' if is_emerg else 'NO'}")
        if reasons:
            print(f"  Razones: {reasons[:3]}")

    # Test 4: Obtener sinónimos
    print("\n🔍 TEST 4: Obtener sinónimos")
    print("-" * 40)

    terms = ["infarto", "disnea", "aspirina", "corazón"]

    for term in terms:
        synonyms = ontology.get_synonyms(term)
        print(f"\n  Término: '{term}'")
        print(f"  Sinónimos: {synonyms[:5]}")

    print("\n✅ Tests de ontología completados")
    return True


if __name__ == "__main__":
    test_ontology()
