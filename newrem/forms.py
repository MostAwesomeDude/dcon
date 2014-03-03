from datetime import datetime

from wtforms.ext.dateutil.fields import DateTimeField
from wtforms.ext.sqlalchemy.fields import (QuerySelectMultipleField,
    QuerySelectField)
from wtforms.ext.sqlalchemy.orm import model_form
from wtforms.fields import (BooleanField, PasswordField, SelectField,
                            SubmitField, TextAreaField, TextField)
from wtforms.validators import EqualTo, Length, Required, ValidationError

from flask.ext.uploads import IMAGES, UploadSet
from flask.ext.wtf import Form, RecaptchaField
from flask.ext.wtf.file import FileField

from newrem.models import Character, Comic, Newspost, Portrait
from newrem.util import split_camel_case


class BetterFileAllowed(object):
    """
    If a file is present, this verifies that the file is in the given upload
    set.

    Borrowed from Flask-WTF but with less fail.
    """

    def __init__(self, upload_set, message=None):
        self.upload_set = upload_set
        self.message = message

    def __call__(self, form, field):
        fs = getattr(field, "file", None)

        if fs and not self.upload_set.file_allowed(fs, fs.filename):
            raise ValidationError(self.message)

images = UploadSet("images", IMAGES)

portrait = FileField("Select a portrait",
    validators=(BetterFileAllowed(images, "Images only!"),))

class FormBase(Form):
    """
    The base of all DCoN forms.

    This class can render its fields. It also knows its name and how to
    format and display it.
    """

    _display_name = None

    def display_name(self):
        if self._display_name is not None:
            name = self._display_name
        else:
            name = self.__class__.__name__

        pieces = split_camel_case(name)
        if pieces[-1] == "Form":
            pieces.pop()

        return " ".join(pieces)


class ConfigForm(FormBase):
    upload_time_now = BooleanField("Default upload time to time of upload")
    reload = SubmitField("Reload!")

    def __init__(self, app):
        super(ConfigForm, self).__init__()

        config = app.config["DCON_CONFIG"]

        self.upload_time_now.default = config["upload_time_now"]


def makeCU(form):
    """
    Make create and update forms for a given form base.

    Works by attaching submission buttons with the appropriate labels to the
    forms.
    """

    class Create(form):
        submit = SubmitField("Create!")

    class Modify(form):
        submit = SubmitField("Modify!")

    return Create, Modify

class UniverseBase(FormBase):
    name = TextField(u"New name", validators=(Required(),))

CreateUniverseForm, ModifyUniverseForm = makeCU(UniverseBase)

class DeleteUniverseForm(FormBase):
    verify = BooleanField(u"""Really delete this universe? Deletion will
        destroy all comics, characters, and other data associated with this
        universe. It cannot be undone. Seriously. It can't. We've tried. This
        universe will cease to be. It will be shuffled off the coil. If you're
        still sure, check this box.""")
    submit = SubmitField("Delete!")

class CharacterBase(FormBase):
    name = TextField(u"New name", validators=(Required(),))
    major = BooleanField(u"Major character", default=True)
    description = TextAreaField("Description")
    portrait = portrait
    submit = SubmitField("Create!")

CreateCharacterForm, ModifyCharacterForm = makeCU(CharacterBase)

class DeleteCharacterForm(FormBase):
    submit = SubmitField("Delete!")

class CreatePortraitForm(FormBase):
    name = TextField(u"New name", validators=(Required(),))
    portrait = portrait
    submit = SubmitField("Create!")

class ModifyPortraitForm(FormBase):
    portraits = QuerySelectField(u"Portraits",
        query_factory=lambda: Portrait.query.order_by(Portrait.name),
        get_label="name")
    portrait = portrait
    submit = SubmitField("Modify!")

class LoginForm(FormBase):
    username = TextField("Username", validators=(Required(),))
    password = PasswordField("Password", validators=(Required(),))
    submit = SubmitField("Login!")

class RegisterForm(LoginForm):
    confirm = PasswordField("Confirm password",
        validators=(Required(), EqualTo("password")))
    captcha = RecaptchaField()
    submit = SubmitField("Register!")

class NewsFormBase(
    model_form(Newspost, base_class=FormBase, exclude=["portrait"])):
    portrait = QuerySelectField(u"Portrait",
        query_factory=lambda: Portrait.query.order_by(Portrait.name),
        get_label="name")
    submit = SubmitField("Post!")

class NewsForm(NewsFormBase):
    pass

class EditNewsForm(NewsFormBase):
    time = DateTimeField("Post time", default=datetime.now)
    submit = SubmitField("Edit!")

def label_for_comic(comic):
    return u'"%s" (%d)' % (comic.title, comic.position)

def select_option_for_comics(first, second):
    first_label = label_for_comic(first)
    second_label = label_for_comic(second)
    return first.id, u"%s to %s" % (first_label, second_label)

def select_list_for_comics(comics):
    if comics:
        first = comics[0]
        l = [(-1, u"Before %s" % label_for_comic(first))]
        if len(comics) > 1:
            for first, second in zip(comics, comics[1::]):
                l.append(select_option_for_comics(first, second))
            last = comics[-1]
            l.append((second.id, u"After %s" % label_for_comic(last)))
        else:
            l.append((comics[0].id, u"After %s" % label_for_comic(comics[0])))
        return l
    else:
        return [(-2, "<No comics exist yet>")]


class ComicFormBase(FormBase):
    file = FileField("Select a file to upload",
        validators=(BetterFileAllowed(images, "Images only!"),))
    title = TextField("Title", validators=(Required(), Length(max=80)))
    description = TextAreaField("Alternate Text")
    comment = TextAreaField("Commentary")
    index = SelectField(u"Where should this comic be placed?",
                        coerce=int)
    characters = QuerySelectMultipleField(u"Characters", get_label="name")
    time = DateTimeField("Activation time", default=datetime.now)

    def __init__(self, universe, *args, **kwargs):
        super(ComicFormBase, self).__init__(*args, **kwargs)

        # Set up the comics index.
        q = Comic.query.filter_by(universe=universe)
        comics = q.order_by(Comic.position).all()
        self.index.choices = select_list_for_comics(comics)

        # Set up the query factory for characters.
        def f():
            q = Character.query.filter_by(universe=universe)
            q = q.order_by(Character.name)
            return q
        self.characters.query_factory = f


CreateComicForm, ModifyComicForm = makeCU(ComicFormBase)

class CommentForm(FormBase):
    anonymous = BooleanField("Post anonymously?")
    sage = BooleanField("Sage?")
    subject = TextField("Subject")
    comment = TextAreaField("Comment")
    datafile = FileField("Image", validators=(BetterFileAllowed(images),))
    submit = SubmitField("Submit")

class ChanForm(FormBase):
    """
    A basic ?chan-style form for both new threads and new replies.
    """

    name = TextField("Name", default="Anonymous")
    email = TextField("Email")
    subject = TextField("Subject")
    comment = TextAreaField("Comment")
    datafile = FileField("Image")
    submit = SubmitField("Submit")
