from datetime import datetime

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, select
from sqlalchemy.orm import relationship, column_property

db = SQLAlchemy()
Base = db.Model


class Company(Base):

    __tablename__ = 'Company'

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
    company = relationship(Company)
    company_name = column_property(
        select([Company.name]).where(Company.id == company_id)
    )

    address_id = Column(ForeignKey('Address.id'))
    address = relationship(Address)
