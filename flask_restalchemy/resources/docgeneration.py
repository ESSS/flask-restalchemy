from sqlalchemy import DateTime, Float, Integer, String


def properties_from_coltype(sqlType):
    if isinstance(sqlType, Integer):
        return {
            'type': 'integer',
            'format': 'int64'
        }
    elif isinstance(sqlType, Float):
        return {
            'type': 'number'
        }
    elif isinstance(sqlType, String):
        return {
            'type': 'string'
        }
    elif isinstance(sqlType, DateTime):
        return {
            'type': 'string',
            'format': 'date-time'
        }
    return {}


def gen_response(http_method, resource_name):
    '''
    This function receives a HTTP method and a resource name and generates the standard responses of the method

    :param str http_method:
        http method used

    :param str resource_name:
        name of the resource being served

    :rtype dict:
    :return: dict containing the standard responses of the method
    '''
    if http_method == 'GET_Collection':
        return {
            '200': {
                'description': 'successful operation',
                'schema': {
                    'type': 'array',
                    'items': {
                        '$ref': '#/definitions/%s' % resource_name
                    }
                }
            }
        }
    elif http_method == 'PUT':
        return {
            '204': {
                'description': 'successfully updated'
            },
            '400': {
                'description': 'invalid %s supplied' % resource_name
            },
            '404': {
                'description': '%s not found' % resource_name
            }
        }
    elif http_method == 'GET':
        return {
            '200': {
                'description': 'successful operation',
                'schema': {
                    '$ref': '#/definitions/%s' % resource_name
                }
            },
            '400': {
                'description': 'invalid ID supplied'
            },
            '404': {
                'description': '%s not found' % resource_name
            }
        }
    elif http_method == 'POST':
        return {
            '201': {
                'description': 'the %s was created successfully' % resource_name
            },
            '405': {
                'description': 'invalid input'
            }
        }
    elif http_method == 'DELETE':
        return {
            '204': {
                'description': 'successfully deleted'
            },
            '400': {
                'description': 'invalid ID supplied'
            },
            '404': {
                'description': '%s not found' % resource_name
            }
        }

    return None


def gen_spec(model, http_method, is_child=False):
    '''
    This function receives a sqlalchemy class model and a HTTP method and generates the flasgger spec dict

    :param bool is_child:
        Tels if the model is a child resource in the route, meaning that a parent id must be part of the route

    :param class model:
        sqlachemy mapper class

    :param str http_method:
        http method used

    :rtype: dict
    :return: dict containing the spec
    '''
    res_name = model.__tablename__

    responses = gen_response(http_method, res_name)

    properties = {}
    for col in model.__table__.columns:
        if col.name != 'id':
            pro_name = col.name
            properties[pro_name] = properties_from_coltype(col.type)

    parameters = []
    if is_child:
        parameters.append({
            'name': 'parent_id',
            'in': 'path',
            'required': True,
            'type': 'integer',
            'format': 'int64'
        })
    if http_method == 'GET' or http_method == 'PUT' or http_method == 'DELETE':
        parameters.append({
            'name': 'id',
            'in': 'path',
            'required': True,
            'type': 'integer',
            'format': 'int64'
        })
    if http_method == 'POST' or http_method == 'PUT':
        parameters.append({
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                '$ref': '#/definitions/%s' % res_name
            }
        })

    produces = ["application/json"]
    receives = ["application/json"]

    specs_dict = {
        "tags": [res_name],
        "parameters": parameters,
        "produces": produces,
        "receives": receives,
        "schemes": [
            "http",
            "https"
        ],
        "deprecated": False,
        "security": [
            {
                "Bearer": []
            }
        ],
        "responses": responses,
        "definitions": {
            res_name: {
                "type": "object",
                "properties": properties
            }
        }
    }

    return specs_dict
