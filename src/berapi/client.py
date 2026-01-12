"""Main BerAPI client class."""

from __future__ import annotations

from typing import Any, Self

from berapi.config.settings import Settings
from berapi.http.session import HttpSession
from berapi.logging.setup import configure_logging
from berapi.middleware.base import Middleware
from berapi.middleware.chain import MiddlewareChain
from berapi.response.response import Response


class BerAPI:
    """Modern API client for testing with fluent assertions.

    The main entry point for making HTTP requests with built-in
    middleware support, structured logging, and fluent assertions.

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
    """

    def __init__(
        self,
        settings: Settings | None = None,
        middlewares: list[Middleware] | None = None,
    ) -> None:
        """Initialize BerAPI client.

        Args:
            settings: Configuration settings. If None, loads from environment.
            middlewares: List of middleware to use.
        """
        self._settings = settings or Settings.from_env()

        # Configure logging
        configure_logging(self._settings.logging)

        # Setup middleware chain
        self._middleware_chain = MiddlewareChain(middlewares)

        # Create HTTP session
        self._session = HttpSession(
            settings=self._settings,
            middleware_chain=self._middleware_chain,
        )

    @property
    def settings(self) -> Settings:
        """Get current settings."""
        return self._settings

    def add_middleware(self, middleware: Middleware) -> Self:
        """Add middleware to the client.

        Args:
            middleware: Middleware to add.

        Returns:
            Self for chaining.
        """
        self._middleware_chain.add(middleware)
        return self

    def with_settings(self, **overrides: Any) -> BerAPI:
        """Create new client with settings overrides.

        Args:
            **overrides: Settings to override.

        Returns:
            New BerAPI instance with overridden settings.
        """
        new_settings = self._settings.merge(overrides)
        return BerAPI(
            settings=new_settings,
            middlewares=list(self._middleware_chain._middlewares),
        )

    # === HTTP Methods ===

    def get(
        self,
        url: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
        **kwargs: Any,
    ) -> Response:
        """Make a GET request.

        Args:
            url: URL to request (can be relative if base_url is set).
            params: Query parameters.
            headers: Additional headers.
            timeout: Request timeout in seconds.
            **kwargs: Additional arguments passed to requests.

        Returns:
            Response wrapper with fluent assertions.
        """
        response_ctx = self._session.request(
            method="GET",
            url=url,
            params=params,
            headers=headers,
            timeout=timeout,
            **kwargs,
        )
        return Response(response_ctx.response)

    def post(
        self,
        url: str,
        json: dict[str, Any] | list[Any] | None = None,
        data: Any | None = None,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
        **kwargs: Any,
    ) -> Response:
        """Make a POST request.

        Args:
            url: URL to request.
            json: JSON body to send.
            data: Form data to send.
            params: Query parameters.
            headers: Additional headers.
            timeout: Request timeout in seconds.
            **kwargs: Additional arguments passed to requests.

        Returns:
            Response wrapper with fluent assertions.
        """
        response_ctx = self._session.request(
            method="POST",
            url=url,
            json=json,
            data=data,
            params=params,
            headers=headers,
            timeout=timeout,
            **kwargs,
        )
        return Response(response_ctx.response)

    def put(
        self,
        url: str,
        json: dict[str, Any] | list[Any] | None = None,
        data: Any | None = None,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
        **kwargs: Any,
    ) -> Response:
        """Make a PUT request.

        Args:
            url: URL to request.
            json: JSON body to send.
            data: Form data to send.
            params: Query parameters.
            headers: Additional headers.
            timeout: Request timeout in seconds.
            **kwargs: Additional arguments passed to requests.

        Returns:
            Response wrapper with fluent assertions.
        """
        response_ctx = self._session.request(
            method="PUT",
            url=url,
            json=json,
            data=data,
            params=params,
            headers=headers,
            timeout=timeout,
            **kwargs,
        )
        return Response(response_ctx.response)

    def patch(
        self,
        url: str,
        json: dict[str, Any] | list[Any] | None = None,
        data: Any | None = None,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
        **kwargs: Any,
    ) -> Response:
        """Make a PATCH request.

        Args:
            url: URL to request.
            json: JSON body to send.
            data: Form data to send.
            params: Query parameters.
            headers: Additional headers.
            timeout: Request timeout in seconds.
            **kwargs: Additional arguments passed to requests.

        Returns:
            Response wrapper with fluent assertions.
        """
        response_ctx = self._session.request(
            method="PATCH",
            url=url,
            json=json,
            data=data,
            params=params,
            headers=headers,
            timeout=timeout,
            **kwargs,
        )
        return Response(response_ctx.response)

    def delete(
        self,
        url: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
        **kwargs: Any,
    ) -> Response:
        """Make a DELETE request.

        Args:
            url: URL to request.
            params: Query parameters.
            headers: Additional headers.
            timeout: Request timeout in seconds.
            **kwargs: Additional arguments passed to requests.

        Returns:
            Response wrapper with fluent assertions.
        """
        response_ctx = self._session.request(
            method="DELETE",
            url=url,
            params=params,
            headers=headers,
            timeout=timeout,
            **kwargs,
        )
        return Response(response_ctx.response)

    def request(
        self,
        method: str,
        url: str,
        json: dict[str, Any] | list[Any] | None = None,
        data: Any | None = None,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
        **kwargs: Any,
    ) -> Response:
        """Make a request with any HTTP method.

        Args:
            method: HTTP method (GET, POST, PUT, PATCH, DELETE, etc.).
            url: URL to request.
            json: JSON body to send.
            data: Form data to send.
            params: Query parameters.
            headers: Additional headers.
            timeout: Request timeout in seconds.
            **kwargs: Additional arguments passed to requests.

        Returns:
            Response wrapper with fluent assertions.
        """
        response_ctx = self._session.request(
            method=method,
            url=url,
            json=json,
            data=data,
            params=params,
            headers=headers,
            timeout=timeout,
            **kwargs,
        )
        return Response(response_ctx.response)

    # === Context Manager ===

    def close(self) -> None:
        """Close the client session."""
        self._session.close()

    def __enter__(self) -> BerAPI:
        """Enter context manager."""
        return self

    def __exit__(self, *args: Any) -> None:
        """Exit context manager."""
        self.close()

    def __repr__(self) -> str:
        """String representation."""
        base_url = self._settings.base_url or "<none>"
        return f"<BerAPI base_url={base_url}>"
