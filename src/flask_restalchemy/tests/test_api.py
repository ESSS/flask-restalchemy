import json
from datetime import datetime

import pytest
from flask_restalchemy.serialization import (
    ModelSerializer,
    Field,
    NestedModelField,
    NestedModelListField,
)

from flask_restalchemy import Api
from flask_restalchemy.tests.sample_model import (
    Employee,
    Company,
    Address,
    Contact,
    ContactType,
)
from flask_restalchemy.resources.resources import ViewFunctionResource


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
    api.add_model(Company, view_name="alt_company")
    api.add_model(Employee, serializer_class=EmployeeSerializer)


@pytest.fixture(autouse=True)
def create_test_sample(db_session):
    contact_type1 = ContactType(label="Phone")
    contact_type2 = ContactType(label="Email")

    company = Company(id=5, name="Terrans")
    emp1 = Employee(id=1, firstname="Jim", lastname="Raynor", company=company)
    emp2 = Employee(id=2, firstname="Sarah", lastname="Kerrigan", company=company)

    addr1 = Address(street="5 Av", number="943", city="Tarsonis")
    emp1.address = addr1

    db_session.add(contact_type1)
    db_session.add(contact_type2)
    db_session.add(company)
    db_session.add(emp1)
    db_session.add(emp2)
    db_session.commit()


def test_get(client, data_regression):
    resp = client.get("/employee/1")
    assert resp.status_code == 200
    serialized = resp.get_json()
    data_regression.check(serialized)
    assert "password" not in serialized
    resp = client.get("/employee/10239")
    assert resp.status_code == 404


def test_get_collection(client, data_regression):
    resp = client.get("/employee")
    assert resp.status_code == 200
    serialized = resp.get_json()
    data_regression.check(serialized)


def test_post(client):
    contacts = [
        {"type_id": 1, "value": "0000-0000"},
        {"type_id": 2, "value": "test@mail.co"},
    ]
    post_data = {
        "id": 3,
        "firstname": "Tychus",
        "lastname": "Findlay",
        "admission": "2002-02-02T00:00:00+0300",
        "contacts": contacts,
    }
    resp = client.post("/employee", data=json.dumps(post_data))
    assert resp.status_code == 201
    emp3 = Employee.query.get(3)
    contact1 = emp3.contacts[0]
    assert emp3.id == 3
    assert emp3.firstname == "Tychus"
    assert emp3.lastname == "Findlay"
    assert emp3.admission == datetime(2002, 2, 2)
    assert contact1
    assert contact1.value == "0000-0000"


def test_post_default_serializer(client):
    resp = client.post("/company", data={"name": "Mangsk Corp"})
    assert resp.status_code == 201


def test_put(client):
    resp = client.put("/employee/1", data={"firstname": "Jimmy"})
    assert resp.status_code == 200
    emp3 = Employee.query.get(1)
    assert emp3.firstname == "Jimmy"


def test_alternative_url(client):
    resp = client.get("/alt_company/5")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["name"] == "Terrans"


def test_url_rule(flask_app, client):
    def hello_world(name):
        return f"hello {name}"

    api = Api(flask_app)
    api.add_url_rule("/<string:name>", "index", hello_world)
    resp = client.get("/raynor")
    assert resp.status_code == 200
    assert resp.data == b"hello raynor"

    resp = client.post("/kerrigan")
    assert resp.status_code == 200
    assert resp.data == b"hello kerrigan"

    resp = client.put("/artanis")
    assert resp.status_code == 200
    assert resp.data == b"hello artanis"

    resp = client.delete("/zeratul")
    assert resp.status_code == 200
    assert resp.data == b"hello zeratul"


def test_route(flask_app, client):

    api = Api(flask_app)

    @api.route("/hello/<string:name>")
    def hello_world(name):
        return f"hello {name}"

    resp = client.get("/hello/raynor")
    assert resp.status_code == 200
    assert resp.data == b"hello raynor"

    resp = client.post("/hello/kerrigan")
    assert resp.status_code == 200
    assert resp.data == b"hello kerrigan"


@pytest.mark.parametrize(
    "methods",
    [
        ["GET_COLLECTION", "GET", "POST", "PUT", "DELETE"],
        ["GET_COLLECTION"],
        ["POST"],
        ["GET_COLLECTION", "POST"],
        ["PUT", "DELETE"],
    ],
)
def test_http_verbs(flask_app, client, methods):
    def ping(*args, **kwargs):
        return "ping"

    api = Api(flask_app)
    api.add_resource(
        ViewFunctionResource,
        "/ping",
        "ping",
        resource_init_args=(ping,),
        methods=methods,
    )
    resp = client.get("/ping")
    assert resp.status_code == 200 if "GET_COLLECTION" in methods else 405
    resp = client.get("/ping/1")
    assert resp.status_code == 200 if "GET" in methods else 405
    resp = client.post("/ping")
    assert resp.status_code == 200 if "POST" in methods else 405
    resp = client.delete("/ping/1")
    assert resp.status_code == 200 if "PUT" in methods else 405
    resp = client.put("/ping/1")
    assert resp.status_code == 200 if "DELETE" in methods else 405
