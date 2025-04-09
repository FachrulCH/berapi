import os

import pytest
from assertpy import assert_that
from faker import Faker

from berapi.apy import berAPI

faker = Faker()


@pytest.fixture()
def api_client():
    return berAPI(base_url='https://gorest.co.in/',
                  base_headers={'Authorization': "Bearer " + os.getenv('API_TOKEN', 'xxx')})


# Executed in sequence top-down
class TestCRUD:
    a_user = {
        "name": faker.name(),
        "email": faker.safe_email(),
        "gender": "male",
        "status": "active"
    }

    def test_create_user(self, api_client):
        response = (api_client
                    .post('/public/v1/users', json=self.a_user)
                    .assert_2xx()
                    .assert_response_time_less_than(seconds=3)
                    )
        response_body = response.parse_json()

        self.a_user['id'] = response.get_value('data.id')
        # or by regular data access
        # self.a_user['id'] = response_body['data']['id']

        assert_that(response_body['data']['id']).is_greater_than(1)
        assert_that(response_body['data']['name']).is_equal_to(self.a_user['name'])
        assert_that(response_body['data']['email']).is_equal_to(self.a_user['email'])
        assert_that(response_body['data']['gender']).is_equal_to('male')

    def test_update_user(self, api_client):
        print("==> Test 2", self.a_user)
        payload = {
            "status": "inactive",
            "email": "updated+" + self.a_user['email']
        }
        response = (api_client
                    .patch('/public/v1/users/' + str(self.a_user['id']), json=payload)
                    .assert_2xx()
                    .assert_response_time_less_than(seconds=3)
                    .parse_json()
                    )

        assert_that(response['data']['email']).is_equal_to("updated+" + self.a_user['email'])
        assert_that(response['data']['status']).is_equal_to("inactive")

    def test_delete_user(self, api_client):
        (api_client
         .delete('/public/v1/users/' + str(self.a_user['id']))
         .assert_status_code(204)
         .assert_response_time_less_than(seconds=3)
         )

        # re-delete
        response = (api_client
                    .delete("/public/v1/users/{}".format(self.a_user['id']))
                    .assert_status_code(404)
                    .assert_response_time_less_than(seconds=3)
                    .parse_json()
                    )
        assert_that(response['data']['message']).is_equal_to("Resource not found")
