from flask import request
from flask_restful import Resource
from .utils import load_request_data, query_from_request, split_nested


class BaseResource(Resource):

    def __init__(self, declarative_model, serializer, session):
        self._resource_model = declarative_model
        self._serializer = serializer
        self._db_session = session


class ItemResource(BaseResource):
    """
    flask-restful resource class that receives receives a SQLAlchemy model class and define the API to provide GET,
    UPDATE and DELETE over a single data identified by id
    """

    def get(self, id):
        data = self._resource_model.query.filter_by(id=id).first()
        if data:
            return self._serializer.dump(data).data
        return '', 404

    def put(self, id):
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

    def delete(self, id):
        data = self._resource_model.query.filter_by(id=id).first()
        if data:
            session = self._db_session
            session.delete(data)
            session.commit()
            return '', 204
        return '', 404


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
        session = self._db_session
        args = load_request_data(request)
        args, nested_args = split_nested(args)
        obj = self._serializer.load(args, session=session).data
        session.add(obj)
        session.commit()
        serialized = self._serializer.dump(obj).data
        return serialized, 201
