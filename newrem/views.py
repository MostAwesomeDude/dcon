from datetime import datetime
import os.path
from operator import attrgetter
from random import choice

from sqlalchemy.orm.exc import NoResultFound

from jinja2.exceptions import TemplateNotFound

from twisted.python.filepath import FilePath

from flask import abort, flash, redirect, render_template, request, url_for
from flask.ext.login import current_user

from newrem.app import DCoN
from newrem.converters import make_model_converter
from newrem.decorators import cached
from newrem.files import extend_fp, save_file
from newrem.forms import CommentForm
from newrem.grammars import BlogGrammar
from newrem.models import (db, Board, Character, Comic, Newspost, Post,
    Universe)
from newrem.util import chan_filename, make_rss2

app = DCoN(__name__)

# Register converters.
app.url_map.converters["board"] = make_model_converter(app, Board,
    "abbreviation")
app.url_map.converters["character"] = make_model_converter(app, Character,
    "slug")
app.url_map.converters["newspost"] = make_model_converter(app, Newspost,
    "time")
app.url_map.converters["universe"] = make_model_converter(app, Universe,
    "slug")

@app.template_filter()
def blogify(s):
    """
    Run a string through a grammar to prettify it somewhat.
    """

    return BlogGrammar(s).paragraphs()

@app.template_filter()
def eblogify(s):
    """
    Like ``blogify``, but also apply HTML escapes. For untrusted input.
    """

    return BlogGrammar(s).safe_paragraphs()

def get_comic_query(universe):
    """
    Make a comic query.

    This helper keeps the temporal filter on all comic queries not otherwise
    safe. The point of the filter is to prevent comics which are posted with a
    timestamp in the future from being displayed or otherwise referenced; as
    far as anybody can tell, those comics simply do not exist until after the
    timestamp elapses. The filter also prevents comics in other universes from
    being selected.
    """

    q = Comic.query.filter(Comic.universe == universe)
    return q.filter(Comic.time < datetime.now())

def get_neighbors_for(universe, comic):
    """
    Grab the comics around a given comic.
    """

    comics = {}

    # Grab the comics corresponding to navigation buttons: First, previous,
    # next, last. This first query doesn't need to have the temporal filter.
    q = Comic.query.filter(Comic.universe == universe)
    q = q.filter(Comic.time < comic.time)
    a = q.order_by(Comic.time).first()
    b = q.order_by(Comic.time.desc()).first()

    q = get_comic_query(universe).filter(Comic.time > comic.time)
    c = q.order_by(Comic.time).first()
    d = q.order_by(Comic.time.desc()).first()

    comics["upload"] = a, b, c, d

    return comics

@app.route("/")
def index():
    universes = Universe.query.all()
    newsposts = Newspost.query.order_by(Newspost.time.desc())[:5]

    return render_template("index.html", universes=universes,
        newsposts=newsposts)


def universe_context(app, u):
    root = FilePath(app.root_path)
    segments = ["static", u.slug, "images", "banners"]
    fp = extend_fp(root, segments)

    # Get a banner, if one exists.
    if fp.exists():
        banners = [p.basename() for p in fp.children()]
        segments.append(choice(banners))
        banner = "/".join(segments[1:])
    else:
        banner = None

    return {
        "u": u,
        "banner": banner,
    }


@app.route("/<universe:u>/cast")
def cast(u):
    # Re-add the universe to the session so that we can query it.
    db.session.add(u)
    characters = sorted(u.characters, key=attrgetter("name"))

    context = universe_context(app, u)
    context.update({
        "characters": characters,
    })

    try:
        return render_template("universe/%s/cast.html" % u.slug, **context)
    except TemplateNotFound:
        return render_template("universe/cast.html", **context)


@app.route("/<universe:u>/")
@app.route("/<universe:u>/comics/recent")
def recent(u):
    char = request.args.get("char", None)
    if char is not None:
        if char == "anything-goes":
            # Get all characters that exist in this universe who have had any
            # appearances. This could fail, in which case we bail with a cute
            # error message.
            q = Character.query.filter_by(universe=u)
            chars = q.filter(Character.comics.any()).all()
            if not chars:
                flash("No characters have been introduced yet. Patience, "
                    "grasshopper.")
                return redirect(url_for("recent", u=u))
            char = choice(chars)
        else:
            char = Character.query.filter_by(universe=u, slug=char).first()
            if not char:
                flash("That character doesn't exist. I'm sorry, but we don't "
                    "have fanfiction-based characters in the story.")
                return redirect(url_for("recent", u=u))
            elif not char.comics:
                flash("That character has not made an appearance yet. We "
                    "know how popular they are, though, so be prepared for "
                    "their debut!")
                return redirect(url_for("recent", u=u))

    q = get_comic_query(u)
    if char:
        q = q.filter(Comic.characters.contains(char))
    comic = q.order_by(Comic.id.desc()).first()

    if not comic:
        # We probably shouldn't have been able to get here, in general. This
        # could happen if there are no comics in this universe yet. However,
        # it could possibly happen if there is some bug in the above
        # character-sorting logic. Be aware of this when debugging this code
        # later. :3
        flash("No comics could be found. Something went wrong, perhaps?")
        return redirect(url_for("index"))

    if char:
        return redirect(url_for("comics", u=u, cid=comic.id, char=char.slug))
    else:
        return redirect(url_for("comics", u=u, cid=comic.id))


@app.route("/<universe:u>/comics/<int:cid>")
def comics(u, cid):
    try:
        comic = get_comic_query(u).filter_by(id=cid).one()
    except NoResultFound:
        abort(404)

    char = request.args.get("char", None)
    if char is not None:
        char = Character.query.filter_by(universe=u, slug=char).first()
        if char is None:
            flash("That character doesn't exist, and typing them into the "
                "URL doesn't magically spring them into the comic. Sorry.")
        elif char not in comic.characters:
            flash("That character isn't in this particular comic, and won't "
                "be, no matter how hard you wish. Sorry.")
            char = None

    comics = get_neighbors_for(u, comic)

    previousq = get_comic_query(u).filter(Comic.position < comic.position)
    nextq = get_comic_query(u).filter(Comic.position > comic.position)

    previous = previousq.order_by(Comic.position.desc()).first()
    chrono = previous, nextq.order_by(Comic.position).first()

    cdict = {}

    for character in list(comic.characters):
        q = previousq.order_by(Comic.position.desc())
        previous = q.filter(Comic.characters.any(slug=character.slug)).first()

        next = nextq.filter(Comic.characters.any(slug=character.slug)).first()

        cdict[character.slug] = character, previous, next

    context = universe_context(app, u)
    context.update({
        "comic": comic,
        "comics": comics,
        "chrono": chrono,
        "characters": cdict,
        "ocform": CommentForm(),
    })

    try:
        return render_template("universe/%s/comics.html" % u.slug, **context)
    except TemplateNotFound:
        return render_template("universe/comics.html", **context)


@app.route("/<universe:u>/comics/<int:cid>/comment", methods=("POST",))
def comment(u, cid):
    if current_user.is_anonymous():
        abort(403)

    try:
        comic = get_comic_query(u).filter_by(id=cid).one()
    except NoResultFound:
        abort(404)

    form = CommentForm()

    if form.validate_on_submit():
        if form.anonymous.data:
            name = "Anonymous"
        else:
            name = current_user.username

        post = Post(name, form.comment.data, "", None)
        post.thread = comic.thread

        image = form.datafile.file
        if image:
            post.filename = chan_filename(image)
            save_file(post.fp(), image)

        db.session.add(post)
        db.session.commit()

    return redirect(url_for("comics", u=u, cid=cid))

@app.route("/rss.xml")
@cached
def rss():
    # Filter out comics that have not yet gone live.
    q = Comic.query.filter(Comic.time < datetime.now())
    comics = q.order_by(Comic.time.desc())[:10]
    stuff = []
    for comic in comics:
        url = url_for("comics", _external=True, u=comic.universe,
            cid=comic.id)
        stuff.append((url, comic))

    link = url_for("index", _external=True)

    return make_rss2(link, "DCoN", stuff)

@app.route("/<universe:u>/rss.xml")
@cached
def universe_rss(u):
    q = get_comic_query(u).order_by(Comic.time.desc())
    comics = q[:10]
    stuff = []
    for comic in comics:
        url = url_for("comics", _external=True, u=u, cid=comic.id)
        stuff.append((url, comic))

    link = url_for("recent", _external=True, u=u)

    return make_rss2(link, u.title, stuff)

@app.errorhandler(404)
def not_found(error):
    directory = os.path.join(app.root_path, "static/404")
    filename = choice(os.listdir(directory))
    image = os.path.join("404", filename)
    return render_template("404.html", image=image)

@app.errorhandler(500)
def internal_server_error(error):
    return render_template("500.html")
