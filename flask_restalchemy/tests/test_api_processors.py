import json

import pytest

from flask_restalchemy import Api
from flask_restalchemy.resources.processors import GET_ITEM, GET_COLLECTION, POST, PUT, DELETE
from flask_restalchemy.tests.sample_model import Employee, Company, Address, EmployeeSerializer

employee_serializer = EmployeeSerializer(Employee)

@pytest.fixture
def sample_api(flask_app):
    return Api(flask_app)

@pytest.fixture(autouse=True)
def create_test_sample(db_session):
    company = Company(id=5, name='Terrans')
    emp1 = Employee(id=1, firstname='Jim', lastname='Raynor', company=company)

    addr1 = Address(street="5 Av", number="943", city="Tarsonis")
    emp1.address = addr1

    db_session.add(company)
    db_session.add(emp1)
    db_session.commit()


def test_get_item_preprocessor(sample_api, client, mocker):
    preprocessor = mocker.Mock(return_value=None)
    sample_api.add_model(Employee, serializer_class=EmployeeSerializer, preprocessors={GET_ITEM: [preprocessor]})

    resp = client.get('/employee/1')
    assert resp.status_code == 200
    preprocessor.assert_called_once_with(resource_id='1')


def test_get_collection_preprocessor(sample_api, client, mocker):
    preprocessor = mocker.Mock(return_value=None)
    sample_api.add_model(Employee, serializer_class=EmployeeSerializer, preprocessors={GET_COLLECTION: [preprocessor]})

    resp = client.get('/employee')
    assert resp.status_code == 200
    preprocessor.assert_called_once_with()


def test_post_processors(sample_api, client, mocker):
    preprocessor = mocker.Mock(return_value=None)
    postprocessor = mocker.Mock(return_value=None)
    sample_api.add_model(Employee, serializer_class=EmployeeSerializer,
                         preprocessors={POST: [preprocessor]},
                         postprocessors={POST: [postprocessor]})

    data = {
        'firstname': 'Ana',
        'lastname': 'Queen'
    }
    resp = client.post('/employee', data=json.dumps(data))
    assert resp.status_code == 201
    preprocessor.assert_called_once_with(data=data)
    employee_id = resp.parsed_data['id']
    assert employee_id
    employee = Employee.query.get(employee_id)
    postprocessor.assert_called_once_with(result=employee_serializer.dump(employee))


def test_put_preprocessors(sample_api, client, mocker):
    preprocessor = mocker.Mock(return_value=None)
    postprocessor = mocker.Mock(return_value=None)
    sample_api.add_model(Employee, serializer_class=EmployeeSerializer,
                         preprocessors={PUT: [preprocessor]},
                         postprocessors={PUT: [postprocessor]})

    data = {
        'firstname': 'Ana',
        'lastname': 'Queen'
    }
    resp = client.put('/employee/1', data=json.dumps(data))
    assert resp.status_code == 200
    preprocessor.assert_called_once_with(resource_id='1', data=data)

    employee = Employee.query.get(1)
    postprocessor.assert_called_once_with(result=employee_serializer.dump(employee))


def test_delete_preprocessors(sample_api, client, mocker):
    preprocessor = mocker.Mock(return_value=None)
    postprocessor = mocker.Mock(return_value=None)
    sample_api.add_model(Employee, serializer_class=EmployeeSerializer,
                         preprocessors={DELETE: [preprocessor]},
                         postprocessors={DELETE: [postprocessor]})

    resp = client.delete('/employee/1')
    assert resp.status_code == 204
    preprocessor.assert_called_once_with(resource_id='1')
    postprocessor.assert_called_once_with(was_deleted=True)


def test_property_get_collection_processor(sample_api, client, mocker):
    preprocessor = mocker.Mock(return_value=None)
    sample_api.add_property(Employee, Employee, 'colleagues', serializer_class=EmployeeSerializer,
                            preprocessors={GET_COLLECTION: [preprocessor]})
    
    resp = client.get('/employee/1/colleagues')
    assert resp.status_code == 200
    preprocessor.assert_called_once_with(relation_id='1')


def test_relation_get_item_preprocessor(sample_api, client, mocker):
    preprocessor = mocker.Mock(return_value=None)
    sample_api.add_relation(Company.employees, serializer_class=EmployeeSerializer, preprocessors={GET_ITEM: [preprocessor]})

    resp = client.get('/company/5/employees/1')
    assert resp.status_code == 200
    preprocessor.assert_called_once_with(relation_id='5', resource_id='1')


def test_relation_get_collection_preprocessor(sample_api, client, mocker):
    preprocessor = mocker.Mock(return_value=None)
    sample_api.add_relation(Company.employees, serializer_class=EmployeeSerializer, preprocessors={GET_COLLECTION: [preprocessor]})

    resp = client.get('/company/5/employees')
    assert resp.status_code == 200
    preprocessor.assert_called_once_with(relation_id='5')


def test_relation_post_processors(sample_api, client, mocker):
    preprocessor = mocker.Mock(return_value=None)
    postprocessor = mocker.Mock(return_value=None)
    sample_api.add_relation(Company.employees, serializer_class=EmployeeSerializer,
                         preprocessors={POST: [preprocessor]},
                         postprocessors={POST: [postprocessor]})

    data = {
        'firstname': 'Ana',
        'lastname': 'Queen'
    }
    resp = client.post('/company/5/employees', data=json.dumps(data))
    assert resp.status_code == 201
    preprocessor.assert_called_once_with(relation_id='5', data=data)
    employee_id = resp.parsed_data['id']
    assert employee_id
    employee = Employee.query.get(employee_id)
    postprocessor.assert_called_once_with(result=employee_serializer.dump(employee))


def test_relation_put_preprocessors(sample_api, client, mocker):
    preprocessor = mocker.Mock(return_value=None)
    postprocessor = mocker.Mock(return_value=None)
    sample_api.add_relation(Company.employees, serializer_class=EmployeeSerializer,
                         preprocessors={PUT: [preprocessor]},
                         postprocessors={PUT: [postprocessor]})

    data = {
        'firstname': 'Ana',
        'lastname': 'Queen'
    }
    resp = client.put('/company/5/employees/1', data=json.dumps(data))
    assert resp.status_code == 200
    preprocessor.assert_called_once_with(relation_id='5', resource_id='1', data=data)

    employee = Employee.query.get(1)
    postprocessor.assert_called_once_with(result=employee_serializer.dump(employee))


def test_relation_delete_preprocessors(sample_api, client, mocker):
    preprocessor = mocker.Mock(return_value=None)
    postprocessor = mocker.Mock(return_value=None)
    sample_api.add_relation(Company.employees, serializer_class=EmployeeSerializer,
                         preprocessors={DELETE: [preprocessor]},
                         postprocessors={DELETE: [postprocessor]})

    resp = client.delete('/company/5/employees/1')
    assert resp.status_code == 204
    preprocessor.assert_called_once_with(relation_id='5', resource_id='1')
    postprocessor.assert_called_once_with(was_deleted=True)