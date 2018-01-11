import json

from flasgger import swag_from
from flask_allows import Permission
from flask_restful import Resource, request
from rfdap_dataservice.resources.utils import RequestException, load_request_data, split_nested
from rfdap_dataservice.services.api import api
from rfdap_dataservice.services.authservice import auth_token_required
from rfdap_dataservice.services.docgeneration import gen_spec
from rfdap_dataservice.services.security import CanRead, CanWrite
from sqlalchemy import text

from ..declarative_base import db


def expose_child_resource(url, child_mapper, child_fk, association_column=None, tags=None):
    """
    This function creates the API for the given sqlalchemy resource model associated with the given parent
    resource model and serve it in the given url, it also associates the resource with the given tags in order to
    verify authorization over the resource.
    Needed when the url to access the resource has the format '/<parent_resource_url>/<parent_id>/<resource_url>'.
    The association between parent and child resource is given by the match of the values of the fields
    parent_in and child_in


    :param string url:
        url route to match for the resource, standard flask routing rules apply.

    :param class child_mapper:
        SQLAlchemy mapper class

    :param string child_fk:
        `child_mapper` foreign key to the parent resource (or to the association item in many-to-many relations).

    :param InstrumentedAttribute association_column:
        Optional field to be used only if `fk_column_name` doesn't refers to the parent primary key (many-to-many
        relationships).

    :param list tags:
        list of tags to be associated to the resource

    .. note::
    A factory is needed because the documentation is associated with the class methods and shared by its objects.
    Then a unique class is created for each sqlalchemy resource, otherwise documentation would be shared by all the
    resources.
    """

    get_list_specs_dict = gen_spec(child_mapper, 'GET_Collection', is_child=True)
    post_specs_dict = gen_spec(child_mapper, 'POST', is_child=True)
    get_specs_dict = gen_spec(child_mapper, 'GET', is_child=True)
    put_specs_dict = gen_spec(child_mapper, 'PUT', is_child=True)
    del_specs_dict = gen_spec(child_mapper, 'DELETE', is_child=True)

    if association_column:
        parent_mapper = association_column.class_
        association_fk = association_column.expression.key
    else:
        parent_mapper = getattr(child_mapper, child_fk).parent.class_
        association_fk = None

    class _ResourceCollection(Resource):
        """
        flask-restful resource class that receives two SQLAlchemy models, a parent model and a child model,
        and define the API to provide LIST and CREATE over data of the child model associated with a specific
        element of the parent model.
        """

        _child_fk = child_fk
        _child_mapper = child_mapper
        _parent_mapper = parent_mapper
        _association_fk = association_fk
        _resource_tags = tags


        def __repr__(self):
            return self._child_mapper.__name__ + self.__class__.__name__


        @auth_token_required
        @swag_from(get_list_specs_dict)
        def get(self, parent_id):
            with Permission(CanRead(self._resource_tags)):
                parent = db.session.query(self._parent_mapper).get(parent_id)
                if parent is None:
                    return {'msg': 'Parent resource does not exist!'}, 400
                if self._association_fk:
                    fk_value = getattr(parent, self._association_fk)
                else:
                    fk_value = parent_id
                fk_column = self._child_fk
                filter_text = "{fk_column} = {fk_value}".format(**locals())
                data = db.session.query(self._child_mapper).filter(text(filter_text)).all()
                return data


        @auth_token_required
        @swag_from(post_specs_dict)
        def post(self, parent_id):
            with Permission(CanWrite(self._resource_tags)):
                parent = db.session.query(self._parent_mapper).get(parent_id)
                if not parent:
                    return {'msg': 'Parent resource does not exist!'}, 400
                if self._association_fk:
                    fk_value = getattr(parent, self._association_fk)
                else:
                    fk_value = parent_id
                args = load_request_data(request)
                args[self._child_fk] = fk_value
                data = self._child_mapper(**args)
                db.session.add(data)
                db.session.commit()
                return data, 201

    class _ResourceItem(Resource):
        """
        flask-restful resource class that receives two SQLAlchemy models, a parent model and a child model,
        and define the API to provide GET, PUT and DELETE operations over data of the child model associated with a
        specific element of the parent model.
        """

        _child_fk = child_fk
        _child_mapper = child_mapper
        _parent_mapper = parent_mapper
        _association_fk = association_fk
        _resource_tags = tags


        def __repr__(self):
            return self._child_mapper.__name__ + self.__class__.__name__


        def query_valid_child(self, parent_id, id):
            parent = db.session.query(self._parent_mapper).get(parent_id)
            if parent is None:
                raise RequestException('Parent resource does not exist!', 400)

            child = db.session.query(self._child_mapper).get(id)
            if child is None:
                raise RequestException('Child not found!', 404)

            if self._association_fk:
                fk_value = getattr(parent, self._association_fk)
            else:
                fk_value = int(parent_id)
            if getattr(child, self._child_fk) != fk_value:
                raise RequestException('Child is not from this parent!', 400)

            return child


        @auth_token_required
        @swag_from(get_specs_dict)
        def get(self, parent_id, id):
            with Permission(CanRead(self._resource_tags)):
                try:
                    child = self.query_valid_child(parent_id, id)
                except RequestException as err:
                    return {'msg': err.msg}, err.error_code

                return child


        @auth_token_required
        @swag_from(put_specs_dict)
        def put(self, parent_id, id):
            with Permission(CanWrite(self._resource_tags)):
                try:
                    child = self.query_valid_child(parent_id, id)
                except RequestException as err:
                    return {'msg': err.msg}, err.error_code

                args = load_request_data(request)
                args, nested_args = split_nested(args)
                for key, value in nested_args.items():
                    if key in child.__mapper__.relationships:
                        setattr(child, key, child.__mapper__.relationships[key].argument(**value))
                for k in args.keys():
                    setattr(child, k, args[k])
                db.session.add(child)
                db.session.commit()
                return child


        @auth_token_required
        @swag_from(del_specs_dict)
        def delete(self, parent_id, id):
            with Permission(CanWrite(self._resource_tags)):
                try:
                    child = self.query_valid_child(parent_id, id)
                except RequestException as err:
                    return {'msg': err.msg}, err.error_code

                db.session.delete(child)
                db.session.commit()
                return '', 204


    endpoint_name = "{}_{}_list".format(parent_mapper.__tablename__, child_mapper.__tablename__)
    api.add_resource(_ResourceCollection, url, endpoint=endpoint_name)

    endpoint_name = "{}_{}".format(parent_mapper.__tablename__, child_mapper.__tablename__)
    api.add_resource(_ResourceItem, url + '/<id>', endpoint=endpoint_name)
