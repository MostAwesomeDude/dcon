import os

from flaskext.uploads import configure_uploads, patch_request_class

from newrem.admin import admin
from newrem.comics import comics
from newrem.forms import images, pngs
from newrem.models import db, lm
from newrem.users import users
from newrem.views import app

from osuchan.blueprint import osuchan

wd = os.getcwd()

app.debug = True

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///%s/temp.db" % wd
app.config["SQLALCHEMY_ECHO"] = True
app.config["SECRET_KEY"] = "just a test!"
app.config["UPLOADS_DEFAULT_DEST"] = os.path.join(wd, "uploads")

app.config["DCON_PATH"] = wd
path = os.path.join(app.config["DCON_PATH"], "secret.key")
app.config["SECRET_KEY"] = open(path).read()
path = os.path.join(app.config["DCON_PATH"], "passwords.dcon")
app.config["DCON_PASSWORD_FILE"] = path

configure_uploads(app, (images, pngs))
patch_request_class(app)

db.init_app(app)
lm.setup_app(app)

app.register_blueprint(users)
app.register_blueprint(admin, url_prefix="/admin")
app.register_blueprint(comics)
app.register_blueprint(osuchan, url_prefix="/chan")
