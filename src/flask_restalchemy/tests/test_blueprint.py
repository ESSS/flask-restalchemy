import pytest
from flask import Blueprint
from flask_restalchemy import Api
from flask_restalchemy.tests.sample_model import Company, Employee


@pytest.fixture(autouse=True)
def blueprint(flask_app):
    test_blueprint = Blueprint("test", __name__, url_prefix="/bp")
    api = Api(test_blueprint)
    api.add_model(Company)
    api.add_model(Employee)
    flask_app.register_blueprint(test_blueprint)


def test_blueprint_api(client):
    resp = client.post("/bp/company", data={"name": "Mangsk Corp"})
    assert resp.status_code == 201

    resp = client.post("/bp/company", data={"name": "Mangsk Corp"})
    assert resp.status_code == 201
