"""pytest-html integration for berapi request/response tracking.

This module provides pytest hooks and fixtures for automatically capturing
API requests and responses, then displaying them in pytest-html reports
when tests fail.

Usage:
    # In your conftest.py:
    pytest_plugins = ["berapi.contrib.pytest_plugin"]

    @pytest.fixture
    def api():
        from berapi.contrib.pytest_plugin import create_tracking_client
        return create_tracking_client(base_url="https://api.example.com")

    # Or for more control:
    from berapi.contrib.pytest_plugin import get_tracker, create_tracking_client

    @pytest.fixture
    def api():
        client = create_tracking_client(
            base_url="https://api.example.com",
            mask_headers=["Authorization"],
        )
        return client
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest

from berapi import BerAPI, Settings
from berapi.middleware.tracking import RequestTracker, TrackingMiddleware

if TYPE_CHECKING:
    from berapi.middleware.base import Middleware

# Global tracker instance - shared across all tests in a session
_global_tracker: RequestTracker | None = None
_track_only_failures: bool = True


def get_tracker() -> RequestTracker:
    """Get the global request tracker instance.

    Returns:
        The global RequestTracker instance.
    """
    global _global_tracker
    if _global_tracker is None:
        _global_tracker = RequestTracker()
    return _global_tracker


def create_tracking_client(
    base_url: str | None = None,
    headers: dict[str, str] | None = None,
    timeout: float = 30.0,
    mask_headers: list[str] | None = None,
    max_requests: int = 10,
    middlewares: list[Middleware] | None = None,
    **settings_kwargs: Any,
) -> BerAPI:
    """Create a BerAPI client with request/response tracking enabled.

    This client automatically tracks all requests and responses, which
    will be displayed in pytest-html reports when tests fail.

    Args:
        base_url: Base URL for API requests.
        headers: Default headers to include in all requests.
        timeout: Request timeout in seconds.
        mask_headers: Header names to mask in reports (e.g., ["Authorization"]).
        max_requests: Maximum number of requests to track per test.
        middlewares: Additional middleware to add (tracking is added automatically).
        **settings_kwargs: Additional settings passed to Settings.

    Returns:
        BerAPI client with tracking enabled.

    Example:
        >>> @pytest.fixture
        ... def api():
        ...     return create_tracking_client(
        ...         base_url="https://api.example.com",
        ...         mask_headers=["Authorization", "X-Api-Key"],
        ...     )
        ...
        >>> def test_users(api):
        ...     api.get("/users").assert_2xx()
    """
    global _global_tracker

    # Configure the global tracker with provided settings
    if _global_tracker is None:
        _global_tracker = RequestTracker(
            max_requests=max_requests,
            mask_headers=mask_headers,
        )
    else:
        # Update settings on existing tracker
        _global_tracker.max_requests = max_requests
        if mask_headers:
            _global_tracker.mask_headers = [h.lower() for h in mask_headers]

    # Create settings
    settings = Settings(
        base_url=base_url,
        headers=headers or {},
        timeout=timeout,
        **settings_kwargs,
    )

    # Build middleware list
    all_middlewares: list[Middleware] = []
    if middlewares:
        all_middlewares.extend(middlewares)
    all_middlewares.append(TrackingMiddleware(_global_tracker))

    return BerAPI(settings=settings, middlewares=all_middlewares)


def configure_tracking(
    track_only_failures: bool = True,
    max_requests: int = 10,
    mask_headers: list[str] | None = None,
) -> None:
    """Configure global tracking settings.

    Call this in conftest.py to customize tracking behavior.

    Args:
        track_only_failures: If True, only add tracking info to failed tests.
        max_requests: Maximum requests to track per test.
        mask_headers: Headers to mask in reports.

    Example:
        >>> # In conftest.py
        >>> from berapi.contrib.pytest_plugin import configure_tracking
        >>> configure_tracking(track_only_failures=False, max_requests=20)
    """
    global _track_only_failures, _global_tracker
    _track_only_failures = track_only_failures

    if _global_tracker is None:
        _global_tracker = RequestTracker(
            max_requests=max_requests,
            mask_headers=mask_headers,
        )
    else:
        _global_tracker.max_requests = max_requests
        if mask_headers:
            _global_tracker.mask_headers = [h.lower() for h in mask_headers]


# =============================================================================
# Pytest Hooks
# =============================================================================


def pytest_configure(config: pytest.Config) -> None:
    """Register the plugin marker."""
    config.addinivalue_line(
        "markers",
        "berapi_tracking: Enable request/response tracking for this test",
    )


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_setup(item: pytest.Item) -> None:
    """Clear request tracker before each test."""
    tracker = get_tracker()
    tracker.clear()


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo) -> Any:
    """Add request/response data to HTML report."""
    outcome = yield
    report = outcome.get_result()

    # Only process after test execution (not setup/teardown)
    if report.when != "call":
        return

    # Check if we should add tracking info
    should_add = (
        (not _track_only_failures) or
        (report.failed)
    )

    if not should_add:
        return

    tracker = get_tracker()
    if not tracker.requests:
        return

    # Get or create extras list
    extras = getattr(report, "extras", None)
    if extras is None:
        extras = getattr(report, "extra", [])

    # Generate and add HTML content
    html_content = f'''
    <div class="berapi-tracking" style="margin-top: 15px;">
        <h4 style="color: {'#dc3545' if report.failed else '#28a745'}; margin-bottom: 10px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
            API Requests/Responses ({len(tracker.requests)} call{'s' if len(tracker.requests) != 1 else ''})
        </h4>
        {tracker.to_html()}
    </div>
    '''
    extras.append(_create_html_extra(html_content))

    # Set extras back on report
    if hasattr(report, "extras"):
        report.extras = extras
    else:
        report.extra = extras


def _create_html_extra(content: str) -> Any:
    """Create pytest-html extra HTML content.

    Args:
        content: HTML content string.

    Returns:
        pytest-html extra object.
    """
    try:
        from pytest_html import extras
        return extras.html(content)
    except ImportError:
        # Fallback for older pytest-html or when not installed
        class HtmlExtra:
            def __init__(self, content: str) -> None:
                self.content = content
                self.name = "html"
        return HtmlExtra(content)
