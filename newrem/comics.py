from flask import Blueprint

comics = Blueprint("comics", __name__, static_folder="static",
    template_folder="templates")
