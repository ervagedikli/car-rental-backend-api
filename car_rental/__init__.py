import os

from flask import Flask

from .extensions import db
from .routes import api


def create_app(test_config=None):
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
        "DATABASE_URL",
        "postgresql://root:rootpassword@localhost:5432/car_rental_db",
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    if test_config:
        app.config.update(test_config)

    db.init_app(app)
    app.register_blueprint(api)

    with app.app_context():
        db.create_all()

    return app
