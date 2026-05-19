from http import HTTPStatus

import pytest
from flask import json
from sqlalchemy import select

from flask_restalchemy import Api
from flask_restalchemy.serialization import Field, ModelSerializer, NestedModelField
from flask_restalchemy.tests.sample_model import (
    Address,
    Company,
    Department,
    Employee,
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
    terrans = Company(id=3, name="Terrans")
    raynor = Employee(id=9, firstname="Jim", lastname="Raynor", company=terrans)
    kerrigan = Employee(id=3, firstname="Sarah", lastname="Kerrigan", company=terrans)
    dept1 = Department(name="Marines")
    dept2 = Department(name="Heroes")
    raynor.departments.append(dept1)
    raynor.departments.append(dept2)

    db_session.add(protoss)
    db_session.add(terrans)
    db_session.add(dept1)
    db_session.add(dept2)
    db_session.add(raynor)
    db_session.add(kerrigan)
    db_session.commit()


@pytest.fixture(autouse=True)
def sample_api(flask_app):
    api = Api(flask_app)
    api.add_model(Company)
    api.add_model(Employee)
    api.add_relation(Company.employees, serializer_class=EmployeeSerializer)
    api.add_property(
        Employee, Employee, "colleagues", serializer_class=EmployeeSerializer
    )
    api.add_relation(Employee.departments)
    return api


def test_get_collection(client, data_regression):
    resp = client.get("/company/3/employees")
    assert resp.status_code == HTTPStatus.OK
    assert resp.is_json
    data = resp.get_json()
    data_regression.check(data)


def test_get_item(client, data_regression):
    resp = client.get("/company/3/employees/3")
    assert resp.status_code == HTTPStatus.OK
    assert resp.is_json
    data = resp.get_json()
    data_regression.check(data)

    assert client.get("/company/5/employees/999").status_code == HTTPStatus.NOT_FOUND


def test_post_item(client):
    post_data = {
        "firstname": "Tychus",
        "lastname": "Findlay",
        "admission": "2002-02-02T00:00:00+0300",
    }
    resp = client.post("/company/3/employees", data=post_data)
    assert resp.status_code == HTTPStatus.CREATED
    assert resp.is_json
    saved_id = resp.get_json()["id"]

    new_employee = db.session.get(Employee, saved_id)
    assert new_employee.firstname == "Tychus"
    assert new_employee.company.id == 3


def test_put_item(client):
    resp = client.put("/company/3/employees/3", data={"lastname": "K."})
    assert resp.status_code == HTTPStatus.OK

    sarah = db.session.execute(
        select(Employee).where(Employee.firstname == "Sarah")
    ).scalar_one()
    assert sarah.lastname == "K."


def test_delete_item(client):
    company = db.session.get(Company, 3)
    assert [emp.firstname for emp in company.employees] == ["Sarah", "Jim"]

    resp = client.delete("/company/3/employees/9")
    assert resp.status_code == HTTPStatus.NO_CONTENT
    assert [emp.firstname for emp in company.employees] == ["Sarah"]

    assert (
        db.session.execute(select(Employee).where(Employee.firstname == "Jim")).first()
        is None
    )

    assert client.delete("/company/5/employees/999").status_code == HTTPStatus.NOT_FOUND


def test_post_append_existent(client):
    resp = client.post("/employee", data={"firstname": "Tychus", "lastname": "Findlay"})
    assert resp.status_code == HTTPStatus.CREATED
    data = resp.get_json()
    empl_id = data["id"]
    thychus = db.session.get(Employee, empl_id)
    assert thychus.company_name is None

    resp = client.post("/company/3/employees", data={"id": empl_id})
    assert resp.status_code == HTTPStatus.OK

    thychus = db.session.get(Employee, empl_id)
    assert thychus.company_name == "Terrans"

    resp = client.post("/company/3/employees", data={"id": 1000})
    assert resp.status_code == HTTPStatus.NOT_FOUND


def test_property(client, data_regression):
    resp = client.get("/employee/9/colleagues")
    assert resp.status_code == HTTPStatus.OK
    response_data = resp.get_json()
    data_regression.check(response_data)

    resp = client.post("/employee/9/colleagues")
    assert resp.status_code == HTTPStatus.METHOD_NOT_ALLOWED


def test_property_pagination(client):

    for i in range(20):
        client.post("/company/3/employees", data={"firstname": f"Jimmy {i}"})

    response = client.get("/employee/9/colleagues?order_by=id&limit=5")
    assert response.status_code == HTTPStatus.OK
    response_data = response.get_json()
    assert len(response_data) == 5
    assert response_data[0]["firstname"] == "Sarah"

    response = client.get(
        "/employee/9/colleagues?filter={}".format(
            json.dumps({"firstname": {"eq": "Sarah"}})
        )
    )
    assert response.status_code == HTTPStatus.OK
    response_data = response.get_json()
    assert len(response_data) == 1
    assert "firstname" in response_data[0]
    assert response_data[0]["firstname"] == "Sarah"

    response = client.get("/employee/9/colleagues?page=1&per_page=10")
    assert response.status_code == HTTPStatus.OK
    response_data = response.get_json()
    assert len(response_data.get("results")) == 10


def test_instrumented_list_triggers_warning(flask_app, client, db_session):
    # Employee.contacts has no lazy="dynamic", so accessing it yields an InstrumentedList
    # and the resource should warn that pagination/filter are unavailable.
    api = Api(flask_app)
    api.add_relation(Employee.contacts)

    with pytest.warns(UserWarning, match="does not support pagination"):
        resp = client.get("/employee/9/contacts")
    assert resp.status_code == HTTPStatus.OK
    assert resp.get_json() == []


def test_delete_on_relation_with_secondary(client):
    jim = db.session.get(Employee, 9)
    assert jim is not None
    dep = jim.departments[0]

    sarah = db.session.get(Employee, 3)
    assert sarah is not None
    assert dep not in sarah.departments

    resp = client.get("/employee/3/departments")
    assert resp.status_code == HTTPStatus.OK

    resp = client.delete("/employee/3/departments/" + str(dep.id))
    assert resp.status_code == HTTPStatus.NOT_FOUND

    resp = client.delete("/employee/9/departments/" + str(dep.id))
    assert resp.status_code == HTTPStatus.NO_CONTENT
