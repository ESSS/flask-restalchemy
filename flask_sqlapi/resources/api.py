from flask_restful import Api as RestfulApi
from marshmallow_sqlalchemy import ModelSchema

from flask_sqlapi.resources.resourcebase import resource_collection_factory, resource_item_factory


class Api(object):

    def __init__(self, app, prefix='', errors=None, request_decorators=None):
        self.restful_api = RestfulApi(app=app, prefix=prefix, decorators=request_decorators,
                                      default_mediatype='application/json', errors=errors)
        self._db = app.extensions['sqlalchemy'].db

    def add_model(self, model, collection_name=None, serializer=None, request_decorators=None):
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
        """
        restful = self.restful_api
        collection_name = collection_name or model.__tablename__
        if not serializer:
            serializer = self.create_default_serializer(model)()
        url = '/' + collection_name.lower()

        ResourceCollectionClass = resource_collection_factory(model, serializer, self._db.session,
                                                              resource_decorators=request_decorators)
        restful.add_resource(
            ResourceCollectionClass, url,
            endpoint=collection_name + '_collection',
        )
        restful.add_resource(
            resource_item_factory(), url + '/<id>',
            endpoint=collection_name,
            resource_class_args=(model, serializer, self._db.session)
        )

    @staticmethod
    def create_default_serializer(declarative):
        class Meta(object):
            model = declarative
            include_fk = True

        schema_class_name = '{}Schema'.format(declarative.__name__)
        schema_class = type(
            schema_class_name,
            (ModelSchema,),
            {'Meta': Meta}
        )
        return schema_class
