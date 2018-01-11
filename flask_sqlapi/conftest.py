import pytest
from sqlalchemy.orm import Session




def db_session(db_connection):
    db.create_all()
    yield db.session
    db.session.remove()
    db.drop_all()

