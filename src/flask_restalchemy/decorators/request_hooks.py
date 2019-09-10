from functools import wraps


def before_request(_callable):
    def create_decorator(func):
        @wraps(func)
        def request_decorator(*args, **kw):
            _callable(*args, **kw)
            return func(*args, **kw)

        return request_decorator

    return create_decorator


def after_request(_callable):
    def create_decorator(func):
        @wraps(func)
        def request_decorator(*args, **kw):
            response = func(*args, **kw)
            decorated_response = _callable(response, **kw)
            return decorated_response or response

        return request_decorator

    return create_decorator
