"""Basic Flask web UI tests that work around import issues."""

import importlib.util
import os
import sys
from pathlib import Path


def test_web_module_exists():
    """Test that the web module directory exists."""
    project_root = Path(__file__).resolve().parent.parent.parent.parent
    web_dir = project_root / "web"
    assert web_dir.exists()
    assert web_dir.is_dir()


def test_flask_app_can_be_loaded():
    """Test that the Flask app can be loaded dynamically."""
    project_root = Path(__file__).resolve().parent.parent.parent.parent

    # Add project root to path
    sys.path.insert(0, str(project_root))

    # Change to project directory for relative imports
    original_cwd = os.getcwd()
    os.chdir(project_root)

    try:
        # Load the web.app module dynamically
        app_path = project_root / "web" / "app.py"
        spec = importlib.util.spec_from_file_location("web.app", app_path)
        web_app_module = importlib.util.module_from_spec(spec)

        # Execute the module to load the app
        spec.loader.exec_module(web_app_module)

        # Test that app exists and is a Flask app
        assert hasattr(web_app_module, "app")
        app = web_app_module.app
        assert app is not None

        # Test basic Flask app properties
        assert hasattr(app, "config")
        assert hasattr(app, "url_map")

        # Test that we can create a test client
        app.config["TESTING"] = True
        with app.test_client() as client:
            response = client.get("/")
            # Should get either 200 or redirect
            assert response.status_code in [200, 302]

    finally:
        # Restore original working directory
        os.chdir(original_cwd)
        # Clean up sys.path
        if str(project_root) in sys.path:
            sys.path.remove(str(project_root))


def test_web_app_files_exist():
    """Test that all expected Flask app files exist."""
    project_root = Path(__file__).resolve().parent.parent.parent.parent
    web_dir = project_root / "web"

    expected_files = ["app.py", "forms.py", "helpers.py", "utils.py", "__init__.py"]

    for filename in expected_files:
        file_path = web_dir / filename
        assert file_path.exists(), f"Missing expected file: {filename}"


def test_web_templates_directory_exists():
    """Test that the templates directory exists."""
    project_root = Path(__file__).resolve().parent.parent.parent.parent
    templates_dir = project_root / "web" / "templates"
    assert templates_dir.exists()
    assert templates_dir.is_dir()


def test_web_static_directory_exists():
    """Test that the static directory exists."""
    project_root = Path(__file__).resolve().parent.parent.parent.parent
    static_dir = project_root / "web" / "static"
    assert static_dir.exists()
    assert static_dir.is_dir()
