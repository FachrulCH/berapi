"""
Example: Request/Response Tracking for pytest-html Reports

This demonstrates how to add API request/response debugging to pytest-html reports.
When a test fails, you'll see exactly what HTTP requests were made and responses received.

Run locally:
    poetry run pytest tests/test_pytest_html_example.py --html=report.html -v

Then open report.html and click on failed tests to see the API debug information.

Note: These tests are skipped in CI as they intentionally fail to demonstrate the feature.
"""
import json
import os
from html import escape
from typing import Any

import pytest
from berapi import BerAPI, Settings


# Skip in CI environment
pytestmark = pytest.mark.skipif(
    os.environ.get("CI") == "true",
    reason="Skipped in CI - intentional failures for HTML report demo"
)


# =============================================================================
# REQUEST/RESPONSE TRACKER
# =============================================================================

class RequestResponseTracker:
    """Tracks API requests and responses for HTML reports."""

    def __init__(self, max_requests: int = 10):
        self.requests: list[dict] = []
        self.max_requests = max_requests

    def track_request(self, method: str, url: str, headers: dict = None, body: Any = None):
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

    def track_response(self, status_code: int, headers: dict = None, body: Any = None, elapsed: Any = None):
        if self.requests and self.requests[-1]['response'] is None:
            self.requests[-1]['response'] = {
                'status_code': status_code,
                'headers': dict(headers) if headers else {},
                'body': body,
                'elapsed': str(elapsed) if elapsed else None,
            }

    def _safe_decode(self, body: Any):
        if body is None:
            return None
        if isinstance(body, bytes):
            try:
                return body.decode('utf-8')
            except UnicodeDecodeError:
                return '<binary data>'
        if isinstance(body, (dict, list)):
            return json.dumps(body)
        return str(body)

    def clear(self):
        self.requests.clear()

    def to_html(self) -> str:
        if not self.requests:
            return '<p style="color: #6c757d;">No API requests tracked.</p>'

        html_parts = []
        for i, item in enumerate(self.requests, 1):
            req = item['request']
            resp = item.get('response') or {}

            # Format bodies
            req_body = req.get('body')
            if req_body:
                try:
                    req_body = json.dumps(json.loads(req_body), indent=2)
                except (json.JSONDecodeError, TypeError):
                    pass

            resp_body = resp.get('body')
            if resp_body and isinstance(resp_body, (dict, list)):
                resp_body = json.dumps(resp_body, indent=2)

            # Status color
            status = resp.get('status_code', 0)
            if 200 <= status < 300:
                status_color, status_bg = '#28a745', '#d4edda'
            elif 400 <= status < 500:
                status_color, status_bg = '#ffc107', '#fff3cd'
            elif status >= 500:
                status_color, status_bg = '#dc3545', '#f8d7da'
            else:
                status_color, status_bg = '#6c757d', '#e9ecef'

            html_parts.append(f'''
<div style="margin-bottom: 15px; border: 1px solid #dee2e6; border-radius: 6px; overflow: hidden;">
    <div style="background: #f8f9fa; padding: 10px; border-bottom: 1px solid #dee2e6;">
        <strong>#{i}</strong>
        <span style="background: #007bff; color: white; padding: 2px 8px; border-radius: 3px; margin-left: 8px; font-size: 12px;">{escape(req.get('method', ''))}</span>
        <code style="margin-left: 8px; font-size: 12px;">{escape(req.get('url', ''))}</code>
        <span style="background: {status_bg}; color: {status_color}; padding: 2px 8px; border-radius: 3px; margin-left: 8px; font-size: 12px; border: 1px solid {status_color}40;">{status}</span>
        {f'<span style="color: #6c757d; margin-left: 8px; font-size: 12px;">⏱ {resp.get("elapsed")}</span>' if resp.get("elapsed") else ''}
    </div>
    <div style="display: flex; flex-wrap: wrap;">
        <div style="flex: 1; min-width: 280px; padding: 10px; border-right: 1px solid #dee2e6;">
            <strong style="font-size: 11px; color: #6c757d;">Request Headers:</strong>
            <pre style="background: #f8f9fa; padding: 8px; border-radius: 4px; font-size: 10px; margin: 5px 0; max-height: 120px; overflow: auto;">{escape(json.dumps(req.get('headers', {}), indent=2))}</pre>
            {f'<strong style="font-size: 11px; color: #6c757d;">Request Body:</strong><pre style="background: #f8f9fa; padding: 8px; border-radius: 4px; font-size: 10px; margin: 5px 0; max-height: 150px; overflow: auto;">{escape(str(req_body))}</pre>' if req_body else ''}
        </div>
        <div style="flex: 1; min-width: 280px; padding: 10px;">
            <strong style="font-size: 11px; color: #6c757d;">Response Body:</strong>
            <pre style="background: #f8f9fa; padding: 8px; border-radius: 4px; font-size: 10px; margin: 5px 0; max-height: 250px; overflow: auto;">{escape(str(resp_body) if resp_body else 'No body')}</pre>
        </div>
    </div>
</div>''')
        return ''.join(html_parts)


# Global tracker
request_tracker = RequestResponseTracker()


# =============================================================================
# TRACKING MIDDLEWARE FOR BERAPI
# =============================================================================

class TrackingMiddleware:
    """Middleware that tracks requests/responses for pytest-html reports."""

    def process_request(self, context):
        request_tracker.track_request(
            method=context.method,
            url=context.url,
            headers=context.headers,
            body=context.data if hasattr(context, 'data') else None
        )
        return context

    def process_response(self, context):
        resp = context.response
        try:
            body = resp.json()
        except Exception:
            body = resp.text[:2000] if resp.text else None

        request_tracker.track_response(
            status_code=resp.status_code,
            headers=dict(resp.headers),
            body=body,
            elapsed=resp.elapsed
        )
        return context

    def on_error(self, error, context):
        pass


# =============================================================================
# PYTEST HOOKS
# =============================================================================

@pytest.hookimpl(tryfirst=True)
def pytest_runtest_setup(item):
    request_tracker.clear()


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()

    if report.when == "call" and report.failed and request_tracker.requests:
        extras = getattr(report, "extras", None) or getattr(report, "extra", [])

        try:
            from pytest_html import extras as html_extras
            html_content = f'''
<div style="margin-top: 15px; font-family: system-ui, sans-serif;">
    <h4 style="color: #dc3545; margin-bottom: 10px;">🔍 API Debug ({len(request_tracker.requests)} request{'s' if len(request_tracker.requests) != 1 else ''})</h4>
    {request_tracker.to_html()}
</div>'''
            extras.append(html_extras.html(html_content))
        except ImportError:
            pass

        if hasattr(report, "extras"):
            report.extras = extras
        else:
            report.extra = extras


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def api():
    """BerAPI client with request/response tracking enabled."""
    client = BerAPI(Settings(base_url="https://httpbin.org"))
    client.add_middleware(TrackingMiddleware())
    return client


# =============================================================================
# EXAMPLE TESTS
# =============================================================================

class TestPytestHtmlDemo:
    """Tests demonstrating pytest-html request/response tracking."""

    def test_success_no_debug_shown(self, api):
        """Passing test - no debug info in report."""
        api.get('/get').assert_2xx()

    def test_failed_assertion_shows_debug(self, api):
        """
        INTENTIONAL FAILURE - demonstrates debug output in HTML report.
        Open report.html and click this test to see request/response details.
        """
        response = api.get('/get').assert_2xx()
        assert response.get('url') == 'wrong', "Check HTML report for API debug info"

    def test_server_error_red_status(self, api):
        """
        INTENTIONAL FAILURE - shows 500 error with red status badge.
        """
        api.get('/status/500').assert_2xx()

    def test_client_error_yellow_status(self, api):
        """
        INTENTIONAL FAILURE - shows 404 error with yellow status badge.
        """
        api.get('/status/404').assert_2xx()

    def test_multiple_requests_tracked(self, api):
        """
        INTENTIONAL FAILURE - shows multiple requests in report.
        All 3 API calls will appear in the debug output.
        """
        api.get('/get').assert_2xx()
        api.post('/post', json={"name": "test"}).assert_2xx()
        api.get('/headers').assert_2xx()
        assert False, "Check HTML report - all 3 requests are tracked"
