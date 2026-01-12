"""Simple tests demonstrating basic berapi functionality."""

from berapi import BerAPI


def test_get_request():
    """Test basic GET request with status assertion."""
    (BerAPI()
     .get("https://jsonplaceholder.typicode.com/users/1")
     .assert_2xx())


def test_json_path_assertion():
    """Test JSON path assertions with dot notation."""
    (BerAPI()
     .get("https://jsonplaceholder.typicode.com/users/1")
     .assert_2xx()
     .assert_json_path("name", "Leanne Graham")
     .assert_json_path("address.city", "Gwenborough")
     .assert_json_path("company.name", "Romaguera-Crona"))


def test_response_contains():
    """Test response body contains specific text."""
    (BerAPI()
     .get("https://jsonplaceholder.typicode.com/users/1")
     .assert_2xx()
     .assert_contains("Leanne Graham")
     .assert_contains("Sincere@april.biz"))


def test_response_time():
    """Test response time assertion."""
    (BerAPI()
     .get("https://jsonplaceholder.typicode.com/users/1")
     .assert_2xx()
     .assert_response_time(5))


def test_get_value():
    """Test extracting values from response."""
    response = (BerAPI()
                .get("https://jsonplaceholder.typicode.com/users/1")
                .assert_2xx())

    name = response.get("name")
    email = response.get("email")
    city = response.get("address.city")

    assert name == "Leanne Graham"
    assert email == "Sincere@april.biz"
    assert city == "Gwenborough"


def test_to_dict():
    """Test converting response to dictionary."""
    response = (BerAPI()
                .get("https://jsonplaceholder.typicode.com/users/1")
                .assert_2xx()
                .to_dict())

    assert response["name"] == "Leanne Graham"
    assert response["address"]["city"] == "Gwenborough"


def test_method_chaining():
    """Test fluent method chaining with multiple assertions."""
    (BerAPI()
     .get("https://jsonplaceholder.typicode.com/posts/1")
     .assert_2xx()
     .assert_json_path("userId", 1)
     .assert_json_path("id", 1)
     .assert_has_key("title")
     .assert_has_key("body")
     .assert_response_time(5))


def test_list_response():
    """Test assertions on list responses."""
    (BerAPI()
     .get("https://jsonplaceholder.typicode.com/posts")
     .assert_2xx()
     .assert_list_not_empty())


def test_status_code_assertion():
    """Test specific status code assertion."""
    (BerAPI()
     .get("https://httpbin.org/status/200")
     .assert_status(200))


def test_404_response():
    """Test 4xx status code assertion."""
    (BerAPI()
     .get("https://httpbin.org/status/404")
     .assert_4xx())
