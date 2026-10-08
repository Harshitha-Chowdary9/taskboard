import os
from flask import Flask
from . import db


def create_app(test_config=None):
    app = Flask(__name__)
    app.config["DATABASE"] = os.environ.get("TASKBOARD_DB", "taskboard.db")
    if test_config:
        app.config.update(test_config)
    db.init_app(app)
    from .routes import bp
    app.register_blueprint(bp)
    with app.app_context():
        db.init_db()
    return app
