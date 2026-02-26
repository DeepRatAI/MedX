# =============================================================================
# MedeX - Tool System Tests (V2-aligned)
# =============================================================================
"""
Comprehensive tests for the MedeX V2 Tool System.

Tests cover:
- Tool models (ToolParameter, ToolDefinition, ToolCall, ToolResult, ToolError)
- Tool registry (registration, retrieval, filtering, enable/disable)
- Tool executor (execution, timeout, batch, metrics)
- Medical tools (drug interactions, dosage, labs, emergency)
- Tool service integration

All tests use the actual V2 API signatures.
"""

from __future__ import annotations

import json
from uuid import uuid4

import pytest

from medex.tools.executor import ToolExecutor
from medex.tools.models import (
    ParameterType,
    ToolCall,
    ToolCategory,
    ToolDefinition,
    ToolError,
    ToolParameter,
    ToolResult,
    ToolStatus,
)
from medex.tools.registry import (
    ToolRegistry,
    number_param,
    string_param,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def sample_parameter() -> ToolParameter:
    """Create a sample tool parameter."""
    return ToolParameter(
        name="medication",
        type=ParameterType.STRING,
        description="Name of the medication",
        required=True,
    )


@pytest.fixture
def sample_definition() -> ToolDefinition:
    """Create a sample tool definition."""
    return ToolDefinition(
        name="check_medication",
        description="Check medication information",
        category=ToolCategory.DRUG,
        parameters=[
            ToolParameter(
                name="medication",
                type=ParameterType.STRING,
                description="Medication name",
                required=True,
            ),
            ToolParameter(
                name="dosage",
                type=ParameterType.NUMBER,
                description="Dosage in mg",
                required=False,
            ),
        ],
        handler=lambda medication, dosage=None: {
            "medication": medication,
            "dosage": dosage,
        },
        tags=["medication", "drug"],
    )


@pytest.fixture
def fresh_registry() -> ToolRegistry:
    """Create a fresh registry for testing."""
    return ToolRegistry()


@pytest.fixture
def executor(fresh_registry: ToolRegistry) -> ToolExecutor:
    """Create an executor with a fresh registry."""
    return ToolExecutor(
        registry=fresh_registry,
        max_concurrent=3,
        default_timeout=5.0,
    )


# =============================================================================
# ToolParameter Tests
# =============================================================================


class TestToolParameter:
    """Tests for ToolParameter model."""

    def test_create_string_parameter(self):
        """Test creating a string parameter."""
        param = ToolParameter(
            name="patient_name",
            type=ParameterType.STRING,
            description="Patient's full name",
            required=True,
        )

        assert param.name == "patient_name"
        assert param.type == ParameterType.STRING
        assert param.required is True

    def test_create_number_parameter_with_range(self):
        """Test creating a number parameter with min/max."""
        param = ToolParameter(
            name="age",
            type=ParameterType.INTEGER,
            description="Patient age",
            required=True,
            minimum=0,
            maximum=150,
        )

        assert param.minimum == 0
        assert param.maximum == 150

    def test_create_enum_parameter(self):
        """Test creating an enum parameter."""
        param = ToolParameter(
            name="severity",
            type=ParameterType.STRING,
            description="Severity level",
            required=True,
            enum=["low", "medium", "high"],
        )

        assert param.enum == ["low", "medium", "high"]

    def test_to_json_schema(self, sample_parameter: ToolParameter):
        """Test conversion to JSON Schema."""
        schema = sample_parameter.to_json_schema()

        assert schema["type"] == "string"
        assert schema["description"] == "Name of the medication"

    def test_to_json_schema_with_constraints(self):
        """Test JSON Schema with constraints."""
        param = ToolParameter(
            name="weight",
            type=ParameterType.NUMBER,
            description="Weight in kg",
            required=True,
            minimum=0.5,
            maximum=500,
        )

        schema = param.to_json_schema()

        assert schema["type"] == "number"
        assert schema["minimum"] == 0.5
        assert schema["maximum"] == 500


# =============================================================================
# ToolDefinition Tests
# =============================================================================


class TestToolDefinition:
    """Tests for ToolDefinition model."""

    def test_create_definition(self, sample_definition: ToolDefinition):
        """Test creating a tool definition."""
        assert sample_definition.name == "check_medication"
        assert sample_definition.category == ToolCategory.DRUG
        assert len(sample_definition.parameters) == 2
        assert sample_definition.enabled is True

    def test_to_openai_format(self, sample_definition: ToolDefinition):
        """Test conversion to OpenAI function calling format."""
        openai_format = sample_definition.to_openai_format()

        assert openai_format["type"] == "function"
        assert openai_format["function"]["name"] == "check_medication"
        assert "parameters" in openai_format["function"]
        assert openai_format["function"]["parameters"]["type"] == "object"
        assert "medication" in openai_format["function"]["parameters"]["properties"]

    def test_to_anthropic_format(self, sample_definition: ToolDefinition):
        """Test conversion to Anthropic tool format."""
        anthropic_format = sample_definition.to_anthropic_format()

        assert anthropic_format["name"] == "check_medication"
        assert "input_schema" in anthropic_format
        assert anthropic_format["input_schema"]["type"] == "object"
        assert "medication" in anthropic_format["input_schema"]["properties"]

    def test_validate_arguments_valid(self, sample_definition: ToolDefinition):
        """Test argument validation with valid arguments."""
        errors = sample_definition.validate_arguments({"medication": "aspirin"})
        assert len(errors) == 0

    def test_validate_arguments_missing_required(
        self, sample_definition: ToolDefinition
    ):
        """Test argument validation with missing required parameter."""
        errors = sample_definition.validate_arguments({})
        assert len(errors) > 0
        assert "medication" in errors[0].lower()


# =============================================================================
# ToolCall Tests
# =============================================================================


class TestToolCall:
    """Tests for ToolCall model."""

    def test_create_tool_call(self):
        """Test creating a tool call."""
        call = ToolCall(
            tool_name="check_drug_interactions",
            arguments={"drugs": ["aspirin", "ibuprofen"]},
        )

        assert call.tool_name == "check_drug_interactions"
        assert call.arguments["drugs"] == ["aspirin", "ibuprofen"]
        assert call.id is not None  # UUID auto-generated

    def test_from_openai(self):
        """Test creating from OpenAI response."""
        openai_response = {
            "id": "call_123",
            "function": {
                "name": "calculate_dose",
                "arguments": '{"drug": "amoxicillin", "weight": 70}',
            },
        }

        call = ToolCall.from_openai(openai_response)

        assert call.tool_name == "calculate_dose"
        assert call.arguments["drug"] == "amoxicillin"
        assert call.arguments["weight"] == 70

    def test_from_anthropic(self):
        """Test creating from Anthropic response."""
        anthropic_response = {
            "id": "toolu_123",
            "name": "interpret_lab",
            "input": {"hemoglobin": 12.5, "sex": "male"},
        }

        call = ToolCall.from_anthropic(anthropic_response)

        assert call.tool_name == "interpret_lab"
        assert call.arguments["hemoglobin"] == 12.5

    def test_to_dict(self):
        """Test serialization to dict."""
        call = ToolCall(
            tool_name="test_tool",
            arguments={"key": "value"},
        )
        d = call.to_dict()

        assert "id" in d
        assert d["tool_name"] == "test_tool"
        assert d["arguments"] == {"key": "value"}
        assert "created_at" in d

    def test_from_openai_invalid_json(self):
        """Test handling of invalid JSON in arguments."""
        openai_response = {
            "function": {
                "name": "test",
                "arguments": "{invalid json}",
            },
        }

        call = ToolCall.from_openai(openai_response)
        assert call.tool_name == "test"
        assert call.arguments == {}


# =============================================================================
# ToolResult Tests
# =============================================================================


class TestToolResult:
    """Tests for ToolResult model."""

    def test_create_success_result(self):
        """Test creating a successful result."""
        call_id = uuid4()
        result = ToolResult(
            call_id=call_id,
            tool_name="calculate_dose",
            status=ToolStatus.SUCCESS,
            output={"dose": 500, "unit": "mg", "frequency": "q8h"},
        )

        assert result.is_success is True
        assert result.is_error is False
        assert result.output["dose"] == 500
        assert result.error is None

    def test_create_error_result(self):
        """Test creating an error result."""
        call_id = uuid4()
        result = ToolResult(
            call_id=call_id,
            tool_name="calculate_dose",
            status=ToolStatus.ERROR,
            error="Invalid weight: must be positive",
            error_code="VALIDATION_ERROR",
        )

        assert result.is_success is False
        assert result.is_error is True
        assert result.error == "Invalid weight: must be positive"

    def test_to_llm_format_success(self):
        """Test formatting successful result for LLM."""
        call_id = uuid4()
        result = ToolResult(
            call_id=call_id,
            tool_name="check_interactions",
            status=ToolStatus.SUCCESS,
            output={
                "interactions": [
                    {"drug1": "warfarin", "drug2": "aspirin", "severity": "high"}
                ]
            },
        )

        llm_format = result.to_llm_format()

        # to_llm_format returns a string
        assert isinstance(llm_format, str)
        content = json.loads(llm_format)
        assert "interactions" in content

    def test_to_llm_format_error(self):
        """Test formatting error result for LLM."""
        call_id = uuid4()
        result = ToolResult(
            call_id=call_id,
            tool_name="failing_tool",
            status=ToolStatus.ERROR,
            error="Something went wrong",
        )

        llm_format = result.to_llm_format()
        assert "failing_tool" in llm_format
        assert "Something went wrong" in llm_format

    def test_to_dict(self):
        """Test serialization to dict."""
        call_id = uuid4()
        result = ToolResult(
            call_id=call_id,
            tool_name="test_tool",
            status=ToolStatus.SUCCESS,
            output={"ok": True},
        )

        d = result.to_dict()
        assert d["call_id"] == str(call_id)
        assert d["tool_name"] == "test_tool"
        assert d["status"] == "success"
        assert d["output"] == {"ok": True}

    def test_to_openai_format(self):
        """Test conversion to OpenAI tool result format."""
        call_id = uuid4()
        result = ToolResult(
            call_id=call_id,
            tool_name="test_tool",
            status=ToolStatus.SUCCESS,
            output={"data": "value"},
        )

        fmt = result.to_openai_format()
        assert fmt["role"] == "tool"
        assert fmt["tool_call_id"] == str(call_id)
        assert "content" in fmt

    def test_timeout_status(self):
        """Test timeout status is considered error."""
        result = ToolResult(
            call_id=uuid4(),
            tool_name="slow_tool",
            status=ToolStatus.TIMEOUT,
        )
        assert result.is_error is True
        assert result.is_success is False

    def test_cancelled_status(self):
        """Test cancelled status is considered error."""
        result = ToolResult(
            call_id=uuid4(),
            tool_name="cancelled_tool",
            status=ToolStatus.CANCELLED,
        )
        assert result.is_error is True
        assert result.is_success is False


# =============================================================================
# ToolError Tests
# =============================================================================


class TestToolError:
    """Tests for ToolError model."""

    def test_create_error(self):
        """Test creating a tool error."""
        error = ToolError(
            code="VALIDATION_ERROR",
            message="Invalid weight: must be positive",
            tool_name="calculate_dose",
        )

        assert error.code == "VALIDATION_ERROR"
        assert error.message == "Invalid weight: must be positive"
        assert error.tool_name == "calculate_dose"
        assert error.recoverable is True

    def test_to_dict(self):
        """Test serialization to dict."""
        error = ToolError(
            code="INTERNAL_ERROR",
            message="Unexpected failure",
            tool_name="broken_tool",
            recoverable=False,
        )

        d = error.to_dict()
        assert d["code"] == "INTERNAL_ERROR"
        assert d["message"] == "Unexpected failure"
        assert d["tool_name"] == "broken_tool"
        assert d["recoverable"] is False

    def test_to_result(self):
        """Test converting error to ToolResult."""
        call_id = uuid4()
        error = ToolError(
            code="TIMEOUT",
            message="Tool timed out",
            tool_name="slow_tool",
        )

        result = error.to_result(call_id)
        assert result.call_id == call_id
        assert result.tool_name == "slow_tool"
        assert result.status == ToolStatus.ERROR
        assert result.error == "Tool timed out"
        assert result.error_code == "TIMEOUT"

    def test_error_codes(self):
        """Test error code constants."""
        assert ToolError.VALIDATION_ERROR == "VALIDATION_ERROR"
        assert ToolError.NOT_FOUND == "TOOL_NOT_FOUND"
        assert ToolError.TIMEOUT == "EXECUTION_TIMEOUT"
        assert ToolError.PERMISSION_DENIED == "PERMISSION_DENIED"
        assert ToolError.RATE_LIMITED == "RATE_LIMITED"
        assert ToolError.INTERNAL_ERROR == "INTERNAL_ERROR"


# =============================================================================
# ToolRegistry Tests
# =============================================================================


class TestToolRegistry:
    """Tests for ToolRegistry."""

    def test_register_tool(self, fresh_registry: ToolRegistry):
        """Test registering a tool."""

        async def my_tool(x: str) -> dict:
            return {"result": x}

        definition = ToolDefinition(
            name="my_tool",
            description="A test tool",
            category=ToolCategory.UTILITY,
            parameters=[],
            handler=my_tool,
        )

        fresh_registry.register(definition)

        assert fresh_registry.get("my_tool") is not None

    def test_get_nonexistent_tool(self, fresh_registry: ToolRegistry):
        """Test getting a tool that doesn't exist."""
        result = fresh_registry.get("nonexistent")
        assert result is None

    def test_get_by_category(self, fresh_registry: ToolRegistry):
        """Test filtering tools by category."""
        for i, category in enumerate(
            [ToolCategory.DRUG, ToolCategory.DRUG, ToolCategory.LAB]
        ):

            async def handler() -> dict:
                return {}

            fresh_registry.register(
                ToolDefinition(
                    name=f"tool_{i}",
                    description=f"Tool {i}",
                    category=category,
                    parameters=[],
                    handler=handler,
                )
            )

        drug_tools = fresh_registry.get_by_category(ToolCategory.DRUG)
        assert len(drug_tools) == 2

        lab_tools = fresh_registry.get_by_category(ToolCategory.LAB)
        assert len(lab_tools) == 1

    def test_enable_disable_tool(
        self, fresh_registry: ToolRegistry, sample_definition: ToolDefinition
    ):
        """Test enabling and disabling a tool."""
        fresh_registry.register(sample_definition)

        # Disable
        assert fresh_registry.disable("check_medication") is True
        tool_def = fresh_registry.get("check_medication")
        assert tool_def.enabled is False

        # Enable
        assert fresh_registry.enable("check_medication") is True
        tool_def = fresh_registry.get("check_medication")
        assert tool_def.enabled is True

    def test_unregister(self, fresh_registry: ToolRegistry):
        """Test unregistering a tool."""

        async def handler() -> dict:
            return {}

        fresh_registry.register(
            ToolDefinition(
                name="removable",
                description="Removable tool",
                category=ToolCategory.UTILITY,
                parameters=[],
                handler=handler,
            )
        )

        assert fresh_registry.get("removable") is not None
        result = fresh_registry.unregister("removable")
        assert result is True
        assert fresh_registry.get("removable") is None

    def test_unregister_nonexistent(self, fresh_registry: ToolRegistry):
        """Test unregistering a tool that doesn't exist."""
        result = fresh_registry.unregister("nonexistent")
        assert result is False

    def test_len_and_contains(self, fresh_registry: ToolRegistry):
        """Test __len__ and __contains__."""

        async def handler() -> dict:
            return {}

        assert len(fresh_registry) == 0
        assert "my_tool" not in fresh_registry

        fresh_registry.register(
            ToolDefinition(
                name="my_tool",
                description="Test",
                category=ToolCategory.UTILITY,
                parameters=[],
                handler=handler,
            )
        )

        assert len(fresh_registry) == 1
        assert "my_tool" in fresh_registry

    def test_summary(self, fresh_registry: ToolRegistry, sample_definition):
        """Test registry summary."""
        fresh_registry.register(sample_definition)
        summary = fresh_registry.summary()

        assert "total_tools" in summary
        assert summary["total_tools"] == 1

    def test_to_openai_format(
        self, fresh_registry: ToolRegistry, sample_definition: ToolDefinition
    ):
        """Test converting all tools to OpenAI format."""
        fresh_registry.register(sample_definition)
        openai_tools = fresh_registry.to_openai_format()

        assert isinstance(openai_tools, list)
        assert len(openai_tools) == 1
        assert openai_tools[0]["type"] == "function"

    def test_to_anthropic_format(
        self, fresh_registry: ToolRegistry, sample_definition: ToolDefinition
    ):
        """Test converting all tools to Anthropic format."""
        fresh_registry.register(sample_definition)
        anthropic_tools = fresh_registry.to_anthropic_format()

        assert isinstance(anthropic_tools, list)
        assert len(anthropic_tools) == 1
        assert "input_schema" in anthropic_tools[0]


# =============================================================================
# ToolExecutor Tests
# =============================================================================


class TestToolExecutor:
    """Tests for ToolExecutor."""

    @pytest.mark.asyncio
    async def test_execute_simple_tool(self, executor: ToolExecutor):
        """Test executing a simple tool."""

        async def greet(name: str) -> dict:
            return {"greeting": f"Hello, {name}!"}

        definition = ToolDefinition(
            name="greet",
            description="Greet someone",
            category=ToolCategory.UTILITY,
            parameters=[string_param("name", "Name to greet")],
            handler=greet,
        )

        executor._registry.register(definition)

        call = ToolCall(tool_name="greet", arguments={"name": "MedeX"})
        result = await executor.execute(call)

        assert result.is_success is True
        assert result.output["greeting"] == "Hello, MedeX!"

    @pytest.mark.asyncio
    async def test_execute_with_validation_error(self, executor: ToolExecutor):
        """Test execution with invalid arguments."""

        async def calculate(x: float, y: float) -> dict:
            return {"sum": x + y}

        definition = ToolDefinition(
            name="calculate",
            description="Calculate sum",
            category=ToolCategory.UTILITY,
            parameters=[
                number_param("x", "First number", required=True),
                number_param("y", "Second number", required=True),
            ],
            handler=calculate,
        )

        executor._registry.register(definition)

        # Missing required argument
        call = ToolCall(tool_name="calculate", arguments={"x": 5})
        result = await executor.execute(call)

        assert result.is_success is False

    @pytest.mark.asyncio
    async def test_execute_tool_not_found(self, executor: ToolExecutor):
        """Test execution of non-existent tool."""
        call = ToolCall(tool_name="nonexistent_tool", arguments={})
        result = await executor.execute(call)

        assert result.is_success is False
        assert result.is_error is True

    @pytest.mark.asyncio
    async def test_execute_batch(self, executor: ToolExecutor):
        """Test batch execution."""

        async def echo(msg: str) -> dict:
            return {"echo": msg}

        definition = ToolDefinition(
            name="echo",
            description="Echo message",
            category=ToolCategory.UTILITY,
            parameters=[string_param("msg", "Message")],
            handler=echo,
        )

        executor._registry.register(definition)

        calls = [
            ToolCall(tool_name="echo", arguments={"msg": "one"}),
            ToolCall(tool_name="echo", arguments={"msg": "two"}),
            ToolCall(tool_name="echo", arguments={"msg": "three"}),
        ]

        results = await executor.execute_batch(calls)

        assert len(results) == 3
        assert all(r.is_success for r in results)
        assert results[0].output["echo"] == "one"
        assert results[1].output["echo"] == "two"
        assert results[2].output["echo"] == "three"

    @pytest.mark.asyncio
    async def test_execute_batch_empty(self, executor: ToolExecutor):
        """Test batch execution with empty list."""
        results = await executor.execute_batch([])
        assert results == []

    @pytest.mark.asyncio
    async def test_execute_batch_sequential(self, executor: ToolExecutor):
        """Test sequential batch execution."""

        async def counter(val: int) -> dict:
            return {"value": val}

        definition = ToolDefinition(
            name="counter",
            description="Return value",
            category=ToolCategory.UTILITY,
            parameters=[],
            handler=counter,
        )

        executor._registry.register(definition)

        calls = [ToolCall(tool_name="counter", arguments={"val": i}) for i in range(3)]

        results = await executor.execute_batch(calls, parallel=False)
        assert len(results) == 3

    @pytest.mark.asyncio
    async def test_get_metrics(self, executor: ToolExecutor):
        """Test metrics collection."""

        async def metric_tool() -> dict:
            return {"ok": True}

        definition = ToolDefinition(
            name="metric_tool",
            description="Tool for metrics",
            category=ToolCategory.UTILITY,
            parameters=[],
            handler=metric_tool,
        )

        executor._registry.register(definition)

        for _ in range(3):
            call = ToolCall(tool_name="metric_tool", arguments={})
            await executor.execute(call)

        metrics = executor.get_metrics()
        assert metrics["total_executions"] == 3
        assert metrics["successful"] == 3

    @pytest.mark.asyncio
    async def test_reset_metrics(self, executor: ToolExecutor):
        """Test resetting metrics."""

        async def dummy() -> dict:
            return {}

        definition = ToolDefinition(
            name="dummy",
            description="Dummy",
            category=ToolCategory.UTILITY,
            parameters=[],
            handler=dummy,
        )

        executor._registry.register(definition)

        call = ToolCall(tool_name="dummy", arguments={})
        await executor.execute(call)

        executor.reset_metrics()
        metrics = executor.get_metrics()
        assert metrics["total_executions"] == 0


# =============================================================================
# Medical Tools Tests
# =============================================================================


class TestDrugInteractionTools:
    """Tests for drug interaction tools."""

    @pytest.mark.asyncio
    async def test_check_drug_interactions_no_interactions(self):
        """Test with drugs that don't interact."""
        from medex.tools.medical.drug_interactions import check_drug_interactions

        result = await check_drug_interactions(["amoxicillin", "paracetamol"])

        assert "interactions" in result

    @pytest.mark.asyncio
    async def test_get_drug_info(self):
        """Test getting drug information."""
        from medex.tools.medical.drug_interactions import get_drug_info

        result = await get_drug_info("metformin")

        assert "name" in result or "drug" in result
        assert "found" in result

    @pytest.mark.asyncio
    async def test_check_drug_interactions_single_drug(self):
        """Test with single drug (edge case)."""
        from medex.tools.medical.drug_interactions import check_drug_interactions

        result = await check_drug_interactions(["aspirin"])
        assert "interactions" in result

    @pytest.mark.asyncio
    async def test_check_drug_interactions_multiple(self):
        """Test with multiple drugs."""
        from medex.tools.medical.drug_interactions import check_drug_interactions

        result = await check_drug_interactions(["warfarin", "aspirin", "ibuprofen"])
        assert "interactions" in result


class TestDosageCalculatorTools:
    """Tests for dosage calculator tools."""

    @pytest.mark.asyncio
    async def test_calculate_pediatric_dose(self):
        """Test pediatric dose calculation."""
        from medex.tools.medical.dosage_calculator import calculate_pediatric_dose

        result = await calculate_pediatric_dose(
            drug_name="amoxicillin",
            weight_kg=20,
        )

        assert "drug_name" in result or "drug" in result

    @pytest.mark.asyncio
    async def test_calculate_bsa(self):
        """Test BSA calculation."""
        from medex.tools.medical.dosage_calculator import calculate_bsa

        result = await calculate_bsa(
            weight_kg=70,
            height_cm=175,
        )

        assert "bsa_m2" in result
        # bsa_m2 is a dict with multiple formula results
        bsa = result["bsa_m2"]
        assert isinstance(bsa, dict)
        assert bsa["recommended"] > 0
        assert bsa["recommended"] < 3

    @pytest.mark.asyncio
    async def test_calculate_creatinine_clearance(self):
        """Test CrCl calculation."""
        from medex.tools.medical.dosage_calculator import calculate_creatinine_clearance

        result = await calculate_creatinine_clearance(
            age_years=65,
            weight_kg=70,
            creatinine_mg_dl=1.2,
            is_female=False,
        )

        assert "creatinine_clearance_ml_min" in result
        assert result["creatinine_clearance_ml_min"] > 0
        assert "gfr_category" in result

    @pytest.mark.asyncio
    async def test_adjust_dose_renal(self):
        """Test renal dose adjustment."""
        from medex.tools.medical.dosage_calculator import adjust_dose_renal

        result = await adjust_dose_renal(
            drug_name="metformin",
            gfr=45.0,
        )

        assert isinstance(result, dict)


class TestLabInterpreterTools:
    """Tests for lab interpreter tools."""

    @pytest.mark.asyncio
    async def test_interpret_cbc(self):
        """Test CBC interpretation."""
        from medex.tools.medical.lab_interpreter import interpret_cbc

        result = await interpret_cbc(
            hemoglobin=10.5,
            sex="female",
            age_years=45,
            mcv=75,
        )

        assert "interpretations" in result
        assert "clinical_findings" in result
        assert "differential_diagnoses" in result

    @pytest.mark.asyncio
    async def test_interpret_liver_panel(self):
        """Test liver panel interpretation."""
        from medex.tools.medical.lab_interpreter import interpret_liver_panel

        result = await interpret_liver_panel(
            alt=150,
            ast=120,
            alp=90,
        )

        assert "pattern" in result
        assert "de_ritis_ratio" in result
        assert result["pattern"] in ["normal", "hepatocelular", "colestásico", "mixto"]

    @pytest.mark.asyncio
    async def test_interpret_thyroid_panel(self):
        """Test thyroid panel interpretation."""
        from medex.tools.medical.lab_interpreter import interpret_thyroid_panel

        result = await interpret_thyroid_panel(
            tsh=0.1,
            t4_free=2.5,
        )

        assert "thyroid_status" in result
        assert "interpretations" in result


class TestEmergencyDetectorTools:
    """Tests for emergency detector tools."""

    @pytest.mark.asyncio
    async def test_detect_emergency_cardiac(self):
        """Test detection of cardiac emergency."""
        from medex.tools.medical.emergency_detector import detect_emergency

        result = await detect_emergency(
            symptoms=["dolor torácico", "sudoración", "disnea"],
            onset="súbito",
            duration="30 minutos",
        )

        assert result["emergency_detected"] is True
        assert result["triage"]["level"] <= 2

    @pytest.mark.asyncio
    async def test_detect_emergency_non_urgent(self):
        """Test with non-urgent symptoms."""
        from medex.tools.medical.emergency_detector import detect_emergency

        result = await detect_emergency(
            symptoms=["tos leve", "congestión nasal"],
            onset="gradual",
            duration="3 días",
        )

        assert result["triage"]["level"] >= 4

    @pytest.mark.asyncio
    async def test_check_critical_values(self):
        """Test critical lab value detection."""
        from medex.tools.medical.emergency_detector import check_critical_values

        result = await check_critical_values(lab_values={"potasio": 7.0, "glucosa": 40})

        assert "has_critical_values" in result

    @pytest.mark.asyncio
    async def test_quick_triage(self):
        """Test quick triage assessment."""
        from medex.tools.medical.emergency_detector import quick_triage

        result = await quick_triage(
            chief_complaint="dolor abdominal severo",
            severity="severo",
            duration_hours=2,
            worsening=True,
        )

        assert "triage_level" in result
        assert "triage_color" in result
        assert "recommendation" in result


# =============================================================================
# Enum Tests
# =============================================================================


class TestEnums:
    """Tests for tool system enums."""

    def test_tool_category_values(self):
        """Test ToolCategory enum values."""
        assert ToolCategory.DRUG.value == "drug"
        assert ToolCategory.LAB.value == "lab"
        assert ToolCategory.DOSAGE.value == "dosage"
        assert ToolCategory.EMERGENCY.value == "emergency"
        assert ToolCategory.DIAGNOSIS.value == "diagnosis"
        assert ToolCategory.UTILITY.value == "utility"

    def test_tool_status_values(self):
        """Test ToolStatus enum values."""
        assert ToolStatus.PENDING.value == "pending"
        assert ToolStatus.RUNNING.value == "running"
        assert ToolStatus.SUCCESS.value == "success"
        assert ToolStatus.ERROR.value == "error"
        assert ToolStatus.TIMEOUT.value == "timeout"

    def test_parameter_type_values(self):
        """Test ParameterType enum values."""
        assert ParameterType.STRING.value == "string"
        assert ParameterType.NUMBER.value == "number"
        assert ParameterType.INTEGER.value == "integer"
        assert ParameterType.BOOLEAN.value == "boolean"
        assert ParameterType.ARRAY.value == "array"
        assert ParameterType.OBJECT.value == "object"


# =============================================================================
# Run Tests
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
