import pytest

from flask_restalchemy import Api
from flask_restalchemy.tests.sample_model import Employee, Company, EmployeeSerializer, Department


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
    api.add_relation(Company.employees, serializer_class=EmployeeSerializer)
    api.add_property(Employee, Employee, 'colleagues', serializer_class=EmployeeSerializer)
    api.add_relation(Employee.departments)
    return api

def test_get_collection(client):
    resp = client.get('/company/3/employees')
    assert resp.status_code == 200
    assert len(resp.parsed_data) == 2
    sarah = resp.parsed_data[0]
    assert sarah['firstname'] == 'Sarah'
    assert sarah['lastname'] == 'Kerrigan'
    jim = resp.parsed_data[1]
    assert jim['firstname'] == 'Jim'
    assert jim['lastname'] == 'Raynor'

def test_post(client):
    resp = client.post('/company/3/employees', data={'id': 7, 'firstname': 'Tychus', 'lastname': 'Findlay'})
    assert resp.status_code == 201
    thychus = Employee.query.get(7)
    assert thychus.company_name == 'Terrans'

def test_get(client):
    resp = client.get('/company/3/employees/9')
    assert resp.status_code == 200
    obtained = resp.parsed_data
    assert obtained['firstname'] == 'Jim'
    assert obtained['lastname'] == 'Raynor'
    assert obtained['company_name'] == 'Terrans'
    # Query a valid resource ID, but with a wrong related ID
    resp = client.get('/company/4/employees/9')
    assert resp.status_code == 404

def test_put(client):
    new_name = 'Jimmy'
    resp = client.put('/company/3/employees/9', data={'firstname': new_name})
    assert resp.status_code == 200
    jim = Employee.query.get(9)
    assert jim.firstname == new_name

def test_delete(client):
    jim = Employee.query.get(9)
    assert jim is not None

    resp = client.delete('/company/3/employees/9')
    assert resp.status_code == 204


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


def test_property(client):
    resp = client.get('/employee/9/colleagues')
    assert resp.status_code == 200
    assert len(resp.parsed_data) == 2
    assert resp.parsed_data[0]['firstname'] == 'Sarah'
    assert resp.parsed_data[1]['firstname'] == 'Jim'

    resp = client.post('/employee/9/colleagues')
    assert resp.status_code == 405
