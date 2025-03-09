import json

import jsonschema
import requests
from assertpy import assert_that, soft_assertions, assert_warn
from genson import SchemaBuilder


class Responder:
    def __init__(self, response: requests.Response):
        self.response = response

    def parse_json(self):
        return self.response.json()

    def assert_status_code(self, status_code: int):
        """Assert status code should equal to status_code"""
        assert_that(self.response.status_code).is_equal_to(status_code)
        return self

    def assert_2xx(self):
        """Test status code should between 200 and 299"""
        assert_that(self.response.status_code).is_between(200, 299)
        return self

    def assert_3xx(self):
        """Test status code should between 300 and 399"""
        assert_that(self.response.status_code).is_between(300, 399)
        return self

    def assert_4xx(self):
        """Test status code should between 400 and 499"""
        assert_that(self.response.status_code).is_between(400, 499)
        return self

    def assert_5xx(self):
        """Test status code should between 500 and 599"""
        assert_that(self.response.status_code).is_between(500, 599)
        return self

    def assert_has_length(self, length: int):
        """Test response body should have length"""
        assert_that(self.response.text).is_length(length)
        return self

    def assert_contains(self, text: str):
        """Test response body should contains text"""
        assert_that(self.response.text).contains(text)
        return self

    def assert_list_contains_values(self, values: list):
        """Test response body should contains some values"""
        with soft_assertions():
            for value in values:
                assert_that(self.response.text).contains(value)
        return self

    def check_contains(self, text: str):
        """When you want to test but execution is not halted and return warning instead"""
        assert_warn(self.response.text).contains(text)
        return self

    def assert_not_contains(self, text: str):
        """Test response body should not contains text"""
        assert_that(self.response.text).does_not_contain(text)
        return self

    def get_data(self, key: str):
        """Get data from response body [data][key]"""
        return self.parse_json().get('data').get(key)

    def get_property(self, key: str):
        """Get data from response body [key]"""
        return self.parse_json().get(key)

    def assert_value(self, key: str, value):
        """Test value from root property"""
        assert_that(self.get_property(key)).is_equal_to(value)
        return self

    def assert_response_time_less_than(self, seconds: int):
        """Test response time should less than seconds"""
        assert_that(self.response.elapsed.total_seconds()).is_less_than(seconds)
        return self

    def assert_schema(self, file_path_json_schema):
        """Test response body should match schema"""
        with open(file_path_json_schema) as f:
            import json
            schema = json.load(f)
            jsonschema.validate(self.parse_json(), schema)
        return self

    def assert_value_not_empty(self, key: str):
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

    def assert_schema_from_sample(self, path_to_sample_json):
        """Test response body should match schema provided by sample json response body"""
        sample_json = self._open_json(path_to_sample_json)
        builder = SchemaBuilder()
        builder.add_object(sample_json)
        schema = builder.to_schema()
        jsonschema.validate(self.parse_json(), schema)
        return self