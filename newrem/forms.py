from datetime import datetime

from wtforms.ext.dateutil.fields import DateTimeField
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from wtforms.fields import Field, TextAreaField
from wtforms.validators import EqualTo, Length
from wtforms.widgets import TextInput

from flaskext.uploads import IMAGES, UploadSet
from flaskext.wtf import (Form, FileAllowed, FileRequired,
    Required, FileField, IntegerField, PasswordField, SubmitField, TextField)

from newrem.models import Character, Portrait

images = UploadSet("images", IMAGES)
pngs = UploadSet("pngs", ("png",))

class TagListField(Field):
    widget = TextInput()

    def _value(self):
        if self.data:
            return u", ".join(self.data)
        else:
            return u""

    def process_formdata(self, data):
        if data:
            self.data = [word.strip() for word in data[0].split(",")]
            self.data.sort()
        else:
            self.data = []

portrait = FileField("Select a portrait",
    validators=(FileAllowed(pngs, "PNGs only!"),))

class CharacterCreateForm(Form):
    name = TextField(u"New name", validators=(Required(),))
    portrait = portrait
    submit = SubmitField("Create!")

class CharacterModifyForm(Form):
    characters = QuerySelectField(u"Characters",
        query_factory=lambda: Character.query.order_by(Character.name),
        get_label="name")
    name = TextField(u"New name")
    portrait = portrait
    submit = SubmitField("Modify!")

class CharacterDeleteForm(Form):
    characters = QuerySelectField(u"Characters",
        query_factory=lambda: Character.query.order_by(Character.name),
        get_label="name")
    submit = SubmitField("Delete!")

class PortraitCreateForm(Form):
    name = TextField(u"New name", validators=(Required(),))
    portrait = portrait
    submit = SubmitField("Create!")

class PortraitModifyForm(Form):
    portraits = QuerySelectField(u"Portraits",
        query_factory=lambda: Portrait.query.order_by(Portrait.name),
        get_label="name")
    portrait = portrait
    submit = SubmitField("Modify!")

class LoginForm(Form):
    username = TextField("Username", validators=(Required(),))
    password = PasswordField("Password", validators=(Required(),))
    submit = SubmitField("Login!")

class RegisterForm(LoginForm):
    confirm = PasswordField("Confirm password",
        validators=(Required(), EqualTo("password")))
    submit = SubmitField("Register!")

class NewsForm(Form):
    title = TextField("Title", validators=(Required(),))
    content = TextAreaField("Content")
    portrait = QuerySelectField(u"Portrait",
        query_factory=lambda: Portrait.query.order_by(Portrait.name),
        get_label="name")
    submit = SubmitField("Post!")

class UploadForm(Form):
    file = FileField("Select a file to upload",
        validators=(FileRequired("Must upload a comic!"),
            FileAllowed(images, "Images only!")))
    title = TextField("Title", validators=(Required(), Length(max=80)))
    description = TextAreaField("Alternate Text")
    comment = TextAreaField("Commentary")
    index = IntegerField("Where to insert this comic?",
        validators=(Required(),))
    characters = TagListField("Characters")
    time = DateTimeField("Activation time", default=datetime.now())
    submit = SubmitField("Upload!")
