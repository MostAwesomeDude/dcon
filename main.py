#!/usr/bin/env python

if __name__ == "__main__":
    import main
    raise SystemExit(main.app.run(debug=True))

from datetime import datetime
import os.path

from sqlalchemy.orm.exc import NoResultFound

from werkzeug import secure_filename

from flask import Flask, abort, flash, redirect, render_template, url_for
from flaskext.sqlalchemy import SQLAlchemy
from flaskext.uploads import configure_uploads, IMAGES, UploadSet
from flaskext.wtf import (Form, FileField, SelectField, SubmitField,
    file_allowed, file_required)

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///temp.db"
app.config["SECRET_KEY"] = "just a test!"
app.config["UPLOADS_DEFAULT_DEST"] = "uploads"

db = SQLAlchemy(app)
images = UploadSet("images", IMAGES)

configure_uploads(app, (images,))

casts = db.Table("casts", db.metadata,
    db.Column("character_id", db.String, db.ForeignKey("characters.slug")),
    db.Column("comic_id", db.Integer, db.ForeignKey("comics.id"))
)

class Character(db.Model):
    """
    A character.
    """

    __tablename__ = "characters"

    slug = db.Column(db.String, primary_key=True)
    name = db.Column(db.String)

    def __init__(self, name):
        self.name = name
        self.slug = name.strip().lower().replace(" ", "-")

    def __repr__(self):
        return "<Character(%r)>" % self.name

class Comic(db.Model):
    """
    A comic.
    """

    __tablename__ = "comics"

    # Serial number, for simple PK.
    id = db.Column(db.Integer, primary_key=True)
    after_id = db.Column(db.Integer, db.ForeignKey("comics.id"))
    # Upload time.
    time = db.Column(db.DateTime)
    # Local filename.
    filename = db.Column(db.String)
    # Relations, for timeline data.
    parents = db.Column(db.PickleType)
    kids = db.Column(db.PickleType)

    # Chronological position, as ascertained during the last sort.
    after = db.relationship("Comic", uselist=False,
        backref=db.backref("before", remote_side=id))

    # List of characters in this comic.
    characters = db.relationship("Character", secondary=casts,
        backref="comics")

    def __init__(self, filename):
        self.filename = filename
        self.time = datetime.utcnow()
        self.parents = {}
        self.kids = {}

    def __repr__(self):
        return "<Comic(%r)>" % self.filename

class CharacterForm(Form):
    characters = SelectField(u"Characters")

@app.route("/characters", methods=("GET", "POST"))
def characters():
    form = CharacterForm()

    q = db.session.query(Character.slug, Character.name)
    characters = q.order_by(Character.name).all()

    form.characters.choices = characters

    return render_template("characters.html", characters=characters, form=form)

class UploadForm(Form):
    file = FileField("Select a file to upload",
        validators=(file_required(), file_allowed(images, "Images only!")))
    submit = SubmitField("Upload!")

@app.route("/upload", methods=("GET", "POST"))
def upload():
    form = UploadForm()

    if form.validate_on_submit():
        filename = secure_filename(form.file.file.filename)
        path = os.path.abspath(os.path.join("uploads", filename))
        if os.path.exists(path):
            flash("Oh noes!")
            return redirect(url_for("index"))
        else:
            form.file.file.save(path)
            comic = Comic(filename)
            db.session.add(comic)
            db.session.commit()
            return redirect(url_for("comics", cid=comic.id))

    return render_template("upload.html", form=form)

@app.errorhandler(404)
def not_found(error):
    return "Couldn't find the page!", 404

@app.route("/")
def index():
    return "One second, please."

@app.route("/comics/")
def comics_root():
    return redirect(url_for("comics", cid=1))

@app.route("/comics/<int:cid>")
def comics(cid):
    try:
        comic = Comic.query.filter(Comic.id == cid).one()
    except NoResultFound:
        abort(404)

    return render_template("comics.html", comic=comic)
