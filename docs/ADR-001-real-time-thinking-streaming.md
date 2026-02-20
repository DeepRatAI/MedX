# ADR-001: Real-Time Thinking Content Streaming

## Status

**Accepted** - 2026-01-14

## Context

### Problem Statement

Los modelos de razonamiento (DeepSeek R1, QwQ-32B) generan contenido de "pensamiento" dentro de tags `<think>...</think>` durante el streaming. El comportamiento anterior era:

1. **Problema UX**: El pensamiento y la respuesta se streameaban mezclados al área de contenido
2. **Post-procesamiento**: Solo al finalizar el stream se separaba el thinking al collapsible
3. **Experiencia confusa**: El usuario veía todo el texto junto y luego "saltaba" al collapsible

### User Expectation

Comportamiento tipo ChatGPT/OpenAI o1:

- El pensamiento debe mostrarse **EN TIEMPO REAL** dentro del área de razonamiento
- Cuando termina el pensamiento (tag `</think>`), la respuesta debe comenzar a streamearse **separadamente**
- Transición visual clara entre "pensando" y "respondiendo"

## Decision

### Arquitectura de Streaming Dual

Implementamos un **state machine** para parsear `<think>` tags en tiempo real:

```python
# Estados del parser
is_reasoning_model = model in ("deepseek-r1", "qwq-32b")
in_thinking = False       # Dentro de <think>
thinking_complete = False # </think> encontrado
```

### Flujo de Datos

```
┌──────────────┐     ┌────────────────┐     ┌──────────────┐
│   Stream     │────>│  State Machine │────>│   UI Update  │
│   (tokens)   │     │  <think> parse │     │  (yield)     │
└──────────────┘     └────────────────┘     └──────────────┘
                            │
                ┌───────────┴───────────┐
                │                       │
        ┌───────▼───────┐       ┌───────▼───────┐
        │ thinking_cont │       │    content    │
        │    buffer     │       │    buffer     │
        └───────────────┘       └───────────────┘
```

### UI States

1. **Estado "Razonando..."**: Cuando `is_streaming & thinking_content != "" & content == ""`

   - Header con spinner y texto "Razonando..."
   - Contenido del thinking visible y scrolleable (max-height: 300px)
   - No collapsible mientras está activo

2. **Estado "Streaming respuesta"**: Cuando `is_streaming & content != ""`

   - Thinking content en collapsible (cerrado por defecto)
   - Respuesta streameándose con cursor parpadeante

3. **Estado "Completo"**: Cuando `!is_streaming`
   - Thinking en collapsible expandible
   - Respuesta completa
   - Botón de copiar visible

## Consequences

### Positive

- **UX mejorada**: El usuario ve el pensamiento en tiempo real
- **Separación visual clara**: Transición natural de thinking a response
- **Consistencia con estándares**: Similar a ChatGPT o1/o3 UX
- **No breaking change**: Modelos sin `<think>` tags funcionan igual

### Negative

- **Complejidad aumentada**: State machine + múltiples buffers
- **Performance mínimamente afectada**: Parsing por cada chunk (pero es O(n) en buffer size)
- **Edge cases**: Tags `<think>` truncados entre chunks requieren buffer completo

### Trade-offs

| Aspecto             | Decisión                         | Justificación                                          |
| ------------------- | -------------------------------- | ------------------------------------------------------ |
| Buffer strategy     | Mantener raw_buffer completo     | Necesario para detectar tags partidos entre chunks     |
| Modelos soportados  | Solo deepseek-r1, qwq-32b        | Únicos que usan `<think>` tags según docs oficiales    |
| Max-height thinking | 300px (live) / 400px (collapsed) | Balance entre visibilidad y no ocupar toda la pantalla |

## Technical Implementation

### Files Modified

- `ui/medex_ui/state.py`: Método `send_message()` con state machine
- `ui/medex_ui/app.py`: Componente `assistant_message()` con 3 estados UI

### Key Code Pattern

```python
# Real-time parsing in streaming loop
if is_reasoning_model and not thinking_complete:
    if "<think>" in raw_buffer and not in_thinking:
        in_thinking = True
        thinking_buffer = raw_buffer[raw_buffer.find("<think>") + 7:]
        self.messages[-1].thinking_content = thinking_buffer
        self.messages[-1].content = ""  # Clear while thinking
        yield  # UI update

    elif in_thinking and "</think>" in raw_buffer:
        thinking_complete = True
        idx = raw_buffer.find("</think>")
        thinking_buffer = raw_buffer[raw_buffer.find("<think>") + 7:idx]
        response_buffer = raw_buffer[idx + 8:].strip()
        self.messages[-1].thinking_content = thinking_buffer.strip()
        self.messages[-1].content = response_buffer
        yield  # UI update - transition to response
```

## References

### Documentation Consulted

- [DeepSeek API - Thinking Mode](https://api-docs.deepseek.com/guides/thinking_mode)
  - `reasoning_content` field at same level as `content`
  - `reasoning_content` always appears before `content` in streaming
- [Moonshot AI - Kimi K2 Thinking Model](https://platform.moonshot.ai/docs/guide/use-kimi-k2-thinking-model)

  - Uses `reasoning_content` field (NOT `<think>` tags)
  - `reasoning_content` controlled by `max_tokens`

- [OpenAI - Reasoning Models](https://platform.openai.com/docs/guides/reasoning)
  - "reasoning tokens" concept
  - Not visible via API, only via summary parameter

### Key Insights from Documentation

1. **DeepSeek R1**: Uses `<think>` tags in stream, `reasoning_content` in final response
2. **Kimi K2**: Uses `reasoning_content` as separate field (no tags)
3. **Qwen3-235B**: **NO** thinking mode - docs explicitly state "non-thinking mode only"
4. **QwQ-32B**: Uses `<think>` tags, similar to DeepSeek R1

## Validation Criteria

- [ ] QwQ-32B: Thinking appears in live area while streaming
- [ ] QwQ-32B: Response appears separately after `</think>`
- [ ] DeepSeek R1: Same behavior as QwQ-32B
- [ ] Qwen3-235B: No collapsible appears (non-reasoning model)
- [ ] Kimi K2: No collapsible appears (uses reasoning_content, not tags)
- [ ] Gemini/Llama: Normal streaming, no thinking UI

---

**Author**: AI Engineering Team  
**Date**: 2026-01-14  
**Version**: 1.0
