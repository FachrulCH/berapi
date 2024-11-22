from berapi.apy import berAPI


def test_get_user():
    """Test get user"""
    response = berAPI().get("https://jsonplaceholder.typicode.com/users/1")
    assert response.status_code == 200

def test_get_user_failed():
    """Test get user"""
    response = berAPI().get("https://jsonplaceholder.typicode.com/users/1")
    assert response.status_code == 404