from datetime import datetime
import os.path
from operator import attrgetter
from random import choice

from sqlalchemy.orm.exc import NoResultFound

from flask import Flask, abort, redirect, render_template, url_for
from flaskext.login import current_user

from newrem.converters import make_model_converter
from newrem.decorators import cached
from newrem.forms import CommentForm
from newrem.grammars import BlogGrammar
from newrem.models import (db, Board, Character, Comic, Newspost, Post,
    Universe)
from newrem.util import chan_filename, make_rss2

app = Flask(__name__)

# Register converters.
app.url_map.converters["board"] = make_model_converter(app, Board,
    "abbreviation")
app.url_map.converters["character"] = make_model_converter(app, Character,
    "slug")
app.url_map.converters["universe"] = make_model_converter(app, Universe,
    "slug")

@app.template_filter()
def blogify(s):
    """
    Run a string through a grammar to prettify it somewhat.
    """

    return BlogGrammar(s).apply("paragraphs")[0]

@app.template_filter()
def eblogify(s):
    """
    Like ``blogify``, but also apply HTML escapes. For untrusted input.
    """

    return BlogGrammar(s).apply("safe_paragraphs")[0]

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
    a = q.order_by(Comic.time.desc()).first()
    b = q.order_by(Comic.time).first()

    q = get_comic_query(universe).filter(Comic.time > comic.time)
    c = q.order_by(Comic.time).first()
    d = q.order_by(Comic.time.desc()).first()

    comics["upload"] = a, b, c, d

    return comics

@app.route("/")
def index():
    universes = Universe.query.all()

    return render_template("root.html", universes=universes)

@app.route("/<universe:u>")
def universe(u):
    newsposts = Newspost.query.order_by(Newspost.time.desc())[:5]

    comic = get_comic_query(u).order_by(Comic.id.desc()).first()

    if comic is None:
        abort(404)

    comics = get_neighbors_for(u, comic)

    return render_template("universe.html", u=u, comic=comic,
        comics=comics, newsposts=newsposts)

@app.route("/<universe:u>/cast")
def cast(u):
    # Re-add the universe to the session so that we can query it.
    db.session.add(u)
    characters = sorted(u.characters, key=attrgetter("name"))
    return render_template("cast.html", u=u, characters=characters)

@app.route("/<universe:u>/comics/<int:cid>")
def comics(u, cid):
    try:
        comic = get_comic_query(u).filter_by(id=cid).one()
    except NoResultFound:
        abort(404)

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

    kwargs = {
        "comic": comic,
        "comics": comics,
        "chrono": chrono,
        "characters": cdict,
        "ocform": CommentForm(),
    }

    return render_template("comics.html", **kwargs)

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

        post = Post(name, form.comment.data, "", "")
        post.thread = comic.thread

        image = form.datafile.file
        if image:
            post.file = os.path.join("comments", chan_filename(image))
            filename = os.path.abspath(os.path.join("uploads", post.file))
            image.save(filename)

        db.session.add(post)
        db.session.commit()

    return redirect(url_for("comics", u=u, cid=cid))

@app.route("/rss.xml")
@cached
def rss():
    comics = Comic.query.order_by(Comic.id.desc())[:10]
    stuff = {}
    for comic in comics:
        url = url_for("comics", _external=True, universe=comic.universe,
            cid=comic.id)
        stuff[url] = comic

    link = url_for("index", _external=True)

    return make_rss2(link, "DCoN", stuff)

@app.route("/<universe:u>/rss.xml")
@cached
def universe_rss(u):
    q = Comic.query.filter(Comic.universe == u).order_by(Comic.id.desc())
    comics = q[:10]
    stuff = {}
    for comic in comics:
        url = url_for("comics", _external=True, u=u, cid=comic.id)
        stuff[url] = comic

    link = url_for("universe", _external=True, u=u)

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
