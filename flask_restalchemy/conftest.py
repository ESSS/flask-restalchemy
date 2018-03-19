import json

import pytest
from flask import Flask
from flask_restalchemy.tests.sample_model import db


@pytest.fixture
def client(flask_app, db_session):
    from werkzeug.wrappers import BaseResponse

    def response_wrapper(*args):
        resp = BaseResponse(*args)
        if resp.status_code in [200, 201]:
            resp.parsed_data = json.loads(resp.data.decode('utf-8'))
        return resp

    test_client = flask_app.test_client()
    test_client.response_wrapper = response_wrapper
    return test_client


@pytest.fixture()
def flask_app():
    app = Flask('flask_sqlapi_sample')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['PROPAGATE_EXCEPTIONS'] = True
    db.init_app(app)
    with app.app_context():
        yield app


@pytest.fixture()
def db_session(flask_app):
    db.create_all()
    yield db.session
    db.session.remove()
    db.drop_all()
