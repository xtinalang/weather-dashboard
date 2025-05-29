import os
import re
from datetime import datetime, timedelta
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
from weather_app.weather_types import LocationData, TemperatureUnit, WeatherData

from .error_handlers import (
    initialize_components_safely,
    initialize_database_safely,
    logger,
    register_error_handlers,
    safe_api_operation,
    safe_database_operation,
    safe_float_conversion,
    validate_coordinates,
    validate_query_string,
)
from .forms import (
    DateWeatherNLForm,
    ForecastDaysForm,
    LocationSearchForm,
    UnitSelectionForm,
    UserInputLocationForm,
)
from .helpers import WEEKDAY_NAMES, WEEKDAY_TO_NUMBER, Helpers
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
        default=config("APP_PORT", default=os.environ.get("FLASK_PORT", 5050)),
        cast=int,
    ),
    cast=int,
)

# Initialize Flask app
app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key")
csrf = CSRFProtect(app)

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


# Helper functions for route handlers
def get_weather_data(
    coords: tuple[float, float], unit: TemperatureUnit
) -> tuple[WeatherData, LocationData]:
    """Get weather data for given coordinates."""
    weather_data = weather_api.get_weather(coords)
    if not weather_data:
        raise ValueError("Failed to get weather data")

    location_obj, _ = Helpers.get_location_by_coordinates(coords[0], coords[1])
    location_obj = Helpers.update_location_from_api_data(location_obj, weather_data)

    # Format the weather data
    formatted_data = {
        "current": {
            "temp_c": weather_data["current"]["temp_c"],
            "temp_f": weather_data["current"]["temp_f"],
            "feelslike_c": weather_data["current"]["feelslike_c"],
            "feelslike_f": weather_data["current"]["feelslike_f"],
            "humidity": weather_data["current"]["humidity"],
            "condition": weather_data["current"]["condition"],
            "wind_kph": weather_data["current"]["wind_kph"],
            "wind_mph": weather_data["current"]["wind_mph"],
            "wind_dir": weather_data["current"]["wind_dir"],
            "pressure_mb": weather_data["current"]["pressure_mb"],
            "precip_mm": weather_data["current"]["precip_mm"],
            "uv": weather_data["current"]["uv"],
            "last_updated": weather_data["current"]["last_updated"],
        }
    }

    return formatted_data, location_obj


def get_forecast_data(
    coords: tuple[float, float], unit: TemperatureUnit
) -> list[dict[str, Any]]:
    """Get forecast data for given coordinates."""
    forecast_data = weather_api.get_forecast(coords)
    if not forecast_data:
        raise ValueError("Failed to get forecast data")

    # Format the forecast data
    formatted_forecast = []
    for day in forecast_data["forecast"]["forecastday"]:
        formatted_day = {
            "date": day["date"],
            "max_temp": (
                day["day"]["maxtemp_c"] if unit == CELSIUS else day["day"]["maxtemp_f"]
            ),
            "min_temp": (
                day["day"]["mintemp_c"] if unit == CELSIUS else day["day"]["mintemp_f"]
            ),
            "condition": day["day"]["condition"]["text"],
            "icon": day["day"]["condition"]["icon"],
            "chance_of_rain": day["day"]["daily_chance_of_rain"],
            "chance_of_snow": day["day"]["daily_chance_of_snow"],
            "maxwind_kph": day["day"]["maxwind_kph"],
            "maxwind_mph": day["day"]["maxwind_mph"],
            "wind_speed": day["day"]["maxwind_kph"]
            if unit == CELSIUS
            else day["day"]["maxwind_mph"],
            "wind_unit": "km/h" if unit == CELSIUS else "mph",
            "humidity": day["day"]["avghumidity"],
            "totalprecip_mm": day["day"]["totalprecip_mm"],
            "totalprecip_in": day["day"]["totalprecip_in"],
            "avghumidity": day["day"]["avghumidity"],
            "uv": day["day"]["uv"],
        }
        formatted_forecast.append(formatted_day)

    return formatted_forecast


# Routes
@app.route("/")
def index() -> str:
    """Home page with search form."""
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
            unit_form.unit.default = (
                "F" if settings.temperature_unit.lower() == "fahrenheit" else "C"
            )
            forecast_days_form.forecast_days.default = str(settings.forecast_days)
            unit_form.process()
            forecast_days_form.process()
    except (AttributeError, ValueError) as e:
        # Settings data format issues
        logger.warning(f"Settings data format issue: {e}")
    except Exception as e:
        # Other settings-related errors
        logger.error(f"Error loading settings: {e}")

    # Get favorite locations for quick access
    favorites = []
    if location_repo:
        favorites = safe_database_operation(location_repo.get_favorites)
        if favorites is None:
            favorites = []

    return render_template(
        "index.html",
        search_form=search_form,
        ui_form=ui_form,
        unit_form=unit_form,
        forecast_days_form=forecast_days_form,
        nl_form=nl_form,
        favorites=favorites,
    )


@app.route("/search", methods=["POST"])
def search() -> Any:
    """Search for locations."""
    form = LocationSearchForm()
    unit = cast(TemperatureUnit, request.form.get("unit", DEFAULT_TEMP_UNIT).upper())
    forecast_days = request.form.get("forecast_days")

    # Determine action based on which form was submitted
    action = "weather"  # default
    if "forecast_days" in request.form and request.form.get("forecast_days"):
        action = "forecast"

    if not form.validate_on_submit():
        logger.warning("Search form validation failed")
        flash("Please enter a valid search query.", "warning")
        return redirect(url_for("index"))

    query = form.query.data

    # Validate query input
    if not validate_query_string(query):
        flash("Invalid search query. Please check your input.", "warning")
        return redirect(url_for("index"))

    # Use safe API operation
    results = safe_api_operation(weather_api.search_city, query)
    if results is None:
        return redirect(url_for("index"))

    if not results:
        flash(f"No cities found matching '{query}'", "warning")
        return redirect(url_for("index"))

    if len(results) == 1:
        # Single result - redirect directly
        if action == "forecast":
            return redirect(
                url_for(
                    "forecast",
                    lat=results[0]["lat"],
                    lon=results[0]["lon"],
                    unit=unit,
                    days=forecast_days,
                )
            )
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
        query=query,
        unit=unit,
        action=action,
        forecast_days=forecast_days,
    )


@app.route("/select-location", methods=["POST"])
def select_location() -> Any:
    """Handle location selection from search results."""
    # Get form data directly since we're using custom HTML radio buttons
    selected_data = request.form.get("selected_location")

    if not selected_data:
        logger.warning("No location selected in form submission")
        flash("Please select a location", "error")
        return redirect(url_for("index"))

    # Parse the selected location data
    try:
        # Expected format: "lat,lon,name,region,country"
        parts = selected_data.split(",", 4)
        if len(parts) != 5:
            raise ValueError("Invalid location data format")

        lat, lon, name, region, country = parts
        lat, lon = safe_float_conversion(lat), safe_float_conversion(lon)

        # Validate coordinates
        if not validate_coordinates(lat, lon):
            raise ValueError("Invalid coordinates")

    except (ValueError, TypeError) as e:
        logger.error(f"Invalid location selection data: {selected_data}, error: {e}")
        flash("Invalid location selection", "error")
        return redirect(url_for("index"))

    action = request.form.get("action", "weather")
    unit = request.form.get("unit", DEFAULT_TEMP_UNIT)
    forecast_days = request.form.get("forecast_days")

    logger.info(
        f"Location selected: {name}, {region}, {country} "
        f"({lat}, {lon}) for action: {action}"
    )

    # Redirect based on action
    if action == "forecast":
        return redirect(
            url_for(
                "forecast",
                lat=lat,
                lon=lon,
                unit=unit,
                days=forecast_days,
            )
        )
    elif action == "nl":
        # For natural language queries, we need to process the original query
        # with the selected coordinates
        nl_query = request.form.get("nl_query", "")
        if nl_query:
            # Store the coordinates in session or pass as parameters
            # For simplicity, we'll redirect to a special NL result route
            return redirect(
                url_for(
                    "nl_result_with_coords",
                    lat=lat,
                    lon=lon,
                    query=nl_query,
                    unit=unit,
                )
            )
        else:
            # Fallback to regular weather
            return redirect(
                url_for(
                    "weather",
                    lat=lat,
                    lon=lon,
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
        weather_data, location = get_weather_data(coords, unit)
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
        weather_data, _ = get_weather_data(coords, unit)
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
        formatted_forecast = get_forecast_data(coords, unit)
        # ADDED: Get location data just like the weather route does
        _, location = get_weather_data(coords, unit)
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
    query = request.form.get("query", "").strip()
    unit = Helpers.get_normalized_unit()

    # Extract location using regex
    try:
        location_match = re.search(
            r"(?:in|for)\s+([A-Za-z\s,]+?)(?:\s+(?:on|at|for|,)|$)",
            query,
            re.IGNORECASE,
        )
        if not location_match:
            flash(
                "Could not find a location in your query. "
                "Please include a location (e.g., 'in London')",
                "error",
            )
            return redirect(url_for("index"))

        location_name = location_match.group(1).strip()
    except (re.error, AttributeError) as e:
        flash(f"Error parsing query format: {str(e)}", "error")
        return redirect(url_for("index"))

    # Try direct API search first
    coords = None
    multiple_results = None
    try:
        results = weather_api.search_city(location_name)

        if results and len(results) > 0:
            if len(results) == 1:
                # Single result - proceed with existing logic
                first_result = results[0]
                try:
                    lat = float(first_result.get("lat", 0))
                    lon = float(first_result.get("lon", 0))
                    if lat == 0 or lon == 0:
                        raise ValueError("Invalid coordinates")
                    coords = (lat, lon)
                except (ValueError, TypeError):
                    coords = None
            else:
                # Multiple results - let user choose
                multiple_results = results
        else:
            location_name = Helpers.normalize_location_input(location_name)
            coords = location_manager.get_coordinates(location_name)
    except (ConnectionError, TimeoutError):
        location_name = Helpers.normalize_location_input(location_name)
        coords = location_manager.get_coordinates(location_name)
    except Exception:
        location_name = Helpers.normalize_location_input(location_name)
        coords = location_manager.get_coordinates(location_name)

    # If we have multiple results, show selection page
    if multiple_results:
        return render_template(
            "location_selection.html",
            results=multiple_results,
            query=location_name,
            unit=unit,
            action="nl",
            nl_query=query,  # Pass the original NL query
        )

    if not coords:
        flash(f"Could not find location: {location_name}", "error")
        return redirect(url_for("index"))

    # Get current weather and forecast data
    try:
        current_weather_data, location_obj = get_weather_data(coords, unit)
        forecast_data = get_forecast_data(coords, unit)
    except (ConnectionError, TimeoutError) as e:
        flash(f"Weather service connection error: {str(e)}", "error")
        return redirect(url_for("index"))
    except ValueError as e:
        flash(f"Invalid weather data received: {str(e)}", "error")
        return redirect(url_for("index"))
    except KeyError as e:
        flash(f"Weather data format error: missing {str(e)}", "error")
        return redirect(url_for("index"))

    try:
        Helpers.save_weather_record(location_obj, current_weather_data)
    except OSError:
        # Non-critical error - just log it
        pass
    except Exception:
        # Non-critical error - don't fail the request
        pass

    # Enhanced natural language date parsing
    query_lower = query.lower()
    filtered_forecast = []
    today = datetime.now().date()

    # Helper function to get date range for filtering
    def get_date_range_for_query(query_text: str, today_date):
        """Parse natural language date queries and return date range."""
        target_dates = []

        # Tomorrow
        if "tomorrow" in query_text:
            tomorrow = today_date + timedelta(days=1)
            target_dates = [tomorrow]

        # This weekend (upcoming Saturday and Sunday)
        elif "this weekend" in query_text:
            days_until_saturday = (5 - today_date.weekday()) % 7
            if (
                days_until_saturday == 0 and today_date.weekday() == 5
            ):  # Today is Saturday
                saturday = today_date
            else:
                saturday = today_date + timedelta(days=days_until_saturday)
            sunday = saturday + timedelta(days=1)
            target_dates = [saturday, sunday]

        # Next weekend
        elif "next weekend" in query_text:
            days_until_next_saturday = ((5 - today_date.weekday()) % 7) + 7
            saturday = today_date + timedelta(days=days_until_next_saturday)
            sunday = saturday + timedelta(days=1)
            target_dates = [saturday, sunday]

        # This week (Monday to Sunday of current week)
        elif "this week" in query_text:
            days_since_monday = today_date.weekday()
            monday = today_date - timedelta(days=days_since_monday)
            target_dates = [monday + timedelta(days=i) for i in range(7)]

        # Next week (Monday to Sunday of next week)
        elif "next week" in query_text:
            days_since_monday = today_date.weekday()
            next_monday = today_date + timedelta(days=(7 - days_since_monday))
            target_dates = [next_monday + timedelta(days=i) for i in range(7)]

        # Specific weekdays
        elif any(day in query_text for day in WEEKDAY_NAMES):
            for day_name, day_num in WEEKDAY_TO_NUMBER.items():
                if day_name in query_text:
                    days_ahead = (day_num - today_date.weekday()) % 7
                    if days_ahead == 0:  # Today is the requested day
                        if "next" in query_text:
                            days_ahead = 7  # Next occurrence
                        else:
                            days_ahead = 0  # Today
                    target_date = today_date + timedelta(days=days_ahead)
                    target_dates = [target_date]
                    break

        # General weekend (any weekend days in forecast)
        elif (
            "weekend" in query_text
            and "this" not in query_text
            and "next" not in query_text
        ):
            # Find all weekend days in the forecast period
            for i in range(7):  # Check next 7 days
                check_date = today_date + timedelta(days=i)
                if check_date.weekday() >= 5:  # Saturday (5) or Sunday (6)
                    target_dates.append(check_date)

        return target_dates

    # Get target dates based on the query
    target_dates = get_date_range_for_query(query_lower, today)

    if target_dates:
        # Filter forecast data for target dates
        try:
            for day in forecast_data:
                day_date = datetime.strptime(day["date"], "%Y-%m-%d").date()
                if day_date in target_dates:
                    filtered_forecast.append(day)

            if filtered_forecast:
                forecast_data = filtered_forecast
        except (ValueError, KeyError):
            # Continue with original forecast data
            pass
        except Exception:
            # Continue with original forecast data
            pass

    # Ensure we have valid coordinates for the template
    lat, lon = coords
    if not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)):
        flash("Invalid coordinates format", "error")
        return redirect(url_for("index"))

    # Convert dates to datetime objects for the template
    try:
        dates = [datetime.strptime(day["date"], "%Y-%m-%d") for day in forecast_data]
    except (ValueError, KeyError) as e:
        flash(f"Error processing forecast dates: {str(e)}", "error")
        return redirect(url_for("index"))

    try:
        return render_template(
            "results_date_weather.html",
            current_weather=current_weather_data,
            forecast_data=forecast_data,
            dates=dates,
            location=location_obj,
            unit=unit,
            lat=lat,
            lon=lon,
        )
    except Exception as e:
        flash(f"Error displaying weather results: {str(e)}", "error")
        return redirect(url_for("index"))


@app.route("/nl-result/<float:lat>/<float:lon>")
def nl_result_with_coords(lat: float, lon: float) -> Any:
    """Handle natural language weather results with selected coordinates."""
    query = request.args.get("query", "")
    unit = request.args.get("unit", DEFAULT_TEMP_UNIT).upper()
    coords = (lat, lon)

    if not query:
        flash("No query provided", "error")
        return redirect(url_for("index"))

    # Get current weather and forecast data
    try:
        current_weather_data, location_obj = get_weather_data(coords, unit)
        forecast_data = get_forecast_data(coords, unit)
    except (ConnectionError, TimeoutError) as e:
        flash(f"Weather service connection error: {str(e)}", "error")
        return redirect(url_for("index"))
    except ValueError as e:
        flash(f"Invalid weather data received: {str(e)}", "error")
        return redirect(url_for("index"))
    except KeyError as e:
        flash(f"Weather data format error: missing {str(e)}", "error")
        return redirect(url_for("index"))

    try:
        Helpers.save_weather_record(location_obj, current_weather_data)
    except OSError:
        # Non-critical error - just log it
        pass
    except Exception:
        # Non-critical error - don't fail the request
        pass

    # Enhanced natural language date parsing (same logic as in nl_date_weather)
    query_lower = query.lower()
    filtered_forecast = []
    today = datetime.now().date()

    # Helper function to get date range for filtering
    def get_date_range_for_query(query_text: str, today_date):
        """Parse natural language date queries and return date range."""
        target_dates = []

        # Tomorrow
        if "tomorrow" in query_text:
            tomorrow = today_date + timedelta(days=1)
            target_dates = [tomorrow]

        # This weekend (upcoming Saturday and Sunday)
        elif "this weekend" in query_text:
            days_until_saturday = (5 - today_date.weekday()) % 7
            if (
                days_until_saturday == 0 and today_date.weekday() == 5
            ):  # Today is Saturday
                saturday = today_date
            else:
                saturday = today_date + timedelta(days=days_until_saturday)
            sunday = saturday + timedelta(days=1)
            target_dates = [saturday, sunday]

        # Next weekend
        elif "next weekend" in query_text:
            days_until_next_saturday = ((5 - today_date.weekday()) % 7) + 7
            saturday = today_date + timedelta(days=days_until_next_saturday)
            sunday = saturday + timedelta(days=1)
            target_dates = [saturday, sunday]

        # This week (Monday to Sunday of current week)
        elif "this week" in query_text:
            days_since_monday = today_date.weekday()
            monday = today_date - timedelta(days=days_since_monday)
            target_dates = [monday + timedelta(days=i) for i in range(7)]

        # Next week (Monday to Sunday of next week)
        elif "next week" in query_text:
            days_since_monday = today_date.weekday()
            next_monday = today_date + timedelta(days=(7 - days_since_monday))
            target_dates = [next_monday + timedelta(days=i) for i in range(7)]

        # Specific weekdays
        elif any(day in query_text for day in WEEKDAY_NAMES):
            for day_name, day_num in WEEKDAY_TO_NUMBER.items():
                if day_name in query_text:
                    days_ahead = (day_num - today_date.weekday()) % 7
                    if days_ahead == 0:  # Today is the requested day
                        if "next" in query_text:
                            days_ahead = 7  # Next occurrence
                        else:
                            days_ahead = 0  # Today
                    target_date = today_date + timedelta(days=days_ahead)
                    target_dates = [target_date]
                    break

        # General weekend (any weekend days in forecast)
        elif (
            "weekend" in query_text
            and "this" not in query_text
            and "next" not in query_text
        ):
            # Find all weekend days in the forecast period
            for i in range(7):  # Check next 7 days
                check_date = today_date + timedelta(days=i)
                if check_date.weekday() >= 5:  # Saturday (5) or Sunday (6)
                    target_dates.append(check_date)

        return target_dates

    # Get target dates based on the query
    target_dates = get_date_range_for_query(query_lower, today)

    if target_dates:
        # Filter forecast data for target dates
        try:
            for day in forecast_data:
                day_date = datetime.strptime(day["date"], "%Y-%m-%d").date()
                if day_date in target_dates:
                    filtered_forecast.append(day)

            if filtered_forecast:
                forecast_data = filtered_forecast
        except (ValueError, KeyError):
            # Continue with original forecast data
            pass
        except Exception:
            # Continue with original forecast data
            pass

    # Convert dates to datetime objects for the template
    try:
        dates = [datetime.strptime(day["date"], "%Y-%m-%d") for day in forecast_data]
    except (ValueError, KeyError) as e:
        flash(f"Error processing forecast dates: {str(e)}", "error")
        return redirect(url_for("index"))

    try:
        return render_template(
            "results_date_weather.html",
            current_weather=current_weather_data,
            forecast_data=forecast_data,
            dates=dates,
            location=location_obj,
            unit=unit,
            lat=lat,
            lon=lon,
            query=query,
        )
    except Exception as e:
        flash(f"Error rendering weather data: {str(e)}", "error")
        return redirect(url_for("index"))


# Run the app
def run() -> None:
    """Run the Flask application."""
    app.run(debug=True, host="0.0.0.0", port=PORT)


if __name__ == "__main__":
    run()
