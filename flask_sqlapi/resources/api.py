from flask_restful import Api as RestfulApi

from flask_sqlapi.resources.resourcebase import resource_collection_factory, resource_item_factory


class Api(object):


    def __init__(self, app=None, prefix='', errors=None):
        self.restful_api = RestfulApi(app=app, prefix=prefix, default_mediatype='application/json', errors=errors)


    def add_model(self, model, collection_name=None):
        collection_name = collection_name or model.__tablename__
        restful = self.restful_api
        url = '/' + collection_name
        ResourceCollectionClass = resource_collection_factory(model)
        restful.add_resource(ResourceCollectionClass, url, collection_name + '_collection')
        ResourceItemClass = resource_item_factory(model)
        restful.add_resource(ResourceItemClass, url + '/<id>', collection_name)
