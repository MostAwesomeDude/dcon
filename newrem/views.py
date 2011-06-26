from functools import wraps
import os.path

from sqlalchemy import func
from sqlalchemy.orm.exc import NoResultFound

from werkzeug import secure_filename
from werkzeug.security import Authenticator

from flask import abort, flash, redirect, render_template, request, url_for
from flaskext.login import login_user, logout_user

from newrem.forms import (CharacterCreateForm, CharacterDeleteForm,
    CharacterModifyForm, LoginForm, RegisterForm, UploadForm)
from newrem.main import app
from newrem.models import db, Character, Comic, User

authenticator = Authenticator({"hurp": "derp"})

def auth_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not authenticator.validate(auth):
            return authenticator.make_basic_challenge("Cid's Lair",
                "Haha, no.")
        return f(*args, **kwargs)
    return decorated

@app.route("/characters")
@auth_required
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

        path = os.path.abspath(os.path.join("uploads", character.portrait))
        form.portrait.file.save(path)

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
            # Which modifications do we want to make?
            if form.name.data:
                character.rename(form.name.data)
                db.session.add(character)
                db.session.commit()
                flash("Successfully renamed character %s!" % character.name)

            if form.portrait.file:
                path = os.path.abspath(os.path.join("uploads",
                    character.portrait))
                form.portrait.file.save(path)
                flash("Successfully changed portrait for character %s!" %
                    character.name)
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

@app.route("/upload", methods=("GET", "POST"))
@auth_required
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
        comic.title = form.title.data

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

@app.route("/cast")
def cast():
    characters = Character.query.order_by(Character.name)
    return render_template("cast.html", characters=characters)

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

    cdict = {}

    for character in list(comic.characters):
        q = Comic.query.filter(Comic.position < comic.position)
        q = q.order_by(Comic.position.desc())
        previous = q.filter(Comic.characters.any(slug=character.slug)).first()

        q = Comic.query.filter(Comic.position > comic.position)
        next = q.filter(Comic.characters.any(slug=character.slug)).first()

        cdict[character.slug] = character, previous, next

    kwargs = {
        "comic": comic,
        "before": before,
        "after": after,
        "chrono": chrono,
        "characters": cdict,
    }

    return render_template("comics.html", **kwargs)

@app.route("/register", methods=("GET", "POST"))
def register():
    form = RegisterForm()

    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()

        if not user:
            user = User(form.username.data, form.password.data)
            db.session.add(user)
            user.login()
            login_user(user, remember=True)
            flash("Logged in!")
            if "next" in request.args:
                return redirect(request.args["next"])
            else:
                return redirect(url_for("index"))

    return render_template("register.html", form=form)

@app.route("/login", methods=("GET", "POST"))
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()

        if user and user.check_password(form.password.data):
            user.login()
            login_user(user, remember=True)
            flash("Logged in!")
            if "next" in request.args:
                return redirect(request.args["next"])
            else:
                return redirect(url_for("index"))

    return render_template("login.html", form=form)

@app.route("/logout")
def logout():
    logout_user()
    flash("Logged out!")

    if "next" in request.args:
        return redirect(request.args["next"])
    else:
        return redirect(url_for("index"))
