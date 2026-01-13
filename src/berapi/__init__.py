"""BerAPI - Modern API Testing Library for Python.

A modern, scalable API testing library with middleware support,
structured logging, and fluent assertions.

Example:
    >>> from berapi import BerAPI, Settings
    >>> from berapi.middleware import LoggingMiddleware
    >>>
    >>> api = BerAPI(
    ...     Settings(base_url="https://api.example.com"),
    ...     middlewares=[LoggingMiddleware()]
    ... )
    >>>
    >>> response = (
    ...     api.get("/users/1")
    ...     .assert_2xx()
    ...     .assert_json_path("name", "John")
    ... )
    >>> user = response.to_dict()
"""

from berapi.client import BerAPI
from berapi.config.settings import Settings, LoggingSettings, RetrySettings
from berapi.response.response import Response

# Re-export commonly used middleware
from berapi.middleware import (
    Middleware,
    RequestContext,
    ResponseContext,
    MiddlewareChain,
    LoggingMiddleware,
    BearerAuthMiddleware,
    ApiKeyMiddleware,
)

# Re-export exceptions
from berapi.exceptions import (
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

__version__ = "2.2.0"

__all__ = [
    # Main client
    "BerAPI",
    # Configuration
    "Settings",
    "LoggingSettings",
    "RetrySettings",
    # Response
    "Response",
    # Middleware
    "Middleware",
    "RequestContext",
    "ResponseContext",
    "MiddlewareChain",
    "LoggingMiddleware",
    "BearerAuthMiddleware",
    "ApiKeyMiddleware",
    # Exceptions
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
    # Version
    "__version__",
]
