"""
Medical Image Analyzer.

Provides specialized analysis for medical imaging modalities
including radiography, CT, MRI, and ultrasound.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional, List


class ImagingModality(Enum):
    """Supported medical imaging modalities."""

    RADIOGRAPHY = "RX"
    CT = "TAC"
    MRI = "RM"
    ULTRASOUND = "US"
    UNKNOWN = "UNKNOWN"


@dataclass
class ImageValidation:
    """Result of image validation.

    Attributes:
        is_valid: Whether the image is a valid medical image
        modality: Detected imaging modality
        confidence: Confidence in the detection
        message: Validation message
    """

    is_valid: bool
    modality: ImagingModality
    confidence: float
    message: str


class ImageAnalyzer:
    """Medical image analyzer.

    Validates and prepares medical images for AI analysis.
    Supports RX, CT, MRI, and ultrasound modalities.
    """

    # Supported file extensions
    SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".dcm", ".dicom"}

    # Maximum file size (50MB)
    MAX_FILE_SIZE = 50 * 1024 * 1024

    def __init__(self) -> None:
        """Initialize the image analyzer."""
        pass

    def validate_image(self, image_path: str) -> ImageValidation:
        """Validate an image file for medical analysis.

        Args:
            image_path: Path to the image file

        Returns:
            ImageValidation result
        """
        path = Path(image_path)

        # Check file exists
        if not path.exists():
            return ImageValidation(
                is_valid=False,
                modality=ImagingModality.UNKNOWN,
                confidence=0.0,
                message=f"File not found: {image_path}",
            )

        # Check extension
        if path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
            return ImageValidation(
                is_valid=False,
                modality=ImagingModality.UNKNOWN,
                confidence=0.0,
                message=f"Unsupported format: {path.suffix}. Use JPG, PNG, or DICOM.",
            )

        # Check file size
        if path.stat().st_size > self.MAX_FILE_SIZE:
            return ImageValidation(
                is_valid=False,
                modality=ImagingModality.UNKNOWN,
                confidence=0.0,
                message=f"File too large. Maximum size: 50MB",
            )

        # Image is valid - modality detection happens via AI
        return ImageValidation(
            is_valid=True,
            modality=ImagingModality.UNKNOWN,
            confidence=0.5,
            message="Image validated. Modality will be detected during analysis.",
        )

    @staticmethod
    def get_supported_modalities() -> List[str]:
        """Get list of supported imaging modalities.

        Returns:
            List of modality names
        """
        return [m.value for m in ImagingModality if m != ImagingModality.UNKNOWN]

    @staticmethod
    def format_rejection_message() -> str:
        """Get standard rejection message for invalid images.

        Returns:
            Rejection message string
        """
        return (
            "❌ No se puede analizar la imagen. "
            "Por favor, provee una RX, TAC, RM o US para el análisis médico."
        )
