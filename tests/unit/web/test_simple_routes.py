"""Simple unit tests for Flask routes - working version."""

import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

# Change to project directory to handle relative imports
original_cwd = os.getcwd()
os.chdir(project_root)

try:
    from web.app import app

    def test_app_creation():
        """Test that the Flask app can be created."""
        assert app is not None
        assert app.name == "web.app"

    def test_app_config():
        """Test app configuration."""
        assert hasattr(app, "config")
        # App should have testing config when we set it
        app.config["TESTING"] = True
        assert app.config["TESTING"] is True

    def test_app_has_routes():
        """Test that app has expected routes."""
        # Get all registered routes
        routes = []
        for rule in app.url_map.iter_rules():
            routes.append(rule.rule)

        # Check for key routes
        assert "/" in routes  # index
        assert "/search" in routes  # search

    def test_simple_index_route():
        """Test the index route returns 200."""
        app.config["TESTING"] = True
        app.config["WTF_CSRF_ENABLED"] = False

        with app.test_client() as client:
            response = client.get("/")
            assert response.status_code == 200
            assert b"Weather Dashboard" in response.data

finally:
    # Restore original working directory
    os.chdir(original_cwd)
