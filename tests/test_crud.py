import os

from assertpy import assert_that
from faker import Faker

from berapi.apy import berAPI

faker = Faker()
a_user = {
    "name": faker.name(),
    "email": faker.safe_email(),
    "gender": "male",
    "status": "active"
}

# Executed in sequence top-down

def test_create_user():
    header = {'Authorization': "Bearer " + os.getenv('API_TOKEN', 'ABC')}

    response = (berAPI()
                .post('https://gorest.co.in/public/v1/users', headers=header, json=a_user)
                .assert_2xx()
                .assert_response_time_less_than(seconds=3)
                .parse_json()
                )
    a_user['id'] = response['data']['id']
    assert_that(response['data']['id']).is_greater_than(1)
    assert_that(response['data']['name']).is_equal_to(a_user['name'])
    assert_that(response['data']['email']).is_equal_to(a_user['email'])
    assert_that(response['data']['gender']).is_equal_to('male')


def test_update_user():
    print("==> Test 2", a_user)
    payload = {
        "status": "inactive",
        "email": "updated+" + a_user['email']
    }
    header = {'Authorization': "Bearer " + os.getenv('API_TOKEN', 'ABC')}

    response = (berAPI()
                .patch('https://gorest.co.in/public/v1/users/' + str(a_user['id']), headers=header, json=payload)
                .assert_2xx()
                .assert_response_time_less_than(seconds=3)
                .parse_json()
                )

    assert_that(response['data']['email']).is_equal_to("updated+" + a_user['email'])
    assert_that(response['data']['status']).is_equal_to("inactive")


def test_delete_user():
    header = {'Authorization': "Bearer " + os.getenv('API_TOKEN', 'ABC')}
    (berAPI()
     .delete('https://gorest.co.in/public/v1/users/' + str(a_user['id']), headers=header)
     .assert_status_code(204)
     .assert_response_time_less_than(seconds=3)
     )

    # re-delete
    response = (berAPI()
                .delete('https://gorest.co.in/public/v1/users/' + str(a_user['id']), headers=header)
                .assert_status_code(404)
                .assert_response_time_less_than(seconds=3)
                .parse_json()
                )
    assert_that(response['data']['message']).is_equal_to("Resource not found")