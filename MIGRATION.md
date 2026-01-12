# Migration Guide: v1 to v2

This guide helps you migrate from berAPI v1 to v2. Version 2 is a complete redesign with breaking changes.

## Overview of Changes

- New package structure with `src/` layout
- New `Settings` class for configuration
- Middleware system for extensibility
- Structured logging with `structlog`
- Built-in retry with exponential backoff
- Renamed assertion methods for clarity
- Unified data access with `get()` method

## Import Changes

### v1
```python
from berapi.apy import berAPI
```

### v2
```python
from berapi import BerAPI, Settings
```

## Client Initialization

### v1
```python
api = berAPI(
    base_url='https://api.example.com',
    base_headers={'Authorization': 'Bearer token'}
)
```

### v2
```python
from berapi import BerAPI, Settings
from berapi.middleware import BearerAuthMiddleware

api = BerAPI(
    Settings(base_url='https://api.example.com'),
    middlewares=[BearerAuthMiddleware(token='token')]
)

# Or with headers directly
api = BerAPI(Settings(
    base_url='https://api.example.com',
    headers={'Authorization': 'Bearer token'}
))
```

## Environment Variables

### v1
```bash
MAX_TIMEOUT=3
MAX_RESPONSE_TIME=5
```

### v2
```bash
BERAPI_TIMEOUT=30
BERAPI_MAX_RESPONSE_TIME=10
BERAPI_LOG_LEVEL=INFO
BERAPI_RETRY_ENABLED=true
BERAPI_MAX_RETRIES=3
```

## Assertion Methods

### Status Code Assertions (unchanged)

```python
# v1 and v2 - same API
response.assert_2xx()
response.assert_4xx()
response.assert_status_code(200)  # v1
response.assert_status(200)       # v2 (renamed)
```

### JSON Value Assertions

#### v1
```python
response.assert_value('name', 'John')
response.assert_value('user.email', 'john@example.com')
```

#### v2
```python
response.assert_json_path('name', 'John')
response.assert_json_path('user.email', 'john@example.com')
```

### Schema Validation

#### v1
```python
response.assert_schema('schemas/user.json')
response.assert_schema_from_sample('samples/user.json')
```

#### v2
```python
response.assert_json_schema('schemas/user.json')
response.assert_json_schema_from_sample('samples/user.json')
```

### Other Assertion Changes

| v1 | v2 |
|----|-----|
| `assert_value(key, val)` | `assert_json_path(key, val)` |
| `assert_value_not_empty(key)` | `assert_json_not_empty(key)` |
| `assert_has_key(key)` | `assert_has_key(key)` (same) |
| `assert_value_in(key, list)` | `assert_json_in(key, list)` |
| `assert_response_time_less_than(sec)` | `assert_response_time(sec)` |
| `assert_status_code(code)` | `assert_status(code)` |

## Data Access Methods

### v1
```python
# Different methods for different access patterns
value = response.get_property('name')           # Root property
nested = response.get_value('user.email')       # Nested with dot notation
data = response.get_data('id')                  # From 'data' wrapper
json_data = response.parse_json()               # Parse JSON
```

### v2
```python
# Unified access with get()
value = response.get('name')                    # Root property
nested = response.get('user.email')             # Nested with dot notation
data = response.get('data.id')                  # From any path
json_data = response.to_dict()                  # Get as dict
```

## Logging

### v1
Standard Python logging with `logging` module.

### v2
Structured logging with `structlog`. Configure via settings:

```python
from berapi import BerAPI, Settings, LoggingSettings

api = BerAPI(Settings(
    logging=LoggingSettings(
        level='DEBUG',
        format='console',  # or 'json'
        log_curl=True,
    )
))
```

## Middleware (New in v2)

v1 had no middleware system. v2 introduces middleware for extensibility:

```python
from berapi import BerAPI, Settings
from berapi.middleware import (
    LoggingMiddleware,
    BearerAuthMiddleware,
)

api = BerAPI(
    Settings(base_url='https://api.example.com'),
    middlewares=[
        LoggingMiddleware(),
        BearerAuthMiddleware(token='your-token'),
    ]
)
```

### Custom Middleware

```python
from berapi.middleware import RequestContext, ResponseContext

class CustomMiddleware:
    def process_request(self, context: RequestContext) -> RequestContext:
        # Modify request
        return context.with_header('X-Custom', 'value')

    def process_response(self, context: ResponseContext) -> ResponseContext:
        # Process response
        return context

    def on_error(self, error: Exception, context: RequestContext) -> None:
        # Handle errors
        pass
```

## Retry (New in v2)

v1 had no retry support. v2 has built-in retry with exponential backoff:

```python
from berapi import BerAPI, Settings, RetrySettings

api = BerAPI(Settings(
    retry=RetrySettings(
        enabled=True,
        max_retries=3,
        backoff_factor=0.5,
        retry_statuses=frozenset({429, 500, 502, 503, 504}),
    )
))
```

## Error Handling

### v1
Generic exceptions and `requests.Timeout`.

### v2
Custom exception hierarchy with detailed information:

```python
from berapi.exceptions import (
    StatusCodeError,
    JsonPathError,
    TimeoutError,
    RetryExhaustedError,
    JsonSchemaError,
)

try:
    response = api.get('/users/1').assert_2xx()
except StatusCodeError as e:
    print(f"Expected {e.expected}, got {e.actual}")
except JsonPathError as e:
    print(f"Path {e.path}: expected {e.expected}, got {e.actual}")
```

## Complete Migration Example

### v1 Test
```python
from berapi.apy import berAPI

def test_user_crud():
    api = berAPI(
        base_url='https://api.example.com',
        base_headers={'Authorization': 'Bearer token'}
    )

    # Create
    response = api.post('/users', json={'name': 'John'})
    response.assert_status_code(201)
    user_id = response.get_value('data.id')

    # Read
    response = api.get(f'/users/{user_id}')
    response.assert_2xx().assert_value('data.name', 'John')

    # Update
    response = api.put(f'/users/{user_id}', json={'name': 'Jane'})
    response.assert_2xx()

    # Delete
    api.delete(f'/users/{user_id}').assert_2xx()
```

### v2 Test
```python
from berapi import BerAPI, Settings
from berapi.middleware import LoggingMiddleware, BearerAuthMiddleware

def test_user_crud():
    api = BerAPI(
        Settings(base_url='https://api.example.com'),
        middlewares=[
            LoggingMiddleware(),
            BearerAuthMiddleware(token='token'),
        ]
    )

    # Create
    response = api.post('/users', json={'name': 'John'})
    response.assert_status(201)
    user_id = response.get('data.id')

    # Read
    response = api.get(f'/users/{user_id}')
    response.assert_2xx().assert_json_path('data.name', 'John')

    # Update
    response = api.put(f'/users/{user_id}', json={'name': 'Jane'})
    response.assert_2xx()

    # Delete
    api.delete(f'/users/{user_id}').assert_2xx()
```

## Quick Reference

| v1 | v2 |
|----|-----|
| `from berapi.apy import berAPI` | `from berapi import BerAPI, Settings` |
| `berAPI(base_url=..., base_headers=...)` | `BerAPI(Settings(base_url=..., headers=...))` |
| `response.get_value('a.b')` | `response.get('a.b')` |
| `response.get_property('key')` | `response.get('key')` |
| `response.get_data('key')` | `response.get('data.key')` |
| `response.parse_json()` | `response.to_dict()` |
| `response.assert_value(key, val)` | `response.assert_json_path(key, val)` |
| `response.assert_value_not_empty(key)` | `response.assert_json_not_empty(key)` |
| `response.assert_value_in(key, list)` | `response.assert_json_in(key, list)` |
| `response.assert_schema(file)` | `response.assert_json_schema(file)` |
| `response.assert_schema_from_sample(file)` | `response.assert_json_schema_from_sample(file)` |
| `response.assert_status_code(code)` | `response.assert_status(code)` |
| `response.assert_response_time_less_than(sec)` | `response.assert_response_time(sec)` |
| `MAX_TIMEOUT` env | `BERAPI_TIMEOUT` env |
| `MAX_RESPONSE_TIME` env | `BERAPI_MAX_RESPONSE_TIME` env |
