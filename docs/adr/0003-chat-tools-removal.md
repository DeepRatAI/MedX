# ADR-0003: Eliminación de Herramientas de Búsqueda del Chat

**Fecha:** 2026-01-15  
**Estado:** Aceptado  
**Autor:** Arquitectura MedeX

## Contexto

El módulo Chat de MedeX contenía un panel de "Herramientas de Chat" con toggles para:
- **Web Search**: Búsqueda en DuckDuckGo
- **PubMed Search**: Búsqueda en literatura científica

### Problema Detectado

Durante la auditoría técnica se identificó que:

1. **Los toggles eran UI-only**: El estado se actualizaba en frontend, pero `send_message()` **nunca consultaba** estos valores para modificar el comportamiento del LLM.

2. **Implementaciones existían pero desconectadas**: Los módulos `web_search.py` y `scientific_search.py` contenían implementaciones funcionales (DuckDuckGo, PubMed API), pero solo estaban integrados con **Deep Research**, no con Chat.

3. **Expectativas falsas**: Los usuarios veían botones activos que prometían funcionalidad inexistente.

## Decisión

**Eliminar completamente el panel "Herramientas de Chat" de la interfaz.**

### Justificación Arquitectónica

| Módulo | Propósito | Acceso a Fuentes Externas |
|--------|-----------|---------------------------|
| **Chat** | Consultas rápidas y seguras | ❌ No - Solo conocimiento base del modelo |
| **Deep Research** | Investigación exhaustiva | ✅ Sí - PubMed, Semantic Scholar, Web |

### Argumentos a Favor

1. **Seguridad médica**: En dominio clínico, la información no auditada puede causar daño. El Chat debe responder con conocimiento verificado.

2. **Claridad de propósito**: Separación clara entre consulta segura (Chat) e investigación activa (Deep Research).

3. **Responsabilidad legal**: El usuario de Deep Research "opta in" conscientemente a información externa que debe validar.

4. **Honestidad de UI**: Eliminar elementos que prometen funcionalidad inexistente.

5. **Mantenibilidad**: Reducir código muerto y estado innecesario.

## Implementación

### Archivos Modificados

**`ui/medex_ui/app.py`:**
- ✅ Eliminada función `tools_toggle_panel()`
- ✅ Renombrada `chat_input_with_tools()` → `chat_input_area()`
- ✅ Eliminado botón "sparkles" y panel flotante
- ✅ Simplificado el input del chat

**`ui/medex_ui/state.py`:**
- ✅ Eliminado `chat_tools_enabled: dict`
- ✅ Eliminado `show_chat_tools_panel: bool`
- ✅ Eliminados métodos:
  - `toggle_chat_tools_panel()`
  - `toggle_web_search()`
  - `toggle_pubmed_search()`
  - `chat_tools_count` (computed var)
  - `has_active_chat_tools` (computed var)
  - `web_search_enabled` (computed var)
  - `pubmed_search_enabled` (computed var)

### Archivos NO Modificados (preservados para Deep Research)

- `ui/medex_ui/web_search.py` - Implementación DuckDuckGo
- `ui/medex_ui/scientific_search.py` - Cliente PubMed/Semantic Scholar
- `src/medex/core/engine.py` - Tool `$web_search` para Kimi

## Consecuencias

### Positivas
- UI más limpia y honesta
- Menor superficie de bugs
- Claridad arquitectónica Chat vs Deep Research
- Reducción de ~150 líneas de código innecesario

### Negativas
- Usuarios que esperaban búsqueda en Chat deberán usar Deep Research
- Knowledge cutoff del modelo puede limitar respuestas sobre temas recientes

### Mitigación
- Deep Research será potenciado como el módulo de investigación
- Posible disclaimer en Chat sobre limitaciones temporales del modelo

## Validación

- [x] Código compila sin errores de sintaxis
- [x] Imports verificados
- [ ] UI renderiza correctamente (pendiente verificación visual)
- [ ] Chat funciona normalmente sin los toggles

## Referencias

- Investigación previa: Análisis de Chat Tools (sesión 2026-01-15)
- Módulos preservados: `web_search.py`, `scientific_search.py`
