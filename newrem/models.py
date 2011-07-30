from datetime import datetime
import os
import re

from PIL import Image

from unidecode import unidecode

from werkzeug.security import generate_password_hash, check_password_hash

from flaskext.login import LoginManager, make_secure_token

from osuchan.models import db, Thread

casts = db.Table("casts", db.metadata,
    db.Column("character_id", db.String, db.ForeignKey("characters.slug")),
    db.Column("comic_id", db.Integer, db.ForeignKey("comics.id"))
)

punctuation = re.compile(r'[\t !"#$%&\'()*\-/<=>?@\[\\\]^_`{|},.]+')

class Character(db.Model):
    """
    A character.
    """

    __tablename__ = "characters"

    name = db.Column(db.Unicode)
    slug = db.Column(db.String, primary_key=True)

    def __init__(self, name):
        self.rename(name)

    def __repr__(self):
        return "<Character(%r)>" % self.name

    def rename(self, name):
        self.name = name

        # ASCIIfy slug. Based on http://flask.pocoo.org/snippets/5/.
        l = []
        for word in punctuation.split(self.name):
            l.extend(unidecode(word).split())
        self.slug = "-".join(word.strip().lower() for word in l)

    @property
    def portrait(self):
        png = "%s.png" % self.slug
        return os.path.join("characters", png)

    @portrait.setter
    def portrait(self, filename):
        os.rename(filename, self.portrait)

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
    filename = db.Column(db.String, unique=True, nullable=False)
    # Position in the timeline.
    position = db.Column(db.Integer, nullable=False)
    # Title of the comic.
    title = db.Column(db.Unicode, nullable=False)
    # Description/alt text.
    description = db.Column(db.Unicode)
    # Commentary.
    comment = db.Column(db.UnicodeText)
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

    def insert_at_head(self):
        """
        Make this comic the very first comic.
        """

        self.position = 0
        db.session.add(self)

        q = Comic.query.filter(Comic.id != self.id)
        q = q.order_by(Comic.position)

        for i, comic in enumerate(q):
            if comic.position != i + 1:
                comic.position = i + 1
                db.session.add(comic)

    def insert(self, prior):
        """
        Move this comic to come just after another comic in the timeline.
        """

        if not prior:
            # First insertion in the table, ever. Let's just set ourselves to
            # zero and walk away.
            self.position = 1
            db.session.add(self)
            return

        position = prior.position + 1

        q = Comic.query.filter(Comic.position >= position)
        q = q.order_by(Comic.position)

        for i, comic in enumerate(q):
            if comic.position != i + position:
                comic.position = i + position
                db.session.add(comic)

        self.position = position
        db.session.add(self)

class Newspost(db.Model):

    __tablename__ = "newsposts"

    time = db.Column(db.DateTime, primary_key=True)
    title = db.Column(db.Unicode, nullable=False)
    content = db.Column(db.UnicodeText)

    # Reference to the attached portrait.
    portrait_id = db.Column(db.String, db.ForeignKey("portraits.slug"),
        nullable=False)
    portrait = db.relationship("Portrait", backref="newsposts")

    def __init__(self, title, content=u""):
        self.time = datetime.utcnow()
        self.title = title
        self.content = content

class Portrait(db.Model):

    __tablename__ = "portraits"

    name = db.Column(db.String)
    slug = db.Column(db.String, primary_key=True)

    def __init__(self, name):
        self.rename(name)

    def __repr__(self):
        return "<Portrait(%r)>" % self.name

    def rename(self, name):
        self.name = name

        # ASCIIfy slug. Based on http://flask.pocoo.org/snippets/5/.
        l = []
        for word in punctuation.split(self.name):
            l.extend(unidecode(word).split())
        self.slug = "-".join(word.strip().lower() for word in l)

    def update_portrait(self, fs, path):
        image = Image.open(fs)
        image.thumbnail((250, 250), Image.ANTIALIAS)
        image.save(path)

    @property
    def portrait(self):
        png = "%s.png" % self.slug
        return os.path.join("portraits", png)

class User(db.Model):

    __tablename__ = "users"

    username = db.Column(db.Unicode, primary_key=True, unique=True,
        nullable=False)
    password = db.Column(db.String)
    logged_in = db.Column(db.Boolean)

    def __init__(self, username, password):
        self.username = username
        self.password = generate_password_hash(password)

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
