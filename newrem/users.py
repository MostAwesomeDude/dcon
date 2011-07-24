from flask import Blueprint, flash, redirect, render_template, request, url_for
from flaskext.login import login_user, logout_user

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
