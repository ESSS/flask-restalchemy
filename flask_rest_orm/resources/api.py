from flask_restful import Api as RestfulApi
from marshmallow_sqlalchemy import ModelSchema

from flask_rest_orm.resources.resourcebase import CollectionResource, ItemResource


class Api(object):

    def __init__(self, app, prefix='', errors=None, request_decorators=None):
        self.restful_api = RestfulApi(app=app, prefix=prefix, decorators=request_decorators,
                                      default_mediatype='application/json', errors=errors)
        self._db = app.extensions['sqlalchemy'].db

    def add_model(self, model, collection_name=None, serializer=None, request_decorators=None,
                  collection_decorators=None):
        """
        Create API endpoints for the given SQLAlchemy model class.

        :param class model: the SQLAlchemy declarative class

        :param string collection_name: name of the endpoint (defaults to model name in lower case)

        :param ModelSchema serializer: Marshmallow schema for serialization. If `None`, a default serializer will be
            created.

        :param list|dict request_decorators: decorators to be applied to HTTP methods. Could be a list of decorators
            or a dict mapping HTTP method types to a list of decorators (dict keys should be 'get', 'post' or 'put').
            See https://flask-restful.readthedocs.io/en/latest/extending.html#resource-method-decorators for more
            details.

        :param list|dict collection_decorators: decorators to be applied to HTTP methods for collections. It defaults to
            request_decorators value.
        """
        restful = self.restful_api
        collection_name = collection_name or model.__tablename__
        if not serializer:
            serializer = self.create_default_serializer(model)()
        url = '/' + collection_name.lower()

        if not request_decorators:
            request_decorators = []
        if not collection_decorators:
            collection_decorators = request_decorators

        class _CollectionResource(CollectionResource):
            method_decorators = collection_decorators

        class _ItemResource(ItemResource):
            method_decorators = request_decorators

        restful.add_resource(
            _CollectionResource,
            url,
            endpoint=collection_name + '_collection',
            resource_class_args=(model, serializer, self._db.session),
        )
        restful.add_resource(
            _ItemResource,
            url + '/<id>',
            endpoint=collection_name,
            resource_class_args=(model, serializer, self._db.session)
        )

    @staticmethod
    def create_default_serializer(model_class):
        """
        Create a default serializer for the given SQLAlchemy declarative class. Recipe based onn
        https://marshmallow-sqlalchemy.readthedocs.io/en/latest/recipes.html#automatically-generating-schemas-for-sqlalchemy-models

        :param model_class: the SQLAlchemy declarative class

        :rtype: class
        """
        class Meta(object):
            model = model_class
            include_fk = True

        schema_class_name = '{}Schema'.format(model_class.__name__)
        schema_class = type(
            schema_class_name,
            (ModelSchema,),
            {'Meta': Meta}
        )
        return schema_class
