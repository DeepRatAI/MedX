# =============================================================================
# MedeX - Tool System Package
# =============================================================================
"""
Tool Integration System for MedeX V2.

This package provides a complete system for defining, registering,
and executing tools that can be called by LLMs using function calling.

Architecture:
- models.py: Data models for tools, parameters, calls, and results
- registry.py: Central tool registry with decorator-based registration
- executor.py: Async tool execution engine with retry and caching
- medical/: Medical-specific tool implementations

Usage:
    from medex.tools import (
        ToolRegistry,
        ToolExecutor,
        tool,
        string_param,
        number_param,
    )

    # Define a tool using the decorator
    @tool(
        name="my_tool",
        description="Does something useful",
        parameters=[
            string_param("input", "The input to process"),
        ]
    )
    async def my_tool(input: str) -> dict:
        return {"result": input.upper()}

    # Execute tools
    executor = create_tool_executor()
    result = await executor.execute(tool_call)
"""

from .executor import ToolExecutor, create_tool_executor

# Re-export medical tools
from .medical import (
    adjust_dose_renal,
    calculate_bsa,
    calculate_creatinine_clearance,
    calculate_pediatric_dose,
    check_critical_values,
    check_drug_interactions,
    detect_emergency,
    get_drug_info,
    interpret_cbc,
    interpret_liver_panel,
    interpret_thyroid_panel,
    quick_triage,
)
from .models import (
    ParameterType,
    ToolCall,
    ToolCategory,
    ToolDefinition,
    ToolError,
    ToolParameter,
    ToolResult,
    ToolStatus,
)
from .registry import (
    ToolRegistry,
    array_param,
    boolean_param,
    enum_param,
    get_tool_registry,
    integer_param,
    number_param,
    object_param,
    string_param,
    tool,
)

__all__ = [
    # Models
    "ToolParameter",
    "ParameterType",
    "ToolDefinition",
    "ToolCategory",
    "ToolStatus",
    "ToolCall",
    "ToolResult",
    "ToolError",
    # Registry
    "ToolRegistry",
    "get_tool_registry",
    "tool",
    "string_param",
    "number_param",
    "integer_param",
    "boolean_param",
    "array_param",
    "object_param",
    "enum_param",
    # Executor
    "ToolExecutor",
    "create_tool_executor",
    # Medical tools
    "check_drug_interactions",
    "get_drug_info",
    "calculate_pediatric_dose",
    "adjust_dose_renal",
    "calculate_bsa",
    "calculate_creatinine_clearance",
    "interpret_cbc",
    "interpret_liver_panel",
    "interpret_thyroid_panel",
    "detect_emergency",
    "check_critical_values",
    "quick_triage",
]

__version__ = "2.0.0"
