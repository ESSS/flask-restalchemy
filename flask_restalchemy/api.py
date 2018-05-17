from flask_restful import Api as RestfulApi

from flask_restalchemy.resources.resources import CollectionResource, ItemResource, CollectionRelationResource, \
    ItemRelationResource, CollectionPropertyResource
from flask_restalchemy.serialization.modelserializer import ModelSerializer


class Api(object):

    def __init__(self, app_or_bp=None, prefix='', errors=None, request_decorators=None):
        """
        :param (Flask|Blueprint) app_or_bp: Flask application or Blueprint

        :param str prefix: API endpoints prefix

        :param errors: A dictionary to define a custom response for each
            exception or error raised during a request

        :param callable request_decorators: request decorators for this API object (see
            Flask-Restful decorators docs for more information)
        """
        self.restful_api = RestfulApi(app=app_or_bp, prefix=prefix, decorators=request_decorators,
                                      default_mediatype='application/json', errors=errors)
        if app_or_bp:
            self.init_app(app_or_bp)
        self._db = None

    def init_app(self, app):
        self.restful_api.init_app(app)

    def add_model(self, model, url=None, serializer_class=None, request_decorators=None,
                  collection_decorators=None, collection_name=None):
        """
        Create API endpoints for the given SQLAlchemy declarative class.


        :param class model: the SQLAlchemy declarative class

        :param string url: one or more url routes to match for the resource, standard
             flask routing rules apply. Defaults to model name in lower case.

        :param string collection_name: custom name for the collection endpoint url definition, if not set the model
            table name will be used

        :param Type[ModelSerializer] serializer_class: If `None`, a default serializer will be created.

        :param list|dict request_decorators: decorators to be applied to HTTP methods. Could be a list of decorators
            or a dict mapping HTTP method types to a list of decorators (dict keys should be 'get', 'post' or 'put').
            See https://flask-restful.readthedocs.io/en/latest/extending.html#resource-method-decorators for more
            details.

        :param list|dict collection_decorators: decorators to be applied to HTTP methods for collections. It defaults to
            request_decorators value.
        """
        restful = self.restful_api
        collection_name = collection_name or model.__tablename__
        if not serializer_class:
            serializer = self.create_default_serializer(model)
        else:
            serializer = serializer_class(model)
        url = url or '/' + collection_name.lower()

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
            endpoint=collection_name + '-list',
            resource_class_args=(model, serializer, self.get_db_session),
        )
        restful.add_resource(
            _ItemResource,
            url + '/<id>',
            endpoint=collection_name,
            resource_class_args=(model, serializer, self.get_db_session)
        )

    def add_relation(self, relation_property, url_rule=None, serializer_class=None, request_decorators=None,
                     collection_decorators=None, endpoint_name=None):
        """
        Create API endpoints for the given SQLAlchemy relationship.

        :param relation_property: model relationship representing the collection to receive the CRUD operations

        :param string url_rule: one or more url routes to match for the resource, standard
             flask routing rules apply. Defaults to model name in lower case.

        :param Type[ModelSerializer] serializer_class: If `None`, a default serializer will be created.

        :param list|dict request_decorators: decorators to be applied to HTTP methods. Could be a list of decorators
            or a dict mapping HTTP method types to a list of decorators (dict keys should be 'get', 'post' or 'put').
            See https://flask-restful.readthedocs.io/en/latest/extending.html#resource-method-decorators for more
            details.

        :param list|dict collection_decorators: decorators to be applied to HTTP methods for collections. It defaults to
            request_decorators value.

        :param string endpoint_name: endpoint name (defaults to :meth:`{model_collection_name}-{related_collection_name}-relation`
            Can be used to reference this route in :class:`fields.Url` fields

        """
        model = relation_property.prop.mapper.class_
        related_model = relation_property.class_
        model_collection_name = model.__tablename__.lower()
        related_collection_name = related_model.__tablename__.lower()
        endpoint_name = endpoint_name or '{}-{}-relation'.format(model_collection_name, related_collection_name)
        if not serializer_class:
            serializer = self.create_default_serializer(model)
        else:
            serializer = serializer_class(model)
        if url_rule:
            assert '<relation_id>' in url_rule
        else:
            url_rule = '/{}/<relation_id>/{}'.format(related_collection_name, relation_property.key)

        if not request_decorators:
            request_decorators = []
        if not collection_decorators:
            collection_decorators = request_decorators

        class _CollectionRelationResource(CollectionRelationResource):
            method_decorators = collection_decorators

        class _ItemRelationResource(ItemRelationResource):
            method_decorators = collection_decorators

        self._add_item_collection_resources(
            _ItemRelationResource,
            _CollectionRelationResource,
            url_rule,
            endpoint_name,
            resource_init_args=(relation_property, serializer, self.get_db_session),
        )

    def _add_item_collection_resources(self, item_resource, collection_resource, url_rule, endpoint,
                                       resource_init_args):
        self.add_resource(
            item_resource,
            url_rule + '/<id>',
            endpoint=endpoint,
            resource_class_args=resource_init_args,
        )
        self.add_resource(
            collection_resource,
            url_rule,
            endpoint=endpoint + '-list',
            resource_class_args=resource_init_args,
        )

    def add_property(self, model, related_model, property_name, url_rule=None, serializer_class=None, request_decorators=[]):
        if not serializer_class:
            serializer = self.create_default_serializer(model)
        else:
            serializer = serializer_class(model)
        related_collection_name = related_model.__tablename__.lower()
        if url_rule:
            assert '<relation_id>' in url_rule
        else:
            url_rule = '/{}/<relation_id>/{}'.format(related_collection_name, property_name.lower())

        class _CollectionPropertyResource(CollectionPropertyResource):
            method_decorators = request_decorators

        self.add_resource(
            _CollectionPropertyResource,
            url_rule,
            endpoint='{}-{}-property'.format(related_collection_name, property_name),
            resource_class_args=(model, related_model, property_name, serializer, self.get_db_session)
        )

    def add_resource(self, *args, **kw):
        self.restful_api.add_resource(*args, **kw)

    @staticmethod
    def create_default_serializer(model_class):
        """
        Create a default serializer for the given SQLAlchemy declarative class. Recipe based on
        https://marshmallow-sqlalchemy.readthedocs.io/en/latest/recipes.html#automatically-generating-schemas-for-sqlalchemy-models

        :param model_class: the SQLAlchemy mapped class

        :rtype: class
        """
        return ModelSerializer(model_class)

    def get_db_session(self):
        """
        Returns an SQLAlchemy object session. Used by flask-restful Resources to access
        the database.
        """
        if not self._db:
            # Get the Flask application
            if self.restful_api.blueprint_setup:
                flask_app = self.restful_api.blueprint_setup.app
            else:
                flask_app = self.restful_api.app
            assert flask_app and flask_app.extensions, "Flask App not initialized yey"
            self._db = flask_app.extensions['sqlalchemy'].db
        return self._db.session
