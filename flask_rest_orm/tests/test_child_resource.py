import pytest

from flask_rest_orm import Api
from flask_rest_orm.tests.sample_model import Employee, Company, EmployeeSerializer, Department


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
    api.add_relation(Company.employees, serializer=EmployeeSerializer())
    return api

def test_get_collection(client):
    resp = client.get('/company/3/employee')
    assert resp.status_code == 200
    assert len(resp.parsed_data) == 2
    sarah = resp.parsed_data[0]
    assert sarah['firstname'] == 'Sarah'
    assert sarah['lastname'] == 'Kerrigan'
    jim = resp.parsed_data[1]
    assert jim['firstname'] == 'Jim'
    assert jim['lastname'] == 'Raynor'

def test_post(client):
    resp = client.post('/company/3/employee', data={'id': 7, 'firstname': 'Tychus', 'lastname': 'Findlay'})
    assert resp.status_code == 201
    thychus = Employee.query.get(7)
    assert thychus.company_name == 'Terrans'

def test_get(client):
    resp = client.get('/company/3/employee/9')
    assert resp.status_code == 200
    obtained = resp.parsed_data
    assert obtained['firstname'] == 'Jim'
    assert obtained['lastname'] == 'Raynor'
    assert obtained['company_name'] == 'Terrans'
    # Query a valid resource ID, but with a wrong related ID
    resp = client.get('/company/4/employee/9')
    assert resp.status_code == 404

def test_put(client):
    new_name = 'Jimmy'
    resp = client.put('/company/3/employee/9', data={'firstname': new_name})
    assert resp.status_code == 200
    jim = Employee.query.get(9)
    assert jim.firstname == new_name

def test_delete(client):
    jim = Employee.query.get(9)
    assert jim is not None

    resp = client.delete('/company/3/employee/9')
    assert resp.status_code == 204
