# Copyright (c) 2010 Ben Kero, 2012 Corbin Simpson
#
# This file is part of DCoN.
#
# DCoN is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License, version 3, as published by the Free
# Software Foundation.
#
# DCoN is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# DCoN. If not, see <http://www.gnu.org/licenses/>.
from flask import Blueprint, render_template, request, url_for

from newrem.forms import ChanForm
from newrem.models import db, Board, Post, Thread
from newrem.util import chan_filename

osuchan = Blueprint("osuchan", __name__, static_folder="static",
    template_folder="templates")

header = "OSUChan"

def save_file(f):
    """
    Save the given file resource to disk.

    Returns the filename on disk.
    """

    # Empty file?
    if not f.content_length:
        return ""

    filename = chan_filename(f)
    f.save("static/images/%s" % filename)

    return filename

@osuchan.route('/')
def index():
    boards = Board.query.all()
    return render_template("oc/index.html", title=header, boards=boards)

@osuchan.route('/<board:b>/comment', methods=('POST',))
def comment(b):
    form = ChanForm()

    if not form.validate_on_submit():
        return "Error"

    if "datafile" not in request.files:
        return "You forgot to select a file to upload"

    filename = save_file(request.files["datafile"])

    # Create thread and first post, inserting them together.
    thread = Thread(b, form.subject.data, form.name.data)
    post = Post(form.name.data, form.comment.data, form.email.data, filename)

    thread.posts = [post]

    db.session.add(thread)
    db.session.commit()

    email = form.email.data

    if email == "noko":
        if request.referrer:
            url = request.referrer
        else:
            url = url_for("osuchan.showthread", board=b, tid=thread)
    else:
        url = url_for("osuchan.showboard", board=b)

    return render_template("oc/redirect.html", url=url)

@osuchan.route('/<board:b>/<int:thread>/comment', methods=('POST',))
def threadcomment(b, thread):
    form = ChanForm()

    if not form.validate_on_submit():
        return "Error"

    if "datafile" in request.files:
        filename = save_file(request.files["datafile"])
    else:
        filename = ""

    post = Post(form.name.data, form.comment.data, form.email.data, filename)
    post.threadid = thread

    db.session.add(post)
    db.session.commit()

    email = form.email.data

    if email == "noko":
        if request.referrer:
            url = request.referrer
        else:
            url = url_for("osuchan.showthread", board=b, tid=thread)
    else:
        url = url_for("osuchan.showboard", board=b)

    return render_template("oc/redirect.html", url=url)

@osuchan.route('/<board:b>/')
def showboard(b):
    form = ChanForm()
    threads = Thread.query.filter_by(board=b).all()

    return render_template("oc/showboard.html", title=b.abbreviation, board=b,
        threads=threads, form=form)

@osuchan.route('/<board:b>/<int:tid>')
def showthread(b, tid):
    form = ChanForm()
    thread = Thread.query.filter_by(id=tid).one()
    subject = thread.subject

    query = Post.query.filter_by(threadid=tid).order_by(Post.timestamp)
    posts = query.all()

    return render_template("oc/showthread.html", title=subject, board=b,
        posts=posts, thread=thread, form=form)
