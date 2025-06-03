"""Web interface for the Weather Dashboard."""

from flask import Flask
from flask_wtf.csrf import CSRFProtect

csrf = CSRFProtect()


def create_app(testing=False):
    """Create and configure the Flask application."""
    app = Flask(__name__)

    if testing:
        app.config.update(
            {"TESTING": True, "WTF_CSRF_ENABLED": False, "SECRET_KEY": "test-key"}
        )
    else:
        app.config.from_object("web.config.Config")

    csrf.init_app(app)
    return app
