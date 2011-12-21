from datetime import datetime

from wtforms.ext.dateutil.fields import DateTimeField
from wtforms.ext.sqlalchemy.fields import (QuerySelectMultipleField,
    QuerySelectField)
from wtforms.fields import BooleanField, TextAreaField
from wtforms.validators import EqualTo, Length

from flaskext.uploads import IMAGES, UploadSet
from flaskext.wtf import (Form, FileAllowed, FileRequired, Required,
    FileField, PasswordField, RecaptchaField, SubmitField, TextField)

from newrem.models import Character, Comic, Portrait
from newrem.util import split_camel_case

images = UploadSet("images", IMAGES)
pngs = UploadSet("pngs", ("png",))

portrait = FileField("Select a portrait",
    validators=(FileAllowed(pngs, "PNGs only!"),))

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

class CharacterCreateForm(FormBase):
    name = TextField(u"New name", validators=(Required(),))
    portrait = portrait
    submit = SubmitField("Create!")

class CharacterModifyForm(FormBase):
    characters = QuerySelectField(u"Characters",
        query_factory=lambda: Character.query.order_by(Character.name),
        get_label="name")
    name = TextField(u"New name")
    portrait = portrait
    submit = SubmitField("Modify!")

class CharacterDeleteForm(FormBase):
    characters = QuerySelectField(u"Characters",
        query_factory=lambda: Character.query.order_by(Character.name),
        get_label="name")
    submit = SubmitField("Delete!")

class PortraitCreateForm(FormBase):
    name = TextField(u"New name", validators=(Required(),))
    portrait = portrait
    submit = SubmitField("Create!")

class PortraitModifyForm(FormBase):
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

class NewsForm(FormBase):
    title = TextField("Title", validators=(Required(),))
    content = TextAreaField("Content")
    portrait = QuerySelectField(u"Portrait",
        query_factory=lambda: Portrait.query.order_by(Portrait.name),
        get_label="name")
    submit = SubmitField("Post!")

class UploadForm(FormBase):
    file = FileField("Select a file to upload",
        validators=(FileRequired("Must upload a comic!"),
            FileAllowed(images, "Images only!")))
    title = TextField("Title", validators=(Required(), Length(max=80)))
    description = TextAreaField("Alternate Text")
    comment = TextAreaField("Commentary")
    index = QuerySelectField(u"Which comic should come before this one?",
        query_factory=lambda: Comic.query.order_by(Comic.position),
        get_label=lambda comic:
            u"%d: %s, %d" % (comic.position, comic.title, comic.id))
    after = BooleanField("(After, not before)")
    characters = QuerySelectMultipleField(u"Characters",
        query_factory=lambda: Character.query.order_by(Character.name),
        get_label="name")
    time = DateTimeField("Activation time", default=datetime.now())
    submit = SubmitField("Upload!")

class CommentForm(FormBase):
    anonymous = BooleanField("Post anonymously?")
    sage = BooleanField("Sage?")
    subject = TextField("Subject")
    comment = TextAreaField("Comment")
    datafile = FileField("Image", validators=(FileAllowed(images),))
    submit = SubmitField("Submit")
