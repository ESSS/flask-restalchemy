from datetime import datetime

from flask_sqlalchemy import SQLAlchemy
from marshmallow import fields, pre_load
from marshmallow_sqlalchemy import ModelSchema
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, select, Table
from sqlalchemy.orm import relationship, column_property, object_session

db = SQLAlchemy()
Base = db.Model


class Company(Base):

    __tablename__ = 'Company'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    employees = relationship("Employee")


class Department(Base):

    __tablename__ = 'Department'

    id = Column(Integer, primary_key=True)
    name = Column(String)


class Address(Base):

    __tablename__ = 'Address'

    id = Column(Integer, primary_key=True)
    street = Column(String)
    number = Column(String)
    zip = Column(String)
    city = Column(String)
    state = Column(String)


class Employee(Base):

    __tablename__ = 'Employee'

    id = Column(Integer, primary_key=True)
    firstname = Column(String)
    lastname = Column(String)
    email = Column(String)
    password = Column(String)
    created_at = Column(DateTime, default=datetime(2000, 1, 1))
    company_id = Column(ForeignKey('Company.id'))
    company = relationship(Company, back_populates='employees')
    company_name = column_property(
        select([Company.name]).where(Company.id == company_id)
    )

    address_id = Column(ForeignKey('Address.id'))
    address = relationship(Address)

    departments = relationship('Department', secondary='employee_department')


    @property
    def colleagues(self):
        return object_session(self).execute(
            select([Employee]).where(Employee.company_id == self.company_id)
        ).fetchall()


employee_department = Table('employee_department', Base.metadata,
    Column('employee_id', Integer, ForeignKey('Employee.id')),
    Column('department_id', Integer, ForeignKey('Department.id'))
)


class AddressSerializer(ModelSchema):
    class Meta:
        model = Address

class EmployeeSerializer(ModelSchema):
    class Meta:
        model = Employee
        include_fk = True

    password = fields.Str(load_only=True)
    created_at = fields.DateTime(dump_only=True)
    company_name = fields.Str(dump_only=True)
    address = fields.Nested(AddressSerializer, allow_none=True)

    # Hack for nested fields to work. See:
    # https://github.com/marshmallow-code/marshmallow/issues/658
    @pre_load
    def set_field_session(self, data):
        self.fields['address'].schema.session = self.session
