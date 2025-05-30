import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logging(app):
    """Configure logging for the Flask application."""
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Configure logging format
    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s in %(module)s: %(message)s"
    )

    # File handler for general logs
    file_handler = RotatingFileHandler(
        "logs/weather_app.log",
        maxBytes=1024 * 1024,  # 1MB
        backupCount=10,
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)

    # File handler for errors
    error_file_handler = RotatingFileHandler(
        "logs/error.log",
        maxBytes=1024 * 1024,  # 1MB
        backupCount=10,
    )
    error_file_handler.setFormatter(formatter)
    error_file_handler.setLevel(logging.ERROR)

    # Stream handler for console output
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.DEBUG if app.debug else logging.INFO)

    # Remove default Flask handlers and add our custom ones
    app.logger.handlers = []
    app.logger.addHandler(file_handler)
    app.logger.addHandler(error_file_handler)
    app.logger.addHandler(console_handler)

    # Set overall logging level
    app.logger.setLevel(logging.DEBUG if app.debug else logging.INFO)

    # Log startup message with port information
    port = os.environ.get("FLASK_PORT", "5001")
    app.logger.info(f"Weather Dashboard startup on port {port}")


def init_debugging(app):
    """Initialize debugging configurations for the Flask application."""
    # Set debug mode based on environment variable
    app.debug = os.environ.get("FLASK_DEBUG", "0") == "1"

    # Enable more detailed error pages in debug mode
    app.config["EXPLAIN_TEMPLATE_LOADING"] = app.debug

    # Configure session for debugging if needed
    if app.debug:
        app.config["TEMPLATES_AUTO_RELOAD"] = True
        app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0

    # Setup logging
    setup_logging(app)

    # Register debug routes if in debug mode
    if app.debug:

        @app.route("/debug/routes")
        def list_routes():
            """List all registered routes for debugging."""
            routes = []
            for rule in app.url_map.iter_rules():
                routes.append(
                    {
                        "endpoint": rule.endpoint,
                        "methods": sorted(rule.methods),
                        "path": str(rule),
                        "arguments": sorted(rule.arguments),
                    }
                )
            return {"routes": routes}

        @app.route("/debug/config")
        def show_config():
            """Show application configuration for debugging."""
            config = {
                key: str(value)
                for key, value in app.config.items()
                if not key.startswith("_")
            }
            return {"config": config}
