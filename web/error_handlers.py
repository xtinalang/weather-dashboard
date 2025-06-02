"""
Error handling module for the weather web application.
Contains error handlers, input validation, and logging configuration.
"""

import logging
from typing import Union

from flask import Flask, flash, redirect, render_template, request, url_for
from flask_wtf.csrf import CSRFError

from .utils import DEFAULT_FORECAST_DAYS


# Configure logging
def setup_logging():
    """Configure application logging."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler("web_app.log"), logging.StreamHandler()],
    )
    return logging.getLogger(__name__)


logger = setup_logging()


# Input validation helpers
def validate_coordinates(lat: Union[str, float], lon: Union[str, float]) -> bool:
    """Validate coordinate ranges."""
    try:
        lat = float(lat)
        lon = float(lon)
        if not (-90 <= lat <= 90):
            logger.warning(f"Latitude {lat} out of valid range (-90 to 90)")
            return False
        if not (-180 <= lon <= 180):
            logger.warning(f"Longitude {lon} out of valid range (-180 to 180)")
            return False
        return True
    except (ValueError, TypeError) as e:
        logger.warning(f"Invalid coordinates format: lat={lat}, lon={lon}, error={e}")
        return False


def validate_location_data(location_data: dict) -> bool:
    """Validate location data structure."""
    required_fields = ["name", "lat", "lon", "country"]
    try:
        # Check required fields exist
        if not all(field in location_data for field in required_fields):
            missing = [f for f in required_fields if f not in location_data]
            logger.warning(f"Missing required location fields: {missing}")
            return False

        # Validate coordinates
        if not validate_coordinates(location_data["lat"], location_data["lon"]):
            return False

        # Validate string fields
        if not location_data["name"] or not isinstance(location_data["name"], str):
            logger.warning("Invalid location name")
            return False
        if not location_data["country"] or not isinstance(
            location_data["country"], str
        ):
            logger.warning("Invalid country")
            return False

        return True
    except Exception as e:
        logger.error(f"Location data validation error: {e}")
        return False


def safe_location_lookup(coords: tuple[float, float], weather_api) -> tuple[bool, str]:
    """
    Safely look up location information.
    Returns (success, error_message).
    """
    try:
        lat, lon = coords
        if not validate_coordinates(lat, lon):
            return False, "Invalid coordinates"

        # Try to get location info from weather API
        weather_data = safe_api_operation(weather_api.get_weather, coords)
        if not weather_data:
            return False, "Could not retrieve location data"

        # Validate location data
        if "location" not in weather_data:
            logger.error("Weather data missing location information")
            return False, "Location information not available"

        location_info = weather_data["location"]
        if not validate_location_data(location_info):
            return False, "Invalid location data received"

        return True, ""

    except Exception as e:
        logger.error(f"Location lookup error: {e}", exc_info=True)
        return False, "Error looking up location"


def safe_float_conversion(value: str, default: float = 0.0) -> float:
    """Safely convert string to float with fallback."""
    try:
        return float(value)
    except (ValueError, TypeError):
        logger.warning(f"Failed to convert '{value}' to float, using default {default}")
        return default


def safe_int_conversion(value: str, default: int = DEFAULT_FORECAST_DAYS) -> int:
    """Safely convert string to int with fallback."""
    try:
        return int(value)
    except (ValueError, TypeError):
        logger.warning(f"Failed to convert '{value}' to int, using default {default}")
        return default


def validate_query_string(query: str, max_length: int = 200) -> bool:
    """Validate user input query strings."""
    if not query or not isinstance(query, str):
        return False

    # Check length
    if len(query.strip()) == 0 or len(query) > max_length:
        logger.warning(f"Invalid query length: {len(query)} characters")
        return False

    # Check for potentially dangerous patterns
    dangerous_patterns = ["<script", "javascript:", "data:", "vbscript:"]
    query_lower = query.lower()
    for pattern in dangerous_patterns:
        if pattern in query_lower:
            logger.warning(f"Potentially dangerous query pattern detected: {pattern}")
            return False

    return True


def register_error_handlers(app: Flask) -> None:
    """Register all error handlers with the Flask app."""

    def create_index_context():
        """Create context variables for index template."""
        from .forms import (
            DateWeatherNLForm,
            ForecastDaysForm,
            LocationSearchForm,
            UnitSelectionForm,
            UserInputLocationForm,
        )

        search_form = LocationSearchForm()
        ui_form = UserInputLocationForm()
        unit_form = UnitSelectionForm()
        forecast_days_form = ForecastDaysForm()
        nl_form = DateWeatherNLForm()
        favorites = []

        return {
            "search_form": search_form,
            "ui_form": ui_form,
            "unit_form": unit_form,
            "forecast_days_form": forecast_days_form,
            "nl_form": nl_form,
            "favorites": favorites,
        }

    @app.errorhandler(404)
    def not_found_error(error):
        """Handle 404 errors."""
        logger.warning(f"404 error: {request.url}")

        # Check if this is a coordinate-based URL
        path = request.path
        if "/nl-result/" in path or "/weather/" in path or "/forecast/" in path:
            try:
                # Extract coordinates from path
                coords_part = path.split("/")[-2:]
                lat, lon = map(float, coords_part)

                # Validate coordinates and location
                success, error_msg = safe_location_lookup((lat, lon), app.weather_api)
                if not success:
                    flash(f"Invalid location: {error_msg}", "error")
                else:
                    flash("The requested weather data is not available.", "warning")
            except Exception as e:
                logger.error(f"Error processing coordinates in 404 handler: {e}")
                flash("Invalid location coordinates.", "error")
        else:
            flash("The page you're looking for doesn't exist.", "warning")

        context = create_index_context()
        return render_template("index.html", **context), 404

    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors."""
        logger.error(f"500 error: {error}")
        flash("An internal server error occurred. Please try again later.", "error")
        context = create_index_context()
        return render_template("index.html", **context), 500

    @app.errorhandler(400)
    def bad_request_error(error):
        """Handle 400 errors."""
        logger.warning(f"400 error: {error}")
        flash("Invalid request. Please check your input and try again.", "warning")
        context = create_index_context()
        return render_template("index.html", **context), 400

    @app.errorhandler(403)
    def forbidden_error(error):
        """Handle 403 errors."""
        logger.warning(f"403 error: {error}")
        flash("Access forbidden.", "error")
        context = create_index_context()
        return render_template("index.html", **context), 403

    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        """Handle CSRF token errors."""
        logger.warning(f"CSRF error: {e.description}")
        flash("Security token expired. Please try again.", "warning")
        return redirect(url_for("index"))

    @app.errorhandler(Exception)
    def handle_general_exception(error):
        """Handle general unhandled exceptions."""
        logger.error(f"Unhandled exception: {error}", exc_info=True)
        flash("An unexpected error occurred. Please try again.", "error")
        context = create_index_context()
        return render_template("index.html", **context), 500


# Database operation wrapper with error handling
def safe_database_operation(operation, *args, **kwargs):
    """Safely execute database operations with error handling."""
    try:
        return operation(*args, **kwargs)
    except OSError as e:
        logger.error(f"Database access error: {e}")
        flash("Database access error. Please try again later.", "warning")
        return None
    except Exception as e:
        logger.error(f"Database operation failed: {e}")
        flash("Database operation failed. Please try again later.", "error")
        return None


# API operation wrapper with error handling
def safe_api_operation(operation, *args, **kwargs):
    """Safely execute API operations with error handling."""
    try:
        return operation(*args, **kwargs)
    except (ConnectionError, TimeoutError) as e:
        logger.error(f"API connection error: {e}")
        flash("Weather service connection error. Please try again later.", "error")
        return None
    except ValueError as e:
        logger.error(f"API data validation error: {e}")
        flash("Invalid weather data received. Please try again.", "error")
        return None
    except KeyError as e:
        logger.error(f"API data format error: missing {e}")
        flash("Weather service returned incomplete data. Please try again.", "error")
        return None
    except Exception as e:
        logger.error(f"API operation failed: {e}")
        flash("Weather service error. Please try again later.", "error")
        return None


# Initialize database with error handling
def initialize_database_safely(initialize_database_func):
    """Initialize database with comprehensive error handling."""
    try:
        initialize_database_func()
        logger.info("Database initialized successfully")
        return True
    except OSError as e:
        logger.error(f"Database file access error: {e}")
        flash("Database access error. Some features may be limited.", "warning")
        return False
    except ImportError as e:
        logger.error(f"Database module import error: {e}")
        flash("Database module error. Some features may be limited.", "warning")
        return False
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        flash(
            "Database initialization failed. Some features may be limited.", "warning"
        )
        return False


# Initialize components with error handling
def initialize_components_safely(component_init_func):
    """Initialize application components with error handling."""
    try:
        components = component_init_func()
        logger.info("Application components initialized successfully")
        return components
    except Exception as e:
        logger.error(f"Failed to initialize application components: {e}")
        flash(
            "Some application features may be limited due to initialization errors.",
            "warning",
        )
        # Return None objects to prevent crashes
        return {
            "weather_api": None,
            "display": None,
            "location_manager": None,
            "location_repo": None,
            "forecast_manager": None,
            "current_manager": None,
            "settings_repo": None,
            "utility": None,
        }
