"""Structlog configuration for BerAPI."""

from __future__ import annotations

import logging
import sys
from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    from berapi.config.settings import LoggingSettings

_configured = False


def configure_logging(settings: LoggingSettings | None = None) -> None:
    """Configure structlog with the given settings.

    Args:
        settings: Logging settings. If None, uses defaults.
    """
    global _configured

    if _configured:
        return

    if settings is None:
        from berapi.config.settings import LoggingSettings

        settings = LoggingSettings()

    # Set up standard logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.level.upper(), logging.INFO),
    )

    # Common processors
    processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if settings.format == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(
            structlog.dev.ConsoleRenderer(
                colors=True,
                exception_formatter=structlog.dev.plain_traceback,
            )
        )

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, settings.level.upper(), logging.INFO)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    _configured = True


def get_logger(name: str | None = None) -> structlog.BoundLogger:
    """Get a configured logger instance.

    Args:
        name: Logger name. Defaults to 'berapi'.

    Returns:
        Configured structlog BoundLogger.
    """
    if not _configured:
        configure_logging()

    return structlog.get_logger(name or "berapi")
