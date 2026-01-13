"""Tests for request/response tracking middleware.

These tests demonstrate the TrackingMiddleware and pytest-html integration.
Run with: pytest tests/test_tracking.py --html=reports/tracking_report.html
"""

from berapi import BerAPI, Settings
from berapi.middleware import TrackingMiddleware, RequestTracker
from berapi.contrib.pytest_plugin import create_tracking_client


class TestRequestTracker:
    """Test RequestTracker functionality."""

    def test_track_request(self):
        """Test tracking a request."""
        tracker = RequestTracker()
        tracker.track_request(
            method="GET",
            url="https://api.example.com/users",
            headers={"Accept": "application/json"},
        )

        assert len(tracker) == 1
        assert tracker.requests[0].method == "GET"
        assert tracker.requests[0].url == "https://api.example.com/users"

    def test_track_response(self):
        """Test tracking a response."""
        tracker = RequestTracker()
        tracker.track_request("GET", "https://api.example.com/users")
        tracker.track_response(
            status_code=200,
            headers={"Content-Type": "application/json"},
            body={"id": 1, "name": "John"},
        )

        assert tracker.requests[0].status_code == 200
        assert "id" in tracker.requests[0].response_body

    def test_max_requests_limit(self):
        """Test that oldest requests are removed when limit is exceeded."""
        tracker = RequestTracker(max_requests=3)

        for i in range(5):
            tracker.track_request("GET", f"https://api.example.com/users/{i}")

        assert len(tracker) == 3
        # Should have requests 2, 3, 4 (oldest removed)
        assert "/users/2" in tracker.requests[0].url
        assert "/users/4" in tracker.requests[2].url

    def test_mask_headers(self):
        """Test that sensitive headers are masked."""
        tracker = RequestTracker(mask_headers=["Authorization", "X-Api-Key"])
        tracker.track_request(
            method="GET",
            url="https://api.example.com/users",
            headers={
                "Authorization": "Bearer secret-token",
                "X-Api-Key": "my-secret-key",
                "Accept": "application/json",
            },
        )

        headers = tracker.requests[0].request_headers
        assert headers["Authorization"] == "***MASKED***"
        assert headers["X-Api-Key"] == "***MASKED***"
        assert headers["Accept"] == "application/json"

    def test_clear(self):
        """Test clearing tracked requests."""
        tracker = RequestTracker()
        tracker.track_request("GET", "https://api.example.com/users")
        tracker.track_request("POST", "https://api.example.com/users")

        assert len(tracker) == 2
        tracker.clear()
        assert len(tracker) == 0

    def test_to_html(self):
        """Test HTML generation."""
        tracker = RequestTracker()
        tracker.track_request("GET", "https://api.example.com/users")
        tracker.track_response(200, {}, {"id": 1})

        html = tracker.to_html()
        assert "GET" in html
        assert "api.example.com" in html
        assert "200" in html

    def test_empty_tracker_html(self):
        """Test HTML generation with no requests."""
        tracker = RequestTracker()
        html = tracker.to_html()
        assert "No API requests tracked" in html


class TestTrackingMiddleware:
    """Test TrackingMiddleware functionality."""

    def test_middleware_tracks_requests(self):
        """Test that middleware tracks requests and responses."""
        tracker = RequestTracker()
        middleware = TrackingMiddleware(tracker)

        api = BerAPI(
            Settings(base_url="https://jsonplaceholder.typicode.com"),
            middlewares=[middleware],
        )

        api.get("/users/1").assert_2xx()

        assert len(tracker) == 1
        assert tracker.requests[0].method == "GET"
        assert tracker.requests[0].status_code == 200

    def test_middleware_tracks_post_body(self):
        """Test that middleware tracks POST request body."""
        tracker = RequestTracker()
        middleware = TrackingMiddleware(tracker)

        api = BerAPI(
            Settings(base_url="https://jsonplaceholder.typicode.com"),
            middlewares=[middleware],
        )

        api.post("/posts", json={"title": "Test", "body": "Content"}).assert_2xx()

        assert len(tracker) == 1
        assert "Test" in tracker.requests[0].request_body

    def test_middleware_with_existing_middlewares(self):
        """Test that tracking middleware works alongside other middlewares."""
        from berapi.middleware import LoggingMiddleware

        tracker = RequestTracker()

        api = BerAPI(
            Settings(base_url="https://jsonplaceholder.typicode.com"),
            middlewares=[
                LoggingMiddleware(),
                TrackingMiddleware(tracker),
            ],
        )

        api.get("/users/1").assert_2xx()
        assert len(tracker) == 1


class TestPytestPluginHelpers:
    """Test pytest plugin helper functions."""

    def test_create_tracking_client(self):
        """Test create_tracking_client helper."""
        api = create_tracking_client(
            base_url="https://jsonplaceholder.typicode.com",
            mask_headers=["Authorization"],
        )

        response = api.get("/users/1").assert_2xx()
        assert response.status_code == 200

    def test_create_tracking_client_with_headers(self):
        """Test create_tracking_client with custom headers."""
        api = create_tracking_client(
            base_url="https://httpbin.org",
            headers={"X-Custom": "test-value"},
        )

        response = api.get("/headers").assert_2xx()
        assert response.to_dict()["headers"]["X-Custom"] == "test-value"


class TestTrackingIntegration:
    """Integration tests demonstrating tracking in action.

    Run these tests with pytest-html to see the tracking output:
        pytest tests/test_tracking.py::TestTrackingIntegration --html=reports/tracking_report.html

    Then open the HTML report and click on any failed test to see
    the full request/response details.
    """

    def test_successful_tracked_request(self):
        """Successful test - tracking info available but not shown in report."""
        api = create_tracking_client(
            base_url="https://jsonplaceholder.typicode.com"
        )

        (api.get("/users/1")
         .assert_2xx()
         .assert_json_path("name", "Leanne Graham"))

    def test_multiple_requests_tracked(self):
        """Multiple requests in one test - all are tracked."""
        api = create_tracking_client(
            base_url="https://jsonplaceholder.typicode.com"
        )

        # Make multiple requests
        api.get("/users/1").assert_2xx()
        api.get("/posts/1").assert_2xx()
        api.post("/posts", json={"title": "Test"}).assert_status(201)

        # All requests are tracked
        from berapi.contrib.pytest_plugin import get_tracker
        tracker = get_tracker()
        assert len(tracker) >= 3

    def test_tracked_request_with_masked_headers(self):
        """Test that sensitive headers are masked in reports."""
        api = create_tracking_client(
            base_url="https://httpbin.org",
            headers={"Authorization": "Bearer secret-token"},
            mask_headers=["Authorization"],
        )

        api.get("/headers").assert_2xx()

        from berapi.contrib.pytest_plugin import get_tracker
        tracker = get_tracker()
        # Authorization should be masked
        assert "***MASKED***" in tracker.requests[-1].request_headers.get("Authorization", "")
