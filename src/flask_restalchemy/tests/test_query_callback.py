import pytest
from flask import json, request
from flask_restalchemy.serialization import ModelSerializer, Field, NestedModelField

from flask_restalchemy import Api
from flask_restalchemy.tests.sample_model import (
    Employee,
    Company,
    Department,
    Address,
    employee_department,
    db,
)


class EmployeeSerializer(ModelSerializer):

    password = Field(load_only=True)
    created_at = Field(dump_only=True)
    company_name = Field(dump_only=True)
    address = NestedModelField(Address)


@pytest.fixture(autouse=True)
def create_test_sample(db_session):
    protoss = Company(id=1, name="Protoss")
    zerg = Company(id=2, name="Zerg")
    terrans = Company(id=3, name="Terrans")

    basic = Department(id=100, name="Basic")
    heroes = Department(id=200, name="Heroes")

    raynor = Employee(
        id=11,
        firstname="Jim",
        lastname="Raynor",
        company=terrans,
        departments=[basic, heroes],
    )
    marine = Employee(
        id=12, firstname="John", lastname="Doe", company=terrans, departments=[basic]
    )
    kerrigan = Employee(
        id=13,
        firstname="Sarah",
        lastname="Kerrigan",
        company=terrans,
        departments=[heroes],
    )

    tassadar = Employee(
        id=21,
        firstname="Tassadar",
        lastname="The Warrior",
        company=protoss,
        departments=[heroes],
    )
    zealot = Employee(
        id=22, firstname="Aiur", lastname="Zealot", company=protoss, departments=[basic]
    )

    zergling = Employee(
        id=31, firstname="Rush", lastname="Lings", company=zerg, departments=[basic]
    )

    db_session.add_all([protoss, zerg, terrans])
    db_session.add_all([basic, heroes])
    db_session.add_all([raynor, kerrigan, marine, tassadar, zealot, zergling])
    db_session.commit()


@pytest.fixture()
def sample_api(flask_app):
    api = Api(flask_app)
    api.add_model(Employee)
    return api


def sample_relation_query(parent_query, model):
    """
    Query callback to get the collection of all Employee that has Department 'Basic'
    :param model:
    :param parent_query:
    :return:
    """
    subquery = (
        db.session.query(employee_department.c.employee_id)
        .filter(employee_department.c.department_id == 100)
        .subquery()
    )
    if parent_query:
        query = parent_query.filter(model.id.in_(subquery))
    else:
        query = model.query.filter(model.id.in_(subquery))
    return query


def sample_model_query(parent_query, model):
    """
    Query callback to get the collection of all Companies only has 'Basic'
    :param model:
    :param parent_query:
    :return:
    """
    all_heroes_subquery = (
        db.session.query(employee_department.c.employee_id)
        .filter(employee_department.c.department_id == 200)
        .subquery()
    )
    all_companies_heroes_only_subquery = (
        db.session.query(Employee.company_id)
        .filter(Employee.id.in_(all_heroes_subquery))
        .subquery()
    )
    if parent_query:
        query = parent_query.filter(
            ~model.id.in_(all_companies_heroes_only_subquery)
        )  # ~ indicates NOT IN
    else:
        query = model.query.filter(~model.id.in_(all_companies_heroes_only_subquery))
    return query


def sample_property_query(parent_query, model):
    """
    Query callback to get the collection of colleagues but not it self
    :param model:
    :param parent_query:
    :return:
    """
    self_id = request.view_args["relation_id"]
    if parent_query:
        query = parent_query.filter(model.id != self_id)
    else:
        query = model.query.filter_by(model.id != self_id)
    return query


def test_get_collection_relation_terrans(client, sample_api, data_regression):
    sample_api.add_model(Company)
    sample_api.add_relation(
        Company.employees,
        serializer_class=EmployeeSerializer,
        query_modifier=sample_relation_query,
    )
    resp = client.get("/company/3/employees")
    assert resp.status_code == 200
    assert len(resp.json) == 2
    data = resp.get_json()
    data_regression.check(data)


def test_get_collection_relation_protoss(client, sample_api, data_regression):
    sample_api.add_model(Company)
    sample_api.add_relation(
        Company.employees,
        serializer_class=EmployeeSerializer,
        query_modifier=sample_relation_query,
    )
    resp = client.get("/company/1/employees")
    assert resp.status_code == 200
    assert len(resp.json) == 1
    data = resp.get_json()
    data_regression.check(data)


def test_get_collection_model(client, sample_api, data_regression):
    sample_api.add_model(Company, query_modifier=sample_model_query)
    resp = client.get("/company")
    assert resp.status_code == 200
    assert len(resp.json) == 1
    data = resp.get_json()
    data_regression.check(data)


def test_get_collection_property(client, sample_api, data_regression):
    sample_api.add_property(
        Employee,
        Employee,
        "colleagues",
        serializer_class=EmployeeSerializer,
        query_modifier=sample_property_query,
    )
    resp = client.get("/employee/11/colleagues")
    assert resp.status_code == 200
    assert len(resp.json) == 2
    data = resp.get_json()
    data_regression.check(data)
