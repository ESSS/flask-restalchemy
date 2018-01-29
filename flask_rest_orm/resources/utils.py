from sqlalchemy import desc
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
    query = model.query

    def build_query(column, request_filter):
        if isinstance(request_filter, dict):
            op_name = next(iter(request_filter))
            return query.filter(get_operator(column, op_name, request_filter.get(op_name)))
        return query.filter(get_operator(column, None, request_filter))

    if 'filter' in request.args:
        filters = json.loads(request.args['filter'])
        for attr, value in filters.items():
            query = build_query(getattr(model, attr), value)
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
        resources = query.paginate().items
    return resources
