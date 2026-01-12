"""Middleware protocol and context classes."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Protocol, runtime_checkable

import requests


def _utc_now() -> datetime:
    """Get current UTC time (timezone-aware)."""
    return datetime.now(timezone.utc)


@dataclass
class RequestContext:
    """Immutable context passed through middleware for requests."""

    method: str
    url: str
    headers: dict[str, str] = field(default_factory=dict)
    params: dict[str, Any] | None = None
    data: Any | None = None
    json_body: dict[str, Any] | list[Any] | None = None
    timeout: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=_utc_now)

    def with_header(self, key: str, value: str) -> RequestContext:
        """Return new context with added header (immutable pattern).

        Args:
            key: Header name.
            value: Header value.

        Returns:
            New RequestContext with the header added.
        """
        new_headers = {**self.headers, key: value}
        return RequestContext(
            method=self.method,
            url=self.url,
            headers=new_headers,
            params=self.params,
            data=self.data,
            json_body=self.json_body,
            timeout=self.timeout,
            metadata=self.metadata,
            timestamp=self.timestamp,
        )

    def with_metadata(self, key: str, value: Any) -> RequestContext:
        """Return new context with added metadata.

        Args:
            key: Metadata key.
            value: Metadata value.

        Returns:
            New RequestContext with the metadata added.
        """
        new_metadata = {**self.metadata, key: value}
        return RequestContext(
            method=self.method,
            url=self.url,
            headers=self.headers,
            params=self.params,
            data=self.data,
            json_body=self.json_body,
            timeout=self.timeout,
            metadata=new_metadata,
            timestamp=self.timestamp,
        )


@dataclass
class ResponseContext:
    """Context passed through middleware for responses."""

    response: requests.Response
    request_context: RequestContext
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def elapsed(self) -> float:
        """Get response elapsed time in seconds."""
        return self.response.elapsed.total_seconds()

    @property
    def status_code(self) -> int:
        """Get response status code."""
        return self.response.status_code


@runtime_checkable
class Middleware(Protocol):
    """Protocol for request/response middleware.

    Middleware can intercept and modify requests before they are sent,
    and responses after they are received.
    """

    def process_request(self, context: RequestContext) -> RequestContext:
        """Process outgoing request.

        Args:
            context: The request context.

        Returns:
            Modified request context.
        """
        ...

    def process_response(self, context: ResponseContext) -> ResponseContext:
        """Process incoming response.

        Args:
            context: The response context.

        Returns:
            Modified response context.
        """
        ...

    def on_error(self, error: Exception, context: RequestContext) -> None:
        """Handle errors during request/response cycle.

        Args:
            error: The exception that occurred.
            context: The request context.
        """
        ...
