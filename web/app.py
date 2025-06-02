import os
import re
from datetime import datetime
from typing import Any, cast

from decouple import config
from flask import Flask, flash, jsonify, redirect, render_template, request, url_for
from flask_wtf.csrf import CSRFProtect

from weather_app.api import WeatherAPI
from weather_app.current import CurrentWeatherManager
from weather_app.database import init_db as initialize_database
from weather_app.display import WeatherDisplay
from weather_app.forecast import ForecastManager
from weather_app.location import LocationManager
from weather_app.repository import LocationRepository, SettingsRepository
from weather_app.weather_types import TemperatureUnit

from .error_handlers import (
    initialize_components_safely,
    initialize_database_safely,
    logger,
    register_error_handlers,
    safe_database_operation,
    safe_float_conversion,
    safe_location_lookup,
    validate_coordinates,
    validate_query_string,
)
from .forms import (
    DateWeatherNLForm,
    ForecastDaysForm,
    LocationDisambiguationForm,
    LocationSearchForm,
    UnitSelectionForm,
    UserInputLocationForm,
)
from .helpers import (
    Helpers,
    extract_location_from_query,
    get_forecast_data,
    get_weather_data,
)
from .logging_config import init_debugging
from .utils import (
    CELSIUS,
    DEFAULT_FORECAST_DAYS,
    DEFAULT_TEMP_UNIT,
    VALID_UNITS,
    Utility,
)

# Configure port from environment variables with fallbacks
PORT = config(
    "FLASK_PORT",
    default=config(
        "PORT",
        default=config("APP_PORT", default=os.environ.get("FLASK_PORT", 5001)),
        cast=int,
    ),
    cast=int,
)

# Initialize Flask app
app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key")
csrf = CSRFProtect(app)

# Initialize debugging and logging
init_debugging(app)

# Register error handlers
register_error_handlers(app)

# Initialize database
initialize_database_safely(initialize_database)


# Initialize API and components
def initialize_app_components():
    """Initialize application components."""
    return {
        "weather_api": WeatherAPI(),
        "display": WeatherDisplay(),
        "location_manager": None,
        "location_repo": LocationRepository(),
        "forecast_manager": None,
        "current_manager": None,
        "settings_repo": SettingsRepository(),
        "utility": Utility(),
    }


# Initialize components with error handling
components = initialize_components_safely(initialize_app_components)

# Extract components
weather_api = components.get("weather_api")
display = components.get("display")
location_repo = components.get("location_repo")
settings_repo = components.get("settings_repo")
utility = components.get("utility")

# Initialize components that depend on others
if weather_api and display:
    location_manager = LocationManager(weather_api, display)
    forecast_manager = ForecastManager(weather_api, display)
    current_manager = CurrentWeatherManager(weather_api, display)
else:
    location_manager = None
    forecast_manager = None
    current_manager = None


# Context processor to add current year to all templates
@app.context_processor
def inject_current_year() -> dict[str, int]:
    return {"current_year": datetime.now().year}


# Routes
@app.route("/")
def index() -> str:
    """Home page with search form."""
    app.logger.debug("Rendering index page")
    search_form = LocationSearchForm()
    ui_form = UserInputLocationForm()
    unit_form = UnitSelectionForm()
    forecast_days_form = ForecastDaysForm()
    nl_form = DateWeatherNLForm()

    # Default to user's saved setting if available
    try:
        settings = (
            safe_database_operation(settings_repo.get_settings)
            if settings_repo
            else None
        )
        if settings:
            app.logger.debug(f"Using saved settings: {settings}")
            unit_form.unit.default = (
                "F" if settings.temperature_unit.lower() == "fahrenheit" else "C"
            )
            forecast_days_form.forecast_days.default = str(settings.forecast_days)
            unit_form.process()
            forecast_days_form.process()
    except (AttributeError, ValueError) as e:
        app.logger.warning(f"Settings data format issue: {e}")
    except Exception as e:
        app.logger.error(f"Error loading settings: {e}", exc_info=True)

    # Get favorite locations for quick access
    favorites = []
    if location_repo:
        favorites = safe_database_operation(location_repo.get_favorites)
        if favorites is None:
            favorites = []
        app.logger.debug(f"Loaded {len(favorites)} favorite locations")

    return render_template(
        "index.html",
        search_form=search_form,
        ui_form=ui_form,
        unit_form=unit_form,
        forecast_days_form=forecast_days_form,
        nl_form=nl_form,
        favorites=favorites,
    )


def handle_location_search(query: str, unit: str, action: str = "weather") -> Any:
    """
    Helper function to handle location searches and return appropriate response.
    Returns redirect response or a tuple of (results, None) for multiple results.
    """
    app.logger.debug(
        f"Handling location search - Query: {query}, Unit: {unit}, Action: {action}"
    )
    try:
        # For NL queries, we want to show all options
        if action == "nl":
            results = weather_api.search_city(query)
        else:
            # For regular searches, use disambiguation
            disambiguated = Helpers.disambiguate_location(query)
            app.logger.debug(f"Disambiguated location: {disambiguated}")
            results = weather_api.search_city(disambiguated)

        app.logger.debug(f"Search results: {results}")

        if not results:
            app.logger.info(f"No locations found for query: {query}")
            flash(f"No locations found matching '{query}'", "warning")
            return redirect(url_for("index"))

        if (
            len(results) == 1 and action != "nl"
        ):  # Only auto-redirect for non-NL queries
            # Single result - get coordinates and redirect
            first_result = results[0]
            lat, lon = float(first_result["lat"]), float(first_result["lon"])
            app.logger.debug(
                f"Single result found: {first_result['name']} ({lat}, {lon})"
            )

            if action == "forecast":
                return redirect(url_for("forecast", lat=lat, lon=lon, unit=unit))
            else:
                return redirect(url_for("weather", lat=lat, lon=lon, unit=unit))

        # Multiple results or NL query - return them for template rendering
        app.logger.debug(f"Multiple results found: {len(results)} locations")
        return results, None

    except (ValueError, TypeError) as e:
        app.logger.error(f"Invalid location format: {e}", exc_info=True)
        flash(f"Invalid location format: {str(e)}", "error")
        return redirect(url_for("index"))
    except (ConnectionError, TimeoutError) as e:
        app.logger.error(f"Weather service connection error: {e}", exc_info=True)
        flash(f"Weather service connection error: {str(e)}", "error")
        return redirect(url_for("index"))
    except Exception as e:
        app.logger.error(f"Unexpected error in location search: {e}", exc_info=True)
        flash(f"Error searching for location: {e}", "error")
        return redirect(url_for("index"))


@app.route("/search", methods=["POST"])
def search() -> Any:
    """Search for locations."""
    app.logger.debug("Processing search request")
    form = LocationSearchForm()
    unit = cast(TemperatureUnit, request.form.get("unit", DEFAULT_TEMP_UNIT).upper())
    forecast_days = request.form.get("forecast_days")

    # Determine action based on which form was submitted
    action = (
        "forecast"
        if "forecast_days" in request.form and request.form.get("forecast_days")
        else "weather"
    )
    app.logger.debug(f"Search action: {action}")

    if not form.validate_on_submit():
        app.logger.warning("Search form validation failed")
        flash("Please enter a valid search query.", "warning")
        return redirect(url_for("index"))

    query = form.query.data
    app.logger.debug(f"Search query: {query}")

    if not validate_query_string(query):
        app.logger.warning(f"Invalid search query: {query}")
        flash("Invalid search query. Please check your input.", "warning")
        return redirect(url_for("index"))

    result = handle_location_search(query, unit, action)
    if isinstance(result, tuple):
        results, _ = result
        app.logger.debug(f"Showing selection page for {len(results)} results")
        # Show selection page for multiple results
        return render_template(
            "location_selection.html",
            results=results,
            query=query,
            unit=unit,
            action=action,
            forecast_days=forecast_days,
        )
    return result  # This is a redirect response


@app.route("/select-location", methods=["POST"])
def select_location() -> Any:
    """Handle location selection from search results."""
    app.logger.debug("Processing location selection")

    # Get form data directly since we're using custom HTML radio buttons
    selected_data = request.form.get("selected_location")
    if not selected_data:
        app.logger.warning("No location selected in form submission")
        flash("Please select a location", "error")
        return redirect(url_for("index"))

    # Parse the selected location data
    try:
        # Expected format: "lat,lon,name,region,country"
        parts = selected_data.split(",", 4)
        if len(parts) != 5:
            raise ValueError("Invalid location data format")

        lat, lon = safe_float_conversion(parts[0]), safe_float_conversion(parts[1])
        name, region, country = parts[2:5]

        # Validate coordinates
        if not validate_coordinates(lat, lon):
            raise ValueError("Invalid coordinates")

        app.logger.debug(
            f"Selected location: {name}, {region}, {country} ({lat}, {lon})"
        )

    except (ValueError, TypeError) as e:
        app.logger.error(
            f"Invalid location selection data: {selected_data}, error: {e}"
        )
        flash("Invalid location selection", "error")
        return redirect(url_for("index"))

    action = request.form.get("action", "weather")
    unit = request.form.get("unit", DEFAULT_TEMP_UNIT)
    nl_query = request.form.get("nl_query")
    forecast_days = request.form.get("forecast_days")

    app.logger.debug(f"Action: {action}, Unit: {unit}, NL Query: {nl_query}")

    # Handle different types of requests
    try:
        if action == "forecast":
            return redirect(
                url_for(
                    "forecast_path",
                    coordinates=f"{lat}/{lon}",
                    unit=unit,
                    days=forecast_days,
                )
            )
        elif action == "nl":
            return redirect(
                url_for(
                    "nl_result_with_coords",
                    coordinates=f"{lat}/{lon}",
                    query=nl_query,
                    unit=unit,
                )
            )
        else:
            return redirect(
                url_for(
                    "weather",
                    lat=lat,
                    lon=lon,
                    unit=unit,
                )
            )
    except Exception as e:
        app.logger.error(
            f"Error redirecting after location selection: {e}", exc_info=True
        )
        flash("Error processing location selection", "error")
        return redirect(url_for("index"))


@app.route("/weather/<path:coordinates>")
def weather_path(coordinates: str) -> Any:
    """Handle weather path with coordinates that may include negative values."""
    try:
        lat, lon = Helpers.parse_coordinates_from_path(coordinates)
        return weather(lat, lon)
    except ValueError as e:
        flash(f"Invalid coordinates format: {str(e)}", "error")
        return redirect(url_for("index"))
    except (TypeError, AttributeError) as e:
        flash(f"Error parsing coordinates: {str(e)}", "error")
        return redirect(url_for("index"))


@app.route("/weather/<float:lat>/<float:lon>")
def weather(lat: float, lon: float) -> Any:
    """Show weather for a location by coordinates."""
    # Validate coordinate ranges
    if not validate_coordinates(lat, lon):
        logger.warning(f"Invalid coordinates provided: lat={lat}, lon={lon}")
        flash("Invalid coordinates provided.", "error")
        return redirect(url_for("index"))

    unit = Helpers.get_normalized_unit()
    coords = (lat, lon)

    try:
        weather_data, location = get_weather_data(coords, unit, weather_api)
    except (ConnectionError, TimeoutError) as e:
        logger.error(f"Weather service connection error: {e}")
        flash(f"Weather service connection error: {str(e)}", "error")
        return redirect(url_for("index"))
    except ValueError as e:
        logger.error(f"Invalid weather data: {e}")
        flash(f"Invalid weather data received: {str(e)}", "error")
        return redirect(url_for("index"))
    except KeyError as e:
        logger.error(f"Weather data format error: {e}")
        flash(f"Weather data format error: missing {str(e)}", "error")
        return redirect(url_for("index"))
    except Exception as e:
        logger.error(f"Unexpected error getting weather data: {e}")
        flash("An unexpected error occurred getting weather data.", "error")
        return redirect(url_for("index"))

    # Safe database operation for saving weather record
    safe_database_operation(Helpers.save_weather_record, location, weather_data)

    return render_template(
        "weather.html",
        weather=weather_data,
        location=location,
        unit=unit,
        lat=lat,
        lon=lon,
    )


@app.route("/ui", methods=["POST"])
def ui_location() -> Any:
    """Handle UI location entry."""
    form = UserInputLocationForm()
    unit = cast(TemperatureUnit, request.form.get("unit", DEFAULT_TEMP_UNIT).upper())
    forecast_days = request.form.get("forecast_days")

    # Determine action - UI form is typically for weather
    action = "weather"

    location = request.form.get("location") or (
        form.location.data if form.validate_on_submit() else None
    )

    if not location:
        flash("Please enter a valid location", "error")
        return redirect(url_for("index"))

    # Disambiguate location before searching
    location = Helpers.disambiguate_location(location)

    try:
        results = weather_api.search_city(location)
    except (ConnectionError, TimeoutError) as e:
        flash(f"Weather service connection error: {str(e)}", "error")
        return redirect(url_for("index"))
    except ValueError as e:
        flash(f"Invalid location format: {str(e)}", "error")
        return redirect(url_for("index"))

    if not results:
        flash(f"No cities found matching '{location}'", "warning")
        return redirect(url_for("index"))

    if len(results) == 1:
        # Single result - redirect directly
        return redirect(
            url_for(
                "weather",
                lat=results[0]["lat"],
                lon=results[0]["lon"],
                unit=unit,
            )
        )

    # Multiple results - show selection page
    return render_template(
        "location_selection.html",
        results=results,
        query=location,
        unit=unit,
        action=action,
        forecast_days=forecast_days,
    )


@app.route("/favorite/<int:location_id>", methods=["POST"])
def toggle_favorite(location_id: int) -> Any:
    """Toggle favorite status for a location."""
    try:
        success = location_manager.toggle_favorite(location_id)
        if success:
            flash("Favorite status updated", "success")
        else:
            flash("Failed to update favorite status", "error")
    except OSError as e:
        flash(f"Database access error: {str(e)}", "error")
    except ValueError as e:
        flash(f"Invalid location ID: {str(e)}", "error")
    except Exception as e:
        flash(f"Error updating favorite status: {e}", "error")

    next_page = request.args.get("next") or url_for("index")
    return redirect(next_page)


@app.route("/unit", methods=["POST"])
def update_unit() -> Any:
    """Update temperature unit preference."""
    form = UnitSelectionForm()
    if form.validate_on_submit():
        unit = cast(TemperatureUnit, form.unit.data.upper())
        if unit in VALID_UNITS:
            try:
                unit_value = "celsius" if unit == CELSIUS else "fahrenheit"
                settings_repo.update_temperature_unit(unit_value)
                flash(f"Temperature unit updated to {unit_value}", "success")
            except OSError as e:
                flash(f"Database access error: {str(e)}", "warning")
            except ValueError as e:
                flash(f"Invalid unit value: {str(e)}", "warning")
            except Exception as e:
                flash(f"Failed to update unit preference: {e}", "warning")

    return redirect(url_for("index"))


@app.route("/api/weather/<float:lat>/<float:lon>")
def api_weather(lat: float, lon: float) -> Any:
    """API endpoint for weather data."""
    unit = Helpers.get_normalized_unit()
    coords = (lat, lon)

    try:
        weather_data, _ = get_weather_data(coords, unit, weather_api)
        return jsonify(weather_data)
    except (ConnectionError, TimeoutError) as e:
        return jsonify({"error": f"Weather service connection error: {str(e)}"}), 503
    except ValueError as e:
        return jsonify({"error": f"Invalid weather data: {str(e)}"}), 400
    except KeyError as e:
        return jsonify({"error": f"Weather data format error: {str(e)}"}), 502
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/forecast/<float:lat>/<float:lon>", methods=["GET", "POST"])
def forecast(lat: float, lon: float) -> Any:
    """Show forecast for a location."""
    unit = Helpers.get_normalized_unit()
    coords = (lat, lon)

    # Get forecast days from form or default to 7
    forecast_days = DEFAULT_FORECAST_DAYS
    if request.method == "POST":
        form = ForecastDaysForm()
        if form.validate_on_submit():
            forecast_days = int(form.forecast_days.data)
    else:
        forecast_days = int(request.args.get("days", DEFAULT_FORECAST_DAYS))

    try:
        formatted_forecast = get_forecast_data(coords, unit, weather_api)
        # ADDED: Get location data just like the weather route does
        _, location = get_weather_data(coords, unit, weather_api)
    except (ConnectionError, TimeoutError) as e:
        flash(f"Weather service connection error: {str(e)}", "error")
        return redirect(url_for("index"))
    except ValueError as e:
        flash(f"Invalid forecast data received: {str(e)}", "error")
        return redirect(url_for("index"))
    except KeyError as e:
        flash(f"Forecast data format error: missing {str(e)}", "error")
        return redirect(url_for("index"))

    return render_template(
        "forecast.html",
        forecast=formatted_forecast,
        location=location,  # ADDED: Pass location object to template
        unit=unit,
        lat=lat,
        lon=lon,
        forecast_days=forecast_days,
    )


@app.route("/forecast", methods=["POST"])
def forecast_form() -> Any:
    """Process forecast form and redirect to forecast page."""
    form = ForecastDaysForm()
    lat = request.form.get("lat")
    lon = request.form.get("lon")
    unit = request.form.get("unit", DEFAULT_TEMP_UNIT).upper()

    if lat and lon:
        if form.validate_on_submit():
            forecast_days = form.forecast_days.data
            return redirect(
                url_for(
                    "forecast_path",
                    coordinates=f"{lat}/{lon}",
                    unit=unit,
                    days=forecast_days,
                )
            )
        flash("Invalid forecast days selection", "error")
        return redirect(url_for("weather_path", coordinates=f"{lat}/{lon}", unit=unit))

    location = request.form.get("location")
    if location:
        # Disambiguate location before searching
        location = Helpers.disambiguate_location(location)

        try:
            results = weather_api.search_city(location)
        except (ConnectionError, TimeoutError) as e:
            flash(f"Weather service connection error: {str(e)}", "error")
            return redirect(url_for("index"))
        except ValueError as e:
            flash(f"Invalid location format: {str(e)}", "error")
            return redirect(url_for("index"))

        if not results:
            flash(f"No cities found matching '{location}'", "warning")
            return redirect(url_for("index"))

        if len(results) == 1 and form.validate_on_submit():
            forecast_days = form.forecast_days.data
            return redirect(
                url_for(
                    "forecast_path",
                    coordinates=f"{results[0]['lat']}/{results[0]['lon']}",
                    unit=unit,
                    days=forecast_days,
                )
            )

        # Multiple results - show selection page
        forecast_days = (
            form.forecast_days.data
            if form.validate_on_submit()
            else DEFAULT_FORECAST_DAYS
        )
        return render_template(
            "location_selection.html",
            results=results,
            query=location,
            unit=unit,
            action="forecast",
            forecast_days=forecast_days,
        )

    flash("Please provide location coordinates or location name", "error")
    return redirect(url_for("index"))


@app.route("/forecast/<path:coordinates>", methods=["GET", "POST"])
def forecast_path(coordinates: str) -> Any:
    """Handle forecast path with coordinates that may include negative values."""
    try:
        lat, lon = Helpers.parse_coordinates_from_path(coordinates)
        return forecast(lat, lon)
    except ValueError:
        flash("Invalid coordinates format", "error")
        return redirect(url_for("index"))
    except Exception as e:
        flash(f"Error getting forecast: {e}", "error")
        return redirect(url_for("index"))


@app.route("/nl-date-weather", methods=["POST"])
def nl_date_weather() -> Any:
    """Handle natural language weather queries."""
    app.logger.debug("Processing natural language weather query")
    query = request.form.get("query", "").strip()
    unit = Helpers.get_normalized_unit()
    app.logger.debug(f"NL Query: {query}, Unit: {unit}")

    # Extract location using multiple regex patterns with exception handling
    try:
        location_name = extract_location_from_query(query)
        app.logger.debug(f"Extracted location: {location_name}")
    except ValueError:
        app.logger.warning(f"Could not extract location from query: {query}")
        flash(
            "Could not find a location in your query. "
            "Please include a location (e.g., 'Portland weather tomorrow', "
            "'Weather for Portland', or 'What's the weather like in Portland?')",
            "error",
        )
        return redirect(url_for("index"))
    except (re.error, AttributeError) as e:
        app.logger.error(f"Error parsing query format: {e}", exc_info=True)
        flash(f"Error parsing query format: {str(e)}", "error")
        return redirect(url_for("index"))

    # Search for the location and get all possible matches
    result = handle_location_search(location_name, unit, "nl")
    if isinstance(result, tuple):
        results, _ = result
        app.logger.debug(f"Showing selection page for {len(results)} results")
        # Show selection page for multiple results
        return render_template(
            "location_selection.html",
            results=results,
            query=location_name,
            unit=unit,
            action="nl",
            nl_query=query,  # Pass the original NL query
        )
    return result  # This is a redirect response


@app.route("/nl-result/<path:coordinates>")
def nl_result_with_coords(coordinates: str) -> Any:
    """Handle natural language weather results with selected coordinates."""
    try:
        # Parse coordinates from path
        lat, lon = Helpers.parse_coordinates_from_path(coordinates)
        query = request.args.get("query", "")
        unit = request.args.get("unit", DEFAULT_TEMP_UNIT).upper()
        coords = (lat, lon)

        app.logger.debug(f"Processing NL result for coordinates: {coords}")
        app.logger.debug(f"Original query: '{query}'")
        app.logger.debug(f"Unit: '{unit}'")

        # Validate location before proceeding
        success, error_msg = safe_location_lookup(coords, weather_api)
        if not success:
            app.logger.error(f"Location validation failed: {error_msg}")
            flash(f"Invalid location: {error_msg}", "error")
            return redirect(url_for("index"))

        # Get weather data
        current_weather_data, location_obj = get_weather_data(coords, unit, weather_api)
        app.logger.debug(f"Got current weather for {location_obj.name}")

        forecast_data = get_forecast_data(coords, unit, weather_api)
        app.logger.debug(f"Got forecast data with {len(forecast_data)} days")

        # Save weather record (non-critical operation)
        try:
            Helpers.save_weather_record(location_obj, current_weather_data)
            app.logger.debug("Saved weather record")
        except Exception as e:
            app.logger.warning(f"Failed to save weather record: {e}")

        # Get target dates based on the query and filter forecast
        target_dates = Helpers.get_date_range_for_query(query)
        app.logger.debug(f"Target dates: {target_dates}")

        filtered_forecast = Helpers.filter_forecast_by_dates(
            forecast_data, target_dates
        )
        app.logger.debug(f"Filtered forecast to {len(filtered_forecast)} days")

        # Convert dates to datetime objects for the template
        dates = [
            datetime.strptime(day["date"], "%Y-%m-%d") for day in filtered_forecast
        ]

        return render_template(
            "results_date_weather.html",
            current_weather=current_weather_data,
            forecast_data=filtered_forecast,
            dates=dates,
            location=location_obj,
            unit=unit,
            lat=lat,
            lon=lon,
            query=query,
        )

    except ValueError as e:
        app.logger.error(f"Value error in weather processing: {e}", exc_info=True)
        flash(str(e), "error")
        return redirect(url_for("index"))
    except (ConnectionError, TimeoutError) as e:
        app.logger.error(f"Weather service connection error: {e}", exc_info=True)
        flash(f"Weather service connection error: {str(e)}", "error")
        return redirect(url_for("index"))
    except Exception as e:
        app.logger.error(f"Unexpected error in weather processing: {e}", exc_info=True)
        flash("An unexpected error occurred processing your request.", "error")
        return redirect(url_for("index"))


@app.route("/disambiguate-location", methods=["GET", "POST"])
def disambiguate_location() -> Any:
    """Handle cases where location disambiguation needs user input."""
    form = LocationDisambiguationForm()

    if request.method == "GET":
        query = request.args.get("query", "")
        unit = request.args.get("unit", DEFAULT_TEMP_UNIT)
        action = request.args.get("action", "weather")

        result = handle_location_search(query, unit, action)
        if isinstance(result, tuple):
            results, _ = result
            # Create choices for the form
            choices = [
                (
                    f"{r['name']}, {r.get('region', '')}, {r['country']}",
                    f"{r['name']}, {r.get('region', '')}, {r['country']}",
                    f"({r['lat']}, {r['lon']})",
                )
                for r in results
            ]
            form.selected_location.choices = choices
            form.original_query.data = query
            form.unit.data = unit
            form.action.data = action

            return render_template("disambiguate_location.html", form=form, query=query)
        return result  # This is a redirect response

    # POST request - process the disambiguation
    if form.validate_on_submit():
        selected_location = form.selected_location.data
        unit = form.unit.data
        action = form.action.data
        nl_query = form.original_query.data if action == "nl" else None

        # Use the helper function for the selected location
        result = handle_location_search(selected_location, unit, action)
        if isinstance(result, tuple):
            results, _ = result
            # Show selection page for multiple results
            return render_template(
                "location_selection.html",
                results=results,
                query=selected_location,
                unit=unit,
                action=action,
                nl_query=nl_query,
            )
        return result  # This is a redirect response

    # Form validation failed
    flash("Please select a location option.", "error")
    return redirect(url_for("index"))


# Run the app
def run() -> None:
    """Run the Flask application."""
    app.logger.info(f"Starting Weather Dashboard on port {PORT}")
    app.run(debug=True, host="0.0.0.0", port=PORT)


if __name__ == "__main__":
    run()
