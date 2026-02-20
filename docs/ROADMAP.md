# 🧭 MedeX ROADMAP — Evolución hacia un Asistente Clínico Integral

> Documento vivo. Última actualización: 2025-10-17  
> Autor: DeepRatAI  
> Versión inicial: v0.1.0  

---

## 🎯 Visión General

MedeX evolucionará desde un asistente RAG educativo hacia una **plataforma médica modular** que combine razonamiento clínico, gestión documental y trazabilidad completa de pacientes.

El objetivo es **construir progresivamente un sistema de soporte clínico integral**, sin romper compatibilidad con el entorno actual ni poner en riesgo la seguridad de los datos.

---

## 🧱 Filosofía de Desarrollo

1. **Modularidad progresiva**: cada nueva función debe poder operar de forma aislada.
2. **Seguridad por diseño**: los datos sensibles (PHI/PII) se separan desde la arquitectura base.
3. **Compatibilidad total**: el núcleo `medex` debe seguir funcionando en modo educativo/mock sin API keys.
4. **Trazabilidad y explicabilidad**: toda inferencia debe poder auditarse y justificarse.
5. **Ciencia antes que espectáculo**: las funcionalidades nuevas deben basarse en evidencia, no hype.

---

## 🧩 Roadmap de Versiones

### 🩺 v0.1.x — Base Estable y Mock Mode (Actual)
**Estado:** ✅ Completado  
**Fecha:** Octubre 2025  

- Paquete `medex/` estructurado y publicable.  
- CLI y API Python funcionales.  
- Modo Mock para entornos sin clave KIMI.  
- Streamlit legacy funcionando sin cambios.  
- Pruebas básicas CI/CD y documentación completa.  

---

### 🧬 v0.2.x — Sistema de Pacientes y Documentos Clínicos
**Objetivo:** vincular conversaciones, documentos y datos persistentes por paciente.  
**Estado:** 🔜 Planificación (Q4 2025)  

#### Funciones clave
- Creación y administración de **perfiles de pacientes** (ID único + metadata).  
- Registro automático de conversaciones y documentos por paciente.  
- Generador de **documentos clínicos estructurados** (recetas, evoluciones, epicrisis).  
- Almacenamiento seguro y auditado (Postgres con cifrado por campo).  
- CLI: `medex patient create` y `medex doc generate`.  

---

### 🧪 v0.3.x — Módulo Farmacéutico y Conocimiento Médico
**Objetivo:** ampliar las capacidades RAG con conocimiento farmacológico y fuentes verificadas.  
**Estado:** 🧩 Diseño inicial  

#### Funciones clave
- Base local de **medicamentos y principios activos** (offline).  
- Buscador semántico con embeddings y metadatos farmacológicos.  
- Integración controlada con websearch (solo dominios médicos verificados).  
- Función de interacción con el módulo RAG: *“check drug interactions”*.  
- API: `/pharma/search?q=` y `/pharma/interactions`.  

---

### 🧠 v0.4.x — Análisis de Imágenes Médicas
**Objetivo:** añadir soporte multimodal (texto + imagen).  
**Estado:** 🧩 Concepto en revisión  

#### Funciones clave
- Carga y vinculación de estudios DICOM/JPEG a pacientes.  
- Procesamiento asincrónico de imágenes (FastAPI + worker).  
- Extracción de metadatos DICOM (anonimizados).  
- Generación de informes automáticos con disclaimer clínico.  
- Integración visual opcional en Streamlit (“visor de hallazgos”).  

---

### 🔍 v0.5.x — Razonamiento Trazable y Explicabilidad
**Objetivo:** permitir auditar el proceso de razonamiento del sistema.  
**Estado:** 🚧 Investigación  

#### Funciones clave
- Registro completo de *context windows*, *retrievals* y *chains of thought simuladas*.  
- Dashboard de trazabilidad: seguimiento de cada inferencia paso a paso.  
- CLI: `medex trace <query>` muestra contexto y razonamiento usado.  
- Módulo de auditoría con visualización en tiempo real.  

---

### ☁️ v0.6.x — Integración Hospitalaria y Multiusuario
**Objetivo:** transformar MedeX en un asistente interoperable para entornos clínicos reales.  
**Estado:** 🔮 A largo plazo  

#### Funciones clave
- Sistema multiusuario con roles (`admin`, `clinician`, `auditor`).  
- Integración con sistemas de gestión hospitalaria (FHIR mock).  
- Base de datos de pacientes compartida entre profesionales autorizados.  
- API REST/GraphQL segura con autenticación por token o SSO.  
- Dashboard profesional: panel completo con métricas y trazabilidad.  

---

## 🔒 Principios Permanentes

| Principio | Descripción |
|------------|-------------|
| **Seguridad por diseño** | Separación física de PHI y datos operativos; cifrado obligatorio. |
| **Mock mode primero** | Ninguna demo pública procesa datos reales. |
| **Explicabilidad mínima** | Cada respuesta debe tener contexto o cita. |
| **Auditoría total** | Toda acción (documento, paciente, análisis) se registra en `audit_log`. |
| **Compatibilidad ascendente** | Los módulos nuevos no rompen el legacy ni el CLI. |

---

## 📆 Cronograma Estimado (Sujeto a Ajustes)

| Hito | Periodo estimado | Estado |
|------|------------------|--------|
| v0.2.0 - Sistema de pacientes y documentos | Noviembre–Diciembre 2025 | 🔜 |
| v0.3.0 - Base farmacéutica consultable | Enero 2026 | 🧩 |
| v0.4.0 - Análisis de imágenes médicas | Febrero 2026 | 🧩 |
| v0.5.0 - Razonamiento trazable y explicabilidad | Marzo 2026 | 🧪 |
| v0.6.0 - Integración hospitalaria | 2º semestre 2026 | 🔮 |

---

## 🧭 Cómo Contribuir

1. Revisa la rama `dev/roadmap-v0.2.0` antes de proponer nuevos módulos.  
2. Abre un issue con tipo `enhancement` y prefijo `[proposal]`.  
3. Toda nueva función debe venir con su propio test mínimo y docstring.  
4. Ninguna PR debe tocar el modo educativo/mock sin justificación técnica.  

---

**MedeX** es una investigación en curso sobre IA médica responsable.  
Su evolución se basa en **precisión, transparencia y trazabilidad**, no en velocidad.

---

_© 2025 DeepRatAI — Proyecto MedeX RAG_
