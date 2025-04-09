import json

import jsonschema
import requests
from assertpy import assert_that, soft_assertions, assert_warn
from genson import SchemaBuilder


class Responder:
    def __init__(self, response: requests.Response):
        self.response = response

    def parse_json(self):
        try:
            return self.response.json()
        except json.JSONDecodeError:
            raise ValueError("Response is not valid JSON")

    def assert_status_code(self, status_code: int) -> 'Responder':
        """Assert status code should equal to status_code"""
        assert_that(self.response.status_code).is_equal_to(status_code)
        return self

    def assert_2xx(self) -> 'Responder':
        """Test status code should between 200 and 299"""
        assert_that(self.response.status_code).is_between(200, 299)
        return self

    def assert_3xx(self) -> 'Responder':
        """Test status code should between 300 and 399"""
        assert_that(self.response.status_code).is_between(300, 399)
        return self

    def assert_4xx(self) -> 'Responder':
        """Test status code should between 400 and 499"""
        assert_that(self.response.status_code).is_between(400, 499)
        return self

    def assert_5xx(self) -> 'Responder':
        """Test status code should between 500 and 599"""
        assert_that(self.response.status_code).is_between(500, 599)
        return self

    def assert_has_length(self, length: int) -> 'Responder':
        """Test response body should have length"""
        assert_that(self.response.text).is_length(length)
        return self

    def assert_contains(self, text: str) -> 'Responder':
        """Test response body should contains text"""
        assert_that(self.response.text).contains(text)
        return self

    def assert_list_contains_values(self, values: list) -> 'Responder':
        """Test response body should contains some values"""
        with soft_assertions():
            for value in values:
                assert_that(self.response.text).contains(value)
        return self

    def check_contains(self, text: str) -> 'Responder':
        """When you want to test but execution is not halted and return warning instead"""
        assert_warn(self.response.text).contains(text)
        return self

    def assert_not_contains(self, text: str) -> 'Responder':
        """Test response body should not contains text"""
        assert_that(self.response.text).does_not_contain(text)
        return self

    def get_value(self, key: str):
        """
        Get value for nested key, example get_value('data.user.id')
        """
        # check if nested key
        data = self.parse_json()
        if '.' in key:
            for part in key.split('.'):
                if isinstance(data, dict) and part in data:
                    data = data.get(part, None)
                    if data is None:
                        break
                else:
                    raise ValueError(f"Key path '{key}' not found in response")
            return data
        else:
            return self.get_data(key)

    def get_data(self, key: str):
        """Get data from response property 'data' -> [data][key]"""
        # return self.parse_json().get('data').get(key)
        return self.get_value(f"data.{key}")

    def get_property(self, key: str):
        """Get data from response body [key]"""
        return self.parse_json().get(key)

    def assert_value(self, key: str, value) -> 'Responder':
        """Test value from root property"""
        if '.' in key:
            assert_that(self.get_value(key)).is_equal_to(value)
        else:
            assert_that(self.get_property(key)).is_equal_to(value)
        return self

    def assert_response_time_less_than(self, seconds: int) -> 'Responder':
        """Test response time should less than seconds"""
        assert_that(self.response.elapsed.total_seconds()).is_less_than(seconds)
        return self

    def assert_schema(self, file_path_json_schema) -> 'Responder':
        """Test response body should match schema"""
        with open(file_path_json_schema) as f:
            schema = json.load(f)
            jsonschema.validate(self.parse_json(), schema)
        return self

    def assert_value_not_empty(self, key: str) -> 'Responder':
        """Test value from root property should not empty"""
        assert_that(self.get_property(key)).is_not_empty()
        assert_that(self.get_property(key)).is_not_none()
        return self

    def _open_json(self, path_to_json, as_string=False):
        import os
        assert os.path.exists(path_to_json), f"JSON not found, Path: {path_to_json}"
        with open(path_to_json, 'r') as content:
            content = json.load(content)
            if as_string:
                return json.dumps(content)
            else:
                return content

    def assert_schema_from_sample(self, path_to_sample_json) -> 'Responder':
        """Test response body should match schema provided by sample json response body"""
        sample_json = self._open_json(path_to_sample_json)
        builder = SchemaBuilder()
        builder.add_object(sample_json)
        schema = builder.to_schema()
        jsonschema.validate(self.parse_json(), schema)
        return self
