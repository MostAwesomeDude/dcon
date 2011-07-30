from functools import wraps

from werkzeug.contrib.cache import SimpleCache

from flask import request

from newrem.security import Authenticator

authenticator = Authenticator({"hurp": "derp"})
cache = SimpleCache()

def auth_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not authenticator.validate(auth):
            return authenticator.make_basic_challenge("Cid's Lair",
                "Haha, no.")
        return f(*args, **kwargs)
    return decorated

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
