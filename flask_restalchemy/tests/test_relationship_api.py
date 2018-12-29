import pytest

from flask_restalchemy import Api
from flask_restalchemy.tests.sample_model import Employee, Company, Address


@pytest.fixture(autouse=True)
def sample_database(db_session):
    company = Company(id=5, name='Terrans')
    emp1 = Employee(id=1, firstname='Jim', lastname='Raynor', company=company)
    emp2 = Employee(id=2, firstname='Sarah', lastname='Kerrigan', company=company)

    db_session.add(company)
    db_session.add(emp1)
    db_session.add(emp2)
    db_session.commit()


@pytest.fixture(autouse=True)
def simple_api(flask_app):
    api = Api(flask_app)
    api.add_model(Company)
    api.add_model(Employee)
    api.add_relation(Company.employees)
    return api


def test_get_collection(client, data_regression):
    resp = client.get('/company/5/employees')
    assert resp.status_code == 200
    assert resp.is_json
    data = resp.get_json()
    data_regression.check(data)


def test_get_item(client, data_regression):
    resp = client.get('/company/5/employees/2')
    assert resp.status_code == 200
    assert resp.is_json
    data = resp.get_json()
    data_regression.check(data)

    assert client.get('/company/5/employees/999').status_code == 404


def test_post_item(client):
    post_data = {
        'firstname': 'Tychus',
        'lastname': 'Findlay',
        'admission': '2002-02-02T00:00:00+0300',
    }
    resp = client.post('/company/5/employees', data=post_data)
    assert resp.status_code == 201
    assert resp.is_json
    saved_id = resp.get_json()['id']

    new_employee = Employee.query.get(saved_id)
    assert new_employee.firstname == 'Tychus'
    assert new_employee.company.id == 5


def test_put_item(client):
    resp = client.put('/company/5/employees/2', data={'lastname': 'K.'})
    assert resp.status_code == 200

    sarah = Employee.query.get(2)
    assert sarah.lastname == 'K.'


def test_delete_item(client):
    company = Company.query.get(5)
    assert [emp.id for emp in company.employees] == [1, 2]

    resp = client.delete('/company/5/employees/2')
    assert resp.status_code == 204
    assert [emp.id for emp in company.employees] == [1]

    assert client.delete('/company/5/employees/999').status_code == 404


def test_post_append_existent(client):
    resp = client.post('/employee', data={'firstname': 'Tychus', 'lastname': 'Findlay'})
    assert resp.status_code == 201
    data = resp.get_json()
    empl_id = data['id']
    thychus = Employee.query.get(empl_id)
    assert thychus.company_name is None

    resp = client.post('/company/5/employees', data={'id': empl_id})
    assert resp.status_code == 200

    thychus = Employee.query.get(empl_id)
    assert thychus.company_name == 'Terrans'

    resp = client.post('/company/3/employees', data={'id': 1000})
    assert resp.status_code == 404
