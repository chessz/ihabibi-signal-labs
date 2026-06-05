"""Logging configuration for signals-lab."""

from __future__ import annotations

import logging
import sys
from typing import Optional

import structlog

from ..config import LoggingSettings


def setup_logging(settings: Optional[LoggingSettings] = None) -> None:
    """Configure structured logging for the application.

    Args:
        settings: Logging configuration. If None, defaults are used.
    """
    if settings is None:
        from ..config import get_settings
        settings = get_settings().logging

    level = getattr(logging, settings.level.upper(), logging.INFO)

    # Shared processors
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
    ]

    if settings.structured:
        # JSON output for production
        structlog.configure(
            processors=[
                *shared_processors,
                structlog.processors.dict_tracebacks,
                structlog.processors.JSONRenderer(),
            ],
            wrapper_class=structlog.make_filtering_bound_logger(level),
            context_class=dict,
            logger_factory=structlog.PrintLoggerFactory(sys.stdout),
            cache_logger_on_first_use=True,
        )
    else:
        # Pretty console output for development
        structlog.configure(
            processors=[
                *shared_processors,
                structlog.dev.ConsoleRenderer(colors=True),
            ],
            wrapper_class=structlog.make_filtering_bound_logger(level),
            context_class=dict,
            logger_factory=structlog.WriteLoggerFactory(sys.stdout),
            cache_logger_on_first_use=True,
        )


def get_logger(name: str) -> structlog.BoundLogger:
    """Get a structured logger for a module.

    Args:
        name: Logger name (typically __name__).
    """
    return structlog.get_logger(name)