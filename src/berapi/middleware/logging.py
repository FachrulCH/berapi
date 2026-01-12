"""Logging middleware for structured request/response logging."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import structlog

from berapi.middleware.base import RequestContext, ResponseContext
from berapi.utils.curl import generate_curl

if TYPE_CHECKING:
    pass


class LoggingMiddleware:
    """Structured logging for requests and responses."""

    def __init__(
        self,
        logger: structlog.BoundLogger | None = None,
        log_request_body: bool = True,
        log_response_body: bool = True,
        log_headers: bool = True,
        redact_headers: frozenset[str] | None = None,
        log_curl: bool = True,
        max_body_length: int = 10000,
    ) -> None:
        """Initialize logging middleware.

        Args:
            logger: Custom logger. Defaults to berapi.http logger.
            log_request_body: Whether to log request bodies.
            log_response_body: Whether to log response bodies.
            log_headers: Whether to log headers.
            redact_headers: Header names to redact (case-insensitive).
            log_curl: Whether to log curl commands.
            max_body_length: Maximum body length to log (truncates if longer).
        """
        self._logger = logger or structlog.get_logger("berapi.http")
        self._log_request_body = log_request_body
        self._log_response_body = log_response_body
        self._log_headers = log_headers
        self._redact_headers = redact_headers or frozenset(
            {"authorization", "x-api-key", "cookie", "x-auth-token"}
        )
        self._log_curl = log_curl
        self._max_body_length = max_body_length

    def process_request(self, context: RequestContext) -> RequestContext:
        """Log outgoing request.

        Args:
            context: Request context.

        Returns:
            Unchanged request context.
        """
        log_data: dict[str, Any] = {
            "event": "http_request",
            "method": context.method,
            "url": context.url,
        }

        if self._log_headers and context.headers:
            log_data["headers"] = self._redact(context.headers)

        if self._log_request_body:
            if context.json_body:
                log_data["body"] = context.json_body
            elif context.data:
                body_str = str(context.data)
                if len(body_str) > self._max_body_length:
                    body_str = body_str[: self._max_body_length] + "...[truncated]"
                log_data["body"] = body_str

        if self._log_curl:
            log_data["curl"] = generate_curl(context)

        self._logger.info(**log_data)
        return context

    def process_response(self, context: ResponseContext) -> ResponseContext:
        """Log incoming response.

        Args:
            context: Response context.

        Returns:
            Unchanged response context.
        """
        log_data: dict[str, Any] = {
            "event": "http_response",
            "method": context.request_context.method,
            "url": context.request_context.url,
            "status_code": context.status_code,
            "elapsed_seconds": round(context.elapsed, 3),
        }

        if self._log_headers:
            log_data["headers"] = dict(context.response.headers)

        if self._log_response_body:
            try:
                log_data["body"] = context.response.json()
            except Exception:
                body_text = context.response.text
                if len(body_text) > self._max_body_length:
                    body_text = body_text[: self._max_body_length] + "...[truncated]"
                if body_text:
                    log_data["body_text"] = body_text

        self._logger.info(**log_data)
        return context

    def on_error(self, error: Exception, context: RequestContext) -> None:
        """Log error.

        Args:
            error: The exception that occurred.
            context: Request context.
        """
        self._logger.error(
            "http_error",
            method=context.method,
            url=context.url,
            error_type=type(error).__name__,
            error_message=str(error),
        )

    def _redact(self, headers: dict[str, str]) -> dict[str, str]:
        """Redact sensitive header values.

        Args:
            headers: Headers to redact.

        Returns:
            Headers with sensitive values replaced.
        """
        return {
            k: "[REDACTED]" if k.lower() in self._redact_headers else v
            for k, v in headers.items()
        }
