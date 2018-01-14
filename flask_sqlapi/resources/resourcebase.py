import json
from contextlib import contextmanager

# from flasgger import swag_from
# from flask_allows import Permission
from functools import wraps

from flask_restful import Resource, request
from .utils import load_request_data, query_from_request, split_nested
from .docgeneration import gen_spec


CanRead = lambda x: True
CanWrite = lambda x: True


@contextmanager
def Permission(*args):
    yield True


def resource_collection_factory(resource_model, serializer, db_session, resource_decorators=None):
    """
    This function creates a class to define a flask-restful resource for Get collection and post method
    from a sqlalchemy resource model with the given resource tags used to verify authorization access.
    It also associates swargger documentation spec dict, generated from the sqlalchemy model, to all the http methods
    implemented.

    :param class resource_model:
        sqlalchemy resource model

    :param list(str) resource_tags:
        resource tag list

    :rtype class:
    :return:
        flask-restful resource class

    .. note::
    A factory is needed because the documentation is associated with the class methods and shared by its objects.
    Then a unique class is created for each sqlalchemy resource, otherwise documentation would be shared by all the
    resources.
    """

    resource_decorators = resource_decorators or []
    get_specs_dict = gen_spec(resource_model, 'GET_Collection')
    post_specs_dict = gen_spec(resource_model, 'POST')

    class _ResourceCollection(Resource):
        """
        flask-restful resource class that receives a SQLAlchemy model class and define the API to provide LIST and
        CREATE over data of that class
        """
        method_decorators = resource_decorators

        _resource_model = resource_model
        _serializer = serializer
        _resource_tags = None

        # @auth_token_required
        # @swag_from(get_specs_dict)
        def get(self):
            with Permission(CanRead(self._resource_tags)):
                collection = []
                data = query_from_request(self._resource_model, request)
                for item in data:
                    collection.append(self._serializer.dump(item).data)
                return collection

        # @auth_token_required
        # @swag_from(post_specs_dict)
        def post(self):
            with Permission(CanWrite(self._resource_tags)):
                args = load_request_data(request)
                args, nested_args = split_nested(args)
                obj = self._serializer.load(args, session=db_session).data
                db_session.add(obj)
                db_session.commit()
                serialized = self._serializer.dump(obj).data
                return serialized, 201

    return _ResourceCollection


def resource_item_factory():
    """
    This function creates a class to define a flask-restful resource for GET, PUT, and DELETE methods over an item
    from a sqlalchemy resource model with the given resource tags used to verify authorization access.
    It also associates swargger documentation spec dict, generated from the sqlalchemy model, to all the http methods
    implemented.

    :param class resource_model:
        sqlalchemy resource model

    :param list(str) resource_tags:
        resource tag list

    :rtype class:
    :return: flask-restful resource class

    .. note::
    A factory is needed because the documentation is associated with the class methods and shared by its objects.
    Then a unique class is created for each sqlalchemy resource, otherwise documentation would be shared by all the
    resources.
    """

    class _ItemResource(ItemResource):
        pass

    return _ItemResource


class ItemResource(Resource):
    """
    flask-restful resource class that receives receives a SQLAlchemy model class and define the API to provide GET,
    UPDATE and DELETE over a single data identified by id
    """

    # get_specs_dict = gen_spec(resource_model, 'GET')
    # put_specs_dict = gen_spec(resource_model, 'PUT')
    # del_specs_dict = gen_spec(resource_model, 'DELETE')

    def __init__(self, declarative_model, serializer, session):
        self._resource_model = declarative_model
        self._serializer = serializer
        self._db_session = session

    # @auth_token_required
    # @swag_from(get_specs_dict)
    def get(self, id):
        with Permission(CanRead(None)):
            data = self._resource_model.query.filter_by(id=id).first()
            if data:
                return self._serializer.dump(data).data
            return '', 404

    # @auth_token_required
    # @swag_from(put_specs_dict)
    def put(self, id):
        with Permission(CanWrite(None)):
            data = self._resource_model.query.filter_by(id=id).first()
            if data:
                session = self._db_session
                args = load_request_data(request)
                args, nested_args = split_nested(args)
                for key, value in nested_args.items():
                    if key in data.__mapper__.relationships:
                        setattr(data, key, data.__mapper__.relationships[key].argument(**value))
                for k in args.keys():
                    setattr(data, k, args[k])
                session.add(data)
                session.commit()
                return self._serializer.dump(data).data
            return '', 404

    # @auth_token_required
    # @swag_from(del_specs_dict)
    def delete(self, id):
        with Permission(CanWrite(None)):
            data = self._resource_model.query.filter_by(id=id).first()
            if data:
                session = self._db_session
                session.delete(data)
                session.commit()
                return '', 204
            return '', 404
