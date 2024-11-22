import jsonschema
import requests
from assertpy import assert_that, soft_assertions, assert_warn


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

    def assert_contains_values(self, values: list):
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

    def assert_schema(self, file_path_json_schema):
        """Test response body should match schema"""
        with open(file_path_json_schema) as f:
            import json
            schema = json.load(f)
            jsonschema.validate(self.parse_json(), schema)
