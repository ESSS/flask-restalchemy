import pytest
from flask import json

from flask_restalchemy import Api
from flask_restalchemy.serialization import ModelSerializer, Field, NestedModelField
from flask_restalchemy.tests.sample_model import Employee, Company, Department, Address


class EmployeeSerializer(ModelSerializer):

    password = Field(load_only=True)
    created_at = Field(dump_only=True)
    company_name = Field(dump_only=True)
    address = NestedModelField(Address)


@pytest.fixture(autouse=True)
def create_test_sample(db_session):
    company1 = Company(id=1, name='Protoss')
    company2 = Company(id=3, name='Terrans')
    emp1 = Employee(id=9, firstname='Jim', lastname='Raynor', company=company2)
    emp2 = Employee(id=3, firstname='Sarah', lastname='Kerrigan', company=company2)
    dept1 = Department(name='Marines')
    dept2 = Department(name='Heroes')
    emp1.departments.append(dept1)
    emp1.departments.append(dept2)

    db_session.add(company1)
    db_session.add(company2)
    db_session.add(dept1)
    db_session.add(dept2)
    db_session.add(emp1)
    db_session.add(emp2)
    db_session.commit()

@pytest.fixture(autouse=True)
def sample_api(flask_app):
    api = Api(flask_app)
    api.add_model(Company)
    api.add_model(Employee)
    api.add_relation(Company.employees, serializer_class=EmployeeSerializer)
    api.add_property(Employee, Employee, 'colleagues', serializer_class=EmployeeSerializer)
    api.add_relation(Employee.departments)
    return api

def test_delete_on_relation_with_secondary(client):
    jim = Employee.query.get(9)
    assert jim is not None
    assert len(jim.departments) > 0
    dep = jim.departments[0]

    sarah = Employee.query.get(3)
    assert jim is not None
    assert dep not in sarah.departments

    resp = client.get('/employee/3/departments')
    assert resp.status_code == 200

    resp = client.delete('/employee/3/departments/' + str(dep.id))
    assert resp.status_code == 404

    resp = client.delete('/employee/9/departments/'+str(dep.id))
    assert resp.status_code == 204


def test_property(client, data_regression):
    resp = client.get('/employee/9/colleagues')
    assert resp.status_code == 200
    response_data = resp.get_json()
    data_regression.check(response_data)

    resp = client.post('/employee/9/colleagues')
    assert resp.status_code == 405


def test_property_pagination(client):

    for i in range(20):
        client.post('/company/3/employees', data={'firstname': 'Jimmy {}'.format(i)})

    response = client.get('/employee/9/colleagues?order_by=id&limit=5')
    assert response.status_code == 200
    response_data = response.get_json()
    assert len(response_data) == 5
    assert response_data[0]['firstname'] == 'Sarah'

    response = client.get(
        '/employee/9/colleagues?filter={}'.format(json.dumps({"firstname": {"eq": "Sarah"}})))
    assert response.status_code == 200
    response_data = response.get_json()
    assert len(response_data) == 1
    assert 'firstname' in response_data[0]
    assert response_data[0]['firstname'] == 'Sarah'

    response = client.get('/employee/9/colleagues?page=1&per_page=10')
    assert response.status_code == 200
    response_data = response.get_json()
    assert len(response_data.get('results')) == 10
