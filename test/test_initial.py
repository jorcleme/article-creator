def test_index(test_client):
    """
    Testcase for positive scenario of index API
    """
    response = test_client.get('/')
    assert response.status_code == 200
    assert response.json()['message'] == 'Hello Codeshift!'


def test_not_existed_endpoint(test_client):
    """
    Testcase for 404, calling the endpoint for which
    no API implemented
    """
    response = test_client.get('/invalid/endpoint')
    assert response.status_code == 404
    assert response.json()['detail'] == 'Not Found'


def test_invalid_method(test_client):
    """
    Testcase for 405, calling the index API with POST method
    instead of GET method
    """
    response = test_client.post('/', json={'field': 'value'})
    assert response.status_code == 405
    assert response.json()['detail'] == 'Method Not Allowed'
