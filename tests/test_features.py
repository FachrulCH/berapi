"""Tests showcasing advanced berapi features.

This module demonstrates the key capabilities of the berapi v2.0 library:
- Settings and configuration
- Middleware system (logging, auth)
- Header assertions
- Custom headers
"""

from berapi import BerAPI, Settings
from berapi.middleware import LoggingMiddleware, BearerAuthMiddleware, ApiKeyMiddleware


# =============================================================================
# Settings & Configuration
# =============================================================================

class TestSettings:
    """Test Settings configuration capabilities."""

    def test_base_url_configuration(self):
        """Test API client with base URL setting."""
        api = BerAPI(Settings(base_url="https://jsonplaceholder.typicode.com"))

        # Requests use relative paths
        (api.get("/users/1")
         .assert_2xx()
         .assert_json_path("name", "Leanne Graham"))

    def test_default_headers(self):
        """Test API client with default headers."""
        api = BerAPI(Settings(
            base_url="https://httpbin.org",
            headers={"X-Custom-Header": "test-value"}
        ))

        response = api.get("/headers").assert_2xx().to_dict()
        assert response["headers"]["X-Custom-Header"] == "test-value"

    def test_timeout_configuration(self):
        """Test API client with custom timeout."""
        api = BerAPI(Settings(
            base_url="https://httpbin.org",
            timeout=10.0
        ))

        (api.get("/delay/1")
         .assert_2xx()
         .assert_response_time(10))


# =============================================================================
# Header Assertions
# =============================================================================

class TestHeaderAssertions:
    """Test header assertion capabilities."""

    def test_content_type_assertion(self):
        """Test content-type header assertion."""
        (BerAPI()
         .get("https://jsonplaceholder.typicode.com/users/1")
         .assert_2xx()
         .assert_content_type("application/json"))

    def test_header_exists(self):
        """Test header exists assertion."""
        (BerAPI()
         .get("https://httpbin.org/response-headers?X-Test=value")
         .assert_2xx()
         .assert_header_exists("X-Test"))

    def test_header_value(self):
        """Test header value assertion."""
        (BerAPI()
         .get("https://httpbin.org/response-headers?X-Custom=hello")
         .assert_2xx()
         .assert_header("X-Custom", "hello"))


# =============================================================================
# Middleware System
# =============================================================================

class TestMiddleware:
    """Test middleware capabilities."""

    def test_logging_middleware(self):
        """Test logging middleware logs requests."""
        api = BerAPI(
            Settings(base_url="https://jsonplaceholder.typicode.com"),
            middlewares=[LoggingMiddleware()]
        )

        api.get("/users/1").assert_2xx()

        # LoggingMiddleware uses structlog, output depends on configuration
        # This test verifies middleware doesn't break the request flow

    def test_bearer_auth_middleware(self):
        """Test bearer auth middleware adds Authorization header."""
        api = BerAPI(
            Settings(base_url="https://httpbin.org"),
            middlewares=[BearerAuthMiddleware(token="test-token-123")]
        )

        response = api.get("/headers").assert_2xx().to_dict()
        assert "Bearer test-token-123" in response["headers"]["Authorization"]

    def test_api_key_middleware_header(self):
        """Test API key middleware adds X-API-Key header."""
        api = BerAPI(
            Settings(base_url="https://httpbin.org"),
            middlewares=[ApiKeyMiddleware(api_key="secret-key")]
        )

        response = api.get("/headers").assert_2xx().to_dict()
        assert response["headers"]["X-Api-Key"] == "secret-key"

    def test_api_key_middleware_custom_header(self):
        """Test API key middleware with custom header name."""
        api = BerAPI(
            Settings(base_url="https://httpbin.org"),
            middlewares=[ApiKeyMiddleware(
                api_key="my-secret",
                header_name="X-Custom-Api-Key"
            )]
        )

        response = api.get("/headers").assert_2xx().to_dict()
        assert response["headers"]["X-Custom-Api-Key"] == "my-secret"

    def test_add_middleware_fluent(self):
        """Test adding middleware with fluent API."""
        api = (BerAPI(Settings(base_url="https://httpbin.org"))
               .add_middleware(ApiKeyMiddleware(api_key="fluent-key")))

        response = api.get("/headers").assert_2xx().to_dict()
        # httpbin returns X-Api-Key header (default header name for ApiKeyMiddleware)
        assert response["headers"].get("X-Api-Key") == "fluent-key"


# =============================================================================
# Data Extraction
# =============================================================================

class TestDataExtraction:
    """Test data extraction capabilities."""

    def test_nested_json_path(self):
        """Test extracting deeply nested values."""
        response = (BerAPI()
                    .get("https://jsonplaceholder.typicode.com/users/1")
                    .assert_2xx())

        # Extract nested values using dot notation
        city = response.get("address.city")
        lat = response.get("address.geo.lat")
        company_name = response.get("company.name")

        assert city == "Gwenborough"
        assert lat == "-37.3159"
        assert company_name == "Romaguera-Crona"

    def test_list_response(self):
        """Test working with list responses."""
        response = (BerAPI()
                    .get("https://jsonplaceholder.typicode.com/users")
                    .assert_2xx()
                    .assert_list_not_empty())

        # Get the full list and access first user
        users = response.to_dict()
        assert users[0]["name"] == "Leanne Graham"

    def test_response_properties(self):
        """Test accessing response properties."""
        response = (BerAPI()
                    .get("https://jsonplaceholder.typicode.com/users/1")
                    .assert_2xx())

        assert response.status_code == 200
        assert "application/json" in response.headers.get("Content-Type", "")
        assert response.elapsed.total_seconds() > 0


# =============================================================================
# Error Handling
# =============================================================================

class TestErrorHandling:
    """Test error handling and status code assertions."""

    def test_404_handling(self):
        """Test handling 404 responses."""
        (BerAPI()
         .get("https://jsonplaceholder.typicode.com/users/9999")
         .assert_4xx()
         .assert_status(404))

    def test_server_error_assertion(self):
        """Test 5xx status code assertion."""
        (BerAPI()
         .get("https://httpbin.org/status/500")
         .assert_5xx())

    def test_redirect_handling(self):
        """Test 3xx redirect handling."""
        # httpbin follows redirects by default
        (BerAPI()
         .get("https://httpbin.org/redirect-to?url=https://httpbin.org/get")
         .assert_2xx())


# =============================================================================
# Request Types
# =============================================================================

class TestRequestTypes:
    """Test different HTTP request types."""

    def test_post_with_json(self):
        """Test POST request with JSON body."""
        payload = {"name": "Test", "value": 123}

        response = (BerAPI()
                    .post("https://httpbin.org/post", json=payload)
                    .assert_2xx()
                    .to_dict())

        assert response["json"]["name"] == "Test"
        assert response["json"]["value"] == 123

    def test_post_with_form_data(self):
        """Test POST request with form data."""
        data = {"field1": "value1", "field2": "value2"}

        response = (BerAPI()
                    .post("https://httpbin.org/post", data=data)
                    .assert_2xx()
                    .to_dict())

        assert response["form"]["field1"] == "value1"
        assert response["form"]["field2"] == "value2"

    def test_request_with_query_params(self):
        """Test request with query parameters."""
        params = {"search": "test", "page": 1}

        response = (BerAPI()
                    .get("https://httpbin.org/get", params=params)
                    .assert_2xx()
                    .to_dict())

        assert response["args"]["search"] == "test"
        assert response["args"]["page"] == "1"

    def test_request_with_custom_headers(self):
        """Test request with custom headers."""
        headers = {"X-Custom-Header": "custom-value", "Accept-Language": "en-US"}

        response = (BerAPI()
                    .get("https://httpbin.org/headers", headers=headers)
                    .assert_2xx()
                    .to_dict())

        assert response["headers"].get("X-Custom-Header") == "custom-value"
        assert response["headers"].get("Accept-Language") == "en-US"
