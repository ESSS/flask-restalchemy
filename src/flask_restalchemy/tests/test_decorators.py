from functools import wraps

from flask import request
from werkzeug.exceptions import abort

from flask_restalchemy import Api
from flask_restalchemy.tests.sample_model import Address, Company
from flask_restalchemy.resources.resources import ViewFunctionResource


def auth_required(func):
    @wraps(func)
    def authenticate(*args, **kw):
        if not request.headers.get("auth"):
            abort(403)
        return func(*args, **kw)

    return authenticate


def post_hook(func):
    @wraps(func)
    def authenticate(*args, **kw):
        response = func(*args, **kw)
        if isinstance(response, str):
            response = response + "post_hook"
        return response

    return authenticate


def test_resource_decorators(client, flask_app):
    api = Api(flask_app)
    api.add_model(Company, request_decorators=[auth_required])
    api.add_model(Address)

    assert client.get("/company").status_code == 403
    assert client.post("/company", data={"name": "Terran"}).status_code == 403
    assert client.get("/address").status_code == 200
    assert client.post("/address", data={"street": "5 Av"}).status_code == 201

    resp = client.post(
        "/company", data={"id": 2, "name": "Protoss"}, headers={"auth": True}
    )
    assert resp.status_code == 201
    assert client.get("/company/2").status_code == 403
    assert client.get("/company/2", headers={"auth": True}).status_code == 200


def test_api_decorators(client, flask_app):
    api = Api(flask_app, request_decorators=[auth_required])
    api.add_model(Company)
    api.add_model(Address, request_decorators=[post_hook])
    assert client.get("/company").status_code == 403

    assert (
        client.post(
            "/company", data={"name": "Terran"}, headers={"auth": True}
        ).status_code
        == 201
    )
    assert client.get("/company", headers={"auth": True}).status_code == 200

    response = client.post("/address", headers={"auth": True})


def test_add_rule_decorators(client, flask_app):
    def hello_world():
        return "hello world"

    api = Api(flask_app, request_decorators=[auth_required])
    api.add_url_rule(
        "/", "index", hello_world, request_decorators={"POST": [post_hook]}
    )
    resp = client.get("/")
    assert resp.status_code == 403
    resp = client.post("/", headers={"auth": True})
    assert resp.status_code == 200
    assert resp.data == b"hello worldpost_hook"
