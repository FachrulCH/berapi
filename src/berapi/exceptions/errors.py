"""Custom exception hierarchy for BerAPI."""

from typing import Any


class BerAPIError(Exception):
    """Base exception for all BerAPI errors."""

    def __init__(self, message: str, **context: Any) -> None:
        super().__init__(message)
        self.message = message
        self.context = context

    def __str__(self) -> str:
        if self.context:
            ctx = ", ".join(f"{k}={v!r}" for k, v in self.context.items())
            return f"{self.message} ({ctx})"
        return self.message


# === HTTP Errors ===


class HTTPError(BerAPIError):
    """Base class for HTTP-related errors."""

    pass


class RequestError(HTTPError):
    """Error occurred while making the request."""

    pass


class ConnectionError(RequestError):
    """Failed to connect to the server."""

    pass


class TimeoutError(RequestError):
    """Request timed out."""

    def __init__(self, message: str, timeout: float, **context: Any) -> None:
        super().__init__(message, timeout=timeout, **context)
        self.timeout = timeout


class ResponseTimeError(HTTPError):
    """Response took longer than allowed threshold."""

    def __init__(
        self,
        message: str,
        elapsed: float,
        threshold: float,
        **context: Any,
    ) -> None:
        super().__init__(message, elapsed=elapsed, threshold=threshold, **context)
        self.elapsed = elapsed
        self.threshold = threshold


# === Assertion Errors ===


class AssertionError(BerAPIError):
    """Base class for assertion failures."""

    pass


class StatusCodeError(AssertionError):
    """Status code assertion failed."""

    def __init__(
        self,
        message: str,
        expected: int | tuple[int, int],
        actual: int,
        **context: Any,
    ) -> None:
        super().__init__(message, expected=expected, actual=actual, **context)
        self.expected = expected
        self.actual = actual


class HeaderError(AssertionError):
    """Header assertion failed."""

    def __init__(
        self,
        message: str,
        header: str,
        expected: str | None = None,
        actual: str | None = None,
        **context: Any,
    ) -> None:
        super().__init__(
            message, header=header, expected=expected, actual=actual, **context
        )
        self.header = header
        self.expected = expected
        self.actual = actual


class JsonPathError(AssertionError):
    """JSON path assertion failed."""

    def __init__(
        self,
        message: str,
        path: str,
        expected: Any,
        actual: Any,
        **context: Any,
    ) -> None:
        super().__init__(message, path=path, expected=expected, actual=actual, **context)
        self.path = path
        self.expected = expected
        self.actual = actual


# === Validation Errors ===


class ValidationError(BerAPIError):
    """Base class for validation errors."""

    def __init__(self, message: str, errors: list[str], **context: Any) -> None:
        super().__init__(message, **context)
        self.errors = errors

    def __str__(self) -> str:
        if self.errors:
            errors_str = "\n  - ".join(self.errors)
            return f"{self.message}:\n  - {errors_str}"
        return self.message


class JsonSchemaError(ValidationError):
    """JSON Schema validation failed."""

    pass


class OpenAPIError(ValidationError):
    """OpenAPI validation failed."""

    def __init__(
        self,
        message: str,
        errors: list[str],
        operation_id: str | None = None,
        **context: Any,
    ) -> None:
        super().__init__(message, errors, operation_id=operation_id, **context)
        self.operation_id = operation_id


# === Configuration Errors ===


class ConfigurationError(BerAPIError):
    """Invalid configuration."""

    pass


# === Retry Errors ===


class RetryExhaustedError(HTTPError):
    """All retry attempts exhausted."""

    def __init__(
        self,
        message: str,
        attempts: int,
        last_error: Exception,
        **context: Any,
    ) -> None:
        super().__init__(message, attempts=attempts, **context)
        self.attempts = attempts
        self.last_error = last_error
        self.__cause__ = last_error
