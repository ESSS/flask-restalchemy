import json

import pytest

from flask_restalchemy import Api
from flask_restalchemy.tests.employer_serializer import EmployeeSerializer
from flask_restalchemy.tests.sample_model import Company, Employee, Address


@pytest.fixture(autouse=True)
def init_test_data(flask_app, db_session):
    for name, location in CLIENTS:
        company = Company(name=name, location=location)
        db_session.add(company)

    address = Address(street="5th Av.")
    emp1 = Employee(firstname="John", lastname="Doe", address=address)
    db_session.add(address)
    db_session.add(emp1)
    db_session.commit()

    api = Api(flask_app)
    api.add_model(Company)
    api.add_model(Employee, serializer_class=EmployeeSerializer)
    api.add_relation(Company.employees, serializer_class=EmployeeSerializer)
    return api


def test_order(client):
    response = client.get("/company?order_by=name")
    data_list = response.get_json()
    assert data_list[0]["name"] == "abe"
    assert data_list[-1]["name"] == "Von"

    response = client.get("/company?order_by=-name")
    data_list = response.get_json()
    assert data_list[0]["name"] == "Von"
    assert data_list[1]["name"] == "vanessa"


def test_order_by_relation(client, db_session):
    company = Company(name="Headquarters", location="Metropolis")
    db_session.add(company)
    db_session.flush()

    address_1 = Address(city="Gotham")
    address_2 = Address(city="Wakanda")
    address_3 = Address(city="Asgard")
    db_session.add(address_1)
    db_session.add(address_2)
    db_session.add(address_3)
    db_session.flush()

    employee_1 = Employee(firstname="Batman", company_id=company.id, address=address_1)
    employee_2 = Employee(firstname="Tchala", company_id=company.id, address=address_2)
    employee_3 = Employee(firstname="Thor", company_id=company.id, address=address_3)

    db_session.add(employee_1)
    db_session.add(employee_2)
    db_session.add(employee_3)
    db_session.commit()

    response = client.get(f"/company/{company.id}/employees")
    data_list = response.json
    assert len(data_list) == 3
    assert data_list[0]["address"]["city"] == "Gotham"
    assert data_list[1]["address"]["city"] == "Wakanda"
    assert data_list[2]["address"]["city"] == "Asgard"

    response = client.get(f"/company/{company.id}/employees?order_by=city")
    data_list = response.json
    assert data_list[0]["address"]["city"] == "Asgard"
    assert data_list[1]["address"]["city"] == "Gotham"
    assert data_list[2]["address"]["city"] == "Wakanda"

    response = client.get(f"/company/{company.id}/employees?order_by=-city")
    data_list = response.json
    assert data_list[0]["address"]["city"] == "Wakanda"
    assert data_list[1]["address"]["city"] == "Gotham"
    assert data_list[2]["address"]["city"] == "Asgard"


def test_filter(client):
    response = client.get("/company")
    data_list = response.get_json()
    assert len(data_list) == 22

    response = client.get("/company?limit=5")
    data_list = response.get_json()
    assert len(data_list) == 5

    response = client.get('/company?filter={"name": "Alvin"}')
    data_list = response.get_json()
    assert len(data_list) == 1

    response = client.get('/company?filter={"name": {"eq": "Alvin"}}')
    data_list = response.get_json()
    assert len(data_list) == 1

    response = client.get(
        '/company?filter={"$or": {"name": "Alvin", "location": "pace"} }'
    )
    data_list = response.get_json()
    assert len(data_list) == 2

    # test if AND is the default Logical Operator
    response = client.get('/company?filter={"name": "Keren", "location": "vilify"}')
    data_list = response.get_json()
    assert len(data_list) == 1

    response = client.get('/company?filter={"name": {"in": ["Alvin", "Keren"]} }')
    data_list = response.get_json()
    assert len(data_list) == 2

    response = client.get('/company?filter={"name": {"endswith": "a"} }')
    data_list = response.get_json()
    assert len(data_list) == 7

    response = client.get('/company?limit=2&filter={"name": {"endswith": "a"} }')
    data_list = response.get_json()
    assert len(data_list) == 2

    response = client.get('/company?limit=2&filter={"name": {"startswith": "Co"} }')
    data_list = response.get_json()
    assert len(data_list) == 2

    with pytest.raises(ValueError, match="Unknown operator unknown_operator"):
        client.get(
            "/company?filter={}".format(
                json.dumps({"name": {"unknown_operator": "Terr"}})
            )
        )


def test_pagination(client):
    response = client.get("/company?page=1&per_page=50")
    data_list = response.get_json()
    assert len(data_list.get("results")) == 22

    response = client.get("/company?page=1&per_page=5")
    data_list = response.get_json()
    assert len(data_list.get("results")) == 5

    response = client.get("/company?page=4&per_page=6")
    data_list = response.get_json()
    assert len(data_list.get("results")) == 4


def test_relations_pagination(client):
    response = client.post("/company", data={"name": "Terrans 1"})
    assert response.status_code == 201
    company_id = response.get_json()["id"]

    for i in range(20):
        client.post(
            f"/company/{company_id}/employees", data={"firstname": f"Jimmy {i}"}
        )

    response = client.get(
        "/company/{}/employees?filter={}".format(
            company_id, json.dumps({"firstname": {"eq": "Jimmy 1"}})
        )
    )
    assert response.status_code == 200
    data_list = response.get_json()
    assert len(data_list) == 1
    assert "firstname" in data_list[0]
    assert data_list[0]["firstname"] == "Jimmy 1"

    response = client.get(f"/company/{company_id}/employees?page=1&per_page=5")
    assert response.status_code == 200
    data_list = response.get_json()
    assert len(data_list.get("results")) == 5


CLIENTS = [
    ("Tyson", "syncretise"),
    ("Shandi", "pace"),
    ("Lurlene", "meteor"),
    ("Cornelius", "revengefulness"),
    ("Steven", "monosodium"),
    ("Von", "outswirl"),
    ("Lucille", "alcatraz"),
    ("Shawanda", "genotypic"),
    ("Erna", "preornamental"),
    ("Gonzalo", "unromanticized"),
    ("Glory", "cowtail"),
    ("Keren", "vilify"),
    ("Alvin", "genesis"),
    ("Melita", "numberless"),
    ("Lakia", "irretentive"),
    ("Joie", "peptonizer"),
    ("Jacqulyn", "underbidding"),
    ("Julius", "alcmene"),
    ("Coretta", "furcated"),
    ("Laverna", "mastaba"),
    ("abe", "abesee"),
    ("vanessa", "vans"),
]
