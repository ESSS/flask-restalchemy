import pytest
from unittest.mock import MagicMock

from flask_restalchemy import Api
from flask_restalchemy.tests.sample_model import db


@pytest.fixture()
def api(flask_app):
    return Api(flask_app)


class TestGetDbSession:

    def test_returns_session(self, api, db_session):
        session = api.get_db_session()
        assert session is db.session

    def test_db_is_cached_after_first_call(self, api, db_session):
        api.get_db_session()
        cached = api._db
        api.get_db_session()
        assert api._db is cached

    def test_flask_sqlalchemy_2x_compat(self, api, flask_app, db_session, mocker):
        """Flask-SQLAlchemy 2.x stores _SQLAlchemyState with a .db attribute
        instead of the SQLAlchemy instance directly."""
        state = MagicMock()
        state.db = db
        mocker.patch.dict(flask_app.extensions, {"sqlalchemy": state})
        api._db = None

        session = api.get_db_session()
        assert session is db.session

    def test_flask_sqlalchemy_3x_compat(self, api, flask_app, db_session, mocker):
        """Flask-SQLAlchemy 3.x stores the SQLAlchemy instance directly,
        with no .db attribute."""
        mocker.patch.dict(flask_app.extensions, {"sqlalchemy": db})
        api._db = None

        session = api.get_db_session()
        assert session is db.session
