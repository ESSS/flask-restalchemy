import json
from unittest.mock import call

import pytest

from flask_restalchemy import Api
from flask_restalchemy.decorators.request_hooks import before_request, after_request
from flask_restalchemy.tests.sample_model import Employee, Company, Address


@pytest.fixture
def sample_api(flask_app):
    return Api(flask_app)


@pytest.fixture(autouse=True)
def create_test_sample(db_session):
    company = Company(id=5, name="Terrans")
    emp1 = Employee(id=1, firstname="Jim", lastname="Raynor", company=company)

    addr1 = Address(street="5 Av", number="943", city="Tarsonis")
    emp1.address = addr1

    db_session.add(company)
    db_session.add(emp1)
    db_session.commit()


@pytest.mark.parametrize("decorator_verb", ["ALL", "GET"])
def test_get_item_preprocessor(sample_api, client, mocker, decorator_verb):
    pre_processor_mock = mocker.Mock(return_value=None)
    sample_api.add_model(
        Employee,
        request_decorators={decorator_verb: before_request(pre_processor_mock)},
    )

    resp = client.get("/employee/1")
    assert resp.status_code == 200
    pre_processor_mock.assert_called_once_with(id=1)
    resp = client.post("/employee", data=json.dumps({"firstname": "Jeff"}))
    assert resp.status_code == 201
    # 2 calls if all verbs were decorated, otherwise test only for GET call
    assert pre_processor_mock.call_count == 2 if decorator_verb == "all" else 1


def test_get_collection_preprocessor(sample_api, client, mocker):
    pre_processor_mock = mocker.Mock(return_value=None)
    sample_api.add_model(
        Employee, request_decorators=before_request(pre_processor_mock)
    )

    resp = client.get("/employee")
    assert resp.status_code == 200
    assert pre_processor_mock.call_args == call(id=None)

    resp = client.post("/employee", data=json.dumps({"firstname": "Jeff"}))
    assert resp.status_code == 201
    assert pre_processor_mock.call_args == call()

    resp = client.put("/employee/1", data=json.dumps({"lastname": "R."}))
    assert resp.status_code == 200
    assert pre_processor_mock.call_args == call(id=1)

    assert pre_processor_mock.call_count == 3


def test_post_processors(sample_api, client, mocker):
    pre_mock = mocker.Mock(return_value=None)
    post_mock = mocker.Mock(return_value=None)
    sample_api.add_model(
        Employee,
        request_decorators={
            "ALL": after_request(post_mock),
            "POST": before_request(pre_mock),
        },
    )

    data = {"firstname": "Ana", "lastname": "Queen"}
    resp = client.post("/employee", data=json.dumps(data))
    assert resp.status_code == 201
    assert pre_mock.call_count == 1

    employee_id = resp.get_json()["id"]
    assert employee_id
    assert post_mock.call_count == 1
    post_mock_args = post_mock.call_args[0]
    assert post_mock_args[0][1] == 201
    assert post_mock_args[0][0].data == resp.data


def test_put_preprocessors(sample_api, client, mocker):
    pre_mock = mocker.Mock(return_value=None)
    post_mock = mocker.Mock(return_value=None)
    sample_api.add_model(
        Employee,
        request_decorators={
            "PUT": [before_request(pre_mock), after_request(post_mock)]
        },
    )

    data = {"firstname": "Ana", "lastname": "Queen"}
    resp = client.put("/employee/1", data=json.dumps(data))
    assert resp.status_code == 200
    assert pre_mock.call_count == 1
    assert pre_mock.call_args == call(id=1)

    assert post_mock.call_count == 1


def test_delete_preprocessors(sample_api, client, mocker):
    pre_mock = mocker.Mock(return_value=None)
    post_mock = mocker.Mock(return_value=None)
    sample_api.add_model(
        Employee,
        request_decorators={
            "DELETE": [before_request(pre_mock), after_request(post_mock)]
        },
    )

    resp = client.delete("/employee/1")
    assert resp.status_code == 204
    assert pre_mock.call_args == call(id=1)
    assert post_mock.call_args == call(("", 204), id=1)


def test_property_get_collection_processor(sample_api, client, mocker):
    pre_mock = mocker.Mock(return_value=None)
    sample_api.add_property(
        Employee,
        Employee,
        "colleagues",
        request_decorators={"GET": before_request(pre_mock)},
    )

    resp = client.get("/employee/1/colleagues")
    assert resp.status_code == 200
    pre_mock.assert_called_once_with(id=None, relation_id=1)


def test_relation_get_item_preprocessor(sample_api, client, mocker):
    pre_mock = mocker.Mock(return_value=None)
    sample_api.add_relation(
        Company.employees, request_decorators={"GET": before_request(pre_mock)}
    )

    resp = client.get("/company/5/employees/1")
    assert resp.status_code == 200
    pre_mock.assert_called_once_with(relation_id=5, id=1)


def test_relation_get_collection_preprocessor(sample_api, client, mocker):
    pre_mock = mocker.Mock(return_value=None)
    sample_api.add_relation(
        Company.employees, request_decorators={"GET": before_request(pre_mock)}
    )

    resp = client.get("/company/5/employees")
    assert resp.status_code == 200
    pre_mock.assert_called_once_with(relation_id=5, id=None)


def test_relation_post_processors(sample_api, client, mocker):
    pre_mock = mocker.Mock(return_value=None)
    post_mock = mocker.Mock(return_value=None)
    sample_api.add_relation(
        Company.employees,
        request_decorators={
            "POST": [before_request(pre_mock), after_request(post_mock)]
        },
    )

    data = {"firstname": "Ana", "lastname": "Queen"}
    resp = client.post("/company/5/employees", data=json.dumps(data))
    assert resp.status_code == 201
    pre_mock.assert_called_once_with(relation_id=5)
    assert post_mock.call_count == 1
    assert post_mock.call_args[1] == {"relation_id": 5}


def test_relation_put_preprocessors(sample_api, client, mocker):
    pre_mock = mocker.Mock(return_value=None)
    post_mock = mocker.Mock(return_value=None)
    sample_api.add_relation(
        Company.employees,
        request_decorators={
            "PUT": [before_request(pre_mock), after_request(post_mock)]
        },
    )

    data = {"firstname": "Ana", "lastname": "Queen"}
    resp = client.put("/company/5/employees/1", data=json.dumps(data))
    assert resp.status_code == 200
    assert pre_mock.call_args == call(relation_id=5, id=1)
    assert post_mock.call_count == 1
    assert post_mock.call_args[1] == {"relation_id": 5, "id": 1}


def test_relation_delete_preprocessors(sample_api, client, mocker):
    pre_mock = mocker.Mock(return_value=None)
    post_mock = mocker.Mock(return_value=None)
    sample_api.add_relation(
        Company.employees,
        request_decorators={
            "DELETE": [before_request(pre_mock), after_request(post_mock)]
        },
    )

    resp = client.delete("/company/5/employees/1")
    assert resp.status_code == 204
    assert pre_mock.call_count == 1
    assert post_mock.call_count == 1
    assert post_mock.call_args[1] == {"relation_id": 5, "id": 1}
