import os

from werkzeug import secure_filename

from flask import (Blueprint, flash, redirect, render_template, request,
    url_for)

from newrem.files import save_file
from newrem.forms import (CharacterCreateForm, CharacterDeleteForm,
    CharacterModifyForm, NewsForm, PortraitCreateForm,
    PortraitModifyForm, UniverseCreateForm, UniverseModifyForm,
    UniverseDeleteForm, UploadForm)
from newrem.models import (db, Board, Character, Comic, Newspost, Portrait,
    Thread, Universe)
from newrem.security import Authenticator
from newrem.util import abbreviate

class AdminBlueprint(Blueprint):
    """
    Custom blueprint which automatically authenticates its views.
    """

    def register(self, app, options, first_registration=False):
        """
        Register this blueprint on an application.
        """

        fp = app.config["DCON_PASSWORD_FILE"]
        d = {}
        for line in fp.open("rb").read().split("\n"):
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

@admin.route("/")
def index():
    form = UniverseCreateForm()
    universes = Universe.query.order_by(Universe.title)

    return render_template("admin.html", form=form, universes=universes)

@admin.route("/<universe:u>/")
def universe(u):
    form = UniverseModifyForm()

    return render_template("admin-universe.html", form=form, u=u)

@admin.route("/universe/create", methods=("POST",))
def universe_create():
    form = UniverseCreateForm()

    if form.validate_on_submit():
        universe = Universe(form.name.data)
        universe.board = Board(abbreviate(universe.title), universe.title)
        db.session.add(universe)
        db.session.commit()

        flash("Successfully created the universe of %s!" % universe.title)
        return redirect(url_for("admin.universe", u=universe))
    else:
        flash("Couldn't validate form. How'd that happen?")
        return redirect(url_for("admin.index"))

@admin.route("/<universe:u>/modify", methods=("POST",))
def universe_modify(u):
    form = UniverseModifyForm()

    if form.validate_on_submit():
        old = u.title
        u.rename(form.name.data)
        db.session.add(u)
        db.session.commit()
        flash("Successfully renamed the universe of %s to %s!" %
            (old, u.title))

    return redirect(url_for("admin.universe", u=u))

@admin.route("/<universe:u>/delete", methods=("GET", "POST"))
def universe_delete(u):
    form = UniverseDeleteForm()

    if form.validate_on_submit():
        if form.verify.data:
            db.session.delete(u)
            db.session.commit()
            flash("Successfully destroyed universe %s!" % u.title)
        else:
            flash("Guess you changed your mind, huh? No worries.")

        return redirect(url_for("admin.index"))
    else:
        return render_template("universe-delete.html", form=form, u=u)

@admin.route("/<universe:u>/characters")
def characters(u):
    characters = Character.query.order_by(Character.name)
    form = CharacterCreateForm()

    return render_template("characters.html", form=form, u=u,
        characters=characters)

@admin.route("/<universe:u>/characters/<character:c>")
def character(u, c):
    mform = CharacterModifyForm(prefix="modify", name=c.name,
        description=c.description)
    dform = CharacterDeleteForm(prefix="delete")

    return render_template("character.html", mform=mform, dform=dform, u=u,
        c=c)

@admin.route("/<universe:u>/characters/create", methods=("POST",))
def characters_create(u):
    form = CharacterCreateForm()

    if form.validate_on_submit():
        character = Character(form.name.data)
        if form.description.data:
            character.description = form.description.data
        character.universe = u
        db.session.add(character)
        db.session.commit()

        if form.portrait.file:
            save_file(character.fp(), form.portrait.file)

        flash("Successfully created character %s!" % character.name)
    else:
        flash("Couldn't validate form...")

    return redirect(url_for("admin.characters", u=u))

@admin.route("/<universe:u>/characters/<character:c>/modify",
    methods=("POST",))
def characters_modify(u, c):
    form = CharacterModifyForm(prefix="modify")

    if form.validate_on_submit():
        # Which modifications do we want to make?
        if form.name.data and form.name.data != c.name:
            c.rename(form.name.data)
            db.session.add(c)
            flash("Successfully renamed character %s!" % c.name)

        if form.portrait.file:
            if save_file(c.fp(), form.portrait.file):
                flash("Successfully changed portrait for character %s!" %
                    c.name)
            else:
                flash("Couldn't save portrait for character %s..." % c.name)

        if form.description.data != c.description:
            if form.description.data:
                c.description = form.description.data
            else:
                c.description = None
            db.session.add(c)
            flash("Successfully changed description for character %s!" %
                c.name)

        db.session.commit()
    else:
        flash("Couldn't validate form...")

    return redirect(url_for("admin.character", u=u, c=c))

@admin.route("/<universe:u>/characters/<character:c>/delete",
    methods=("POST",))
def characters_delete(u, c):
    form = CharacterDeleteForm(prefix="delete")

    if form.validate_on_submit():
        db.session.delete(c)
        db.session.commit()
        c.fp().remove()
        flash("Successfully removed character %s!" % c.name)
    else:
        flash("Couldn't validate form...")

    return redirect(url_for("admin.characters", u=u))

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

        portrait.update_portrait(form.portrait.file)

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
            portrait.update_portrait(form.portrait.file)

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

@admin.route("/<universe:u>/upload", methods=("GET", "POST"))
def upload(u):
    form = UploadForm(u)

    if form.validate_on_submit():
        filename = secure_filename(form.file.file.filename)

        try:
            comic = Comic(u, filename)
        except Exception, e:
            flash("Couldn't create comic: %s" % ", ".join(e.args))
            return render_template("upload.html", form=form, u=u)

        comic.characters = form.characters.data
        comic.title = form.title.data
        comic.description = form.description.data
        comic.comment = form.comment.data
        comic.thread = Thread(u.board, comic.title, "DCoN")

        if form.time.data:
            comic.time = form.time.data

        comic.insert(form.index.data, form.after.data)

        db.session.add(comic)
        db.session.commit()

        save_file(comic.fp(), form.file.file)

        return redirect(url_for("comics", u=u, cid=comic.id))

    return render_template("upload.html", form=form, u=u)
