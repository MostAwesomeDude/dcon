from datetime import datetime
import os

from PIL import Image

from werkzeug.security import generate_password_hash, check_password_hash

from flaskext.login import LoginManager, make_secure_token

from osuchan.models import db, Thread

from newrem.util import slugify

casts = db.Table("casts", db.metadata,
    db.Column("character_id", db.String(45), db.ForeignKey("characters.slug")),
    db.Column("comic_id", db.Integer, db.ForeignKey("comics.id"))
)

class Character(db.Model):
    """
    A character.
    """

    __tablename__ = "characters"

    name = db.Column(db.Unicode(40))
    slug = db.Column(db.String(45), primary_key=True)

    def __init__(self, name):
        self.rename(name)

    def __repr__(self):
        return "<Character(%r)>" % self.name

    def rename(self, name):
        self.name = name
        self.slug = slugify(name)

    def _get_portrait(self):
        png = "%s.png" % self.slug
        return os.path.join("characters", png)

    def _set_portrait(self, filename):
        os.rename(filename, self.portrait)

    portrait = property(_get_portrait, _set_portrait)

class Comic(db.Model):
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
    description = db.Column(db.UnicodeText(1024*1024))
    # Commentary.
    comment = db.Column(db.UnicodeText(1024*1024))
    # The discussion thread.
    threadid = db.Column(db.Integer, db.ForeignKey(Thread.id))

    # List of characters in this comic.
    characters = db.relationship(Character, secondary=casts, backref="comics")
    # The thread which discusses this comic.
    thread = db.relationship(Thread, backref="comic")

    def __init__(self, filename):
        self.filename = filename
        self.time = datetime.utcnow()

    def __repr__(self):
        return "<Comic(%r)>" % self.filename

    @classmethod
    def reorder(cls):
        """
        Compact chronological ordering.

        The reason for doing this is almost completely aesthetic.
        """

        for i, comic in enumerate(cls.query.order_by(cls.position)):
            if comic.position != i:
                comic.position = i
                db.session.add(comic)

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

        if after:
            position = max(prior.position - 1, 0)
        else:
            position = prior.position + 1

        q = Comic.query.filter(Comic.position >= position)
        q = q.order_by(Comic.position)

        for i, comic in enumerate(q):
            # The correct new position. The +1 offset is because this current
            # comic is shifting the old comics up.
            target = i + position + 1
            if comic.position != target:
                comic.position = target
                db.session.add(comic)

        self.position = position
        db.session.add(self)

class Portrait(db.Model):

    __tablename__ = "portraits"

    name = db.Column(db.String(40))
    slug = db.Column(db.String(45), primary_key=True)

    def __init__(self, name):
        self.rename(name)

    def __repr__(self):
        return "<Portrait(%r)>" % self.name

    def rename(self, name):
        self.name = name
        self.slug = slugify(name)

    def update_portrait(self, fs, path):
        image = Image.open(fs)
        image.thumbnail((250, 250), Image.ANTIALIAS)
        image.save(path)

    @property
    def portrait(self):
        png = "%s.png" % self.slug
        return os.path.join("portraits", png)

class Newspost(db.Model):

    __tablename__ = "newsposts"

    time = db.Column(db.DateTime, primary_key=True)
    title = db.Column(db.Unicode(80), nullable=False)
    content = db.Column(db.UnicodeText(1024*1024))

    # Reference to the attached portrait.
    portrait_id = db.Column(db.String(45), db.ForeignKey(Portrait.slug),
        nullable=False)
    portrait = db.relationship(Portrait, backref="newsposts")

    def __init__(self, title, content=u""):
        self.time = datetime.utcnow()
        self.title = title
        self.content = content

class User(db.Model):

    __tablename__ = "users"

    username = db.Column(db.Unicode(30), primary_key=True, unique=True,
        nullable=False)
    password = db.Column(db.String(60))
    logged_in = db.Column(db.Boolean)

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

lm = LoginManager()

@lm.user_loader
def user_loader(username):
    return User.query.filter_by(username=username).first()
