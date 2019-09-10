import pytest

from flask_restalchemy.tests.sample_model import Employee


@pytest.mark.parametrize(
    "method, expected_response_codes, expected_tag",
    [
        pytest.param("get", {"200", "400", "404"}, "Employee", marks=pytest.mark.xfail),
        pytest.param("put", {"204", "400", "404"}, "Employee", marks=pytest.mark.xfail),
        pytest.param(
            "delete", {"204", "400", "404"}, "Employee", marks=pytest.mark.xfail
        ),
    ],
)
def test_item_resource_spec_gen(method, expected_response_codes, expected_tag):
    serializer = EmployeeSerializer(Employee)
    resource = item_resource_factory(ItemResource, serializer)
    specs = getattr(resource, method).specs_dict
    assert specs["tags"] == [expected_tag]
    assert specs["responses"].keys() == expected_response_codes


@pytest.mark.parametrize(
    "method, expected_response_codes, expected_tag",
    [
        pytest.param("get", {"200"}, "Employee", marks=pytest.mark.xfail),
        pytest.param("post", {"201", "405"}, "Employee", marks=pytest.mark.xfail),
    ],
)
def test_collection_resource_spec_gen(method, expected_response_codes, expected_tag):
    serializer = EmployeeSerializer(Employee)
    resource = collection_resource_factory(CollectionResource, serializer)
    specs = getattr(resource, method).specs_dict
    assert specs["tags"] == [expected_tag]
    assert specs["responses"].keys() == expected_response_codes


@pytest.mark.xfail
def test_schema():
    resource = item_resource_factory(ItemResource, EmployeeSerializer(Employee))
    specs_get_method = resource.get.specs_dict
    schema_props = specs_get_method["definitions"]["Employee"]["properties"]
    assert set(schema_props.keys()).issuperset({"created_at", "company_name"})
