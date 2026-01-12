"""Tests demonstrating CRUD operations with berapi."""

import pytest
from assertpy import assert_that

from berapi import BerAPI, Settings


@pytest.fixture()
def api_client():
    """Create API client with base URL configured."""
    return BerAPI(Settings(base_url="https://jsonplaceholder.typicode.com"))


class TestCRUD:
    """Test CRUD operations using JSONPlaceholder API.

    Note: JSONPlaceholder is a fake API that simulates CRUD operations.
    POST/PUT/PATCH/DELETE requests are faked but return realistic responses.
    """

    def test_create_post(self, api_client):
        """Test POST request to create a new resource."""
        payload = {
            "title": "Test Post",
            "body": "This is a test post body",
            "userId": 1
        }

        response = (api_client
                    .post("/posts", json=payload)
                    .assert_status(201)
                    .assert_response_time(5))

        response_body = response.to_dict()

        assert_that(response_body["id"]).is_greater_than(0)
        assert_that(response_body["title"]).is_equal_to(payload["title"])
        assert_that(response_body["body"]).is_equal_to(payload["body"])
        assert_that(response_body["userId"]).is_equal_to(payload["userId"])

    def test_read_post(self, api_client):
        """Test GET request to read a resource."""
        response = (api_client
                    .get("/posts/1")
                    .assert_2xx()
                    .assert_response_time(5))

        assert_that(response.get("id")).is_equal_to(1)
        assert_that(response.get("userId")).is_equal_to(1)
        assert_that(response.get("title")).is_not_empty()

    def test_update_post_put(self, api_client):
        """Test PUT request to fully update a resource."""
        payload = {
            "id": 1,
            "title": "Updated Title",
            "body": "Updated body content",
            "userId": 1
        }

        response = (api_client
                    .put("/posts/1", json=payload)
                    .assert_2xx()
                    .assert_response_time(5)
                    .to_dict())

        assert_that(response["title"]).is_equal_to("Updated Title")
        assert_that(response["body"]).is_equal_to("Updated body content")

    def test_update_post_patch(self, api_client):
        """Test PATCH request to partially update a resource."""
        payload = {"title": "Patched Title"}

        response = (api_client
                    .patch("/posts/1", json=payload)
                    .assert_2xx()
                    .assert_response_time(5)
                    .to_dict())

        assert_that(response["title"]).is_equal_to("Patched Title")

    def test_delete_post(self, api_client):
        """Test DELETE request to remove a resource."""
        (api_client
         .delete("/posts/1")
         .assert_2xx()
         .assert_response_time(5))

    def test_list_posts(self, api_client):
        """Test GET request to list resources."""
        response = (api_client
                    .get("/posts")
                    .assert_2xx()
                    .assert_list_not_empty()
                    .assert_response_time(5))

        posts = response.to_dict()
        assert_that(posts).is_length(100)

    def test_filter_posts_by_user(self, api_client):
        """Test GET request with query parameters."""
        response = (api_client
                    .get("/posts", params={"userId": 1})
                    .assert_2xx()
                    .assert_list_not_empty()
                    .assert_response_time(5))

        posts = response.to_dict()
        for post in posts:
            assert_that(post["userId"]).is_equal_to(1)
