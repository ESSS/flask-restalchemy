from flask import json
from datetime import datetime
from json import JSONEncoder

from sqlalchemy import Column, LargeBinary, desc


class RequestException(Exception):
    def __init__(self, msg, error_code):
        self.msg = msg
        self.error_code = error_code


def split_nested(args):
    """
    This function is used to get the nested dicts, that are generally associated with relationships on the model

    :param dict args:
        request args dict

    :rtype: (dict, dict)
    :return:
        First dict with non-nested args, second dict with nested args
    """
    ret_args = {}
    nested_args = {}
    for key, value in args.items():
        if isinstance(value, dict):
            nested_args[key] = value
        else:
            ret_args[key] = value
    return ret_args, nested_args


def load_request_data(req):
    """
    Load data from an HTTP request

    :param req: the HTTP req
    :rtype: dict
    """
    if req.data:
        data = json.loads(req.data.decode('utf-8'))
    else:
        data = req.form.to_dict()
    # TODO remove it. Task ID: RFDAP-332
    data.pop('password', None)
    return data


def query_from_request(model, request):
    """
    Perform a filtered search in the database model table using query parameters in the http URL,
    disposed on the request args.

    It also paginate the response if a 'page' value is present in the query parameters. A 'per_page'
    value in the query parameters defines the page length, default to 20 items.

    Ordered search is available using 'order_by=<col_name>' providing the name of the model column to be the
    ordination key. A 'desc' in the query parameters make the ordination in a descending order.

    :param class model:
        SQLAlchemy model class representing a database resource

    :param request:
        Flask http request data

    :rtype: list
    :return: the items for the current page
    """
    builder = model.query
    for key in request.args:
        if hasattr(model, key):
            vals = request.args.getlist(key)  # one or many
            builder = builder.filter(getattr(model, key).in_(vals))
    if 'order_by' in request.args:
        col = getattr(model,request.args['order_by'])
        if 'desc' in request.args:
            builder = builder.order_by(desc(col))
        else:
            builder = builder.order_by(col)
    if 'page' not in request.args:
        resources = builder.all()
    else:
        resources = builder.paginate().items
    return resources


class DataJSONEncoder(JSONEncoder):
    '''
    This class is used to set the default way flask should encode datetime and SQLAlchemy model objects
    The class must be set to the app.json_encoder.
    '''
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif hasattr(obj, '__table__'):
            return self.to_dict(obj)
        return JSONEncoder.default(self, obj)

    @staticmethod
    def to_dict(obj, fields_config=None):
        data = {}

        if fields_config:
            for field_name, field in fields_config.items():
                data[field_name] = field.output(field_name, obj)

        for col_name, col in obj.__mapper__.columns.items():
            # TODO remove it. Task ID: RFDAP-332
            if col_name is 'password':
                continue
            if isinstance(col, Column) and isinstance(col.type, LargeBinary):
                continue
            data[col_name] = getattr(obj, col_name)

        for col_name, col in obj.__mapper__.relationships.items():
            if col_name.startswith('_') or col.uselist:
                continue
            data[col_name] = getattr(obj, col_name)

        property_names = [p for p in dir(obj.__class__) if isinstance(getattr(obj.__class__, p), property)]
        for prop in property_names:
            data[prop] = getattr(obj, prop)

        return data
