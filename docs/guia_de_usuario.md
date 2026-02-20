![MedeX Banner](../banner.png)

# 📖 Guía de Usuario de MedeX v25.83

> **[User Guide (English)](user_guide.md) | Guía de Usuario (Español)**

[![Volver al README Principal](https://img.shields.io/badge/← Volver%20al-README%20Principal-blue.svg)](../README.md)

---

## 🏥 **Bienvenido a MedeX v25.83**

MedeX v25.83 es un sistema avanzado de inteligencia artificial médica que **detecta automáticamente** si eres un **profesional de la salud** o un **usuario general**, adaptando sus respuestas según tu perfil. Este sistema está impulsado por **Kimi K2-0711-Preview** y cuenta con una base de conocimiento médico integral.

---

## 🎯 **Detección Automática de Usuarios**

### 🤖 **¿Cómo funciona la detección?**

MedeX v25.83 analiza automáticamente tu consulta para determinar tu perfil:

#### 👨‍⚕️ **Usuario PROFESIONAL** - Se detecta cuando usas:

- **Terminología médica especializada**: "paciente masculino de 45 años"
- **Signos vitales**: "PA 140/90, FC 110, SatO₂ 95%"
- **Código clínico**: "antecedente de HTA, DM2"
- **Casos clínicos**: descripciones detalladas de síntomas con contexto médico

#### 🎓 **Usuario EDUCATIVO** - Se detecta cuando preguntas:

- **Información general**: "¿Qué son los AINEs?"
- **Explicaciones básicas**: "¿Cómo funciona el corazón?"
- **Definiciones**: "Explícame qué es la diabetes"
- **Conceptos médicos básicos** sin terminología especializada

---

## 🚨 **Sistema de Detección de Emergencias**

### ⚡ **Activación Automática**

MedeX detecta automáticamente situaciones de emergencia cuando mencionas:

- **Síntomas críticos**: dolor torácico agudo, dificultad respiratoria severa
- **Signos de alarma**: pérdida de conciencia, sangrado abundante
- **Condiciones urgentes**: infarto, stroke, anafilaxia
- **Valores vitales críticos**: presión arterial extrema, frecuencia cardíaca peligrosa

#### 🔴 **Protocolo de Emergencia Activado**:

```
🚨 EMERGENCIA MÉDICA DETECTADA 🚨

⚠️ ACCIÓN INMEDIATA REQUERIDA:
1. Llamar al 911 o servicio de emergencias local
2. Si es posible, trasladar al centro médico más cercano
3. Seguir las instrucciones de los servicios de emergencia

📱 La información proporcionada NO sustituye atención médica inmediata
```

---

## 💬 **Tipos de Respuesta según Usuario**

### 👨‍⚕️ **Respuestas PROFESIONALES**

Cuando eres detectado como profesional, recibes:

#### **Formato Clínico Estructurado**:

```
📋 ANÁLISIS CLÍNICO/DIAGNÓSTICO MÁS PROBABLE: [Diagnóstico]
Código CIE-10: [Código] – [Descripción]
Fecha: [Timestamp]
Modalidad: [Especialidad] – [Ámbito]

1. SÍNTESIS DEL CASO
2. DIAGNÓSTICOS DIFERENCIALES JERARQUIZADOS
3. PLAN DIAGNÓSTICO INMEDIATO
4. PLAN TERAPÉUTICO INICIAL
5. CRITERIOS DE INTERNACIÓN / DERIVACIÓN
6. FACTORES DE RIESGO Y PRONÓSTICO
7. FUENTES Y REFERENCIAS (RAG)
```

#### **Características Profesionales**:

- **Códigos CIE-10** automáticos
- **Diagnósticos diferenciales** jerarquizados por probabilidad
- **Planes diagnósticos** con justificaciones clínicas
- **Protocolos terapéuticos** con dosis específicas
- **Referencias médicas** actualizadas
- **Disclaimers médicos** profesionales

### 🎓 **Respuestas EDUCATIVAS**

Cuando eres detectado como usuario general, recibes:

#### **Formato Didáctico Amigable**:

```
🔍 Información Médica General
📚 Explicaciones Simples y Claras
💡 Analogías Fáciles de Entender
⚠️ Cuándo Consultar a un Médico
📖 Información Adicional Útil
```

#### **Características Educativas**:

- **Lenguaje sencillo** sin jerga médica compleja
- **Analogías comprensibles** para conceptos médicos
- **Explicaciones paso a paso**
- **Ilustraciones conceptuales**
- **Recomendaciones de cuándo consultar** profesionales

---

## 🖥️ **Uso del Sistema**

### **Instalación Rápida**

```bash
# 1. Clonar repositorio
git clone https://github.com/tu-usuario/medex.git
cd medex

# 2. Crear entorno virtual
python3 -m venv medex_venv
source medex_venv/bin/activate  # Linux/Mac

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar API Key
# - Abre el archivo 'api_key.txt' (ya incluido en el repositorio)
# - Pega tu API key de https://platform.moonshot.ai/
# - Guarda el archivo

# 5. Ejecutar MedeX
python MEDEX_FINAL.py
```

### **Comandos del Sistema**

Una vez ejecutando MedeX, tienes estos comandos disponibles:

| Comando   | Función                       | Ejemplo   |
| --------- | ----------------------------- | --------- |
| `salir`   | Terminar sesión               | `salir`   |
| `estado`  | Ver estadísticas del sistema  | `estado`  |
| `limpiar` | Limpiar historial             | `limpiar` |
| `exit`    | Terminar sesión (alternativo) | `exit`    |
| `quit`    | Terminar sesión (alternativo) | `quit`    |

---

## 📚 **Ejemplos de Uso**

### 🎓 **Ejemplo: Consulta Educativa**

**Usuario pregunta**: "¿Qué son los AINEs?"

**MedeX detecta**: Usuario EDUCATIVO

**Respuesta de MedeX**:

```
🔍 ¿Qué son los AINEs?

Los AINEs son como los "bomberos" de tu cuerpo. Cuando algo se inflama
(como una lesión), tu cuerpo envía "mensajeros de alarma". Los AINEs
bloquean esos mensajeros para reducir:

💊 El DOLOR
🔥 La INFLAMACIÓN
🌡️ La FIEBRE

Ejemplos comunes:
- Ibuprofeno (Advil)
- Naproxeno (Aleve)
- Aspirina

⚠️ Consulta a tu médico antes de tomarlos regularmente
```

### 👨‍⚕️ **Ejemplo: Consulta Profesional**

**Usuario pregunta**: "Paciente masculino 45 años, fumador, dolor torácico opresivo irradiado a brazo izquierdo, 40 min evolución, PA 140/85, FC 110"

**MedeX detecta**: Usuario PROFESIONAL + posible EMERGENCIA

**Respuesta de MedeX**:

```
📋 ANÁLISIS CLÍNICO/DIAGNÓSTICO MÁS PROBABLE:
SÍNDROME CORONARIO AGUDO CON ELEVACIÓN DEL ST (SCACEST)

Código CIE-10: I21.9 – Infarto agudo de miocardio
Modalidad: Cardiología de Urgencia – Hospitalario/UCI

🚨 EMERGENCIA MÉDICA DETECTADA 🚨

DIAGNÓSTICOS DIFERENCIALES JERARQUIZADOS:
│ Probabilidad │ Diagnóstico │ Criterios │
│ Alta (85-90%) │ IAM ST+ │ Dolor típico >30min, factores riesgo │
│ Moderada (8-12%) │ Angina inestable │ Sin elevación ST │

PLAN DIAGNÓSTICO INMEDIATO:
- ECG 12 derivaciones en <10 min
- Troponina I/T alta sensibilidad
- Gasometría arterial
[... protocolo completo ...]
```

---

## ⚙️ **Características Avanzadas**

### 🧠 **Sistema RAG (Recuperación Aumentada)**

MedeX integra un sistema RAG que:

- **Busca automáticamente** en literatura médica
- **Encuentra referencias relevantes** para tu consulta
- **Cita fuentes específicas** en respuestas profesionales
- **Actualiza conocimiento** en tiempo real

### 📊 **Estadísticas de Sesión**

Usa `estado` para ver:

```
📊 ESTADÍSTICAS DE MEDEX v25.83
════════════════════════════════
Consultas totales: 15
├─ Consultas profesionales: 8 (53.3%)
├─ Consultas educativas: 6 (40.0%)
└─ Emergencias detectadas: 1 (6.7%)

Tiempo de sesión: 45 min
Usuario predominante: PROFESIONAL
Estado del sistema: ✅ ÓPTIMO
```

### 🔄 **Streaming en Tiempo Real**

Las respuestas aparecen progresivamente:

```
🤔 Analizando consulta...
🔍 Buscando en base de conocimiento...
📚 Consultando literatura médica...
💬 Generando respuesta personalizada...
✅ Respuesta completa
```

---

## 🛡️ **Limitaciones y Disclaimers**

### ⚠️ **IMPORTANTE: Limitaciones de MedeX**

#### **MedeX NO puede:**

- ❌ Diagnosticar enfermedades definitivamente
- ❌ Prescribir medicamentos específicos
- ❌ Reemplazar consulta médica profesional
- ❌ Interpretar estudios médicos complejos
- ❌ Proporcionar atención médica de emergencia real

#### **MedeX SÍ puede:**

- ✅ Proporcionar información médica educativa
- ✅ Sugerir posibles diagnósticos diferenciales
- ✅ Explicar conceptos médicos claramente
- ✅ Identificar cuándo buscar atención médica
- ✅ Dar pautas generales basadas en evidencia

### 🏥 **Uso Profesional Responsable**

**Para profesionales de la salud:**

- Usar como **herramienta de apoyo** únicamente
- Aplicar siempre **juicio clínico profesional**
- Verificar información con **fuentes primarias**
- Considerar **contexto específico** de cada paciente

---

## 🔧 **Solución de Problemas**

### ❓ **Problemas Comunes**

#### **"MedeX no me detecta como profesional"**

**Solución**: Usa terminología médica más específica:

```
❌ Incorrecto: "Persona con dolor de pecho"
✅ Correcto: "Paciente masculino 45 años con dolor torácico opresivo"
```

#### **"Las respuestas son demasiado básicas/complejas"**

**Solución**: MedeX se adapta automáticamente. Si necesitas cambiar el nivel:

```
Para más detalle: "Necesito información clínica detallada sobre..."
Para más simplicidad: "Explícame de forma sencilla qué es..."
```

#### **"Error de conexión con Kimi"**

**Solución**: Verificar configuración de API key:

```bash
# 1. Verificar que el archivo api_key.txt existe
ls -la api_key.txt

# 2. Verificar el contenido (debe contener solo tu API key)
cat api_key.txt

# 3. Editar el archivo si es necesario:
# - Abre api_key.txt con cualquier editor de texto
# - Pega únicamente tu API key de Moonshot (sin espacios extra)
# - Guarda el archivo
```

**Obtener API key**: Ve a [platform.moonshot.ai](https://platform.moonshot.ai/), crea una cuenta y genera tu API key.

#### **"Respuestas incompletas o cortadas"**

**Solución**: El sistema usa streaming. Espera unos segundos para la respuesta completa.

---

## 📈 **Casos de Uso Avanzados**

### 🏥 **Para Profesionales de la Salud**

#### **Consulta de Diagnóstico Diferencial**

```
"Paciente femenina 28 años con dolor abdominal RID, leucocitosis
15000, Blumberg positivo, ecografía con líquido libre"

→ MedeX proporciona diagnósticos diferenciales jerarquizados
→ Protocolos diagnósticos específicos
→ Criterios de derivación urgente
```

#### **Revisión de Protocolos**

```
"Protocolo manejo hipertensión arterial grado 2 en diabético"

→ Guías actualizadas basadas en evidencia
→ Algoritmos de tratamiento
→ Metas terapéuticas específicas
```

### 🎓 **Para Estudiantes de Medicina**

#### **Aprendizaje Conceptual**

```
"Explícame la fisiopatología de la insuficiencia cardíaca"

→ Explicación detallada pero comprensible
→ Diagramas conceptuales textuales
→ Correlación clínica práctica
```

### 🧑‍🎓 **Para Usuarios Generales**

#### **Educación en Salud**

```
"¿Cuándo debo preocuparme por un dolor de cabeza?"

→ Señales de alarma explicadas claramente
→ Cuándo consultar al médico
→ Medidas generales de alivio
```

---

## 🔗 **Enlaces Útiles**

### 📚 **Documentación**

- **[README Principal](../README.md)** - Información general del proyecto
- **[User Guide (English)](user_guide.md)** - This guide in English
- **[Ejemplos de Consultas](.)** - Consultas médicas reales procesadas

### 🎯 **Ejemplos de Consultas Médicas**

#### **Consultas Educativas**

- **[AINEs y sus Características](consulta_aines_caracteristicas.md)** - Información sobre antiinflamatorios
- **[Síndrome Pierre Robin](consulta_sindrome_pierre_robin.md)** - Malformación congénita
- **[Síndrome de Treacher Collins](consulta_sindrome_treacher_collins.md)** - Disostosis facial

#### **Consultas Profesionales**

- **[Enfermedad Celíaca](consulta_celiaca_malabsorcion.md)** - Caso gastroenterológico
- **[Dermatomiositis](consulta_dermatomiositis_adulto.md)** - Caso reumatológico
- **[Pleuritis Lúpica](consulta_pleuritis_lupica.md)** - Complicación en lupus
- **[Síndrome Coronario Agudo](consulta_sindrome_coronario_agudo.md)** - Emergencia cardíaca
- **[Diabetes Insípida](consulta_diabetes_insipida.md)** - Caso endocrinológico

---

## 📞 **Soporte y Contacto**

### 🐛 **Reportar Problemas**

- **GitHub Issues**: Para bugs y mejoras
- **Documentación**: Consultar esta guía primero

### 🤝 **Contribuir**

- **Fork del repo**: Para contribuir con código
- **Sugerencias**: Issues para nuevas características
- **Documentación**: Ayuda a mejorar las guías

---

## ⚠️ **DISCLAIMER MÉDICO FINAL**

**MedeX v25.83 es una herramienta de apoyo educativo e informativo. NO sustituye la consulta médica profesional, el diagnóstico médico, el tratamiento prescrito o las decisiones clínicas profesionales.**

**En caso de emergencia médica real:**

- 🚨 Contacte inmediatamente servicios de emergencia (911)
- 🏥 Acuda al centro médico más cercano
- 👨‍⚕️ No dependa únicamente de información de IA

**Para profesionales de la salud:**

- 🩺 Úselo solo como herramienta de apoyo
- 🧠 Aplique siempre su juicio clínico profesional
- 📚 Verifique información con fuentes primarias confiables
- 👥 Considere el contexto específico de cada paciente

---

🤖 **Desarrollado con IA responsable para el futuro de la medicina digital**

_Guía actualizada para MedeX v25.83 - Sistema de IA médica avanzada_
