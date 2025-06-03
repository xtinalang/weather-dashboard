import sys
from pathlib import Path

import pytest


def _setup_paths():
    """Set up Python paths for testing."""
    # Add the project root directory to Python path
    project_root = Path(__file__).parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    # Add the web directory to Python path
    web_dir = project_root / "web"
    if str(web_dir) not in sys.path:
        sys.path.insert(0, str(web_dir))


# Set up paths before importing web modules
_setup_paths()

from web.app import app as flask_app  # noqa: E402


@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    flask_app.config.update(
        {"TESTING": True, "WTF_CSRF_ENABLED": False, "SECRET_KEY": "test-key"}
    )
    return flask_app


@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """A test CLI runner for the Flask app."""
    return app.test_cli_runner()
