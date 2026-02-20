#!/usr/bin/env python3
"""
🔬 Condiciones Endocrinas y Metabólicas - Base de Conocimiento Expandida
Basado en: ICD-10-CM 2026, ADA Standards 2024, Endocrine Society Guidelines

Cobertura:
- Diabetes Mellitus (E10-E14)
- Trastornos Tiroideos (E00-E07)
- Trastornos Adrenales (E24-E27)
- Obesidad y Síndrome Metabólico (E66)
- Hiperlipidemia (E78)
- Trastornos Hipofisiarios (E22-E23)
- Trastornos del Calcio (E83)
- Trastornos Electrolíticos
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


ENDOCRINE_CONDITIONS = {
    # =========================================================================
    # DIABETES MELLITUS TIPO 1 (E10)
    # =========================================================================
    "E10": MedicalCondition(
        icd10_code="E10",
        name="Diabetes Mellitus Tipo 1",
        category="Endocrinología",
        description="Enfermedad autoinmune caracterizada por destrucción de células beta pancreáticas con deficiencia absoluta de insulina. Debut típico en infancia/adolescencia.",
        symptoms=[
            "Poliuria (micción frecuente)",
            "Polidipsia (sed excesiva)",
            "Polifagia con pérdida de peso",
            "Fatiga y debilidad",
            "Visión borrosa",
            "Cetoacidosis diabética al debut (frecuente)",
            "Infecciones recurrentes",
        ],
        risk_factors=[
            "Historia familiar de DM1 o enfermedades autoinmunes",
            "Anticuerpos anti-GAD, anti-IA2, anti-insulina positivos",
            "HLA-DR3/DR4",
            "Infecciones virales previas (enterovirus)",
            "Enfermedad celíaca asociada",
        ],
        complications=[
            "Cetoacidosis diabética (CAD) - EMERGENCIA",
            "Hipoglucemia severa",
            "Retinopatía diabética",
            "Nefropatía diabética → ERC",
            "Neuropatía periférica y autonómica",
            "Enfermedad cardiovascular prematura",
            "Pie diabético",
        ],
        diagnostic_criteria=[
            "Glucemia ayunas ≥126 mg/dL (2 ocasiones)",
            "Glucemia random ≥200 mg/dL + síntomas",
            "HbA1c ≥6.5%",
            "PTOG 2h ≥200 mg/dL",
            "Péptido C bajo/indetectable",
            "Anticuerpos anti-islote positivos (GAD65, IA2, ZnT8)",
        ],
        differential_diagnosis=[
            "DM tipo 2 de inicio juvenil",
            "MODY (Maturity Onset Diabetes of the Young)",
            "Diabetes secundaria a pancreatitis",
            "LADA (Latent Autoimmune Diabetes in Adults)",
            "Diabetes inducida por fármacos (corticoides)",
        ],
        treatment_protocol=[
            "INSULINA obligatoria de por vida",
            "Basal-bolo: Glargina/Detemir + Lispro/Aspart",
            "Bomba de insulina (ISCI) en casos seleccionados",
            "Monitorización glucémica continua (CGM)",
            "Conteo de carbohidratos",
            "HbA1c objetivo <7% (individualizar)",
            "Screening anual de complicaciones desde 5 años post-diagnóstico",
        ],
        emergency_signs=[
            "Cetoacidosis: náuseas, vómitos, dolor abdominal, respiración Kussmaul",
            "Cetonuria/cetonemia positiva",
            "pH <7.3, bicarbonato <18 mEq/L",
            "Alteración del sensorio",
            "Deshidratación severa",
        ],
        prognosis="Con control adecuado, expectativa de vida cercana a normal. HbA1c <7% reduce complicaciones microvasculares 25-76%.",
        follow_up=[
            "HbA1c cada 3 meses",
            "Función renal (creatinina, albuminuria) anual",
            "Fondo de ojo anual",
            "Perfil lipídico anual",
            "Examen de pies cada visita",
            "TSH anual (asociación tiroiditis autoinmune)",
        ],
    ),
    # =========================================================================
    # DIABETES MELLITUS TIPO 2 (E11)
    # =========================================================================
    "E11": MedicalCondition(
        icd10_code="E11",
        name="Diabetes Mellitus Tipo 2",
        category="Endocrinología",
        description="Enfermedad metabólica caracterizada por resistencia a insulina y deficiencia relativa de secreción. Asociada a obesidad y síndrome metabólico.",
        symptoms=[
            "Frecuentemente asintomático al inicio",
            "Poliuria y polidipsia (cuando glucemia >180 mg/dL)",
            "Fatiga",
            "Visión borrosa",
            "Infecciones cutáneas/urinarias recurrentes",
            "Acantosis nigricans",
            "Cicatrización lenta de heridas",
        ],
        risk_factors=[
            "Obesidad (IMC ≥30)",
            "Edad >45 años",
            "Historia familiar de DM2",
            "Sedentarismo",
            "Prediabetes (glucemia ayunas 100-125 mg/dL)",
            "Síndrome de ovario poliquístico",
            "Diabetes gestacional previa",
            "Hipertensión arterial",
            "Dislipidemia",
        ],
        complications=[
            "Estado hiperosmolar hiperglucémico (EHH) - EMERGENCIA",
            "Enfermedad cardiovascular (principal causa de muerte)",
            "Retinopatía diabética",
            "Nefropatía diabética",
            "Neuropatía diabética",
            "Pie diabético → amputación",
            "Hígado graso no alcohólico",
        ],
        diagnostic_criteria=[
            "Glucemia ayunas ≥126 mg/dL",
            "HbA1c ≥6.5%",
            "Glucemia 2h post-PTOG ≥200 mg/dL",
            "Glucemia random ≥200 mg/dL con síntomas",
            "Confirmar con segundo test si asintomático",
        ],
        differential_diagnosis=[
            "Prediabetes",
            "DM tipo 1 de inicio tardío",
            "LADA",
            "Diabetes secundaria (Cushing, acromegalia)",
            "Diabetes inducida por fármacos",
        ],
        treatment_protocol=[
            "1ª LÍNEA: Metformina 500-2000 mg/día + cambios estilo de vida",
            "2ª LÍNEA: Añadir iSGLT2 (empagliflozina) si ECV/ERC",
            "2ª LÍNEA: Añadir GLP-1 RA (semaglutida) si obesidad",
            "Escalar a insulina basal si HbA1c >10% o síntomas",
            "Control PA <130/80 mmHg (IECA/ARA-II)",
            "Estatinas si >40 años o factores de riesgo CV",
            "Aspirina si riesgo CV alto",
        ],
        emergency_signs=[
            "EHH: glucemia >600 mg/dL, osmolaridad >320, sin cetosis",
            "Deshidratación severa",
            "Alteración del sensorio → coma",
            "Hipoglucemia severa (confusión, convulsiones)",
        ],
        prognosis="Control intensivo (HbA1c <7%) reduce complicaciones microvasculares. Reducción de peso 5-10% mejora control glucémico significativamente.",
        follow_up=[
            "HbA1c cada 3-6 meses",
            "Función renal anual",
            "Fondo de ojo al diagnóstico y anual",
            "Perfil lipídico anual",
            "PA en cada visita",
            "Examen de pies cada visita",
        ],
    ),
    # =========================================================================
    # HIPOTIROIDISMO (E03)
    # =========================================================================
    "E03": MedicalCondition(
        icd10_code="E03",
        name="Hipotiroidismo",
        category="Endocrinología",
        description="Deficiencia de hormonas tiroideas. Causa más común: tiroiditis de Hashimoto (autoinmune). Puede ser primario, secundario o terciario.",
        symptoms=[
            "Fatiga y somnolencia",
            "Intolerancia al frío",
            "Aumento de peso",
            "Estreñimiento",
            "Piel seca",
            "Caída de cabello",
            "Bradicardia",
            "Mixedema (cara hinchada)",
            "Deterioro cognitivo, depresión",
            "Irregularidades menstruales",
        ],
        risk_factors=[
            "Sexo femenino (8:1)",
            "Edad >60 años",
            "Historia familiar de enfermedad tiroidea",
            "Enfermedades autoinmunes (DM1, vitiligo, artritis reumatoide)",
            "Radioterapia cabeza/cuello",
            "Tiroidectomía previa",
            "Medicamentos (amiodarona, litio)",
        ],
        complications=[
            "Coma mixedematoso - EMERGENCIA",
            "Cardiomegalia, derrame pericárdico",
            "Dislipidemia secundaria",
            "Hiponatremia",
            "Anemia",
            "Infertilidad, abortos recurrentes",
            "Bocio",
        ],
        diagnostic_criteria=[
            "TSH elevada (>4.5 mU/L) - hipotiroidismo primario",
            "T4 libre baja confirma hipotiroidismo clínico",
            "TSH elevada + T4L normal = hipotiroidismo subclínico",
            "Anti-TPO positivos sugieren Hashimoto",
            "TSH baja/normal + T4L baja = hipotiroidismo central",
        ],
        differential_diagnosis=[
            "Depresión",
            "Anemia",
            "Síndrome de fatiga crónica",
            "Apnea del sueño",
            "Insuficiencia cardíaca",
            "Enfermedad de Addison",
        ],
        treatment_protocol=[
            "Levotiroxina (T4): dosis inicial 1.6 mcg/kg/día",
            "Inicio con dosis bajas en ancianos y cardiópatas (25-50 mcg)",
            "Tomar en ayunas, 30-60 min antes del desayuno",
            "Ajustar dosis cada 6-8 semanas hasta normalizar TSH",
            "Objetivo TSH: 0.5-2.5 mU/L en adultos jóvenes",
            "En embarazo: objetivo TSH <2.5 mU/L (1er trimestre)",
        ],
        emergency_signs=[
            "Coma mixedematoso: hipotermia, hipoglucemia, bradicardia severa",
            "Alteración del sensorio",
            "Hipotensión refractaria",
            "Hipoventilación con hipercapnia",
        ],
        prognosis="Excelente con tratamiento adecuado. Requiere tratamiento de por vida. Normalización de síntomas en semanas a meses.",
        follow_up=[
            "TSH cada 6-8 semanas al iniciar/ajustar tratamiento",
            "TSH anual una vez estable",
            "Perfil lipídico tras normalización",
            "En embarazo: TSH cada 4-6 semanas",
        ],
    ),
    # =========================================================================
    # HIPERTIROIDISMO (E05)
    # =========================================================================
    "E05": MedicalCondition(
        icd10_code="E05",
        name="Hipertiroidismo",
        category="Endocrinología",
        description="Exceso de hormonas tiroideas. Causa más común: enfermedad de Graves (autoinmune). Otras: bocio multinodular tóxico, adenoma tóxico.",
        symptoms=[
            "Pérdida de peso con apetito conservado",
            "Palpitaciones, taquicardia",
            "Intolerancia al calor, sudoración",
            "Temblor fino de manos",
            "Nerviosismo, irritabilidad, ansiedad",
            "Diarrea o aumento de frecuencia deposiciones",
            "Debilidad muscular proximal",
            "Exoftalmos (en Graves)",
            "Bocio difuso o nodular",
            "Irregularidades menstruales",
        ],
        risk_factors=[
            "Sexo femenino",
            "Historia familiar de enfermedad tiroidea",
            "Enfermedades autoinmunes",
            "Ingesta excesiva de yodo",
            "Medicamentos (amiodarona)",
            "Estrés significativo",
        ],
        complications=[
            "Crisis tirotóxica (tormenta tiroidea) - EMERGENCIA",
            "Fibrilación auricular",
            "Insuficiencia cardíaca de alto gasto",
            "Osteoporosis",
            "Oftalmopatía de Graves (puede dejar secuelas)",
            "Dermopatía pretibial",
        ],
        diagnostic_criteria=[
            "TSH suprimida (<0.1 mU/L)",
            "T4 libre y/o T3 elevadas",
            "TSH bajo + T4L/T3 normales = hipertiroidismo subclínico",
            "Anticuerpos anti-receptor TSH (TRAb) positivos en Graves",
            "Gammagrafía tiroidea: captación aumentada/disminuida según causa",
        ],
        differential_diagnosis=[
            "Tiroiditis subaguda (fase hipertiroidea)",
            "Tirotoxicosis facticia",
            "Adenoma hipofisario secretor de TSH",
            "Ansiedad",
            "Feocromocitoma",
        ],
        treatment_protocol=[
            "ANTITIROIDEOS: Metimazol 10-30 mg/día (1ª línea)",
            "Propiltiouracilo solo en 1er trimestre embarazo o crisis",
            "BETABLOQUEADORES: Propranolol 40-120 mg/día para síntomas",
            "YODO RADIACTIVO (I-131): tratamiento definitivo en adultos",
            "CIRUGÍA: tiroidectomía en bocio grande, sospecha malignidad, Graves severo",
            "Tratamiento 12-18 meses con antitiroideos, 30-50% remisión",
        ],
        emergency_signs=[
            "Crisis tirotóxica: fiebre >40°C, taquicardia >140/min",
            "Agitación severa, delirium, psicosis",
            "Insuficiencia cardíaca aguda",
            "Ictericia",
            "Score Burch-Wartofsky ≥45",
        ],
        prognosis="Bueno con tratamiento. Graves: 30-50% remisión con antitiroideos. Post-I-131 o cirugía requieren levotiroxina de por vida.",
        follow_up=[
            "T4L y TSH cada 4-6 semanas al inicio",
            "Hemograma (vigilar agranulocitosis con antitiroideos)",
            "Función hepática periódica",
            "Evaluación oftalmológica si Graves",
            "TSH anual post-tratamiento definitivo",
        ],
    ),
    # =========================================================================
    # NÓDULO TIROIDEO (E04)
    # =========================================================================
    "E04": MedicalCondition(
        icd10_code="E04",
        name="Nódulo Tiroideo",
        category="Endocrinología",
        description="Lesión discreta dentro de la glándula tiroides. Muy frecuentes (50% de población). 5-15% son malignos. Evaluación según tamaño y características ecográficas.",
        symptoms=[
            "Mayoría asintomáticos (hallazgo incidental)",
            "Masa palpable en cuello",
            "Disfagia (si grande)",
            "Disnea (compresión traqueal)",
            "Disfonía (si invasión nervio laríngeo recurrente)",
            "Síntomas de hipertiroidismo si nódulo tóxico",
        ],
        risk_factors=[
            "Sexo femenino",
            "Edad avanzada",
            "Déficit de yodo",
            "Radiación cabeza/cuello en infancia",
            "Historia familiar de cáncer tiroideo",
            "Síndromes hereditarios (MEN2, síndrome Cowden)",
        ],
        complications=[
            "Malignidad (5-15%)",
            "Compresión de estructuras cervicales",
            "Hipertiroidismo (nódulo autónomo)",
            "Hemorragia intratiroidea",
        ],
        diagnostic_criteria=[
            "Ecografía tiroidea: tamaño, características TI-RADS",
            "TSH: si suprimida, sugiere nódulo funcionante",
            "Gammagrafía: nódulo caliente vs frío",
            "PAAF (punción aspiración aguja fina): indicada según TI-RADS",
            "TI-RADS 3: PAAF si ≥2.5 cm",
            "TI-RADS 4: PAAF si ≥1.5 cm",
            "TI-RADS 5: PAAF si ≥1 cm",
        ],
        differential_diagnosis=[
            "Nódulo benigno (coloide, adenoma folicular)",
            "Carcinoma papilar de tiroides",
            "Carcinoma folicular",
            "Carcinoma medular",
            "Linfoma tiroideo",
            "Metástasis",
        ],
        treatment_protocol=[
            "OBSERVACIÓN: nódulos benignos <1 cm, baja sospecha",
            "SEGUIMIENTO ecográfico: 6-12 meses inicial, luego anual",
            "PAAF: repetir si crecimiento significativo (>50% volumen)",
            "CIRUGÍA: citología sospechosa/maligna, compresión sintomática",
            "ABLACIÓN por radiofrecuencia: nódulos benignos sintomáticos seleccionados",
            "I-131: nódulos tóxicos en pacientes no quirúrgicos",
        ],
        emergency_signs=[
            "Disnea aguda por compresión traqueal",
            "Crecimiento rápido (semanas) sugiere malignidad agresiva o hemorragia",
            "Disfonía súbita",
        ],
        prognosis="95% benignos. Carcinoma papilar (más común): supervivencia >98% a 10 años. Carcinoma anaplásico: pronóstico pobre.",
        follow_up=[
            "Ecografía cada 6-12 meses inicialmente",
            "PAAF si crecimiento o cambio características",
            "TSH anual",
            "Post-tiroidectomía: tiroglobulina para vigilancia",
        ],
    ),
    # =========================================================================
    # SÍNDROME DE CUSHING (E24)
    # =========================================================================
    "E24": MedicalCondition(
        icd10_code="E24",
        name="Síndrome de Cushing",
        category="Endocrinología",
        description="Hipercortisolismo crónico. Causa más común: iatrogénica (corticoides exógenos). Endógeno: adenoma hipofisario (enfermedad de Cushing 70%), tumores adrenales, secreción ectópica ACTH.",
        symptoms=[
            "Obesidad central con extremidades delgadas",
            "Cara de luna llena, plétora facial",
            "Giba de búfalo (acumulación grasa dorsocervical)",
            "Estrías violáceas anchas (>1 cm)",
            "Fragilidad capilar, equimosis fáciles",
            "Hirsutismo, acné",
            "Debilidad muscular proximal",
            "Hipertensión arterial",
            "Hiperglucemia/diabetes",
            "Osteoporosis, fracturas patológicas",
            "Labilidad emocional, depresión, psicosis",
        ],
        risk_factors=[
            "Uso crónico de corticoides (más común)",
            "Adenoma hipofisario",
            "Tumores adrenales",
            "Tumores neuroendocrinos (pulmón de células pequeñas)",
        ],
        complications=[
            "Diabetes secundaria",
            "Hipertensión refractaria",
            "Osteoporosis con fracturas vertebrales",
            "Infecciones oportunistas",
            "Tromboembolismo venoso",
            "Enfermedad cardiovascular",
        ],
        diagnostic_criteria=[
            "SCREENING: Cortisol libre urinario 24h (>3x límite superior)",
            "Test supresión dexametasona 1mg nocturno (cortisol AM >1.8 μg/dL)",
            "Cortisol salival nocturno elevado (>0.3 μg/dL)",
            "Confirmar con al menos 2 tests",
            "ACTH: elevada (Cushing, ectópico) vs suprimida (adrenal)",
            "RM hipófisis, TAC suprarrenal según ACTH",
        ],
        differential_diagnosis=[
            "Pseudo-Cushing (depresión, alcoholismo, obesidad)",
            "Síndrome metabólico",
            "Síndrome de ovario poliquístico",
            "Hiperplasia adrenal congénita",
        ],
        treatment_protocol=[
            "CAUSA IATROGÉNICA: reducir dosis corticoides gradualmente",
            "ENFERMEDAD DE CUSHING: cirugía transesfenoidal (1ª línea)",
            "TUMOR ADRENAL: adrenalectomía",
            "ECTÓPICO: resección tumor si posible",
            "FÁRMACOS: ketoconazol, osilodrostat, metirapona (preoperatorio o irresecable)",
            "Tratar comorbilidades: HTA, DM, osteoporosis",
        ],
        emergency_signs=[
            "Crisis adrenal post-cirugía (insuficiencia adrenal aguda)",
            "Infecciones severas (inmunodepresión)",
            "Psicosis aguda",
        ],
        prognosis="Post-cirugía exitosa: remisión 70-90%. Cushing no tratado: mortalidad 50% a 5 años por complicaciones CV e infecciosas.",
        follow_up=[
            "Cortisol post-cirugía (esperado suprimido → insuficiencia adrenal)",
            "Suplementación con hidrocortisona post-cirugía (meses a años)",
            "Monitoreo de recurrencia: cortisol libre urinario anual",
            "Densitometría ósea",
            "Control HTA, DM",
        ],
    ),
    # =========================================================================
    # INSUFICIENCIA ADRENAL (E27.1)
    # =========================================================================
    "E27.1": MedicalCondition(
        icd10_code="E27.1",
        name="Insuficiencia Adrenal (Enfermedad de Addison)",
        category="Endocrinología",
        description="Deficiencia de cortisol ± aldosterona. Primaria (Addison): destrucción adrenal (autoinmune 80%). Secundaria: déficit ACTH. Terciaria: supresión por corticoides exógenos.",
        symptoms=[
            "Fatiga progresiva, debilidad",
            "Hipotensión ortostática",
            "Hiperpigmentación (pliegues, cicatrices, mucosas) - solo primaria",
            "Pérdida de peso, anorexia",
            "Náuseas, vómitos, dolor abdominal",
            "Deseo de sal (avidez por sal)",
            "Hipoglucemia",
            "Mialgias, artralgias",
            "Pérdida de vello axilar/púbico (en mujeres)",
        ],
        risk_factors=[
            "Enfermedades autoinmunes (Hashimoto, DM1, vitiligo)",
            "Tuberculosis adrenal (países endémicos)",
            "Uso crónico de corticoides (secundaria)",
            "Infecciones VIH, CMV (en inmunodeprimidos)",
            "Metástasis adrenales (pulmón, mama)",
            "Síndrome antifosfolípido (hemorragia adrenal)",
        ],
        complications=[
            "Crisis adrenal - EMERGENCIA MÉDICA",
            "Shock hipovolémico",
            "Hiperkalemia severa (primaria)",
            "Hiponatremia",
            "Hipoglucemia",
        ],
        diagnostic_criteria=[
            "Cortisol AM <3 μg/dL: confirma diagnóstico",
            "Cortisol AM 3-18 μg/dL: test estimulación ACTH",
            "Test ACTH: cortisol <18 μg/dL a los 30-60 min = insuficiencia",
            "ACTH: elevada (primaria) vs baja (secundaria)",
            "Anticuerpos anti-21-hidroxilasa: positivos en autoinmune",
            "TAC/RM adrenal: atrofia o lesiones",
        ],
        differential_diagnosis=[
            "Síndrome de fatiga crónica",
            "Depresión",
            "Hipotiroidismo",
            "Trastornos gastrointestinales crónicos",
            "Malabsorción",
        ],
        treatment_protocol=[
            "REEMPLAZO GLUCOCORTICOIDE: Hidrocortisona 15-25 mg/día (en 2-3 dosis)",
            "Dosis mayor por la mañana (10-15 mg) + tarde (5-10 mg)",
            "REEMPLAZO MINERALOCORTICOIDE (primaria): Fludrocortisona 0.05-0.2 mg/día",
            "DHEA 25-50 mg/día en mujeres (opcional)",
            "REGLAS DE ESTRÉS: duplicar/triplicar dosis en enfermedad",
            "Inyección IM de hidrocortisona disponible en casa para emergencias",
        ],
        emergency_signs=[
            "Crisis adrenal: hipotensión severa (<90/60), shock",
            "Deshidratación, oliguria",
            "Dolor abdominal agudo, fiebre",
            "Alteración del sensorio → coma",
            "Hipoglucemia, hiperkalemia, hiponatremia",
        ],
        prognosis="Excelente con tratamiento adecuado. Expectativa de vida normal. Riesgo de crisis adrenal requiere educación del paciente.",
        follow_up=[
            "Clínico cada 3-6 meses",
            "Electrolitos, renina (ajustar fludrocortisona)",
            "Evitar sobrerreemplazo (osteoporosis, síndrome Cushing iatrogénico)",
            "Tarjeta/brazalete de identificación de insuficiencia adrenal",
            "Densitometría ósea periódica",
        ],
    ),
    # =========================================================================
    # FEOCROMOCITOMA (E27.5)
    # =========================================================================
    "E27.5": MedicalCondition(
        icd10_code="E27.5",
        name="Feocromocitoma",
        category="Endocrinología",
        description="Tumor neuroendocrino productor de catecolaminas. 90% adrenales (feocromocitoma), 10% extraadrenales (paraganglioma). 10% malignos. Regla del 10%: 10% bilaterales, 10% familiares, 10% niños.",
        symptoms=[
            "TRÍADA CLÁSICA: cefalea, sudoración, palpitaciones",
            "Hipertensión paroxística o sostenida",
            "Palidez durante crisis (vasoconstricción)",
            "Ansiedad, ataques de pánico",
            "Pérdida de peso",
            "Intolerancia al calor",
            "Hiperglucemia",
            "Crisis pueden ser espontáneas o desencadenadas",
        ],
        risk_factors=[
            "Síndromes hereditarios (40%): MEN2, VHL, NF1, SDHB/C/D",
            "Historia familiar de feocromocitoma",
            "Mutaciones germinales en genes SDH",
        ],
        complications=[
            "Crisis hipertensiva - EMERGENCIA",
            "Miocardiopatía por catecolaminas",
            "ACV, IAM",
            "Arritmias",
            "Edema pulmonar",
            "Muerte súbita si cirugía sin preparación",
        ],
        diagnostic_criteria=[
            "Metanefrinas fraccionadas plasmáticas (SENSIBILIDAD 96-99%)",
            "Metanefrinas urinarias 24h",
            "TAC/RM adrenal: masa adrenal típica",
            "Gammagrafía con MIBG: localización y metástasis",
            "PET 68Ga-DOTATATE: paragangliomas, metástasis",
            "Estudio genético recomendado en todos",
        ],
        differential_diagnosis=[
            "Hipertensión esencial",
            "Trastorno de ansiedad/pánico",
            "Hipertiroidismo",
            "Carcinoide",
            "Abuso de cocaína/anfetaminas",
            "Síndrome de abstinencia",
        ],
        treatment_protocol=[
            "PREPARACIÓN PREOPERATORIA obligatoria (2-4 semanas):",
            "Alfa-bloqueador: Fenoxibenzamina 10-40 mg c/12h o Doxazosina",
            "Beta-bloqueador: agregar DESPUÉS de alfa-bloqueo (Propranolol)",
            "Hidratación, dieta con sal (expandir volumen)",
            "CIRUGÍA: Adrenalectomía laparoscópica (curativa en 90%)",
            "MALIGNOS: I-131 MIBG, quimioterapia, terapia dirigida",
        ],
        emergency_signs=[
            "Crisis hipertensiva: PA >220/120 mmHg",
            "Encefalopatía hipertensiva",
            "Edema agudo de pulmón",
            "Dolor torácico (isquemia miocárdica)",
            "Crisis durante inducción anestésica",
        ],
        prognosis="Benigno resecado: curación >90%. Maligno: supervivencia 50% a 5 años. Seguimiento de por vida por riesgo de recurrencia.",
        follow_up=[
            "Metanefrinas 2-4 semanas post-cirugía, luego anual x 10 años",
            "Estudio genético si no realizado",
            "Screening familiar si mutación identificada",
            "Imágenes si metanefrinas elevadas post-cirugía",
        ],
    ),
    # =========================================================================
    # HIPERLIPIDEMIA (E78)
    # =========================================================================
    "E78": MedicalCondition(
        icd10_code="E78",
        name="Hiperlipidemia",
        category="Endocrinología",
        description="Elevación de lípidos plasmáticos. Hipercolesterolemia (LDL), hipertrigliceridemia, dislipidemia mixta. Factor de riesgo cardiovascular mayor.",
        symptoms=[
            "Generalmente asintomático",
            "Xantomas (tendinosos, tuberosos, eruptivos)",
            "Xantelasmas (depósitos palpebrales)",
            "Arco corneal (menores de 45 años)",
            "Lipemia retinalis (triglicéridos muy altos)",
            "Pancreatitis aguda (TG >500-1000 mg/dL)",
        ],
        risk_factors=[
            "Dieta alta en grasas saturadas",
            "Obesidad",
            "Sedentarismo",
            "Historia familiar de hiperlipidemia o ECV prematura",
            "Diabetes mellitus",
            "Hipotiroidismo",
            "Síndrome nefrótico",
            "Medicamentos (tiazidas, beta-bloqueadores, antipsicóticos)",
        ],
        complications=[
            "Enfermedad coronaria (IAM)",
            "ACV isquémico",
            "Enfermedad arterial periférica",
            "Pancreatitis aguda (hipertrigliceridemia)",
            "Esteatosis hepática",
        ],
        diagnostic_criteria=[
            "Perfil lipídico en ayunas (9-12 horas):",
            "Colesterol total >200 mg/dL",
            "LDL-C >130 mg/dL (o según riesgo CV)",
            "HDL-C <40 mg/dL (hombres), <50 mg/dL (mujeres)",
            "Triglicéridos >150 mg/dL",
            "No-HDL-C = CT - HDL (objetivo si TG >200)",
        ],
        differential_diagnosis=[
            "Dislipidemia primaria (familiar)",
            "Dislipidemia secundaria (DM, hipotiroidismo, ERC)",
            "Inducida por fármacos",
            "Síndrome metabólico",
        ],
        treatment_protocol=[
            "CAMBIOS ESTILO DE VIDA: dieta mediterránea, ejercicio 150 min/sem",
            "ESTATINAS (1ª línea): según riesgo CV",
            "Riesgo muy alto (ASCVD): LDL <55 mg/dL (Atorvastatina/Rosuvastatina alta intensidad)",
            "Riesgo alto: LDL <70 mg/dL",
            "EZETIMIBE 10 mg: añadir si no alcanza objetivo",
            "INHIBIDORES PCSK9: si muy alto riesgo y no alcanza objetivo",
            "FIBRATOS: hipertrigliceridemia >500 mg/dL",
            "OMEGA-3 (icosapent etil): TG elevados + alto riesgo CV",
        ],
        emergency_signs=[
            "Pancreatitis por hipertrigliceridemia (TG >1000 mg/dL)",
            "Síndrome coronario agudo",
            "ACV",
        ],
        prognosis="Estatinas reducen eventos CV 25-35%. Control de LDL reduce progresión de aterosclerosis.",
        follow_up=[
            "Perfil lipídico 4-12 semanas post-inicio tratamiento",
            "Transaminasas si síntomas musculares o uso de dosis altas",
            "CK si mialgias",
            "Una vez estable: perfil lipídico anual",
        ],
    ),
    # =========================================================================
    # OBESIDAD (E66)
    # =========================================================================
    "E66": MedicalCondition(
        icd10_code="E66",
        name="Obesidad",
        category="Endocrinología",
        description="Acumulación anormal o excesiva de grasa corporal. IMC ≥30 kg/m². Enfermedad crónica multifactorial. Pandemia global con múltiples comorbilidades.",
        symptoms=[
            "IMC ≥30 kg/m²",
            "Circunferencia abdominal aumentada (>102 cm H, >88 cm M)",
            "Disnea de esfuerzo",
            "Fatiga",
            "Dolor articular (rodillas, espalda)",
            "Apnea del sueño, ronquidos",
            "Reflujo gastroesofágico",
            "Sudoración excesiva",
            "Intertrigo en pliegues",
        ],
        risk_factors=[
            "Dieta hipercalórica",
            "Sedentarismo",
            "Factores genéticos (50-70% heredabilidad)",
            "Factores socioeconómicos",
            "Trastornos del sueño",
            "Medicamentos (antipsicóticos, antidepresivos, corticoides)",
            "Endocrinopatías (hipotiroidismo, Cushing - raros)",
        ],
        complications=[
            "Diabetes mellitus tipo 2",
            "Hipertensión arterial",
            "Dislipidemia",
            "Enfermedad cardiovascular",
            "Apnea obstructiva del sueño",
            "Hígado graso no alcohólico (NAFLD/NASH)",
            "Osteoartritis",
            "Cáncer (mama, colon, endometrio)",
            "Infertilidad",
        ],
        diagnostic_criteria=[
            "IMC = peso (kg) / altura² (m)",
            "Sobrepeso: IMC 25-29.9 kg/m²",
            "Obesidad grado I: IMC 30-34.9 kg/m²",
            "Obesidad grado II: IMC 35-39.9 kg/m²",
            "Obesidad grado III (mórbida): IMC ≥40 kg/m²",
            "Circunferencia abdominal: riesgo aumentado si >102 cm (H), >88 cm (M)",
        ],
        differential_diagnosis=[
            "Edema/retención de líquidos",
            "Hipotiroidismo",
            "Síndrome de Cushing",
            "Lipodistrofia",
            "Síndromes genéticos (Prader-Willi)",
        ],
        treatment_protocol=[
            "INTERVENCIÓN ESTILO DE VIDA intensiva (1ª línea):",
            "Déficit calórico 500-750 kcal/día → pérdida 0.5-1 kg/semana",
            "Dieta: mediterránea, baja en carbohidratos, o déficit calórico",
            "Ejercicio: 150-300 min/semana moderado + fuerza",
            "Apoyo conductual/psicológico",
            "FARMACOTERAPIA si IMC ≥30 o ≥27 con comorbilidades:",
            "Semaglutida 2.4 mg SC semanal (Wegovy) - 15-17% pérdida",
            "Tirzepatida (Mounjaro) - hasta 20% pérdida",
            "Liraglutida 3 mg SC diario",
            "CIRUGÍA BARIÁTRICA si IMC ≥40 o ≥35 con comorbilidades:",
            "Bypass gástrico, gastrectomía en manga",
        ],
        emergency_signs=[
            "Síndrome de hipoventilación-obesidad (hipercapnia)",
            "Apnea del sueño severa no tratada",
            "Descompensación de comorbilidades",
        ],
        prognosis="Pérdida de peso 5-10% mejora significativamente comorbilidades. Cirugía bariátrica: remisión DM2 30-60%, reducción mortalidad CV.",
        follow_up=[
            "Peso y circunferencia abdominal cada visita",
            "Screening de comorbilidades (glucemia, perfil lipídico, PA)",
            "TSH (descartar hipotiroidismo)",
            "Evaluación nutricional y conductual",
            "Post-cirugía bariátrica: suplementación vitamínica de por vida",
        ],
    ),
    # =========================================================================
    # HIPONATREMIA (E87.1)
    # =========================================================================
    "E87.1": MedicalCondition(
        icd10_code="E87.1",
        name="Hiponatremia",
        category="Endocrinología",
        description="Sodio sérico <135 mEq/L. Trastorno electrolítico más común en hospitalizados. Causas: SIADH, diuréticos, insuficiencia cardíaca, cirrosis, polidipsia.",
        symptoms=[
            "Leve (130-135): frecuentemente asintomático",
            "Moderada (125-130): náuseas, cefalea, malestar",
            "Severa (<125): confusión, letargia, calambres",
            "Crítica (<120): convulsiones, coma, paro respiratorio",
            "Velocidad de instalación determina severidad",
        ],
        risk_factors=[
            "Edad avanzada",
            "Diuréticos tiazídicos",
            "ISRS y otros psicofármacos",
            "Insuficiencia cardíaca",
            "Cirrosis hepática",
            "Hipotiroidismo",
            "Insuficiencia adrenal",
            "Cirugía reciente",
            "Maratones (hiponatremia del ejercicio)",
        ],
        complications=[
            "Edema cerebral - EMERGENCIA",
            "Convulsiones",
            "Herniación cerebral",
            "Síndrome de desmielinización osmótica (corrección rápida)",
            "Muerte",
        ],
        diagnostic_criteria=[
            "Sodio sérico <135 mEq/L",
            "Evaluar osmolaridad sérica: <280 mOsm/kg = hipotonía verdadera",
            "Evaluar volemia clínica",
            "Sodio urinario: >30 mEq/L sugiere SIADH o diuréticos",
            "Osmolaridad urinaria: >100 mOsm/kg = respuesta ADH presente",
            "Descartar causas secundarias: TSH, cortisol",
        ],
        differential_diagnosis=[
            "Pseudohiponatremia (hiperproteinemia, hiperlipidemia)",
            "Hiponatremia hipertónica (hiperglucemia)",
            "SIADH",
            "Hipovolemia (vómitos, diarrea, hemorragia)",
            "Hipervolemia (ICC, cirrosis, síndrome nefrótico)",
            "Insuficiencia adrenal",
        ],
        treatment_protocol=[
            "ASINTOMÁTICO CRÓNICO: restricción hídrica 1-1.5 L/día",
            "TRATAR CAUSA de base",
            "DIURÉTICOS: suspender tiazidas, considerar furosemida si hipervolémico",
            "SIADH: restricción hídrica, tolvaptán (vaptanes)",
            "SINTOMÁTICO AGUDO - EMERGENCIA:",
            "NaCl 3% IV: 100-150 mL en bolo 10-20 min, repetir x2-3 si persisten síntomas",
            "Objetivo: elevar Na 4-6 mEq/L en primeras horas",
            "NO exceder 8-10 mEq/L en 24 horas (riesgo desmielinización)",
        ],
        emergency_signs=[
            "Convulsiones",
            "Alteración severa del sensorio, coma",
            "Signos de herniación cerebral",
            "Sodio <120 mEq/L sintomático",
        ],
        prognosis="Depende de causa y velocidad de corrección. Desmielinización osmótica por corrección rápida puede ser devastadora.",
        follow_up=[
            "Sodio sérico cada 2-4 horas durante corrección aguda",
            "Monitoreo neurológico",
            "Identificar y tratar causa subyacente",
            "Educación sobre restricción hídrica si crónico",
        ],
    ),
    # =========================================================================
    # HIPERKALEMIA (E87.5)
    # =========================================================================
    "E87.5": MedicalCondition(
        icd10_code="E87.5",
        name="Hiperkalemia",
        category="Endocrinología",
        description="Potasio sérico >5.0 mEq/L. Potencialmente letal por arritmias. Causas: insuficiencia renal, medicamentos (IECA, espironolactona), destrucción celular, insuficiencia adrenal.",
        symptoms=[
            "Frecuentemente asintomático hasta niveles peligrosos",
            "Debilidad muscular, fatiga",
            "Parestesias",
            "Parálisis flácida (severa)",
            "Palpitaciones, bradicardia",
            "Náuseas, diarrea",
        ],
        risk_factors=[
            "Enfermedad renal crónica (causa principal)",
            "IECA/ARA-II",
            "Espironolactona, eplerenona",
            "AINEs",
            "Suplementos de potasio",
            "Diabetes (hipoaldosteronismo hiporreninémico)",
            "Insuficiencia adrenal",
            "Hemólisis, rabdomiólisis, lisis tumoral",
        ],
        complications=[
            "Arritmias cardíacas - EMERGENCIA",
            "Fibrilación ventricular, asistolia",
            "Parálisis respiratoria",
            "Muerte súbita",
        ],
        diagnostic_criteria=[
            "Potasio sérico >5.0 mEq/L",
            "Confirmar no es pseudohiperkalemia (hemólisis, trombocitosis, leucocitosis)",
            "ECG obligatorio: cambios progresivos",
            "K 5.5-6.0: ondas T picudas",
            "K 6.0-7.0: prolongación PR, aplanamiento P",
            "K >7.0: ensanchamiento QRS, ondas sinusoidales",
            "Evaluar función renal, medicamentos",
        ],
        differential_diagnosis=[
            "Pseudohiperkalemia (muestra hemolizada)",
            "Redistribución: acidosis, déficit insulina, beta-bloqueadores",
            "Insuficiencia renal",
            "Insuficiencia adrenal",
            "Medicamentos",
        ],
        treatment_protocol=[
            "ESTABILIZACIÓN MEMBRANA (si cambios ECG):",
            "Gluconato de calcio 10% 10-20 mL IV en 2-3 min",
            "REDISTRIBUIR POTASIO:",
            "Insulina regular 10 U IV + Dextrosa 50% 50 mL",
            "Salbutamol nebulizado 10-20 mg",
            "Bicarbonato de sodio si acidosis",
            "ELIMINAR POTASIO:",
            "Furosemida 40-80 mg IV si función renal preservada",
            "Resinas: Patiromer, sulfonato de poliestireno sódico",
            "Hemodiálisis: si severo, refractario o ERC terminal",
            "SUSPENDER medicamentos que elevan K+",
        ],
        emergency_signs=[
            "K+ >6.5 mEq/L",
            "Cambios ECG (ensanchamiento QRS, arritmias)",
            "Debilidad muscular progresiva",
            "Bradicardia severa",
        ],
        prognosis="Mortal si no se trata. Con tratamiento adecuado, excelente recuperación. Prevención en pacientes de riesgo es clave.",
        follow_up=[
            "Potasio sérico cada 2-4 horas durante tratamiento agudo",
            "ECG seriado",
            "Identificar y eliminar causas",
            "Ajustar medicamentos crónicos",
            "Educación sobre dieta baja en potasio en ERC",
        ],
    ),
    # =========================================================================
    # HIPOCALCEMIA (E83.5)
    # =========================================================================
    "E83.5": MedicalCondition(
        icd10_code="E83.5",
        name="Hipocalcemia",
        category="Endocrinología",
        description="Calcio sérico corregido <8.5 mg/dL o calcio ionizado <4.6 mg/dL. Causas: hipoparatiroidismo (post-quirúrgico más común), déficit vitamina D, insuficiencia renal.",
        symptoms=[
            "Parestesias peribucales y extremidades",
            "Calambres musculares",
            "Tetania (espasmo carpopedal)",
            "Signo de Chvostek positivo (espasmo facial)",
            "Signo de Trousseau positivo (espasmo mano con manguito)",
            "Laringoespasmo",
            "Convulsiones",
            "Prolongación QT en ECG",
            "Depresión, confusión",
        ],
        risk_factors=[
            "Cirugía tiroidea/paratiroidea (hipoparatiroidismo)",
            "Déficit de vitamina D",
            "Insuficiencia renal crónica",
            "Malabsorción intestinal",
            "Pancreatitis aguda",
            "Hipomagnesemia",
            "Síndrome de hueso hambriento post-paratiroidectomía",
        ],
        complications=[
            "Tetania generalizada - EMERGENCIA",
            "Laringoespasmo, broncoespasmo",
            "Convulsiones",
            "Arritmias (prolongación QT → Torsades)",
            "Insuficiencia cardíaca",
            "Cataratas (crónico)",
        ],
        diagnostic_criteria=[
            "Calcio sérico corregido <8.5 mg/dL",
            "Corrección por albúmina: Ca corregido = Ca + 0.8 × (4 - albúmina)",
            "Calcio ionizado <4.6 mg/dL (más preciso)",
            "PTH: baja en hipoparatiroidismo, alta si causa es déficit vit D o renal",
            "Vitamina D (25-OH): evaluar deficiencia",
            "Magnesio: descartar hipomagnesemia",
            "Fósforo: alto en hipoparatiroidismo, bajo en déficit vit D",
        ],
        differential_diagnosis=[
            "Hipoparatiroidismo",
            "Déficit de vitamina D",
            "ERC con hiperparatiroidismo secundario",
            "Pseudohipoparatiroidismo",
            "Hipomagnesemia",
            "Pancreatitis aguda",
        ],
        treatment_protocol=[
            "HIPOCALCEMIA SINTOMÁTICA/SEVERA - EMERGENCIA:",
            "Gluconato de calcio 10% 10-20 mL IV lento (10 min)",
            "Seguido de infusión: 50-100 mL gluconato Ca 10% en 500 mL D5W a 1-2 mg/kg/h",
            "Corregir hipomagnesemia concomitante",
            "HIPOCALCEMIA CRÓNICA:",
            "Carbonato de calcio 500-1000 mg c/8h con comidas",
            "Vitamina D: Calcitriol 0.25-0.5 mcg/día (si hipoparatiroidismo)",
            "Colecalciferol 1000-4000 UI/día (si déficit vit D)",
        ],
        emergency_signs=[
            "Tetania, espasmo carpopedal",
            "Laringoespasmo, estridor",
            "Convulsiones",
            "QT prolongado, arritmias",
            "Calcio <7.0 mg/dL",
        ],
        prognosis="Excelente con tratamiento adecuado. Hipoparatiroidismo requiere suplementación de por vida.",
        follow_up=[
            "Calcio sérico cada 6-12 horas durante tratamiento IV",
            "Calcio y fósforo sérico periódico (evitar hipercalcemia)",
            "Calcio urinario 24h (evitar hipercalciuria → nefrolitiasis)",
            "Vitamina D anual",
            "Densitometría ósea en casos crónicos",
        ],
    ),
}

# Estadísticas del módulo
ENDOCRINE_STATS = {
    "total": len(ENDOCRINE_CONDITIONS),
    "category": "Endocrinología y Metabolismo",
}

if __name__ == "__main__":
    print(f"Condiciones Endocrinas: {ENDOCRINE_STATS['total']} cargadas")
    for code, cond in ENDOCRINE_CONDITIONS.items():
        print(f"  {code}: {cond.name}")
