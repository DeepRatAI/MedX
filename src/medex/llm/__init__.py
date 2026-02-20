# =============================================================================
# MedeX - LLM System Module
# =============================================================================
"""
LLM System for MedeX Medical Assistant.

This module provides a complete SOTA-level LLM integration system with:

- **Multi-Provider Routing**: Automatic failover across Kimi K2, OpenRouter,
  Groq, DeepSeek, Together, Cerebras, and Ollama
- **Prompt Management**: Medical-optimized prompts for educational and
  professional use cases, with multi-language support
- **Response Parsing**: Structured extraction of medical data including
  diagnoses, CIE-10 codes, medications, and dosages
- **SSE Streaming**: Real-time token streaming with heartbeat support
- **Cost Optimization**: Prioritizes free-tier providers

Usage Example:
    ```python
    from medex.llm import get_llm_service, UserMode

    # Get service instance
    service = get_llm_service()

    # Simple query (educational mode)
    response = await service.query(
        query="¿Qué son los antiinflamatorios?",
        user_mode=UserMode.EDUCATIONAL,
    )
    print(response.content)

    # Professional query with context
    parsed = await service.query_medical(
        query="Paciente 56 años con dolor torácico...",
        context=rag_context,
    )
    print(parsed.medical_report.diagnosis)
    print(parsed.medical_report.cie10_code)

    # Streaming response
    async for chunk in service.query_stream(query="..."):
        print(chunk.delta, end="", flush=True)

    # SSE for HTTP streaming
    async for sse_event in service.query_stream_sse(query="..."):
        yield sse_event  # Send to client
    ```

Provider Priority:
    1. Kimi K2 (Moonshot) - 128K context, free tier
    2. Groq - Ultra-fast inference, free tier
    3. OpenRouter - Multi-model gateway
    4. DeepSeek - High quality, low cost
    5. Together - Llama 3.3 70B
    6. Cerebras - Fast inference
    7. Ollama - Local fallback

Environment Variables:
    KIMI_API_KEY: Moonshot AI API key
    GROQ_API_KEY: Groq API key
    OPENROUTER_API_KEY: OpenRouter API key
    DEEPSEEK_API_KEY: DeepSeek API key
    TOGETHER_API_KEY: Together AI API key
    CEREBRAS_API_KEY: Cerebras API key
"""

from medex.llm.models import (  # Enums; Config; Messages; Responses; Status
    FinishReason,
    LLMConfig,
    LLMProvider,
    LLMRequest,
    LLMResponse,
    Message,
    MessageRole,
    ProviderStatus,
    ResponseFormat,
    StreamChunk,
    StreamEventType,
    TokenUsage,
)
from medex.llm.parser import (  # Enums; Data classes; Parser; Factory
    DiagnosticInfo,
    DrugInfo,
    ParsedContentType,
    ParsedMedicalReport,
    ParsedResponse,
    ParserConfig,
    ResponseParser,
    UrgencyLevel,
    create_parser,
    get_parser,
)
from medex.llm.prompts import (  # Enums; Config; Manager; Factory
    Language,
    PromptConfig,
    PromptManager,
    PromptType,
    UserMode,
    create_prompt_manager,
    get_prompt_manager,
)
from medex.llm.router import (  # Config; Client; Router; Factory
    LLMClient,
    LLMRouter,
    RouterConfig,
    create_llm_router,
    get_llm_router,
    shutdown_llm_router,
)
from medex.llm.service import (  # Config; Metrics; Service; Factory
    LLMService,
    LLMServiceConfig,
    LLMServiceMetrics,
    create_llm_service,
    get_llm_service,
    shutdown_llm_service,
)
from medex.llm.streaming import (  # Config; State; Handler; Utilities; Factory
    StreamConfig,
    StreamHandler,
    StreamState,
    create_stream_handler,
    format_chunk_sse,
    format_done,
    format_heartbeat,
    format_sse_event,
    get_stream_handler,
)

__all__ = [
    # === Models ===
    # Enums
    "FinishReason",
    "LLMProvider",
    "MessageRole",
    "ResponseFormat",
    "StreamEventType",
    # Config
    "LLMConfig",
    # Messages
    "Message",
    # Request/Response
    "LLMRequest",
    "LLMResponse",
    "StreamChunk",
    "TokenUsage",
    "ProviderStatus",
    # === Parser ===
    # Enums
    "ParsedContentType",
    "UrgencyLevel",
    # Data classes
    "DiagnosticInfo",
    "DrugInfo",
    "ParsedMedicalReport",
    "ParsedResponse",
    # Parser
    "ParserConfig",
    "ResponseParser",
    "create_parser",
    "get_parser",
    # === Prompts ===
    # Enums
    "Language",
    "PromptType",
    "UserMode",
    # Config
    "PromptConfig",
    # Manager
    "PromptManager",
    "create_prompt_manager",
    "get_prompt_manager",
    # === Router ===
    # Config
    "RouterConfig",
    # Client
    "LLMClient",
    # Router
    "LLMRouter",
    "create_llm_router",
    "get_llm_router",
    "shutdown_llm_router",
    # === Service ===
    # Config
    "LLMServiceConfig",
    # Metrics
    "LLMServiceMetrics",
    # Service
    "LLMService",
    "create_llm_service",
    "get_llm_service",
    "shutdown_llm_service",
    # === Streaming ===
    # Config
    "StreamConfig",
    # State
    "StreamState",
    # Handler
    "StreamHandler",
    # Utilities
    "format_chunk_sse",
    "format_done",
    "format_heartbeat",
    "format_sse_event",
    "create_stream_handler",
    "get_stream_handler",
]
