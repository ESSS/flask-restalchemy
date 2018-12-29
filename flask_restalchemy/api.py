
from flask_restalchemy.resourcefactory import property_resource_factory
from flask_restalchemy.resources import ToManyRelationResource, ModelResource, \
    CollectionPropertyResource
from flask_restalchemy.serialization import ColumnSerializer
from flask_restalchemy.serialization.datetimeserializer import is_datetime_field, DateTimeSerializer
from flask_restalchemy.serialization.enumserializer import is_enum_field, EnumSerializer


class Api(object):

    def __init__(self, blueprint=None, prefix='', errors=None, request_decorators=None):
        """
        :param (Flask|Blueprint) blueprint: Flask application or Blueprint

        :param str prefix: API endpoints prefix

        :param errors: A dictionary to define a custom response for each
            exception or error raised during a request

        :param callable request_decorators: request decorators for this API object (see
            Flask-Restful decorators docs for more information)
        """
        self.default_mediatype = 'application/json'
        self._blueprint = blueprint
        self._db = None

    def init_app(self, blueprint):
        self._blueprint = blueprint

    def add_model(self, model, url=None, serializer_class=None, request_decorators=None,
                  collection_decorators=None, collection_name=None, preprocessors=None, postprocessors=None):
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

        :param preprocessors: A dict with the lists of callable preprocessors for each API method

        :param postprocessors: A dict with the lists of callable postprocessors for each API method
        """
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

        view_func = ModelResource.as_view(collection_name, model, serializer, self.get_db_session)
        self.register_view(view_func, url)

    def add_relation(self, relation_property, url_rule=None, serializer_class=None,
                     request_decorators=None, collection_decorators=None, endpoint_name=None,
                     preprocessors=None, postprocessors=None):
        """
        Create API endpoints for the given SQLAlchemy relationship.

        :param relation_property: model relationship representing the collection to receive the
            CRUD operations.

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
        view_name = "{}.{}".format(model.__tablename__, related_model.__tablename__).lower()

        if not serializer_class:
            serializer = self.create_default_serializer(model)
        else:
            serializer = serializer_class(model)
        if url_rule:
            assert '<relation_id>' in url_rule
        else:
            parent_endpoint = related_model.__tablename__.lower()
            url_rule = '/{}/<relation_id>/{}'.format(parent_endpoint, relation_property.key)
        endpoint_name = endpoint_name or url_rule

        if not request_decorators:
            request_decorators = []
        if not collection_decorators:
            collection_decorators = request_decorators

        view_func = ToManyRelationResource.as_view(
            view_name, relation_property, serializer, self.get_db_session
        )
        self.register_view(view_func, url_rule)

    def add_property(self, property_type, model, property_name, url_rule=None,
                     serializer_class=None, request_decorators=[], endpoint_name=None,
                     preprocessors=None, postprocessors=None):
        if not serializer_class:
            serializer = self.create_default_serializer(property_type)
        else:
            serializer = serializer_class(property_type)
        view_name = "{}.{}".format(model.__tablename__, property_name).lower()
        if url_rule:
            assert '<relation_id>' in url_rule
        else:
            parent_endpoint = (model.__tablename__.lower())
            url_rule = '/{}/<relation_id>/{}'.format(parent_endpoint, property_name.lower())

        endpoint = endpoint_name or url_rule

        view_func = CollectionPropertyResource.as_view(
            view_name, property_type, model, property_name, serializer,  self.get_db_session
        )
        self.register_view(view_func, url_rule)

    def add_resource(self, *args, **kw):
        self.restful_api.add_resource(*args, **kw)

    def register_view(self, view_func, url, pk='id', pk_type='int'):
        app = self._blueprint
        app.add_url_rule(url, defaults={pk: None}, view_func=view_func, methods=['GET', ])
        app.add_url_rule(url, view_func=view_func, methods=['POST', ])
        app.add_url_rule('%s/<%s:%s>' % (url, pk_type, pk), view_func=view_func,
                         methods=['GET', 'PUT', 'DELETE']
                         )


    @staticmethod
    def create_default_serializer(model_class):
        """
        Create a default serializer for the given SQLAlchemy declarative class. Recipe based on
        https://marshmallow-sqlalchemy.readthedocs.io/en/latest/recipes.html#automatically-generating-schemas-for-sqlalchemy-models

        :param model_class: the SQLAlchemy mapped class

        :rtype: class
        """
        from flask_restalchemy.serialization.modelserializer import ModelSerializer
        return ModelSerializer(model_class)

    def get_db_session(self):
        """
        Returns an SQLAlchemy object session. Used by flask-restful Resources to access
        the database.
        """
        if not self._db:
            # Get the Flask application
            flask_app = self._blueprint
            assert flask_app and flask_app.extensions, "Flask App not initialized yey"
            self._db = flask_app.extensions['sqlalchemy'].db
        return self._db.session

    _FIELD_SERIALIZERS = [
        (DateTimeSerializer, is_datetime_field),
        (EnumSerializer, is_enum_field)
    ]

    @classmethod
    def register_column_serializer(cls, serializer_class, predicate):
        '''
        Register a serializer for a given column to be used globally by ModelSerializers

        :param Type[ColumnSerializer] serializer_class: the Serializer class
        :param callable predicate: a function that receives a column type and returns True if the
            given serializer is valid for that column
        '''
        if not issubclass(serializer_class, ColumnSerializer):
            raise TypeError('Invalid serializer class')
        cls._FIELD_SERIALIZERS.append((serializer_class, predicate))


    @classmethod
    def find_column_serializer(cls, column):
        '''
        :param Column column: search for a registered serializer for the given column

        :rtype: ColumnSerializer
        '''
        for serializer_class, predicate in reversed(cls._FIELD_SERIALIZERS):
            if predicate(column):
                return serializer_class(column)
        else:
            return None
