from flask_restful import Api as RestfulApi
from marshmallow_sqlalchemy import ModelSchema

from flask_sqlapi.resources.resourcebase import resource_collection_factory, resource_item_factory


class Api(object):


    def __init__(self, app, prefix='', errors=None):
        self.restful_api = RestfulApi(app=app, prefix=prefix, default_mediatype='application/json', errors=errors)
        self._db = app.extensions['sqlalchemy'].db

    def add_model(self, model, collection_name=None, serializer=None):
        if not serializer:
            serializer = self.create_default_serializer(model)

        collection_name = collection_name or model.__tablename__
        restful = self.restful_api
        url = '/' + collection_name.lower()
        ResourceCollectionClass = resource_collection_factory(model, serializer, self._db.session)
        ResourceItemClass = resource_item_factory(model, serializer, self._db.session)
        restful.add_resource(ResourceCollectionClass, url, endpoint=collection_name + '_collection')
        restful.add_resource(ResourceItemClass, url + '/<id>', endpoint=collection_name)


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
        return schema_class()