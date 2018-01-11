from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, String, Integer

db = SQLAlchemy()
Base = db.Model


class Employee(Base):

    __tablename__ = 'Employee'

    id = Column(Integer, primary_key=True)
    firstname = Column(String)
    lastname = Column(String)
    email = Column(String)

