"""Request/Response tracking middleware for debugging and reporting."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import timedelta
from html import escape
from typing import Any

from berapi.middleware.base import RequestContext, ResponseContext


@dataclass
class TrackedRequest:
    """A tracked API request with its response."""

    method: str
    url: str
    request_headers: dict[str, str] = field(default_factory=dict)
    request_body: str | None = None
    status_code: int | None = None
    response_headers: dict[str, str] = field(default_factory=dict)
    response_body: str | None = None
    elapsed: timedelta | None = None


class RequestTracker:
    """Stores and renders tracked API requests for debugging.

    This class collects request/response data and can generate HTML
    reports suitable for pytest-html integration.

    Example:
        >>> tracker = RequestTracker(max_requests=10)
        >>> tracker.track_request("GET", "https://api.example.com/users")
        >>> tracker.track_response(200, {"Content-Type": "application/json"}, '{"id": 1}')
        >>> html = tracker.to_html()
    """

    def __init__(
        self,
        max_requests: int = 10,
        mask_headers: list[str] | None = None,
    ) -> None:
        """Initialize the request tracker.

        Args:
            max_requests: Maximum number of requests to store (oldest removed first).
            mask_headers: Header names to mask (e.g., ["Authorization", "X-Api-Key"]).
        """
        self.requests: list[TrackedRequest] = []
        self.max_requests = max_requests
        self.mask_headers = [h.lower() for h in (mask_headers or [])]

    def track_request(
        self,
        method: str,
        url: str,
        headers: dict[str, str] | None = None,
        body: Any | None = None,
    ) -> None:
        """Track an outgoing request.

        Args:
            method: HTTP method (GET, POST, etc.).
            url: Request URL.
            headers: Request headers.
            body: Request body (will be converted to string).
        """
        masked_headers = self._mask_headers(headers or {})
        body_str = self._safe_stringify(body)

        self.requests.append(TrackedRequest(
            method=method,
            url=url,
            request_headers=masked_headers,
            request_body=body_str,
        ))

        # Remove oldest if over limit
        if len(self.requests) > self.max_requests:
            self.requests.pop(0)

    def track_response(
        self,
        status_code: int,
        headers: dict[str, str] | None = None,
        body: Any | None = None,
        elapsed: timedelta | None = None,
    ) -> None:
        """Track an incoming response for the most recent request.

        Args:
            status_code: HTTP status code.
            headers: Response headers.
            body: Response body.
            elapsed: Response time.
        """
        if not self.requests:
            return

        current = self.requests[-1]
        if current.status_code is not None:
            return  # Already has response

        current.status_code = status_code
        current.response_headers = dict(headers) if headers else {}
        current.response_body = self._safe_stringify(body)
        current.elapsed = elapsed

    def clear(self) -> None:
        """Clear all tracked requests."""
        self.requests.clear()

    def _mask_headers(self, headers: dict[str, str]) -> dict[str, str]:
        """Mask sensitive header values."""
        return {
            k: "***MASKED***" if k.lower() in self.mask_headers else v
            for k, v in headers.items()
        }

    def _safe_stringify(self, value: Any) -> str | None:
        """Safely convert value to string."""
        if value is None:
            return None
        if isinstance(value, bytes):
            try:
                return value.decode("utf-8")
            except UnicodeDecodeError:
                return "<binary data>"
        if isinstance(value, (dict, list)):
            try:
                return json.dumps(value, indent=2, default=str)
            except (TypeError, ValueError):
                return str(value)
        return str(value)

    def _format_json(self, text: str | None) -> str:
        """Try to format as pretty JSON."""
        if not text:
            return ""
        try:
            parsed = json.loads(text)
            return json.dumps(parsed, indent=2)
        except (json.JSONDecodeError, TypeError):
            return text

    def _get_status_color(self, status: int | None) -> str:
        """Get color for status code."""
        if status is None:
            return "#6c757d"  # gray
        if 200 <= status < 300:
            return "#28a745"  # green
        if 300 <= status < 400:
            return "#17a2b8"  # blue
        if 400 <= status < 500:
            return "#ffc107"  # yellow
        return "#dc3545"  # red

    def to_html(self) -> str:
        """Generate HTML representation of tracked requests.

        Returns:
            HTML string suitable for pytest-html reports.
        """
        if not self.requests:
            return "<p>No API requests tracked</p>"

        html_parts = []
        for i, req in enumerate(self.requests, 1):
            req_body = self._format_json(req.request_body)
            resp_body = self._format_json(req.response_body)
            status_color = self._get_status_color(req.status_code)
            elapsed_str = f"{req.elapsed.total_seconds():.3f}s" if req.elapsed else ""

            html_parts.append(f'''
            <div style="margin-bottom: 20px; border: 1px solid #ddd; border-radius: 4px; overflow: hidden; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
                <div style="background: #f5f5f5; padding: 10px; border-bottom: 1px solid #ddd;">
                    <strong>Request #{i}:</strong>
                    <span style="color: #007bff; font-weight: bold;">{escape(req.method)}</span>
                    <code style="background: #e9ecef; padding: 2px 6px; border-radius: 3px; font-size: 12px;">{escape(req.url)}</code>
                    <span style="background: {status_color}; color: white; padding: 2px 8px; border-radius: 3px; margin-left: 10px; font-size: 12px;">
                        {req.status_code or 'N/A'}
                    </span>
                    {f'<span style="color: #6c757d; margin-left: 10px; font-size: 12px;">{elapsed_str}</span>' if elapsed_str else ''}
                </div>
                <div style="display: flex; flex-wrap: wrap;">
                    <div style="flex: 1; min-width: 300px; padding: 10px; border-right: 1px solid #ddd;">
                        <strong style="font-size: 12px;">Request Headers:</strong>
                        <pre style="background: #f8f9fa; padding: 8px; border-radius: 3px; overflow-x: auto; font-size: 11px; max-height: 150px; margin: 5px 0;">{escape(json.dumps(req.request_headers, indent=2))}</pre>
                        {f'<strong style="font-size: 12px;">Request Body:</strong><pre style="background: #f8f9fa; padding: 8px; border-radius: 3px; overflow-x: auto; font-size: 11px; max-height: 200px; margin: 5px 0;">{escape(req_body)}</pre>' if req_body else ''}
                    </div>
                    <div style="flex: 1; min-width: 300px; padding: 10px;">
                        <strong style="font-size: 12px;">Response Headers:</strong>
                        <pre style="background: #f8f9fa; padding: 8px; border-radius: 3px; overflow-x: auto; font-size: 11px; max-height: 150px; margin: 5px 0;">{escape(json.dumps(req.response_headers, indent=2))}</pre>
                        <strong style="font-size: 12px;">Response Body:</strong>
                        <pre style="background: #f8f9fa; padding: 8px; border-radius: 3px; overflow-x: auto; font-size: 11px; max-height: 300px; margin: 5px 0;">{escape(resp_body) if resp_body else 'No body'}</pre>
                    </div>
                </div>
            </div>
            ''')

        return ''.join(html_parts)

    def __len__(self) -> int:
        """Return number of tracked requests."""
        return len(self.requests)


class TrackingMiddleware:
    """Middleware that tracks requests and responses for debugging.

    Use this middleware to capture API calls for debugging, logging,
    or integration with test reporting tools like pytest-html.

    Example:
        >>> from berapi import BerAPI
        >>> from berapi.middleware import TrackingMiddleware
        >>>
        >>> tracker = RequestTracker()
        >>> middleware = TrackingMiddleware(tracker)
        >>> api = BerAPI(middlewares=[middleware])
        >>>
        >>> api.get("https://api.example.com/users").assert_2xx()
        >>> print(tracker.to_html())  # Get HTML report
    """

    def __init__(self, tracker: RequestTracker | None = None) -> None:
        """Initialize tracking middleware.

        Args:
            tracker: RequestTracker instance to store data.
                    If None, creates a new tracker.
        """
        self.tracker = tracker if tracker is not None else RequestTracker()

    def process_request(self, context: RequestContext) -> RequestContext:
        """Track the outgoing request.

        Args:
            context: Request context.

        Returns:
            Unchanged request context.
        """
        body = context.json_body or context.data
        self.tracker.track_request(
            method=context.method,
            url=context.url,
            headers=context.headers,
            body=body,
        )
        return context

    def process_response(self, context: ResponseContext) -> ResponseContext:
        """Track the incoming response.

        Args:
            context: Response context.

        Returns:
            Unchanged response context.
        """
        response = context.response
        try:
            body = response.json()
        except Exception:
            try:
                body = response.text[:5000] if response.text else None
            except Exception:
                body = None

        self.tracker.track_response(
            status_code=response.status_code,
            headers=dict(response.headers),
            body=body,
            elapsed=response.elapsed,
        )
        return context

    def on_error(self, error: Exception, context: RequestContext) -> None:
        """Handle errors (no-op for tracking).

        Args:
            error: The exception that occurred.
            context: Request context.
        """
        pass
