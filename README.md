# 🔥 berAPI 🔥
An API client for simplifying API testing with Python + PyTest

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
make sure pytest.ini is having output log
```ini
[pytest]
log_cli_level = INFO
```

### Install Development

```bash
pip install poetry
pip install pytest
pip install pytest-html
```