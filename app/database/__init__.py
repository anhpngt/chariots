from flask_sqlalchemy import SQLAlchemy
from flask import Flask

db = SQLAlchemy()


def setup_database(app: Flask) -> None:
    db.init_app(app)

    @app.before_first_request
    def setup_sqlalchemy():
        db.create_all()
