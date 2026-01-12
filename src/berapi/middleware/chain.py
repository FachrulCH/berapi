"""Middleware chain executor."""

from __future__ import annotations

from typing import TYPE_CHECKING

from berapi.logging.setup import get_logger

if TYPE_CHECKING:
    from berapi.middleware.base import Middleware, RequestContext, ResponseContext


class MiddlewareChain:
    """Executes middleware in order for requests and reverse for responses."""

    def __init__(self, middlewares: list[Middleware] | None = None) -> None:
        """Initialize middleware chain.

        Args:
            middlewares: List of middleware to execute.
        """
        self._middlewares: list[Middleware] = list(middlewares or [])
        self._logger = get_logger("berapi.middleware")

    def add(self, middleware: Middleware) -> MiddlewareChain:
        """Add middleware to the chain.

        Args:
            middleware: Middleware to add.

        Returns:
            Self for chaining.
        """
        self._middlewares.append(middleware)
        return self

    def insert(self, index: int, middleware: Middleware) -> MiddlewareChain:
        """Insert middleware at specific position.

        Args:
            index: Position to insert at.
            middleware: Middleware to insert.

        Returns:
            Self for chaining.
        """
        self._middlewares.insert(index, middleware)
        return self

    def execute_request(self, context: RequestContext) -> RequestContext:
        """Execute all middleware for outgoing request.

        Args:
            context: Request context to process.

        Returns:
            Processed request context.
        """
        for middleware in self._middlewares:
            try:
                context = middleware.process_request(context)
            except Exception as e:
                self._logger.error(
                    "middleware_request_error",
                    middleware=type(middleware).__name__,
                    error=str(e),
                )
                raise
        return context

    def execute_response(self, context: ResponseContext) -> ResponseContext:
        """Execute all middleware for incoming response (reverse order).

        Args:
            context: Response context to process.

        Returns:
            Processed response context.
        """
        for middleware in reversed(self._middlewares):
            try:
                context = middleware.process_response(context)
            except Exception as e:
                self._logger.error(
                    "middleware_response_error",
                    middleware=type(middleware).__name__,
                    error=str(e),
                )
                raise
        return context

    def handle_error(self, error: Exception, context: RequestContext) -> None:
        """Notify all middleware of an error.

        Args:
            error: The exception that occurred.
            context: The request context.
        """
        for middleware in self._middlewares:
            try:
                middleware.on_error(error, context)
            except Exception as e:
                self._logger.warning(
                    "middleware_error_handler_failed",
                    middleware=type(middleware).__name__,
                    error=str(e),
                )

    def __len__(self) -> int:
        """Return number of middleware in chain."""
        return len(self._middlewares)
