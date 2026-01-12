"""Tests demonstrating JSON schema validation capabilities."""

from pathlib import Path

from berapi import BerAPI

project_path = str(Path(__file__).parent.parent)


def test_json_schema_validation():
    """Test response validation against JSON schema file."""
    (BerAPI()
     .get("https://jsonplaceholder.typicode.com/users/1")
     .assert_2xx()
     .assert_json_path("name", "Leanne Graham")
     .assert_response_time(5)
     .assert_json_schema(f"{project_path}/tests/resources/user_schema.json"))


def test_json_schema_from_sample():
    """Test schema generation from sample JSON response."""
    (BerAPI()
     .get("https://jsonplaceholder.typicode.com/users/1")
     .assert_2xx()
     .assert_json_schema_from_sample(f"{project_path}/tests/resources/user_sample.json"))


def test_post_schema_validation():
    """Test post response against schema."""
    (BerAPI()
     .get("https://jsonplaceholder.typicode.com/posts/1")
     .assert_2xx()
     .assert_json_schema(f"{project_path}/tests/resources/post_schema.json"))


def test_inline_schema_validation():
    """Test response validation against inline schema dict."""
    schema = {
        "type": "object",
        "required": ["id", "name", "email"],
        "properties": {
            "id": {"type": "integer"},
            "name": {"type": "string"},
            "email": {"type": "string", "format": "email"},
            "phone": {"type": "string"},
            "website": {"type": "string"}
        }
    }

    (BerAPI()
     .get("https://jsonplaceholder.typicode.com/users/1")
     .assert_2xx()
     .assert_json_schema(schema))
