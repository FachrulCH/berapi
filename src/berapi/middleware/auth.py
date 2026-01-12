"""Authentication middleware implementations."""

from __future__ import annotations

from typing import Callable

from berapi.middleware.base import RequestContext, ResponseContext


class BearerAuthMiddleware:
    """Adds Bearer token authentication to requests."""

    def __init__(self, token: str | Callable[[], str]) -> None:
        """Initialize Bearer auth middleware.

        Args:
            token: Static token string or callable that returns token
                   (for dynamic/refreshable tokens).
        """
        self._token = token

    def process_request(self, context: RequestContext) -> RequestContext:
        """Add Authorization header with Bearer token.

        Args:
            context: Request context.

        Returns:
            Context with Authorization header added.
        """
        token = self._token() if callable(self._token) else self._token
        return context.with_header("Authorization", f"Bearer {token}")

    def process_response(self, context: ResponseContext) -> ResponseContext:
        """Pass through response unchanged.

        Args:
            context: Response context.

        Returns:
            Unchanged response context.
        """
        return context

    def on_error(self, error: Exception, context: RequestContext) -> None:
        """No-op error handler.

        Args:
            error: The exception that occurred.
            context: Request context.
        """
        pass


class ApiKeyMiddleware:
    """Adds API key authentication to requests."""

    def __init__(
        self,
        api_key: str | Callable[[], str],
        header_name: str = "X-API-Key",
        prefix: str = "",
    ) -> None:
        """Initialize API key middleware.

        Args:
            api_key: API key string or callable that returns the key.
            header_name: Name of the header to use.
            prefix: Optional prefix for the key value.
        """
        self._api_key = api_key
        self._header_name = header_name
        self._prefix = prefix

    def process_request(self, context: RequestContext) -> RequestContext:
        """Add API key header.

        Args:
            context: Request context.

        Returns:
            Context with API key header added.
        """
        key = self._api_key() if callable(self._api_key) else self._api_key
        value = f"{self._prefix}{key}" if self._prefix else key
        return context.with_header(self._header_name, value)

    def process_response(self, context: ResponseContext) -> ResponseContext:
        """Pass through response unchanged.

        Args:
            context: Response context.

        Returns:
            Unchanged response context.
        """
        return context

    def on_error(self, error: Exception, context: RequestContext) -> None:
        """No-op error handler.

        Args:
            error: The exception that occurred.
            context: Request context.
        """
        pass


class BasicAuthMiddleware:
    """Adds Basic authentication to requests."""

    def __init__(self, username: str, password: str) -> None:
        """Initialize Basic auth middleware.

        Args:
            username: Username for authentication.
            password: Password for authentication.
        """
        import base64

        credentials = f"{username}:{password}"
        encoded = base64.b64encode(credentials.encode()).decode()
        self._auth_header = f"Basic {encoded}"

    def process_request(self, context: RequestContext) -> RequestContext:
        """Add Authorization header with Basic auth.

        Args:
            context: Request context.

        Returns:
            Context with Authorization header added.
        """
        return context.with_header("Authorization", self._auth_header)

    def process_response(self, context: ResponseContext) -> ResponseContext:
        """Pass through response unchanged.

        Args:
            context: Response context.

        Returns:
            Unchanged response context.
        """
        return context

    def on_error(self, error: Exception, context: RequestContext) -> None:
        """No-op error handler.

        Args:
            error: The exception that occurred.
            context: Request context.
        """
        pass
