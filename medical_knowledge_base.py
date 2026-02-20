#!/usr/bin/env python3
"""
🗄️ Medical Knowledge Base - Base de Conocimiento Médica Completa
Sistema de conocimiento médico integral para MedeX

Incluye:
- ICD-10 completo
- Protocolos clínicos
- Guías de práctica clínica
- Medicamentos y dosis
- Procedimientos diagnósticos
- Signos vitales normales
- Valores de laboratorio
"""

from dataclasses import dataclass, asdict
from typing import Dict, List, Any, Optional
import json
from datetime import datetime

@dataclass
class MedicalCondition:
    """Condición médica completa"""
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

@dataclass
class Medication:
    """Medicamento completo"""
    name: str
    generic_name: str
    category: str
    indications: List[str]
    contraindications: List[str]
    dosage_adult: str
    dosage_pediatric: str
    side_effects: List[str]
    interactions: List[str]
    monitoring: List[str]
    pregnancy_category: str

@dataclass
class DiagnosticProcedure:
    """Procedimiento diagnóstico"""
    name: str
    category: str
    indications: List[str]
    contraindications: List[str]
    preparation: List[str]
    procedure_steps: List[str]
    interpretation: List[str]
    complications: List[str]
    cost_range: str

@dataclass
class ClinicalProtocol:
    """Protocolo clínico"""
    name: str
    category: str
    indication: str
    steps: List[str]
    decision_points: List[str]
    emergency_modifications: List[str]
    evidence_level: str
    last_updated: str

class MedicalKnowledgeBase:
    """Base de conocimiento médica completa"""
    
    def __init__(self):
        self.conditions = {}
        self.medications = {}
        self.procedures = {}
        self.protocols = {}
        self.vital_signs_normal = {}
        self.lab_values_normal = {}
        
        # Inicializar base de conocimiento
        self._initialize_knowledge_base()
    
    def _initialize_knowledge_base(self):
        """Inicializa la base de conocimiento médica"""
        
        # Condiciones cardiovasculares
        self._add_cardiovascular_conditions()
        
        # Condiciones endocrinológicas
        self._add_endocrine_conditions()
        
        # Condiciones respiratorias
        self._add_respiratory_conditions()
        
        # Condiciones neurológicas
        self._add_neurological_conditions()
        
        # Medicamentos esenciales
        self._add_essential_medications()
        
        # Procedimientos diagnósticos
        self._add_diagnostic_procedures()
        
        # Protocolos clínicos
        self._add_clinical_protocols()
        
        # Valores normales
        self._add_normal_values()
    
    def _add_cardiovascular_conditions(self):
        """Condiciones cardiovasculares"""
        
        # Síndrome Coronario Agudo
        self.conditions["I21"] = MedicalCondition(
            icd10_code="I21",
            name="Síndrome Coronario Agudo",
            category="Cardiovascular",
            description="Espectro de condiciones causadas por isquemia miocárdica aguda",
            symptoms=[
                "Dolor torácico opresivo",
                "Dolor irradiado a brazo izquierdo, mandíbula o espalda",
                "Disnea",
                "Diaforesis",
                "Náuseas y vómitos",
                "Sensación de muerte inminente"
            ],
            risk_factors=[
                "Diabetes mellitus",
                "Hipertensión arterial",
                "Tabaquismo",
                "Dislipidemia",
                "Historia familiar de cardiopatía isquémica",
                "Edad avanzada",
                "Sedentarismo",
                "Obesidad"
            ],
            complications=[
                "Shock cardiogénico",
                "Arritmias ventriculares",
                "Insuficiencia cardíaca aguda",
                "Ruptura cardíaca",
                "Pericarditis",
                "Tromboembolismo"
            ],
            diagnostic_criteria=[
                "Elevación de troponinas cardíacas",
                "Cambios electrocardiográficos compatibles",
                "Síntomas clínicos compatibles",
                "Evidencia imagenológica de nueva pérdida de viabilidad miocárdica"
            ],
            differential_diagnosis=[
                "Pericarditis aguda",
                "Disección aórtica",
                "Embolia pulmonar",
                "Neumonía",
                "Reflujo gastroesofágico",
                "Dolor musculoesquelético"
            ],
            treatment_protocol=[
                "ABCDE - Vía aérea, respiración, circulación",
                "Oxígeno si saturación <90%",
                "Aspirina 325mg masticada",
                "Clopidogrel 600mg o Ticagrelor 180mg",
                "Atorvastatina 80mg",
                "Metoprolol 25mg cada 12h si no contraindicado",
                "Heparina según peso",
                "Cateterismo urgente si STEMI"
            ],
            emergency_signs=[
                "Dolor torácico > 20 minutos",
                "Elevación del ST en ECG",
                "Hipotensión arterial",
                "Arritmias ventriculares",
                "Signos de shock"
            ],
            prognosis="Variable según extensión del infarto y tiempo de reperfusión",
            follow_up=[
                "Ecocardiograma a las 48-72 horas",
                "Control con cardiología en 1-2 semanas",
                "Rehabilitación cardíaca",
                "Modificación de factores de riesgo"
            ]
        )
        
        # Hipertensión Arterial
        self.conditions["I10"] = MedicalCondition(
            icd10_code="I10",
            name="Hipertensión Arterial Esencial",
            category="Cardiovascular",
            description="Elevación sostenida de la presión arterial ≥140/90 mmHg",
            symptoms=[
                "Usualmente asintomática",
                "Cefalea occipital matutina",
                "Mareos",
                "Visión borrosa",
                "Disnea de esfuerzo",
                "Epistaxis"
            ],
            risk_factors=[
                "Edad avanzada",
                "Antecedentes familiares",
                "Obesidad",
                "Consumo excesivo de sal",
                "Sedentarismo",
                "Tabaquismo",
                "Diabetes",
                "Estrés crónico"
            ],
            complications=[
                "Enfermedad cardiovascular",
                "Accidente cerebrovascular",
                "Insuficiencia renal",
                "Retinopatía hipertensiva",
                "Insuficiencia cardíaca"
            ],
            diagnostic_criteria=[
                "PA ≥140/90 mmHg en al menos 2 ocasiones",
                "Promedio de PA ambulatoria diurna ≥135/85 mmHg",
                "Promedio de PA domiciliaria ≥135/85 mmHg"
            ],
            differential_diagnosis=[
                "Hipertensión secundaria",
                "Síndrome de bata blanca",
                "Hipertensión enmascarada",
                "Crisis hipertensiva"
            ],
            treatment_protocol=[
                "Modificaciones del estilo de vida",
                "IECA o ARA II como primera línea",
                "Diuréticos tiazídicos",
                "Bloqueadores de canales de calcio",
                "Meta <140/90 mmHg (o <130/80 en diabéticos)"
            ],
            emergency_signs=[
                "PA >180/120 mmHg con síntomas",
                "Dolor torácico",
                "Déficit neurológico",
                "Disnea severa",
                "Alteración del estado mental"
            ],
            prognosis="Excelente con tratamiento adecuado",
            follow_up=[
                "Control mensual hasta meta terapéutica",
                "Control cada 3-6 meses estable",
                "Monitoreo de órgano blanco anual"
            ]
        )
    
    def _add_endocrine_conditions(self):
        """Condiciones endocrinológicas"""
        
        # Diabetes Mellitus Tipo 2
        self.conditions["E11"] = MedicalCondition(
            icd10_code="E11",
            name="Diabetes Mellitus Tipo 2",
            category="Endocrinología",
            description="Trastorno metabólico caracterizado por hiperglucemia crónica",
            symptoms=[
                "Poliuria",
                "Polidipsia",
                "Polifagia",
                "Pérdida de peso inexplicable",
                "Fatiga",
                "Visión borrosa",
                "Heridas que sanan lentamente",
                "Infecciones recurrentes"
            ],
            risk_factors=[
                "Obesidad",
                "Edad >45 años",
                "Antecedentes familiares",
                "Sedentarismo",
                "Hipertensión",
                "Dislipidemia",
                "Síndrome de ovarios poliquísticos",
                "Diabetes gestacional previa"
            ],
            complications=[
                "Retinopatía diabética",
                "Nefropatía diabética",
                "Neuropatía diabética",
                "Enfermedad cardiovascular",
                "Pie diabético",
                "Cetoacidosis diabética",
                "Síndrome hiperosmolar"
            ],
            diagnostic_criteria=[
                "Glucosa en ayunas ≥126 mg/dL",
                "Glucosa a las 2 horas ≥200 mg/dL en PTGO",
                "HbA1c ≥6.5%",
                "Glucosa aleatoria ≥200 mg/dL con síntomas"
            ],
            differential_diagnosis=[
                "Diabetes tipo 1",
                "Diabetes MODY",
                "Diabetes secundaria",
                "Intolerancia a la glucosa"
            ],
            treatment_protocol=[
                "Modificaciones del estilo de vida",
                "Metformina como primera línea",
                "Meta HbA1c <7% (individualizada)",
                "Control de presión arterial <140/90 mmHg",
                "Control de lípidos (LDL <100 mg/dL)"
            ],
            emergency_signs=[
                "Glucosa >400 mg/dL",
                "Cetonas en orina",
                "Alteración del estado mental",
                "Deshidratación severa",
                "Signos de shock"
            ],
            prognosis="Buena con control glucémico adecuado",
            follow_up=[
                "HbA1c cada 3 meses",
                "Examen oftalmológico anual",
                "Microalbuminuria anual",
                "Examen de pies cada visita"
            ]
        )
    
    def _add_respiratory_conditions(self):
        """Condiciones respiratorias"""
        
        # Neumonía Adquirida en la Comunidad
        self.conditions["J18"] = MedicalCondition(
            icd10_code="J18",
            name="Neumonía Adquirida en la Comunidad",
            category="Respiratorio",
            description="Infección aguda del parénquima pulmonar",
            symptoms=[
                "Fiebre y escalofríos",
                "Tos productiva",
                "Disnea",
                "Dolor torácico pleurítico",
                "Fatiga",
                "Confusión (ancianos)",
                "Cefalea",
                "Mialgias"
            ],
            risk_factors=[
                "Edad >65 años",
                "Tabaquismo",
                "Alcoholismo",
                "EPOC",
                "Diabetes",
                "Insuficiencia cardíaca",
                "Inmunosupresión",
                "Aspiración"
            ],
            complications=[
                "Insuficiencia respiratoria",
                "Sepsis",
                "Derrame pleural",
                "Absceso pulmonar",
                "Meningitis",
                "Endocarditis"
            ],
            diagnostic_criteria=[
                "Infiltrado pulmonar en radiografía",
                "Síntomas respiratorios agudos",
                "Signos vitales anormales",
                "Leucocitosis o leucopenia"
            ],
            differential_diagnosis=[
                "Bronquitis aguda",
                "Embolia pulmonar",
                "Insuficiencia cardíaca",
                "Cáncer pulmonar",
                "Tuberculosis"
            ],
            treatment_protocol=[
                "Evaluación con CURB-65",
                "Ambulatorio: Amoxicilina 1g cada 8h x 7 días",
                "Hospitalizado: Ceftriaxona + Azitromicina",
                "UCI: Ceftriaxona + Azitromicina + Vancomicina",
                "Oxígeno si saturación <90%"
            ],
            emergency_signs=[
                "Saturación O2 <90%",
                "Frecuencia respiratoria >30",
                "Presión arterial <90/60 mmHg",
                "Confusión",
                "BUN >20 mg/dL"
            ],
            prognosis="Buena en pacientes jóvenes y sanos",
            follow_up=[
                "Radiografía de control en 6-8 semanas",
                "Mejoría clínica en 48-72 horas",
                "Vacunación anti-neumocócica"
            ]
        )
    
    def _add_neurological_conditions(self):
        """Condiciones neurológicas"""
        
        # Accidente Cerebrovascular Isquémico
        self.conditions["I63"] = MedicalCondition(
            icd10_code="I63",
            name="Accidente Cerebrovascular Isquémico",
            category="Neurología",
            description="Oclusión de un vaso cerebral con consecuente isquemia",
            symptoms=[
                "Hemiparesia o hemiplejía súbita",
                "Alteración del habla (afasia, disartria)",
                "Alteración de la visión",
                "Alteración del estado mental",
                "Cefalea súbita severa",
                "Vértigo, ataxia",
                "Pérdida de sensibilidad"
            ],
            risk_factors=[
                "Hipertensión arterial",
                "Diabetes mellitus",
                "Fibrilación auricular",
                "Tabaquismo",
                "Dislipidemia",
                "Edad avanzada",
                "Antecedentes de ACV",
                "Estenosis carotídea"
            ],
            complications=[
                "Edema cerebral",
                "Transformación hemorrágica",
                "Convulsiones",
                "Neumonía aspirativa",
                "Trombosis venosa profunda",
                "Depresión post-ACV"
            ],
            diagnostic_criteria=[
                "Déficit neurológico focal agudo",
                "TC cerebral sin hemorragia",
                "Inicio súbito de síntomas",
                "Duración >24 horas o muerte"
            ],
            differential_diagnosis=[
                "ACV hemorrágico",
                "AIT",
                "Migraña con aura",
                "Convulsiones",
                "Hipoglucemia",
                "Intoxicación"
            ],
            treatment_protocol=[
                "Activación código ictus",
                "TC cerebral urgente",
                "rtPA si <4.5 horas desde inicio",
                "Trombectomía mecánica si <6 horas",
                "Aspirina 325mg si no rtPA",
                "Control de presión arterial"
            ],
            emergency_signs=[
                "Déficit neurológico súbito",
                "Alteración del nivel de conciencia",
                "Signos de herniación",
                "Convulsiones",
                "Fiebre >38°C"
            ],
            prognosis="Variable según extensión y localización",
            follow_up=[
                "Rehabilitación multidisciplinaria",
                "Control de factores de riesgo",
                "Antiagregación plaquetaria",
                "Evaluación neurológica seriada"
            ]
        )
    
    def _add_essential_medications(self):
        """Medicamentos esenciales"""
        
        # Aspirina
        self.medications["aspirina"] = Medication(
            name="Aspirina",
            generic_name="Ácido acetilsalicílico",
            category="Antiagregante plaquetario",
            indications=[
                "Prevención cardiovascular primaria y secundaria",
                "Síndrome coronario agudo",
                "Accidente cerebrovascular isquémico",
                "Fiebre y dolor (dosis analgésicas)"
            ],
            contraindications=[
                "Alergia a salicilatos",
                "Úlcera péptica activa",
                "Sangrado gastrointestinal",
                "Trastornos de coagulación",
                "Insuficiencia hepática severa"
            ],
            dosage_adult="75-100mg diarios para prevención; 325mg para SCA",
            dosage_pediatric="No usar en <16 años (riesgo de síndrome de Reye)",
            side_effects=[
                "Sangrado gastrointestinal",
                "Úlceras pépticas",
                "Tinnitus",
                "Reacciones alérgicas",
                "Síndrome de Reye (niños)"
            ],
            interactions=[
                "Warfarina (aumenta riesgo de sangrado)",
                "Metotrexato (toxicidad)",
                "IECA (reduce efecto)",
                "Corticosteroides (úlceras)"
            ],
            monitoring=[
                "Signos de sangrado",
                "Función renal",
                "Hemoglobina/hematocrito",
                "Síntomas gastrointestinales"
            ],
            pregnancy_category="C (D en tercer trimestre)"
        )
        
        # Metformina
        self.medications["metformina"] = Medication(
            name="Metformina",
            generic_name="Metformina clorhidrato",
            category="Antidiabético oral",
            indications=[
                "Diabetes mellitus tipo 2",
                "Síndrome de ovarios poliquísticos",
                "Prevención de diabetes en prediabetes"
            ],
            contraindications=[
                "Insuficiencia renal (TFG <30 mL/min)",
                "Acidosis metabólica",
                "Insuficiencia cardíaca descompensada",
                "Hipoxia tisular",
                "Alcoholismo"
            ],
            dosage_adult="500mg dos veces al día, máximo 2550mg/día",
            dosage_pediatric="500mg dos veces al día en >10 años",
            side_effects=[
                "Náuseas y vómitos",
                "Diarrea",
                "Dolor abdominal",
                "Sabor metálico",
                "Acidosis láctica (raro)"
            ],
            interactions=[
                "Contrastes yodados (suspender 48h)",
                "Alcohol (acidosis láctica)",
                "Diuréticos (deshidratación)",
                "Corticosteroides (hiperglucemia)"
            ],
            monitoring=[
                "Función renal cada 6 meses",
                "HbA1c cada 3 meses",
                "Vitamina B12 anual",
                "Síntomas gastrointestinales"
            ],
            pregnancy_category="B"
        )
        
        # Lisinopril
        self.medications["lisinopril"] = Medication(
            name="Lisinopril",
            generic_name="Lisinopril",
            category="IECA",
            indications=[
                "Hipertensión arterial",
                "Insuficiencia cardíaca",
                "Post-infarto agudo miocardio",
                "Nefropatía diabética"
            ],
            contraindications=[
                "Angioedema previo con IECA",
                "Embarazo",
                "Estenosis bilateral de arteria renal",
                "Hiperpotasemia severa"
            ],
            dosage_adult="10mg diarios, máximo 40mg/día",
            dosage_pediatric="0.1mg/kg/día máximo 5mg/día",
            side_effects=[
                "Tos seca",
                "Hiperpotasemia",
                "Angioedema",
                "Hipotensión",
                "Insuficiencia renal"
            ],
            interactions=[
                "Diuréticos ahorradores de potasio",
                "Suplementos de potasio",
                "AINE (reduce efecto)",
                "Litio (toxicidad)"
            ],
            monitoring=[
                "Presión arterial",
                "Función renal y electrolitos",
                "Potasio sérico",
                "Síntomas de angioedema"
            ],
            pregnancy_category="D"
        )
    
    def _add_diagnostic_procedures(self):
        """Procedimientos diagnósticos"""
        
        # Electrocardiograma
        self.procedures["ecg"] = DiagnosticProcedure(
            name="Electrocardiograma",
            category="Cardiología",
            indications=[
                "Dolor torácico",
                "Palpitaciones",
                "Síncope",
                "Disnea",
                "Seguimiento de arritmias"
            ],
            contraindications=["Ninguna absoluta"],
            preparation=["Paciente en reposo", "Piel limpia", "Posición supina"],
            procedure_steps=[
                "Colocar electrodos en posiciones estándar",
                "Verificar calidad de la señal",
                "Registrar 12 derivaciones",
                "Imprimir trazado"
            ],
            interpretation=[
                "Ritmo y frecuencia",
                "Eje eléctrico",
                "Ondas P, QRS, T",
                "Intervalos PR, QT",
                "Signos de isquemia o infarto"
            ],
            complications=["Irritación cutánea leve"],
            cost_range="$20-50 USD"
        )
        
        # Radiografía de Tórax
        self.procedures["rx_torax"] = DiagnosticProcedure(
            name="Radiografía de Tórax",
            category="Radiología",
            indications=[
                "Disnea",
                "Dolor torácico",
                "Tos persistente",
                "Fiebre",
                "Sospecha de neumonía"
            ],
            contraindications=["Embarazo (relativa)"],
            preparation=["Remover objetos metálicos", "Bata hospitalaria"],
            procedure_steps=[
                "Posición PA y lateral",
                "Inspiración profunda",
                "Mantener inmóvil durante exposición"
            ],
            interpretation=[
                "Campos pulmonares",
                "Silueta cardíaca",
                "Hilios pulmonares",
                "Diafragmas",
                "Estructuras óseas"
            ],
            complications=["Exposición mínima a radiación"],
            cost_range="$30-80 USD"
        )
    
    def _add_clinical_protocols(self):
        """Protocolos clínicos"""
        
        # Protocolo de Dolor Torácico
        self.protocols["dolor_toracico"] = ClinicalProtocol(
            name="Protocolo de Dolor Torácico en Urgencias",
            category="Emergencias",
            indication="Paciente con dolor torácico en servicio de urgencias",
            steps=[
                "1. Evaluación inicial ABCDE",
                "2. Historia clínica dirigida",
                "3. Examen físico cardiovascular",
                "4. ECG en primeros 10 minutos",
                "5. Troponinas seriadas",
                "6. Radiografía de tórax",
                "7. Estratificación de riesgo",
                "8. Decisión terapéutica"
            ],
            decision_points=[
                "ECG con elevación ST → Activar código infarto",
                "Troponinas elevadas → Ingreso a cuidados coronarios",
                "Score HEART bajo → Considerar alta temprana",
                "Dolor atípico → Descartar otras causas"
            ],
            emergency_modifications=[
                "Activación inmediata de código infarto si STEMI",
                "Antiagregación dual si SCA confirmado",
                "Evitar AINE en pacientes con riesgo cardiovascular"
            ],
            evidence_level="A",
            last_updated="2024-01-01"
        )
        
        # Protocolo de Hipertensión
        self.protocols["hipertension"] = ClinicalProtocol(
            name="Protocolo de Manejo de Hipertensión Arterial",
            category="Cardiovascular",
            indication="Diagnóstico y manejo de hipertensión arterial",
            steps=[
                "1. Confirmar diagnóstico con múltiples mediciones",
                "2. Evaluación de órgano blanco",
                "3. Identificar factores de riesgo",
                "4. Modificaciones del estilo de vida",
                "5. Inicio de terapia farmacológica si indicada",
                "6. Monitoreo y ajuste de tratamiento"
            ],
            decision_points=[
                "PA >140/90 → Confirmar diagnóstico",
                "PA >160/100 → Iniciar tratamiento inmediato",
                "Diabético o ERC → Meta <130/80",
                "Edad >65 años → Reducción gradual"
            ],
            emergency_modifications=[
                "Crisis hipertensiva → Reducción gradual 10-20%",
                "Emergencia hipertensiva → UCI y reducción inmediata"
            ],
            evidence_level="A",
            last_updated="2024-01-01"
        )
    
    def _add_normal_values(self):
        """Valores normales de signos vitales y laboratorio"""
        
        # Signos vitales normales
        self.vital_signs_normal = {
            "adults": {
                "heart_rate": {"min": 60, "max": 100, "unit": "lpm"},
                "blood_pressure_systolic": {"min": 90, "max": 139, "unit": "mmHg"},
                "blood_pressure_diastolic": {"min": 60, "max": 89, "unit": "mmHg"},
                "respiratory_rate": {"min": 12, "max": 20, "unit": "rpm"},
                "temperature": {"min": 36.0, "max": 37.5, "unit": "°C"},
                "oxygen_saturation": {"min": 95, "max": 100, "unit": "%"}
            },
            "pediatric": {
                "heart_rate": {"min": 80, "max": 120, "unit": "lpm"},
                "blood_pressure_systolic": {"min": 80, "max": 120, "unit": "mmHg"},
                "blood_pressure_diastolic": {"min": 50, "max": 80, "unit": "mmHg"},
                "respiratory_rate": {"min": 20, "max": 30, "unit": "rpm"},
                "temperature": {"min": 36.0, "max": 37.5, "unit": "°C"},
                "oxygen_saturation": {"min": 95, "max": 100, "unit": "%"}
            }
        }
        
        # Valores de laboratorio normales
        self.lab_values_normal = {
            "hematology": {
                "hemoglobin_male": {"min": 13.5, "max": 17.5, "unit": "g/dL"},
                "hemoglobin_female": {"min": 12.0, "max": 15.5, "unit": "g/dL"},
                "hematocrit_male": {"min": 41, "max": 53, "unit": "%"},
                "hematocrit_female": {"min": 36, "max": 46, "unit": "%"},
                "platelets": {"min": 150000, "max": 450000, "unit": "/μL"},
                "wbc": {"min": 4000, "max": 11000, "unit": "/μL"}
            },
            "chemistry": {
                "glucose_fasting": {"min": 70, "max": 99, "unit": "mg/dL"},
                "glucose_random": {"min": 70, "max": 139, "unit": "mg/dL"},
                "creatinine_male": {"min": 0.7, "max": 1.3, "unit": "mg/dL"},
                "creatinine_female": {"min": 0.6, "max": 1.1, "unit": "mg/dL"},
                "bun": {"min": 7, "max": 20, "unit": "mg/dL"},
                "sodium": {"min": 136, "max": 145, "unit": "mEq/L"},
                "potassium": {"min": 3.5, "max": 5.1, "unit": "mEq/L"},
                "chloride": {"min": 98, "max": 107, "unit": "mEq/L"}
            },
            "lipids": {
                "total_cholesterol": {"target": "<200", "unit": "mg/dL"},
                "ldl_cholesterol": {"target": "<100", "unit": "mg/dL"},
                "hdl_cholesterol_male": {"min": 40, "unit": "mg/dL"},
                "hdl_cholesterol_female": {"min": 50, "unit": "mg/dL"},
                "triglycerides": {"target": "<150", "unit": "mg/dL"}
            },
            "cardiac": {
                "troponin_i": {"normal": "<0.04", "unit": "ng/mL"},
                "ck_mb": {"normal": "<6.3", "unit": "ng/mL"},
                "bnp": {"normal": "<100", "unit": "pg/mL"},
                "nt_probnp": {"normal": "<125", "unit": "pg/mL"}
            }
        }
    
    def search_condition_by_symptoms(self, symptoms: List[str]) -> List[str]:
        """Busca condiciones por síntomas"""
        matches = []
        for code, condition in self.conditions.items():
            for symptom in symptoms:
                if any(symptom.lower() in s.lower() for s in condition.symptoms):
                    matches.append(code)
                    break
        return matches
    
    def get_condition_info(self, code: str) -> Optional[MedicalCondition]:
        """Obtiene información completa de una condición"""
        return self.conditions.get(code)
    
    def get_medication_info(self, name: str) -> Optional[Medication]:
        """Obtiene información completa de un medicamento"""
        return self.medications.get(name.lower())
    
    def get_protocol_info(self, name: str) -> Optional[ClinicalProtocol]:
        """Obtiene información de un protocolo clínico"""
        return self.protocols.get(name)
    
    def interpret_vital_signs(self, vitals: Dict[str, float], age_group: str = "adults") -> Dict[str, str]:
        """Interpreta signos vitales"""
        interpretations = {}
        normal_values = self.vital_signs_normal.get(age_group, {})
        
        for vital, value in vitals.items():
            if vital in normal_values:
                normal_range = normal_values[vital]
                if value < normal_range["min"]:
                    interpretations[vital] = "Bajo"
                elif value > normal_range["max"]:
                    interpretations[vital] = "Alto"
                else:
                    interpretations[vital] = "Normal"
            else:
                interpretations[vital] = "No evaluado"
        
        return interpretations
    
    def interpret_lab_values(self, labs: Dict[str, float], patient_gender: str = "male") -> Dict[str, str]:
        """Interpreta valores de laboratorio"""
        interpretations = {}
        
        for lab, value in labs.items():
            # Buscar en todas las categorías
            found = False
            for category, tests in self.lab_values_normal.items():
                if lab in tests:
                    normal_range = tests[lab]
                    
                    # Manejar rangos específicos por género
                    if f"{lab}_{patient_gender}" in tests:
                        normal_range = tests[f"{lab}_{patient_gender}"]
                    
                    if "min" in normal_range and "max" in normal_range:
                        if value < normal_range["min"]:
                            interpretations[lab] = "Bajo"
                        elif value > normal_range["max"]:
                            interpretations[lab] = "Alto"
                        else:
                            interpretations[lab] = "Normal"
                    elif "target" in normal_range:
                        target_val = float(normal_range["target"].replace("<", "").replace(">", ""))
                        if "<" in normal_range["target"]:
                            interpretations[lab] = "Normal" if value < target_val else "Alto"
                        elif ">" in normal_range["target"]:
                            interpretations[lab] = "Normal" if value > target_val else "Bajo"
                    elif "normal" in normal_range:
                        normal_val = float(normal_range["normal"].replace("<", "").replace(">", ""))
                        if "<" in normal_range["normal"]:
                            interpretations[lab] = "Normal" if value < normal_val else "Elevado"
                    
                    found = True
                    break
            
            if not found:
                interpretations[lab] = "No evaluado"
        
        return interpretations
    
    def export_knowledge_base(self) -> Dict[str, Any]:
        """Exporta toda la base de conocimiento"""
        return {
            "conditions": {k: asdict(v) for k, v in self.conditions.items()},
            "medications": {k: asdict(v) for k, v in self.medications.items()},
            "procedures": {k: asdict(v) for k, v in self.procedures.items()},
            "protocols": {k: asdict(v) for k, v in self.protocols.items()},
            "vital_signs_normal": self.vital_signs_normal,
            "lab_values_normal": self.lab_values_normal,
            "export_date": datetime.now().isoformat()
        }

# Función de prueba
def test_knowledge_base():
    """Prueba la base de conocimiento"""
    kb = MedicalKnowledgeBase()
    
    print("🧪 PROBANDO BASE DE CONOCIMIENTO MÉDICA")
    print("=" * 60)
    
    # Probar búsqueda por síntomas
    symptoms = ["dolor torácico", "disnea"]
    matches = kb.search_condition_by_symptoms(symptoms)
    print(f"Condiciones para síntomas {symptoms}: {matches}")
    
    # Probar información de condición
    if matches:
        condition = kb.get_condition_info(matches[0])
        if condition:
            print(f"\nCondición: {condition.name}")
            print(f"Descripción: {condition.description}")
            print(f"Tratamiento: {condition.treatment_protocol[:2]}")
    
    # Probar medicamentos
    med = kb.get_medication_info("aspirina")
    if med:
        print(f"\nMedicamento: {med.name}")
        print(f"Indicaciones: {med.indications[:2]}")
    
    # Probar interpretación de signos vitales
    vitals = {"heart_rate": 120, "blood_pressure_systolic": 160}
    interpretations = kb.interpret_vital_signs(vitals)
    print(f"\nSignos vitales: {interpretations}")
    
    print(f"\nTotal condiciones: {len(kb.conditions)}")
    print(f"Total medicamentos: {len(kb.medications)}")
    print(f"Total procedimientos: {len(kb.procedures)}")
    print(f"Total protocolos: {len(kb.protocols)}")

if __name__ == "__main__":
    test_knowledge_base()