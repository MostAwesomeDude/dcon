#!/usr/bin/env python

from flask import Flask
from flaskext.sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///temp.db"

db = SQLAlchemy(app)

if __name__ == "__main__":
    import main
    raise SystemExit(main.app.run())
