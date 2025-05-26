"""Simple unit tests for Flask routes - using shared utilities."""


def test_app_creation(flask_app):
    """Test that the Flask app can be created."""
    assert flask_app is not None
    assert flask_app.name == "web.app"


def test_app_config(flask_app):
    """Test app configuration."""
    assert hasattr(flask_app, "config")
    # App should have testing config when we set it
    flask_app.config["TESTING"] = True
    assert flask_app.config["TESTING"] is True


def test_app_has_routes(flask_app):
    """Test that app has expected routes."""
    # Get all registered routes
    routes = []
    for rule in flask_app.url_map.iter_rules():
        routes.append(rule.rule)

    # Check for key routes
    assert "/" in routes  # index
    assert "/search" in routes  # search


def test_simple_index_route(flask_app):
    """Test the index route returns 200."""
    flask_app.config["TESTING"] = True
    flask_app.config["WTF_CSRF_ENABLED"] = False

    with flask_app.test_client() as client:
        response = client.get("/")
        assert response.status_code == 200
        assert b"Weather Dashboard" in response.data
