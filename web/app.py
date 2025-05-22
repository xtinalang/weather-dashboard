import os
import re
import time
from datetime import datetime

from dateutil import parser as date_parser
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

from .forms import (
    ForecastDaysForm,
    LocationSearchForm,
    UnitSelectionForm,
    UserInputLocationForm,
)
from .helpers import DEFAULT_FORECAST_DAYS, DEFAULT_TEMP_UNIT, Helpers
from .utils import format_weather_data

# Configure port from environment variables with fallbacks
# Try different possible environment variable names in order of preference
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

# Initialize database
try:
    initialize_database()
except Exception as e:
    print(f"Warning: Failed to initialize database: {e}")

# Initialize API and components
weather_api = WeatherAPI()
display = WeatherDisplay()
location_manager = LocationManager(weather_api, display)
location_repo = LocationRepository()
forecast_manager = ForecastManager(weather_api, display)
current_manager = CurrentWeatherManager(weather_api, display)
settings_repo = SettingsRepository()


# Context processor to add current year to all templates
@app.context_processor
def inject_current_year():
    return {"current_year": datetime.now().year}


# Routes
@app.route("/")
def index():
    """Home page with search form"""
    search_form = LocationSearchForm()
    ui_form = UserInputLocationForm()
    unit_form = UnitSelectionForm()
    forecast_days_form = ForecastDaysForm()

    # Default to user's saved setting if available
    try:
        settings = settings_repo.get_settings()
        unit_form.unit.default = (
            "F" if settings.temperature_unit.lower() == "fahrenheit" else "C"
        )
        forecast_days_form.forecast_days.default = str(settings.forecast_days)
        unit_form.process()
        forecast_days_form.process()
    except Exception:
        pass

    # Get favorite locations for quick access
    favorites = []
    try:
        favorites = location_repo.get_favorites()
    except Exception as e:
        flash(f"Error loading favorite locations: {e}", "error")

    return render_template(
        "index.html",
        search_form=search_form,
        ui_form=ui_form,
        unit_form=unit_form,
        forecast_days_form=forecast_days_form,
        favorites=favorites,
    )


@app.route("/search", methods=["POST"])
def search():
    """Search for locations"""
    form = LocationSearchForm()
    unit = request.form.get("unit", DEFAULT_TEMP_UNIT).upper()

    if form.validate_on_submit():
        query = form.query.data
        return Helpers.search_location_and_handle_results(query, unit)

    return redirect(url_for("index"))


@app.route("/weather/<path:coordinates>")
def weather_path(coordinates):
    """
    Handle weather path with coordinates that may include negative values.
    This is a workaround for Flask's router which can have issues with negative numbers.
    """
    try:
        lat, lon = Helpers.parse_coordinates_from_path(coordinates)
        return weather(lat, lon)
    except ValueError:
        flash("Invalid coordinates format", "error")
        return redirect(url_for("index"))
    except Exception as e:
        flash(f"Error getting weather: {e}", "error")
        return redirect(url_for("index"))


@app.route("/weather/<float:lat>/<float:lon>")
def weather(lat, lon):
    """Show weather for a location by coordinates"""
    unit = Helpers.get_normalized_unit()

    try:
        # Find or create location and get coordinates string
        location, coords = Helpers.get_location_by_coordinates(lat, lon)

        # Get weather data
        weather_data = weather_api.get_weather(coords)
        if not weather_data:
            flash("Failed to get weather data", "error")
            return redirect(url_for("index"))

        # Update location from API data
        location = Helpers.update_location_from_api_data(location, weather_data)

        # Format data for template
        formatted_data = format_weather_data(weather_data, unit)

        # Save record to database
        Helpers.save_weather_record(location, weather_data)

        return render_template(
            "weather.html",
            weather=formatted_data,
            location=location,
            unit=unit,
            lat=lat,
            lon=lon,
        )

    except Exception as e:
        flash(f"Error getting weather: {e}", "error")
        return redirect(url_for("index"))


@app.route("/ui", methods=["POST"])
def ui_location():
    """Handle UI location entry"""
    form = UserInputLocationForm()

    # Get location from form or direct hidden input field
    location = None
    unit = request.form.get("unit", DEFAULT_TEMP_UNIT).upper()

    if "location" in request.form:
        location = request.form.get("location")
    elif form.validate_on_submit():
        location = form.location.data

    if not location:
        flash("Please enter a valid location", "error")
        return redirect(url_for("index"))

    return Helpers.search_location_and_handle_results(location, unit)


@app.route("/favorite/<int:location_id>", methods=["POST"])
def toggle_favorite(location_id):
    """Toggle favorite status for a location"""
    try:
        success = location_manager.toggle_favorite(location_id)
        if success:
            flash("Favorite status updated", "success")
        else:
            flash("Failed to update favorite status", "error")
    except Exception as e:
        flash(f"Error updating favorite status: {e}", "error")

    # Return to previous page or index
    next_page = request.args.get("next") or url_for("index")
    return redirect(next_page)


@app.route("/unit", methods=["POST"])
def update_unit():
    """Update temperature unit preference"""
    form = UnitSelectionForm()
    if form.validate_on_submit():
        unit = form.unit.data.upper()
        if unit in ["C", "F"]:
            try:
                # Update in database
                unit_value = "celsius" if unit == "C" else "fahrenheit"
                settings_repo.update_temperature_unit(unit_value)
                flash(f"Temperature unit updated to {unit_value}", "success")
            except Exception as e:
                flash(f"Failed to update unit preference: {e}", "warning")

    return redirect(url_for("index"))


@app.route("/api/weather/<float:lat>/<float:lon>")
def api_weather(lat, lon):
    """API endpoint for weather data"""
    unit = Helpers.get_normalized_unit()

    try:
        _, coords = Helpers.get_location_by_coordinates(lat, lon)
        weather_data = weather_api.get_weather(coords)

        if not weather_data:
            return jsonify({"error": "Failed to get weather data"}), 404

        formatted_data = format_weather_data(weather_data, unit)
        return jsonify(formatted_data)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/forecast/<float:lat>/<float:lon>", methods=["GET", "POST"])
def forecast(lat, lon):
    """Show forecast for a location"""
    unit = Helpers.get_normalized_unit()

    # Get forecast days from form or default to 7
    forecast_days = DEFAULT_FORECAST_DAYS
    if request.method == "POST":
        form = ForecastDaysForm()
        if form.validate_on_submit():
            forecast_days = int(form.forecast_days.data)
    else:
        forecast_days = int(request.args.get("days", DEFAULT_FORECAST_DAYS))

    try:
        # Find or get location
        location, coords = Helpers.get_location_by_coordinates(lat, lon)

        # Get forecast data
        forecast_data = weather_api.get_forecast(coords, days=forecast_days)

        if not forecast_data:
            flash("Failed to get forecast data", "error")
            return redirect(url_for("index"))

        # Update location name from API data if it was auto-created
        location = Helpers.update_location_from_api_data(location, forecast_data)

        # Format data for template
        formatted_forecast = []
        if "forecast" in forecast_data and "forecastday" in forecast_data["forecast"]:
            for day in forecast_data["forecast"]["forecastday"]:
                formatted_day = {
                    "date": day["date"],
                    "max_temp": day["day"]["maxtemp_c"]
                    if unit == "C"
                    else day["day"]["maxtemp_f"],
                    "min_temp": day["day"]["mintemp_c"]
                    if unit == "C"
                    else day["day"]["mintemp_f"],
                    "condition": day["day"]["condition"]["text"],
                    "icon": day["day"]["condition"]["icon"],
                    "chance_of_rain": day["day"]["daily_chance_of_rain"],
                    "chance_of_snow": day["day"]["daily_chance_of_snow"],
                    "humidity": day["day"]["avghumidity"],
                    "wind_speed": day["day"]["maxwind_kph"]
                    if unit == "C"
                    else day["day"]["maxwind_mph"],
                    "wind_unit": "km/h" if unit == "C" else "mph",
                }
                formatted_forecast.append(formatted_day)

        # Render forecast template
        return render_template(
            "forecast.html",
            forecast=formatted_forecast,
            location=location,
            unit=unit,
            lat=lat,
            lon=lon,
            forecast_days=forecast_days,
        )

    except Exception as e:
        flash(f"Error getting forecast: {e}", "error")
        return redirect(url_for("index"))


@app.route("/forecast", methods=["POST"])
def forecast_form():
    """Process forecast form and redirect to forecast page"""
    form = ForecastDaysForm()
    lat = request.form.get("lat")
    lon = request.form.get("lon")
    unit = request.form.get("unit", DEFAULT_TEMP_UNIT).upper()

    # If the request is coming from weather.html, it should have lat/lon
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
        else:
            flash("Invalid forecast days selection", "error")
            return redirect(
                url_for("weather_path", coordinates=f"{lat}/{lon}", unit=unit)
            )

    # If the request is coming from index.html, it may have a location name to search
    location = request.form.get("location")
    if location:
        try:
            # Search for the location
            results = weather_api.search_city(location)
            if not results or len(results) == 0:
                flash(f"No cities found matching '{location}'", "warning")
                return redirect(url_for("index"))

            # If only one result, go directly to forecast
            if len(results) == 1 and form.validate_on_submit():
                forecast_days = form.forecast_days.data
                lat = results[0]["lat"]
                lon = results[0]["lon"]
                return redirect(
                    url_for(
                        "forecast_path",
                        coordinates=f"{lat}/{lon}",
                        unit=unit,
                        days=forecast_days,
                    )
                )

            # If multiple results, show them
            return render_template(
                "search_results.html", results=results, query=location, unit=unit
            )
        except Exception as e:
            flash(f"Error finding location: {e}", "error")

    # If we get here, the request was invalid
    flash("Missing location information", "error")
    return redirect(url_for("index"))


@app.route("/forecast/<path:coordinates>", methods=["GET", "POST"])
def forecast_path(coordinates):
    """
    Handle forecast path with coordinates that may include negative values.
    This is a workaround for Flask's router which can have issues with negative numbers.
    """
    try:
        lat, lon = Helpers.parse_coordinates_from_path(coordinates)
        return forecast(lat, lon)
    except ValueError:
        flash("Invalid coordinates format", "error")
        return redirect(url_for("index"))
    except Exception as e:
        flash(f"Error getting forecast: {e}", "error")
        return redirect(url_for("index"))


@app.route("/date-weather", methods=["GET", "POST"])
def date_weather():
    """Handle weather queries for specific dates"""
    form = None  # DateWeatherForm()
    unit = Helpers.get_normalized_unit()

    if form.validate_on_submit():
        try:
            # Get location coordinates
            location = form.location.data
            location_name = Helpers.normalize_location_input(location)
            coords = location_manager.get_coordinates(location_name)
            if not coords:
                flash(f"Could not find location: {location}", "error")
                return redirect(url_for("index"))

            # Get weather data
            weather_data = weather_api.get_weather(coords)
            if not weather_data:
                flash("Failed to get weather data", "error")
                return redirect(url_for("index"))

            # Find or create location and update from API data
            location_obj, _ = Helpers.get_location_by_coordinates(coords[0], coords[1])
            location_obj = Helpers.update_location_from_api_data(
                location_obj, weather_data
            )

            # Format data for template
            formatted_data = format_weather_data(weather_data, unit)

            # Save record to database
            Helpers.save_weather_record(location_obj, weather_data)

            return render_template(
                "date_weather.html",
                weather=formatted_data,
                location=location_obj,
                unit=unit,
                date=form.date.data,
                lat=coords[0],
                lon=coords[1],
            )

        except Exception as e:
            flash(f"Error getting weather: {e}", "error")
            return redirect(url_for("index"))

    return render_template("date_weather_form.html", form=form, unit=unit)


@app.route("/nl-date-weather", methods=["POST"])
def nl_date_weather():
    """Handle natural language weather queries"""
    start_time = time.time()  # Start timing
    query = request.form.get("query", "").strip()
    unit = Helpers.get_normalized_unit()

    try:
        # Extract date using dateutil
        date = date_parser.parse(query, fuzzy=True)
        print(f"Date parsing took: {time.time() - start_time:.2f} seconds")

        # Extract location using regex
        location_match = re.search(
            r"(?:in|for)\s+([A-Za-z\s,]+?)(?:\s+(?:on|at|for|,)|$)",
            query,
            re.IGNORECASE,
        )
        if not location_match:
            flash(
                "Could not find a location in your query. Please include a location (e.g., 'in London')",
                "error",
            )
            return redirect(url_for("index"))

        location_name = location_match.group(1).strip()
        print(f"Location extraction took: {time.time() - start_time:.2f} seconds")

        # Try direct API search first
        try:
            api_start = time.time()
            results = weather_api.search_city(location_name)
            print(f"API search took: {time.time() - api_start:.2f} seconds")

            if results and len(results) > 0:
                # Use the first result
                lat = float(results[0]["lat"])
                lon = float(results[0]["lon"])
                coords = (lat, lon)
                print(f"Found coordinates via API: {coords}")
            else:
                # If API search fails, try normalized input
                location_name = Helpers.normalize_location_input(location_name)
                print(f"Trying normalized location: {location_name}")
                coords = location_manager.get_coordinates(location_name)
        except Exception as api_error:
            print(f"API search failed: {api_error}")
            # Fall back to normalized input
            location_name = Helpers.normalize_location_input(location_name)
            coords = location_manager.get_coordinates(location_name)

        if not coords:
            flash(f"Could not find location: {location_name}", "error")
            return redirect(url_for("index"))

        # Get weather data
        weather_start = time.time()
        weather_data = weather_api.get_weather(coords)
        print(f"Weather data fetch took: {time.time() - weather_start:.2f} seconds")

        if not weather_data:
            flash("Failed to get weather data", "error")
            return redirect(url_for("index"))

        # Find or create location and update from API data
        location_obj, _ = Helpers.get_location_by_coordinates(coords[0], coords[1])
        location_obj = Helpers.update_location_from_api_data(location_obj, weather_data)

        # Format data for template
        formatted_data = format_weather_data(weather_data, unit)

        # Save record to database
        Helpers.save_weather_record(location_obj, weather_data)

        print(f"Total request time: {time.time() - start_time:.2f} seconds")

        return render_template(
            "date_weather.html",
            weather=formatted_data,
            location=location_obj,
            unit=unit,
            date=date,
            lat=coords[0],
            lon=coords[1],
        )

    except Exception as e:
        print(f"Error in nl_date_weather: {str(e)}")  # Debug log
        flash(f"Error processing your query: {str(e)}", "error")
        return redirect(url_for("index"))


# Run the app
def run():
    """Run the Flask application"""
    app.run(host="0.0.0.0", port=PORT)


if __name__ == "__main__":
    run()
