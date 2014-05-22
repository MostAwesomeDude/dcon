# Copyright 2014 Google Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License.  You may obtain a copy
# of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.  See the
# License for the specific language governing permissions and limitations under
# the License.
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask.ext.login import login_user, logout_user

from newrem.forms import LoginForm, RegisterForm
from newrem.models import db, User

users = Blueprint("users", __name__)

@users.route("/register", methods=("GET", "POST"))
def register():
    form = RegisterForm()

    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()

        if user:
            flash("Username already taken; please pick another!")
        else:
            user = User(form.username.data, form.password.data)
            db.session.add(user)
            user.login()
            login_user(user, remember=True)
            flash("Logged in!")
            if "next" in request.args:
                return redirect(request.args["next"])
            else:
                return redirect(url_for("index"))

    return render_template("register.html", form=form)

@users.route("/login", methods=("GET", "POST"))
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()

        if user:
            if user.check_password(form.password.data):
                user.login()
                login_user(user, remember=True)
                flash("Logged in!")
                if "next" in request.args:
                    return redirect(request.args["next"])
                else:
                    return redirect(url_for("index"))
            else:
                flash("Incorrect password!")
        else:
            flash("No user %s found!" % form.username.data)

    return render_template("login.html", login_form=form)

@users.route("/logout")
def logout():
    logout_user()
    flash("Logged out!")

    if "next" in request.args:
        return redirect(request.args["next"])
    else:
        return redirect(url_for("index"))
