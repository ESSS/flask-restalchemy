from flask import request, json
from flask_restful import Resource
from .utils import query_from_request


class BaseResource(Resource):

    def __init__(self, declarative_model, serializer, session):
        self._resource_model = declarative_model
        self._serializer = serializer
        self._db_session = session

    def save_from_request(self, req):
        if req.data:
            request_data = json.loads(req.data.decode('utf-8'))
        else:
            request_data = req.form.to_dict()
        session = self._db_session
        model_obj = self._serializer.load(request_data, session).data
        session.add(model_obj)
        session.commit()
        return self._serializer.dump(model_obj).data


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
            saved = self.save_from_request(request)
            return saved
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
        saved = self.save_from_request(request)
        return saved, 201
