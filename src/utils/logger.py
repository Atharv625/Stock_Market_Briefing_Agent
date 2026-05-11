"""
src/utils/logger.py
===================
Structured JSON logging for CloudWatch compatibility.
Uses 'structlog' for consistent, machine-readable log output.
"""

import logging
import sys
from typing import Any
import structlog
from src.utils.config import get_settings


def setup_logging() -> None:
    """Configure structlog with JSON rendering for production."""
    settings = get_settings()
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.BoundLogger,
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=True,
    )

    # Also configure stdlib logging for third-party libraries
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )


def get_logger(name: str) -> structlog.BoundLogger:
    """
    Get a named logger instance.

    Usage:
        logger = get_logger(__name__)
        logger.info("event", key="value")
    """
    return structlog.get_logger(name)


class AgentLogger:
    """
    Convenience wrapper that attaches agent context to all log entries.
    Ensures every log line contains the agent name for easy filtering.
    """

    def __init__(self, agent_name: str) -> None:
        self._logger = get_logger(agent_name).bind(agent=agent_name)

    def info(self, event: str, **kwargs: Any) -> None:
        self._logger.info(event, **kwargs)

    def warning(self, event: str, **kwargs: Any) -> None:
        self._logger.warning(event, **kwargs)

    def error(self, event: str, **kwargs: Any) -> None:
        self._logger.error(event, **kwargs)

    def debug(self, event: str, **kwargs: Any) -> None:
        self._logger.debug(event, **kwargs)

    def exception(self, event: str, **kwargs: Any) -> None:
        self._logger.exception(event, **kwargs)
