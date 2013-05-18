import os

from twisted.python.filepath import FilePath

from flask.ext.uploads import configure_uploads, patch_request_class

from newrem.admin import admin
from newrem.chan import osuchan
from newrem.comics import comics
from newrem.forms import images, pngs
from newrem.models import db, lm
from newrem.users import users
from newrem.views import app

wd = None
if wd is None:
    wd = os.getcwd()

wd = FilePath(wd)

app.debug = True

# This default should be sufficient to limp along for starters.
app.config["DCON_STATIC_URL"] = "/static/"

app.config["DCON_PATH"] = wd
app.config["DCON_PASSWORD_FILE"] = wd.child("passwords.dcon")
app.config["DCON_UPLOAD_PATH"] = wd.child("uploads")
app.config["SECRET_KEY"] = wd.child("secret.key").open("rb").read()

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///%s/temp.db" % wd.path
app.config["SQLALCHEMY_ECHO"] = True
app.config["SECRET_KEY"] = "just a test!"
app.config["UPLOADS_DEFAULT_DEST"] = app.config["DCON_UPLOAD_PATH"].path

configure_uploads(app, (images, pngs))
patch_request_class(app)

db.init_app(app)
lm.setup_app(app)

app.register_blueprint(users)
app.register_blueprint(admin, url_prefix="/admin")
app.register_blueprint(comics)
app.register_blueprint(osuchan, url_prefix="/chan")
