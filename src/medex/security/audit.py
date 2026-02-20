# =============================================================================
# MedeX - Audit Trail System
# =============================================================================
"""
Comprehensive audit trail system for compliance and security.

Features:
- Event logging to multiple backends
- Queryable audit history
- Compliance reporting (HIPAA, GDPR)
- Real-time alerting for high-risk events
"""

from __future__ import annotations

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from medex.security.models import (
    AuditEvent,
    AuditEventType,
    AuditQuery,
    RiskLevel,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Audit Backend Interface
# =============================================================================


class AuditBackend(ABC):
    """Abstract base class for audit backends."""

    @abstractmethod
    async def write(self, event: AuditEvent) -> None:
        """Write audit event."""
        pass

    @abstractmethod
    async def query(self, query: AuditQuery) -> list[AuditEvent]:
        """Query audit events."""
        pass

    @abstractmethod
    async def count(self, query: AuditQuery) -> int:
        """Count matching events."""
        pass

    async def close(self) -> None:
        """Close backend connection."""
        pass


# =============================================================================
# In-Memory Backend (Development)
# =============================================================================


class InMemoryAuditBackend(AuditBackend):
    """In-memory audit backend for development/testing."""

    def __init__(self, max_events: int = 10000) -> None:
        """Initialize in-memory backend."""
        self.max_events = max_events
        self._events: list[AuditEvent] = []
        self._lock = asyncio.Lock()

    async def write(self, event: AuditEvent) -> None:
        """Write event to memory."""
        async with self._lock:
            self._events.append(event)
            # Trim old events
            if len(self._events) > self.max_events:
                self._events = self._events[-self.max_events :]

    async def query(self, query: AuditQuery) -> list[AuditEvent]:
        """Query events from memory."""
        async with self._lock:
            filtered = self._filter_events(query)
            return filtered[query.offset : query.offset + query.limit]

    async def count(self, query: AuditQuery) -> int:
        """Count matching events."""
        async with self._lock:
            return len(self._filter_events(query))

    def _filter_events(self, query: AuditQuery) -> list[AuditEvent]:
        """Filter events based on query."""
        result = self._events.copy()

        if query.user_id:
            result = [e for e in result if e.user_id == query.user_id]

        if query.event_types:
            result = [e for e in result if e.event_type in query.event_types]

        if query.start_date:
            result = [e for e in result if e.timestamp >= query.start_date]

        if query.end_date:
            result = [e for e in result if e.timestamp <= query.end_date]

        if query.resource_type:
            result = [e for e in result if e.resource_type == query.resource_type]

        if query.resource_id:
            result = [e for e in result if e.resource_id == query.resource_id]

        if query.success_only is not None:
            result = [e for e in result if e.success == query.success_only]

        if query.risk_levels:
            result = [e for e in result if e.risk_level in query.risk_levels]

        # Sort by timestamp descending
        result.sort(key=lambda e: e.timestamp, reverse=True)

        return result


# =============================================================================
# File Backend
# =============================================================================


class FileAuditBackend(AuditBackend):
    """File-based audit backend with JSON lines format."""

    def __init__(
        self,
        log_dir: str | Path = "/var/log/medex/audit",
        rotate_daily: bool = True,
    ) -> None:
        """Initialize file backend."""
        self.log_dir = Path(log_dir)
        self.rotate_daily = rotate_daily
        self._lock = asyncio.Lock()

        # Ensure directory exists
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def _get_log_file(self, date: datetime | None = None) -> Path:
        """Get log file path for date."""
        if date is None:
            date = datetime.utcnow()

        if self.rotate_daily:
            filename = f"audit_{date.strftime('%Y%m%d')}.jsonl"
        else:
            filename = "audit.jsonl"

        return self.log_dir / filename

    async def write(self, event: AuditEvent) -> None:
        """Write event to file."""
        log_file = self._get_log_file(event.timestamp)

        async with self._lock:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(event.to_dict()) + "\n")

    async def query(self, query: AuditQuery) -> list[AuditEvent]:
        """Query events from files."""
        events = []

        # Determine date range
        start_date = query.start_date or datetime.utcnow() - timedelta(days=30)
        end_date = query.end_date or datetime.utcnow()

        # Read relevant log files
        current = start_date
        while current <= end_date:
            log_file = self._get_log_file(current)
            if log_file.exists():
                events.extend(await self._read_file(log_file, query))
            current += timedelta(days=1)

        # Sort and paginate
        events.sort(key=lambda e: e.timestamp, reverse=True)
        return events[query.offset : query.offset + query.limit]

    async def _read_file(
        self,
        log_file: Path,
        query: AuditQuery,
    ) -> list[AuditEvent]:
        """Read and filter events from file."""
        events = []

        with open(log_file, encoding="utf-8") as f:
            for line in f:
                try:
                    data = json.loads(line.strip())
                    event = AuditEvent.from_dict(data)

                    if self._matches_query(event, query):
                        events.append(event)
                except (json.JSONDecodeError, KeyError):
                    continue

        return events

    def _matches_query(self, event: AuditEvent, query: AuditQuery) -> bool:
        """Check if event matches query."""
        if query.user_id and event.user_id != query.user_id:
            return False
        if query.event_types and event.event_type not in query.event_types:
            return False
        if query.start_date and event.timestamp < query.start_date:
            return False
        if query.end_date and event.timestamp > query.end_date:
            return False
        if query.resource_type and event.resource_type != query.resource_type:
            return False
        if query.success_only is not None and event.success != query.success_only:
            return False
        if query.risk_levels and event.risk_level not in query.risk_levels:
            return False
        return True

    async def count(self, query: AuditQuery) -> int:
        """Count matching events."""
        events = await self.query(
            AuditQuery(
                user_id=query.user_id,
                event_types=query.event_types,
                start_date=query.start_date,
                end_date=query.end_date,
                resource_type=query.resource_type,
                risk_levels=query.risk_levels,
                limit=100000,
            )
        )
        return len(events)


# =============================================================================
# Configuration
# =============================================================================


@dataclass
class AuditTrailConfig:
    """Configuration for audit trail."""

    # Backend settings
    backend_type: str = "memory"  # memory, file, database
    file_log_dir: str = "/var/log/medex/audit"

    # Event settings
    log_success_events: bool = True
    log_failure_events: bool = True

    # Alerting
    alert_on_risk_levels: list[RiskLevel] = None  # type: ignore
    alert_callback: Callable[[AuditEvent], None] | None = None

    # Retention
    retention_days: int = 365

    def __post_init__(self) -> None:
        """Set defaults."""
        if self.alert_on_risk_levels is None:
            self.alert_on_risk_levels = [RiskLevel.CRITICAL, RiskLevel.HIGH]


# =============================================================================
# Audit Trail Service
# =============================================================================


class AuditTrail:
    """Audit trail service."""

    def __init__(self, config: AuditTrailConfig | None = None) -> None:
        """Initialize audit trail."""
        self.config = config or AuditTrailConfig()
        self._backend = self._create_backend()
        self._alert_callback = self.config.alert_callback
        logger.info(f"Audit trail initialized with {self.config.backend_type} backend")

    def _create_backend(self) -> AuditBackend:
        """Create audit backend based on config."""
        if self.config.backend_type == "file":
            return FileAuditBackend(self.config.file_log_dir)
        return InMemoryAuditBackend()

    async def log(self, event: AuditEvent) -> None:
        """
        Log an audit event.

        Args:
            event: AuditEvent to log
        """
        # Check if we should log
        if event.success and not self.config.log_success_events:
            return
        if not event.success and not self.config.log_failure_events:
            return

        # Write to backend
        await self._backend.write(event)

        # Check for alerts
        if event.risk_level in self.config.alert_on_risk_levels:
            await self._trigger_alert(event)

        logger.debug(f"Audit event logged: {event.event_type.value}")

    async def log_query(
        self,
        user_id: str,
        query_text: str,
        session_id: str | None = None,
        ip_address: str | None = None,
    ) -> AuditEvent:
        """Log a patient/medical query."""
        event = AuditEvent(
            event_type=AuditEventType.PATIENT_QUERY,
            user_id=user_id,
            session_id=session_id,
            ip_address=ip_address,
            resource_type="medical_query",
            action="query",
            metadata={"query_length": len(query_text)},
        )
        await self.log(event)
        return event

    async def log_diagnosis(
        self,
        user_id: str,
        diagnosis: str,
        cie10_code: str | None = None,
        probability: float | None = None,
    ) -> AuditEvent:
        """Log a diagnosis generation."""
        event = AuditEvent(
            event_type=AuditEventType.DIAGNOSIS_GENERATED,
            user_id=user_id,
            resource_type="diagnosis",
            action="generate",
            metadata={
                "diagnosis": diagnosis,
                "cie10_code": cie10_code,
                "probability": probability,
            },
        )
        await self.log(event)
        return event

    async def log_pii_detection(
        self,
        user_id: str | None,
        pii_type: str,
        action: str = "detected",
        was_redacted: bool = True,
    ) -> AuditEvent:
        """Log PII detection event."""
        event = AuditEvent(
            event_type=(
                AuditEventType.PII_DETECTED
                if action == "detected"
                else AuditEventType.PII_REDACTED
            ),
            user_id=user_id,
            resource_type="pii",
            action=action,
            metadata={
                "pii_type": pii_type,
                "was_redacted": was_redacted,
            },
            risk_level=RiskLevel.HIGH,
        )
        await self.log(event)
        return event

    async def log_security_event(
        self,
        event_type: AuditEventType,
        user_id: str | None = None,
        ip_address: str | None = None,
        details: dict[str, Any] | None = None,
        risk_level: RiskLevel = RiskLevel.HIGH,
    ) -> AuditEvent:
        """Log a security event."""
        event = AuditEvent(
            event_type=event_type,
            user_id=user_id,
            ip_address=ip_address,
            resource_type="security",
            action=event_type.value,
            metadata=details or {},
            risk_level=risk_level,
        )
        await self.log(event)
        return event

    async def log_emergency(
        self,
        user_id: str | None,
        triage_level: int,
        chief_complaint: str,
    ) -> AuditEvent:
        """Log emergency detection."""
        event = AuditEvent(
            event_type=AuditEventType.EMERGENCY_DETECTED,
            user_id=user_id,
            resource_type="emergency",
            action="detect",
            metadata={
                "triage_level": triage_level,
                "chief_complaint_length": len(chief_complaint),
            },
            risk_level=RiskLevel.CRITICAL if triage_level <= 2 else RiskLevel.HIGH,
        )
        await self.log(event)
        return event

    async def query(self, query: AuditQuery) -> list[AuditEvent]:
        """Query audit events."""
        return await self._backend.query(query)

    async def count(self, query: AuditQuery) -> int:
        """Count matching events."""
        return await self._backend.count(query)

    async def get_user_history(
        self,
        user_id: str,
        days: int = 30,
        limit: int = 100,
    ) -> list[AuditEvent]:
        """Get audit history for a user."""
        query = AuditQuery(
            user_id=user_id,
            start_date=datetime.utcnow() - timedelta(days=days),
            limit=limit,
        )
        return await self.query(query)

    async def get_security_events(
        self,
        hours: int = 24,
        risk_levels: list[RiskLevel] | None = None,
    ) -> list[AuditEvent]:
        """Get recent security events."""
        if risk_levels is None:
            risk_levels = [RiskLevel.CRITICAL, RiskLevel.HIGH]

        query = AuditQuery(
            start_date=datetime.utcnow() - timedelta(hours=hours),
            risk_levels=risk_levels,
            limit=500,
        )
        return await self.query(query)

    async def generate_compliance_report(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> dict[str, Any]:
        """Generate compliance report for date range."""
        query = AuditQuery(
            start_date=start_date,
            end_date=end_date,
            limit=100000,
        )

        events = await self.query(query)

        # Aggregate statistics
        event_counts = {}
        risk_counts = {level.value: 0 for level in RiskLevel}
        pii_events = 0
        emergency_events = 0

        for event in events:
            # Count by event type
            event_type = event.event_type.value
            event_counts[event_type] = event_counts.get(event_type, 0) + 1

            # Count by risk level
            risk_counts[event.risk_level.value] += 1

            # Special counts
            if event.event_type in {
                AuditEventType.PII_DETECTED,
                AuditEventType.PII_REDACTED,
            }:
                pii_events += 1
            if event.event_type == AuditEventType.EMERGENCY_DETECTED:
                emergency_events += 1

        return {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            },
            "total_events": len(events),
            "events_by_type": event_counts,
            "events_by_risk": risk_counts,
            "pii_events": pii_events,
            "emergency_events": emergency_events,
            "generated_at": datetime.utcnow().isoformat(),
        }

    async def _trigger_alert(self, event: AuditEvent) -> None:
        """Trigger alert for high-risk event."""
        logger.warning(
            f"SECURITY ALERT: {event.event_type.value} - "
            f"Risk: {event.risk_level.value} - "
            f"User: {event.user_id}"
        )

        if self._alert_callback:
            try:
                self._alert_callback(event)
            except Exception as e:
                logger.error(f"Alert callback failed: {e}")

    async def close(self) -> None:
        """Close audit trail."""
        await self._backend.close()


# =============================================================================
# Factory Functions
# =============================================================================


def create_audit_trail(
    config: AuditTrailConfig | None = None,
) -> AuditTrail:
    """Create audit trail service."""
    return AuditTrail(config)
