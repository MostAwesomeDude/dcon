from random import SystemRandom

# because the API of hmac changed with the introduction of the
# new hashlib module, we have to support both.  This sets up a
# mapping to the digest factory functions and the digest modules
# (or factory functions with changed API)
try:
    from hashlib import sha1, md5
    _hash_funcs = _hash_mods = {'sha1': sha1, 'md5': md5}
    _sha1_mod = sha1
    _md5_mod = md5
except ImportError:
    import sha as _sha1_mod, md5 as _md5_mod
    _hash_mods = {'sha1': _sha1_mod, 'md5': _md5_mod}
    _hash_funcs = {'sha1': _sha1_mod.new, 'md5': _md5_mod.new}

from werkzeug.wrappers import Response

_sys_rng = SystemRandom()

def gen_nonce(length):
    nonce = ''.join(chr(_sys_rng.randint(16, 255)) for _ in xrange(length))
    return nonce.encode("hex")


class Authenticator(object):
    """An object which can validate HTTP authentication attempts and issue
    appropriate challenges in response.
    """

    def __init__(self, users=None):
        """Create an authenticator.

        ``users`` is an optional dictionary of usernames to passwords which
        can be provided for authentication.
        """

        self.users = users

    def password_for_user(self, user):
        """Retrieve a password for a certain user."""

        if user in self.users:
            return self.users[user]

        return None

    def make_basic_challenge(self, realm, message=None):
        """Create a HTTP basic authentication challenge."""

        if message is None:
            message = "Authentication is required"

        authenticate = 'Basic realm="%s"' % realm

        return Response(message, 401, {"WWW-Authenticate": authenticate})

    def make_digest_challenge(self, realm, message=None):
        """Create a HTTP digest authentication challenge."""

        if message is None:
            message = "Authentication is required"

        param_dict = {
            "realm": realm,
            "nonce": gen_nonce(16),
            "opaque": gen_nonce(16),
        }

        parameters = ", ".join('%s="%s"' % t for t in param_dict.items())

        authenticate = "Digest %s" % parameters

        return Response(message, 401, {"WWW-Authenticate": authenticate})

    def validate(self, authorization, method="GET"):
        """Validate an authorization.

        ``authorization`` is an ``Authorization`` object.

        ``method`` should be the actual method used, for HTTP digests.
        """

        if authorization.type == "basic":
            username = authorization.username
            expected = self.password_for_user(username)
            if expected is None:
                return False
            return expected == authorization.password

        if authorization.type == "digest":
            username = authorization.username
            password = self.password_for_user(username)
            if password is None:
                return False

            # Prepare the digest. RFCs 2069 and 2617 will be helpful in
            # explaining what everything is, but hopefully this is just as
            # self-explanatory.
            md5 = _hash_funcs["md5"]
            a1 = ":".join([authorization.username, authorization.realm,
                password])
            ha1 = md5(a1).hexdigest()
            a2 = ":".join([method, authorization.uri])
            ha2 = md5(a2).hexdigest()
            a3 = ":".join([ha1, authorization.nonce, ha2])
            expected = md5(a3).hexdigest()
            return expected == authorization.response

        return False
