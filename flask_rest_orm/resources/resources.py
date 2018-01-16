from flask import request, json
from flask_restful import Resource
from sqlalchemy import text

from .utils import query_from_request


class BaseResource(Resource):

    def __init__(self, declarative_model, serializer, session_getter):
        """
        The Base class for ORM resources

        :param class declarative_model: the SQLAlchemy declarative class.

        :param ModelSchema serializer: Marshmallow schema for serialization. If `None`, a default serializer will be
            created.

        :param callable session_getter: a callable that returns the DB session. A callable is used since a reference to
            DB session may not be available on the resource initialization.
        """
        self._resource_model = declarative_model
        self._serializer = serializer
        self._serializer.strict = True
        self._session_getter = session_getter

    def save_from_request(self, extra_attrs={}):
        session = self._session_getter()
        model_obj = self._serializer.load(load_request_data(), session).data
        for attr_name, value in extra_attrs.items():
            setattr(model_obj, attr_name, value)
        session.add(model_obj)
        session.commit()
        return self._serializer.dump(model_obj).data

    def _save_serialized(self, serialized_data):
        session = self._session_getter()
        model_obj = self._serializer.load(serialized_data, session).data
        session.add(model_obj)
        session.commit()
        return self._serializer.dump(model_obj).data

    @property
    def _db_session(self):
        return self._session_getter()


class ItemResource(BaseResource):
    """
    flask-restful resource class that receives receives a SQLAlchemy model class and define the API to provide GET,
    UPDATE and DELETE over a single data identified by id
    """

    def get(self, id):
        data = self._resource_model.query.get(id)
        if data is None:
            return NOT_FOUND_ERROR, 404
        return self._serializer.dump(data).data

    def put(self, id):
        data = self._resource_model.query.get(id)
        if data is None:
            return NOT_FOUND_ERROR, 404
        serialized = self._serializer.dump(data).data
        serialized.update(load_request_data())
        self._save_serialized(serialized)
        return serialized

    def delete(self, id):
        data = self._resource_model.query.get(id)
        if data is None:
            return NOT_FOUND_ERROR, 404
        session = self._db_session
        session.delete(data)
        session.commit()
        return '', 204


class CollectionResource(BaseResource):
    """
    flask-restful resource class that receives a SQLAlchemy model class and define the API to provide LIST and
    CREATE over data of that class
    """

    def get(self):
        collection = []
        data = query_from_request(self._resource_model, request)
        for item in data:
            collection.append(self._serializer.dump(item).data)
        return collection

    def post(self):
        saved = self._save_serialized(load_request_data())
        return saved, 201


class CollectionRelationResource(BaseResource):
    """
    flask-restful resource class that receives two SQLAlchemy models, a parent model and a child model,
    and define the API to provide LIST and CREATE over data of the child model associated with a specific
    element of the parent model.
    """

    def __init__(self, declarative_model, relation_fk, related_model, serializer, session_getter):
        """
        The Base class for ORM resources

        :param class declarative_model: the SQLAlchemy declarative class.

        :param ModelSchema serializer: Marshmallow schema for serialization. If `None`, a default serializer will be
            created.

        :param callable session_getter: a callable that returns the DB session. A callable is used since a reference to
            DB session may not be available on the resource initialization.
        """
        super(CollectionRelationResource, self).__init__(declarative_model, serializer, session_getter)
        self._relation_fk = relation_fk
        self._related_model = related_model
        self._association_fk = None


    def get(self, relation_id):
        session = self._db_session()
        related_obj = session.query(self._related_model).get(relation_id)
        if related_obj is None:
            return {'msg': 'Parent resource does not exist!'}, 400
        if self._association_fk:
            fk_value = getattr(related_obj, self._association_fk)
        else:
            fk_value = relation_id
        fk_column = self._relation_fk
        filter_text = "{fk_column} = {fk_value}".format(**locals())
        data = session.query(self._resource_model).filter(text(filter_text)).all()
        collection = [self._serializer.dump(item).data for item in data]
        return collection


    def post(self, relation_id):
        session = self._db_session()
        related = session.query(self._related_model).get(relation_id)
        if not related:
            return {'msg': 'Parent resource does not exist!'}, 400
        if self._association_fk:
            fk_value = getattr(related, self._association_fk)
        else:
            fk_value = relation_id
        serialized = load_request_data()
        serialized[self._relation_fk] = int(fk_value)
        data = self._save_serialized(serialized)
        return data, 201


class ItemRelationResource(BaseResource):
    """
    flask-restful resource class that receives two SQLAlchemy models, a parent model and a child model,
    and define the API to provide GET, PUT and DELETE operations over data of the child model associated with a
    specific element of the parent model.
    """

    def __init__(self, declarative_model, relation_fk, related_model, serializer, session_getter):
        """
        The Base class for ORM resources

        :param class declarative_model: the SQLAlchemy declarative class.

        :param ModelSchema serializer: Marshmallow schema for serialization. If `None`, a default serializer will be
            created.

        :param callable session_getter: a callable that returns the DB session. A callable is used since a reference to
            DB session may not be available on the resource initialization.
        """
        super(ItemRelationResource, self).__init__(declarative_model, serializer, session_getter)
        self._relation_fk = relation_fk
        self._related_model = related_model
        self._association_fk = None

    def get(self, relation_id, id):
        try:
            model_obj = self._query_valid_child(relation_id, id)
        except RequestException as err:
            return err.msg, err.error_code
        return self._serializer.dump(model_obj).data


    def put(self, relation_id, id):
        try:
            model_obj = self._query_valid_child(relation_id, id)
        except RequestException as err:
            return err.msg, err.error_code
        serialized = self._serializer.dump(model_obj).data
        serialized.update(load_request_data())
        return self._save_serialized(serialized)

    def delete(self, relation_id, id):
        try:
            child = self._query_valid_child(relation_id, id)
        except RequestException as err:
            return err.msg, err.error_code
        session = self._db_session()
        session.delete(child)
        session.commit()
        return '', 204

    def _query_valid_child(self, related_id, id):
        session = self._db_session()
        related = session.query(self._related_model).get(related_id)
        if related is None:
            raise RequestException('Related resource does not exist!', 400)

        model = session.query(self._resource_model).get(id)
        if model is None:
            raise RequestException('Child not found!', 404)

        if self._association_fk:
            fk_value = getattr(related, self._association_fk)
        else:
            fk_value = int(related_id)
        if getattr(model, self._relation_fk) != fk_value:
            raise RequestException('Child is not from this parent!', 400)

        return model


class RequestException(Exception):
    def __init__(self, msg, error_code):
        self.msg = msg
        self.error_code = error_code


def load_request_data():
    if request.data:
        return json.loads(request.data.decode('utf-8'))
    else:
        return request.form.to_dict()


NOT_FOUND_ERROR = 'Resource not found in the database!'