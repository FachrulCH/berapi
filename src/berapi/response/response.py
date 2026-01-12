"""Response wrapper with fluent assertions."""

from __future__ import annotations

import json
from datetime import timedelta
from typing import Any, Self

import requests

from berapi.exceptions.errors import (
    HeaderError,
    JsonPathError,
    JsonSchemaError,
    StatusCodeError,
)
from berapi.utils.json_path import get_by_path, has_path


class Response:
    """Wrapper around requests.Response with fluent assertion methods.

    All assertion methods return `self` for method chaining.
    """

    def __init__(self, response: requests.Response) -> None:
        """Initialize response wrapper.

        Args:
            response: The requests Response object to wrap.
        """
        self._response = response
        self._json_cache: dict[str, Any] | list[Any] | None = None

    # === Properties ===

    @property
    def status_code(self) -> int:
        """Get response status code."""
        return self._response.status_code

    @property
    def headers(self) -> requests.structures.CaseInsensitiveDict[str]:
        """Get response headers."""
        return self._response.headers

    @property
    def text(self) -> str:
        """Get response text."""
        return self._response.text

    @property
    def content(self) -> bytes:
        """Get response content as bytes."""
        return self._response.content

    @property
    def json(self) -> dict[str, Any] | list[Any]:
        """Get response as JSON.

        Returns:
            Parsed JSON response.

        Raises:
            ValueError: If response is not valid JSON.
        """
        if self._json_cache is None:
            try:
                self._json_cache = self._response.json()
            except json.JSONDecodeError as e:
                raise ValueError(f"Response is not valid JSON: {e}") from e
        return self._json_cache

    @property
    def elapsed(self) -> timedelta:
        """Get response elapsed time."""
        return self._response.elapsed

    @property
    def url(self) -> str:
        """Get request URL."""
        return self._response.url

    @property
    def request(self) -> requests.PreparedRequest:
        """Get the prepared request."""
        return self._response.request

    @property
    def raw_response(self) -> requests.Response:
        """Get the underlying requests.Response object."""
        return self._response

    # === Status Code Assertions ===

    def assert_status(self, expected: int) -> Self:
        """Assert exact status code.

        Args:
            expected: Expected status code.

        Returns:
            Self for chaining.

        Raises:
            StatusCodeError: If status code doesn't match.
        """
        if self.status_code != expected:
            raise StatusCodeError(
                f"Expected status code {expected}, got {self.status_code}",
                expected=expected,
                actual=self.status_code,
                url=self.url,
            )
        return self

    def assert_status_range(self, start: int, end: int) -> Self:
        """Assert status code is within range (inclusive).

        Args:
            start: Start of range (inclusive).
            end: End of range (inclusive).

        Returns:
            Self for chaining.

        Raises:
            StatusCodeError: If status code not in range.
        """
        if not (start <= self.status_code <= end):
            raise StatusCodeError(
                f"Expected status code {start}-{end}, got {self.status_code}",
                expected=(start, end),
                actual=self.status_code,
                url=self.url,
            )
        return self

    def assert_2xx(self) -> Self:
        """Assert success status code (200-299).

        Returns:
            Self for chaining.
        """
        return self.assert_status_range(200, 299)

    def assert_3xx(self) -> Self:
        """Assert redirect status code (300-399).

        Returns:
            Self for chaining.
        """
        return self.assert_status_range(300, 399)

    def assert_4xx(self) -> Self:
        """Assert client error status code (400-499).

        Returns:
            Self for chaining.
        """
        return self.assert_status_range(400, 499)

    def assert_5xx(self) -> Self:
        """Assert server error status code (500-599).

        Returns:
            Self for chaining.
        """
        return self.assert_status_range(500, 599)

    # === Header Assertions ===

    def assert_header(self, key: str, expected: str) -> Self:
        """Assert header has specific value.

        Args:
            key: Header name (case-insensitive).
            expected: Expected header value.

        Returns:
            Self for chaining.

        Raises:
            HeaderError: If header doesn't match.
        """
        actual = self.headers.get(key)
        if actual != expected:
            raise HeaderError(
                f"Expected header '{key}' to be '{expected}', got '{actual}'",
                header=key,
                expected=expected,
                actual=actual,
                url=self.url,
            )
        return self

    def assert_header_exists(self, key: str) -> Self:
        """Assert header exists.

        Args:
            key: Header name (case-insensitive).

        Returns:
            Self for chaining.

        Raises:
            HeaderError: If header doesn't exist.
        """
        if key not in self.headers:
            raise HeaderError(
                f"Expected header '{key}' to exist",
                header=key,
                url=self.url,
            )
        return self

    def assert_content_type(self, expected: str) -> Self:
        """Assert Content-Type header contains value.

        Args:
            expected: Expected content type (can be partial match).

        Returns:
            Self for chaining.

        Raises:
            HeaderError: If Content-Type doesn't contain expected value.
        """
        content_type = self.headers.get("Content-Type", "")
        if expected not in content_type:
            raise HeaderError(
                f"Expected Content-Type to contain '{expected}', got '{content_type}'",
                header="Content-Type",
                expected=expected,
                actual=content_type,
                url=self.url,
            )
        return self

    # === Body Assertions ===

    def assert_contains(self, text: str) -> Self:
        """Assert response body contains text.

        Args:
            text: Text to search for.

        Returns:
            Self for chaining.

        Raises:
            AssertionError: If text not found.
        """
        if text not in self.text:
            raise AssertionError(f"Response body does not contain '{text}'")
        return self

    def assert_not_contains(self, text: str) -> Self:
        """Assert response body does not contain text.

        Args:
            text: Text that should not be present.

        Returns:
            Self for chaining.

        Raises:
            AssertionError: If text found.
        """
        if text in self.text:
            raise AssertionError(f"Response body contains '{text}' but should not")
        return self

    # === JSON Assertions ===

    def assert_json_path(self, path: str, expected: Any) -> Self:
        """Assert JSON value at path equals expected.

        Supports dot notation for nested access:
        - "user.name" -> response["user"]["name"]
        - "users.0.name" -> response["users"][0]["name"]

        Args:
            path: Dot-separated path to value.
            expected: Expected value.

        Returns:
            Self for chaining.

        Raises:
            JsonPathError: If value doesn't match.
        """
        actual = get_by_path(self.json, path)
        if actual != expected:
            raise JsonPathError(
                f"Expected '{path}' to be {expected!r}, got {actual!r}",
                path=path,
                expected=expected,
                actual=actual,
                url=self.url,
            )
        return self

    def assert_has_key(self, path: str) -> Self:
        """Assert JSON has key at path.

        Args:
            path: Dot-separated path to check.

        Returns:
            Self for chaining.

        Raises:
            JsonPathError: If key doesn't exist.
        """
        if not has_path(self.json, path):
            raise JsonPathError(
                f"Expected key '{path}' to exist",
                path=path,
                expected="<exists>",
                actual="<missing>",
                url=self.url,
            )
        return self

    def assert_json_not_empty(self, path: str) -> Self:
        """Assert JSON value at path is not empty/None.

        Args:
            path: Dot-separated path to value.

        Returns:
            Self for chaining.

        Raises:
            JsonPathError: If value is empty or None.
        """
        value = get_by_path(self.json, path)
        if value is None or value == "" or value == [] or value == {}:
            raise JsonPathError(
                f"Expected '{path}' to not be empty, got {value!r}",
                path=path,
                expected="<not empty>",
                actual=value,
                url=self.url,
            )
        return self

    def assert_list_not_empty(self) -> Self:
        """Assert response is a non-empty JSON array.

        Returns:
            Self for chaining.

        Raises:
            AssertionError: If not a list or empty.
        """
        data = self.json
        if not isinstance(data, list):
            raise AssertionError(
                f"Expected response to be a list, got {type(data).__name__}"
            )
        if len(data) == 0:
            raise AssertionError("Expected response list to not be empty")
        return self

    def assert_json_in(self, path: str, allowed: list[Any]) -> Self:
        """Assert JSON value at path is one of allowed values.

        Args:
            path: Dot-separated path to value.
            allowed: List of allowed values.

        Returns:
            Self for chaining.

        Raises:
            JsonPathError: If value not in allowed list.
        """
        value = get_by_path(self.json, path)
        if value not in allowed:
            raise JsonPathError(
                f"Expected '{path}' to be one of {allowed!r}, got {value!r}",
                path=path,
                expected=allowed,
                actual=value,
                url=self.url,
            )
        return self

    # === Schema Assertions ===

    def assert_json_schema(self, schema: dict[str, Any] | str) -> Self:
        """Assert response matches JSON Schema.

        Args:
            schema: JSON Schema dict or path to schema file.

        Returns:
            Self for chaining.

        Raises:
            JsonSchemaError: If validation fails.
        """
        from berapi.validation.json_schema import validate_json_schema

        if isinstance(schema, str):
            # Load from file
            with open(schema) as f:
                schema = json.load(f)

        errors = validate_json_schema(self.json, schema)
        if errors:
            raise JsonSchemaError(
                "JSON Schema validation failed",
                errors=errors,
                url=self.url,
            )
        return self

    def assert_json_schema_from_sample(self, sample_path: str) -> Self:
        """Assert response matches schema generated from sample JSON.

        Args:
            sample_path: Path to sample JSON file.

        Returns:
            Self for chaining.

        Raises:
            JsonSchemaError: If validation fails.
        """
        from berapi.validation.json_schema import validate_against_sample

        errors = validate_against_sample(self.json, sample_path)
        if errors:
            raise JsonSchemaError(
                "Schema validation (from sample) failed",
                errors=errors,
                url=self.url,
            )
        return self

    def assert_openapi(self, operation_id: str, spec_path: str | None = None) -> Self:
        """Assert response matches OpenAPI specification.

        Args:
            operation_id: Operation ID in the OpenAPI spec.
            spec_path: Path to OpenAPI spec file. If None, uses configured path.

        Returns:
            Self for chaining.

        Raises:
            OpenAPIError: If validation fails.
        """
        from berapi.validation.openapi import validate_openapi_response

        errors = validate_openapi_response(
            response=self._response,
            operation_id=operation_id,
            spec_path=spec_path,
        )
        if errors:
            from berapi.exceptions.errors import OpenAPIError

            raise OpenAPIError(
                "OpenAPI validation failed",
                errors=errors,
                operation_id=operation_id,
                url=self.url,
            )
        return self

    # === Performance Assertions ===

    def assert_response_time(self, max_seconds: float) -> Self:
        """Assert response time is under threshold.

        Args:
            max_seconds: Maximum allowed response time in seconds.

        Returns:
            Self for chaining.

        Raises:
            AssertionError: If response time exceeds threshold.
        """
        elapsed = self.elapsed.total_seconds()
        if elapsed > max_seconds:
            raise AssertionError(
                f"Response time {elapsed:.3f}s exceeded threshold {max_seconds}s"
            )
        return self

    # === Data Access Methods ===

    def get(self, path: str, default: Any = None) -> Any:
        """Get value from JSON using dot notation.

        Args:
            path: Dot-separated path to value.
            default: Default value if path not found.

        Returns:
            Value at path or default.
        """
        return get_by_path(self.json, path, default)

    def get_all(self, paths: list[str]) -> dict[str, Any]:
        """Get multiple values from JSON.

        Args:
            paths: List of dot-separated paths.

        Returns:
            Dict mapping paths to values.
        """
        return {path: get_by_path(self.json, path) for path in paths}

    def to_dict(self) -> dict[str, Any] | list[Any]:
        """Get response as dictionary/list.

        Returns:
            Parsed JSON response.
        """
        return self.json

    # === Dunder Methods ===

    def __repr__(self) -> str:
        """String representation."""
        return f"<Response [{self.status_code}]>"
