from datetime import datetime
import json

import pytest

from flask_restalchemy import Api
from flask_restalchemy.tests.sample_model import Employee, Company, Address, EmployeeSerializer


@pytest.fixture(autouse=True)
def sample_api(flask_app):
    api = Api(flask_app)
    api.add_model(Company)
    api.add_model(Employee, serializer_class=EmployeeSerializer)
    api.add_relation(Company.employees, serializer_class=EmployeeSerializer)
    return api

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

# noinspection PyShadowingNames
def test_get(client):
    resp = client.get('/employee/1')
    assert resp.status_code == 200
    expected_employee = Employee.query.get(1)
    serialized = resp.parsed_data
    assert serialized['firstname'] == expected_employee.firstname
    assert serialized['lastname'] == expected_employee.lastname
    assert serialized['created_at'] == '2000-01-02T00:00:00'
    assert 'password' not in serialized
    assert serialized['company_id'] == expected_employee.company_id
    assert serialized['company_name'] == Company.query.get(expected_employee.company_id).name
    expected_address = expected_employee.address
    assert serialized['address']['city'] == expected_address.city
    assert serialized['address']['number'] == expected_address.number

    resp = client.get('/employee/10239')
    assert resp.status_code == 404

def test_get_collection(client):
    resp = client.get('/employee')
    assert resp.status_code == 200
    assert len(resp.parsed_data) == 2
    for i, expected_employee in enumerate(Employee.query.all()):
        serialized = resp.parsed_data[i]
        assert serialized['firstname'] == expected_employee.firstname
        assert serialized['lastname'] == expected_employee.lastname
        assert 'password' not in serialized

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

def test_filter(client):
    for i in range(20):
        client.post('/company', data={ 'name': 'Terrans {}'.format(i), 'location': 'Location {}'.format(20 - i)})

    response = client.get('/company')
    dataList = response.parsed_data
    assert len(dataList) == 21

    response = client.get('/company?limit=5')
    dataList = response.parsed_data
    assert len(dataList) == 5

    response = client.get('/company?filter={}'.format(json.dumps({"name": "Terrans 1"})))
    dataList = response.parsed_data
    assert len(dataList) == 1

    response = client.get('/company?filter={}'.format(json.dumps({"name": {"eq": "Terrans 1"}})))
    dataList = response.parsed_data
    assert len(dataList) == 1


    response = client.get('/company?filter={}'.format(json.dumps({
        "$or": {
            "name": {"eq": "Terrans 1"},
            "location": "Location 1"
        }
    })))
    dataList = response.parsed_data
    assert len(dataList) == 2

    # test if AND is the default Logical Operator
    response = client.get('/company?filter={}'.format(json.dumps({
        "name": {"eq": "Terrans 1"},
        "location": "Location 1"
    })))
    dataList = response.parsed_data
    assert len(dataList) == 0

    response = client.get('/company?filter={}'.format(json.dumps({
        "$and": {
            "name": {"eq": "Terrans 10"},
            "location": "Location 10"
        }
    })))
    dataList = response.parsed_data
    assert len(dataList) == 1

    response = client.get('/company?filter={}'.format(json.dumps({"name": { "in": ["Terrans 1", "Terrans 2"]}})))
    dataList = response.parsed_data
    assert len(dataList) == 2

    response = client.get('/company?filter={}'.format(json.dumps({"name": {"endswith": '9'}})))
    dataList = response.parsed_data
    assert len(dataList) == 2

    response = client.get('/company?filter={}'.format(json.dumps({"name": {"startswith": 'Terr'}})))
    dataList = response.parsed_data
    assert len(dataList) == 21

    response = client.get('/company?limit=5&filter={}'.format(json.dumps({"name": {"startswith": 'Terr'}})))
    dataList = response.parsed_data
    assert len(dataList) == 5

    with pytest.raises(ValueError, message='Unknown operator unknown_operator'):
        client.get('/company?filter={}'.format(json.dumps({"name": {"unknown_operator": 'Terr'}})))


def test_pagination(client):
    for i in range(20):
        client.post('/company', data={ 'name': 'Terrans {}'.format(i)})

    response = client.get('/company?page=1&per_page=50')
    dataList = response.parsed_data
    assert len(dataList.get('results')) == 21

    response = client.get('/company?page=1&per_page=5')
    dataList = response.parsed_data
    assert len(dataList.get('results')) == 5

    response = client.get('/company?page=5&per_page=5')
    dataList = response.parsed_data
    assert len(dataList.get('results')) == 1


def test_pagination(client):
    response = client.post('/company', data={'name': 'Terrans 1'})
    assert response.status_code == 201
    company_id = response.parsed_data['id']

    for i in range(20):
        client.post('/company/{}/employees'.format(company_id), data={'firstname': 'Jimmy {}'.format(i)})

    response = client.get('/company/{}/employees?filter={}'.format(company_id, json.dumps({"firstname": {"eq": "Jimmy 1"}})))
    assert response.status_code == 200
    dataList = response.parsed_data
    assert len(dataList) == 1
    assert 'firstname' in dataList[0]
    assert dataList[0]['firstname'] == 'Jimmy 1'

    response = client.get('/company/{}/employees?page=1&per_page=5'.format(company_id))
    assert response.status_code == 200
    dataList = response.parsed_data
    assert len(dataList.get('results')) == 5
