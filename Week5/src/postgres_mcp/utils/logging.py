"""
Structured logging setup using structlog.

Args:
----------
    None

Returns:
----------
    None

Raises:
----------
    None
"""

from __future__ import annotations

import logging
from typing import Any

import structlog


def configure_logging(level: str = "INFO") -> None:
    """
    Configure structlog with JSON output.

    Args:
    ----------
        level: Log level string.

    Returns:
    ----------
        None

    Raises:
    ----------
        None
    """

    logging.basicConfig(format="%(message)s", level=getattr(logging, level.upper(), logging.INFO))
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, level.upper(), logging.INFO)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(**context: Any) -> structlog.BoundLogger:
    """
    Get a structured logger with optional context.

    Args:
    ----------
        **context: Context values to bind to the logger.

    Returns:
    ----------
        Structlog bound logger instance.

    Raises:
    ----------
        None
    """

    return structlog.get_logger().bind(**context)
