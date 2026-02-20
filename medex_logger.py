"""
MedeX Clinical Logger - Sistema de Logging Clínico Estructurado
================================================================

Módulo de logging especializado para aplicaciones médicas con:
- Audit trail completo para consultas clínicas
- Timestamps ISO 8601 con timezone
- Anonimización automática de PII (Protected Health Information)
- Niveles de log clínicos (CONSULTA, DIAGNÓSTICO, EMERGENCIA, AUDIT)
- Rotación de logs y retención configurable
- Formato estructurado JSON para análisis posterior

Cumplimiento: HIPAA-aware, GDPR-ready (anonimización)
Autor: MedeX Team
Versión: 1.0.0 Alpha
"""

import logging
import json
import hashlib
import re
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any, List, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
import uuid


# ============================================================================
# ENUMS Y CONSTANTES
# ============================================================================


class LogLevel(Enum):
    """Niveles de log clínicos extendidos."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    CONSULTA = "CONSULTA"  # Consulta médica estándar
    DIAGNOSTICO = "DIAGNOSTICO"  # Resultado de diagnóstico
    ALERTA = "ALERTA"  # Alerta clínica (no emergencia)
    EMERGENCIA = "EMERGENCIA"  # Situación de emergencia detectada
    AUDIT = "AUDIT"  # Eventos de auditoría
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class EventType(Enum):
    """Tipos de eventos clínicos."""

    QUERY_RECEIVED = "query_received"
    QUERY_PROCESSED = "query_processed"
    EMERGENCY_DETECTED = "emergency_detected"
    DIAGNOSIS_GENERATED = "diagnosis_generated"
    RAG_SEARCH = "rag_search"
    MODEL_INFERENCE = "model_inference"
    USER_MODE_CHANGE = "user_mode_change"
    SESSION_START = "session_start"
    SESSION_END = "session_end"
    ERROR_OCCURRED = "error_occurred"
    PII_DETECTED = "pii_detected"
    EXPORT_GENERATED = "export_generated"


# Patrones PII para anonimización
PII_PATTERNS = {
    # Nombres propios (patrones comunes en español)
    "nombre_patron": r"\b(?:Sr\.|Sra\.|Dr\.|Dra\.|Don|Doña)\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)*\b",
    # DNI/NIE español
    "dni_nie": r"\b[0-9]{8}[A-Z]\b|\b[XYZ][0-9]{7}[A-Z]\b",
    # Teléfonos (varios formatos)
    "telefono": r"\b(?:\+?34)?[\s.-]?[6789]\d{2}[\s.-]?\d{3}[\s.-]?\d{3}\b",
    # Email
    "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
    # Direcciones (parcial)
    "direccion": r"\b(?:Calle|C/|Avenida|Av\.|Plaza|Pza\.|Paseo)\s+[A-Za-záéíóúñÁÉÍÓÚÑ\s]+,?\s*(?:n[º°]?\s*)?\d+\b",
    # Números de historia clínica (patrones comunes)
    "historia_clinica": r"\b(?:HC|NHC|Historia)[:\s]*\d{6,10}\b",
    # Fechas de nacimiento explícitas
    "fecha_nacimiento": r"\b(?:nacido|nacida|FN|fecha de nacimiento)[:\s]*\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",
    # Números de seguridad social
    "nss": r"\b\d{2}[/-]?\d{8}[/-]?\d{2}\b",
    # Tarjeta sanitaria
    "tarjeta_sanitaria": r"\b[A-Z]{2,4}\d{10,14}\b",
}


# ============================================================================
# DATA CLASSES
# ============================================================================


@dataclass
class ClinicalLogEntry:
    """Entrada de log clínico estructurada."""

    timestamp: str
    session_id: str
    event_type: str
    level: str
    message: str
    user_mode: Optional[str] = None
    query_hash: Optional[str] = None  # Hash de la consulta (anonimizado)
    is_emergency: bool = False
    response_time_ms: Optional[float] = None
    model_used: Optional[str] = None
    rag_sources_count: Optional[int] = None
    pii_detected: bool = False
    pii_anonymized: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario para serialización."""
        return {k: v for k, v in asdict(self).items() if v is not None}

    def to_json(self) -> str:
        """Serializa a JSON."""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=None)


@dataclass
class AuditTrailEntry:
    """Entrada de auditoría para compliance."""

    timestamp: str
    audit_id: str
    action: str
    actor: str  # "system", "user", "admin"
    resource: str
    details: Dict[str, Any]
    ip_hash: Optional[str] = None  # Hash de IP para privacidad
    success: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ============================================================================
# CLASE PRINCIPAL: MedeXLogger
# ============================================================================


class MedeXLogger:
    """
    Sistema de logging clínico estructurado para MedeX.

    Características:
    - Logging estructurado en JSON
    - Anonimización automática de PII
    - Múltiples handlers (consola, archivo, rotación)
    - Audit trail separado
    - Métricas de sesión

    Uso:
        logger = MedeXLogger()
        logger.log_consulta("dolor de pecho", user_mode="PROFESSIONAL")
        logger.log_emergencia_detectada("IAM", confidence=0.95)
    """

    def __init__(
        self,
        log_dir: str = "logs",
        log_level: str = "INFO",
        enable_console: bool = True,
        enable_file: bool = True,
        enable_audit: bool = True,
        max_file_size_mb: int = 10,
        backup_count: int = 5,
        anonymize_pii: bool = True,
    ):
        """
        Inicializa el logger clínico.

        Args:
            log_dir: Directorio para archivos de log
            log_level: Nivel mínimo de logging
            enable_console: Habilitar output a consola
            enable_file: Habilitar logging a archivo
            enable_audit: Habilitar audit trail separado
            max_file_size_mb: Tamaño máximo de archivo antes de rotar
            backup_count: Número de archivos de backup a mantener
            anonymize_pii: Anonimizar PII automáticamente
        """
        self.log_dir = Path(log_dir)
        self.log_level = log_level
        self.anonymize_pii = anonymize_pii
        self.session_id = self._generate_session_id()
        self.session_start = datetime.now(timezone.utc)
        self.query_count = 0
        self.emergency_count = 0

        # Crear directorio de logs
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Configurar loggers
        self._setup_main_logger(
            enable_console, enable_file, max_file_size_mb, backup_count
        )

        if enable_audit:
            self._setup_audit_logger(max_file_size_mb, backup_count)

        # Log inicio de sesión
        self._log_session_start()

    def _generate_session_id(self) -> str:
        """Genera ID único de sesión."""
        return (
            f"medex_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        )

    def _setup_main_logger(
        self,
        enable_console: bool,
        enable_file: bool,
        max_file_size_mb: int,
        backup_count: int,
    ):
        """Configura el logger principal."""
        self.logger = logging.getLogger("medex_clinical")
        self.logger.setLevel(getattr(logging, self.log_level))
        self.logger.handlers = []  # Limpiar handlers existentes

        # Formatter JSON
        class JSONFormatter(logging.Formatter):
            def format(self, record):
                log_data = {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "level": record.levelname,
                    "message": record.getMessage(),
                }
                if hasattr(record, "extra_data"):
                    log_data.update(record.extra_data)
                return json.dumps(log_data, ensure_ascii=False)

        json_formatter = JSONFormatter()

        # Console handler
        if enable_console:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(
                logging.Formatter(
                    "%(asctime)s | %(levelname)-8s | %(message)s", datefmt="%H:%M:%S"
                )
            )
            self.logger.addHandler(console_handler)

        # File handler con rotación
        if enable_file:
            log_file = (
                self.log_dir / f"medex_clinical_{datetime.now().strftime('%Y%m%d')}.log"
            )
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=max_file_size_mb * 1024 * 1024,
                backupCount=backup_count,
                encoding="utf-8",
            )
            file_handler.setFormatter(json_formatter)
            self.logger.addHandler(file_handler)

    def _setup_audit_logger(self, max_file_size_mb: int, backup_count: int):
        """Configura el logger de auditoría separado."""
        self.audit_logger = logging.getLogger("medex_audit")
        self.audit_logger.setLevel(logging.INFO)
        self.audit_logger.handlers = []

        audit_file = self.log_dir / f"medex_audit_{datetime.now().strftime('%Y%m')}.log"
        audit_handler = RotatingFileHandler(
            audit_file,
            maxBytes=max_file_size_mb * 1024 * 1024,
            backupCount=backup_count * 2,  # Más backups para audit
            encoding="utf-8",
        )

        class AuditFormatter(logging.Formatter):
            def format(self, record):
                if hasattr(record, "audit_entry"):
                    return json.dumps(record.audit_entry, ensure_ascii=False)
                return super().format(record)

        audit_handler.setFormatter(AuditFormatter())
        self.audit_logger.addHandler(audit_handler)

    # ========================================================================
    # ANONIMIZACIÓN PII
    # ========================================================================

    def anonymize_text(self, text: str) -> tuple[str, bool, List[str]]:
        """
        Anonimiza texto eliminando/reemplazando PII.

        Args:
            text: Texto a anonimizar

        Returns:
            Tuple de (texto_anonimizado, pii_detectado, tipos_pii)
        """
        if not self.anonymize_pii or not text:
            return text, False, []

        anonymized = text
        pii_found = []

        for pii_type, pattern in PII_PATTERNS.items():
            matches = re.findall(pattern, anonymized, re.IGNORECASE)
            if matches:
                pii_found.append(pii_type)
                # Reemplazar con placeholder
                anonymized = re.sub(
                    pattern,
                    f"[{pii_type.upper()}_REDACTED]",
                    anonymized,
                    flags=re.IGNORECASE,
                )

        return anonymized, len(pii_found) > 0, pii_found

    def hash_query(self, query: str) -> str:
        """Genera hash SHA-256 de la consulta para tracking anónimo."""
        return hashlib.sha256(query.encode("utf-8")).hexdigest()[:16]

    # ========================================================================
    # MÉTODOS DE LOGGING CLÍNICO
    # ========================================================================

    def log_consulta(
        self,
        query: str,
        user_mode: str = "EDUCATIONAL",
        response_time_ms: Optional[float] = None,
        model_used: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ClinicalLogEntry:
        """
        Registra una consulta médica.

        Args:
            query: Texto de la consulta
            user_mode: EDUCATIONAL o PROFESSIONAL
            response_time_ms: Tiempo de respuesta en ms
            model_used: Modelo LLM utilizado
            metadata: Metadatos adicionales
        """
        self.query_count += 1

        # Anonimizar
        anon_query, pii_detected, pii_types = self.anonymize_text(query)

        entry = ClinicalLogEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            session_id=self.session_id,
            event_type=EventType.QUERY_RECEIVED.value,
            level=LogLevel.CONSULTA.value,
            message=f"Consulta #{self.query_count} recibida",
            user_mode=user_mode,
            query_hash=self.hash_query(query),
            response_time_ms=response_time_ms,
            model_used=model_used,
            pii_detected=pii_detected,
            pii_anonymized=pii_detected,
            metadata={
                "query_length": len(query),
                "query_anonymized": anon_query[:200] + "..."
                if len(anon_query) > 200
                else anon_query,
                "pii_types": pii_types,
                **(metadata or {}),
            },
        )

        self.logger.info(entry.message, extra={"extra_data": entry.to_dict()})

        # Audit si PII detectado
        if pii_detected:
            self._log_audit(
                action="pii_detection",
                resource="query",
                details={"pii_types": pii_types, "anonymized": True},
            )

        return entry

    def log_emergencia_detectada(
        self,
        emergency_type: str,
        confidence: float,
        query: str,
        triggers: List[str],
        recommended_action: str = "Activar protocolo de emergencia",
    ) -> ClinicalLogEntry:
        """
        Registra detección de emergencia médica.

        Args:
            emergency_type: Tipo de emergencia (IAM, ACV, etc.)
            confidence: Nivel de confianza 0-1
            query: Consulta original
            triggers: Palabras/frases que activaron la detección
            recommended_action: Acción recomendada
        """
        self.emergency_count += 1

        entry = ClinicalLogEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            session_id=self.session_id,
            event_type=EventType.EMERGENCY_DETECTED.value,
            level=LogLevel.EMERGENCIA.value,
            message=f"🚨 EMERGENCIA DETECTADA: {emergency_type}",
            is_emergency=True,
            query_hash=self.hash_query(query),
            metadata={
                "emergency_type": emergency_type,
                "confidence": confidence,
                "triggers": triggers,
                "recommended_action": recommended_action,
                "emergency_count_session": self.emergency_count,
            },
        )

        # Log con nivel CRITICAL
        self.logger.critical(entry.message, extra={"extra_data": entry.to_dict()})

        # Audit obligatorio para emergencias
        self._log_audit(
            action="emergency_detection",
            resource="clinical_query",
            details={
                "type": emergency_type,
                "confidence": confidence,
                "triggers": triggers,
            },
        )

        return entry

    def log_diagnostico(
        self,
        diagnosis: str,
        icd10_code: str,
        confidence: float,
        differentials: List[str],
        response_time_ms: float,
        model_used: str,
    ) -> ClinicalLogEntry:
        """
        Registra generación de diagnóstico.

        Args:
            diagnosis: Diagnóstico principal
            icd10_code: Código CIE-10
            confidence: Nivel de confianza
            differentials: Lista de diagnósticos diferenciales
            response_time_ms: Tiempo de respuesta
            model_used: Modelo utilizado
        """
        entry = ClinicalLogEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            session_id=self.session_id,
            event_type=EventType.DIAGNOSIS_GENERATED.value,
            level=LogLevel.DIAGNOSTICO.value,
            message=f"Diagnóstico generado: {diagnosis} ({icd10_code})",
            response_time_ms=response_time_ms,
            model_used=model_used,
            metadata={
                "diagnosis": diagnosis,
                "icd10_code": icd10_code,
                "confidence": confidence,
                "differentials_count": len(differentials),
                "differentials": differentials[:5],  # Top 5
            },
        )

        self.logger.info(entry.message, extra={"extra_data": entry.to_dict()})
        return entry

    def log_rag_search(
        self,
        query: str,
        sources_count: int,
        top_source: Optional[str] = None,
        search_time_ms: float = 0,
    ) -> ClinicalLogEntry:
        """Registra búsqueda RAG."""
        entry = ClinicalLogEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            session_id=self.session_id,
            event_type=EventType.RAG_SEARCH.value,
            level=LogLevel.INFO.value,
            message=f"RAG search: {sources_count} fuentes encontradas",
            query_hash=self.hash_query(query),
            rag_sources_count=sources_count,
            response_time_ms=search_time_ms,
            metadata={"top_source": top_source, "query_preview": query[:100]},
        )

        self.logger.info(entry.message, extra={"extra_data": entry.to_dict()})
        return entry

    def log_error(
        self,
        error_type: str,
        error_message: str,
        stack_trace: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> ClinicalLogEntry:
        """Registra errores del sistema."""
        entry = ClinicalLogEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            session_id=self.session_id,
            event_type=EventType.ERROR_OCCURRED.value,
            level=LogLevel.ERROR.value,
            message=f"Error: {error_type} - {error_message}",
            metadata={
                "error_type": error_type,
                "error_message": error_message,
                "stack_trace": stack_trace[:500] if stack_trace else None,
                **(context or {}),
            },
        )

        self.logger.error(entry.message, extra={"extra_data": entry.to_dict()})

        # Audit para errores
        self._log_audit(
            action="error_logged",
            resource="system",
            details={"error_type": error_type},
            success=False,
        )

        return entry

    # ========================================================================
    # AUDIT TRAIL
    # ========================================================================

    def _log_audit(
        self,
        action: str,
        resource: str,
        details: Dict[str, Any],
        actor: str = "system",
        success: bool = True,
    ):
        """Registra entrada de auditoría."""
        if not hasattr(self, "audit_logger"):
            return

        audit_entry = AuditTrailEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            audit_id=f"audit_{uuid.uuid4().hex[:12]}",
            action=action,
            actor=actor,
            resource=resource,
            details=details,
            success=success,
        )

        record = logging.LogRecord(
            name="medex_audit",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="",
            args=(),
            exc_info=None,
        )
        record.audit_entry = audit_entry.to_dict()
        self.audit_logger.handle(record)

    # ========================================================================
    # SESIÓN Y MÉTRICAS
    # ========================================================================

    def _log_session_start(self):
        """Registra inicio de sesión."""
        entry = ClinicalLogEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            session_id=self.session_id,
            event_type=EventType.SESSION_START.value,
            level=LogLevel.INFO.value,
            message=f"Sesión MedeX iniciada: {self.session_id}",
            metadata={"version": "Alpha", "anonymization_enabled": self.anonymize_pii},
        )
        self.logger.info(entry.message, extra={"extra_data": entry.to_dict()})

        self._log_audit(
            action="session_start",
            resource="medex_session",
            details={"session_id": self.session_id},
        )

    def log_session_end(self) -> Dict[str, Any]:
        """
        Registra fin de sesión con métricas.

        Returns:
            Métricas de la sesión
        """
        duration = (datetime.now(timezone.utc) - self.session_start).total_seconds()

        metrics = {
            "session_id": self.session_id,
            "duration_seconds": round(duration, 2),
            "total_queries": self.query_count,
            "emergencies_detected": self.emergency_count,
            "queries_per_minute": round(self.query_count / (duration / 60), 2)
            if duration > 0
            else 0,
        }

        entry = ClinicalLogEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            session_id=self.session_id,
            event_type=EventType.SESSION_END.value,
            level=LogLevel.INFO.value,
            message=f"Sesión finalizada: {self.query_count} consultas en {round(duration / 60, 1)} min",
            metadata=metrics,
        )

        self.logger.info(entry.message, extra={"extra_data": entry.to_dict()})

        self._log_audit(action="session_end", resource="medex_session", details=metrics)

        return metrics

    def get_session_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de la sesión actual."""
        duration = (datetime.now(timezone.utc) - self.session_start).total_seconds()
        return {
            "session_id": self.session_id,
            "started": self.session_start.isoformat(),
            "duration_seconds": round(duration, 2),
            "queries": self.query_count,
            "emergencies": self.emergency_count,
        }


# ============================================================================
# SINGLETON Y FUNCIONES DE CONVENIENCIA
# ============================================================================

_logger_instance: Optional[MedeXLogger] = None


def get_logger(**kwargs) -> MedeXLogger:
    """
    Obtiene la instancia singleton del logger.

    Uso:
        from medex_logger import get_logger
        logger = get_logger()
        logger.log_consulta("dolor de pecho")
    """
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = MedeXLogger(**kwargs)
    return _logger_instance


def reset_logger():
    """Resetea el logger singleton (útil para tests)."""
    global _logger_instance
    if _logger_instance:
        _logger_instance.log_session_end()
    _logger_instance = None


# ============================================================================
# EJEMPLO DE USO
# ============================================================================

if __name__ == "__main__":
    # Demo del sistema de logging
    print("=" * 60)
    print("🏥 MedeX Clinical Logger - Demo")
    print("=" * 60)

    # Crear logger
    logger = MedeXLogger(
        log_dir="logs_demo", enable_console=True, enable_file=True, anonymize_pii=True
    )

    # Simular consultas
    print("\n📋 Simulando consultas clínicas...\n")

    # Consulta normal
    logger.log_consulta(
        query="Paciente con dolor torácico opresivo de 2 horas de evolución",
        user_mode="PROFESSIONAL",
        response_time_ms=1250,
        model_used="Kimi-K2",
    )

    # Consulta con PII
    logger.log_consulta(
        query="El Sr. Juan García, DNI 12345678A, refiere cefalea intensa",
        user_mode="PROFESSIONAL",
    )

    # Emergencia
    logger.log_emergencia_detectada(
        emergency_type="IAM",
        confidence=0.92,
        query="dolor de pecho que se irradia al brazo izquierdo",
        triggers=["dolor de pecho", "irradia al brazo"],
        recommended_action="Llamar al 112 inmediatamente",
    )

    # Diagnóstico
    logger.log_diagnostico(
        diagnosis="Infarto agudo de miocardio",
        icd10_code="I21.0",
        confidence=0.85,
        differentials=["Angina inestable", "Pericarditis", "Disección aórtica"],
        response_time_ms=2100,
        model_used="Kimi-K2",
    )

    # RAG search
    logger.log_rag_search(
        query="protocolo IAM",
        sources_count=5,
        top_source="Guías ESC 2023",
        search_time_ms=150,
    )

    # Métricas de sesión
    print("\n📊 Estadísticas de sesión:")
    stats = logger.get_session_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")

    # Fin de sesión
    metrics = logger.log_session_end()

    print("\n✅ Demo completada. Revisa el directorio 'logs_demo/'")
    print("=" * 60)
