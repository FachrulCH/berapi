from berapi.apy import berAPI


def test_get_user():
    """Test get user"""
    (berAPI()
     .get("https://jsonplaceholder.typicode.com/users/1")
     .assert_2xx())

def test_get_user_failed():
    """Test get user"""
    (berAPI()
     .get("https://jsonplaceholder.typicode.com/users/1")
     .assert_4xx())

def test_starwars_ok():
    url = 'https://swapi.dev/api/people/1'
    api = berAPI()
    api.get(url).assert_2xx().assert_contains_values(['Luke Skywalker', 'male', 'blue', '172'])

def test_starwars_failed():
    url = 'https://swapi.dev/api/people/1'
    api = berAPI()
    api.get(url).assert_2xx().assert_contains_values(['Luke Skywalker', 'female', 'red', '172'])

def test_starwars_values():
    url = 'https://swapi.dev/api/people/1'
    api = berAPI()
    name = api.get(url).assert_2xx().get_property('name')
    assert name == 'Luke Skywalker'


def test_starwars_multi_assert():
    url = 'https://swapi.dev/api/people/1'
    api = berAPI()
    response = api.get(url).assert_2xx().parse_json()
    assert response.get('name') == 'Luke Skywalker'
    assert response.get('gender') == 'male'
    assert response.get('eye_color') == 'red'
    assert "this never executed" == ""

def test_chaining():
    (berAPI()
     .get('https://swapi.dev/api/people/1')
     .assert_2xx()
     .assert_value('name', 'Luke Skywalker')
     .assert_response_time_less_than(seconds=1)
     )