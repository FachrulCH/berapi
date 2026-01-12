"""Retry handler with exponential backoff."""

from __future__ import annotations

import random
import time
from dataclasses import dataclass, field
from typing import Callable, TypeVar

from berapi.exceptions.errors import RetryExhaustedError
from berapi.logging.setup import get_logger

T = TypeVar("T")


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""

    max_retries: int = 3
    backoff_factor: float = 0.5
    backoff_max: float = 60.0
    retry_statuses: frozenset[int] = field(
        default_factory=lambda: frozenset({429, 500, 502, 503, 504})
    )
    retry_exceptions: tuple[type[Exception], ...] = field(
        default_factory=lambda: (ConnectionError, TimeoutError)
    )
    jitter: bool = True  # Add randomness to prevent thundering herd


class RetryHandler:
    """Handles retry logic with exponential backoff."""

    def __init__(self, config: RetryConfig | None = None) -> None:
        """Initialize retry handler.

        Args:
            config: Retry configuration. Uses defaults if not provided.
        """
        self.config = config or RetryConfig()
        self._logger = get_logger("berapi.retry")

    def execute(
        self,
        func: Callable[[], T],
        on_retry: Callable[[int, Exception, float], None] | None = None,
    ) -> T:
        """Execute function with retry logic.

        Args:
            func: Function to execute.
            on_retry: Optional callback called before each retry with
                     (attempt_number, exception, delay_seconds).

        Returns:
            Result of the function.

        Raises:
            RetryExhaustedError: If all retry attempts are exhausted.
        """
        last_exception: Exception | None = None

        for attempt in range(self.config.max_retries + 1):
            try:
                return func()
            except self.config.retry_exceptions as e:
                last_exception = e

                if attempt < self.config.max_retries:
                    delay = self._calculate_delay(attempt)

                    self._logger.warning(
                        "retry_attempt",
                        attempt=attempt + 1,
                        max_retries=self.config.max_retries,
                        error_type=type(e).__name__,
                        error_message=str(e),
                        delay_seconds=round(delay, 2),
                    )

                    if on_retry:
                        on_retry(attempt + 1, e, delay)

                    time.sleep(delay)

        if last_exception is not None:
            raise RetryExhaustedError(
                f"All {self.config.max_retries} retry attempts exhausted",
                attempts=self.config.max_retries,
                last_error=last_exception,
            )

        # This should never happen, but satisfies type checker
        raise RuntimeError("Unexpected state in retry handler")

    def should_retry_status(self, status_code: int) -> bool:
        """Check if status code should trigger retry.

        Args:
            status_code: HTTP status code.

        Returns:
            True if the status code should trigger a retry.
        """
        return status_code in self.config.retry_statuses

    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay with exponential backoff and optional jitter.

        Args:
            attempt: Current attempt number (0-indexed).

        Returns:
            Delay in seconds.
        """
        delay = min(
            self.config.backoff_factor * (2**attempt),
            self.config.backoff_max,
        )

        if self.config.jitter:
            # Add 0-100% jitter
            delay *= 0.5 + random.random()

        return delay
