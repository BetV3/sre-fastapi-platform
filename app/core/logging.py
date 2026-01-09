"""Structured logging configuration."""

import logging
import sys
from contextvars import ContextVar
from typing import Any

import structlog
from structlog.types import EventDict, Processor

from app.config import settings

# Context variable for request ID
request_id_ctx: ContextVar[str | None] = ContextVar("request_id", default=None)


def add_request_id(
    logger: logging.Logger, method_name: str, event_dict: EventDict
) -> EventDict:
    """Add request ID to log event."""
    request_id = request_id_ctx.get()
    if request_id:
        event_dict["request_id"] = request_id
    return event_dict


def add_app_context(
    logger: logging.Logger, method_name: str, event_dict: EventDict
) -> EventDict:
    """Add application context to log event."""
    event_dict["app"] = settings.app_name
    event_dict["environment"] = settings.environment
    return event_dict


def setup_logging() -> None:
    """Configure structured logging for the application."""
    # Shared processors
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.PositionalArgumentsFormatter(),
        add_request_id,
        add_app_context,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if settings.log_format == "json":
        # JSON format for production
        renderer: Processor = structlog.processors.JSONRenderer()
    else:
        # Human-readable format for development
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    structlog.configure(
        processors=shared_processors
        + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Configure standard logging
    log_level = getattr(logging, settings.log_level.upper())

    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(log_level)

    # Quiet noisy loggers
    for logger_name in ["uvicorn.access", "httpcore", "httpx"]:
        logging.getLogger(logger_name).setLevel(logging.WARNING)


def get_logger(name: str | None = None) -> Any:
    """Get a structured logger instance."""
    return structlog.get_logger(name)
