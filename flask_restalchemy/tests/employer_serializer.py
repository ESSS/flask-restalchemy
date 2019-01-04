from flask_restalchemy.serialization import ModelSerializer, Field, NestedModelField
from flask_restalchemy.tests.sample_model import Address


class EmployeeSerializer(ModelSerializer):

    password = Field(load_only=True)
    created_at = Field(dump_only=True)
    company_name = Field(dump_only=True)
    address = NestedModelField(Address)
