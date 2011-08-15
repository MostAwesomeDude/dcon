from datetime import datetime
import os.path
from random import choice

from PyRSS2Gen import Guid, RSS2, RSSItem

from sqlalchemy import func
from sqlalchemy.orm.exc import NoResultFound

from werkzeug import secure_filename

from flask import abort, flash, redirect, render_template, url_for

from newrem.decorators import cached, make_auth_required
from newrem.forms import (CharacterCreateForm, CharacterDeleteForm,
    CharacterModifyForm, NewsForm, PortraitCreateForm,
    PortraitModifyForm, UploadForm)
from newrem.main import app
from newrem.models import db, Character, Comic, Newspost, Portrait

from osuchan.models import Thread

auth_required = make_auth_required(app)

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

@app.route("/portraits")
@auth_required
def portraits():
    cform = PortraitCreateForm(prefix="create")
    mform = PortraitModifyForm(prefix="modify")

    return render_template("portraits.html", cform=cform, mform=mform)

@app.route("/portraits/create", methods=("POST",))
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

    return redirect(url_for("portraits"))

@app.route("/portraits/modify", methods=("POST",))
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

    return redirect(url_for("portraits"))

@app.route("/news", methods=("GET", "POST"))
@auth_required
def news():
    form = NewsForm()

    if form.validate_on_submit():
        post = Newspost(form.title.data, form.content.data)
        post.portrait = form.portrait.data
        db.session.add(post)
        db.session.commit()
        return redirect(url_for("index"))

    return render_template("news.html", form=form)

@app.route("/upload", methods=("GET", "POST"))
@auth_required
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

def get_comic_query():
    """
    Make a comic query.

    This helper mostly just keeps the temporal filter on all comic queries not
    otherwise safe. The point of the filter is to prevent comics which are
    posted with a timestamp in the future from being displayed or otherwise
    referenced; as far as anybody can tell, those comics simply do not exist
    until after the timestamp elapses.
    """

    return Comic.query.filter(Comic.time < datetime.now())

def get_neighbors_for(comic):
    """
    Grab the comics around a given comic.
    """

    comics = {}

    # Grab the comics corresponding to navigation buttons: First, previous,
    # next, last. This first query doesn't need to have the temporal filter.
    q = Comic.query.filter(Comic.time < comic.time)
    a = q.order_by(Comic.time.desc()).first()
    b = q.order_by(Comic.time).first()

    q = get_comic_query().filter(Comic.time > comic.time)
    c = q.order_by(Comic.time).first()
    d = q.order_by(Comic.time.desc()).first()

    comics["upload"] = a, b, c, d

    return comics

@app.route("/")
def index():
    comic = get_comic_query().order_by(Comic.id.desc()).first()

    if comic is None:
        abort(404)

    comics = get_neighbors_for(comic)

    newsposts = Newspost.query.order_by(Newspost.time.desc())[:5]
    return render_template("index.html", comic=comic, comics=comics,
        newsposts=newsposts)

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
        comic = get_comic_query().filter_by(id=cid).one()
    except NoResultFound:
        abort(404)

    comics = get_neighbors_for(comic)

    previousq = get_comic_query().filter(Comic.position < comic.position)
    nextq = get_comic_query().filter(Comic.position > comic.position)

    previous = previousq.order_by(Comic.position.desc()).first()
    chrono = previous, nextq.order_by(Comic.position).first()

    cdict = {}

    for character in list(comic.characters):
        q = previousq.order_by(Comic.position.desc())
        previous = q.filter(Comic.characters.any(slug=character.slug)).first()

        next = nextq.filter(Comic.characters.any(slug=character.slug)).first()

        cdict[character.slug] = character, previous, next

    kwargs = {
        "comic": comic,
        "comics": comics,
        "chrono": chrono,
        "characters": cdict,
    }

    return render_template("comics.html", **kwargs)

@app.route("/rss.xml")
@cached
def rss():
    comics = Comic.query.order_by(Comic.id.desc())[:10]
    items = []
    for comic in comics:
        url = url_for("comics", _external=True, cid=comic.id)
        item = RSSItem(title=comic.title, link=url, description=comic.title,
            guid=Guid(url), pubDate=comic.time)
        items.append(item)

    rss2 = RSS2(title="RSS", link=url_for("index", _external=True),
        description="Flavor Text", lastBuildDate=datetime.utcnow(), items=items)
    return rss2.to_xml(encoding="utf8")

@app.errorhandler(404)
def not_found(error):
    directory = os.path.join(app.root_path, "static/404")
    filename = choice(os.listdir(directory))
    image = os.path.join("404", filename)
    return render_template("404.html", image=image)

@app.errorhandler(500)
def internal_server_error(error):
    return render_template("500.html")
