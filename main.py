#!/usr/bin/env python

if __name__ == "__main__":
    import main
    raise SystemExit(main.app.run(debug=True))

from datetime import datetime
import os.path

from sqlalchemy import func
from sqlalchemy.orm.exc import NoResultFound

from werkzeug import secure_filename

from flask import Flask, abort, flash, redirect, render_template, url_for
from flaskext.sqlalchemy import SQLAlchemy
from flaskext.uploads import configure_uploads, IMAGES, UploadSet
from flaskext.wtf import (Form, FileAllowed, FileRequired,
    Required, FileField, QuerySelectField, IntegerField,
    SubmitField, TextField)
from wtforms.fields import Field
from wtforms.widgets import TextInput

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
    id = db.Column(db.Integer, primary_key=True, unique=True, nullable=False)
    # Upload time.
    time = db.Column(db.DateTime, unique=True, nullable=False)
    # Local filename.
    filename = db.Column(db.String, unique=True, nullable=False)
    # Position in the timeline.
    position = db.Column(db.Integer, nullable=False)

    # List of characters in this comic.
    characters = db.relationship("Character", secondary=casts,
        backref="comics")

    def __init__(self, filename):
        self.filename = filename
        self.time = datetime.utcnow()

    def __repr__(self):
        return "<Comic(%r)>" % self.filename

    @classmethod
    def reorder(cls):
        """
        Compact chronological ordering.

        The reason for doing this is almost completely aesthetic.
        """

        for i, comic in enumerate(cls.query.order_by(cls.position)):
            if comic.position != i:
                comic.position = i
                db.session.add(comic)

    def insert_at_head(self):
        """
        Make this comic the very first comic.
        """

        self.position = 0
        db.session.add(self)

        q = Comic.query.filter(Comic.id != self.id)
        q = q.order_by(Comic.position)

        for i, comic in enumerate(q):
            if comic.position != i + 1:
                comic.position = i + 1
                db.session.add(comic)

    def insert(self, prior):
        """
        Move this comic to come just after another comic in the timeline.
        """

        if not prior:
            # First insertion in the table, ever. Let's just set ourselves to
            # zero and walk away.
            self.position = 1
            db.session.add(self)
            return

        position = prior.position + 1

        q = Comic.query.filter(Comic.position >= position)
        q = q.order_by(Comic.position)

        for i, comic in enumerate(q):
            if comic.position != i + position:
                comic.position = i + position
                db.session.add(comic)

        self.position = position
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

class TagListField(Field):
    widget = TextInput()

    def _value(self):
        if self.data:
            return u", ".join(self.data)
        else:
            return u""

    def process_formdata(self, data):
        if data:
            self.data = [word.strip() for word in data[0].split(",")]
            self.data.sort()
        else:
            self.data = []

class UploadForm(Form):
    file = FileField("Select a file to upload",
        validators=(FileRequired("Must upload a comic!"),
            FileAllowed(images, "Images only!")))
    characters = TagListField("Characters")
    index = IntegerField("Where to insert this comic?",
        validators=(Required(),))
    submit = SubmitField("Upload!")

@app.route("/upload", methods=("GET", "POST"))
def upload():
    form = UploadForm()

    if form.validate_on_submit():
        d = dict((c.name, c) for c in
            Character.query.order_by(Character.name).all())
        try:
            characters = [d[name] for name in form.characters.data]
        except KeyError, ke:
            flash("Couldn't find character %s..." % ke.args)
            return render_template("upload.html", form=form)

        bottom = db.session.query(func.min(Comic.position)).first()[0]
        top = db.session.query(func.max(Comic.position)).first()[0]

        if (bottom and top and form.index.data and
            not bottom <= form.index.data <= top):
            flash("Couldn't find insertion point between %d and %d"
                % (bottom, top))
            return render_template("upload.html", form=form)

        filename = secure_filename(form.file.file.filename)
        path = os.path.abspath(os.path.join("uploads", filename))
        if os.path.exists(path):
            flash("File already exists!")
            return render_template("upload.html", form=form)

        form.file.file.save(path)
        comic = Comic(filename)
        comic.characters = characters

        if form.index.data == 0:
            comic.insert_at_head()
        else:
            prior = Comic.query.filter(Comic.position < form.index.data).first()
            comic.insert(prior)

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

    q = Comic.query.filter(Comic.position < comic.position)
    previous = q.order_by(Comic.position.desc()).first()

    q = Comic.query.filter(Comic.position > comic.position)
    chrono = previous, q.order_by(Comic.position).first()

    kwargs = {
        "comic": comic,
        "before": before,
        "after": after,
        "chrono": chrono,
    }

    return render_template("comics.html", **kwargs)
