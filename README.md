# 🔥 berAPI 🔥
An API client for simplifying API testing with Python + PyTest

[Project Link](https://pypi.org/project/berapi/)

## Features
- Builtin curl API in the `pytest-html` report
- Easy to import the API logs into Postman/curl
- Multiple common assertions to a single request

![Report](berapi-report.gif)

## Installation
```bash
pip3 install berapi
```

## How to use
Create an instance of berAPI class, and you can build API test request and assertion chain of the response

```python
from berapi.apy import berAPI

def test_simple():
    url = 'https://swapi.dev/api/people/1'
    api = berAPI()
    response = api.get(url).assert_2xx().parse_json()
    assert response['name'] == 'Luke Skywalker'

def test_chaining():
    (berAPI()
     .get('https://swapi.dev/api/people/1')
     .assert_2xx()
     .assert_value('name', 'Luke Skywalker')
     .assert_response_time_less_than(seconds=1)
     )
```
### Configuration 
env variable used in berapi

```bash
export MAX_RESPONSE_TIME=5
export MAX_TIMEOUT=3
```


To have robust response log make sure you enable settings in pytest.ini
```ini
[pytest]
log_cli_level = INFO
```

### Install Development

```bash
pip install poetry
poetry install --with test
```

### Run Test
```bash
poetry run pytest tests
```

### Building Lib
```bash
poetry build
poetry publish
```