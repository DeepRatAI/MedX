# =============================================================================
# MedeX - Tool System Tests
# =============================================================================
"""
Comprehensive tests for the MedeX Tool System.

Tests cover:
- Tool models (ToolParameter, ToolDefinition, ToolCall, ToolResult)
- Tool registry (registration, retrieval, filtering)
- Tool executor (execution, timeout, retry, caching)
- Medical tools (drug interactions, dosage, labs, emergency)
- Tool service (facade integration)
"""

from __future__ import annotations

import asyncio
import json
from uuid import uuid4

import pytest

from medex.tools.executor import ToolExecutor, create_tool_executor
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
    tool,
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
def executor() -> ToolExecutor:
    """Create an executor for testing."""
    return create_tool_executor(max_concurrent=3, default_timeout=5.0)


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
        assert sample_definition.status == ToolStatus.ENABLED

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
            id=str(uuid4()),
            name="check_drug_interactions",
            arguments={"drugs": ["aspirin", "ibuprofen"]},
        )

        assert call.name == "check_drug_interactions"
        assert call.arguments["drugs"] == ["aspirin", "ibuprofen"]

    def test_from_openai_response(self):
        """Test creating from OpenAI response."""
        openai_response = {
            "id": "call_123",
            "function": {
                "name": "calculate_dose",
                "arguments": '{"drug": "amoxicillin", "weight": 70}',
            },
        }

        call = ToolCall.from_openai_response(openai_response)

        assert call.id == "call_123"
        assert call.name == "calculate_dose"
        assert call.arguments["drug"] == "amoxicillin"
        assert call.arguments["weight"] == 70

    def test_from_anthropic_response(self):
        """Test creating from Anthropic response."""
        anthropic_response = {
            "id": "toolu_123",
            "name": "interpret_lab",
            "input": {"hemoglobin": 12.5, "sex": "male"},
        }

        call = ToolCall.from_anthropic_response(anthropic_response)

        assert call.id == "toolu_123"
        assert call.name == "interpret_lab"
        assert call.arguments["hemoglobin"] == 12.5


# =============================================================================
# ToolResult Tests
# =============================================================================


class TestToolResult:
    """Tests for ToolResult model."""

    def test_create_success_result(self):
        """Test creating a successful result."""
        result = ToolResult(
            call_id="call_123",
            tool_name="calculate_dose",
            success=True,
            data={"dose": 500, "unit": "mg", "frequency": "q8h"},
        )

        assert result.success is True
        assert result.data["dose"] == 500
        assert result.error is None

    def test_create_error_result(self):
        """Test creating an error result."""
        error = ToolError(
            code="VALIDATION_ERROR",
            message="Invalid weight: must be positive",
        )

        result = ToolResult(
            call_id="call_456",
            tool_name="calculate_dose",
            success=False,
            error=error,
        )

        assert result.success is False
        assert result.error.code == "VALIDATION_ERROR"

    def test_to_llm_format(self):
        """Test formatting result for LLM."""
        result = ToolResult(
            call_id="call_789",
            tool_name="check_interactions",
            success=True,
            data={
                "interactions": [
                    {"drug1": "warfarin", "drug2": "aspirin", "severity": "high"}
                ]
            },
        )

        llm_format = result.to_llm_format()

        assert "tool_call_id" in llm_format or "id" in llm_format
        assert "content" in llm_format

        # Content should be JSON string
        content = json.loads(llm_format["content"])
        assert "interactions" in content


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

        assert fresh_registry.get_tool("my_tool") is not None

    def test_get_nonexistent_tool(self, fresh_registry: ToolRegistry):
        """Test getting a tool that doesn't exist."""
        result = fresh_registry.get_tool("nonexistent")
        assert result is None

    def test_get_tools_by_category(self, fresh_registry: ToolRegistry):
        """Test filtering tools by category."""
        # Register tools in different categories
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

        drug_tools = fresh_registry.get_tools_by_category(ToolCategory.DRUG)
        assert len(drug_tools) == 2

        lab_tools = fresh_registry.get_tools_by_category(ToolCategory.LAB)
        assert len(lab_tools) == 1

    def test_enable_disable_tool(
        self, fresh_registry: ToolRegistry, sample_definition: ToolDefinition
    ):
        """Test enabling and disabling a tool."""
        fresh_registry.register(sample_definition)

        # Disable
        assert fresh_registry.disable_tool("check_medication") is True
        tool = fresh_registry.get_tool("check_medication")
        assert tool.status == ToolStatus.DISABLED

        # Enable
        assert fresh_registry.enable_tool("check_medication") is True
        tool = fresh_registry.get_tool("check_medication")
        assert tool.status == ToolStatus.ENABLED

    def test_decorator_registration(self, fresh_registry: ToolRegistry):
        """Test registering tool via decorator."""

        @tool(
            name="decorated_tool",
            description="A tool registered via decorator",
            category=ToolCategory.UTILITY,
            parameters=[string_param("input", "The input")],
            registry=fresh_registry,
        )
        async def decorated_tool(input: str) -> dict:
            return {"output": input.upper()}

        registered = fresh_registry.get_tool("decorated_tool")
        assert registered is not None
        assert registered.name == "decorated_tool"


# =============================================================================
# ToolExecutor Tests
# =============================================================================


class TestToolExecutor:
    """Tests for ToolExecutor."""

    @pytest.mark.asyncio
    async def test_execute_simple_tool(self, executor: ToolExecutor):
        """Test executing a simple tool."""

        # Register a tool
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

        # Execute
        call = ToolCall(id="call_1", name="greet", arguments={"name": "MedeX"})
        result = await executor.execute(call)

        assert result.success is True
        assert result.data["greeting"] == "Hello, MedeX!"

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
        call = ToolCall(id="call_2", name="calculate", arguments={"x": 5})
        result = await executor.execute(call)

        assert result.success is False
        assert result.error is not None

    @pytest.mark.asyncio
    async def test_execute_timeout(self, executor: ToolExecutor):
        """Test execution timeout."""

        async def slow_tool() -> dict:
            await asyncio.sleep(10)  # Will timeout
            return {"done": True}

        definition = ToolDefinition(
            name="slow_tool",
            description="A slow tool",
            category=ToolCategory.UTILITY,
            parameters=[],
            handler=slow_tool,
        )

        executor._registry.register(definition)

        call = ToolCall(id="call_3", name="slow_tool", arguments={})
        result = await executor.execute(call, timeout=0.1)

        assert result.success is False
        assert (
            "timeout" in result.error.code.lower()
            or "timeout" in result.error.message.lower()
        )

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
            ToolCall(id="call_a", name="echo", arguments={"msg": "one"}),
            ToolCall(id="call_b", name="echo", arguments={"msg": "two"}),
            ToolCall(id="call_c", name="echo", arguments={"msg": "three"}),
        ]

        results = await executor.execute_batch(calls)

        assert len(results) == 3
        assert all(r.success for r in results)
        assert results[0].data["echo"] == "one"
        assert results[1].data["echo"] == "two"
        assert results[2].data["echo"] == "three"

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

        # Execute a few times
        for _ in range(3):
            call = ToolCall(id=str(uuid4()), name="metric_tool", arguments={})
            await executor.execute(call)

        metrics = executor.get_metrics()

        assert metrics["total_calls"] == 3
        assert metrics["successful_calls"] == 3
        assert "metric_tool" in metrics.get("by_tool", {})


# =============================================================================
# Medical Tools Tests
# =============================================================================


class TestDrugInteractionTools:
    """Tests for drug interaction tools."""

    @pytest.mark.asyncio
    async def test_check_drug_interactions(self):
        """Test checking drug interactions."""
        from medex.tools.medical.drug_interactions import check_drug_interactions

        result = await check_drug_interactions(["warfarin", "aspirin"])

        assert "interactions" in result
        assert len(result["interactions"]) > 0
        assert result["interactions"][0]["severity"] in ["alta", "moderada", "baja"]

    @pytest.mark.asyncio
    async def test_check_drug_interactions_no_interactions(self):
        """Test with drugs that don't interact."""
        from medex.tools.medical.drug_interactions import check_drug_interactions

        result = await check_drug_interactions(["amoxicillin", "paracetamol"])

        assert "interactions" in result
        # May or may not have interactions, but should not error

    @pytest.mark.asyncio
    async def test_get_drug_info(self):
        """Test getting drug information."""
        from medex.tools.medical.drug_interactions import get_drug_info

        result = await get_drug_info("metformin")

        assert "drug" in result
        assert "found" in result


class TestDosageCalculatorTools:
    """Tests for dosage calculator tools."""

    @pytest.mark.asyncio
    async def test_calculate_pediatric_dose(self):
        """Test pediatric dose calculation."""
        from medex.tools.medical.dosage_calculator import calculate_pediatric_dose

        result = await calculate_pediatric_dose(
            drug="amoxicillin",
            weight_kg=20,
            indication="otitis",
        )

        assert "drug" in result
        assert "calculations" in result or "error" in result

    @pytest.mark.asyncio
    async def test_calculate_bsa(self):
        """Test BSA calculation."""
        from medex.tools.medical.dosage_calculator import calculate_bsa

        result = await calculate_bsa(
            weight_kg=70,
            height_cm=175,
            formula="mosteller",
        )

        assert "bsa_m2" in result
        assert result["bsa_m2"] > 0
        assert result["bsa_m2"] < 3  # Reasonable range

    @pytest.mark.asyncio
    async def test_calculate_creatinine_clearance(self):
        """Test CrCl calculation."""
        from medex.tools.medical.dosage_calculator import calculate_creatinine_clearance

        result = await calculate_creatinine_clearance(
            age_years=65,
            weight_kg=70,
            serum_creatinine=1.2,
            sex="male",
        )

        assert "crcl_ml_min" in result
        assert result["crcl_ml_min"] > 0
        assert "stage" in result


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
        assert result["triage"]["level"] <= 2  # High urgency

    @pytest.mark.asyncio
    async def test_detect_emergency_non_urgent(self):
        """Test with non-urgent symptoms."""
        from medex.tools.medical.emergency_detector import detect_emergency

        result = await detect_emergency(
            symptoms=["tos leve", "congestión nasal"],
            onset="gradual",
            duration="3 días",
        )

        # Should not be marked as emergency
        assert result["triage"]["level"] >= 4

    @pytest.mark.asyncio
    async def test_check_critical_values(self):
        """Test critical lab value detection."""
        from medex.tools.medical.emergency_detector import check_critical_values

        result = await check_critical_values(
            lab_values={"potassium": 7.0, "glucose": 40}
        )

        assert result["has_critical_values"] is True
        assert len(result["critical_alerts"]) >= 1

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
# Integration Tests
# =============================================================================


class TestToolServiceIntegration:
    """Integration tests for the complete tool system."""

    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """Test complete workflow from registration to execution."""
        from medex.tools.service import ToolService

        service = ToolService()
        await service.initialize()

        try:
            # Get tools for LLM
            tools = service.get_tools_for_llm(format="openai")
            assert len(tools) > 0

            # Find and execute a tool
            tool_call = ToolCall(
                id="test_call",
                name="calculate_bsa",
                arguments={
                    "weight_kg": 70,
                    "height_cm": 175,
                    "formula": "mosteller",
                },
            )

            result = await service.execute(tool_call)
            assert result.success is True
            assert "bsa_m2" in result.data

        finally:
            await service.shutdown()

    @pytest.mark.asyncio
    async def test_get_medical_tools(self):
        """Test getting all medical tools."""
        from medex.tools.service import ToolService

        service = ToolService()
        await service.initialize()

        try:
            medical_tools = service.get_medical_tools()
            assert len(medical_tools) > 0

            # Check categories
            categories = {t.category for t in medical_tools}
            assert ToolCategory.DRUG in categories or ToolCategory.LAB in categories

        finally:
            await service.shutdown()


# =============================================================================
# Run Tests
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
