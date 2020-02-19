from sqlalchemy import desc, or_, and_, func
import json
import operator
from sqlalchemy.ext.associationproxy import AssociationProxyInstance

CASE_INSENSITIVE_ORDER_BY_ENABLED = True


def create_collection_query(parent_query, model_class, model_serializer, args):
    """
        Build a query using query parameters in the http URL, disposed on the request args.
        The default logical operator is AND, but you can set the OR as in the following examples:

            a) OR -> ?filter={"$or":{"name": {"startswith": "Terrans 1"},"location": "Location 1"}}
            b) AND -> ?filter={"$and":{"name": {"ilike": "%Terrans 1%"},"location": "Location 1"}}
                or ?filter={"name": {"ilike": "%Terrans 1%"},"location": {"eq": "Location 1"}}

        Ordered search is available using 'order_by=<col_name>'. The minus sign ("-<col_name>") could be
        used to set descending order.

        :param parent_query:
            SQLAlchemy query instance

        :param class model_class:
            SQLAlchemy model class representing a database resource

        :param model_serializer:
            instance of model serializer

        :param args:
            arguments of the Flask http request

        :rtype: query
        :return: SQLAlchemy query instance
        """

    def build_filter_operator(column_name, request_filter, serializer):
        if column_name == "$or":
            return or_(
                build_filter_operator(attr, value, serializer)
                for attr, value in request_filter.items()
            )
        elif column_name == "$and":
            return and_(
                build_filter_operator(attr, value, serializer)
                for attr, value in request_filter.items()
            )
        if isinstance(request_filter, dict):
            op_name = next(iter(request_filter))
            return get_operator(
                getattr(model_class, column_name),
                op_name,
                request_filter.get(op_name),
                get_field_serializer_or_none(serializer, column_name),
            )
        return get_operator(
            getattr(model_class, column_name),
            None,
            request_filter,
            get_field_serializer_or_none(serializer, column_name),
        )

    res_query = parent_query
    if "filter" in args:
        filters = json.loads(args["filter"])
        for attr, value in filters.items():
            res_query = res_query.filter(
                build_filter_operator(attr, value, model_serializer)
            )
    if "order_by" in args:
        fields = args["order_by"].split(",")
        for field in fields:
            field_name = field.lstrip("-")
            column = getattr(model_class, field_name)
            # Join with the associated table and define column as the associated property to support sorting
            if isinstance(column, AssociationProxyInstance):
                res_query = res_query.outerjoin(column.target_class)
                column = column.remote_attr
            if CASE_INSENSITIVE_ORDER_BY_ENABLED and str(column.type) == "VARCHAR":
                column = func.lower(column)
            if field[0] == "-":
                column = desc(column)
            res_query = res_query.order_by(column)
    # limit and pagination have to be done after order_by
    if "limit" in args:
        limit = args["limit"]
        res_query = res_query.limit(limit)

    return res_query


# Filter operators defined on SQLAlchemy ColumnElement
SQLA_OPERATORS = {
    "like": "like",
    "notlike": "notlike",
    "ilike": "ilike",
    "notilike": "notilike",
    "is": "is_",
    "isnot": "isnot",
    "match": "match",
    "startswith": "startswith",
    "endswith": "endswith",
    "contains": "contains",
    "in": "in_",
    "notin": "notin_",
    "between": "between",
    "eq": "__eq__",
    "ne": "__ne__",
    "gt": "__gt__",
    "ge": "__ge__",
    "lt": "__lt__",
    "le": "__le__",
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
        if op == "between":
            return column.between(
                parse_value(value[0], serializer), parse_value(value[1], serializer)
            )
        return getattr(column, op)(parse_value(value, serializer))
    else:
        raise ValueError(f"Unknown operator {op_name}")


def get_field_serializer_or_none(serializer, field_name):
    field = serializer.fields.get(field_name)
    if not field:
        return None
    return field.serializer
