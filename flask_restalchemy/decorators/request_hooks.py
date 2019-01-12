from functools import wraps

from flask import request


def before_request(all=None, **kwargs):

    call_by_verbs = _process_verbs_from_kwargs(kwargs)

    def create_decorator(func):
        @wraps(func)
        def request_decorator(*args, **kw):
            if all:
                all(**kw)
            if request.method in call_by_verbs:
                call_by_verbs[request.method](**kw)
            return func(*args, **kw)
        return request_decorator

    return create_decorator


def after_request(all=None, **kwargs):

    call_by_verbs = _process_verbs_from_kwargs(kwargs)

    def create_decorator(func):
        @wraps(func)
        def request_decorator(*args, **kw):
            response = func(*args, **kw)
            decorated_response = None
            if all:
                decorated_response = all(response, **kw)
            if request.method in call_by_verbs:
                decorated_response = call_by_verbs[request.method](decorated_response, **kw)
            return decorated_response or response
        return request_decorator

    return create_decorator


def _process_verbs_from_kwargs(kwargs):
    verb_calls = {}
    for verb in ['GET', 'POST', 'PUT', 'DELETE']:
        if verb.lower() in kwargs:
            verb_calls[verb] = kwargs.pop(verb.lower())
    if kwargs:
        raise TypeError("Invalid verb argument for decorator")
    return verb_calls
