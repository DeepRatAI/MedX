"""
Tests para MedeX Clinical Logger
================================

Suite de tests para el sistema de logging clínico estructurado.
"""

import json
import shutil
import tempfile
from pathlib import Path

import pytest

from medex_logger import (
    PII_PATTERNS,
    AuditTrailEntry,
    ClinicalLogEntry,
    EventType,
    LogLevel,
    MedeXLogger,
    get_logger,
    reset_logger,
)

# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def temp_log_dir():
    """Crea directorio temporal para logs de test."""
    temp_dir = tempfile.mkdtemp(prefix="medex_test_logs_")
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def logger(temp_log_dir):
    """Crea logger de test."""
    reset_logger()  # Asegurar estado limpio
    return MedeXLogger(
        log_dir=temp_log_dir,
        enable_console=False,  # Sin output en tests
        enable_file=True,
        enable_audit=True,
        anonymize_pii=True,
    )


@pytest.fixture
def logger_no_anonymize(temp_log_dir):
    """Logger sin anonimización."""
    reset_logger()
    return MedeXLogger(log_dir=temp_log_dir, enable_console=False, anonymize_pii=False)


# ============================================================================
# TESTS: INICIALIZACIÓN
# ============================================================================


class TestLoggerInitialization:
    """Tests de inicialización del logger."""

    def test_logger_creates_log_directory(self, temp_log_dir):
        """Verifica que se crea el directorio de logs."""
        log_path = Path(temp_log_dir) / "new_logs"
        logger = MedeXLogger(log_dir=str(log_path), enable_console=False)
        assert log_path.exists()

    def test_logger_generates_session_id(self, logger):
        """Verifica generación de session_id."""
        assert logger.session_id.startswith("medex_")
        assert len(logger.session_id) > 20

    def test_logger_initializes_counters(self, logger):
        """Verifica inicialización de contadores."""
        assert logger.query_count == 0
        assert logger.emergency_count == 0

    def test_logger_creates_log_files(self, logger, temp_log_dir):
        """Verifica creación de archivos de log."""
        # Log algo para crear archivo
        logger.log_consulta("test query")

        log_files = list(Path(temp_log_dir).glob("*.log"))
        assert len(log_files) >= 1  # Al menos clinical log


# ============================================================================
# TESTS: ANONIMIZACIÓN PII
# ============================================================================


class TestPIIAnonymization:
    """Tests de anonimización de información personal."""

    def test_anonymize_dni(self, logger):
        """Anonimiza DNI español."""
        text = "Paciente con DNI 12345678A presenta fiebre"
        anon, detected, types = logger.anonymize_text(text)

        assert detected
        assert "dni_nie" in types
        assert "12345678A" not in anon
        assert "[DNI_NIE_REDACTED]" in anon

    def test_anonymize_nie(self, logger):
        """Anonimiza NIE español."""
        text = "Extranjero NIE X1234567L"
        anon, detected, types = logger.anonymize_text(text)

        assert detected
        assert "X1234567L" not in anon

    def test_anonymize_phone(self, logger):
        """Anonimiza teléfono."""
        text = "Contacto: 612345678"
        anon, detected, types = logger.anonymize_text(text)

        assert detected
        assert "telefono" in types
        assert "612345678" not in anon

    def test_anonymize_email(self, logger):
        """Anonimiza email."""
        text = "Email: paciente@hospital.es"
        anon, detected, types = logger.anonymize_text(text)

        assert detected
        assert "email" in types
        assert "paciente@hospital.es" not in anon

    def test_anonymize_nombre_patron(self, logger):
        """Anonimiza nombres con prefijo."""
        text = "El Sr. García López refiere dolor"
        anon, detected, types = logger.anonymize_text(text)

        assert detected
        assert "nombre_patron" in types
        assert "García" not in anon

    def test_no_anonymize_medical_terms(self, logger):
        """No anonimiza términos médicos."""
        text = "Diagnóstico: diabetes mellitus tipo 2"
        anon, detected, types = logger.anonymize_text(text)

        assert not detected
        assert anon == text

    def test_multiple_pii_types(self, logger):
        """Detecta múltiples tipos de PII."""
        text = "Sr. Pérez, DNI 12345678A, teléfono 612345678"
        anon, detected, types = logger.anonymize_text(text)

        assert detected
        assert len(types) >= 2

    def test_no_anonymize_when_disabled(self, logger_no_anonymize):
        """No anonimiza cuando está deshabilitado."""
        text = "DNI 12345678A"
        anon, detected, types = logger_no_anonymize.anonymize_text(text)

        assert not detected
        assert anon == text


# ============================================================================
# TESTS: HASH DE QUERIES
# ============================================================================


class TestQueryHashing:
    """Tests de hashing de consultas."""

    def test_hash_consistency(self, logger):
        """Hash es consistente para misma query."""
        query = "dolor de cabeza"
        hash1 = logger.hash_query(query)
        hash2 = logger.hash_query(query)

        assert hash1 == hash2

    def test_hash_different_queries(self, logger):
        """Hash diferente para queries diferentes."""
        hash1 = logger.hash_query("dolor de cabeza")
        hash2 = logger.hash_query("dolor de pecho")

        assert hash1 != hash2

    def test_hash_length(self, logger):
        """Hash tiene longitud correcta (16 chars)."""
        hash_val = logger.hash_query("test query")
        assert len(hash_val) == 16


# ============================================================================
# TESTS: LOG CONSULTA
# ============================================================================


class TestLogConsulta:
    """Tests de logging de consultas."""

    def test_log_consulta_increments_counter(self, logger):
        """Incrementa contador de consultas."""
        logger.log_consulta("consulta 1")
        logger.log_consulta("consulta 2")

        assert logger.query_count == 2

    def test_log_consulta_returns_entry(self, logger):
        """Retorna ClinicalLogEntry."""
        entry = logger.log_consulta("test query", user_mode="PROFESSIONAL")

        assert isinstance(entry, ClinicalLogEntry)
        assert entry.user_mode == "PROFESSIONAL"
        assert entry.event_type == EventType.QUERY_RECEIVED.value

    def test_log_consulta_with_metadata(self, logger):
        """Acepta metadata adicional."""
        entry = logger.log_consulta("test", metadata={"custom_field": "value"})

        assert "custom_field" in entry.metadata

    def test_log_consulta_detects_pii(self, logger):
        """Detecta PII en consultas."""
        entry = logger.log_consulta("Paciente DNI 12345678A con fiebre")

        assert entry.pii_detected
        assert entry.pii_anonymized


# ============================================================================
# TESTS: LOG EMERGENCIA
# ============================================================================


class TestLogEmergencia:
    """Tests de logging de emergencias."""

    def test_log_emergencia_increments_counter(self, logger):
        """Incrementa contador de emergencias."""
        logger.log_emergencia_detectada(
            emergency_type="IAM",
            confidence=0.9,
            query="dolor de pecho",
            triggers=["dolor pecho"],
        )

        assert logger.emergency_count == 1

    def test_log_emergencia_is_emergency_flag(self, logger):
        """Marca flag is_emergency."""
        entry = logger.log_emergencia_detectada(
            emergency_type="ACV",
            confidence=0.95,
            query="debilidad lado izquierdo",
            triggers=["debilidad"],
        )

        assert entry.is_emergency
        assert entry.level == LogLevel.EMERGENCIA.value

    def test_log_emergencia_metadata(self, logger):
        """Incluye metadata de emergencia."""
        entry = logger.log_emergencia_detectada(
            emergency_type="IAM",
            confidence=0.92,
            query="test",
            triggers=["trigger1", "trigger2"],
            recommended_action="Llamar 112",
        )

        assert entry.metadata["emergency_type"] == "IAM"
        assert entry.metadata["confidence"] == 0.92
        assert "trigger1" in entry.metadata["triggers"]


# ============================================================================
# TESTS: LOG DIAGNÓSTICO
# ============================================================================


class TestLogDiagnostico:
    """Tests de logging de diagnósticos."""

    def test_log_diagnostico_structure(self, logger):
        """Estructura correcta de diagnóstico."""
        entry = logger.log_diagnostico(
            diagnosis="Diabetes mellitus",
            icd10_code="E11",
            confidence=0.85,
            differentials=["Hipotiroidismo", "Síndrome metabólico"],
            response_time_ms=1500,
            model_used="Test-Model",
        )

        assert entry.event_type == EventType.DIAGNOSIS_GENERATED.value
        assert entry.model_used == "Test-Model"
        assert entry.metadata["icd10_code"] == "E11"
        assert entry.metadata["confidence"] == 0.85


# ============================================================================
# TESTS: RAG SEARCH
# ============================================================================


class TestLogRAGSearch:
    """Tests de logging de búsquedas RAG."""

    def test_log_rag_search(self, logger):
        """Log de búsqueda RAG."""
        entry = logger.log_rag_search(
            query="protocolo sepsis",
            sources_count=10,
            top_source="Guía Sepsis 2024",
            search_time_ms=150,
        )

        assert entry.rag_sources_count == 10
        assert entry.metadata["top_source"] == "Guía Sepsis 2024"


# ============================================================================
# TESTS: LOG ERROR
# ============================================================================


class TestLogError:
    """Tests de logging de errores."""

    def test_log_error(self, logger):
        """Log de error del sistema."""
        entry = logger.log_error(
            error_type="ModelError",
            error_message="Timeout en inferencia",
            stack_trace="traceback...",
            context={"model": "test"},
        )

        assert entry.level == LogLevel.ERROR.value
        assert entry.metadata["error_type"] == "ModelError"


# ============================================================================
# TESTS: SESIÓN Y MÉTRICAS
# ============================================================================


class TestSessionMetrics:
    """Tests de métricas de sesión."""

    def test_get_session_stats(self, logger):
        """Obtiene estadísticas de sesión."""
        logger.log_consulta("test 1")
        logger.log_consulta("test 2")

        stats = logger.get_session_stats()

        assert stats["queries"] == 2
        assert stats["emergencies"] == 0
        assert "session_id" in stats
        assert "duration_seconds" in stats

    def test_log_session_end(self, logger):
        """Log de fin de sesión."""
        logger.log_consulta("test")
        metrics = logger.log_session_end()

        assert "total_queries" in metrics
        assert metrics["total_queries"] == 1


# ============================================================================
# TESTS: DATA CLASSES
# ============================================================================


class TestDataClasses:
    """Tests de data classes."""

    def test_clinical_log_entry_to_dict(self):
        """Serialización a dict."""
        entry = ClinicalLogEntry(
            timestamp="2024-01-01T00:00:00Z",
            session_id="test_session",
            event_type="test",
            level="INFO",
            message="Test message",
        )

        d = entry.to_dict()
        assert d["timestamp"] == "2024-01-01T00:00:00Z"
        assert d["session_id"] == "test_session"
        # None values should not be in dict
        assert "model_used" not in d or d["model_used"] is None

    def test_clinical_log_entry_to_json(self):
        """Serialización a JSON."""
        entry = ClinicalLogEntry(
            timestamp="2024-01-01T00:00:00Z",
            session_id="test",
            event_type="test",
            level="INFO",
            message="Test",
        )

        json_str = entry.to_json()
        parsed = json.loads(json_str)
        assert parsed["session_id"] == "test"

    def test_audit_trail_entry(self):
        """AuditTrailEntry structure."""
        audit = AuditTrailEntry(
            timestamp="2024-01-01T00:00:00Z",
            audit_id="audit_123",
            action="test_action",
            actor="system",
            resource="test_resource",
            details={"key": "value"},
        )

        d = audit.to_dict()
        assert d["action"] == "test_action"
        assert d["success"] == True


# ============================================================================
# TESTS: ENUMS
# ============================================================================


class TestEnums:
    """Tests de enumeraciones."""

    def test_log_level_values(self):
        """LogLevel tiene valores correctos."""
        assert LogLevel.EMERGENCIA.value == "EMERGENCIA"
        assert LogLevel.CONSULTA.value == "CONSULTA"
        assert LogLevel.DIAGNOSTICO.value == "DIAGNOSTICO"

    def test_event_type_values(self):
        """EventType tiene valores correctos."""
        assert EventType.QUERY_RECEIVED.value == "query_received"
        assert EventType.EMERGENCY_DETECTED.value == "emergency_detected"


# ============================================================================
# TESTS: SINGLETON
# ============================================================================


class TestSingleton:
    """Tests del patrón singleton."""

    def test_get_logger_singleton(self, temp_log_dir):
        """get_logger retorna singleton."""
        reset_logger()

        logger1 = get_logger(log_dir=temp_log_dir, enable_console=False)
        logger2 = get_logger()

        assert logger1 is logger2
        assert logger1.session_id == logger2.session_id

    def test_reset_logger(self, temp_log_dir):
        """reset_logger crea nueva instancia."""
        reset_logger()

        logger1 = get_logger(log_dir=temp_log_dir, enable_console=False)
        session1 = logger1.session_id

        reset_logger()

        logger2 = get_logger(log_dir=temp_log_dir, enable_console=False)
        session2 = logger2.session_id

        assert session1 != session2


# ============================================================================
# TESTS: INTEGRACIÓN
# ============================================================================


class TestIntegration:
    """Tests de integración."""

    def test_full_clinical_workflow(self, logger, temp_log_dir):
        """Workflow clínico completo."""
        # 1. Consulta inicial
        logger.log_consulta(
            "Paciente masculino 55 años con dolor torácico", user_mode="PROFESSIONAL"
        )

        # 2. RAG search
        logger.log_rag_search(
            query="dolor torácico diagnóstico diferencial", sources_count=5
        )

        # 3. Emergencia detectada
        logger.log_emergencia_detectada(
            emergency_type="Posible IAM",
            confidence=0.88,
            query="dolor torácico irradiado",
            triggers=["dolor torácico"],
        )

        # 4. Diagnóstico
        logger.log_diagnostico(
            diagnosis="Síndrome coronario agudo",
            icd10_code="I24.9",
            confidence=0.82,
            differentials=["IAM", "Angina inestable"],
            response_time_ms=2000,
            model_used="Kimi-K2",
        )

        # Verificar métricas
        stats = logger.get_session_stats()
        assert stats["queries"] == 1
        assert stats["emergencies"] == 1

        # Verificar archivos creados
        log_files = list(Path(temp_log_dir).glob("*.log"))
        assert len(log_files) >= 1

    def test_log_file_contains_json(self, logger, temp_log_dir):
        """Archivos de log contienen JSON válido."""
        logger.log_consulta("test query")

        clinical_logs = list(Path(temp_log_dir).glob("medex_clinical_*.log"))
        assert len(clinical_logs) > 0

        with open(clinical_logs[0], encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    # Cada línea debe ser JSON válido
                    parsed = json.loads(line)
                    assert "timestamp" in parsed


# ============================================================================
# TESTS: PII PATTERNS
# ============================================================================


class TestPIIPatterns:
    """Tests específicos de patrones PII."""

    def test_pii_patterns_exist(self):
        """Patrones PII están definidos."""
        expected_patterns = [
            "dni_nie",
            "telefono",
            "email",
            "nombre_patron",
            "historia_clinica",
        ]

        for pattern in expected_patterns:
            assert pattern in PII_PATTERNS

    def test_dni_pattern_variations(self, logger):
        """Patrón DNI detecta variaciones."""
        test_cases = [
            "12345678A",
            "87654321Z",
        ]

        for dni in test_cases:
            text = f"DNI: {dni}"
            _, detected, _ = logger.anonymize_text(text)
            assert detected, f"No detectó DNI: {dni}"

    def test_phone_pattern_variations(self, logger):
        """Patrón teléfono detecta variaciones."""
        test_cases = [
            "612345678",
            "912345678",
            "+34612345678",
        ]

        for phone in test_cases:
            text = f"Tel: {phone}"
            _, detected, types = logger.anonymize_text(text)
            assert detected, f"No detectó teléfono: {phone}"
