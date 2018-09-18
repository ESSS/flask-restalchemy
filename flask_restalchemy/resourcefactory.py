from .serialization.swagger_spec import gen_spec


def item_resource_factory(item_resource_class, serializer, item_decorators = None):
    '''
    Creates a new Resource class in runtime to allow use of Flasgger to automatic generate Swagger specs,
    since Flaggers needs a different resource class for each REST resource.

    Note: this is inefficient and makes the code harder to read. See #26

    :param item_resource_class:
    :param ModelSerializer serializer:
    :param item_decorators:
    '''

    item_decorators = item_decorators or []

    class _ItemResource(item_resource_class):
        method_decorators = item_decorators

        def get(self, **kw): return item_resource_class.get(self, **kw)

        def put(self, **kw): return item_resource_class.put(self, **kw)

        def delete(self, **kw): return item_resource_class.delete(self, **kw)

        get.specs_dict = gen_spec(serializer, "GET")
        put.specs_dict = gen_spec(serializer, "PUT")
        delete.specs_dict = gen_spec(serializer, "DELETE")

    return _ItemResource


def collection_resource_factory(collection_resource_class, serializer, collection_decorators=None):
    '''
    Creates a new Resource class in runtime to allow use of Flasgger to automatic generate Swagger specs,
    since Flaggers needs a different resource class for each REST resource.

    Note: this is inefficient and makes the code harder to read. See #26

    :param collection_resource_class:
    :param ModelSerializer serializer:
    :param collection_decorators:
    '''

    class _CollectionResource(collection_resource_class):
        method_decorators = collection_decorators

        def get(self, **kw): return collection_resource_class.get(self, **kw)

        def post(self, **kw): return collection_resource_class.post(self, **kw)

        get.specs_dict = gen_spec(serializer, "GET_Collection")
        post.specs_dict = gen_spec(serializer, "POST")


    return _CollectionResource
