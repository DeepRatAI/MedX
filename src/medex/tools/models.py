# =============================================================================
# MedeX - Tool Models
# =============================================================================
"""
Data models for MedeX V2 Tool System.

This module provides:
- ToolParameter: Parameter definition for tools
- ToolDefinition: Complete tool specification
- ToolCall: Represents a tool invocation request
- ToolResult: Result from tool execution
- ToolError: Error information from failed execution

Design:
- OpenAI-compatible tool format
- Type-safe parameter definitions
- Comprehensive validation
- Serialization support for LLM APIs
"""

from __future__ import annotations

import json
from collections.abc import Callable, Coroutine
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

# =============================================================================
# Enums
# =============================================================================


class ToolCategory(Enum):
    """Categories of medical tools."""

    DRUG = "drug"  # Drug-related tools
    LAB = "lab"  # Laboratory interpretation
    DOSAGE = "dosage"  # Dosage calculations
    EMERGENCY = "emergency"  # Emergency detection
    DIAGNOSIS = "diagnosis"  # Diagnostic support
    REFERENCE = "reference"  # Reference lookup
    UTILITY = "utility"  # General utilities


class ToolStatus(Enum):
    """Execution status of a tool."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class ParameterType(Enum):
    """JSON Schema types for parameters."""

    STRING = "string"
    NUMBER = "number"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"


# =============================================================================
# Tool Parameter
# =============================================================================


@dataclass
class ToolParameter:
    """
    Definition of a tool parameter.

    Follows JSON Schema specification for OpenAI compatibility.
    """

    name: str
    type: ParameterType
    description: str
    required: bool = True
    default: Any = None
    enum: list[str] | None = None
    items: dict[str, Any] | None = None  # For array types
    properties: dict[str, Any] | None = None  # For object types
    minimum: float | None = None
    maximum: float | None = None
    min_length: int | None = None
    max_length: int | None = None

    def to_json_schema(self) -> dict[str, Any]:
        """Convert to JSON Schema format."""
        schema: dict[str, Any] = {
            "type": self.type.value,
            "description": self.description,
        }

        if self.enum:
            schema["enum"] = self.enum

        if self.items and self.type == ParameterType.ARRAY:
            schema["items"] = self.items

        if self.properties and self.type == ParameterType.OBJECT:
            schema["properties"] = self.properties

        if self.minimum is not None:
            schema["minimum"] = self.minimum

        if self.maximum is not None:
            schema["maximum"] = self.maximum

        if self.min_length is not None:
            schema["minLength"] = self.min_length

        if self.max_length is not None:
            schema["maxLength"] = self.max_length

        if self.default is not None:
            schema["default"] = self.default

        return schema


# =============================================================================
# Tool Definition
# =============================================================================


@dataclass
class ToolDefinition:
    """
    Complete definition of a tool.

    Includes metadata, parameters, and execution function.
    """

    name: str
    description: str
    category: ToolCategory
    parameters: list[ToolParameter] = field(default_factory=list)
    handler: Callable[..., Coroutine[Any, Any, Any]] | None = None
    enabled: bool = True
    requires_auth: bool = False
    timeout_seconds: float = 30.0
    max_retries: int = 0
    cache_ttl: int | None = None  # Cache TTL in seconds
    tags: list[str] = field(default_factory=list)
    version: str = "1.0.0"

    def to_openai_format(self) -> dict[str, Any]:
        """
        Convert to OpenAI function calling format.

        Returns:
            Dict compatible with OpenAI tools API
        """
        properties = {}
        required = []

        for param in self.parameters:
            properties[param.name] = param.to_json_schema()
            if param.required:
                required.append(param.name)

        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                },
            },
        }

    def to_anthropic_format(self) -> dict[str, Any]:
        """
        Convert to Anthropic tool use format.

        Returns:
            Dict compatible with Anthropic tools API
        """
        properties = {}
        required = []

        for param in self.parameters:
            properties[param.name] = param.to_json_schema()
            if param.required:
                required.append(param.name)

        return {
            "name": self.name,
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
        }

    def validate_arguments(self, arguments: dict[str, Any]) -> list[str]:
        """
        Validate arguments against parameter definitions.

        Args:
            arguments: Arguments to validate

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        # Check required parameters
        for param in self.parameters:
            if param.required and param.name not in arguments:
                errors.append(f"Missing required parameter: {param.name}")

        # Check types and constraints
        for name, value in arguments.items():
            param = next((p for p in self.parameters if p.name == name), None)
            if param is None:
                errors.append(f"Unknown parameter: {name}")
                continue

            # Type validation
            if not self._validate_type(value, param.type):
                errors.append(
                    f"Parameter '{name}' expected {param.type.value}, "
                    f"got {type(value).__name__}"
                )

            # Enum validation
            if param.enum and value not in param.enum:
                errors.append(f"Parameter '{name}' must be one of: {param.enum}")

            # Range validation
            if isinstance(value, (int, float)):
                if param.minimum is not None and value < param.minimum:
                    errors.append(f"Parameter '{name}' must be >= {param.minimum}")
                if param.maximum is not None and value > param.maximum:
                    errors.append(f"Parameter '{name}' must be <= {param.maximum}")

            # String length validation
            if isinstance(value, str):
                if param.min_length and len(value) < param.min_length:
                    errors.append(
                        f"Parameter '{name}' must have >= {param.min_length} chars"
                    )
                if param.max_length and len(value) > param.max_length:
                    errors.append(
                        f"Parameter '{name}' must have <= {param.max_length} chars"
                    )

        return errors

    def _validate_type(self, value: Any, expected: ParameterType) -> bool:
        """Validate value matches expected type."""
        type_map = {
            ParameterType.STRING: str,
            ParameterType.NUMBER: (int, float),
            ParameterType.INTEGER: int,
            ParameterType.BOOLEAN: bool,
            ParameterType.ARRAY: list,
            ParameterType.OBJECT: dict,
        }
        return isinstance(value, type_map.get(expected, object))


# =============================================================================
# Tool Call
# =============================================================================


@dataclass
class ToolCall:
    """
    Represents a request to execute a tool.

    Created from LLM function call response.
    """

    id: UUID = field(default_factory=uuid4)
    tool_name: str = ""
    arguments: dict[str, Any] = field(default_factory=dict)
    raw_arguments: str = ""  # Original JSON string from LLM
    created_at: datetime = field(default_factory=datetime.utcnow)

    @classmethod
    def from_openai(cls, tool_call: dict[str, Any]) -> ToolCall:
        """
        Create from OpenAI tool call format.

        Args:
            tool_call: OpenAI tool call dict

        Returns:
            ToolCall instance
        """
        function = tool_call.get("function", {})
        raw_args = function.get("arguments", "{}")

        try:
            arguments = json.loads(raw_args)
        except json.JSONDecodeError:
            arguments = {}

        return cls(
            id=uuid4(),
            tool_name=function.get("name", ""),
            arguments=arguments,
            raw_arguments=raw_args,
        )

    @classmethod
    def from_anthropic(cls, tool_use: dict[str, Any]) -> ToolCall:
        """
        Create from Anthropic tool use format.

        Args:
            tool_use: Anthropic tool use dict

        Returns:
            ToolCall instance
        """
        return cls(
            id=uuid4(),
            tool_name=tool_use.get("name", ""),
            arguments=tool_use.get("input", {}),
            raw_arguments=json.dumps(tool_use.get("input", {})),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": str(self.id),
            "tool_name": self.tool_name,
            "arguments": self.arguments,
            "created_at": self.created_at.isoformat(),
        }


# =============================================================================
# Tool Result
# =============================================================================


@dataclass
class ToolResult:
    """
    Result from tool execution.

    Contains output data, status, and metadata.
    """

    call_id: UUID
    tool_name: str
    status: ToolStatus = ToolStatus.PENDING
    output: Any = None
    error: str | None = None
    error_code: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    execution_time_ms: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_success(self) -> bool:
        """Check if execution was successful."""
        return self.status == ToolStatus.SUCCESS

    @property
    def is_error(self) -> bool:
        """Check if execution failed."""
        return self.status in (
            ToolStatus.ERROR,
            ToolStatus.TIMEOUT,
            ToolStatus.CANCELLED,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "call_id": str(self.call_id),
            "tool_name": self.tool_name,
            "status": self.status.value,
            "output": self.output,
            "error": self.error,
            "error_code": self.error_code,
            "execution_time_ms": self.execution_time_ms,
            "metadata": self.metadata,
        }

    def to_llm_format(self) -> str:
        """
        Format result for LLM consumption.

        Returns:
            String representation for LLM context
        """
        if self.is_error:
            return f"Error ejecutando {self.tool_name}: {self.error}"

        if isinstance(self.output, dict):
            return json.dumps(self.output, ensure_ascii=False, indent=2)

        if isinstance(self.output, list):
            return json.dumps(self.output, ensure_ascii=False, indent=2)

        return str(self.output)

    def to_openai_format(self) -> dict[str, Any]:
        """
        Format for OpenAI tool result.

        Returns:
            Dict for OpenAI messages API
        """
        return {
            "role": "tool",
            "tool_call_id": str(self.call_id),
            "content": self.to_llm_format(),
        }


# =============================================================================
# Tool Error
# =============================================================================


@dataclass
class ToolError:
    """
    Detailed error information from tool execution.

    Provides structured error data for logging and debugging.
    """

    code: str
    message: str
    tool_name: str
    arguments: dict[str, Any] = field(default_factory=dict)
    exception_type: str | None = None
    stack_trace: str | None = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    recoverable: bool = True

    # Common error codes
    VALIDATION_ERROR = "VALIDATION_ERROR"
    NOT_FOUND = "TOOL_NOT_FOUND"
    TIMEOUT = "EXECUTION_TIMEOUT"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    RATE_LIMITED = "RATE_LIMITED"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    DEPENDENCY_ERROR = "DEPENDENCY_ERROR"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for logging."""
        return {
            "code": self.code,
            "message": self.message,
            "tool_name": self.tool_name,
            "arguments": self.arguments,
            "exception_type": self.exception_type,
            "timestamp": self.timestamp.isoformat(),
            "recoverable": self.recoverable,
        }

    def to_result(self, call_id: UUID) -> ToolResult:
        """Convert to ToolResult for consistent handling."""
        return ToolResult(
            call_id=call_id,
            tool_name=self.tool_name,
            status=ToolStatus.ERROR,
            error=self.message,
            error_code=self.code,
            completed_at=self.timestamp,
        )
