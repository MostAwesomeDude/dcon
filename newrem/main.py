import os

from flask import Flask
from flaskext.uploads import configure_uploads

from newrem.comics import comics
from newrem.forms import images, pngs
from newrem.models import db, lm
from newrem.users import users

wd = os.getcwd()

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///%s/temp.db" % wd
app.config["SQLALCHEMY_ECHO"] = True
app.config["SECRET_KEY"] = "just a test!"
app.config["UPLOADS_DEFAULT_DEST"] = os.path.join(wd, "uploads")

configure_uploads(app, (images, pngs))

db.init_app(app)
lm.setup_app(app)

app.register_blueprint(users)
app.register_blueprint(comics)
