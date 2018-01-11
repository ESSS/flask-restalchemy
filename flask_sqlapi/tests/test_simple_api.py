import json

import pytest
from flask import Flask
from flask_sqlapi.resources import Api

from flask_sqlapi.resources.resourcebase import resource_collection_factory, resource_item_factory
from flask_sqlapi.tests.sample_model import Employee, db


@pytest.fixture(scope="session")
def flask_app():
    app = Flask('flask_sqlapi_sample')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    db.init_app(app)
    with app.app_context():
        yield app

@pytest.fixture(scope="session")
def sample_api(flask_app):
    api = Api(flask_app)
    api.add_model(Employee)
    return api


@pytest.fixture(scope="function")
def db_session(flask_app):
    db.create_all()
    yield db.session
    db.session.remove()
    db.drop_all()


@pytest.fixture
def test_client(flask_app):
    from werkzeug.wrappers import BaseResponse

    def response_wrapper(*args):
        resp = BaseResponse(*args)
        if resp.status_code in [200, 201]:
            resp.parsed_data = json.loads(resp.data.decode('utf-8'))
        return resp

    test_client = flask_app.test_client()
    test_client.response_wrapper = response_wrapper
    return test_client


@pytest.fixture(autouse=True)
def register_model_and_api(db_session, sample_api):
    emp1 = Employee(id=1, firstname='Odete', lastname='Roithmann')
    emp2 = Employee(id=2, firstname='Eduardo', lastname='Figueroa')
    db_session.add(emp1)
    db_session.add(emp2)
    db_session.commit()

# noinspection PyShadowingNames
def test_get(test_client):
    resp = test_client.get('/employee/1')
    assert resp.status_code == 200
    expected_employee = Employee.query.get(1)
    assert resp.parsed_data['firstname'] == expected_employee.firstname
    assert resp.parsed_data['lastname'] == expected_employee.lastname


# noinspection PyShadowingNames
def test_get_collection(test_client):
    resp = test_client.get('/employee')
    assert resp.status_code == 200
    assert len(resp.parsed_data) == 2
    for i, expected_employee in enumerate(Employee.query.all()):
        assert resp.parsed_data[i]['firstname'] == expected_employee.firstname
        assert resp.parsed_data[i]['lastname'] == expected_employee.lastname
