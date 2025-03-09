from pathlib import Path

from berapi.apy import berAPI

project_path = str(Path(__file__).parent.parent)


def test_schema():
    (berAPI()
     .get('https://swapi.dev/api/people/1')
     .assert_2xx()
     .assert_value('name', 'Luke Skywalker')
     .assert_response_time_less_than(seconds=5)
     .assert_schema(f'{project_path}/tests/resources/sample_schema.json')
     )


def test_schema_failed():
 (berAPI()
  .get('https://swapi.dev/api/people/1')
  .assert_2xx()
  .assert_value('name', 'Luke Skywalker')
  .assert_response_time_less_than(seconds=5)
  .assert_schema(f'{project_path}/tests/resources/sample_wrong_schema.json')
  )


def test_schema_json():
    (berAPI()
     .get('https://swapi.dev/api/people/1')
     .assert_2xx()
     .assert_value('name', 'Luke Skywalker')
     .assert_response_time_less_than(seconds=5)
     .assert_schema_from_sample(f'{project_path}/tests/resources/sample_response.json')
     )


def test_schema_json_failed():
    (berAPI()
     .get('https://swapi.dev/api/people/1')
     .assert_2xx()
     .assert_value('name', 'Luke Skywalker')
     .assert_response_time_less_than(seconds=5)
     .assert_schema_from_sample(f'{project_path}/tests/resources/sample_wrong_response.json')
     )
