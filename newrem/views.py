from datetime import datetime
import os.path
from random import choice

from PyRSS2Gen import Guid, RSS2, RSSItem

from sqlalchemy.orm.exc import NoResultFound

from flask import abort, redirect, render_template, url_for
from flaskext.login import current_user

from newrem.decorators import cached
from newrem.forms import CommentForm
from newrem.main import app
from newrem.models import db, Character, Comic, Newspost

from osuchan.models import Post

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
        "ocform": CommentForm(),
    }

    return render_template("comics.html", **kwargs)

@app.route("/comics/<int:cid>/comment", methods=("POST",))
def comment(cid):
    if current_user.is_anonymous():
        abort(403)

    try:
        comic = get_comic_query().filter_by(id=cid).one()
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

        db.session.add(post)
        db.session.commit()

    return redirect(url_for("comics", cid=cid))

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
