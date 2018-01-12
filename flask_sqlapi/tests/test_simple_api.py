import json

import pytest
from flask import Flask
from marshmallow import fields
from marshmallow_sqlalchemy import ModelSchema

from flask_sqlapi.resources import Api
from flask_sqlapi.tests.sample_model import Employee, db, Company


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

    class EmployeeSerializer(ModelSchema):
        class Meta:
            model = Employee

        password = fields.Str(load_only=True)
        created_at = fields.DateTime(dump_only=True)
        company_name = fields.Str(dump_only=True)

    api.add_model(Company)
    api.add_model(Employee, serializer=EmployeeSerializer())
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
    company = Company(name='Terrans')
    emp1 = Employee(id=1, firstname='Jim', lastname='Raynor', company=company)
    emp2 = Employee(id=2, firstname='Sarah', lastname='Kerrigan', company=company)
    db_session.add(company)
    db_session.add(emp1)
    db_session.add(emp2)
    db_session.commit()

# noinspection PyShadowingNames
def test_get(test_client):
    resp = test_client.get('/employee/1')
    assert resp.status_code == 200
    expected_employee = Employee.query.get(1)
    serialized = resp.parsed_data
    assert serialized['firstname'] == expected_employee.firstname
    assert serialized['lastname'] == expected_employee.lastname
    assert serialized['created_at'] == '2000-01-01T00:00:00+00:00'
    assert 'password' not in serialized
    assert serialized['company'] == expected_employee.company_id
    assert serialized['company_name'] == Company.query.get(expected_employee.company_id).name


# noinspection PyShadowingNames
def test_get_collection(test_client):
    resp = test_client.get('/employee')
    assert resp.status_code == 200
    assert len(resp.parsed_data) == 2
    for i, expected_employee in enumerate(Employee.query.all()):
        serialized = resp.parsed_data[i]
        assert serialized['firstname'] == expected_employee.firstname
        assert serialized['lastname'] == expected_employee.lastname
        assert 'password' not in serialized


def test_post(test_client):
    resp = test_client.post('/employee', data={'id': 3, 'firstname': 'Tychus', 'lastname': 'Findlay'})
    assert resp.status_code == 201
    emp3 = Employee.query.get(3)
    assert emp3.id == 3
    assert emp3.firstname == 'Tychus'
    assert emp3.lastname == 'Findlay'

    resp = test_client.post('/employee', data={'firstname': 'Mangsk', 'created_at': '2002-02-02T00:00'})



def test_put(test_client):
    resp = test_client.put('/employee/2', data={'id': 2, 'firstname': 'Jimmy'})
    assert resp.status_code == 200
    emp3 = Employee.query.get(2)
    assert emp3.firstname == 'Jimmy'
