from flask_restalchemy import Api
from flask_restalchemy.tests.sample_model import Company, Address


def test_api_creation(client, flask_app):
    api = Api(flask_app)
    api.add_model(Company)
    api.add_model(Company, collection_name='extern_company')

    assert client.get('/company').status_code == 200
    assert client.get('/extern_company').status_code == 200
