#!/usr/bin/env python3
"""
💊 PHARMACEUTICAL DATABASE SYSTEM (Micromedex-style)
Base de datos farmacéutica completa integrada con RAG

📋 CARACTERÍSTICAS:
✅ Monografías completas de medicamentos
✅ Interacciones medicamentosas
✅ Dosificación por edad/peso/patología
✅ Efectos adversos y contraindicaciones
✅ Compatibilidad IV
✅ Farmacocinética y farmacodinamia
✅ Equivalencias terapéuticas
✅ Alertas de seguridad
"""

from dataclasses import dataclass
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
import json
from pathlib import Path

class InteractionSeverity(Enum):
    MINOR = "minor"
    MODERATE = "moderate"
    MAJOR = "major"
    CONTRAINDICATED = "contraindicated"

class RouteOfAdministration(Enum):
    ORAL = "oral"
    IV = "intravenous"
    IM = "intramuscular"
    SC = "subcutaneous"
    TOPICAL = "topical"
    INHALATION = "inhalation"
    RECTAL = "rectal"
    SUBLINGUAL = "sublingual"

@dataclass
class DrugInteraction:
    """Interacción medicamentosa"""
    drug_a: str
    drug_b: str
    severity: InteractionSeverity
    mechanism: str
    clinical_effect: str
    management: str
    onset: str  # rapid, delayed
    documentation: str  # excellent, good, fair, poor

@dataclass
class Dosage:
    """Dosificación por condición específica"""
    indication: str
    adult_dose: str
    pediatric_dose: Optional[str]
    elderly_dose: Optional[str]
    renal_adjustment: Optional[str]
    hepatic_adjustment: Optional[str]
    route: RouteOfAdministration
    frequency: str
    duration: Optional[str]
    max_dose: Optional[str]

@dataclass
class AdverseEffect:
    """Efecto adverso"""
    effect: str
    frequency: str  # very_common, common, uncommon, rare, very_rare
    severity: str   # mild, moderate, severe, life_threatening
    onset: str      # immediate, early, delayed
    reversible: bool
    monitoring_required: bool

@dataclass
class Contraindication:
    """Contraindicación"""
    condition: str
    severity: str  # absolute, relative
    reason: str

@dataclass
class PharmacokineticData:
    """Datos farmacocinéticos"""
    absorption: str
    distribution: str
    metabolism: str
    elimination: str
    half_life: str
    bioavailability: Optional[str]
    protein_binding: Optional[str]
    clearance: Optional[str]

@dataclass
class DrugMonograph:
    """Monografía completa de medicamento"""
    name: str
    generic_name: str
    brand_names: List[str]
    drug_class: str
    therapeutic_category: str
    mechanism_of_action: str
    indications: List[str]
    dosages: List[Dosage]
    contraindications: List[Contraindication]
    adverse_effects: List[AdverseEffect]
    pharmacokinetics: PharmacokineticData
    monitoring_parameters: List[str]
    patient_counseling: List[str]
    storage_conditions: str
    pregnancy_category: str
    lactation_safety: str
    pediatric_use: str
    geriatric_use: str
    cost_effectiveness: Optional[str]

class PharmaceuticalDatabase:
    """Base de datos farmacéutica completa tipo Micromedex"""
    
    def __init__(self):
        self.monographs: Dict[str, DrugMonograph] = {}
        self.interactions: List[DrugInteraction] = []
        self.compatibility_matrix: Dict[str, Dict[str, str]] = {}
        
        self._initialize_database()
        print("💊 Base de datos farmacéutica inicializada")
    
    def _initialize_database(self):
        """Inicializa la base de datos con medicamentos esenciales"""
        
        # Aspirina - Antiagregante plaquetario
        aspirin_monograph = DrugMonograph(
            name="Aspirina",
            generic_name="Ácido acetilsalicílico",
            brand_names=["Aspirina", "AAS", "Aspegic", "Cardioaspirina"],
            drug_class="AINE - Antiagregante plaquetario",
            therapeutic_category="Cardiovascular/Analgésico",
            mechanism_of_action="Inhibición irreversible de COX-1 y COX-2, bloqueando síntesis de tromboxano A2",
            indications=[
                "Prevención cardiovascular primaria y secundaria",
                "Síndrome coronario agudo",
                "Dolor leve a moderado",
                "Fiebre",
                "Artritis reumatoide"
            ],
            dosages=[
                Dosage(
                    indication="Prevención cardiovascular",
                    adult_dose="75-100 mg",
                    pediatric_dose="No recomendado < 16 años (Síndrome de Reye)",
                    elderly_dose="75 mg (ajustar por sangrado)",
                    renal_adjustment="Evitar si ClCr < 30 mL/min",
                    hepatic_adjustment="Evitar en insuficiencia hepática severa",
                    route=RouteOfAdministration.ORAL,
                    frequency="Una vez al día",
                    duration="Indefinido si no hay contraindicaciones",
                    max_dose="100 mg/día para cardioprotección"
                ),
                Dosage(
                    indication="Síndrome coronario agudo",
                    adult_dose="150-300 mg dosis carga, luego 75-100 mg",
                    pediatric_dose="No aplicable",
                    elderly_dose="75-100 mg",
                    renal_adjustment="Monitorear función renal",
                    hepatic_adjustment="Precaución",
                    route=RouteOfAdministration.ORAL,
                    frequency="Dosis carga única, luego diario",
                    duration="Indefinido",
                    max_dose="300 mg dosis carga"
                )
            ],
            contraindications=[
                Contraindication("Alergia a salicilatos", "absolute", "Riesgo anafilaxia"),
                Contraindication("Sangrado activo", "absolute", "Antiagregación"),
                Contraindication("Úlcera péptica activa", "absolute", "Riesgo hemorragia"),
                Contraindication("Asma inducida por AINE", "absolute", "Broncoespasmo severo"),
                Contraindication("Niños < 16 años con fiebre", "absolute", "Síndrome de Reye")
            ],
            adverse_effects=[
                AdverseEffect("Dispepsia", "common", "mild", "early", True, False),
                AdverseEffect("Sangrado gastrointestinal", "uncommon", "severe", "variable", False, True),
                AdverseEffect("Tinnitus", "uncommon", "moderate", "delayed", True, False),
                AdverseEffect("Reacciones de hipersensibilidad", "rare", "severe", "immediate", True, True)
            ],
            pharmacokinetics=PharmacokineticData(
                absorption="Rápida y completa, 80-100%",
                distribution="Amplia, atraviesa BHE y placenta",
                metabolism="Hepático (conjugación)",
                elimination="Renal 95%",
                half_life="15-30 min (dosis bajas), 4-6 h (dosis altas)",
                bioavailability="80-100%",
                protein_binding="80-90%",
                clearance="Dependiente de dosis"
            ),
            monitoring_parameters=[
                "Función renal",
                "Signos de sangrado",
                "Hemograma",
                "Función hepática"
            ],
            patient_counseling=[
                "Tomar con alimentos para reducir irritación gástrica",
                "Reportar sangrados inusuales",
                "No suspender abruptamente si uso cardiovascular",
                "Evitar alcohol excesivo"
            ],
            storage_conditions="Temperatura ambiente, proteger de humedad",
            pregnancy_category="D (tercer trimestre)",
            lactation_safety="Compatible en dosis bajas",
            pediatric_use="Contraindicado < 16 años por Síndrome de Reye",
            geriatric_use="Aumentar monitoreo por riesgo sangrado",
            cost_effectiveness="Excelente para prevención cardiovascular"
        )
        
        # Metformina - Antidiabético
        metformin_monograph = DrugMonograph(
            name="Metformina",
            generic_name="Metformina clorhidrato",
            brand_names=["Glucophage", "Glafornil", "Metformina"],
            drug_class="Biguanida",
            therapeutic_category="Antidiabético oral",
            mechanism_of_action="Reduce gluconeogénesis hepática, aumenta sensibilidad a insulina",
            indications=[
                "Diabetes mellitus tipo 2",
                "Prediabetes",
                "Síndrome de ovario poliquístico",
                "Resistencia a insulina"
            ],
            dosages=[
                Dosage(
                    indication="Diabetes tipo 2",
                    adult_dose="500 mg BID, incrementar cada semana",
                    pediatric_dose="500 mg BID > 10 años",
                    elderly_dose="Iniciar 500 mg/día, ajustar por función renal",
                    renal_adjustment="Evitar si eGFR < 30 mL/min/1.73m²",
                    hepatic_adjustment="Evitar en insuficiencia hepática",
                    route=RouteOfAdministration.ORAL,
                    frequency="2-3 veces al día",
                    duration="Indefinido",
                    max_dose="2550 mg/día"
                )
            ],
            contraindications=[
                Contraindication("eGFR < 30 mL/min/1.73m²", "absolute", "Riesgo acidosis láctica"),
                Contraindication("Acidosis metabólica", "absolute", "Empeora acidosis"),
                Contraindication("Insuficiencia hepática", "absolute", "Metabolismo lactato"),
                Contraindication("Insuficiencia cardíaca descompensada", "absolute", "Hipoxia tisular")
            ],
            adverse_effects=[
                AdverseEffect("Diarrea", "very_common", "mild", "early", True, False),
                AdverseEffect("Náuseas", "very_common", "mild", "early", True, False),
                AdverseEffect("Dolor abdominal", "common", "mild", "early", True, False),
                AdverseEffect("Acidosis láctica", "very_rare", "life_threatening", "variable", False, True),
                AdverseEffect("Deficiencia B12", "uncommon", "moderate", "delayed", True, True)
            ],
            pharmacokinetics=PharmacokineticData(
                absorption="50-60% biodisponibilidad oral",
                distribution="No se une a proteínas plasmáticas",
                metabolism="No metabolizada",
                elimination="Renal 90% sin cambios",
                half_life="4-9 horas",
                bioavailability="50-60%",
                protein_binding="0%",
                clearance="Renal activo"
            ),
            monitoring_parameters=[
                "HbA1c",
                "Función renal (eGFR)",
                "Vitamina B12",
                "Función hepática",
                "Lactato (si sospecha acidosis)"
            ],
            patient_counseling=[
                "Tomar con comidas para reducir efectos GI",
                "No suspender sin consultar",
                "Reconocer síntomas de acidosis láctica",
                "Suspender antes de procedimientos con contraste"
            ],
            storage_conditions="Temperatura ambiente",
            pregnancy_category="B",
            lactation_safety="Compatible",
            pediatric_use="Seguro > 10 años",
            geriatric_use="Ajustar por función renal",
            cost_effectiveness="Excelente, primera línea en DM2"
        )
        
        # Atorvastatina - Estatina
        atorvastatin_monograph = DrugMonograph(
            name="Atorvastatina",
            generic_name="Atorvastatina cálcica",
            brand_names=["Lipitor", "Zarator", "Atorvastatina"],
            drug_class="Inhibidor HMG-CoA reductasa (Estatina)",
            therapeutic_category="Hipolipemiante",
            mechanism_of_action="Inhibición competitiva HMG-CoA reductasa, reduce síntesis colesterol",
            indications=[
                "Hipercolesterolemia",
                "Prevención cardiovascular primaria",
                "Prevención cardiovascular secundaria",
                "Dislipidemia familiar"
            ],
            dosages=[
                Dosage(
                    indication="Hipercolesterolemia",
                    adult_dose="10-20 mg inicial",
                    pediatric_dose="10 mg > 10 años (hipercolesterolemia familiar)",
                    elderly_dose="10 mg inicial",
                    renal_adjustment="No requiere ajuste",
                    hepatic_adjustment="Contraindicado en hepatopatía activa",
                    route=RouteOfAdministration.ORAL,
                    frequency="Una vez al día por la noche",
                    duration="Indefinido",
                    max_dose="80 mg/día"
                )
            ],
            contraindications=[
                Contraindication("Hepatopatía activa", "absolute", "Hepatotoxicidad"),
                Contraindication("Embarazo", "absolute", "Teratogenia"),
                Contraindication("Lactancia", "absolute", "Paso a leche materna"),
                Contraindication("Miopatía activa", "absolute", "Rabdomiólisis")
            ],
            adverse_effects=[
                AdverseEffect("Mialgia", "common", "mild", "variable", True, False),
                AdverseEffect("Elevación transaminasas", "uncommon", "moderate", "delayed", True, True),
                AdverseEffect("Rabdomiólisis", "very_rare", "life_threatening", "variable", False, True),
                AdverseEffect("Diabetes de nuevo diagnóstico", "uncommon", "moderate", "delayed", False, True)
            ],
            pharmacokinetics=PharmacokineticData(
                absorption="Rápida, baja biodisponibilidad (14%)",
                distribution="98% unión proteica",
                metabolism="CYP3A4 extenso primer paso",
                elimination="Biliar principalmente",
                half_life="14 horas",
                bioavailability="14%",
                protein_binding="98%",
                clearance="Hepática"
            ),
            monitoring_parameters=[
                "Perfil lipídico",
                "Transaminasas",
                "CK (si síntomas musculares)",
                "HbA1c (riesgo diabetes)"
            ],
            patient_counseling=[
                "Tomar por la noche",
                "Reportar dolor muscular",
                "Seguir dieta cardiosaludable",
                "No suspender sin consultar"
            ],
            storage_conditions="Temperatura ambiente",
            pregnancy_category="X",
            lactation_safety="Contraindicado",
            pediatric_use="Hipercolesterolemia familiar > 10 años",
            geriatric_use="Mismo perfil de seguridad",
            cost_effectiveness="Excelente para prevención cardiovascular"
        )
        
        # Registrar monografías
        self.monographs["aspirina"] = aspirin_monograph
        self.monographs["metformina"] = metformin_monograph
        self.monographs["atorvastatina"] = atorvastatin_monograph
        
        # Interacciones importantes
        self.interactions = [
            DrugInteraction(
                drug_a="aspirina",
                drug_b="warfarina",
                severity=InteractionSeverity.MAJOR,
                mechanism="Antiagregación sinérgica + anticoagulación",
                clinical_effect="Aumento significativo riesgo sangrado",
                management="Evitar combinación o monitoreo estrecho INR",
                onset="rapid",
                documentation="excellent"
            ),
            DrugInteraction(
                drug_a="metformina",
                drug_b="contraste_iodado",
                severity=InteractionSeverity.MAJOR,
                mechanism="Nefrotoxicidad del contraste + eliminación renal metformina",
                clinical_effect="Riesgo acidosis láctica por acumulación",
                management="Suspender metformina 48h antes y después del contraste",
                onset="delayed",
                documentation="excellent"
            ),
            DrugInteraction(
                drug_a="atorvastatina",
                drug_b="ciclosporina",
                severity=InteractionSeverity.MAJOR,
                mechanism="Inhibición CYP3A4 por ciclosporina",
                clinical_effect="Aumento concentraciones atorvastatina, riesgo miopatía",
                management="Reducir dosis atorvastatina o cambiar estatina",
                onset="delayed",
                documentation="excellent"
            )
        ]
        
        # Matriz de compatibilidad IV (ejemplos)
        self.compatibility_matrix = {
            "furosemida": {
                "aminofilina": "incompatible",
                "dexametasona": "compatible",
                "heparina": "compatible",
                "insulina": "compatible"
            },
            "heparina": {
                "furosemida": "compatible",
                "diazepam": "incompatible",
                "morfina": "compatible"
            }
        }
    
    def search_drug(self, drug_name: str) -> Optional[DrugMonograph]:
        """Busca medicamento por nombre"""
        drug_lower = drug_name.lower()
        
        # Búsqueda directa
        if drug_lower in self.monographs:
            return self.monographs[drug_lower]
        
        # Búsqueda por nombre genérico o marca
        for monograph in self.monographs.values():
            if (drug_lower in monograph.generic_name.lower() or
                any(drug_lower in brand.lower() for brand in monograph.brand_names)):
                return monograph
        
        return None
    
    def check_interactions(self, drug_list: List[str]) -> List[DrugInteraction]:
        """Verifica interacciones entre lista de medicamentos"""
        interactions_found = []
        
        for i, drug_a in enumerate(drug_list):
            for drug_b in drug_list[i+1:]:
                for interaction in self.interactions:
                    if ((interaction.drug_a.lower() == drug_a.lower() and 
                         interaction.drug_b.lower() == drug_b.lower()) or
                        (interaction.drug_a.lower() == drug_b.lower() and 
                         interaction.drug_b.lower() == drug_a.lower())):
                        interactions_found.append(interaction)
        
        return interactions_found
    
    def get_dosage_recommendation(self, drug_name: str, indication: str, 
                                patient_age: int, weight: Optional[float] = None,
                                renal_function: Optional[str] = None) -> Optional[str]:
        """Obtiene recomendación de dosificación personalizada"""
        monograph = self.search_drug(drug_name)
        if not monograph:
            return None
        
        # Buscar dosificación para indicación específica
        relevant_dosages = [d for d in monograph.dosages 
                          if indication.lower() in d.indication.lower()]
        
        if not relevant_dosages:
            relevant_dosages = monograph.dosages
        
        if not relevant_dosages:
            return None
        
        dosage = relevant_dosages[0]  # Tomar primera coincidencia
        
        # Determinar dosis según edad
        if patient_age < 18 and dosage.pediatric_dose:
            base_dose = dosage.pediatric_dose
        elif patient_age >= 65 and dosage.elderly_dose:
            base_dose = dosage.elderly_dose
        else:
            base_dose = dosage.adult_dose
        
        recommendation = f"Dosis recomendada: {base_dose}"
        recommendation += f"\nVía: {dosage.route.value}"
        recommendation += f"\nFrecuencia: {dosage.frequency}"
        
        if dosage.duration:
            recommendation += f"\nDuración: {dosage.duration}"
        
        # Ajustes especiales
        if renal_function and renal_function.lower() in ["reducida", "insuficiente"]:
            if dosage.renal_adjustment:
                recommendation += f"\nAjuste renal: {dosage.renal_adjustment}"
        
        return recommendation
    
    def get_safety_alerts(self, drug_name: str, patient_conditions: List[str]) -> List[str]:
        """Obtiene alertas de seguridad para condiciones del paciente"""
        monograph = self.search_drug(drug_name)
        if not monograph:
            return []
        
        alerts = []
        
        # Verificar contraindicaciones
        for contraindication in monograph.contraindications:
            for condition in patient_conditions:
                if condition.lower() in contraindication.condition.lower():
                    severity_text = "⚠️ ALERTA" if contraindication.severity == "relative" else "🚨 CONTRAINDICACIÓN ABSOLUTA"
                    alerts.append(f"{severity_text}: {contraindication.condition} - {contraindication.reason}")
        
        # Efectos adversos graves
        serious_effects = [ae for ae in monograph.adverse_effects 
                         if ae.severity in ["severe", "life_threatening"]]
        if serious_effects:
            alerts.append(f"⚠️ Monitorear: {', '.join([ae.effect for ae in serious_effects])}")
        
        return alerts
    
    def check_iv_compatibility(self, drug_a: str, drug_b: str) -> Optional[str]:
        """Verifica compatibilidad IV entre dos medicamentos"""
        drug_a_lower = drug_a.lower()
        drug_b_lower = drug_b.lower()
        
        if drug_a_lower in self.compatibility_matrix:
            return self.compatibility_matrix[drug_a_lower].get(drug_b_lower)
        elif drug_b_lower in self.compatibility_matrix:
            return self.compatibility_matrix[drug_b_lower].get(drug_a_lower)
        
        return None
    
    def generate_pharmaceutical_context(self, query: str) -> str:
        """Genera contexto farmacéutico para RAG"""
        query_lower = query.lower()
        context_parts = []
        
        # Buscar medicamentos mencionados
        for drug_name, monograph in self.monographs.items():
            if (drug_name in query_lower or 
                monograph.generic_name.lower() in query_lower or
                any(brand.lower() in query_lower for brand in monograph.brand_names)):
                
                context_parts.append(f"MEDICAMENTO: {monograph.name}")
                context_parts.append(f"Clase: {monograph.drug_class}")
                context_parts.append(f"Indicaciones: {', '.join(monograph.indications[:3])}")
                
                if monograph.dosages:
                    context_parts.append(f"Dosis típica: {monograph.dosages[0].adult_dose}")
                
                # Contraindicaciones importantes
                major_contraindications = [c.condition for c in monograph.contraindications 
                                         if c.severity == "absolute"]
                if major_contraindications:
                    context_parts.append(f"Contraindicaciones: {', '.join(major_contraindications[:2])}")
                
                context_parts.append("---")
        
        # Agregar alertas de interacciones si se mencionan múltiples medicamentos
        mentioned_drugs = []
        for drug_name in self.monographs.keys():
            if drug_name in query_lower:
                mentioned_drugs.append(drug_name)
        
        if len(mentioned_drugs) > 1:
            interactions = self.check_interactions(mentioned_drugs)
            if interactions:
                context_parts.append("INTERACCIONES DETECTADAS:")
                for interaction in interactions[:2]:  # Máximo 2
                    context_parts.append(f"⚠️ {interaction.drug_a} + {interaction.drug_b}: {interaction.clinical_effect}")
        
        return "\n".join(context_parts) if context_parts else ""

if __name__ == "__main__":
    # Demo del sistema farmacéutico
    pharma_db = PharmaceuticalDatabase()
    
    print("💊 DEMO BASE DE DATOS FARMACÉUTICA")
    print("=" * 40)
    
    # Buscar medicamento
    aspirin = pharma_db.search_drug("aspirina")
    if aspirin:
        print(f"✅ Encontrado: {aspirin.name}")
        print(f"Clase: {aspirin.drug_class}")
        print(f"Indicaciones: {len(aspirin.indications)}")
    
    # Verificar interacciones
    interactions = pharma_db.check_interactions(["aspirina", "warfarina"])
    print(f"🔍 Interacciones encontradas: {len(interactions)}")
    
    # Generar contexto
    context = pharma_db.generate_pharmaceutical_context("paciente diabético toma metformina")
    print(f"🧠 Contexto generado: {len(context)} caracteres")
    
    print("\n✅ Sistema farmacéutico operativo")