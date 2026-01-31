# BerAPI

A modern, scalable API testing library for Python with middleware support, structured logging, and fluent assertions.

[![PyPI version](https://badge.fury.io/py/berapi.svg)](https://pypi.org/project/berapi/)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Features

- **Fluent Assertions** - Chainable syntax like `.get().assert_2xx().assert_json_path("name", "John")`
- **Middleware System** - Extensible request/response middleware for logging, auth, and custom logic
- **Structured Logging** - JSON-formatted logs with structlog for easy parsing and debugging
- **Retry with Backoff** - Automatic retries with exponential backoff and jitter
- **OpenAPI Validation** - Validate responses against OpenAPI/Swagger specifications
- **JSON Schema Validation** - Validate responses against JSON Schema
- **Type Hints** - Full type annotations for IDE support and type checking

## Installation

```bash
pip install berapi
```

## Quick Start

```python
from berapi import BerAPI, Settings
from berapi.middleware import LoggingMiddleware

# Create client with configuration
api = BerAPI(
    Settings(base_url="https://jsonplaceholder.typicode.com"),
    middlewares=[LoggingMiddleware()]
)

# Make request with fluent assertions
response = (
    api.get("/posts/1")
    .assert_2xx()
    .assert_json_path("userId", 1)
    .assert_response_time(2.0)
)

# Access response data
post = response.to_dict()
title = response.get("title")
```

## Table of Contents

- [Configuration](#configuration)
- [Making Requests](#making-requests)
- [Assertions](#assertions)
- [Data Access](#data-access)
- [Middleware](#middleware)
  - [Why Use Middleware?](#why-use-middleware)
  - [Built-in Middleware](#built-in-middleware)
  - [Custom Middleware Examples](#custom-middleware-examples)
  - [pytest-html Integration](#pytest-html-integration)
- [Retry and Backoff](#retry-and-backoff)
  - [Why Use Retry?](#why-use-retry)
  - [How Exponential Backoff Works](#how-exponential-backoff-works)
  - [Use Cases](#use-cases)
- [OpenAPI Validation](#openapi-validation)
  - [Why Use OpenAPI Validation?](#why-use-openapi-validation)
  - [Setup](#setup)
  - [Use Cases](#use-cases-1)
- [Error Handling](#error-handling)
- [Migration from v1](#migration-from-v1)

## Configuration

### Using Settings

```python
from berapi import BerAPI, Settings, LoggingSettings, RetrySettings

api = BerAPI(Settings(
    base_url="https://api.example.com",
    timeout=30.0,
    max_response_time=10.0,  # Fail if response takes longer
    verify_ssl=True,
    headers={"X-Custom-Header": "value"},
    logging=LoggingSettings(
        level="INFO",
        format="json",  # or "console"
        log_curl=True,
    ),
    retry=RetrySettings(
        enabled=True,
        max_retries=3,
        backoff_factor=0.5,
        jitter=True,
    ),
))
```

### Using Environment Variables

```python
from berapi import BerAPI, Settings

# Load all settings from environment
api = BerAPI(Settings.from_env())
```

Environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `BERAPI_BASE_URL` | None | Base URL for requests |
| `BERAPI_TIMEOUT` | 30.0 | Request timeout (seconds) |
| `BERAPI_MAX_RESPONSE_TIME` | None | Max response time threshold |
| `BERAPI_VERIFY_SSL` | true | Verify SSL certificates |
| `BERAPI_LOG_LEVEL` | INFO | Log level (DEBUG, INFO, WARNING, ERROR) |
| `BERAPI_LOG_FORMAT` | json | Log format (json, console) |
| `BERAPI_LOG_CURL` | true | Log curl commands |
| `BERAPI_RETRY_ENABLED` | true | Enable retry |
| `BERAPI_MAX_RETRIES` | 3 | Max retry attempts |
| `BERAPI_BACKOFF_FACTOR` | 0.5 | Backoff multiplier |
| `BERAPI_OPENAPI_SPEC` | None | Path to OpenAPI spec |

## Making Requests

### HTTP Methods

```python
from berapi import BerAPI, Settings

api = BerAPI(Settings(base_url="https://api.example.com"))

# GET
response = api.get("/users", params={"page": 1})

# POST with JSON
response = api.post("/users", json={"name": "John", "email": "john@example.com"})

# PUT
response = api.put("/users/1", json={"name": "Jane"})

# PATCH
response = api.patch("/users/1", json={"email": "jane@example.com"})

# DELETE
response = api.delete("/users/1")

# Custom method
response = api.request("OPTIONS", "/users")
```

### Request Options

```python
# Custom headers
response = api.get("/users", headers={"X-Request-ID": "123"})

# Query parameters
response = api.get("/users", params={"page": 1, "limit": 10})

# Custom timeout
response = api.get("/users", timeout=60.0)
```

## Assertions

All assertion methods return `self` for chaining.

### Status Code

```python
response.assert_status(200)           # Exact status
response.assert_status_range(200, 299) # Range
response.assert_2xx()                  # 200-299
response.assert_3xx()                  # 300-399
response.assert_4xx()                  # 400-499
response.assert_5xx()                  # 500-599
```

### Headers

```python
response.assert_header("X-Request-ID", "123")
response.assert_header_exists("X-Rate-Limit")
response.assert_content_type("application/json")
```

### Response Body

```python
response.assert_contains("success")
response.assert_not_contains("error")
```

### JSON

```python
# Assert value at path (supports dot notation)
response.assert_json_path("name", "John")
response.assert_json_path("user.email", "john@example.com")
response.assert_json_path("items.0.id", 1)

# Assert key exists
response.assert_has_key("id")
response.assert_has_key("user.profile.avatar")

# Assert not empty
response.assert_json_not_empty("name")

# Assert value in list
response.assert_json_in("status", ["active", "pending", "inactive"])

# Assert list response
response.assert_list_not_empty()
```

### Schema Validation

```python
# JSON Schema from dict
response.assert_json_schema({
    "type": "object",
    "required": ["id", "name"],
    "properties": {
        "id": {"type": "integer"},
        "name": {"type": "string"}
    }
})

# JSON Schema from file
response.assert_json_schema("schemas/user.json")

# Auto-generated schema from sample
response.assert_json_schema_from_sample("samples/user_response.json")
```

### OpenAPI Validation

```python
# With spec path
response.assert_openapi("getUser", spec_path="openapi.yaml")

# With configured spec
api = BerAPI(Settings(openapi_spec_path="openapi.yaml"))
api.get("/users/1").assert_openapi("getUser")
```

### Performance

```python
response.assert_response_time(2.0)  # Max 2 seconds
```

## Data Access

```python
# Get entire response as dict
data = response.to_dict()

# Get value with dot notation
user_id = response.get("id")
email = response.get("user.email")
first_item = response.get("items.0")

# Get with default
status = response.get("status", "unknown")

# Get multiple values
values = response.get_all(["id", "name", "email"])

# Access properties
status_code = response.status_code
headers = response.headers
text = response.text
elapsed = response.elapsed
```

## Middleware

Middleware provides a powerful way to intercept and modify requests and responses. It follows the chain of responsibility pattern, allowing you to compose multiple middleware for different concerns.

### Why Use Middleware?

- **Separation of Concerns** - Keep authentication, logging, and other cross-cutting concerns separate from your test logic
- **Reusability** - Write once, use across all your API tests
- **Composability** - Stack multiple middleware to build complex behaviors
- **Testability** - Easy to mock and test individual middleware components

### How Middleware Works

```
Request Flow:  Client -> Middleware1 -> Middleware2 -> Server
Response Flow: Client <- Middleware1 <- Middleware2 <- Server
```

Each middleware can:
1. **Modify requests** before they're sent (add headers, transform body, etc.)
2. **Modify responses** after they're received (parse, validate, transform)
3. **Handle errors** that occur during the request/response cycle

### Built-in Middleware

#### LoggingMiddleware

Provides structured logging for all HTTP requests and responses.

```python
from berapi import BerAPI, Settings
from berapi.middleware import LoggingMiddleware

api = BerAPI(
    Settings(base_url="https://api.example.com"),
    middlewares=[
        LoggingMiddleware(
            log_curl=True,              # Log curl command for reproduction
            log_request_body=True,      # Log request body
            log_response_body=True,     # Log response body
            log_headers=True,           # Log headers
            max_body_length=10000,      # Truncate large bodies
            redact_headers=frozenset({  # Hide sensitive headers
                "authorization",
                "x-api-key",
                "cookie"
            }),
        )
    ]
)
```

**Output Example (JSON format):**
```json
{
  "event": "http_request",
  "method": "POST",
  "url": "https://api.example.com/users",
  "headers": {"Authorization": "[REDACTED]", "Content-Type": "application/json"},
  "body": {"name": "John", "email": "john@example.com"},
  "curl": "curl -X POST 'https://api.example.com/users' -H 'Content-Type: application/json' -d '{\"name\":\"John\"}'",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### BearerAuthMiddleware

Automatically adds Bearer token authentication to all requests.

```python
from berapi.middleware import BearerAuthMiddleware

# Static token
api = BerAPI(
    Settings(base_url="https://api.example.com"),
    middlewares=[BearerAuthMiddleware(token="your-jwt-token")]
)

# Dynamic token (refreshable)
def get_fresh_token():
    # Fetch from token service, cache, or generate new
    return token_service.get_access_token()

api = BerAPI(
    Settings(base_url="https://api.example.com"),
    middlewares=[BearerAuthMiddleware(token=get_fresh_token)]
)
```

#### ApiKeyMiddleware

Adds API key authentication via custom header.

```python
from berapi.middleware import ApiKeyMiddleware

# Default header (X-API-Key)
api = BerAPI(
    middlewares=[ApiKeyMiddleware(api_key="your-api-key")]
)

# Custom header name
api = BerAPI(
    middlewares=[ApiKeyMiddleware(
        api_key="your-api-key",
        header_name="X-Custom-Auth",
        prefix="ApiKey "  # Optional prefix
    )]
)
```

### Custom Middleware Examples

#### Request ID Middleware

Add unique request IDs for tracing:

```python
import uuid
from berapi.middleware import RequestContext, ResponseContext

class RequestIdMiddleware:
    def process_request(self, context: RequestContext) -> RequestContext:
        request_id = str(uuid.uuid4())
        return context.with_header("X-Request-ID", request_id)

    def process_response(self, context: ResponseContext) -> ResponseContext:
        return context

    def on_error(self, error: Exception, context: RequestContext) -> None:
        pass
```

#### Timing Middleware

Track and alert on slow requests:

```python
import time
from berapi.middleware import RequestContext, ResponseContext

class TimingMiddleware:
    def __init__(self, warn_threshold: float = 1.0):
        self.warn_threshold = warn_threshold

    def process_request(self, context: RequestContext) -> RequestContext:
        # Store start time in metadata
        return context.with_metadata("start_time", time.time())

    def process_response(self, context: ResponseContext) -> ResponseContext:
        start_time = context.request_context.metadata.get("start_time")
        if start_time:
            elapsed = time.time() - start_time
            if elapsed > self.warn_threshold:
                print(f"SLOW REQUEST: {context.request_context.url} took {elapsed:.2f}s")
        return context

    def on_error(self, error: Exception, context: RequestContext) -> None:
        pass
```

#### Response Caching Middleware

Cache responses for repeated requests:

```python
import hashlib
import json
from berapi.middleware import RequestContext, ResponseContext

class CachingMiddleware:
    def __init__(self):
        self._cache = {}

    def _cache_key(self, context: RequestContext) -> str:
        key_data = f"{context.method}:{context.url}:{json.dumps(context.params or {})}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def process_request(self, context: RequestContext) -> RequestContext:
        # Only cache GET requests
        if context.method == "GET":
            cache_key = self._cache_key(context)
            context = context.with_metadata("cache_key", cache_key)
        return context

    def process_response(self, context: ResponseContext) -> ResponseContext:
        cache_key = context.request_context.metadata.get("cache_key")
        if cache_key and context.status_code == 200:
            self._cache[cache_key] = context.response.json()
        return context

    def on_error(self, error: Exception, context: RequestContext) -> None:
        pass
```

#### Error Notification Middleware

Send alerts on failures:

```python
class SlackNotificationMiddleware:
    def __init__(self, webhook_url: str, notify_on_status: list[int] = None):
        self.webhook_url = webhook_url
        self.notify_on_status = notify_on_status or [500, 502, 503, 504]

    def process_request(self, context: RequestContext) -> RequestContext:
        return context

    def process_response(self, context: ResponseContext) -> ResponseContext:
        if context.status_code in self.notify_on_status:
            self._send_notification(
                f"API Error: {context.request_context.method} {context.request_context.url} "
                f"returned {context.status_code}"
            )
        return context

    def on_error(self, error: Exception, context: RequestContext) -> None:
        self._send_notification(f"API Exception: {context.url} - {error}")

    def _send_notification(self, message: str):
        import requests
        requests.post(self.webhook_url, json={"text": message})
```

### Middleware Order

Middleware executes in order for requests and reverse order for responses:

```python
api = BerAPI(
    middlewares=[
        LoggingMiddleware(),      # 1st for request, 3rd for response
        BearerAuthMiddleware(),   # 2nd for request, 2nd for response
        TimingMiddleware(),       # 3rd for request, 1st for response
    ]
)
```

### Adding Middleware Dynamically

```python
api = BerAPI(Settings(base_url="https://api.example.com"))

# Add middleware after creation
api.add_middleware(LoggingMiddleware())
api.add_middleware(BearerAuthMiddleware(token="token"))

# Middleware is added to the end of the chain
```

### pytest-html Integration

You can create a custom middleware to capture API requests and responses for pytest-html reports. This is useful for debugging failed tests by showing exactly what was sent and received.

> **Full implementation with cURL generation**: See [docs/pytest-html-tracking.md](docs/pytest-html-tracking.md) for the enhanced version with cURL commands, CSS optimizations, and more customization options.

#### 1. Create a Request Tracker

```python
# conftest.py
import json
from html import escape

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
                </div>
                <pre style="padding: 8px; margin: 0; overflow-x: auto; font-size: 11px;">{escape(str(resp_body) if resp_body else 'No body')}</pre>
            </div>
            ''')
        return ''.join(html_parts)


# Global tracker instance
_request_tracker = RequestResponseTracker()
```

#### 2. Create Tracking Middleware

```python
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
```

#### 3. Add pytest Hooks

```python
import pytest

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
                    <h4>API Requests ({len(_request_tracker.requests)} calls)</h4>
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
```

#### 4. Create API Client Fixture

```python
from berapi import BerAPI, Settings

@pytest.fixture()
def api_client() -> BerAPI:
    """API client with request/response tracking."""
    client = BerAPI(Settings(base_url="https://api.example.com"))
    client.add_middleware(TrackingMiddleware())
    return client
```

#### 5. Run Tests with HTML Report

```bash
pytest --html=report.html
```

When tests fail, the HTML report will show all API requests made during the test with:
- Request method and URL
- Response status code (color-coded: green/yellow/red)
- Full response body

> **Want more features?** See the [detailed pytest-html guide](docs/pytest-html-tracking.md) for:
> - **cURL command generation** - Ready-to-use commands to reproduce requests
> - **CSS optimizations** - Proper width/wrapping without horizontal scrolling
> - **Request/response headers** - Full header inspection
> - **Customization options** - Sensitive header redaction, custom colors, and more
> - **Integration with other HTTP clients** (requests, httpx)

---

## Retry and Backoff

BerAPI includes built-in retry functionality with exponential backoff to handle transient failures gracefully.

### Why Use Retry?

- **Handle Transient Failures** - Network glitches, temporary server issues
- **Rate Limiting** - Automatically retry after rate limit responses (429)
- **Improved Reliability** - Tests don't fail due to temporary issues
- **Server Recovery** - Wait for overwhelmed servers to recover

### How Exponential Backoff Works

Exponential backoff increases the delay between retries exponentially:

```
Attempt 1: Immediate
Attempt 2: Wait 0.5s  (backoff_factor * 2^0)
Attempt 3: Wait 1.0s  (backoff_factor * 2^1)
Attempt 4: Wait 2.0s  (backoff_factor * 2^2)
...
```

With **jitter** (randomness), delays are varied to prevent thundering herd:
```
Attempt 2: Wait 0.25s - 0.75s (50% - 150% of calculated delay)
```

### Configuration

```python
from berapi import BerAPI, Settings, RetrySettings

api = BerAPI(Settings(
    base_url="https://api.example.com",
    retry=RetrySettings(
        enabled=True,           # Enable/disable retry
        max_retries=3,          # Maximum retry attempts
        backoff_factor=0.5,     # Base delay multiplier
        backoff_max=60.0,       # Maximum delay cap (seconds)
        jitter=True,            # Add randomness to delays
        retry_statuses=frozenset({  # Status codes to retry
            429,  # Too Many Requests
            500,  # Internal Server Error
            502,  # Bad Gateway
            503,  # Service Unavailable
            504,  # Gateway Timeout
        }),
    ),
))
```

### Use Cases

#### Rate Limiting (429 Too Many Requests)

```python
# API returns 429 when rate limited
# BerAPI automatically waits and retries

api = BerAPI(Settings(
    base_url="https://api.example.com",
    retry=RetrySettings(
        enabled=True,
        max_retries=5,
        backoff_factor=1.0,  # Start with 1 second delay
        retry_statuses=frozenset({429}),
    ),
))

# This will retry up to 5 times if rate limited
response = api.get("/high-traffic-endpoint").assert_2xx()
```

#### Flaky Services

```python
# Handle unreliable third-party services
api = BerAPI(Settings(
    base_url="https://flaky-service.example.com",
    retry=RetrySettings(
        enabled=True,
        max_retries=3,
        backoff_factor=0.5,
        retry_statuses=frozenset({500, 502, 503, 504}),
    ),
))
```

#### Load Testing Resilience

```python
# During load tests, services may temporarily fail
api = BerAPI(Settings(
    retry=RetrySettings(
        enabled=True,
        max_retries=2,
        backoff_factor=0.25,  # Quick retries
        jitter=True,          # Prevent synchronized retries
    ),
))
```

### Handling Retry Exhaustion

```python
from berapi.exceptions import RetryExhaustedError

api = BerAPI(Settings(
    retry=RetrySettings(enabled=True, max_retries=3),
))

try:
    response = api.get("/unreliable-endpoint").assert_2xx()
except RetryExhaustedError as e:
    print(f"Failed after {e.attempts} attempts")
    print(f"Last error: {e.last_error}")
    # Handle permanent failure
```

### Disabling Retry for Specific Tests

```python
# Global retry enabled
api = BerAPI(Settings(
    retry=RetrySettings(enabled=True, max_retries=3),
))

# Disable for specific test by creating new client
api_no_retry = api.with_settings(retry={"enabled": False})
response = api_no_retry.get("/endpoint-that-should-not-retry")
```

### Retry Timing Examples

With `backoff_factor=0.5` and `max_retries=4`:

| Attempt | Delay (no jitter) | Delay (with jitter) |
|---------|-------------------|---------------------|
| 1       | 0s (immediate)    | 0s                  |
| 2       | 0.5s              | 0.25s - 0.75s       |
| 3       | 1.0s              | 0.5s - 1.5s         |
| 4       | 2.0s              | 1.0s - 3.0s         |
| 5       | 4.0s              | 2.0s - 6.0s         |

---

## OpenAPI Validation

Validate your API responses against OpenAPI (Swagger) specifications to ensure contract compliance.

### Why Use OpenAPI Validation?

- **Contract Testing** - Ensure API responses match documented specification
- **Regression Detection** - Catch breaking changes early
- **Documentation Accuracy** - Verify docs match implementation
- **Type Safety** - Validate response data types automatically
- **Schema Evolution** - Detect unintended schema changes

### Setup

#### 1. Provide OpenAPI Spec

Create or use your existing OpenAPI specification (YAML or JSON):

```yaml
# openapi.yaml
openapi: 3.0.0
info:
  title: User API
  version: 1.0.0
paths:
  /users/{id}:
    get:
      operationId: getUser
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: integer
      responses:
        '200':
          description: User found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/User'
        '404':
          description: User not found

components:
  schemas:
    User:
      type: object
      required:
        - id
        - name
        - email
      properties:
        id:
          type: integer
        name:
          type: string
        email:
          type: string
          format: email
        createdAt:
          type: string
          format: date-time
```

#### 2. Configure BerAPI

```python
from berapi import BerAPI, Settings

# Option 1: Configure in Settings
api = BerAPI(Settings(
    base_url="https://api.example.com",
    openapi_spec_path="openapi.yaml",
))

# Option 2: Specify per assertion
api = BerAPI(Settings(base_url="https://api.example.com"))
response.assert_openapi("getUser", spec_path="openapi.yaml")
```

### Basic Usage

```python
from berapi import BerAPI, Settings

api = BerAPI(Settings(
    base_url="https://api.example.com",
    openapi_spec_path="specs/openapi.yaml",
))

# Validate response matches OpenAPI spec for "getUser" operation
response = (
    api.get("/users/1")
    .assert_2xx()
    .assert_openapi("getUser")  # Validates against spec
)
```

### Use Cases

#### Contract Testing

Ensure your API implementation matches the documented contract:

```python
import pytest
from berapi import BerAPI, Settings

@pytest.fixture
def api():
    return BerAPI(Settings(
        base_url="https://api.example.com",
        openapi_spec_path="openapi.yaml",
    ))

class TestUserAPIContract:
    def test_get_user_matches_spec(self, api):
        """Verify GET /users/{id} matches OpenAPI spec."""
        response = (
            api.get("/users/1")
            .assert_2xx()
            .assert_openapi("getUser")
        )

    def test_create_user_matches_spec(self, api):
        """Verify POST /users matches OpenAPI spec."""
        response = (
            api.post("/users", json={
                "name": "John Doe",
                "email": "john@example.com"
            })
            .assert_status(201)
            .assert_openapi("createUser")
        )

    def test_list_users_matches_spec(self, api):
        """Verify GET /users matches OpenAPI spec."""
        response = (
            api.get("/users")
            .assert_2xx()
            .assert_openapi("listUsers")
        )
```

#### Regression Testing

Detect breaking changes when API is updated:

```python
def test_user_schema_unchanged(api):
    """Ensure user schema hasn't changed unexpectedly."""
    response = api.get("/users/1").assert_2xx()

    # OpenAPI validation catches:
    # - Missing required fields
    # - Wrong data types
    # - Invalid enum values
    # - Format violations (email, date-time, etc.)
    response.assert_openapi("getUser")
```

#### Multi-Environment Validation

Validate different environments against the same spec:

```python
import pytest
from berapi import BerAPI, Settings

@pytest.fixture(params=["dev", "staging", "prod"])
def api(request):
    base_urls = {
        "dev": "https://dev-api.example.com",
        "staging": "https://staging-api.example.com",
        "prod": "https://api.example.com",
    }
    return BerAPI(Settings(
        base_url=base_urls[request.param],
        openapi_spec_path="openapi.yaml",
    ))

def test_all_environments_match_spec(api):
    """All environments should match the API contract."""
    response = api.get("/users/1").assert_2xx().assert_openapi("getUser")
```

### Error Handling

```python
from berapi.exceptions import OpenAPIError

try:
    response = api.get("/users/1").assert_openapi("getUser")
except OpenAPIError as e:
    print(f"Validation failed for operation: {e.operation_id}")
    print(f"Errors:")
    for error in e.errors:
        print(f"  - {error}")
```

**Example Error Output:**
```
OpenAPI validation failed:
  - Response body validation failed: 'email' is a required property
  - Content-Type 'text/plain' not in allowed types ['application/json']
```

### Combining with JSON Schema

You can use both OpenAPI validation and JSON Schema for comprehensive validation:

```python
response = (
    api.get("/users/1")
    .assert_2xx()
    .assert_openapi("getUser")           # Validate against OpenAPI spec
    .assert_json_schema({                 # Additional custom validation
        "type": "object",
        "properties": {
            "email": {"pattern": "^[a-z]+@example\\.com$"}  # Custom pattern
        }
    })
)
```

### Best Practices

1. **Keep specs in version control** - Track changes to your API contract
2. **Use operationId** - Give each operation a unique, descriptive ID
3. **Validate on CI/CD** - Run contract tests in your pipeline
4. **Test error responses** - Validate 4xx/5xx responses too
5. **Update specs first** - Change spec before implementation (contract-first)

```python
# Test error response schema
def test_not_found_matches_spec(api):
    response = api.get("/users/99999").assert_4xx().assert_openapi("getUser")

def test_validation_error_matches_spec(api):
    response = (
        api.post("/users", json={"invalid": "data"})
        .assert_status(422)
        .assert_openapi("createUser")
    )
```

## Error Handling

```python
from berapi import BerAPI, Settings
from berapi.exceptions import (
    StatusCodeError,
    JsonPathError,
    TimeoutError,
    RetryExhaustedError,
)

api = BerAPI(Settings(base_url="https://api.example.com"))

try:
    response = api.get("/users/1").assert_2xx()
except StatusCodeError as e:
    print(f"Expected {e.expected}, got {e.actual}")
except JsonPathError as e:
    print(f"Path {e.path}: expected {e.expected}, got {e.actual}")
except TimeoutError as e:
    print(f"Request timed out after {e.timeout}s")
except RetryExhaustedError as e:
    print(f"Failed after {e.attempts} attempts: {e.last_error}")
```

## Complete Example

```python
import pytest
from berapi import BerAPI, Settings
from berapi.middleware import LoggingMiddleware, BearerAuthMiddleware

@pytest.fixture
def api():
    return BerAPI(
        Settings(
            base_url="https://jsonplaceholder.typicode.com",
            timeout=10.0,
        ),
        middlewares=[LoggingMiddleware()]
    )

class TestUserAPI:
    def test_get_user(self, api):
        response = (
            api.get("/users/1")
            .assert_2xx()
            .assert_json_path("id", 1)
            .assert_has_key("email")
            .assert_response_time(2.0)
        )
        user = response.to_dict()
        assert "name" in user

    def test_create_user(self, api):
        response = (
            api.post("/users", json={
                "name": "John Doe",
                "email": "john@example.com"
            })
            .assert_status(201)
            .assert_json_not_empty("id")
        )
        user_id = response.get("id")
        assert user_id is not None

    def test_list_users(self, api):
        response = (
            api.get("/users")
            .assert_2xx()
            .assert_list_not_empty()
        )
        users = response.to_dict()
        assert len(users) > 0

    def test_not_found(self, api):
        api.get("/users/99999").assert_4xx()
```

## Migration from v1

See [MIGRATION.md](MIGRATION.md) for detailed migration guide from v1 to v2.

## Development

```bash
# Install dependencies
pip install poetry
poetry install --with test

# Run tests
poetry run pytest tests/

# Type checking
poetry run mypy src/
```

## License

MIT License - see [LICENSE](LICENSE) for details.
