"""
src/utils/retry.py
==================
Exponential backoff retry decorator using 'tenacity'.
Applied to all external API calls to handle transient failures,
rate limits, and network errors gracefully.
"""

import functools
from typing import Callable, Type, Tuple, Any
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
    RetryError,
)
import logging

logger = logging.getLogger(__name__)


def with_retry(
    max_attempts: int = 3,
    min_wait: float = 1.0,
    max_wait: float = 10.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
) -> Callable:
    """
    Decorator factory for exponential backoff retry.

    Args:
        max_attempts: Maximum number of retry attempts.
        min_wait: Minimum seconds between retries.
        max_wait: Maximum seconds between retries.
        exceptions: Tuple of exception types to retry on.

    Usage:
        @with_retry(max_attempts=3, exceptions=(requests.HTTPError,))
        def fetch_data():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @retry(
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
            retry=retry_if_exception_type(exceptions),
            before_sleep=before_sleep_log(logger, logging.WARNING),
            reraise=True,
        )
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return func(*args, **kwargs)
        return wrapper
    return decorator


def with_async_retry(
    max_attempts: int = 3,
    min_wait: float = 1.0,
    max_wait: float = 10.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
) -> Callable:
    """
    Async version of the retry decorator.

    Usage:
        @with_async_retry(max_attempts=3)
        async def fetch_data():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @retry(
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
            retry=retry_if_exception_type(exceptions),
            before_sleep=before_sleep_log(logger, logging.WARNING),
            reraise=True,
        )
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            return await func(*args, **kwargs)
        return wrapper
    return decorator
