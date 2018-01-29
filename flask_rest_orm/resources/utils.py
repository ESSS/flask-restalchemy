from sqlalchemy import desc
import json
import operator

OPERATORS = {
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
}

OPERATE = {
    'eq': 'eq',
    'ne': 'ne',
    'gt': 'gt',
    'ge': 'ge',
    'lt': 'lt',
    'le': 'le',
}

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

    def get_operator(attr, key, value):
        if not key:
            return attr.operate(operator.eq, value)
        elif key in OPERATORS:
            op = OPERATORS.get(key)
            if op == 'between':
                return attr.between(value[0],value[1])
            return getattr(attr, op)(value)
        elif key in OPERATE:
            op = OPERATE.get(key)
            return attr.operate(getattr(operator, op), value)
        else:
            raise Exception('Unknown operator')

    def filter(attr, value):
        if isinstance(value, dict):
            key = next(iter(value))
            return builder.filter(get_operator(attr, key, value.get(key)))
        return builder.filter(get_operator(attr, None, value))

    if 'filter' in request.args:
        filters = json.loads(request.args['filter'])
        for attr, value in filters.items():
            builder = filter(getattr(model, attr), value)
    if 'limit' in request.args:
        limit = request.args['limit']
        builder = builder.limit(limit)
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
