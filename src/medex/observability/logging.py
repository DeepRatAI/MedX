# =============================================================================
# MedeX - Structured Logging
# =============================================================================
"""
Structured logging system.

Provides:
- JSON-formatted logs
- Correlation IDs (trace_id, span_id)
- Context propagation
- Log aggregation support
"""

from __future__ import annotations

import contextvars
import json
import logging
import sys
import traceback
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from medex.observability.models import LogLevel

# =============================================================================
# Context Variables for Correlation
# =============================================================================

_trace_id: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "trace_id", default=None
)
_span_id: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "span_id", default=None
)
_user_id: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "user_id", default=None
)
_session_id: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "session_id", default=None
)
_request_id: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "request_id", default=None
)


def set_correlation_context(
    trace_id: str | None = None,
    span_id: str | None = None,
    user_id: str | None = None,
    session_id: str | None = None,
    request_id: str | None = None,
) -> None:
    """Set correlation context for current async context."""
    if trace_id:
        _trace_id.set(trace_id)
    if span_id:
        _span_id.set(span_id)
    if user_id:
        _user_id.set(user_id)
    if session_id:
        _session_id.set(session_id)
    if request_id:
        _request_id.set(request_id)


def get_correlation_context() -> dict[str, str | None]:
    """Get current correlation context."""
    return {
        "trace_id": _trace_id.get(),
        "span_id": _span_id.get(),
        "user_id": _user_id.get(),
        "session_id": _session_id.get(),
        "request_id": _request_id.get(),
    }


def clear_correlation_context() -> None:
    """Clear correlation context."""
    _trace_id.set(None)
    _span_id.set(None)
    _user_id.set(None)
    _session_id.set(None)
    _request_id.set(None)


# =============================================================================
# JSON Formatter
# =============================================================================


class JSONFormatter(logging.Formatter):
    """JSON log formatter."""

    def __init__(
        self,
        include_timestamp: bool = True,
        include_extra: bool = True,
        pretty: bool = False,
    ) -> None:
        """Initialize formatter."""
        super().__init__()
        self.include_timestamp = include_timestamp
        self.include_extra = include_extra
        self.pretty = pretty

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        # Base fields
        log_data: dict[str, Any] = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if self.include_timestamp:
            log_data["timestamp"] = datetime.fromtimestamp(record.created).isoformat()

        # Location info
        log_data["location"] = {
            "file": record.pathname,
            "line": record.lineno,
            "function": record.funcName,
        }

        # Correlation context
        ctx = get_correlation_context()
        for key, value in ctx.items():
            if value:
                log_data[key] = value

        # Exception info
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": traceback.format_exception(*record.exc_info),
            }

        # Extra fields
        if self.include_extra and hasattr(record, "extra_fields"):
            log_data["extra"] = record.extra_fields

        # Format
        if self.pretty:
            return json.dumps(log_data, indent=2, default=str, ensure_ascii=False)
        return json.dumps(log_data, default=str, ensure_ascii=False)


class TextFormatter(logging.Formatter):
    """Human-readable text formatter with colors."""

    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"

    def __init__(self, use_colors: bool = True) -> None:
        """Initialize formatter."""
        super().__init__()
        self.use_colors = use_colors

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as colored text."""
        timestamp = datetime.fromtimestamp(record.created).strftime(
            "%Y-%m-%d %H:%M:%S.%f"
        )[:-3]

        level = record.levelname
        if self.use_colors:
            color = self.COLORS.get(level, "")
            level = f"{color}{level:8}{self.RESET}"
        else:
            level = f"{level:8}"

        message = record.getMessage()

        # Add correlation info
        ctx = get_correlation_context()
        correlation = ""
        if ctx.get("trace_id"):
            correlation = f" [trace={ctx['trace_id'][:8]}...]"
        if ctx.get("request_id"):
            correlation += f" [req={ctx['request_id'][:8]}...]"

        base = f"{timestamp} | {level} | {record.name}{correlation} | {message}"

        # Add exception
        if record.exc_info:
            base += "\n" + "".join(traceback.format_exception(*record.exc_info))

        return base


# =============================================================================
# Logging Configuration
# =============================================================================


@dataclass
class LoggingConfig:
    """Configuration for logging."""

    level: LogLevel = LogLevel.INFO
    format: str = "json"  # json or text

    # Output
    log_to_console: bool = True
    log_to_file: bool = False
    file_path: str = "/var/log/medex/app.log"

    # Options
    use_colors: bool = True
    pretty_json: bool = False
    include_location: bool = True

    # Filters
    exclude_loggers: list[str] = field(
        default_factory=lambda: [
            "httpx",
            "httpcore",
            "urllib3",
            "asyncio",
        ]
    )


def configure_logging(config: LoggingConfig | None = None) -> None:
    """Configure logging for the application."""
    config = config or LoggingConfig()

    # Get root logger
    root = logging.getLogger()
    root.setLevel(getattr(logging, config.level.value))

    # Remove existing handlers
    root.handlers.clear()

    # Create formatter
    if config.format == "json":
        formatter = JSONFormatter(pretty=config.pretty_json)
    else:
        formatter = TextFormatter(use_colors=config.use_colors)

    # Console handler
    if config.log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        root.addHandler(console_handler)

    # File handler
    if config.log_to_file:
        try:
            from pathlib import Path

            Path(config.file_path).parent.mkdir(parents=True, exist_ok=True)

            file_handler = logging.FileHandler(config.file_path)
            file_handler.setFormatter(JSONFormatter())  # Always JSON for files
            root.addHandler(file_handler)
        except Exception as e:
            root.warning(f"Could not create file handler: {e}")

    # Reduce noise from third-party libraries
    for logger_name in config.exclude_loggers:
        logging.getLogger(logger_name).setLevel(logging.WARNING)


# =============================================================================
# Structured Logger
# =============================================================================


class StructuredLogger:
    """Logger with structured logging support."""

    def __init__(self, name: str) -> None:
        """Initialize logger."""
        self._logger = logging.getLogger(name)

    def _log(
        self,
        level: int,
        message: str,
        extra: dict[str, Any] | None = None,
        exc_info: bool = False,
    ) -> None:
        """Log with extra fields."""
        record = self._logger.makeRecord(
            self._logger.name,
            level,
            "(unknown file)",
            0,
            message,
            (),
            None,
        )

        if extra:
            record.extra_fields = extra

        if exc_info:
            record.exc_info = sys.exc_info()

        self._logger.handle(record)

    def debug(self, message: str, **kwargs: Any) -> None:
        """Log debug message."""
        self._log(logging.DEBUG, message, kwargs if kwargs else None)

    def info(self, message: str, **kwargs: Any) -> None:
        """Log info message."""
        self._log(logging.INFO, message, kwargs if kwargs else None)

    def warning(self, message: str, **kwargs: Any) -> None:
        """Log warning message."""
        self._log(logging.WARNING, message, kwargs if kwargs else None)

    def error(self, message: str, exc_info: bool = False, **kwargs: Any) -> None:
        """Log error message."""
        self._log(logging.ERROR, message, kwargs if kwargs else None, exc_info)

    def critical(self, message: str, exc_info: bool = False, **kwargs: Any) -> None:
        """Log critical message."""
        self._log(logging.CRITICAL, message, kwargs if kwargs else None, exc_info)

    def exception(self, message: str, **kwargs: Any) -> None:
        """Log exception with traceback."""
        self.error(message, exc_info=True, **kwargs)

    # Context-aware logging
    def log_request(
        self,
        method: str,
        path: str,
        status: int,
        duration_ms: float,
        **kwargs: Any,
    ) -> None:
        """Log HTTP request."""
        self.info(
            f"{method} {path} -> {status}",
            method=method,
            path=path,
            status=status,
            duration_ms=duration_ms,
            **kwargs,
        )

    def log_llm_call(
        self,
        provider: str,
        model: str,
        tokens_in: int,
        tokens_out: int,
        duration_ms: float,
        **kwargs: Any,
    ) -> None:
        """Log LLM API call."""
        self.info(
            f"LLM call: {provider}/{model}",
            provider=provider,
            model=model,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            duration_ms=duration_ms,
            **kwargs,
        )

    def log_security_event(
        self,
        event_type: str,
        severity: str,
        details: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        """Log security event."""
        level = logging.WARNING if severity in ["HIGH", "CRITICAL"] else logging.INFO
        self._log(
            level,
            f"Security event: {event_type}",
            {
                "event_type": event_type,
                "severity": severity,
                "details": details,
                **kwargs,
            },
        )


def get_logger(name: str) -> StructuredLogger:
    """Get structured logger."""
    return StructuredLogger(name)
