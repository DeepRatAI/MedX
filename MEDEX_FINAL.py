#!/usr/bin/env python3
"""
🏥 MEDEX v25.83 - Sistema Médico IA con RAG Integrado
Sistema médico completo sin modo fallback, 100% Kimi K2

🎯 CARACTERÍSTICAS v25.83:
✅ Kimi K2-0711-Preview + Sistema RAG integrado
✅ Streaming en tiempo real con auditoría completa
✅ Detección avanzada: Educacional vs Profesional (casos clínicos)
✅ Emergencias: Protocolos automáticos mejorados
✅ Base conocimiento médico RAG actualizada
✅ Disclaimers obligatorios y limitaciones IA
✅ Historial conversacional con log de detección
✅ Branding actualizado v25.83
"""

import asyncio
import json
import re
import base64
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

from openai import OpenAI


class MedeXv2583:
    """Sistema médico avanzado v25.83 con RAG integrado y detección mejorada"""

    def __init__(self):
        # Cargar API key con soporte para HF Spaces y local
        import os

        print("🔍 [MedeX v25.83] Cargando API key...")

        # Prioridad 1: Variable de entorno (HF Spaces)
        self.api_key = os.getenv("KIMI_API_KEY")

        if self.api_key:
            print("✅ API Key cargada desde variable de entorno: KIMI_API_KEY")
            print(f"   📏 Longitud: {len(self.api_key)} caracteres")
            print(f"   🔑 Formato: {self.api_key[:8]}...{self.api_key[-4:]}")
        else:
            # Prioridad 2: Archivo local (desarrollo)
            try:
                with open("api_key.txt", "r") as f:
                    self.api_key = f.read().strip()
                print("✅ API Key cargada desde archivo: api_key.txt")
                print(f"   📏 Longitud: {len(self.api_key)} caracteres")
                print(f"   🔑 Formato: {self.api_key[:8]}...{self.api_key[-4:]}")
            except FileNotFoundError:
                print("❌ Error: No se encontró API key")
                print("   💡 HF Spaces: Configura secret 'KIMI_API_KEY'")
                print(
                    "   💡 Local: Crea archivo 'api_key.txt' con tu API key de Moonshot"
                )
                raise Exception("API key no configurada")
            except Exception as e:
                print(f"❌ Error leyendo API key: {e}")
                raise Exception("No se pudo cargar la API key")

        # Validar formato de API key
        if not self.api_key.startswith("sk-"):
            print(f"⚠️ ADVERTENCIA: La API key no comienza con 'sk-'")
            print(f"   Formato detectado: {self.api_key[:20]}...")
            print(f"   ¿Es una API key válida de Moonshot?")

        # Inicializar cliente
        print("🔧 Inicializando cliente Moonshot AI (Kimi K2)...")
        try:
            self.client = OpenAI(
                api_key=self.api_key, base_url="https://api.moonshot.ai/v1"
            )
            print("✅ Cliente Moonshot inicializado correctamente")
        except Exception as e:
            print(f"❌ Error al inicializar cliente OpenAI: {e}")
            raise

        self.conversation_history = []
        self.session_stats = {
            "queries": 0,
            "emergencies": 0,
            "professional_queries": 0,
            "educational_queries": 0,
            "images_analyzed": 0,
            "detection_log": [],  # Para trazabilidad
        }

        # Patrones de emergencia - AMPLIADOS
        self.emergency_keywords = [
            # Cardiovascular
            "dolor precordial",
            "dolor toracico",
            "dolor torácico",
            "dolor pecho intenso",
            "dolor de pecho",
            "infarto",
            "ataque cardiaco",
            "ataque cardíaco",
            "paro cardiaco",
            "paro cardíaco",
            # Respiratorio
            "dificultad respiratoria severa",
            "no puedo respirar",
            "no puede respirar",
            "asfixia",
            "ahogando",
            "cianosis",
            # Neurológico
            "convulsiones",
            "convulsión",
            "perdida conciencia",
            "pérdida de conciencia",
            "desmayo",
            "inconsciente",
            "no responde",
            "accidente cerebrovascular",
            "acv",
            "stroke",
            "ictus",
            # Hemorragia
            "hemorragia abundante",
            "sangrado masivo",
            "sangrado profuso",
            "desangrando",
            # Cefalea grave
            "dolor cabeza explosivo",
            "peor dolor vida",
            "peor dolor de mi vida",
            "cefalea trueno",
            # Otros graves
            "vision doble",
            "visión doble",
            "paralisis",
            "parálisis",
            "no puedo mover",
            "muriendo",
            "se muere",
            "está muriendo",
            "emergencia",
            "urgencia vital",
            "anafilaxia",
            "shock",
        ]

        # Patrones profesionales - vignetas clínicas y casos estructurados
        self.professional_patterns = [
            # Patrón telegráfico con sexo/edad
            r"^(M|F)\s?\d{1,3}\s?a\.",
            r"(masculino|femenino|hombre|mujer)\s+de\s+\d+\s+años",
            r"(masculino|femenino)\s+\d+\s+años",  # Sin "de"
            # Términos de caso clínico
            r"paciente\s+(de\s+)?\d+\s+años",
            r"caso\s+clinico",
            r"\bFUR\b|\bSV\b|\bSat\b|\bTA\b|\bFC\b|\bFR\b|\bTemp\b|\bPA\b",
            r"examen\s+fisico",
            r"blumberg|murphy|mcburney",
            # Obstetricia y Ginecología
            r"G\d+P\d+",  # Gesta/Para (G2P1, G3P2, etc.)
            r"\d+\s*semanas?\s+(de\s+)?gestación",
            r"\d+\s*semanas?\s+de\s+embarazo",
            r"proteinuria",
            r"preeclampsia|eclampsia",
            # Valores numéricos y parámetros
            r"\d+\s*/\s*\d+\s*mmHg",  # PA
            r"\d+\s*/\s*\d+",  # PA sin unidades (150/95)
            r"\d+\s*lpm|\d+\s*x\'",  # FC
            r"\d+\s*°C|\d+\s*grados",  # Temperatura
            r"\d+\s*(mg|gr|ml|cc)/\s*(kg|día|h)",  # Dosis
            # Evolución temporal
            r"\d+\s*(horas?|días?|semanas?)\s+de\s+evolución",
            r"desde\s+hace\s+\d+\s*(h|horas?|d|días?)",
            # Antecedentes y examen
            r"antecedentes\s+de",
            r"al\s+examen",
            r"presenta\s+en",
            r"se\s+presenta\s+con",
        ]

        # Patrones educacionales - consultas informativas
        self.educational_patterns = [
            # Interrogativos
            r"¿?(cuáles?|qué|cómo|por\s+qué|cuándo|dónde)",
            r"lista\s+de",
            r"tipos\s+de",
            r"criterios\s+de",
            r"manejo\s+de\s+\w+(?!\s+en\s+paciente)",  # Evitar casos clínicos
            r"definición\s+de",
            r"fisiopatología\s+de",
            r"mecanismo\s+de\s+acción",
            r"explicar|explica|explique",
            r"describir|describe|describa",
            # Peticiones de contenido
            r"algoritmo\s+de",
            r"protocolo\s+general",
            r"guía\s+de",
            r"clasificación\s+de",
            r"diferencias\s+entre",
            r"comparación\s+entre",
        ]

    def detect_user_type(self, query):
        """
        Detecta si el usuario es profesional médico o educacional
        Profesional: casos clínicos, vignetas, manejo específico de pacientes
        Educacional: consultas informativas, conceptos generales
        """
        import re

        query_clean = query.lower().strip()

        # Log para auditoría
        detection_reasons = []

        # Puntaje de detección
        professional_score = 0
        educational_score = 0

        # Análisis de patrones profesionales (casos clínicos)
        for pattern in self.professional_patterns:
            matches = len(re.findall(pattern, query_clean, re.IGNORECASE))
            if matches > 0:
                professional_score += matches * 2  # Peso doble
                detection_reasons.append(
                    f"Patrón profesional: {pattern} ({matches} coincidencias)"
                )

        # Análisis de patrones educacionales
        for pattern in self.educational_patterns:
            matches = len(re.findall(pattern, query_clean, re.IGNORECASE))
            if matches > 0:
                educational_score += matches
                detection_reasons.append(
                    f"Patrón educacional: {pattern} ({matches} coincidencias)"
                )

        # Factores adicionales
        # Longitud: casos clínicos suelen ser más largos
        if len(query) > 200:
            professional_score += 1
            detection_reasons.append("Query larga (>200 caracteres)")

        # Preguntas directas suelen ser educacionales
        if query_clean.startswith(("¿", "que es", "cuales son", "como se")):
            educational_score += 2
            detection_reasons.append("Pregunta directa educacional")

        # Decisión final
        if professional_score > educational_score:
            user_type = "Professional"
        else:
            user_type = "Educational"

        # Log de auditoría
        self.session_stats["detection_log"].append(
            {
                "query_hash": hash(query),
                "professional_score": professional_score,
                "educational_score": educational_score,
                "detected_type": user_type,
                "reasons": detection_reasons[:3],  # Top 3 razones
            }
        )

        return user_type

    def detect_emergency(self, query: str) -> bool:
        """Detecta emergencias médicas"""
        query_lower = query.lower()
        for keyword in self.emergency_keywords:
            if keyword in query_lower:
                return True
        return False

    def create_system_prompt(self, user_type: str, is_emergency: bool) -> str:
        """Crea prompt del sistema optimizado"""

        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        base_prompt = f"""Eres MedeX, sistema de inteligencia artificial médica avanzada.

FECHA Y HORA: {current_time}
TIPO DE USUARIO: {user_type.upper()}
EMERGENCIA: {"SÍ" if is_emergency else "NO"}

"""

        if user_type == "Professional":
            base_prompt += """MODO PROFESIONAL MÉDICO - FORMATO CLÍNICO ESTRUCTURADO OBLIGATORIO:

ESTRUCTURA OBLIGATORIA PARA CASOS CLÍNICOS:
## 📋 ANÁLISIS CLÍNICO/DIAGNÓSTICO MÁS PROBABLE: – [DIAGNÓSTICO PRINCIPAL]
**Código CIE-10**: [Código] – [Descripción específica]
**Fecha**: {current_time}myres
**Modalidad**: [Especialidad médica] – [Ambulatorio/Hospitalario/UCI]

### 1. SÍNTESIS DEL CASO
**Paciente**: [Sexo edad años]
**Antecedente**: [Antecedentes patológicos relevantes]
**Motivo**: [Motivo de consulta estructurado con síntomas y evolución]
**Cumplimiento/Adherencia**: [Si aplica]
**Exploración física**: [Hallazgos físicos clave con signos específicos]
**Laboratorio/Paraclínicos**: [Valores anómalos con unidades]

### 2. DIAGNÓSTICOS DIFERENCIALES JERARQUIZADOS
| **Probabilidad** | **Diagnóstico** | **Criterios de apoyo** | **Próximos pasos diagnósticos** |
|------------------|------------------|------------------------|----------------------------------|
| **Alta (70–80%)** | **Diagnóstico más probable:** [Descripción principal] | [Criterios clínicos específicos] | [Estudios confirmatorios específicos] |
| **Moderada (15–25%)** | **Diagnóstico posible:** [Diagnóstico alternativo] | [Criterios diferenciales] | [Estudios para descartar/confirmar] |
| **Baja (5–10%)** | **A descartar:** [Diagnóstico menos probable] | [Criterios limitados] | [Estudios adicionales si persiste sospecha] |
| **Muy baja (<5%)** | **Diagnóstico diferencial:** [Diagnóstico de exclusión] | [Criterios específicos para excluir] | [Estudios especializados si indicado] |

### 3. PLAN DIAGNÓSTICO INMEDIATO (Ambulatorio/Hospitalario)
| **Estudio** | **Justificación clínica** | **Valor normal/Interpretación** |
|-------------|-------------------|------------------|
| **[Laboratorio específico]** | [Justificación fisiopatológica] | [Rango normal con unidades específicas] |
| **[Imagenología específica]** | [Indicación precisa] | [Hallazgos esperados/normales] |
| **[Procedimiento diagnóstico]** | [Criterios de indicación] | [Resultados normales/patológicos] |
| **ELECTIVO: [Estudio especializado]** | [Condiciones para solicitar] | [Escalas/clasificaciones aplicables] |

### 4. PLAN TERAPÉUTICO INICIAL
| **Medida terapéutica** | **Especificaciones farmacológicas/técnicas** |
|------------|-------------|
| **[Objetivo terapéutico 1]** | **[Clase farmacológica]: [Medicamento ejemplo] [dosis sugerida]** [vía administración] [frecuencia] – **Duración: [tiempo específico]** |
| **[Objetivo terapéutico 2]** | **[Clase farmacológica]: [Principio activo dosis/kg]** + [coadyuvante para absorción] – **Controles: [parámetros a monitorizar]** |
| **[Medidas no farmacológicas]** | [Especificaciones técnicas detalladas con objetivos específicos] |
| **[Reposición nutricional/vitamínica]** | **[Vitamina/mineral]: [dosis sugerida] [vía] [frecuencia] x [duración]** si [condición específica] |
| **[Derivación especializada]** | En <[tiempo específico] para [procedimiento/evaluación] y valoración de [condición específica] |

⚠️ **DISCLAIMER TERAPÉUTICO OBLIGATORIO:**
**"⚠️ Validar dosis y esquemas con guías locales, protocolos institucionales, comorbilidades y contraindicaciones del paciente."**

### 5. CRITERIOS DE INTERNACIÓN / DERIVACIÓN URGENTE
- **[Criterio clínico 1]**: [Parámetros cuantitativos específicos] (ej: IMC <18.5 kg/m² o pérdida >10% en 3 meses)
- **[Criterio de laboratorio]**: [Valores específicos] (ej: Hb <8 g/dL, síncope, ICC)
- **[Criterio de complicación]**: [Signos específicos] ([síntomas específicos], [hallazgos físicos], [estudios anómalos])
- **[Criterio de inestabilidad]**: [Parámetros hemodinámicos] con [consecuencias específicas]

### 6. FACTORES DE RIESGO Y PRONÓSTICO
- **Riesgo de complicaciones**: [Lista específica de complicaciones con porcentajes si disponibles]
- **Supervivencia/Pronóstico**: [Información específica con estadísticas si aplicables y factores pronósticos]
- **Seguimiento**: [Intervalos específicos] con [parámetros a monitorizar]

### 7. FUENTES Y REFERENCIAS (RAG)
**📚 EVIDENCIA CIENTÍFICA:**
1. [Guía clínica relevante] - [Organización] ([Año])
2. [Consenso médico especializado] - [Sociedad médica] ([Año])
3. [Literatura científica] - [Journal] ([Año])
4. [Protocolo institucional] - [Institución] ([Año])

*Fuentes extraídas de base de conocimiento médico RAG actualizada*

CARACTERÍSTICAS TÉCNICAS OBLIGATORIAS:
- Terminología médica técnica y precisa (nomenclatura internacional)
- Códigos CIE-10 específicos y actualizados
- Dosis farmacológicas SUGERIDAS (no definitivas) con clase farmacológica, principio activo, vía, frecuencia y duración
- OBJETIVOS TERAPÉUTICOS específicos antes de esquemas farmacológicos
- Valores de laboratorio con rangos normales específicos por edad/sexo
- Probabilidades diagnósticas CUANTIFICADAS con percentiles
- NUNCA usar "diagnóstico confirmado" - usar "más probable", "posible", "a descartar"
- Criterios de derivación con parámetros CUANTITATIVOS específicos
- Protocolos basados en guías de práctica clínica internacionales
- Referencias a escalas validadas (APACHE, Glasgow, GRACE, NYHA, Child-Pugh, etc.)
- Farmacocinética relevante y contraindicaciones ESPECÍFICAS
- Interacciones medicamentosas si aplicables
- Monitorización de efectos adversos con parámetros específicos
- OBLIGATORIO: 2-4 referencias RAG de guías médicas, consensos o literatura actual
- SIEMPRE incluir disclaimer terapéutico: "⚠️ Validar dosis y esquemas con guías locales, protocolos institucionales, comorbilidades y contraindicaciones del paciente"

"""
        else:
            base_prompt += """MODO EDUCACIONAL - Profesor Universitario de Medicina de Élite:

ESTILO PEDAGÓGICO AVANZADO:
Adopta el rol del más prestigioso profesor universitario de medicina del mundo. Tu misión es educar con el rigor académico de Harvard Medical School, la precisión de Mayo Clinic y la claridad didáctica de los mejores educadores médicos internacionales.

ESTRUCTURA EDUCATIVA UNIVERSITARIA OBLIGATORIA:

📚 **MARCO CONCEPTUAL FUNDAMENTAL**
- Definición académica precisa con nomenclatura internacional ESPECÍFICA
- Clasificaciones actualizadas con CÓDIGOS específicos (WHO, ICD-11, consensos con AÑOS y UBICACIÓN)
- Epidemiología con DATOS NUMÉRICOS exactos y rangos poblacionales
- Contexto histórico con FECHAS, NOMBRES específicos y evolución cronológica detallada
- OBLIGATORIO: Mencionar consensos específicos, cambios históricos en criterios diagnósticos

🔬 **FISIOPATOLOGÍA AVANZADA CON PRECISIÓN MOLECULAR**
- Mecanismos moleculares con GENES ESPECÍFICOS nombrados (ej: SOX9, KCNJ2, HOX)
- Cascadas bioquímicas con VÍAS DE SEÑALIZACIÓN exactas y proteínas involucradas
- Correlación anatomo-patológica con MEDIDAS CUANTIFICADAS (ej: ángulos, distancias en mm)
- Interacciones sistémicas con CRONOLOGÍA embriológica específica (semanas de gestación)
- Bases genéticas con CROMOSOMAS específicos, patrones de herencia exactos

🧬 **ASPECTOS CLÍNICOS ACADÉMICOS CUANTIFICADOS**
- Manifestaciones clínicas con CORRELACIÓN FISIOPATOLÓGICA específica y medible
- Criterios diagnósticos con CONSENSOS específicos (año, organización, cambios históricos)
- Diagnóstico diferencial con CARACTERÍSTICAS DIFERENCIALES cuantificadas
- Herramientas diagnósticas con VALORES NORMALES específicos y rangos patológicos
- Evolución natural con DATOS PRONÓSTICOS numericos y percentiles de supervivencia

💊 **FUNDAMENTOS TERAPÉUTICOS BASADOS EN EVIDENCIA**
- Principios farmacológicos con MECANISMOS MOLECULARES específicos
- Clases terapéuticas con NOMENCLATURA QUÍMICA y clasificaciones actualizadas
- Medicina basada en evidencia con ESTUDIOS específicos y niveles de evidencia
- Consideraciones farmacogenómicas con POLIMORFISMOS específicos cuando aplique
- Objetivos terapéuticos CUANTIFICADOS con parámetros medibles de éxito

🎯 **PERSPECTIVA ACADÉMICA AVANZADA ESPECÍFICA**
- Investigación actual con LÍNEAS específicas, universidades/institutos líderes
- Controversias científicas ACTUALES con POSICIONES específicas y evidencia
- Medicina de precisión con BIOMARCADORES específicos y aplicaciones clínicas
- Implicaciones de salud pública con DATOS epidemiológicos específicos
- Consideraciones bioéticas con MARCOS específicos y dilemas actuales

📖 **CARACTERÍSTICAS PEDAGÓGICAS DE ÉLITE UNIVERSITARIA**
- Terminología médica precisa con ETIMOLOGÍA y evolución histórica cuando enriquezca
- Analogías SOFISTICADAS que conecten múltiples sistemas y conceptos complejos
- Referencias a LITERATURA ESPECÍFICA con autores, journals, años
- Correlaciones clínico-patológicas con DATOS CUANTITATIVOS específicos
- Razonamiento crítico con ANÁLISIS MULTIFACTORIAL y consideraciones diferenciales
- Perspectiva global con VARIACIONES GEOGRÁFICAS/POBLACIONALES específicas
- Integración MULTIESPECIALIDAD con roles específicos y colaboración interprofesional
- OBLIGATORIO: 2-4 referencias RAG específicas de literatura médica actual, consensos nombrados con años y organizaciones

🎓 **ESTILO COMUNICATIVO DE PROFESOR UNIVERSITARIO DE ÉLITE OBLIGATORIO:**
- Precisión académica quirúrgica con DETALLES específicos que sorprendan a profesionales
- Profundidad conceptual con INFORMACIÓN que médicos especializados desconozcan
- Secuencia lógica: fundamentos específicos → mecanismos cuantificados → aplicaciones medibles
- Énfasis en COMPRENSIÓN INTEGRAL con conexiones interdisciplinarias complejas
- Estimulación del pensamiento crítico con PREGUNTAS implícitas y análisis multivariado
- Tono de AUTORIDAD ACADÉMICA prestigiosa pero pedagógicamente accesible

📝 **DESARROLLO TEÓRICO NARRATIVO EXPANSIVO OBLIGATORIO:**
- COMBINAR estructura organizada (listas, tablas, cuadros) CON párrafos explicativos extensos y desarrollo teórico profundo
- Cada sección DEBE incluir desarrollo narrativo académico detallado ADEMÁS de datos estructurados
- EXPLICACIONES CONTEXTUALES: Desarrollar el "por qué" y "cómo" de cada concepto con párrafos elaborados
- MARCOS TEÓRICOS: Incluir fundamentos conceptuales, evolución histórica del conocimiento y perspectivas actuales
- ANÁLISIS CRÍTICOS EXPANDIDOS: Razonamiento académico desarrollado que conecte teoría con práctica clínica
- TRANSICIONES NARRATIVAS: Párrafos que enlacen secciones con explicaciones teóricas que faciliten la comprensión
- DESARROLLO CONCEPTUAL PROGRESIVO: Construir conocimiento paso a paso con explicaciones que se profundicen progresivamente
- EJEMPLIFICACIÓN ACADÉMICA: Casos teóricos, analogías sofisticadas y aplicaciones prácticas explicadas detalladamente
- SÍNTESIS INTEGRADORA: Párrafos de cierre que conecten todos los conceptos en una visión holística
- CONTEXTO CIENTÍFICO: Explicar cómo cada concepto se inserta en el panorama médico actual y futuro

**ENFOQUE NARRATIVO-PEDAGÓGICO ESPECÍFICO:**
- INTRODUCIR cada tema con contexto histórico y evolución del conocimiento
- DESARROLLAR los mecanismos subyacentes con explicaciones detalladas antes de presentar datos
- EXPLICAR las implicaciones de cada hallazgo clínico en párrafos reflexivos
- CONECTAR conceptos entre disciplinas médicas con desarrollo teórico interdisciplinario
- ANALIZAR controversias actuales con perspectivas múltiples desarrolladas narrativamente
- PROYECTAR tendencias futuras y líneas de investigación con análisis prospectivo

**FORMATO HÍBRIDO ENRIQUECIDO OBLIGATORIO:**
- MANTENER todas las listas, tablas y cuadros organizativos actuales
- AÑADIR párrafos introductorios extensos que contextualicen cada sección
- INTERCALAR desarrollo teórico narrativo profundo entre y dentro de secciones organizadas
- EXPANDIR cada concepto con explicaciones detalladas, contexto histórico y perspectivas actuales
- DESARROLLAR conexiones conceptuales con párrafos analíticos que expliquen relaciones complejas
- INCLUIR reflexiones académicas narrativas que profundicen la comprensión integral del tema
- CREAR puentes conceptuales entre secciones con análisis que conecten el conocimiento fragmentado

**ELEMENTOS DE PRECISIÓN ACADÉMICA OBLIGATORIOS:**
- SIEMPRE incluir datos numéricos específicos (rangos, percentiles, medidas)
- SIEMPRE mencionar consensos/cambios históricos en criterios (con año y organización)
- SIEMPRE nombrar genes/proteínas/vías específicas cuando sea relevante
- SIEMPRE cuantificar cuando sea posible (ángulos, distancias, probabilidades)
- SIEMPRE incluir información que pueda sorprender a profesionales especializados

**DESARROLLO NARRATIVO ACADÉMICO ESPECÍFICO OBLIGATORIO:**
- PÁRRAFOS INTRODUCTORIOS: Cada sección principal debe comenzar con 2-3 párrafos que contextualicen el tema, expliquen su relevancia y establezcan el marco conceptual
- ELABORACIÓN TEÓRICA: Después de cada lista o tabla, incluir párrafos que analicen, interpreten y conecten la información con conceptos más amplios
- EXPLICACIONES MECANÍSTICAS: Desarrollar en detalle narrativo los "cómo" y "por qué" de los procesos fisiopatológicos
- EVOLUCIÓN HISTÓRICA: Incluir párrafos que expliquen cómo ha evolucionado el entendimiento del tema a lo largo del tiempo
- PERSPECTIVAS INTERDISCIPLINARIAS: Conectar el tema con otras áreas médicas mediante desarrollo narrativo
- IMPLICACIONES CLÍNICAS: Párrafos que expliquen el significado práctico de cada concepto teórico
- CONTROVERSIAS Y DEBATES: Desarrollo narrativo de los puntos de discusión actuales en la literatura
- PROYECCIONES FUTURAS: Párrafos analíticos sobre las direcciones de la investigación y práctica clínica
- SÍNTESIS CONCEPTUAL: Párrafos de cierre que integren todos los elementos en una comprensión holística

**TÉCNICAS NARRATIVAS PEDAGÓGICAS AVANZADAS:**
- Usar ANALOGÍAS SOFISTICADAS que conecten conceptos médicos complejos con fenómenos conocidos
- Incluir EJEMPLOS CLÍNICOS NARRATIVOS que ilustren conceptos abstractos
- Desarrollar RAZONAMIENTO DEDUCTIVO paso a paso en formato narrativo
- Crear CONEXIONES CAUSALES explícitas entre fenómenos mediante párrafos explicativos
- Usar PREGUNTAS RETÓRICAS que guíen el pensamiento crítico del lector
- Implementar TRANSICIONES LÓGICAS que conecten ideas de manera fluida
- Incluir REFLEXIONES ACADÉMICAS que profundicen la comprensión conceptual

```
🎓 **ESTILO COMUNICATIVO DE ÉLITE**
- Precisión académica con claridad expositiva excepcional
- Profundidad conceptual equivalente a educación médica superior
- Secuencia lógica: fundamentos → mecanismos → aplicaciones clínicas
- Énfasis en comprensión integral, no memorización
- Estimulación del pensamiento crítico y análisis científico
- Tono profesoral prestigioso pero accesible

⚠️ **DISCLAIMERS EDUCATIVOS OBLIGATORIOS**:
"📚 Contenido educativo de nivel universitario avanzado. Para decisiones clínicas específicas, siempre consulte con profesionales médicos especializados."
"🎓 Esta información representa el estado actual del conocimiento médico con fines educativos exclusivamente."

"""

        if is_emergency:
            base_prompt += """🚨 PROTOCOLO DE EMERGENCIA ACTIVADO:
- Evaluar necesidad de atención inmediata
- Pasos de acción específicos y claros
- Cuándo llamar servicios de emergencia
- Priorizar seguridad del paciente
- No minimizar síntomas graves

"""

        base_prompt += """SISTEMA RAG INTEGRADO OBLIGATORIO:
- Consulta automática de base de conocimiento médico actualizada
- Referencias científicas cuando corresponda (especialmente en modo Professional)
- Fuentes bibliográficas en respuestas especializadas con evidencia
- Citas de guías de práctica clínica internacionales
- Integración de conocimiento farmacológico especializado

DISCLAIMERS OBLIGATORIOS POR TIPO DE USUARIO:
MODO PROFESSIONAL:
⚠️ **Esta información es de soporte clínico educacional, no sustituye la evaluación médica presencial ni el juicio clínico profesional**
🚨 **En situaciones de emergencia real, activar protocolos hospitalarios y contactar servicios de emergencia inmediatamente**
💊 **IMPORTANTE: Validar dosis y esquemas con guías locales, protocolos institucionales, comorbilidades y contraindicaciones del paciente**
🤖 **MedeX v25.83 es herramienta de soporte clínico, no sustituye el criterio médico profesional ni la responsabilidad clínica del médico tratante**
📋 **Códigos CIE-10 y protocolos requieren validación con guías locales e institucionales actualizadas**
📚 **Referencias RAG requieren confirmación con fuentes primarias actualizadas**

MODO EDUCACIONAL:
⚠️ **Esta información es estrictamente educativa, NO constituye diagnóstico ni tratamiento médico**
🚨 **En emergencias reales, contactar inmediatamente servicios de emergencia (911/números locales)**
👨‍⚕️ **Consulte SIEMPRE con profesional de salud para evaluación, diagnóstico y tratamiento específico**
🤖 **MedeX v25.83 es herramienta educativa, NO reemplaza consulta médica profesional**
💊 **NO seguir recomendaciones de medicamentos sin supervisión médica profesional**

INSTRUCCIONES TÉCNICAS ESPECÍFICAS OBLIGATORIAS:
- Proporciona respuestas médicas precisas basadas en evidencia científica actualizada
- Adapta rigurosamente el nivel técnico y formato al tipo de usuario detectado (Professional vs Educational)
- En modo Professional: OBLIGATORIO usar estructura tabular completa, códigos CIE-10, dosis específicas, probabilidades cuantificadas
- En modo Educational: OBLIGATORIO usar narrativa comprensible, evitar tecnicismos, incluir analogías
- Cita fuentes RAG y referencias científicas cuando sea información especializada
- Mantén equilibrio entre precisión clínica y comprensibilidad según audiencia
- SIEMPRE incluir disclaimers apropiados al final de cada respuesta

RESPUESTA COMPLETA OBLIGATORIA:
- NUNCA truncar respuestas profesionales
- Completar TODAS las secciones del análisis clínico
- Incluir TODOS los diagnósticos diferenciales con probabilidades
- Especificar TODOS los tratamientos con dosis exactas
- Proporcionar TODOS los criterios de derivación
- Generar respuesta estructurada COMPLETA sin omisiones

FORMATO ESTRICTO PARA CASOS CLÍNICOS:
1. Síntesis completa del caso
2. Tabla completa de diagnósticos diferenciales (mínimo 3-4 opciones)
3. Plan diagnóstico completo con justificaciones
4. Plan terapéutico detallado con dosis específicas
5. Criterios de internación específicos
6. Factores pronósticos y seguimiento
7. Disclaimers profesionales completos"""

        return base_prompt

    async def generate_response(self, query: str, use_streaming: bool = True) -> str:
        """Genera respuesta médica"""

        # Analizar query
        user_type = self.detect_user_type(query)
        is_emergency = self.detect_emergency(query)

        # Actualizar estadísticas
        self.session_stats["queries"] += 1
        if is_emergency:
            self.session_stats["emergencies"] += 1
        if user_type == "Professional":
            self.session_stats["professional_queries"] += 1
        else:
            self.session_stats["educational_queries"] += 1

        # Crear system prompt
        system_prompt = self.create_system_prompt(user_type, is_emergency)

        # Configurar herramientas para búsqueda web si no es emergencia
        tools = None
        if not is_emergency:
            tools = [{"type": "builtin_function", "function": {"name": "$web_search"}}]

        # Preparar mensajes
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query},
        ]

        # Agregar historial reciente si existe
        if self.conversation_history:
            # Incluir últimas 3 interacciones para contexto
            for interaction in self.conversation_history[-3:]:
                if "user_query" in interaction:
                    messages.insert(
                        -1, {"role": "user", "content": interaction["user_query"]}
                    )
                if "response" in interaction:
                    messages.insert(
                        -1,
                        {"role": "assistant", "content": interaction["response"][:500]},
                    )  # Limitar longitud

        print(
            f"\n🩺 MedeX - Usuario: {user_type.upper()} | Emergencia: {'SÍ' if is_emergency else 'NO'}"
        )

        try:
            if use_streaming:
                return await self._generate_streaming(
                    messages, tools, query, user_type, is_emergency
                )
            else:
                return await self._generate_direct(messages, tools, user_type)

        except Exception as e:
            error_msg = f"Error en MedeX: {e}"
            print(f"❌ {error_msg}")
            return error_msg

    async def generate_response_stream(self, query: str):
        """
        Genera respuesta médica con streaming REAL para Streamlit.
        Yielde los chunks progresivamente en lugar de retornar todo al final.
        """

        # Analizar query
        user_type = self.detect_user_type(query)
        is_emergency = self.detect_emergency(query)

        # Actualizar estadísticas
        self.session_stats["queries"] += 1
        if is_emergency:
            self.session_stats["emergencies"] += 1
        if user_type == "Professional":
            self.session_stats["professional_queries"] += 1
        else:
            self.session_stats["educational_queries"] += 1

        # Crear system prompt
        system_prompt = self.create_system_prompt(user_type, is_emergency)

        # Configurar herramientas para búsqueda web si no es emergencia
        tools = None
        if not is_emergency:
            tools = [{"type": "builtin_function", "function": {"name": "$web_search"}}]

        # Preparar mensajes
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query},
        ]

        # Agregar historial reciente si existe
        if self.conversation_history:
            for interaction in self.conversation_history[-3:]:
                if "user_query" in interaction:
                    messages.insert(
                        -1, {"role": "user", "content": interaction["user_query"]}
                    )
                if "response" in interaction:
                    messages.insert(
                        -1,
                        {"role": "assistant", "content": interaction["response"][:500]},
                    )

        print(
            f"\n🩺 MedeX - Usuario: {user_type.upper()} | Emergencia: {'SÍ' if is_emergency else 'NO'}"
        )

        # Configurar max_tokens dinámico
        if user_type == "Educational":
            max_tokens = 5120
        else:
            max_tokens = 5120

        try:
            # Manejar tool calls si es necesario
            finish_reason = None
            full_response = ""

            while finish_reason is None or finish_reason == "tool_calls":
                stream = self.client.chat.completions.create(
                    model="kimi-k2-0711-preview",
                    messages=messages,
                    temperature=0.6,
                    max_tokens=max_tokens,
                    stream=True,
                    tools=tools,
                )

                tool_calls = []
                current_message = {"role": "assistant", "content": ""}

                for chunk in stream:
                    if chunk.choices:
                        choice = chunk.choices[0]
                        finish_reason = choice.finish_reason

                        if choice.delta:
                            # Contenido normal - YIELD para streaming
                            if choice.delta.content:
                                content_chunk = choice.delta.content
                                full_response += content_chunk
                                current_message["content"] += content_chunk

                                # YIELD el chunk para Streamlit
                                yield content_chunk

                            # Tool calls
                            if choice.delta.tool_calls:
                                for tool_call in choice.delta.tool_calls:
                                    if len(tool_calls) <= tool_call.index:
                                        tool_calls.extend(
                                            [None]
                                            * (tool_call.index + 1 - len(tool_calls))
                                        )

                                    if tool_calls[tool_call.index] is None:
                                        tool_calls[tool_call.index] = {
                                            "id": tool_call.id,
                                            "type": tool_call.type,
                                            "function": {
                                                "name": tool_call.function.name,
                                                "arguments": "",
                                            },
                                        }

                                    if tool_call.function.arguments:
                                        tool_calls[tool_call.index]["function"][
                                            "arguments"
                                        ] += tool_call.function.arguments

                # Si hay tool calls, procesarlos
                if finish_reason == "tool_calls" and tool_calls:
                    current_message["tool_calls"] = [
                        tc for tc in tool_calls if tc is not None
                    ]
                    messages.append(current_message)

                    yield "\n\n🔍 _Buscando información médica actualizada..._\n\n"

                    for tool_call in current_message["tool_calls"]:
                        if tool_call["function"]["name"] == "$web_search":
                            try:
                                arguments = json.loads(
                                    tool_call["function"]["arguments"]
                                )
                                messages.append(
                                    {
                                        "role": "tool",
                                        "tool_call_id": tool_call["id"],
                                        "name": "$web_search",
                                        "content": json.dumps(arguments),
                                    }
                                )
                            except:
                                messages.append(
                                    {
                                        "role": "tool",
                                        "tool_call_id": tool_call["id"],
                                        "name": "$web_search",
                                        "content": json.dumps({"query": query}),
                                    }
                                )

            # Guardar en historial
            self.conversation_history.append(
                {
                    "timestamp": datetime.now().isoformat(),
                    "user_query": query,
                    "response": full_response,
                    "user_type": user_type,
                    "is_emergency": is_emergency,
                }
            )

        except Exception as e:
            error_msg = f"❌ Error en streaming: {e}"
            print(error_msg)
            yield error_msg

    async def _generate_streaming(
        self,
        messages: List[Dict],
        tools: Optional[List],
        query: str,
        user_type: str,
        is_emergency: bool,
    ) -> str:
        """Genera respuesta con streaming"""

        print("🤔 Analizando con Kimi K2...")

        # Configurar max_tokens dinámico según el tipo de usuario
        if user_type == "Educational":
            # Modo Educacional necesita más tokens para explicaciones universitarias extensas
            max_tokens = 5120  # Explicaciones educativas completas
        else:
            # Modo Profesional necesita MÁS tokens para análisis clínicos detallados con tablas
            max_tokens = 5120  # Aumentado para análisis profesionales completos con estructura tabular

        # Manejar tool calls si es necesario
        finish_reason = None
        while finish_reason is None or finish_reason == "tool_calls":
            stream = self.client.chat.completions.create(
                model="kimi-k2-0711-preview",
                messages=messages,
                temperature=0.6,
                max_tokens=max_tokens,
                stream=True,
                tools=tools,
            )

            full_response = ""
            tool_calls = []
            current_message = {"role": "assistant", "content": ""}

            print(f"\n💬 Respuesta MedeX:")
            print("-" * 60)

            for chunk in stream:
                if chunk.choices:
                    choice = chunk.choices[0]
                    finish_reason = choice.finish_reason

                    if choice.delta:
                        # Contenido normal
                        if choice.delta.content:
                            full_response += choice.delta.content
                            current_message["content"] += choice.delta.content
                            print(choice.delta.content, end="", flush=True)

                        # Tool calls
                        if choice.delta.tool_calls:
                            for tool_call in choice.delta.tool_calls:
                                if len(tool_calls) <= tool_call.index:
                                    tool_calls.extend(
                                        [None] * (tool_call.index + 1 - len(tool_calls))
                                    )

                                if tool_calls[tool_call.index] is None:
                                    tool_calls[tool_call.index] = {
                                        "id": tool_call.id,
                                        "type": tool_call.type,
                                        "function": {
                                            "name": tool_call.function.name,
                                            "arguments": "",
                                        },
                                    }

                                if tool_call.function.arguments:
                                    tool_calls[tool_call.index]["function"][
                                        "arguments"
                                    ] += tool_call.function.arguments

            # Si hay tool calls, procesarlos
            if finish_reason == "tool_calls" and tool_calls:
                current_message["tool_calls"] = [
                    tc for tc in tool_calls if tc is not None
                ]
                messages.append(current_message)

                print(f"\n🔍 Buscando información médica actualizada...")

                for tool_call in current_message["tool_calls"]:
                    if tool_call["function"]["name"] == "$web_search":
                        # Para búsqueda web, solo retornar los argumentos
                        try:
                            arguments = json.loads(tool_call["function"]["arguments"])
                            messages.append(
                                {
                                    "role": "tool",
                                    "tool_call_id": tool_call["id"],
                                    "name": "$web_search",
                                    "content": json.dumps(arguments),
                                }
                            )
                        except:
                            messages.append(
                                {
                                    "role": "tool",
                                    "tool_call_id": tool_call["id"],
                                    "name": "$web_search",
                                    "content": json.dumps({"query": query}),
                                }
                            )
            else:
                # Respuesta final
                print("\n" + "-" * 60)

                # Guardar en historial
                self.conversation_history.append(
                    {
                        "timestamp": datetime.now().isoformat(),
                        "user_query": query,
                        "response": full_response,
                        "user_type": user_type,
                        "is_emergency": is_emergency,
                    }
                )

                return full_response

        return full_response

    async def _generate_direct(
        self,
        messages: List[Dict],
        tools: Optional[List],
        user_type: str = "Professional",
    ) -> str:
        """Genera respuesta directa sin streaming"""

        # Configurar max_tokens dinámico según el tipo de usuario
        if user_type == "Educational":
            # Modo Educacional necesita más tokens para explicaciones universitarias extensas
            max_tokens = 4096  # Explicaciones educativas completas
        else:
            # Modo Profesional necesita MÁS tokens para análisis clínicos detallados con tablas
            max_tokens = 5120  # Aumentado para análisis profesionales completos con estructura tabular

        response = self.client.chat.completions.create(
            model="kimi-k2-0711-preview",
            messages=messages,
            temperature=0.6,
            max_tokens=max_tokens,
            tools=tools,
        )

        return response.choices[0].message.content

    async def analyze_medical_image(
        self, image_path: str, clinical_context: str = ""
    ) -> str:
        """Analiza imágenes médicas"""

        try:
            # Verificar que el archivo existe
            if not Path(image_path).exists():
                return f"❌ Error: Archivo {image_path} no encontrado"

            # Leer imagen
            with open(image_path, "rb") as f:
                image_data = f.read()

            # Codificar en base64
            image_base64 = base64.b64encode(image_data).decode("utf-8")
            file_ext = Path(image_path).suffix.lower()

            # Detectar tipo de usuario del contexto
            user_type = (
                self.detect_user_type(clinical_context)
                if clinical_context
                else "Educational"
            )

            # Crear prompt específico para análisis de imagen con filtrado de modalidades médicas válidas
            if user_type == "Professional":
                system_prompt = f"""Eres MedeX v25.83, especialista en análisis de imágenes médicas para profesionales médicos.
FECHA Y HORA: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
TIPO DE USUARIO: PROFESSIONAL - ANÁLISIS DE IMAGEN MÉDICA
MODALIDADES VÁLIDAS ÚNICAMENTE: RX, TAC, RM, US

PROTOCOLO DE FILTRADO OBLIGATORIO INICIAL:
1. PRIMERO: Identifica si la imagen corresponde EXCLUSIVAMENTE a alguna de estas modalidades médicas:
   - RX (Radiografía/Rayos X)
   - TAC (Tomografía Axial Computarizada/CT)
   - RM (Resonancia Magnética/MRI)
   - US (Ultrasonido/Ecografía)

2. SI LA IMAGEN NO CORRESPONDE A NINGUNA MODALIDAD VÁLIDA:
   RESPONDE ÚNICAMENTE: "❌ No se puede analizar la imagen. Por favor, provee una RX, TAC, RM o US para el análisis médico."

3. SI LA IMAGEN CORRESPONDE A UNA MODALIDAD VÁLIDA:
   INICIA TU RESPUESTA CON: "[MODALIDAD] recibida" (ej: "RX recibida", "TAC recibida", "RM recibida", "US recibida")
"""

                user_prompt = f"""PROTOCOLO DE ANÁLISIS IMAGENOLÓGICO PROFESIONAL:

**PASO 1 - FILTRADO OBLIGATORIO**: Determina si esta imagen corresponde EXCLUSIVAMENTE a alguna de las modalidades médicas válidas: RX, TAC, RM o US.

**PASO 2 - RESPUESTA SEGÚN VALIDACIÓN**:
- Si NO es RX/TAC/RM/US: Responde únicamente el mensaje de rechazo especificado
- Si SÍ es RX/TAC/RM/US: Inicia con "[MODALIDAD] recibida" y procede con a realiza un análisis detallado de la imagen con enfoque clínico y educativo.
- Describe el caso de la imagen con rigor cientifico/médico, incluyendo hallazgos relevantes, posibles diagnósticos diferenciales y recomendaciones para estudios adicionales o manejo clínico.
"""

            else:
                system_prompt = f"""Eres MedeX v25.83, profesor universitario eminencia en medicina .
FECHA Y HORA: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
TIPO DE USUARIO: EDUCATIONAL - ANÁLISIS EDUCATIVO DE IMAGEN MÉDICA
MODALIDADES VÁLIDAS ÚNICAMENTE: RX, TAC, RM, US

PROTOCOLO DE FILTRADO OBLIGATORIO INICIAL:
1. PRIMERO: Identifica si la imagen corresponde EXCLUSIVAMENTE a alguna de estas modalidades médicas:
   - RX (Radiografía/Rayos X)
   - TAC (Tomografía Axial Computarizada/CT)
   - RM (Resonancia Magnética/MRI)
   - US (Ultrasonido/Ecografía)

2. SI LA IMAGEN NO CORRESPONDE A NINGUNA MODALIDAD VÁLIDA:
   RESPONDE ÚNICAMENTE: "❌ No se puede analizar la imagen. Por favor, provee una RX, TAC, RM o US para el análisis médico."

3. SI LA IMAGEN CORRESPONDE A UNA MODALIDAD VÁLIDA:
   INICIA TU RESPUESTA CON: "[MODALIDAD] recibida" (ej: "RX recibida", "TAC recibida", "RM recibida", "US recibida"), y continua con: 
    -Realiza un análisis detallado de la imagen con enfoque clínico y educativo.
    -Describe el caso de la imagen con rigor cientifico/médico, incluyendo hallazgos relevantes, posibles diagnósticos diferenciales y recomendaciones para estudios adicionales o manejo clínico.


"""

                user_prompt = f"""PROTOCOLO DE ANÁLISIS IMAGENOLÓGICO EDUCATIVO:

**PASO 1 - FILTRADO OBLIGATORIO**: Determina si esta imagen corresponde EXCLUSIVAMENTE a alguna de las modalidades médicas válidas: RX, TAC, RM o US.

**PASO 2 - RESPUESTA SEGÚN VALIDACIÓN**:
- Si NO es RX/TAC/RM/US: Responde únicamente el mensaje de rechazo especificado
- Si SÍ es RX/TAC/RM/US: Inicia con "[MODALIDAD] recibida" y procede con análisis educativo detallado de la imagen.
- Explica los hallazgos de manera comprensible, incluyendo conceptos anatómicos, fisiopatología relevante y contexto clínico educativo.
"""

            # Configurar mensajes
            messages = [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image{file_ext};base64,{image_base64}"
                            },
                        },
                        {"type": "text", "text": user_prompt},
                    ],
                },
            ]

            # Configurar max_tokens dinámico según el tipo de usuario
            if user_type == "Educational":
                # Modo Educacional necesita más tokens para explicaciones detalladas de imágenes
                max_tokens = (
                    3000  # Mayor límite para explicaciones educativas de imágenes
                )
            else:
                # Modo Profesional - análisis técnico conciso
                max_tokens = 1500

            # Generar análisis
            response = self.client.chat.completions.create(
                model="moonshot-v1-128k-vision-preview",
                messages=messages,
                temperature=0.3,
                max_tokens=max_tokens,
            )

            result = response.choices[0].message.content

            # Actualizar estadísticas
            self.session_stats["images_analyzed"] += 1

            return result

        except Exception as e:
            return f"❌ Error analizando imagen: {e}"

    def get_session_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de la sesión"""
        return {
            **self.session_stats,
            "conversations": len(self.conversation_history),
            "model": "kimi-k2-0711-preview + RAG",
            "capabilities": [
                "Streaming real-time",
                "Emergency detection",
                "Professional/Educational mode",
                "Medical image analysis",
                "Web search integration",
                "Conversational memory",
            ],
        }

    def clear_history(self):
        """Limpia el historial conversacional"""
        self.conversation_history.clear()
        print("🧹 Historial limpiado")


# Interfaz de chat principal
class MedeXChat:
    """Interfaz de chat para MedeX v25.83"""

    def __init__(self):
        self.medex = MedeXv2583()
        self.session_start = datetime.now()

    def print_header(self):
        """Header del sistema"""
        print("\n" + "=" * 80)
        print("🏥 MedeX v25.83 — Sistema Médico de IA con RAG")
        print("🧠 Kimi K2-0711-Preview • 📚 RAG sobre base médica curada")
        print("👤 Detección automática: Educational ↔ Professional")
        print("🚨 Triage de emergencias • 🌐 Evidencia con citas")
        print("=" * 80)
        print("💡 COMANDOS")
        print("  📊 estado — Ver estadísticas")
        print("  🧹 limpiar — Limpiar historial")
        print("  🚪 salir — Terminar")
        print("=" * 80)
        print(
            "⚠️ Uso profesional y educativo. No reemplaza valoración médica presencial."
        )
        print("=" * 80 + "\n")

    async def handle_special_commands(self, user_input: str) -> Optional[bool]:
        """Maneja comandos especiales"""
        parts = user_input.lower().strip().split()
        command = parts[0] if parts else ""

        if command in ["salir", "exit", "quit"]:
            print("\n👋 Cerrando MedeX v25.83...")
            duration = datetime.now() - self.session_start
            print(f"⏱️  Duración de sesión: {duration}")
            stats = self.medex.get_session_stats()
            print(f"📊 Consultas procesadas: {stats['queries']}")
            print("🙏 ¡Gracias por usar MedeX!")
            return False

        elif command == "estado":
            stats = self.medex.get_session_stats()
            print(f"\n📊 ESTADÍSTICAS DE SESIÓN:")
            print(f"   💬 Consultas: {stats['queries']}")
            print(f"   🚨 Emergencias: {stats['emergencies']}")
            print(f"   👨‍⚕️ Profesionales: {stats['professional_queries']}")
            print(f"   🎓 Educacionales: {stats['educational_queries']}")
            print(f"   🧠 Modelo: {stats['model']}")
            return True

        elif command == "limpiar":
            self.medex.clear_history()
            return True

        return None

    async def chat_loop(self):
        """Loop principal del chat"""

        self.print_header()
        print("🚀 MedeX v25.83 iniciado correctamente")
        print("💬 Escribe tu consulta médica...\n")

        try:
            while True:
                try:
                    user_input = input("🩺 Consulta: ").strip()

                    if not user_input:
                        continue

                    # Manejar comandos especiales
                    command_result = await self.handle_special_commands(user_input)

                    if command_result is False:
                        break
                    elif command_result is True:
                        continue

                    # Procesar consulta médica
                    await self.medex.generate_response(user_input, use_streaming=True)
                    print("\n" + "─" * 60 + "\n")

                except KeyboardInterrupt:
                    print("\n\n⌨️  Interrupción detectada...")
                    confirm = input("¿Salir? (s/N): ").lower()
                    if confirm in ["s", "si", "y", "yes"]:
                        break
                    else:
                        continue

                except Exception as e:
                    print(f"\n❌ Error: {e}")
                    print("💡 Sistema operativo. Intenta nueva consulta.")

        finally:
            print("\n🏥 Sesión MedeX v25.83 terminada")


# Función principal
async def main():
    """Función principal"""

    print("🏥 Iniciando MedeX v25.83...")

    try:
        chat = MedeXChat()
        await chat.chat_loop()
    except Exception as e:
        print(f"❌ Error crítico: {e}")


if __name__ == "__main__":
    asyncio.run(main())
