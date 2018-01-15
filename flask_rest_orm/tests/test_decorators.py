from functools import wraps

from flask_restful import abort, request

from flask_rest_orm.resources import Api
from flask_rest_orm.tests.sample_model import Address, Company


def auth_required(func):
    @wraps(func)
    def authenticate(*args, **kw):
        if not request.headers.get('auth'):
            abort(403)
        return func(*args, **kw)

    return authenticate


def test_resource_decorators(client, flask_app):
    api = Api(flask_app)
    api.add_model(Company)
    api.add_model(Address, request_decorators=[auth_required])

    assert client.get('/address').status_code == 403
    assert client.post('/address', data={'steet': '5 Av'}).status_code == 403
    assert client.get('/company', data={'name': 'Terran'}).status_code == 200
    assert client.post('/company', data={'name': 'Terran'}).status_code == 201

    assert client.post('/address', data={'id': 2, 'steet': '5 Av'}, headers={'auth': True}).status_code == 201
    assert client.post('/company', data={'name': 'Terran'}, headers={'auth': True}).status_code == 201
    assert client.get('/address/2').status_code == 403
    assert client.get('/address/2', headers={'auth': True}).status_code == 200


def test_api_decorators(client, flask_app):
    global AUTHENTICATED
    api = Api(flask_app, request_decorators=[auth_required])
    api.add_model(Company)
    assert client.get('/company').status_code == 403

    assert client.post('/company', data={'name': 'Terran'}, headers={'auth': True}).status_code == 201
    assert client.get('/company', headers={'auth': True}).status_code == 200
