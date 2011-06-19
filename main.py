#!/usr/bin/env python

if __name__ == "__main__":
    import main
    raise SystemExit(main.app.run(debug=True))

from datetime import datetime

from sqlalchemy.orm.exc import NoResultFound

from flask import Flask, abort, redirect, url_for
from flaskext.sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///temp.db"

db = SQLAlchemy(app)

class Comic(db.Model):
    """
    A comic.
    """

    __tablename__ = "comics"

    # Serial number, for simple PK.
    id = db.Column(db.Integer, primary_key=True)
    after_id = db.Column(db.Integer, db.ForeignKey("comics.id"))
    # Upload time.
    time = db.Column(db.DateTime)
    # Local filename.
    filename = db.Column(db.String)
    # Relations, for timeline data.
    parents = db.Column(db.PickleType)
    kids = db.Column(db.PickleType)

    # Chronological position, as ascertained during the last sort.
    after = db.relationship("Comic", uselist=False,
        backref=db.backref("before", remote_side=id))

    def __init__(self, filename):
        self.filename = filename
        self.time = datetime.utcnow()
        self.parents = {}
        self.kids = {}

    def __repr__(self):
        return "<Comic(%r)>" % self.filename

@app.errorhandler(404)
def not_found(error):
    return "Couldn't find the page!", 404

@app.route("/")
def root():
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

    return "Here's the comic: %s" % comic
