# =============================================================================
# MedeX - Vision Module Tests
# =============================================================================
"""
Tests for the MedeX Vision module.

Covers:
- ImageAnalyzer: validation, supported modalities, rejection messages
- ImagingModality: enum values
- ImageValidation: dataclass construction
"""

from __future__ import annotations

from pathlib import Path

import pytest

from medex.vision.analyzer import ImageAnalyzer, ImageValidation, ImagingModality

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def analyzer() -> ImageAnalyzer:
    """Create an ImageAnalyzer instance."""
    return ImageAnalyzer()


@pytest.fixture
def valid_image(tmp_path: Path) -> Path:
    """Create a valid test image file (small PNG-like)."""
    img = tmp_path / "test_xray.png"
    # Write minimal content (not a real image, but we only validate metadata)
    img.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)
    return img


@pytest.fixture
def valid_dicom(tmp_path: Path) -> Path:
    """Create a valid DICOM test file."""
    dcm = tmp_path / "scan.dcm"
    dcm.write_bytes(b"DICM" + b"\x00" * 100)
    return dcm


@pytest.fixture
def oversized_image(tmp_path: Path) -> Path:
    """Create an oversized test file (>50MB)."""
    img = tmp_path / "huge.jpg"
    # Write just over 50MB
    img.write_bytes(b"\xff\xd8" + b"\x00" * (51 * 1024 * 1024))
    return img


# =============================================================================
# ImagingModality Tests
# =============================================================================


class TestImagingModality:
    """Tests for ImagingModality enum."""

    def test_modality_values(self):
        """Test all modality enum values."""
        assert ImagingModality.RADIOGRAPHY.value == "RX"
        assert ImagingModality.CT.value == "TAC"
        assert ImagingModality.MRI.value == "RM"
        assert ImagingModality.ULTRASOUND.value == "US"
        assert ImagingModality.UNKNOWN.value == "UNKNOWN"

    def test_modality_members(self):
        """Test all modality members exist."""
        members = list(ImagingModality)
        assert len(members) == 5
        assert ImagingModality.UNKNOWN in members


# =============================================================================
# ImageValidation Tests
# =============================================================================


class TestImageValidation:
    """Tests for ImageValidation dataclass."""

    def test_create_valid_result(self):
        """Test creating a valid validation result."""
        result = ImageValidation(
            is_valid=True,
            modality=ImagingModality.RADIOGRAPHY,
            confidence=0.95,
            message="Valid radiograph",
        )

        assert result.is_valid is True
        assert result.modality == ImagingModality.RADIOGRAPHY
        assert result.confidence == 0.95
        assert result.message == "Valid radiograph"

    def test_create_invalid_result(self):
        """Test creating an invalid validation result."""
        result = ImageValidation(
            is_valid=False,
            modality=ImagingModality.UNKNOWN,
            confidence=0.0,
            message="File not found",
        )

        assert result.is_valid is False
        assert result.modality == ImagingModality.UNKNOWN
        assert result.confidence == 0.0


# =============================================================================
# ImageAnalyzer Tests
# =============================================================================


class TestImageAnalyzer:
    """Tests for ImageAnalyzer class."""

    def test_analyzer_initialization(self, analyzer: ImageAnalyzer):
        """Test analyzer creates successfully."""
        assert analyzer is not None

    def test_supported_extensions(self, analyzer: ImageAnalyzer):
        """Test supported file extensions."""
        assert ".jpg" in analyzer.SUPPORTED_EXTENSIONS
        assert ".jpeg" in analyzer.SUPPORTED_EXTENSIONS
        assert ".png" in analyzer.SUPPORTED_EXTENSIONS
        assert ".dcm" in analyzer.SUPPORTED_EXTENSIONS
        assert ".dicom" in analyzer.SUPPORTED_EXTENSIONS

    def test_max_file_size(self, analyzer: ImageAnalyzer):
        """Test max file size is 50MB."""
        assert analyzer.MAX_FILE_SIZE == 50 * 1024 * 1024

    def test_validate_valid_png(self, analyzer: ImageAnalyzer, valid_image: Path):
        """Test validation of valid PNG file."""
        result = analyzer.validate_image(str(valid_image))

        assert result.is_valid is True
        assert result.modality == ImagingModality.UNKNOWN  # Detection happens via AI
        assert result.confidence == 0.5

    def test_validate_valid_dicom(self, analyzer: ImageAnalyzer, valid_dicom: Path):
        """Test validation of valid DICOM file."""
        result = analyzer.validate_image(str(valid_dicom))

        assert result.is_valid is True

    def test_validate_file_not_found(self, analyzer: ImageAnalyzer):
        """Test validation with non-existent file."""
        result = analyzer.validate_image("/tmp/definitely_nonexistent_file.png")

        assert result.is_valid is False
        assert result.modality == ImagingModality.UNKNOWN
        assert result.confidence == 0.0
        assert "not found" in result.message.lower()

    def test_validate_unsupported_extension(
        self, analyzer: ImageAnalyzer, tmp_path: Path
    ):
        """Test validation with unsupported file extension."""
        bad_file = tmp_path / "document.pdf"
        bad_file.write_bytes(b"%PDF-1.4" + b"\x00" * 100)

        result = analyzer.validate_image(str(bad_file))

        assert result.is_valid is False
        assert "unsupported" in result.message.lower()

    def test_validate_oversized_file(
        self, analyzer: ImageAnalyzer, oversized_image: Path
    ):
        """Test validation with oversized file."""
        result = analyzer.validate_image(str(oversized_image))

        assert result.is_valid is False
        assert "too large" in result.message.lower()

    def test_validate_jpg_extension(self, analyzer: ImageAnalyzer, tmp_path: Path):
        """Test validation with .jpg extension."""
        jpg = tmp_path / "xray.jpg"
        jpg.write_bytes(b"\xff\xd8\xff" + b"\x00" * 100)

        result = analyzer.validate_image(str(jpg))
        assert result.is_valid is True

    def test_validate_jpeg_extension(self, analyzer: ImageAnalyzer, tmp_path: Path):
        """Test validation with .jpeg extension."""
        jpeg = tmp_path / "scan.jpeg"
        jpeg.write_bytes(b"\xff\xd8\xff" + b"\x00" * 100)

        result = analyzer.validate_image(str(jpeg))
        assert result.is_valid is True

    def test_get_supported_modalities(self):
        """Test getting supported modalities list."""
        modalities = ImageAnalyzer.get_supported_modalities()

        assert isinstance(modalities, list)
        assert "RX" in modalities
        assert "TAC" in modalities
        assert "RM" in modalities
        assert "US" in modalities
        assert "UNKNOWN" not in modalities

    def test_format_rejection_message(self):
        """Test standard rejection message."""
        msg = ImageAnalyzer.format_rejection_message()

        assert isinstance(msg, str)
        assert len(msg) > 0
        assert "RX" in msg or "TAC" in msg  # Contains modality references


# =============================================================================
# Run Tests
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
