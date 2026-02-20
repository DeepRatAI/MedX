"""
Normalización de Categorías - MedeX Knowledge Base
===================================================

Este módulo normaliza todas las categorías de la KB a español,
elimina duplicados y unifica nombres consistentes.

Esquema de 25 categorías maestras normalizadas:
- Todo en español
- Sin duplicados semánticos
- Nombres consistentes
"""

# Mapeo de categorías inglés/duplicados → español normalizado
CATEGORY_NORMALIZATION_MAP = {
    # CARDIOLOGÍA (fusionar Cardiology, Cardiovascular, Cardiac Arrhythmias)
    "Cardiology": "Cardiología",
    "Cardiovascular": "Cardiología",
    "Cardiac Arrhythmias": "Cardiología - Arritmias",
    "Cardiothoracic Surgery": "Cirugía Cardiotorácica",
    "Vascular Disorders": "Cardiología - Vascular",
    "Vascular Surgery": "Cirugía Vascular",
    # NEUMOLOGÍA (fusionar Pulmonology, Respiratory, Respiratory Disorders)
    "Pulmonology": "Neumología",
    "Respiratorio": "Neumología",
    "Respiratory Disorders": "Neumología",
    # GASTROENTEROLOGÍA (fusionar Gastroenterology, Gastrointestinal, etc.)
    "Gastroenterology": "Gastroenterología",
    "Gastrointestinal": "Gastroenterología",
    "Gastrointestinal Disorders": "Gastroenterología",
    "Hepatic Disorders": "Gastroenterología - Hepático",
    # NEUROLOGÍA (unificar todas las variantes)
    "Neurology": "Neurología",
    "Neurological Disorders": "Neurología",
    "Neurología - Cefaleas Primarias": "Neurología",
    "Neurología - Enfermedad Cerebrovascular": "Neurología",
    "Neurología - Enfermedades Neurodegenerativas": "Neurología",
    "Neurología - Trastornos Paroxísticos": "Neurología",
    "Neurosurgery": "Neurocirugía",
    # ENDOCRINOLOGÍA (fusionar todas las variantes)
    "Endocrinology": "Endocrinología",
    "Endocrine Disorders": "Endocrinología",
    "Endocrinología": "Endocrinología",  # Ya está bien
    "Thyroid Disorders": "Endocrinología - Tiroides",
    "Metabolic Disorders": "Endocrinología - Metabólico",
    # PSIQUIATRÍA (fusionar)
    "Psychiatry": "Psiquiatría",
    "Psiquiatría": "Psiquiatría",  # Ya está bien
    "Substance Use Disorders": "Psiquiatría - Adicciones",
    # REUMATOLOGÍA (fusionar)
    "Rheumatology": "Reumatología",
    "Reumatología": "Reumatología",  # Ya está bien
    "Autoimmune Disorders": "Reumatología - Autoinmune",
    # INFECTOLOGÍA (fusionar)
    "Infectious Disease": "Infectología",
    "Infectious Diseases": "Infectología",
    "Infecciosas": "Infectología",
    "Tropical Medicine": "Infectología - Tropical",
    # EMERGENCIAS (fusionar)
    "Emergency Medicine": "Emergencias",
    "Emergencias": "Emergencias",  # Ya está bien
    "Critical Care": "Cuidados Intensivos",
    "Poisoning": "Toxicología",
    "Toxicology": "Toxicología",
    # DERMATOLOGÍA
    "Dermatology": "Dermatología",
    "Burns and Thermal Injuries": "Dermatología - Quemaduras",
    "Wound Care": "Dermatología - Heridas",
    # OFTALMOLOGÍA
    "Ophthalmology": "Oftalmología",
    "Ophthalmologic Emergencies": "Oftalmología - Emergencias",
    # OTORRINOLARINGOLOGÍA
    "Otolaryngology": "Otorrinolaringología",
    "ENT/Otolaryngology": "Otorrinolaringología",
    # NEFROLOGÍA
    "Nephrology": "Nefrología",
    "Renal Disorders": "Nefrología",
    "Electrolyte Disorders": "Nefrología - Electrolitos",
    # UROLOGÍA
    "Urology": "Urología",
    # HEMATOLOGÍA
    "Hematology": "Hematología",
    "Immunodeficiency Disorders": "Hematología - Inmunodeficiencia",
    # ONCOLOGÍA
    "Oncology": "Oncología",
    # GINECOLOGÍA Y OBSTETRICIA
    "OB/GYN": "Ginecología y Obstetricia",
    "Pregnancy Conditions": "Ginecología y Obstetricia - Embarazo",
    "Breast Disorders": "Ginecología y Obstetricia - Mama",
    # PEDIATRÍA
    "Pediatrics": "Pediatría",
    "Neonatology": "Pediatría - Neonatología",
    "Adolescent Medicine": "Pediatría - Adolescentes",
    "Congenital Disorders": "Pediatría - Congénito",
    # TRAUMATOLOGÍA Y ORTOPEDIA
    "Orthopedics": "Traumatología y Ortopedia",
    "Musculoskeletal Disorders": "Traumatología y Ortopedia",
    "Fractures": "Traumatología y Ortopedia - Fracturas",
    "Sports Medicine": "Traumatología y Ortopedia - Deportiva",
    # CIRUGÍA
    "General Surgery": "Cirugía General",
    "Trauma Surgery": "Cirugía - Trauma",
    # ALERGOLOGÍA E INMUNOLOGÍA
    "Allergy/Immunology": "Alergología e Inmunología",
    # GERIATRÍA
    "Geriatrics": "Geriatría",
    # MEDICINA INTERNA / ATENCIÓN PRIMARIA
    "Primary Care": "Medicina Familiar",
    "Chronic Disease Management": "Medicina Interna - Crónicos",
    "Common Presentations": "Medicina Interna - Presentaciones",
    "Preventive Medicine": "Medicina Preventiva",
    # GENÉTICA
    "Medical Genetics": "Genética Médica",
    "Rare Diseases": "Genética Médica - Enfermedades Raras",
    # REHABILITACIÓN
    "Rehabilitation Medicine": "Medicina de Rehabilitación",
    "Pain Medicine": "Medicina del Dolor",
    # CUIDADOS PALIATIVOS
    "Palliative Care": "Cuidados Paliativos",
    # MEDICINA DEL SUEÑO
    "Sleep Medicine": "Medicina del Sueño",
    # MEDICINA OCUPACIONAL
    "Occupational Medicine": "Medicina Ocupacional",
    # TRASPLANTES
    "Transplant Medicine": "Medicina de Trasplantes",
    # ODONTOLOGÍA
    "Dental/Oral Conditions": "Odontología",
    # NUTRICIÓN
    "Nutritional Disorders": "Nutrición",
    # OTROS
    "Laboratory Findings": "Hallazgos de Laboratorio",
    "Symptoms/Signs": "Signos y Síntomas",
    "Social/Environmental Factors": "Factores Sociales/Ambientales",
    "Complications of Medical Care": "Complicaciones Iatrogénicas",
}


def normalize_category(category: str) -> str:
    """
    Normaliza una categoría al estándar español.

    Args:
        category: Categoría original (puede estar en inglés o español)

    Returns:
        Categoría normalizada en español
    """
    return CATEGORY_NORMALIZATION_MAP.get(category, category)


def get_all_normalized_categories() -> list:
    """
    Retorna lista ordenada de todas las categorías normalizadas únicas.
    """
    normalized = set(CATEGORY_NORMALIZATION_MAP.values())
    return sorted(normalized)


def get_master_categories() -> dict:
    """
    Retorna las categorías maestras agrupadas por especialidad principal.

    Útil para UI con categorías colapsables.
    """
    return {
        "Cardiología": [
            "Cardiología",
            "Cardiología - Arritmias",
            "Cardiología - Vascular",
            "Cirugía Cardiotorácica",
            "Cirugía Vascular",
        ],
        "Neumología": ["Neumología"],
        "Gastroenterología": ["Gastroenterología", "Gastroenterología - Hepático"],
        "Neurología": ["Neurología", "Neurocirugía"],
        "Endocrinología": [
            "Endocrinología",
            "Endocrinología - Tiroides",
            "Endocrinología - Metabólico",
        ],
        "Psiquiatría": ["Psiquiatría", "Psiquiatría - Adicciones"],
        "Reumatología": ["Reumatología", "Reumatología - Autoinmune"],
        "Infectología": ["Infectología", "Infectología - Tropical"],
        "Emergencias y Cuidados Críticos": [
            "Emergencias",
            "Cuidados Intensivos",
            "Toxicología",
        ],
        "Dermatología": [
            "Dermatología",
            "Dermatología - Quemaduras",
            "Dermatología - Heridas",
        ],
        "Oftalmología": ["Oftalmología", "Oftalmología - Emergencias"],
        "Otorrinolaringología": ["Otorrinolaringología"],
        "Nefrología": ["Nefrología", "Nefrología - Electrolitos"],
        "Urología": ["Urología"],
        "Hematología": ["Hematología", "Hematología - Inmunodeficiencia"],
        "Oncología": ["Oncología"],
        "Ginecología y Obstetricia": [
            "Ginecología y Obstetricia",
            "Ginecología y Obstetricia - Embarazo",
            "Ginecología y Obstetricia - Mama",
        ],
        "Pediatría": [
            "Pediatría",
            "Pediatría - Neonatología",
            "Pediatría - Adolescentes",
            "Pediatría - Congénito",
        ],
        "Traumatología y Ortopedia": [
            "Traumatología y Ortopedia",
            "Traumatología y Ortopedia - Fracturas",
            "Traumatología y Ortopedia - Deportiva",
        ],
        "Cirugía": ["Cirugía General", "Cirugía - Trauma"],
        "Alergología e Inmunología": ["Alergología e Inmunología"],
        "Geriatría": ["Geriatría"],
        "Medicina Interna": [
            "Medicina Familiar",
            "Medicina Interna - Crónicos",
            "Medicina Interna - Presentaciones",
            "Medicina Preventiva",
        ],
        "Genética Médica": ["Genética Médica", "Genética Médica - Enfermedades Raras"],
        "Otras Especialidades": [
            "Medicina de Rehabilitación",
            "Medicina del Dolor",
            "Cuidados Paliativos",
            "Medicina del Sueño",
            "Medicina Ocupacional",
            "Medicina de Trasplantes",
            "Odontología",
            "Nutrición",
            "Hallazgos de Laboratorio",
            "Signos y Síntomas",
            "Factores Sociales/Ambientales",
            "Complicaciones Iatrogénicas",
        ],
    }


# Estadísticas
NORMALIZED_STATS = {
    "total_original_categories": len(CATEGORY_NORMALIZATION_MAP),
    "total_normalized_categories": len(set(CATEGORY_NORMALIZATION_MAP.values())),
    "master_specialties": 23,  # Especialidades principales
}


if __name__ == "__main__":
    print("=" * 60)
    print("NORMALIZACIÓN DE CATEGORÍAS - MedeX")
    print("=" * 60)
    print(f"\nCategorías originales: {NORMALIZED_STATS['total_original_categories']}")
    print(f"Categorías normalizadas: {NORMALIZED_STATS['total_normalized_categories']}")
    print(f"Especialidades maestras: {NORMALIZED_STATS['master_specialties']}")

    print("\n📋 Categorías normalizadas:")
    for cat in get_all_normalized_categories():
        print(f"   • {cat}")
