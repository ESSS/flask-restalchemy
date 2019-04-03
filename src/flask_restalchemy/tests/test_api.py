import json
from datetime import datetime

import pytest
from flask_restalchemy.serialization import ModelSerializer, Field, NestedModelField, NestedModelListField

from flask_restalchemy import Api
from flask_restalchemy.tests.sample_model import Employee, Company, Address, Contact, ContactType


class EmployeeSerializer(ModelSerializer):

    password = Field(load_only=True)
    created_at = Field(dump_only=True)
    company_name = Field(dump_only=True)
    address = NestedModelField(Address)
    contacts = NestedModelListField(Contact)


@pytest.fixture(autouse=True)
def sample_api(flask_app):
    api = Api(flask_app)
    api.add_model(Company)
    api.add_model(Company, view_name='alt_company')
    api.add_model(Employee, serializer_class=EmployeeSerializer)

@pytest.fixture(autouse=True)
def create_test_sample(db_session):
    contact_type1 = ContactType(label='Phone')
    contact_type2 = ContactType(label='Email')

    company = Company(id=5, name='Terrans')
    emp1 = Employee(id=1, firstname='Jim', lastname='Raynor', company=company)
    emp2 = Employee(id=2, firstname='Sarah', lastname='Kerrigan', company=company)

    addr1 = Address(street="5 Av", number="943", city="Tarsonis")
    emp1.address = addr1

    db_session.add(contact_type1)
    db_session.add(contact_type2)
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
    contacts = [
        { 'type_id': 1, 'value': '0000-0000' },
        { 'type_id': 2, 'value': 'test@mail.co' }
    ]
    post_data = {
        'id': 3,
        'firstname': 'Tychus',
        'lastname': 'Findlay',
        'admission': '2002-02-02T00:00:00+0300',
        'contacts': contacts
    }
    resp = client.post('/employee', data=json.dumps(post_data))
    assert resp.status_code == 201
    emp3 = Employee.query.get(3)
    contact1 = emp3.contacts[0]
    assert emp3.id == 3
    assert emp3.firstname == 'Tychus'
    assert emp3.lastname == 'Findlay'
    assert emp3.admission == datetime(2002, 2, 2)
    assert contact1
    assert contact1.value == '0000-0000'


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


def test_url_rule(flask_app, client):

    def hello_world(name):
        return f'hello {name}'

    api = Api(flask_app)
    api.add_url_rule('/<string:name>', 'index', hello_world)
    resp = client.get('/raynor')
    assert resp.status_code == 200
    assert resp.data == b'hello raynor'


def test_http_verbs(flask_app, client):

    def get(*args, **kwargs):
        return 'ping'

    def post(*args, **kwargs):
        return 'ping'

    def get_post(*args, **kwargs):
        return 'ping'

    def put_del(*args, **kwargs):
        return 'ping'

    api = Api(flask_app)
    api.register_view(get, '/get_col_only', methods=['GET_COLLECTION'])
    resp = client.get('/get_col_only')
    assert resp.status_code == 200
    resp = client.post('/get_col_only')
    assert resp.status_code == 405
    resp = client.put('/get_col_only')
    assert resp.status_code == 405
    resp = client.delete('/get_col_only')
    assert resp.status_code == 405

    api.register_view(post, '/post_only', methods=['POST'])
    resp = client.get('/post_only')
    assert resp.status_code == 405
    resp = client.post('/post_only')
    assert resp.status_code == 200
    resp = client.put('/post_only')
    assert resp.status_code == 405
    resp = client.delete('/post_only')
    assert resp.status_code == 405

    api.register_view(get_post, '/post_getcol_only', methods=['GET_COLLECTION', 'POST'])
    resp = client.get('/post_getcol_only')
    assert resp.status_code == 200
    resp = client.post('/post_getcol_only')
    assert resp.status_code == 200
    resp = client.put('/post_getcol_only')
    assert resp.status_code == 405
    resp = client.delete('/post_getcol_only')
    assert resp.status_code == 405

    api.register_view(put_del, '/put_del_only', methods=['PUT', 'DELETE'])
    resp = client.get('/put_del_only/1')
    assert resp.status_code == 405
    resp = client.post('/put_del_only/1')
    assert resp.status_code == 405
    resp = client.put('/put_del_only/1')
    assert resp.status_code == 200
    resp = client.delete('/put_del_only/1')
    assert resp.status_code == 200