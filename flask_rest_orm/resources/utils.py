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


def get_operator(column, op_name, value):
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
        return column.operate(operator.eq, value)
    elif op_name in SQLA_OPERATORS:
        op = SQLA_OPERATORS.get(op_name)
        if op == 'between':
            return column.between(value[0], value[1])
        return getattr(column, op)(value)
    else:
        raise ValueError('Unknown operator {}'.format(op_name))


def query_from_request(model, request):
    """
    Perform a filtered search in the database model table using query parameters in the http URL,
    disposed on the request args. The default logical operator is AND, but you can set the OR as
    in the following examples:

        a) OR -> ?filter={"$or":{"name": {"startswith": "Terrans 1"},"location": "Location 1"}}
        b) AND -> ?filter={"$and":{"name": {"ilike": "%Terrans 1%"},"location": "Location 1"}}
            or ?filter={"name": {"ilike": "%Terrans 1%"},"location": {"eq": "Location 1"}}

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
    query = model.query

    def build_filter_operator(column_name, request_filter):
        if column_name == '$or':
            return or_(build_filter_operator(attr, value) for attr, value in request_filter.items())
        elif column_name == '$and':
            return and_(build_filter_operator(attr, value) for attr, value in request_filter.items())
        if isinstance(request_filter, dict):
            op_name = next(iter(request_filter))
            return get_operator(getattr(model, column_name), op_name, request_filter.get(op_name))
        return get_operator(getattr(model, column_name), None, request_filter)

    if 'filter' in request.args:
        filters = json.loads(request.args['filter'])
        for attr, value in filters.items():
            query = query.filter(build_filter_operator(attr, value))
    if 'limit' in request.args:
        limit = request.args['limit']
        query = query.limit(limit)
    if 'order_by' in request.args:
        col = getattr(model,request.args['order_by'])
        if 'desc' in request.args:
            query = query.order_by(desc(col))
        else:
            query = query.order_by(col)
    if 'page' not in request.args:
        resources = query.all()
    else:
        resources = query.paginate()
    return resources
