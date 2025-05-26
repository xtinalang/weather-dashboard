"""Shared utilities for web unit tests to eliminate code duplication."""

import importlib.util
import os
import sys
from pathlib import Path
from typing import Any, Tuple

import pytest


def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).resolve().parent.parent.parent.parent


def dynamic_import_cleanup(original_cwd: str, project_root: Path) -> None:
    """Clean up after dynamic import operations."""
    os.chdir(original_cwd)
    if str(project_root) in sys.path:
        sys.path.remove(str(project_root))


def load_web_module(module_name: str, file_path: str) -> Tuple[Any, str, Path]:
    """
    Dynamically load a web module.

    Args:
        module_name: Name for the module (e.g., 'web.app')
        file_path: Relative path from project root (e.g., 'web/app.py')

    Returns:
        Tuple of (module, original_cwd, project_root)
    """
    project_root = get_project_root()

    # Add project root to path
    sys.path.insert(0, str(project_root))

    # Change to project directory for relative imports
    original_cwd = os.getcwd()
    os.chdir(project_root)

    try:
        # Load the module dynamically
        module_path = project_root / file_path
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        return module, original_cwd, project_root

    except Exception:
        # Clean up on error
        dynamic_import_cleanup(original_cwd, project_root)
        raise


def get_flask_app():
    """Dynamically load and return the Flask app."""
    app_module, original_cwd, project_root = load_web_module("web.app", "web/app.py")
    return app_module.app, original_cwd, project_root


def get_web_forms():
    """Dynamically load and return the web.forms module."""
    forms_module, original_cwd, project_root = load_web_module(
        "web.forms", "web/forms.py"
    )
    return forms_module, original_cwd, project_root


def get_web_helpers():
    """Dynamically load and return the web.helpers module."""
    helpers_module, original_cwd, project_root = load_web_module(
        "web.helpers", "web/helpers.py"
    )
    return helpers_module, original_cwd, project_root


def get_web_utils():
    """Dynamically load and return the web.utils module."""
    utils_module, original_cwd, project_root = load_web_module(
        "web.utils", "web/utils.py"
    )
    return utils_module, original_cwd, project_root


def get_web_modules():
    """Dynamically load and return both web.helpers and web.utils modules."""
    project_root = get_project_root()

    # Add project root to path
    sys.path.insert(0, str(project_root))

    # Change to project directory for relative imports
    original_cwd = os.getcwd()
    os.chdir(project_root)

    try:
        # Load the web.helpers module
        helpers_path = project_root / "web" / "helpers.py"
        helpers_spec = importlib.util.spec_from_file_location(
            "web.helpers", helpers_path
        )
        web_helpers_module = importlib.util.module_from_spec(helpers_spec)
        helpers_spec.loader.exec_module(web_helpers_module)

        # Load the web.utils module
        utils_path = project_root / "web" / "utils.py"
        utils_spec = importlib.util.spec_from_file_location("web.utils", utils_path)
        web_utils_module = importlib.util.module_from_spec(utils_spec)
        utils_spec.loader.exec_module(web_utils_module)

        return web_helpers_module, web_utils_module, original_cwd, project_root

    except Exception:
        # Clean up on error
        dynamic_import_cleanup(original_cwd, project_root)
        raise


# Shared pytest fixtures
@pytest.fixture
def flask_app():
    """Get Flask app for testing."""
    app, original_cwd, project_root = get_flask_app()
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False

    yield app

    dynamic_import_cleanup(original_cwd, project_root)


@pytest.fixture
def web_forms_module():
    """Get web.forms module for testing."""
    forms_module, original_cwd, project_root = get_web_forms()

    yield forms_module

    dynamic_import_cleanup(original_cwd, project_root)


@pytest.fixture
def web_helpers_module():
    """Get web.helpers module for testing."""
    helpers_module, original_cwd, project_root = get_web_helpers()

    yield helpers_module

    dynamic_import_cleanup(original_cwd, project_root)


@pytest.fixture
def web_utils_module():
    """Get web.utils module for testing."""
    utils_module, original_cwd, project_root = get_web_utils()

    yield utils_module

    dynamic_import_cleanup(original_cwd, project_root)


@pytest.fixture
def web_modules_combined():
    """Get both web.helpers and web.utils modules for testing."""
    helpers_module, utils_module, original_cwd, project_root = get_web_modules()

    yield helpers_module, utils_module

    dynamic_import_cleanup(original_cwd, project_root)
