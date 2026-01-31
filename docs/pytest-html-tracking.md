# Request/Response Tracking for pytest-html Reports

Add API request/response debugging to your pytest-html reports. When a test fails, see exactly what HTTP requests were made and responses received, including ready-to-use cURL commands.

## Features

- **Request/Response Tracking** - Capture all API calls made during tests
- **Color-coded Status Badges** - Green (2xx), Yellow (4xx), Red (5xx)
- **cURL Command Generation** - Copy-paste commands to reproduce requests
- **CSS Optimized Layout** - No horizontal scrolling, proper text wrapping
- **Automatic Cleanup** - Data cleared between tests, only shown on failures

## Quick Start

### 1. Install Dependencies

```bash
pip install pytest pytest-html berapi
# or with poetry
poetry add pytest pytest-html berapi
```

### 2. Create the Tracker and Middleware

Add this to your `tests/conftest.py`:

```python
import json
from html import escape
import pytest
from berapi import BerAPI, Settings


class RequestResponseTracker:
    """Tracks API requests and responses for debugging in HTML reports."""

    def __init__(self):
        self.requests = []
        self.max_requests = 10  # Keep last N requests

    def track_request(self, method, url, headers, body):
        """Track an outgoing request."""
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
        """Track an incoming response (pairs with last request)."""
        if self.requests and self.requests[-1]['response'] is None:
            self.requests[-1]['response'] = {
                'status_code': status_code,
                'headers': dict(headers) if headers else {},
                'body': body,
                'elapsed': str(elapsed) if elapsed else None,
            }

    def _safe_decode(self, body):
        """Safely decode request body."""
        if body is None:
            return None
        if isinstance(body, bytes):
            try:
                return body.decode('utf-8')
            except UnicodeDecodeError:
                return '<binary data>'
        return str(body)

    def clear(self):
        """Clear tracked requests."""
        self.requests.clear()

    def _generate_curl(self, req: dict) -> str:
        """Generate a curl command from request data."""
        method = req.get('method', 'GET')
        url = req.get('url', '')
        headers = req.get('headers', {})
        body = req.get('body')

        parts = ['curl']
        if method != 'GET':
            parts.append(f'-X {method}')
        parts.append(f"'{url}'")

        for key, value in headers.items():
            if key.lower() == 'content-length':
                continue
            escaped_value = str(value).replace("'", "'\\''")
            parts.append(f"-H '{key}: {escaped_value}'")

        if body:
            try:
                body_json = json.loads(body) if isinstance(body, str) else body
                body_str = json.dumps(body_json, separators=(',', ':'))
            except (json.JSONDecodeError, TypeError):
                body_str = str(body)
            escaped_body = body_str.replace("'", "'\\''")
            parts.append(f"-d '{escaped_body}'")

        return ' \\\n  '.join(parts)

    def to_html(self) -> str:
        """Generate HTML representation of tracked requests."""
        if not self.requests:
            return '<p>No API requests tracked</p>'

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
                status_color = '#28a745'
            elif 400 <= status < 500:
                status_color = '#ffc107'
            else:
                status_color = '#dc3545'

            curl_cmd = self._generate_curl(req)

            # CSS styles
            pre_style = "background: #f8f9fa; padding: 8px; border-radius: 3px; overflow-x: hidden; white-space: pre-wrap; word-break: break-word; font-size: 11px;"
            url_style = "background: #e9ecef; padding: 2px 6px; border-radius: 3px; word-break: break-all; max-width: 60%; display: inline-block; vertical-align: middle;"

            html_parts.append(f'''
            <div style="margin-bottom: 20px; border: 1px solid #ddd; border-radius: 4px; overflow: hidden; max-width: 100%; box-sizing: border-box;">
                <div style="background: #f5f5f5; padding: 10px; border-bottom: 1px solid #ddd;">
                    <strong>Request #{i}:</strong>
                    <span style="color: #007bff;">{escape(req.get('method', 'UNKNOWN'))}</span>
                    <code style="{url_style}">{escape(req.get('url', ''))}</code>
                    <span style="background: {status_color}; color: white; padding: 2px 8px; border-radius: 3px; margin-left: 10px;">
                        {status}
                    </span>
                    {f'<span style="color: #6c757d; margin-left: 10px;">{resp.get("elapsed")}</span>' if resp.get("elapsed") else ''}
                </div>
                <div style="display: flex; flex-wrap: wrap;">
                    <div style="flex: 1; min-width: 300px; padding: 10px; border-right: 1px solid #ddd;">
                        <strong>Request Headers:</strong>
                        <pre style="{pre_style} max-height: 150px;">{escape(json.dumps(req.get('headers', {}), indent=2))}</pre>
                        {f'<strong>Request Body:</strong><pre style="{pre_style} max-height: 200px;">{escape(str(req_body))}</pre>' if req_body else ''}
                    </div>
                    <div style="flex: 1; min-width: 300px; padding: 10px;">
                        <strong>Response Headers:</strong>
                        <pre style="{pre_style} max-height: 150px;">{escape(json.dumps(resp.get('headers', {}), indent=2))}</pre>
                        <strong>Response Body:</strong>
                        <pre style="{pre_style} max-height: 300px;">{escape(str(resp_body) if resp_body else 'No body')}</pre>
                    </div>
                </div>
                <div style="padding: 10px; border-top: 1px solid #ddd; background: #2d2d2d;">
                    <strong style="color: #a0a0a0;">cURL Command:</strong>
                    <pre style="background: #1e1e1e; color: #d4d4d4; padding: 10px; border-radius: 3px; overflow-x: hidden; white-space: pre-wrap; word-break: break-word; font-size: 11px; margin-top: 5px;">{escape(curl_cmd)}</pre>
                </div>
            </div>
            ''')

        return ''.join(html_parts)


# Global tracker instance
_request_tracker = RequestResponseTracker()


class TrackingMiddleware:
    """BerAPI middleware that tracks requests and responses."""

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
                try:
                    body = resp.text[:2000] if resp.text else None
                except Exception:
                    pass
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
```

### 3. Add pytest Hooks

Add these hooks to the same `tests/conftest.py`:

```python
@pytest.hookimpl(tryfirst=True)
def pytest_runtest_setup(item):
    """Clear request tracker before each test."""
    _request_tracker.clear()


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Add request/response data to HTML report for failed tests."""
    outcome = yield
    report = outcome.get_result()

    if report.when == "call" and report.failed:
        if _request_tracker.requests:
            html_content = f'''
            <div class="api-debug-info" style="margin-top: 15px;">
                <h4 style="color: #dc3545; margin-bottom: 10px;">
                    API Requests/Responses ({len(_request_tracker.requests)} calls)
                </h4>
                {_request_tracker.to_html()}
            </div>
            '''
            extra_item = _create_html_extra(html_content)

            # pytest-html 4.x uses 'extras', older versions use 'extra'
            if hasattr(report, "extras"):
                if report.extras is None:
                    report.extras = []
                report.extras.append(extra_item)
            else:
                if not hasattr(report, "extra") or report.extra is None:
                    report.extra = []
                report.extra.append(extra_item)


def _create_html_extra(content):
    """Create pytest-html extra HTML content."""
    try:
        from pytest_html import extras
        return extras.html(content)
    except ImportError:
        class HtmlExtra:
            def __init__(self, content):
                self.content = content
                self.name = "html"
        return HtmlExtra(content)
```

### 4. Create API Client Fixture

```python
@pytest.fixture
def api():
    """BerAPI client with request/response tracking enabled."""
    client = BerAPI(Settings(base_url="https://your-api.com"))
    client.add_middleware(TrackingMiddleware())
    return client
```

### 5. Write Tests

```python
class TestUserAPI:
    def test_get_user(self, api):
        response = api.get('/users/1').assert_2xx()
        assert response.get('name') == 'John'

    def test_create_user(self, api):
        response = api.post('/users', json={
            'name': 'Jane',
            'email': 'jane@example.com'
        }).assert_2xx()
        assert response.get('id') is not None
```

### 6. Run Tests with HTML Report

```bash
pytest tests/ --html=report.html -v
```

Open `report.html` in a browser. Click on any failed test to see the API debug information.

## What You'll See

For each failed test, the report shows:

```
┌─────────────────────────────────────────────────────────────┐
│ Request #1: POST https://api.example.com/users        201   │
├─────────────────────────────────────────────────────────────┤
│ Request Headers:          │ Response Headers:               │
│ {                         │ {                               │
│   "Content-Type": "...",  │   "Content-Type": "...",        │
│   "Authorization": "..."  │   "X-Request-Id": "..."         │
│ }                         │ }                               │
│                           │                                 │
│ Request Body:             │ Response Body:                  │
│ {                         │ {                               │
│   "name": "Jane",         │   "id": 123,                    │
│   "email": "jane@..."     │   "name": "Jane",               │
│ }                         │   "email": "jane@..."           │
│                           │ }                               │
├─────────────────────────────────────────────────────────────┤
│ cURL Command:                                               │
│ curl -X POST 'https://api.example.com/users' \              │
│   -H 'Content-Type: application/json' \                     │
│   -d '{"name":"Jane","email":"jane@example.com"}'           │
└─────────────────────────────────────────────────────────────┘
```

## Customization

### Change Maximum Tracked Requests

```python
_request_tracker.max_requests = 20  # Default is 10
```

### Track All Tests (Not Just Failures)

Modify the hook to remove the failure check:

```python
@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()

    # Remove 'report.failed' check to show for all tests
    if report.when == "call":
        if _request_tracker.requests:
            # ... rest of the code
```

### Custom Status Colors

Modify the `to_html()` method:

```python
# Custom colors
if 200 <= status < 300:
    status_color = '#00ff00'  # bright green
elif 400 <= status < 500:
    status_color = '#ff9900'  # orange
else:
    status_color = '#ff0000'  # bright red
```

### Hide Sensitive Headers

Add filtering in `_generate_curl()`:

```python
SENSITIVE_HEADERS = {'authorization', 'x-api-key', 'cookie'}

for key, value in headers.items():
    if key.lower() in SENSITIVE_HEADERS:
        escaped_value = '***REDACTED***'
    else:
        escaped_value = str(value).replace("'", "'\\''")
    parts.append(f"-H '{key}: {escaped_value}'")
```

## Using with Other HTTP Clients

### requests library

```python
import requests

class RequestsTrackingSession(requests.Session):
    def request(self, method, url, **kwargs):
        _request_tracker.track_request(
            method=method,
            url=url,
            headers=kwargs.get('headers', {}),
            body=kwargs.get('json') or kwargs.get('data')
        )
        response = super().request(method, url, **kwargs)
        _request_tracker.track_response(
            status_code=response.status_code,
            headers=dict(response.headers),
            body=response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text[:2000],
            elapsed=response.elapsed
        )
        return response

@pytest.fixture
def http():
    return RequestsTrackingSession()
```

### httpx library

```python
import httpx

class TrackingTransport(httpx.BaseTransport):
    def __init__(self):
        self._transport = httpx.HTTPTransport()

    def handle_request(self, request):
        _request_tracker.track_request(
            method=request.method,
            url=str(request.url),
            headers=dict(request.headers),
            body=request.content.decode() if request.content else None
        )
        response = self._transport.handle_request(request)
        _request_tracker.track_response(
            status_code=response.status_code,
            headers=dict(response.headers),
            body=response.json() if 'application/json' in response.headers.get('content-type', '') else response.text[:2000]
        )
        return response

@pytest.fixture
def http():
    return httpx.Client(transport=TrackingTransport())
```

## Troubleshooting

### Debug info not appearing

1. Ensure hooks are in `conftest.py` (not just the test file)
2. Verify `pytest-html` is installed: `pip show pytest-html`
3. Check the test actually failed (debug info only shows on failures by default)

### cURL command doesn't work

1. Check for special characters in the URL or body that need escaping
2. Verify the API endpoint is accessible from your terminal
3. Add `-v` flag to curl for verbose output: `curl -v ...`

### Report shows "No API requests tracked"

1. Ensure the middleware is added to your client: `client.add_middleware(TrackingMiddleware())`
2. Check that the fixture is being used in the test
3. Verify the global `_request_tracker` instance is the same one used by hooks

## Example Project Structure

```
my-project/
├── tests/
│   ├── conftest.py          # Tracker, middleware, hooks, fixtures
│   ├── test_users.py         # User API tests
│   └── test_orders.py        # Order API tests
├── pytest.ini
└── requirements.txt
```

## See Also

- [pytest-html documentation](https://pytest-html.readthedocs.io/)
- [BerAPI documentation](https://github.com/anthropics/berapi)
- [Example implementation](../tests/test_pytest_html_example.py)
