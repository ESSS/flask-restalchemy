import json
from contextlib import contextmanager

# from flasgger import swag_from
# from flask_allows import Permission
from flask_restful import Resource, request
from .utils import load_request_data, query_from_request, split_nested, DataJSONEncoder
from .docgeneration import gen_spec


CanRead = lambda x: True
CanWrite = lambda x: True


@contextmanager
def Permission(*args):
    yield True


def expose_resource(url, resource, tags, entity_fields=None):
    """
    This function creates the API entries for the given sqlalchemy resource class and serve in the given url, it also
    associates the resource with the given tags in order to verify authorization over the resource.
    If the resource is marked as auditable, an API for Audit logs is created as child resource.

    :param class resource:
        sqlalchemy resource class

    :param str url:
        url route to match for the resource, standard flask routing rules apply.

    :param list(str) tags:
        tags to be associated to the resource

    :param bool auditable:
        Flag to tell if the resource is auditable and add a entry point for audit log as child resource
    """
    assert isinstance(url, str)
    _ResourceCollectionClass = resource_collection_factory(resource, tags)
    api.add_resource(_ResourceCollectionClass, url, endpoint=resource.__tablename__ + '_list')

    _ResourceItemClass = resource_item_factory(resource, tags, entity_fields)
    api.add_resource(_ResourceItemClass, url + '/<id>', endpoint=resource.__tablename__)


def create_resource_api(resource, url, *args, **kw):
    import warnings
    warnings.warn("Deprecated: use expose_resource instead", DeprecationWarning)
    expose_resource(url, resource, *args, **kw)


def resource_collection_factory(resource_model, serializer, db_session):
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

    get_specs_dict = gen_spec(resource_model, 'GET_Collection')
    post_specs_dict = gen_spec(resource_model, 'POST')

    class _ResourceCollection(Resource):
        """
        flask-restful resource class that receives a SQLAlchemy model class and define the API to provide LIST and
        CREATE over data of that class
        """
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


def resource_item_factory(resource_model, serializer, db_session):
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
    get_specs_dict = gen_spec(resource_model, 'GET')
    put_specs_dict = gen_spec(resource_model, 'PUT')
    del_specs_dict = gen_spec(resource_model, 'DELETE')

    class _ResourceItem(Resource):
        """
        flask-restful resource class that receives receives a SQLAlchemy model class and define the API to provide GET,
        UPDATE and DELETE over a single data identified by id
        """
        _resource_model = resource_model
        _resource_tags = None
        _serializer = serializer

        # @auth_token_required
        # @swag_from(get_specs_dict)
        def get(self, id):
            with Permission(CanRead(self._resource_tags)):
                data = self._resource_model.query.filter_by(id=id).first()
                if data:
                    return self._serializer.dump(data).data
                return '', 404

        # @auth_token_required
        # @swag_from(put_specs_dict)
        def put(self, id):
            with Permission(CanWrite(self._resource_tags)):
                data = self._resource_model.query.filter_by(id=id).first()
                if data:
                    args = load_request_data(request)
                    args, nested_args = split_nested(args)
                    for key, value in nested_args.items():
                        if key in data.__mapper__.relationships:
                            setattr(data, key, data.__mapper__.relationships[key].argument(**value))
                    for k in args.keys():
                        setattr(data, k, args[k])
                    db_session.add(data)
                    db_session.commit()
                    return self._serializer.dump(data).data
                return '', 404

        # @auth_token_required
        # @swag_from(del_specs_dict)
        def delete(self, id):
            with Permission(CanWrite(self._resource_tags)):
                data = self._resource_model.query.filter_by(id=id).first()
                if data:
                    db_session.delete(data)
                    db_session.commit()
                    return '', 204
                return '', 404

    return _ResourceItem
