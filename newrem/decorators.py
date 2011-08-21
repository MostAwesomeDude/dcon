from functools import wraps

from werkzeug.contrib.cache import SimpleCache

from flask import request

cache = SimpleCache()

def cached(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        key = request.path
        data = cache.get(key)
        if data is not None:
            return data
        data = f(*args, **kwargs)
        cache.set(key, data)
        return data
    return decorated
