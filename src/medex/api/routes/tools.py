# =============================================================================
# MedeX - Tools API Routes
# =============================================================================
"""
FastAPI routes for medical tools.

Provides fast, direct access to medical tools without LLM overhead:
- Drug interaction checker
- Dosage calculator
- Lab value interpreter

These endpoints use local databases/dictionaries for instant results.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

# Import tools directly for fast execution
from medex.tools.medical.drug_interactions import check_drug_interactions

logger = logging.getLogger(__name__)

# Create router with prefix
router = APIRouter(prefix="/api/v1/tools", tags=["tools"])


# =============================================================================
# Request/Response Models
# =============================================================================


class DrugInteractionsRequest(BaseModel):
    """Request for drug interaction check."""

    drugs: list[str] = Field(
        ..., min_items=2, description="List of drug names to check"
    )


class DrugInteractionItem(BaseModel):
    """Single drug interaction result."""

    drug_a: str
    drug_b: str
    severity: str
    mechanism: str
    clinical_effect: str
    management: str


class DrugInteractionsResponse(BaseModel):
    """Response for drug interaction check."""

    interactions: list[DrugInteractionItem]
    checked_drugs: list[str]
    total_interactions: int
    checked_at: str


class DosageRequest(BaseModel):
    """Request for dosage calculation."""

    drug_name: str = Field(..., description="Name of the drug")
    patient_weight: float = Field(..., gt=0, description="Patient weight in kg")
    patient_age: int | None = Field(
        None, ge=0, le=120, description="Patient age in years"
    )
    indication: str | None = Field(None, description="Clinical indication")


class DosageResponse(BaseModel):
    """Response for dosage calculation."""

    drug_name: str
    recommended_dose: str
    dose_per_kg: float | None
    frequency: str
    max_daily_dose: str
    route: str
    warnings: list[str]
    adjustments: list[str]
    calculated_at: str


class LabInterpretRequest(BaseModel):
    """Request for lab value interpretation."""

    test_name: str = Field(..., description="Name of the lab test")
    value: float = Field(..., description="Lab test value")
    unit: str | None = Field(None, description="Unit of measurement")
    patient_sex: str | None = Field(None, description="Patient sex (M/F)")
    patient_age: int | None = Field(None, description="Patient age in years")


class LabInterpretResponse(BaseModel):
    """Response for lab interpretation."""

    test_name: str
    value: float
    unit: str
    reference_range: str
    interpretation: str
    status: str  # normal, low, high, critical_low, critical_high
    clinical_significance: str
    recommendations: list[str]
    interpreted_at: str


# =============================================================================
# Drug Interactions Endpoint
# =============================================================================


@router.post("/drug-interactions", response_model=DrugInteractionsResponse)
async def check_interactions(
    request: DrugInteractionsRequest,
) -> DrugInteractionsResponse:
    """
    Check for drug interactions between multiple medications.

    Uses local database for instant results without LLM latency.

    Args:
        request: List of drug names to check

    Returns:
        List of found interactions with severity and management
    """
    try:
        # Call the tool directly (synchronous, uses local dictionary)
        result: DrugInteractionResult = await check_drug_interactions(  # noqa: F821
            drugs=request.drugs
        )

        # Convert to response format
        interactions = [
            DrugInteractionItem(
                drug_a=interaction.drug_a,
                drug_b=interaction.drug_b,
                severity=interaction.severity,
                mechanism=interaction.mechanism,
                clinical_effect=interaction.clinical_effect,
                management=interaction.management,
            )
            for interaction in result.interactions
        ]

        return DrugInteractionsResponse(
            interactions=interactions,
            checked_drugs=request.drugs,
            total_interactions=len(interactions),
            checked_at=datetime.now().isoformat(),
        )

    except Exception as e:
        logger.error(f"Drug interaction check failed: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error checking interactions: {str(e)}"
        ) from e


# =============================================================================
# Dosage Calculator Endpoint
# =============================================================================


@router.post("/dosage-calculator", response_model=DosageResponse)
async def calculate_drug_dosage(request: DosageRequest) -> DosageResponse:
    """
    Calculate recommended dosage for a medication.

    Uses evidence-based dosing guidelines for instant calculation.

    Args:
        request: Drug name, patient weight, and optional parameters

    Returns:
        Recommended dosage with warnings and adjustments
    """
    try:
        # Call the tool directly
        result: DosageResult = await calculate_dosage(  # noqa: F821
            drug_name=request.drug_name,
            patient_weight_kg=request.patient_weight,
            patient_age_years=request.patient_age,
            indication=request.indication,
        )

        return DosageResponse(
            drug_name=request.drug_name,
            recommended_dose=result.recommended_dose,
            dose_per_kg=result.dose_per_kg,
            frequency=result.frequency,
            max_daily_dose=result.max_daily_dose,
            route=result.route,
            warnings=result.warnings,
            adjustments=result.adjustments,
            calculated_at=datetime.now().isoformat(),
        )

    except Exception as e:
        logger.error(f"Dosage calculation failed: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error calculating dosage: {str(e)}"
        ) from e


# =============================================================================
# Lab Interpreter Endpoint
# =============================================================================


@router.post("/lab-interpreter", response_model=LabInterpretResponse)
async def interpret_lab(request: LabInterpretRequest) -> LabInterpretResponse:
    """
    Interpret a laboratory test value.

    Compares against reference ranges and provides clinical context.

    Args:
        request: Lab test name, value, and patient demographics

    Returns:
        Interpretation with clinical significance and recommendations
    """
    try:
        # Call the tool directly
        result: LabInterpretationResult = await interpret_lab_value(  # noqa: F821
            test_name=request.test_name,
            value=request.value,
            unit=request.unit,
            patient_sex=request.patient_sex,
            patient_age_years=request.patient_age,
        )

        return LabInterpretResponse(
            test_name=request.test_name,
            value=request.value,
            unit=result.unit or request.unit or "",
            reference_range=result.reference_range,
            interpretation=result.interpretation,
            status=result.status,
            clinical_significance=result.clinical_significance,
            recommendations=result.recommendations,
            interpreted_at=datetime.now().isoformat(),
        )

    except Exception as e:
        logger.error(f"Lab interpretation failed: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error interpreting lab value: {str(e)}"
        ) from e


# =============================================================================
# Tools Discovery Endpoint
# =============================================================================


@router.get("/")
async def list_tools() -> dict[str, Any]:
    """
    List all available medical tools.

    Returns:
        Dictionary of available tools with descriptions
    """
    return {
        "tools": [
            {
                "id": "drug-interactions",
                "name": "Drug Interaction Checker",
                "description": "Check for interactions between multiple medications",
                "endpoint": "/api/v1/tools/drug-interactions",
                "method": "POST",
            },
            {
                "id": "dosage-calculator",
                "name": "Dosage Calculator",
                "description": "Calculate medication dosages based on patient parameters",
                "endpoint": "/api/v1/tools/dosage-calculator",
                "method": "POST",
            },
            {
                "id": "lab-interpreter",
                "name": "Lab Value Interpreter",
                "description": "Interpret laboratory test results with clinical context",
                "endpoint": "/api/v1/tools/lab-interpreter",
                "method": "POST",
            },
        ],
        "version": "2.0.0",
    }
