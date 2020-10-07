import warnings

from flask import request, json, jsonify, Response
from flask.views import MethodView
from sqlalchemy.orm import load_only
from sqlalchemy.orm.collections import InstrumentedList

from flask_restalchemy.serialization import ModelSerializer
from .querybuilder import create_collection_query


class BaseResource(MethodView):
    """The Base class for resources

    :param dict|list request_decorators: a list of decorators
    """

    def __init__(self, request_decorators=None):
        if not request_decorators:
            return
        for verb, decorator_list in request_decorators.items():
            for decorator in decorator_list:
                if verb == "ALL":
                    self.dispatch_request = decorator(self.dispatch_request)
                else:
                    verb_method_name = verb.lower()
                    decorated_method = decorator(getattr(self, verb_method_name))
                    setattr(self, verb_method_name, decorated_method)

    def dispatch_request(self, *args, **kwargs):
        view_response = super().dispatch_request(*args, **kwargs)
        data, code, header = unpack(view_response)
        if isinstance(data, Response):
            return data
        elif isinstance(data, str):
            return data, code, header
        else:
            return jsonify(data), code, header


class ViewFunctionResource(BaseResource):

    """
    Class created to provide url rules for free functions.

    :param callable func: function to be called

    :param dict request_decorators: dictionary of decorators for the function
    """

    def __init__(self, func, request_decorators=None):
        super().__init__(request_decorators)
        self.func = func

    def get(self, *args, **kwargs):
        return self.func(*args, **kwargs)

    def post(self, *args, **kwargs):
        return self.func(*args, **kwargs)

    def put(self, *args, **kwargs):
        return self.func(*args, **kwargs)

    def delete(self, *args, **kwargs):
        return self.func(*args, **kwargs)


class BaseModelResource(BaseResource):
    """The Base class for ORM resources

    :param class declarative_model: the SQLAlchemy declarative class.

    :param ModelSerializer serializer: schema for serialization. If `None`, a default serializer will be created.

    :param callable session_getter: a callable that returns the DB session. A callable is used since a reference to
        DB session may not be available on the resource initialization.

    :param callable query_modifier: function that returns a query and expects a `model` as parameter that
        should be used to create the query and expects a `parent_query` to be incremented with the callback query
        function. The method signature should look like this: query_callback(parent_query, resource_model)

    :param dict|list request_decorators: a list of decorators
    """

    def __init__(
        self,
        declarative_model,
        serializer,
        session_getter,
        query_modifier=None,
        request_decorators=None,
    ):
        """Constructor
        """

        super().__init__(request_decorators)
        self._resource_model = declarative_model
        self._serializer = serializer
        self._serializer.strict = True
        assert isinstance(
            self._serializer, ModelSerializer
        ), f"Invalid serializer instance: {serializer}"
        self._session_getter = session_getter
        self._query_modifier = query_modifier

    def _save_model(self, model):
        session = self._session_getter()
        session.add(model)
        session.commit()

    def _save_serialized(self, serialized_data, existing_model=None):
        model = self._serializer.load(
            serialized_data, existing_model, self._session_getter()
        )
        self._save_model(model)
        return self._serializer.dump(model)

    @property
    def _db_session(self):
        return self._session_getter()


class ModelResource(BaseModelResource):
    def get(self, id=None):
        if id is not None:
            model = self._resource_model.query.get(id)
            if model is None:
                return NOT_FOUND_ERROR, 404
            return self._serializer.dump(model)
        else:
            query = self._resource_model.query
            if self._query_modifier:
                query = self._query_modifier(query, self._resource_model)
            query = create_collection_query(
                query, self._resource_model, self._serializer, request.args
            )

            return create_response_from_query(query, self._serializer)

    def post(self):
        serialized = load_request_json()
        saved = self._save_serialized(serialized)
        return saved, 201

    def put(self, id):
        model = self._resource_model.query.get(id)
        if model is None:
            return NOT_FOUND_ERROR, 404

        serialized = self._serializer.dump(model)
        request_data = load_request_json()
        serialized.update(request_data)
        result = self._save_serialized(serialized, existing_model=model)
        return result

    def delete(self, id):
        model = self._resource_model.query.get(id)
        if model is None:
            return NOT_FOUND_ERROR, 404
        session = self._db_session
        session.delete(model)
        session.flush()
        session.commit()
        return "", 204


class ToManyRelationResource(BaseModelResource):
    """Resource class that receives an SQLAlchemy relationship define the API to provide
    LIST and CREATE over data of the child model associated with a specific
    element of the parent model.

    :param relationship relation_property: the SQLAlchemy relationship.

    :param ModelSerializer serializer: schema for serialization. If `None`, a default serializer will be created.

    :param callable session_getter: a callable that returns the DB session. A callable is used since a reference to
        DB session may not be available on the resource initialization.

    :param callable query_modifier: function that returns a query and expects a `model` as parameter that
        should be used to create the query and expects a `parent_query` to be incremented with the callback query
        function. The method signature should look like this: query_callback(parent_query, resource_model)

    :param dict|list request_decorators: a list of decorators
    """

    def __init__(
        self,
        relation_property,
        serializer,
        session_getter,
        query_modifier=None,
        request_decorators=None,
    ):
        """Constructor
        """
        resource_model = relation_property.prop.mapper.class_
        super().__init__(
            resource_model,
            serializer,
            session_getter,
            query_modifier=query_modifier,
            request_decorators=request_decorators,
        )
        self._relation_property = relation_property
        self._related_model = relation_property.class_

    def get(self, relation_id, id=None):
        if id:
            requested_obj = self._query_related_obj(relation_id, id)
            if not requested_obj:
                return NOT_FOUND_ERROR, 404
            return self._serializer.dump(requested_obj), 200
        else:
            session = self._db_session
            # using options(load_only('id')) avoid unintended subquerying, as all we want is
            # check if the element exists
            related_obj = (
                session.query(self._related_model)
                .options(load_only("id"))
                .get(relation_id)
            )
            if related_obj is None:
                return NOT_FOUND_ERROR, 404

            # TODO: Is there a more efficient way than using getattr?
            relation_list_or_query = getattr(related_obj, self._relation_property.key)
            if isinstance(relation_list_or_query, InstrumentedList) or not hasattr(
                relation_list_or_query, "paginate"
            ):
                warnings.warn(
                    "Warnning: relationship does not support pagination nor filter."
                    'Use flask-sqlalchemy relationship with lazy="dynamic".'
                )
                collection = [
                    self._serializer.dump(item) for item in relation_list_or_query
                ]
            else:
                query = relation_list_or_query
                if self._query_modifier:
                    query = self._query_modifier(query, self._resource_model)
                query = create_collection_query(
                    query, self._resource_model, self._serializer, request.args
                )
                collection = create_response_from_query(query, self._serializer)
            return collection

    def post(self, relation_id):
        session = self._db_session
        related_obj = session.query(self._related_model).get(relation_id)
        if not related_obj:
            return NOT_FOUND_ERROR, 404
        collection = getattr(related_obj, self._relation_property.key)
        data_dict = load_request_json()
        resource_id = data_dict.get("id", None)

        if resource_id is not None:
            model = session.query(self._resource_model).get(resource_id)
            if model is None:
                return NOT_FOUND_ERROR, 404
            status_code = 200
        else:
            model = self._serializer.load(data_dict, session=session)
            status_code = 201
            session.add(model)
        collection.append(model)
        self._save_model(model)
        saved = self._serializer.dump(model)
        return saved, status_code

    def put(self, relation_id, id):
        request_data = load_request_json()
        requested_obj = self._query_related_obj(relation_id, id)
        if not requested_obj:
            return NOT_FOUND_ERROR, 404
        serialized = self._serializer.dump(requested_obj)
        serialized.update(request_data)
        saved = self._save_serialized(serialized, requested_obj)
        return saved

    def delete(self, relation_id, id):
        session = self._db_session
        requested_obj = self._query_related_obj(relation_id, id)
        if not requested_obj:
            return NOT_FOUND_ERROR, 404
        related_obj = session.query(self._related_model).get(relation_id)
        collection = getattr(related_obj, self._relation_property.key)
        collection.remove(requested_obj)
        session.delete(requested_obj)
        session.commit()
        return "", 204

    def _query_related_obj(self, relation_id, id):
        """
        Query resource model by ID but also add the relationship as a query constrain.

        :param relation_id: id of the related model
        :param id: id of the model being required
        :return: model with 'id' that has a related model with 'related_id'
        """

        # This checks if there is a parent with the related child on its relation property
        related = (
            self._db_session.query(self._related_model)
            .options(load_only("id"))
            .filter(
                self._related_model.id == relation_id,
                self._relation_property.any(id=id),
            )
            .one_or_none()
        )

        if related is None:
            return None

        return self._db_session.query(self._resource_model).get(id)


class CollectionPropertyResource(ToManyRelationResource):
    def __init__(
        self,
        declarative_model,
        related_model,
        property_name,
        serializer,
        session_getter,
        query_modifier=None,
        request_decorators=None,
    ):
        super(ToManyRelationResource, self).__init__(
            declarative_model,
            serializer,
            session_getter,
            query_modifier=query_modifier,
            request_decorators=request_decorators,
        )
        self._related_model = related_model
        self._property_name = property_name

    def get(self, relation_id, id=None):
        session = self._db_session
        related_obj = session.query(self._related_model).get(relation_id)
        if related_obj is None:
            return NOT_FOUND_ERROR, 404
        relation_list_or_query = getattr(related_obj, self._property_name)
        if isinstance(relation_list_or_query, InstrumentedList) or not hasattr(
            relation_list_or_query, "paginate"
        ):
            warnings.warn(
                "Warnning: property "
                + self._property_name
                + " does not support pagination nor filter."
                " Use flask-sqlalchemy and make your property return a query object"
            )
            collection = [
                self._serializer.dump(item) for item in relation_list_or_query
            ]
        else:
            query = relation_list_or_query
            if self._query_modifier:
                query = self._query_modifier(query, self._related_model)
            query = create_collection_query(
                query, self._resource_model, self._serializer, request.args
            )
            collection = create_response_from_query(query, self._serializer)
        return collection

    def post(self, relation_id):
        return "POST not allowed for property resources", 405


def load_request_json():
    """
    Returns request data as dict.

    :rtype: dict
    """
    if request.data:
        return json.loads(request.data.decode("utf-8"))
    else:
        return request.form.to_dict()


def unpack(value):
    """
    Return a three tuple of data, code, and headers

    :param value:
    :return:
    """
    if not isinstance(value, tuple):
        return value, 200, {}

    try:
        data, code, headers = value
        return data, code, headers
    except ValueError:
        pass

    try:
        data, code = value
        return data, code, {}
    except ValueError:
        pass

    return value, 200, {}


def create_response_from_query(query, serializer):
    if "page" in request.args:
        data = query.paginate()
        return {
            "page": data.page,
            "per_page": data.per_page,
            "count": data.total,
            "results": [serializer.dump(item) for item in data.items],
        }
    else:
        data = query.all()
        return [serializer.dump(item) for item in data]


NOT_FOUND_ERROR = "Resource not found in the database!"
