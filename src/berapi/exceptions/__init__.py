"""BerAPI custom exceptions."""

from berapi.exceptions.errors import (
    BerAPIError,
    HTTPError,
    RequestError,
    ConnectionError,
    TimeoutError,
    ResponseTimeError,
    AssertionError,
    StatusCodeError,
    HeaderError,
    JsonPathError,
    ValidationError,
    JsonSchemaError,
    OpenAPIError,
    ConfigurationError,
    RetryExhaustedError,
)

__all__ = [
    "BerAPIError",
    "HTTPError",
    "RequestError",
    "ConnectionError",
    "TimeoutError",
    "ResponseTimeError",
    "AssertionError",
    "StatusCodeError",
    "HeaderError",
    "JsonPathError",
    "ValidationError",
    "JsonSchemaError",
    "OpenAPIError",
    "ConfigurationError",
    "RetryExhaustedError",
]
