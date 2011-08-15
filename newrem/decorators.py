from functools import wraps

from werkzeug.contrib.cache import SimpleCache

from flask import request

from newrem.security import Authenticator

cache = SimpleCache()

def make_auth_required(app):
    path = app.config["DCON_PASSWORD_FILE"]
    d = {}
    for line in open(path, "rb").read().split("\n"):
        try:
            k, v = line.split(":", 1)
        except ValueError:
            pass
        else:
            d[k.strip()] = v.strip()

    authenticator = Authenticator(d)

    def auth_required(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            auth = request.authorization
            if not auth or not authenticator.validate(auth):
                return authenticator.make_basic_challenge("Cid's Lair",
                    "Haha, no.")
            return f(*args, **kwargs)
        return decorated
    return auth_required

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
