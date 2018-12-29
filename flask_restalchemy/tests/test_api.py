from datetime import datetime

import pytest

from flask_restalchemy import Api
from flask_restalchemy.serialization import ModelSerializer, Field, NestedModelField
from flask_restalchemy.tests.sample_model import Employee, Company, Address


class EmployeeSerializer(ModelSerializer):

    password = Field(load_only=True)
    created_at = Field(dump_only=True)
    company_name = Field(dump_only=True)
    address = NestedModelField(Address)


@pytest.fixture(autouse=True)
def simple_api(flask_app):
    api = Api(flask_app)
    api.add_model(Company)
    api.add_model(Company, collection_name='alt_company')
    api.add_model(Employee, serializer_class=EmployeeSerializer)


@pytest.fixture(autouse=True)
def create_test_sample(db_session):
    company = Company(id=5, name='Terrans')
    emp1 = Employee(id=1, firstname='Jim', lastname='Raynor', company=company)
    emp2 = Employee(id=2, firstname='Sarah', lastname='Kerrigan', company=company)

    addr1 = Address(street="5 Av", number="943", city="Tarsonis")
    emp1.address = addr1

    db_session.add(company)
    db_session.add(emp1)
    db_session.add(emp2)
    db_session.commit()


def test_get(client, data_regression):
    resp = client.get('/employee/1')
    assert resp.status_code == 200
    serialized = resp.get_json()
    data_regression.check(serialized)
    assert 'password' not in serialized
    resp = client.get('/employee/10239')
    assert resp.status_code == 404


def test_get_collection(client, data_regression):
    resp = client.get('/employee')
    assert resp.status_code == 200
    serialized = resp.get_json()
    data_regression.check(serialized)


def test_post(client):
    post_data = {
        'id': 3,
        'firstname': 'Tychus',
        'lastname': 'Findlay',
        'admission': '2002-02-02T00:00:00+0300',
    }
    resp = client.post('/employee', data=post_data)
    assert resp.status_code == 201
    emp3 = Employee.query.get(3)
    assert emp3.id == 3
    assert emp3.firstname == 'Tychus'
    assert emp3.lastname == 'Findlay'
    assert emp3.admission == datetime(2002, 2, 2)


def test_post_default_serializer(client):
    resp = client.post('/company', data={'name': 'Mangsk Corp', })
    assert resp.status_code == 201


def test_put(client):
    resp = client.put('/employee/1', data={'firstname': 'Jimmy'})
    assert resp.status_code == 200
    emp3 = Employee.query.get(1)
    assert emp3.firstname == 'Jimmy'


def test_alternative_url(client):
    resp = client.get('/alt_company/5')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['name'] == 'Terrans'
