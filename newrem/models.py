from datetime import datetime
from functools import partial

from PIL import Image

from werkzeug.security import generate_password_hash, check_password_hash

from flask import current_app

from flask.ext.login import LoginManager, make_secure_token
from flask.ext.sqlalchemy import SQLAlchemy

from newrem.files import extend_fp, extend_url, fp_root, url_root
from newrem.util import slugify

db = SQLAlchemy()
lm = LoginManager()

# ON UPDATE CASCADE.
FK = partial(db.ForeignKey, onupdate="cascade", ondelete="cascade")
# Oh, wait, that doesn't work on SQLite or MySQL. Plan B!
relationship = partial(db.relationship, cascade="all", passive_updates=False)

casts = db.Table("casts", db.metadata,
    db.Column("character_id", db.String(45), FK("characters.slug")),
    db.Column("comic_id", db.Integer, FK("comics.id"))
)


class FilenameMixin(object):
    """
    A mixin to provide some file access based on segments.
    """

    def fp(self):
        return extend_fp(fp_root(current_app), self.segments())

    def url(self):
        return extend_url(url_root(current_app), self.segments())


class Wordfilter(db.Model):
    __tablename__ = "badwords"

    name = db.Column(db.Unicode(30), primary_key=True)
    replacement = db.Column(db.Unicode(30))


class Category(db.Model):
    __tablename__ = "boardcategory"

    title = db.Column(db.Unicode(30), primary_key=True)


class Board(db.Model):
    __tablename__ = "board"

    name = db.Column(db.Unicode(30))
    abbreviation = db.Column(db.String(5), primary_key=True)
    category_fk = db.Column(db.Unicode(30), FK(Category.title))

    category = relationship(Category, backref="boards")

    def __init__(self, abbreviation, name):
        self.abbreviation = abbreviation
        self.name = name


class Thread(db.Model):
    __tablename__ = "thread"

    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.Unicode(50))
    author = db.Column(db.Unicode(30))
    board_fk = db.Column(db.String(5), FK(Board.abbreviation))

    board = relationship(Board, backref="threads")

    def __init__(self, board, subject, author):
        self.board = board
        self.subject = subject
        self.author = author


class Post(db.Model, FilenameMixin):
    __tablename__ = "post"

    id = db.Column(db.Integer, primary_key=True)
    author = db.Column(db.Unicode(30), nullable=False)
    threadid = db.Column(db.Integer, FK(Thread.id), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)
    comment = db.Column(db.UnicodeText(1024 * 1024))
    email = db.Column(db.String(30))
    filename = db.Column(db.String(50))

    thread = relationship(Thread, backref="posts", single_parent=True,
                          cascade="all, delete, delete-orphan")

    def __init__(self, author, comment, email, filename):
        self.comment = comment
        self.author = author
        self.email = email
        self.filename = filename

        self.timestamp = datetime.now()

    def segments(self):
        return ["comments", self.filename]


class Universe(db.Model):

    __tablename__ = "universes"

    slug = db.Column(db.String(85), primary_key=True)
    title = db.Column(db.Unicode(80), nullable=False)
    board_fk = db.Column(db.String(5), FK(Board.abbreviation))

    board = relationship(Board, backref="universe", uselist=False)

    def __init__(self, title):
        self.rename(title)

    def __repr__(self):
        return "<Universe(%r)>" % self.title

    def rename(self, title):
        self.title = title
        self.slug = slugify(title)


class Character(db.Model, FilenameMixin):
    """
    A character.
    """

    __tablename__ = "characters"

    slug = db.Column(db.String(45), primary_key=True)
    name = db.Column(db.Unicode(40))
    description = db.Column(db.UnicodeText(1024 * 1024))
    universe_fk = db.Column(db.String(85), FK(Universe.slug), nullable=False)
    universe = relationship(Universe, backref="characters")

    def __init__(self, universe, name):
        self.universe = universe
        self.rename(name)

    def __repr__(self):
        return "<Character(%r) in %r>" % (self.name, self.universe)

    @property
    def portrait(self):
        return "%s.png" % self.slug

    def segments(self):
        return ["characters", self.universe.slug, self.portrait]

    def rename(self, name):
        self.name = name
        fp = self.fp()
        self.slug = slugify(name)

        if fp.exists():
            fp.moveTo(self.fp())


class Comic(db.Model, FilenameMixin):
    """
    A comic.
    """

    __tablename__ = "comics"

    # Serial number, for simple PK.
    id = db.Column(db.Integer, primary_key=True, unique=True, nullable=False)
    # Upload time.
    time = db.Column(db.DateTime, unique=True, nullable=False)
    # Local filename.
    filename = db.Column(db.String(50), unique=True, nullable=False)
    # Position in the timeline.
    position = db.Column(db.Integer, nullable=False)
    # Title of the comic.
    title = db.Column(db.Unicode(80), nullable=False)
    # Description/alt text.
    description = db.Column(db.UnicodeText(1024 * 1024))
    # Commentary.
    comment = db.Column(db.UnicodeText(1024 * 1024))
    # The discussion thread.
    threadid = db.Column(db.Integer, FK(Thread.id))
    # The universe in which this comic occurs.
    universe_fk = db.Column(db.String(85), FK(Universe.slug), nullable=False)

    # List of characters in this comic.
    characters = relationship(Character, secondary=casts, backref="comics")
    # The thread which discusses this comic.
    thread = relationship(Thread, backref="comic", uselist=False)
    # The universe which owns this comic.
    universe = relationship(Universe, backref="comics")

    def __init__(self, universe, filename):
        self.universe = universe
        self.filename = filename
        self.time = datetime.utcnow()

        # Check at comic creation. Flat-out refuse to create this comic if
        # the space for it isn't there.
        self.verify_fp()

    def __repr__(self):
        return "<Comic(%r) in %r>" % (self.filename, self.universe)

    def segments(self):
        return ["comics", self.universe.slug, self.filename]

    def verify_fp(self):
        """
        Assert that this comic will not destroy any pre-existing comic.
        """

        if self.fp().exists():
            raise Exception("File already exists!")

    def insert(self, prior, after=False):
        """
        Move this comic to come just after another comic in the timeline.

        If after is True, move this comic to just *before* another comic.
        """

        if not prior:
            # First insertion in the table, ever. Let's just set ourselves to
            # zero and walk away.
            self.position = 0
            db.session.add(self)
            return

        if prior.universe != self.universe:
            raise Exception(
                "Comic.insert called with differing universes %r and %r" %
                (self.universe, prior.universe))

        if after:
            position = max(prior.position - 1, 0)
        else:
            position = prior.position + 1

        q = Comic.query.filter(Comic.universe == self.universe)
        q = q.filter(Comic.position >= position).order_by(Comic.position)

        for i, comic in enumerate(q):
            # The correct new position. The +1 offset is because this current
            # comic is shifting the old comics up.
            target = i + position + 1
            if comic.position != target:
                comic.position = target
                db.session.add(comic)

        self.position = position
        db.session.add(self)


class Portrait(db.Model, FilenameMixin):

    __tablename__ = "portraits"

    name = db.Column(db.String(40))
    slug = db.Column(db.String(45), primary_key=True)

    def __init__(self, name):
        self.rename(name)

    def __repr__(self):
        return "<Portrait(%r)>" % self.name

    @property
    def portrait(self):
        return "%s.png" % self.slug

    def segments(self):
        # XXX When Portraits are Universe-sensitive, the Universe slug should
        # be part of the segments here.
        return ["portraits", self.portrait]

    def rename(self, name):
        self.name = name
        fp = self.fp()
        self.slug = slugify(name)

        if fp.exists():
            fp.moveTo(self.fp())

    def update_portrait(self, fs):
        image = Image.open(fs)
        image.thumbnail((250, 250), Image.ANTIALIAS)
        image.save(self.fp().path)


class Newspost(db.Model):

    __tablename__ = "newsposts"

    time = db.Column(db.DateTime, primary_key=True)
    title = db.Column(db.Unicode(80), nullable=False)
    content = db.Column(db.UnicodeText(1024 * 1024))

    # Reference to the attached portrait.
    portrait_id = db.Column(db.String(45), FK(Portrait.slug), nullable=False)
    portrait = relationship(Portrait, backref="newsposts")

    def __init__(self, title, content=u""):
        self.time = datetime.utcnow()
        self.title = title
        self.content = content


class User(db.Model):

    __tablename__ = "users"

    username = db.Column(db.Unicode(30), primary_key=True, unique=True,
                         nullable=False)
    password = db.Column(db.String(60))
    logged_in = db.Column(db.Boolean, default=False)

    def __init__(self, username, password):
        self.username = username
        self.password = generate_password_hash(password)

    def __repr__(self):
        return "<User(%r)>" % self.username

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def login(self):
        self.logged_in = True
        db.session.add(self)
        db.session.commit()

    def logout(self):
        self.logged_in = False
        db.session.add(self)
        db.session.commit()

    def is_authenticated(self):
        return self.logged_in

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return self.username

    def get_auth_token(self):
        return make_secure_token(self.username, self.password)


@lm.user_loader
def user_loader(username):
    return User.query.filter_by(username=username).first()
