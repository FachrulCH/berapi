"""
Example: Request/Response Tracking for pytest-html Reports

This test file demonstrates how to use custom middleware to capture API
requests/responses and display them in pytest-html reports when tests fail.

Run locally with:
    poetry run pytest tests/test_pytest_html_example.py --html=report.html -v

Then open report.html and click on failed tests to see request/response details.

Note: These tests are skipped in CI (GitHub Actions) because they intentionally
fail to demonstrate the HTML report feature.
"""
import json
import os
from html import escape

import pytest
from berapi import BerAPI, Settings


# Skip all tests in this module when running in CI
pytestmark = pytest.mark.skipif(
    os.environ.get("CI") == "true",
    reason="Skipped in CI - these tests intentionally fail to demo HTML reports"
)


# =============================================================================
# Request/Response Tracking Implementation
# =============================================================================

class RequestResponseTracker:
    """Tracks API requests and responses for HTML reports."""

    def __init__(self):
        self.requests = []
        self.max_requests = 10

    def track_request(self, method, url, headers, body):
        self.requests.append({
            'request': {
                'method': method,
                'url': str(url),
                'headers': dict(headers) if headers else {},
                'body': self._safe_decode(body),
            },
            'response': None
        })
        if len(self.requests) > self.max_requests:
            self.requests.pop(0)

    def track_response(self, status_code, headers, body, elapsed=None):
        if self.requests and self.requests[-1]['response'] is None:
            self.requests[-1]['response'] = {
                'status_code': status_code,
                'headers': dict(headers) if headers else {},
                'body': body,
                'elapsed': str(elapsed) if elapsed else None,
            }

    def _safe_decode(self, body):
        if body is None:
            return None
        if isinstance(body, bytes):
            try:
                return body.decode('utf-8')
            except UnicodeDecodeError:
                return '<binary data>'
        return str(body)

    def clear(self):
        self.requests.clear()

    def to_html(self) -> str:
        """Generate HTML representation of tracked requests."""
        if not self.requests:
            return '<p>No API requests tracked</p>'

        html_parts = []
        for i, item in enumerate(self.requests, 1):
            req = item['request']
            resp = item.get('response') or {}

            status = resp.get('status_code', 0)
            if 200 <= status < 300:
                status_color = '#28a745'  # green
            elif 400 <= status < 500:
                status_color = '#ffc107'  # yellow
            else:
                status_color = '#dc3545'  # red

            resp_body = resp.get('body')
            if resp_body and isinstance(resp_body, (dict, list)):
                resp_body = json.dumps(resp_body, indent=2)

            html_parts.append(f'''
            <div style="margin: 10px 0; border: 1px solid #ddd; border-radius: 4px;">
                <div style="background: #f5f5f5; padding: 8px;">
                    <strong>{escape(req.get('method', ''))}</strong>
                    <code>{escape(req.get('url', ''))}</code>
                    <span style="background: {status_color}; color: white; padding: 2px 6px; border-radius: 3px; margin-left: 8px;">{status}</span>
                    {f'<span style="color: #6c757d; margin-left: 8px;">{resp.get("elapsed")}</span>' if resp.get("elapsed") else ''}
                </div>
                <pre style="padding: 8px; margin: 0; overflow-x: auto; font-size: 11px; max-height: 300px;">{escape(str(resp_body) if resp_body else 'No body')}</pre>
            </div>
            ''')
        return ''.join(html_parts)


# Global tracker instance for this test module
_request_tracker = RequestResponseTracker()


class TrackingMiddleware:
    """Middleware that tracks requests/responses for debugging."""

    def process_request(self, context):
        try:
            _request_tracker.track_request(
                method=context.method,
                url=context.url,
                headers=context.headers,
                body=context.body if hasattr(context, 'body') else None
            )
        except Exception:
            pass
        return context

    def process_response(self, context):
        try:
            resp = context.response
            body = None
            try:
                body = resp.json()
            except Exception:
                body = resp.text[:2000] if resp.text else None
            _request_tracker.track_response(
                status_code=resp.status_code,
                headers=resp.headers,
                body=body,
                elapsed=resp.elapsed if hasattr(resp, 'elapsed') else None
            )
        except Exception:
            pass
        return context

    def on_error(self, error, context):
        pass


# =============================================================================
# Pytest Hooks for HTML Report Integration
# =============================================================================

@pytest.hookimpl(tryfirst=True)
def pytest_runtest_setup(item):
    """Clear tracker before each test."""
    _request_tracker.clear()


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Add request/response data to HTML report for failed tests."""
    outcome = yield
    report = outcome.get_result()

    if report.when == "call" and report.failed:
        extras = getattr(report, "extras", []) or getattr(report, "extra", [])

        if _request_tracker.requests:
            try:
                from pytest_html import extras as html_extras
                html_content = f'''
                <div style="margin-top: 15px;">
                    <h4 style="color: #dc3545;">API Requests/Responses ({len(_request_tracker.requests)} calls)</h4>
                    {_request_tracker.to_html()}
                </div>
                '''
                extras.append(html_extras.html(html_content))
            except ImportError:
                pass

        if hasattr(report, "extras"):
            report.extras = extras
        else:
            report.extra = extras


# =============================================================================
# API Client Fixture
# =============================================================================

@pytest.fixture()
def tracked_api() -> BerAPI:
    """API client with request/response tracking enabled."""
    client = BerAPI(Settings(base_url="https://httpbin.org"))
    client.add_middleware(TrackingMiddleware())
    return client


# =============================================================================
# Example Tests
# =============================================================================

class TestPytestHtmlTracking:
    """
    Example tests demonstrating request/response tracking in HTML reports.

    Run with: pytest tests/test_pytest_html_example.py --html=report.html -v
    """

    def test_successful_request_no_tracking_shown(self, tracked_api):
        """This test passes - no debug info shown in report."""
        response = tracked_api.get('/get').assert_2xx()
        assert response.status_code == 200

    def test_failed_assertion_shows_request_response(self, tracked_api):
        """
        This test fails - request/response will appear in HTML report.

        Open report.html and click on this test to see:
        - The GET request to /get
        - Response status code (green 200)
        - Full response body
        """
        response = tracked_api.get('/get').assert_2xx()
        # This assertion will fail - check the HTML report!
        assert response.get('url') == 'https://wrong-url.com', \
            "Intentional failure to demonstrate HTML report tracking"

    def test_api_error_shows_in_report(self, tracked_api):
        """
        Test with 500 response - shows red status in report.

        The HTML report will show the 500 error response.
        """
        response = tracked_api.get('/status/500')
        # This will fail - report shows the 500 response in red
        response.assert_2xx()

    def test_multiple_requests_all_tracked(self, tracked_api):
        """
        Multiple API calls - all are tracked in the report.

        The HTML report will show all 3 requests made during this test.
        """
        # First request
        tracked_api.get('/get').assert_2xx()

        # Second request with POST
        tracked_api.post('/post', json={"test": "data"}).assert_2xx()

        # Third request
        tracked_api.get('/headers').assert_2xx()

        # This will fail - all 3 requests appear in the report
        assert False, "Intentional failure to show multiple tracked requests"

    def test_404_response_yellow_status(self, tracked_api):
        """
        Test with 404 response - shows yellow status in report.
        """
        response = tracked_api.get('/status/404')
        # This will fail - report shows the 404 response in yellow
        response.assert_2xx()
