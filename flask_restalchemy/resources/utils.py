from sqlalchemy import desc, or_, and_
import json
import operator

# Filter operators defined on SqlAlchemy ColumnElement
SQLA_OPERATORS = {
    'like': 'like',
    'notlike': 'notlike',
    'ilike': 'ilike',
    'notilike': 'notilike',
    'is': 'is_',
    'isnot': 'isnot',
    'match': 'match',
    'startswith': 'startswith',
    'endswith': 'endswith',
    'contains': 'contains',
    'in': 'in_',
    'notin': 'notin_',
    'between': 'between',
    'eq': '__eq__',
    'ne': '__ne__',
    'gt': '__gt__',
    'ge': '__ge__',
    'lt': '__lt__',
    'le': '__le__',
}

def parse_value(value, serializer):
    if not serializer:
        return value
    if isinstance(value, list):
        return [serializer.load(item) for item in value]
    return serializer.load(value)


def get_operator(column, op_name, value, serializer):
    """
    :param column:
         SQLAlchemy ColumnElement

    :param op_name:
        Key of OPERATORS or COMPARE_OPERATORS

    :param value:
        value to be applied to the operator

    :rtype: ColumnOperators
    :return:
        returns a boolean, comparison, and other operators for ColumnElement expressions.
        ref: http://docs.sqlalchemy.org/en/latest/core/sqlelement.html#sqlalchemy.sql.operators.ColumnOperators
    """
    if not op_name:
        return column.operate(operator.eq, parse_value(value, serializer))
    elif op_name in SQLA_OPERATORS:
        op = SQLA_OPERATORS.get(op_name)
        if op == 'between':
            return column.between(parse_value(value[0], serializer), parse_value(value[1], serializer))
        return getattr(column, op)(parse_value(value, serializer))
    else:
        raise ValueError('Unknown operator {}'.format(op_name))


def get_field_serializer_or_none(serializer, field_name):
    field = serializer._fields.get(field_name)
    if not field:
        return None
    return field.serializer


def query_from_request(model, model_serializer, request, query=None):
    """
    Perform a filtered search in the database model table using query parameters in the http URL,
    disposed on the request args. The default logical operator is AND, but you can set the OR as
    in the following examples:

        a) OR -> ?filter={"$or":{"name": {"startswith": "Terrans 1"},"location": "Location 1"}}
        b) AND -> ?filter={"$and":{"name": {"ilike": "%Terrans 1%"},"location": "Location 1"}}
            or ?filter={"name": {"ilike": "%Terrans 1%"},"location": {"eq": "Location 1"}}

    It also paginate the response if a 'page' value is present in the query parameters. A 'per_page'
    value in the query parameters defines the page length, default to 20 items.

    Ordered search is available using 'order_by=<col_name>'. The minus sign ("-<col_name>") could be
    used to set descending order.

    :param class model:
        SQLAlchemy model class representing a database resource

    :param model_serializer:
        instance of model serializer

    :param request:
        Flask http request data

    :param query:
        SQLAlchemy query instance

    :rtype: list|dict
    :return: the serialized response: "if 'page' is defined in the query params, a dict with page, per page, count and results is returned,
    otherwise returns a list of serialized objects"
    """
    if not query:
        query = model.query

    def build_filter_operator(column_name, request_filter, serializer):
        if column_name == '$or':
            return or_(build_filter_operator(attr, value, serializer) for attr, value in request_filter.items())
        elif column_name == '$and':
            return and_(build_filter_operator(attr, value, serializer) for attr, value in request_filter.items())
        if isinstance(request_filter, dict):
            op_name = next(iter(request_filter))
            return get_operator(getattr(model, column_name), op_name, request_filter.get(op_name),
                                get_field_serializer_or_none(serializer, column_name))
        return get_operator(getattr(model, column_name), None, request_filter,
                            get_field_serializer_or_none(serializer, column_name))

    if 'filter' in request.args:
        filters = json.loads(request.args['filter'])
        for attr, value in filters.items():
            query = query.filter(build_filter_operator(attr, value, model_serializer))
    if 'order_by' in request.args:
        fields = request.args['order_by'].split(',')
        for field in fields:
            if field[0] == '-':
                col = getattr(model, field[1:])
                query = query.order_by(desc(col))
            else:
                col = getattr(model, field)
                query = query.order_by(col)
    # limit and pagination have to be done after order_by
    if 'limit' in request.args:
        limit = request.args['limit']
        query = query.limit(limit)
    if 'page' in request.args:
        data = query.paginate()
        return {
            'page': data.page,
            'per_page': data.per_page,
            'count': data.total,
            'results': [model_serializer.dump(item) for item in data.items]
        }
    else:
        data = query.all()
        return [model_serializer.dump(item) for item in data]
