import datetime

import pytest

from flask_rest_orm.serialization.modelserializer import ModelSerializer, Field, NestedModelField, NestedAttributesField
from flask_rest_orm.tests.sample_model import Employee, Company, Address


class EmployeeSerializer(ModelSerializer):

    password = Field(load_only=True)
    created_at = Field(dump_only=True)
    address = NestedModelField(declarative_class=Address)
    company = NestedAttributesField(['name'], dump_only=True)


class CompanySerializer(ModelSerializer):

    employees = NestedAttributesField(['firstname', 'lastname', 'email'])


@pytest.fixture(autouse=True)
def seed_data(db_session):
    company = Company(id=5, name='Terrans')
    emp1 = Employee(id=1, firstname='Jim', lastname='Raynor', company=company)
    emp2 = Employee(id=2, firstname='Sarah', lastname='Kerrigan', company=company)
    emp3 = Employee(id=3, firstname='Tychus', lastname='Findlay')

    addr1 = Address(street="5 Av", number="943", city="Tarsonis")
    emp1.address = addr1

    db_session.add_all([company, emp1, emp2, emp3])
    db_session.commit()

def test_serialization():
    emp = Employee.query.get(1)
    serializer = EmployeeSerializer(Employee)
    serialized_dict = serializer.dump(emp)
    assert serialized_dict["firstname"] == emp.firstname
    assert serialized_dict["lastname"] == emp.lastname
    assert serialized_dict["created_at"] == "2000-01-02T00:00:00"
    assert serialized_dict["company_id"] == 5
    assert serialized_dict["company"]["name"] == "Terrans"

    assert "password" not in serialized_dict
    address = serialized_dict["address"]

    assert address["id"] == 1
    assert address["number"] == "943"
    assert address["street"] == "5 Av"

def test_deserialization():
    serializer = EmployeeSerializer(Employee)
    serialized = {
        "firstname": "John",
        "lastname": "Doe",
        "company_id": 5,
        "admission": "2004-06-01T00:00:00",
        "address": {
            "number": "245",
            "street": "6 Av",
            "zip": "88088-000"
        },
        # Dump only field, must be ignored
        "created_at": "2023-12-21T00:00:00",
    }
    loaded_emp = serializer.load(serialized)
    assert loaded_emp.firstname == serialized["firstname"]
    assert loaded_emp.admission == datetime.datetime(2004, 6, 1, 0, 0)
    assert loaded_emp.company_id == serialized["company_id"]
    assert loaded_emp.address.number == "245"
    assert loaded_emp.created_at is None

def test_nested():
    serializer = CompanySerializer(Company)
    company = Company.query.get(5)
    serialized = serializer.dump(company)
    assert serialized['name'] == 'Terrans'
    assert len(serialized['employees']) == 2
    assert serialized['employees'][0]['firstname'] == 'Jim'
    assert serialized['employees'][1]['lastname'] == 'Kerrigan'
    assert 'password' not in serialized['employees'][0].keys()

def test_empty_nested():
    serializer = EmployeeSerializer(Employee)
    serialized = serializer.dump(Employee.query.get(3))
    assert serialized['company'] is None
    model = serializer.load(serialized)
    assert model.company is None
