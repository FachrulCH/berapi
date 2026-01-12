"""HTTP session management."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from urllib.parse import urljoin

import requests

from berapi.exceptions.errors import (
    ConnectionError as BerAPIConnectionError,
    ResponseTimeError,
    TimeoutError as BerAPITimeoutError,
)
from berapi.http.retry import RetryConfig, RetryHandler
from berapi.middleware.base import RequestContext, ResponseContext
from berapi.middleware.chain import MiddlewareChain

if TYPE_CHECKING:
    from berapi.config.settings import Settings


class HttpSession:
    """HTTP session with middleware and retry support."""

    def __init__(
        self,
        settings: Settings,
        middleware_chain: MiddlewareChain | None = None,
    ) -> None:
        """Initialize HTTP session.

        Args:
            settings: Configuration settings.
            middleware_chain: Middleware chain to use.
        """
        self._settings = settings
        self._session = requests.Session()
        self._middleware_chain = middleware_chain if middleware_chain is not None else MiddlewareChain()

        # Configure session
        self._session.headers.update(settings.headers)
        self._session.verify = settings.verify_ssl

        # Setup retry handler if enabled
        self._retry_handler: RetryHandler | None = None
        if settings.retry.enabled:
            self._retry_handler = RetryHandler(
                RetryConfig(
                    max_retries=settings.retry.max_retries,
                    backoff_factor=settings.retry.backoff_factor,
                    backoff_max=settings.retry.backoff_max,
                    retry_statuses=settings.retry.retry_statuses,
                    jitter=settings.retry.jitter,
                )
            )

    def request(
        self,
        method: str,
        url: str,
        params: dict[str, Any] | None = None,
        data: Any | None = None,
        json: dict[str, Any] | list[Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
        **kwargs: Any,
    ) -> ResponseContext:
        """Make an HTTP request.

        Args:
            method: HTTP method (GET, POST, etc.).
            url: URL to request. Can be relative if base_url is set.
            params: Query parameters.
            data: Request body data.
            json: JSON request body.
            headers: Additional headers.
            timeout: Request timeout in seconds.
            **kwargs: Additional arguments passed to requests.

        Returns:
            ResponseContext with the response.

        Raises:
            BerAPIConnectionError: If connection fails.
            BerAPITimeoutError: If request times out.
            ResponseTimeError: If response time exceeds threshold.
        """
        # Resolve URL
        full_url = self._resolve_url(url)

        # Build request context
        request_headers = {**self._session.headers, **(headers or {})}
        request_timeout = timeout or self._settings.timeout

        context = RequestContext(
            method=method.upper(),
            url=full_url,
            headers=request_headers,
            params=params,
            data=data,
            json_body=json,
            timeout=request_timeout,
        )

        # Execute middleware for request
        context = self._middleware_chain.execute_request(context)

        # Define the actual request function
        def make_request() -> requests.Response:
            try:
                response = self._session.request(
                    method=context.method,
                    url=context.url,
                    params=context.params,
                    data=context.data,
                    json=context.json_body,
                    headers=context.headers,
                    timeout=context.timeout,
                    **kwargs,
                )
                return response
            except requests.exceptions.ConnectionError as e:
                raise BerAPIConnectionError(
                    f"Failed to connect to {context.url}",
                    url=context.url,
                ) from e
            except requests.exceptions.Timeout as e:
                raise BerAPITimeoutError(
                    f"Request to {context.url} timed out",
                    timeout=context.timeout or self._settings.timeout,
                    url=context.url,
                ) from e

        # Execute with retry if enabled
        try:
            if self._retry_handler:
                response = self._retry_handler.execute(make_request)
            else:
                response = make_request()
        except Exception as e:
            self._middleware_chain.handle_error(e, context)
            raise

        # Check response time threshold
        if self._settings.max_response_time is not None:
            elapsed = response.elapsed.total_seconds()
            if elapsed > self._settings.max_response_time:
                error = ResponseTimeError(
                    f"Response time {elapsed:.2f}s exceeded threshold "
                    f"{self._settings.max_response_time}s",
                    elapsed=elapsed,
                    threshold=self._settings.max_response_time,
                    url=context.url,
                )
                self._middleware_chain.handle_error(error, context)
                raise error

        # Build response context
        response_context = ResponseContext(
            response=response,
            request_context=context,
        )

        # Execute middleware for response
        response_context = self._middleware_chain.execute_response(response_context)

        return response_context

    def _resolve_url(self, url: str) -> str:
        """Resolve URL, joining with base_url if relative.

        Args:
            url: URL to resolve.

        Returns:
            Resolved URL.
        """
        if url.startswith(("http://", "https://")):
            return url

        if self._settings.base_url:
            return urljoin(self._settings.base_url, url)

        return url

    def close(self) -> None:
        """Close the session."""
        self._session.close()

    def __enter__(self) -> HttpSession:
        """Enter context manager."""
        return self

    def __exit__(self, *args: Any) -> None:
        """Exit context manager."""
        self.close()
