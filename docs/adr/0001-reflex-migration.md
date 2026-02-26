# ADR-0001: Migración de Streamlit a Reflex

**Fecha:** 2026-01-15  
**Estado:** Aceptado  
**Autor:** Gonzalo

## Contexto

MedeX originalmente utilizaba Streamlit como framework de UI. A medida que el proyecto
evolucionó hacia una plataforma médica profesional con múltiples módulos interactivos
(chat en tiempo real, herramientas médicas, triage, investigación profunda), las
limitaciones de Streamlit se hicieron evidentes.

### Limitaciones de Streamlit

1. **Modelo de re-ejecución completa**: Cada interacción del usuario re-ejecuta el
   script completo, lo que es ineficiente para aplicaciones con estado complejo.

2. **Sin WebSocket nativo**: Streamlit usa polling HTTP para actualizaciones, lo que
   impide streaming en tiempo real del LLM con baja latencia.

3. **Control limitado del layout**: La API de componentes no permite layouts
   responsivos complejos como el panel lateral con múltiples secciones desplegables
   que MedeX requiere.

4. **Estado global frágil**: `st.session_state` no escala bien cuando hay 50+
   variables de estado interrelacionadas (como en MedeXState).

5. **Sin soporte multi-página nativo**: Las soluciones de routing son workarounds,
   no primera clase.

## Decisión

**Adoptar Reflex (reflex.dev) como framework de UI.**

### Justificación

| Criterio | Streamlit | Reflex |
|----------|-----------|--------|
| Estado reactivo | Re-ejecución completa | Granular, por componente |
| WebSocket | No nativo | Nativo, bidireccional |
| Layout | Limitado | Full CSS/Flexbox/Grid |
| Backend | Implícito | FastAPI integrado |
| Despliegue | Streamlit Cloud | Cualquier infraestructura |
| Python puro | Sí | Sí |
| Componentes custom | Limitado | React wrapping completo |

### Factores Decisivos

1. **Streaming LLM**: Reflex permite `rx.State` con `yield` para streaming token
   por token via WebSocket, esencial para la experiencia de chat médico.

2. **Estado complejo**: `MedeXState` (~2900 líneas) gestiona >50 variables de estado
   con lógica condicional compleja. El modelo reactivo de Reflex lo maneja nativamente.

3. **Layout profesional**: El sidebar con navegación por módulos, paneles colapsables,
   y grid de herramientas requiere control CSS completo.

4. **Backend unificado**: Reflex compila a FastAPI internamente, eliminando la
   necesidad de mantener dos servidores separados para UI y API.

## Consecuencias

### Positivas

- Streaming en tiempo real para respuestas del LLM
- Estado reactivo granular sin re-renders innecesarios
- Control total del layout para la interfaz médica profesional
- Un solo proceso Python para UI + API
- Deploy containerizado estándar

### Negativas

- Curva de aprendizaje para contribuyentes acostumbrados a Streamlit
- Reflex es un framework más joven con ecosistema más pequeño
- El código UI es más verboso (componentes explícitos vs. API implícita de Streamlit)
- Debugging del frontend compilado (React) requiere herramientas adicionales

### Riesgos Mitigados

- **Madurez de Reflex**: El framework tiene releases regulares y soporte activo.
  MedeX usa solo APIs estables.
- **Complejidad de UI**: Se documentan patterns y convenciones en DEVELOPMENT.md
  para onboarding de nuevos contribuyentes.

## Implementación

- Todos los archivos de UI residen en `ui/medex_ui/`
- `app.py` contiene los componentes de UI (~3800 líneas)
- `state.py` contiene el estado reactivo (~2900 líneas)
- Referencias residuales a Streamlit eliminadas en PR #17
- El `Dockerfile` y `docker-compose.yml` usan `reflex run` como entrypoint
