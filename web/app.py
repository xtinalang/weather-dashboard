import os
from datetime import datetime

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
    unit = request.form.get("unit", "C").upper()

    if form.validate_on_submit():
        query = form.query.data
        try:
            results = weather_api.search_city(query)
            if not results:
                flash(f"No cities found matching '{query}'", "warning")
                return redirect(url_for("index"))

            return render_template(
                "search_results.html", results=results, query=query, unit=unit
            )
        except Exception as e:
            flash(f"Error searching for location: {e}", "error")
            return redirect(url_for("index"))

    return redirect(url_for("index"))


@app.route("/weather/<path:coordinates>")
def weather_path(coordinates):
    """
    Handle weather path with coordinates that may include negative values.
    This is a workaround for Flask's router which can have issues with negative numbers.
    """
    # Parse coordinates from the path
    try:
        # Split by slash and convert to float
        parts = coordinates.split("/")
        if len(parts) != 2:
            flash("Invalid coordinates format", "error")
            return redirect(url_for("index"))

        lat = float(parts[0])
        lon = float(parts[1])

        # Call the weather function directly
        unit = request.args.get("unit", "C").upper()
        if unit not in ["C", "F"]:
            unit = "C"

        # Find or create location
        location = location_repo.find_or_create_by_coordinates(
            name="Custom Location",  # Will be updated from API data
            latitude=lat,
            longitude=lon,
            country="",  # Will be updated from API data
            region=None,
        )

        # Get weather data
        coords = f"{lat},{lon}"
        weather_data = weather_api.get_weather(coords)

        if not weather_data:
            flash("Failed to get weather data", "error")
            return redirect(url_for("index"))

        # Update location name from API data if it was auto-created
        if location.name == "Custom Location":
            api_location = weather_data["location"]
            location = location_repo.update(
                location.id,
                {
                    "name": api_location["name"],
                    "country": api_location["country"],
                    "region": api_location.get("region"),
                },
            )

        # Format data for template
        formatted_data = format_weather_data(weather_data, unit)

        # Save record to database
        try:
            current_manager._save_weather_record(location, weather_data)
        except Exception as e:
            flash(f"Note: Failed to save weather data: {e}", "warning")

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


@app.route("/weather/<float:lat>/<float:lon>")
def weather(lat, lon):
    """Show weather for a location by coordinates"""
    unit = request.args.get("unit", "C").upper()
    if unit not in ["C", "F"]:
        unit = "C"

    try:
        # Find or create location
        location = location_repo.find_or_create_by_coordinates(
            name="Custom Location",  # Will be updated from API data
            latitude=lat,
            longitude=lon,
            country="",  # Will be updated from API data
            region=None,
        )

        # Get weather data
        coords = f"{lat},{lon}"
        weather_data = weather_api.get_weather(coords)

        if not weather_data:
            flash("Failed to get weather data", "error")
            return redirect(url_for("index"))

        # Update location name from API data if it was auto-created
        if location.name == "Custom Location":
            api_location = weather_data["location"]
            location = location_repo.update(
                location.id,
                {
                    "name": api_location["name"],
                    "country": api_location["country"],
                    "region": api_location.get("region"),
                },
            )

        # Format data for template
        formatted_data = format_weather_data(weather_data, unit)

        # Save record to database
        try:
            current_manager._save_weather_record(location, weather_data)
        except Exception as e:
            flash(f"Note: Failed to save weather data: {e}", "warning")

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
    unit = request.form.get("unit", "C").upper()

    if "location" in request.form:
        location = request.form.get("location")
    elif form.validate_on_submit():
        location = form.location.data

    if not location:
        flash("Please enter a valid location", "error")
        return redirect(url_for("index"))

    try:
        # Search for the location
        results = weather_api.search_city(location)
        if not results or len(results) == 0:
            flash(f"No cities found matching '{location}'", "warning")
            return redirect(url_for("index"))

        # If only one result, go directly to weather
        if len(results) == 1:
            return redirect(
                url_for(
                    "weather", lat=results[0]["lat"], lon=results[0]["lon"], unit=unit
                )
            )

        # If multiple results, show them
        return render_template(
            "search_results.html", results=results, query=location, unit=unit
        )

    except Exception as e:
        flash(f"Error finding location: {e}", "error")

    return redirect(url_for("index"))


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
    unit = request.args.get("unit", "C").upper()
    if unit not in ["C", "F"]:
        unit = "C"

    try:
        coords = f"{lat},{lon}"
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
    unit = request.args.get("unit", "C").upper()
    if unit not in ["C", "F"]:
        unit = "C"

    # Get forecast days from form or default to 7
    forecast_days = 7
    if request.method == "POST":
        form = ForecastDaysForm()
        if form.validate_on_submit():
            forecast_days = int(form.forecast_days.data)
    else:
        forecast_days = int(request.args.get("days", 7))

    try:
        # Find or get location
        location = location_repo.find_or_create_by_coordinates(
            name="Custom Location",
            latitude=lat,
            longitude=lon,
            country="",
            region=None,
        )

        # Get forecast data
        coords = f"{lat},{lon}"
        forecast_data = weather_api.get_forecast(coords, days=forecast_days)

        if not forecast_data:
            flash("Failed to get forecast data", "error")
            return redirect(url_for("index"))

        # Update location name from API data if it was auto-created
        if location.name == "Custom Location" and "location" in forecast_data:
            api_location = forecast_data["location"]
            location = location_repo.update(
                location.id,
                {
                    "name": api_location["name"],
                    "country": api_location["country"],
                    "region": api_location.get("region"),
                },
            )

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


# Keep the existing forecast route for form submission
@app.route("/forecast", methods=["POST"])
def forecast_form():
    """Process forecast form and redirect to forecast page"""
    form = ForecastDaysForm()
    lat = request.form.get("lat")
    lon = request.form.get("lon")
    unit = request.form.get("unit", "C")

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
    # Parse coordinates from the path
    try:
        # Split by slash and convert to float
        parts = coordinates.split("/")
        if len(parts) != 2:
            flash("Invalid coordinates format", "error")
            return redirect(url_for("index"))

        lat = float(parts[0])
        lon = float(parts[1])

        # Call the forecast function directly with the parsed coordinates
        return forecast(lat, lon)
    except Exception as e:
        flash(f"Error getting forecast: {e}", "error")
        return redirect(url_for("index"))


# Run the app
def run():
    """Run the Flask application"""
    app.run(debug=True, host="0.0.0.0", port=PORT)


if __name__ == "__main__":
    run()
