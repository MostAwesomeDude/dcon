import os

from sqlalchemy import func

from werkzeug import secure_filename

from flask import (Blueprint, flash, redirect, render_template, request,
    url_for)

from newrem.forms import (CharacterCreateForm, CharacterDeleteForm,
    CharacterModifyForm, NewsForm, PortraitCreateForm,
    PortraitModifyForm, UploadForm)
from newrem.models import db, Character, Comic, Newspost, Portrait
from newrem.security import Authenticator

from osuchan.models import Thread

class AdminBlueprint(Blueprint):
    """
    Custom blueprint which automatically authenticates its views.
    """

    def register(self, app, options, first_registration=False):
        """
        Register this blueprint on an application.
        """

        path = app.config["DCON_PASSWORD_FILE"]
        d = {}
        for line in open(path, "rb").read().split("\n"):
            try:
                k, v = line.split(":", 1)
            except ValueError:
                pass
            else:
                d[k.strip()] = v.strip()

        self._authenticator = Authenticator(d)

        self.before_request(lambda: self._require_authentication(app))

        Blueprint.register(self, app, options, first_registration)

    def _require_authentication(self, app):
        auth = request.authorization
        if not auth or not self._authenticator.validate(auth):
            return self._authenticator.make_basic_challenge("Cid's Lair",
                "Haha, no.")

admin = AdminBlueprint("admin", __name__, static_folder="static",
    template_folder="templates")

@admin.route("/characters")
def characters():
    cform = CharacterCreateForm(prefix="create")
    mform = CharacterModifyForm(prefix="modify")
    dform = CharacterDeleteForm(prefix="delete")

    return render_template("characters.html", cform=cform, mform=mform, dform=dform)

@admin.route("/characters/create", methods=("POST",))
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

@admin.route("/characters/modify", methods=("POST",))
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

@admin.route("/characters/delete", methods=("POST",))
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

@admin.route("/portraits")
def portraits():
    cform = PortraitCreateForm(prefix="create")
    mform = PortraitModifyForm(prefix="modify")

    return render_template("portraits.html", cform=cform, mform=mform)

@admin.route("/portraits/create", methods=("POST",))
def portraits_create():
    form = PortraitCreateForm(prefix="create")

    if form.validate_on_submit():
        portrait = Portrait(form.name.data)
        db.session.add(portrait)
        db.session.commit()

        path = os.path.abspath(os.path.join("uploads", portrait.portrait))
        portrait.update_portrait(form.portrait.file, path)

        flash("Successfully created portrait %s!" % portrait.name)
    else:
        flash("Couldn't validate form...")

    return redirect(url_for("admin.portraits"))

@admin.route("/portraits/modify", methods=("POST",))
def portraits_modify():
    form = PortraitModifyForm(prefix="modify")

    if form.validate_on_submit():
        portrait = form.portraits.data
        if portrait and form.portrait.file:
            path = os.path.abspath(os.path.join("uploads", portrait.portrait))
            portrait.update_portrait(form.portrait.file, path)

            flash("Successfully changed portrait for portrait %s!" %
                portrait.name)
        else:
            flash("Couldn't find portrait for slug %s..." %
                form.portraits.data)
    else:
        flash("Couldn't validate form...")

    return redirect(url_for("admin.portraits"))

@admin.route("/news", methods=("GET", "POST"))
def news():
    form = NewsForm()

    if form.validate_on_submit():
        post = Newspost(form.title.data, form.content.data)
        post.portrait = form.portrait.data
        db.session.add(post)
        db.session.commit()
        return redirect(url_for("index"))

    return render_template("news.html", form=form)

@admin.route("/upload", methods=("GET", "POST"))
def upload():
    form = UploadForm()

    if form.validate_on_submit():
        bottom = db.session.query(func.min(Comic.position)).first()[0]
        top = db.session.query(func.max(Comic.position)).first()[0]

        if (bottom and top and form.index.data and
            not bottom <= form.index.data <= top):
            flash("Couldn't find insertion point between %d and %d"
                % (bottom, top))
            return render_template("upload.html", form=form)

        filename = os.path.join("comics",
            secure_filename(form.file.file.filename))
        path = os.path.abspath(os.path.join("uploads", filename))
        if os.path.exists(path):
            flash("File already exists!")
            return render_template("upload.html", form=form)

        form.file.file.save(path)
        comic = Comic(filename)
        comic.characters = form.characters.data
        comic.title = form.title.data
        comic.description = form.description.data
        comic.comment = form.comment.data
        comic.thread = Thread("co", comic.title, "Newrem")

        if form.time.data:
            comic.time = form.time.data

        if form.index.data == 0:
            comic.insert_at_head()
        else:
            prior = Comic.query.filter(Comic.position < form.index.data).first()
            comic.insert(prior)

        db.session.add(comic)
        db.session.commit()
        return redirect(url_for("comics", cid=comic.id))

    return render_template("upload.html", form=form)
