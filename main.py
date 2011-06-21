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
from flaskext.wtf import (Form, FileAllowed, FileRequired, Required,
    FileField, QuerySelectField, QuerySelectMultipleField, SubmitField,
    TextField)

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

    name = db.Column(db.String)
    slug = db.Column(db.String, primary_key=True)

    def __init__(self, name):
        self.rename(name)

    def __repr__(self):
        return "<Character(%r)>" % self.name

    def rename(self, name):
        self.name = name
        self.slug = name.strip().lower().replace(" ", "-")

class Comic(db.Model):
    """
    A comic.
    """

    __tablename__ = "comics"

    # Serial number, for simple PK.
    id = db.Column(db.Integer, primary_key=True)
    after_id = db.Column(db.Integer, db.ForeignKey(id))
    # Upload time.
    time = db.Column(db.DateTime)
    # Local filename.
    filename = db.Column(db.String)

    # Chronological position, as ascertained during the last sort.
    after = db.relationship("Comic", uselist=False,
        backref=db.backref("before", remote_side=id, uselist=False))

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

    @property
    def orphaned(self):
        """
        Whether this comic is chronologically oriented.
        """

        return bool(self.before or self.after)

    def orphan(self):
        """
        Remove this comic from its current position in the timeline.
        """

        if self.after:
            db.session.add(self.after)
            self.after.before = self.before

        self.after = None
        db.session.add(self)

    def insert(self, prior):
        """
        Move this comic to come just after another comic in the timeline.
        """

        self.after = prior.after
        prior.after = self
        db.session.add(prior)
        db.session.add(self)

class CharacterCreateForm(Form):
    name = TextField(u"New name", validators=(Required(),))
    submit = SubmitField("Create!")

class CharacterModifyForm(Form):
    characters = QuerySelectField(u"Characters",
        query_factory=lambda: Character.query.order_by(Character.name),
        get_label="name")
    name = TextField(u"New name", validators=(Required(),))
    submit = SubmitField("Modify!")

class CharacterDeleteForm(Form):
    characters = QuerySelectField(u"Characters",
        query_factory=lambda: Character.query.order_by(Character.name),
        get_label="name")
    submit = SubmitField("Delete!")

@app.route("/characters")
def characters():
    cform = CharacterCreateForm(prefix="create")
    mform = CharacterModifyForm(prefix="modify")
    dform = CharacterDeleteForm(prefix="delete")

    return render_template("characters.html", cform=cform, mform=mform, dform=dform)

@app.route("/characters/create", methods=("POST",))
def characters_create():
    form = CharacterCreateForm(prefix="create")

    if form.validate_on_submit():
        character = Character(form.name.data)
        db.session.add(character)
        db.session.commit()
        flash("Successfully created character %s!" % character.name)
    else:
        flash("Couldn't validate form...")

    return redirect(url_for("characters"))

@app.route("/characters/modify", methods=("POST",))
def characters_modify():
    form = CharacterModifyForm(prefix="modify")

    if form.validate_on_submit():
        character = form.characters.data
        if character:
            character.rename(form.name.data)
            db.session.add(character)
            db.session.commit()
            flash("Successfully renamed character %s!" % character.name)
        else:
            flash("Couldn't find character for slug %s..." %
                form.characters.data)
    else:
        flash("Couldn't validate form...")

    return redirect(url_for("characters"))

@app.route("/characters/delete", methods=("POST",))
def characters_delete():
    form = CharacterDeleteForm(prefix="delete")

    if form.validate_on_submit():
        character = form.characters.data
        if character:
            db.session.delete(character)
            db.session.commit()
            flash("Successfully removed character %s!" % character.name)
        else:
            flash("Couldn't find character for slug %s..." %
                form.characters.data)
    else:
        flash("Couldn't validate form...")

    return redirect(url_for("characters"))

class UploadForm(Form):
    file = FileField("Select a file to upload",
        validators=(FileRequired("Must upload a comic!"),
            FileAllowed(images, "Images only!")))
    characters = QuerySelectMultipleField("Available characters:",
        query_factory=lambda: Character.query.order_by(Character.name),
        get_label="name")
    submit = SubmitField("Upload!")

@app.route("/upload", methods=("GET", "POST"))
def upload():
    form = UploadForm()

    if form.validate_on_submit():
        filename = secure_filename(form.file.file.filename)
        path = os.path.abspath(os.path.join("uploads", filename))
        if os.path.exists(path):
            flash("File already exists!")
            return redirect(url_for("upload"))
        else:
            form.file.file.save(path)
            comic = Comic(filename)
            comic.characters = form.characters.data
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

    q = Comic.query.filter(Comic.time < comic.time)
    before = q.order_by(Comic.time.desc()).first()

    q = Comic.query.filter(Comic.time > comic.time)
    after = q.order_by(Comic.time).first()

    kwargs = {
        "comic": comic,
        "before": before,
        "after": after,
    }

    return render_template("comics.html", **kwargs)
