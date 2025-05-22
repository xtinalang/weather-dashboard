import os
import re
import time
from datetime import datetime
from typing import Any, Dict, List, Tuple, cast

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
from weather_app.weather_types import (
    CELSIUS,
    DEFAULT_FORECAST_DAYS,
    DEFAULT_TEMP_UNIT,
    FAHRENHEIT,
    LocationData,
    TemperatureUnit,
    WeatherData,
)

from .forms import (
    DateWeatherNLForm,
    ForecastDaysForm,
    LocationSearchForm,
    UnitSelectionForm,
    UserInputLocationForm,
)
from .helpers import Helpers
from .utils import Utility

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
utility = Utility()


# Context processor to add current year to all templates
@app.context_processor
def inject_current_year() -> Dict[str, int]:
    return {"current_year": datetime.now().year}


# Helper functions for route handlers
def get_weather_data(
    coords: Tuple[float, float], unit: TemperatureUnit
) -> Tuple[WeatherData, LocationData]:
    """Get weather data for given coordinates."""
    weather_data = weather_api.get_weather(coords)
    if not weather_data:
        raise ValueError("Failed to get weather data")

    location_obj, _ = Helpers.get_location_by_coordinates(coords[0], coords[1])
    location_obj = Helpers.update_location_from_api_data(location_obj, weather_data)

    # Debug logging
    print("\nDEBUG: Raw Weather API Response:")
    print(f"Raw weather data structure: {weather_data}")

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

    # Debug logging
    print("\nDEBUG: Formatted Weather Data:")
    print(f"Formatted data structure: {formatted_data}")

    return formatted_data, location_obj


def get_forecast_data(coords: Tuple[float, float], unit: TemperatureUnit) -> List[Dict]:
    """Get forecast data for given coordinates."""
    forecast_data = weather_api.get_forecast(coords)
    if not forecast_data:
        raise ValueError("Failed to get forecast data")

    # Debug logging
    print("\nDEBUG: Raw Forecast API Response:")
    print(f"Raw forecast data structure: {forecast_data}")

    # Format the forecast data
    formatted_forecast = []
    for day in forecast_data["forecast"]["forecastday"]:
        formatted_day = {
            "date": day["date"],
            "max_temp": day["day"]["maxtemp_c"]
            if unit == TemperatureUnit.CELSIUS
            else day["day"]["maxtemp_f"],
            "min_temp": day["day"]["mintemp_c"]
            if unit == TemperatureUnit.CELSIUS
            else day["day"]["mintemp_f"],
            "condition": day["day"]["condition"],
            "chance_of_rain": day["day"]["daily_chance_of_rain"],
            "chance_of_snow": day["day"]["daily_chance_of_snow"],
            "maxwind_kph": day["day"]["maxwind_kph"],
            "maxwind_mph": day["day"]["maxwind_mph"],
            "totalprecip_mm": day["day"]["totalprecip_mm"],
            "totalprecip_in": day["day"]["totalprecip_in"],
            "avghumidity": day["day"]["avghumidity"],
            "uv": day["day"]["uv"],
        }
        formatted_forecast.append(formatted_day)

    # Debug logging
    print("\nDEBUG: Formatted Forecast Data:")
    print(f"Formatted forecast structure: {formatted_forecast}")
    if formatted_forecast:
        print(f"First forecast day structure: {formatted_forecast[0]}")

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
        nl_form=nl_form,
        favorites=favorites,
    )


@app.route("/search", methods=["POST"])
def search() -> Any:
    """Search for locations."""
    form = LocationSearchForm()
    unit = cast(TemperatureUnit, request.form.get("unit", DEFAULT_TEMP_UNIT).upper())
    forecast_days = request.form.get("forecast_days")

    if not form.validate_on_submit():
        return redirect(url_for("index"))

    query = form.query.data
    results = weather_api.search_city(query)

    if not results:
        flash(f"No cities found matching '{query}'", "warning")
        return redirect(url_for("index"))

    if len(results) == 1:
        if forecast_days:
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

    return render_template(
        "search_results.html", results=results, query=query, unit=unit
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
    except Exception as e:
        flash(f"Error getting weather: {str(e)}", "error")
        return redirect(url_for("index"))


@app.route("/weather/<float:lat>/<float:lon>")
def weather(lat: float, lon: float) -> Any:
    """Show weather for a location by coordinates."""
    try:
        # Validate coordinate ranges
        if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
            raise ValueError("Coordinates out of valid range")

        unit = Helpers.get_normalized_unit()
        coords = (lat, lon)

        weather_data, location = get_weather_data(coords, unit)
        Helpers.save_weather_record(location, weather_data)

        return render_template(
            "weather.html",
            weather=weather_data,
            location=location,
            unit=unit,
            lat=lat,
            lon=lon,
        )
    except ValueError as e:
        flash(f"Invalid coordinates: {str(e)}", "error")
        return redirect(url_for("index"))
    except Exception as e:
        flash(f"Error getting weather: {str(e)}", "error")
        return redirect(url_for("index"))


@app.route("/ui", methods=["POST"])
def ui_location() -> Any:
    """Handle UI location entry."""
    form = UserInputLocationForm()
    unit = cast(TemperatureUnit, request.form.get("unit", DEFAULT_TEMP_UNIT).upper())
    forecast_days = request.form.get("forecast_days")

    location = request.form.get("location") or (
        form.location.data if form.validate_on_submit() else None
    )

    if not location:
        flash("Please enter a valid location", "error")
        return redirect(url_for("index"))

    try:
        results = weather_api.search_city(location)
        if not results:
            flash(f"No cities found matching '{location}'", "warning")
            return redirect(url_for("index"))

        if len(results) == 1:
            if forecast_days:
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

        return render_template(
            "search_results.html", results=results, query=location, unit=unit
        )
    except Exception as e:
        flash(f"Error finding location: {e}", "error")
        return redirect(url_for("index"))


@app.route("/favorite/<int:location_id>", methods=["POST"])
def toggle_favorite(location_id: int) -> Any:
    """Toggle favorite status for a location."""
    try:
        success = location_manager.toggle_favorite(location_id)
        if success:
            flash("Favorite status updated", "success")
        else:
            flash("Failed to update favorite status", "error")
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
        if unit in [CELSIUS, FAHRENHEIT]:
            try:
                unit_value = "celsius" if unit == CELSIUS else "fahrenheit"
                settings_repo.update_temperature_unit(unit_value)
                flash(f"Temperature unit updated to {unit_value}", "success")
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

        return render_template(
            "forecast.html",
            forecast=formatted_forecast,
            unit=unit,
            lat=lat,
            lon=lon,
            forecast_days=forecast_days,
        )
    except Exception as e:
        flash(f"Error getting forecast: {e}", "error")
        return redirect(url_for("index"))


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

            return render_template(
                "search_results.html", results=results, query=location, unit=unit
            )
        except Exception as e:
            flash(f"Error finding location: {e}", "error")

    flash("Missing location information", "error")
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
    start_time = time.time()
    query = request.form.get("query", "").strip()
    unit = Helpers.get_normalized_unit()

    try:
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
                # Extract coordinates from the first result
                first_result = results[0]
                print(f"First API result: {first_result}")  # Debug log
                try:
                    lat = float(first_result.get("lat", 0))
                    lon = float(first_result.get("lon", 0))
                    if lat == 0 or lon == 0:
                        raise ValueError("Invalid coordinates")
                    coords = (lat, lon)
                    print(f"Found coordinates via API: {coords}")
                except (ValueError, TypeError) as e:
                    print(f"Error parsing coordinates: {e}")
                    print(f"Raw lat value: {first_result.get('lat')}")
                    print(f"Raw lon value: {first_result.get('lon')}")
                    coords = None
            else:
                location_name = Helpers.normalize_location_input(location_name)
                print(f"Trying normalized location: {location_name}")
                coords = location_manager.get_coordinates(location_name)
        except Exception as api_error:
            print(f"API search failed: {api_error}")
            location_name = Helpers.normalize_location_input(location_name)
            coords = location_manager.get_coordinates(location_name)

        if not coords:
            flash(f"Could not find location: {location_name}", "error")
            return redirect(url_for("index"))

        # Get current weather and forecast data
        current_weather_data, location_obj = get_weather_data(coords, unit)
        forecast_data = get_forecast_data(coords, unit)

        # Debug logging
        print("\nDEBUG: Current Weather Data:")
        print(f"Current weather data structure: {current_weather_data}")
        print("\nDEBUG: Forecast Data:")
        print(f"Forecast data structure: {forecast_data}")
        print(f"Number of forecast days: {len(forecast_data)}")
        if forecast_data:
            print(f"First forecast day structure: {forecast_data[0]}")

        Helpers.save_weather_record(location_obj, current_weather_data)

        print(f"Total request time: {time.time() - start_time:.2f} seconds")

        # Check if the query mentions weekend or next week
        query_lower = query.lower()
        if "weekend" in query_lower or "next week" in query_lower:
            # Filter forecast data for weekend or next week
            filtered_forecast = []
            today = datetime.now().date()

            if "weekend" in query_lower:
                # Get this weekend's forecast
                for day in forecast_data:
                    day_date = datetime.strptime(day["date"], "%Y-%m-%d").date()
                    if day_date.weekday() >= 5:  # Saturday (5) or Sunday (6)
                        filtered_forecast.append(day)
            elif "next week" in query_lower:
                # Get next week's forecast
                for day in forecast_data:
                    day_date = datetime.strptime(day["date"], "%Y-%m-%d").date()
                    days_ahead = (day_date - today).days
                    if 1 <= days_ahead <= 7:  # Next 7 days
                        filtered_forecast.append(day)

            forecast_data = filtered_forecast

        # Ensure we have valid coordinates for the template
        lat, lon = coords
        print(f"Final coordinates for template: lat={lat}, lon={lon}")  # Debug log
        if not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)):
            raise ValueError("Invalid coordinates format")

        # Convert dates to datetime objects for the template
        dates = [datetime.strptime(day["date"], "%Y-%m-%d") for day in forecast_data]

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
        print(f"Error in nl_date_weather: {str(e)}")
        print(f"Full error details: {type(e).__name__}: {str(e)}")  # Debug log
        flash(f"Error processing your query: {str(e)}", "error")
        return redirect(url_for("index"))


# Run the app
def run() -> None:
    """Run the Flask application."""
    app.run(debug=True, host="0.0.0.0", port=PORT)


if __name__ == "__main__":
    run()
