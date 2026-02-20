# Decisiones de Diseño: Streaming de Razonamiento en Tiempo Real

**Fecha**: 2026-01-14  
**Estado**: Implementado  
**Autor**: GitHub Copilot (Claude Opus 4.5)

---

## 1. Contexto del Problema

Los modelos de razonamiento (DeepSeek R1, QwQ 32B) emiten su proceso de pensamiento dentro de tags `<think>...</think>` mezclado con la respuesta final. El usuario reportó:

1. El pensamiento se streameaba junto con la respuesta
2. Al final del streaming, el pensamiento se movía al colapsable
3. Comportamiento deseado: el pensamiento debe aparecer DENTRO del colapsable MIENTRAS se streamea

---

## 2. Investigación UX

### 2.1 Patrones Observados en la Industria

| Plataforma | Comportamiento |
|------------|----------------|
| **ChatGPT (o1/o3)** | Muestra "Thinking..." con contador de tiempo, luego revela respuesta |
| **Claude** | Muestra "Extended thinking" colapsado, streaming paralelo |
| **DeepSeek Web** | Muestra thinking en panel separado mientras streamea |

### 2.2 Principios de Diseño Adoptados

1. **Feedback inmediato**: El usuario debe ver actividad desde el primer token
2. **Separación visual clara**: Thinking y respuesta en contenedores distintos
3. **Progressive disclosure**: El thinking es colapsable (no interrumpe)
4. **Estado de streaming visible**: Indicador de "pensando" mientras se recibe

---

## 3. Arquitectura de la Solución

### 3.1 Flujo de Datos

```
HuggingFace Router → Backend (stream) → Frontend (parse) → UI Update
                                              ↓
                                    State Machine:
                                    [INIT] → detect <think>
                                    [THINKING] → buffer to thinking_content
                                    [COMPLETE] → detect </think>
                                    [RESPONSE] → buffer to content
```

### 3.2 Máquina de Estados en `state.py`

```python
# Variables de estado
raw_buffer = ""           # Buffer completo para fallback
thinking_buffer = ""      # Contenido dentro de <think>
response_buffer = ""      # Contenido después de </think>
in_thinking = False       # Actualmente dentro de <think>
thinking_complete = False # Ya se vio </think>
```

### 3.3 Lógica de Parsing en Tiempo Real

1. **Modelo NO razonador**: Stream directo a `content`
2. **Modelo razonador, pre-`<think>`**: Esperar hasta 50 chars o detectar `<think>`
3. **Modelo razonador, in-`<think>`**: Stream a `thinking_content`
4. **Modelo razonador, post-`</think>`**: Stream a `content`

---

## 4. Decisiones Técnicas

### 4.1 ¿Por qué parsing en frontend y no en backend?

**Opción descartada**: Backend parsea y envía `thinking_content` separado

**Opción elegida**: Frontend parsea en tiempo real

**Justificación**:
- El backend recibe SSE de HuggingFace sin conocimiento de `<think>` tags
- Modificar el backend requeriría buffering que aumentaría latencia
- El frontend puede actualizar la UI inmediatamente (menor tiempo a primer token visible)
- Reflex soporta yields múltiples para actualizaciones granulares

### 4.2 ¿Por qué máquina de estados vs regex post-hoc?

**Problema con regex post-hoc**:
- El thinking aparece mezclado durante el streaming
- Solo al final se mueve al colapsable (mala UX)

**Solución con máquina de estados**:
- Cada chunk se procesa al llegar
- La UI se actualiza en el lugar correcto inmediatamente
- El usuario ve el thinking acumularse EN el colapsable

### 4.3 Modelos Afectados

| Modelo | Usa `<think>` | `is_reasoning_model` |
|--------|---------------|----------------------|
| deepseek-r1 | ✓ | True |
| qwq-32b | ✓ | True |
| qwen3-235b | ✗ | False |
| kimi-k2 | ✗ (usa `reasoning_content`) | False* |
| gemini-2-flash | ✗ | False |
| llama-70b | ✗ | False |

*Kimi K2 envía `reasoning_content` como campo separado en la API, no usa tags.

---

## 5. Trade-offs y Limitaciones

### 5.1 Aceptados

| Trade-off | Decisión | Justificación |
|-----------|----------|---------------|
| Complejidad de código | +95 líneas en `send_message()` | UX significativamente mejor |
| Duplicación de lógica | Parser en frontend + cleanup final | Robustez ante edge cases |
| Latencia de 50 chars | Esperar antes de decidir si hay `<think>` | Evitar falsos negativos |

### 5.2 Limitaciones Conocidas

1. **Modelos con thinking incompleto**: Si el stream se corta antes de `</think>`, el thinking queda en el buffer pero se limpia en el cleanup final
2. **Tags malformados**: `<think>` sin `</think>` se maneja en cleanup final
3. **Nested tags**: No soportado (no hay modelos que los usen)

---

## 6. UI Components

### 6.1 Collapsible Thinking (app.py)

```python
rx.cond(
    msg["thinking_content"] != "",
    rx.box(
        rx.collapsible.root(
            rx.collapsible.trigger(...),  # "Ver razonamiento del modelo"
            rx.collapsible.content(
                rx.markdown(msg["thinking_content"]),  # Streaming aquí
            )
        )
    )
)
```

### 6.2 Indicador de Estado (implementación pendiente para v2)

Posible mejora futura: mostrar "🤔 Pensando..." animado mientras `in_thinking=True`.

---

## 7. Testing

### 7.1 Casos de Prueba

| Caso | Input | Esperado |
|------|-------|----------|
| QwQ con thinking | Pregunta médica | Thinking en collapsible, respuesta separada |
| DeepSeek R1 | Pregunta médica | Thinking en collapsible, respuesta separada |
| Qwen3 235B | Pregunta médica | NO collapsible (no es reasoning model) |
| Kimi K2 | Pregunta médica | NO collapsible (no usa `<think>`) |
| Stream cortado | Timeout | Cleanup maneja thinking parcial |

### 7.2 Resultados (2026-01-14)

- ✅ QwQ 32B: Thinking en collapsible
- ✅ DeepSeek R1: Thinking en collapsible
- ✅ Qwen3 235B: Sin collapsible, respuesta directa
- ✅ Kimi K2: Funciona correctamente
- ⏳ Pendiente: Verificar comportamiento de streaming en tiempo real

---

## 8. Referencias

1. [DeepSeek API - Thinking Mode](https://api-docs.deepseek.com/guides/thinking_mode)
2. [Qwen3 Model Card](https://huggingface.co/Qwen/Qwen3-235B-A22B-Instruct-2507) - "Non-thinking mode only"
3. [Reflex Docs - Event Handlers](https://reflex.dev/docs/events/events_overview/)
4. [SSE Specification](https://html.spec.whatwg.org/multipage/server-sent-events.html)

---

## 9. Changelog

| Fecha | Cambio |
|-------|--------|
| 2026-01-14 | Implementación inicial de streaming en tiempo real |
| 2026-01-14 | Máquina de estados para parsing de `<think>` tags |
| 2026-01-14 | Documentación de decisiones técnicas |
