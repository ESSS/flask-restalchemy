import pytest

from flask_restalchemy.resourcefactory import item_resource_factory, collection_resource_factory
from flask_restalchemy.resources import ItemResource, CollectionResource
from flask_restalchemy.tests.sample_model import EmployeeSerializer, Employee


@pytest.mark.parametrize("resource_class, method, expected_response_codes, expected_tag", [
    (ItemResource, 'get', {"200", "400", "404"}, 'Employee'),
    (ItemResource, 'put', {"204", "400", "404"}, 'Employee'),
    (ItemResource, 'delete', {"204", "400", "404"}, 'Employee'),
])
def test_item_resource_spec_gen(resource_class, method, expected_response_codes, expected_tag):
    serializer = EmployeeSerializer(Employee)
    resource = item_resource_factory(resource_class, serializer)
    specs = getattr(resource, method).specs_dict
    assert specs["tags"] == [expected_tag]
    assert specs["responses"].keys() == expected_response_codes


@pytest.mark.parametrize("resource_class, method, expected_response_codes, expected_tag", [
    (CollectionResource, 'get', {"200"}, 'Employee'),
    (CollectionResource, 'post', {"201", "405"}, 'Employee'),
])
def test_collection_resource_spec_gen(resource_class, method, expected_response_codes,
                                      expected_tag):
    serializer = EmployeeSerializer(Employee)
    resource = collection_resource_factory(resource_class, serializer)
    specs = getattr(resource, method).specs_dict
    assert specs["tags"] == [expected_tag]
    assert specs["responses"].keys() == expected_response_codes


def test_schema():
    resource = item_resource_factory(ItemResource, EmployeeSerializer(Employee))
    specs_get_method = resource.get.specs_dict
    schema_props = specs_get_method["definitions"]["Employee"]["properties"]
    assert set(schema_props.keys()).issuperset({"created_at", "company_name"})
