from datetime import datetime

from decouple import config
from flask import Flask, flash, jsonify, redirect, render_template, request, url_for
from flask_wtf.csrf import CSRFProtect

from weather_app.api import WeatherAPI
from weather_app.current import CurrentWeatherManager
from weather_app.database import init_db
from weather_app.display import WeatherDisplay
from weather_app.forecast import ForecastManager
from weather_app.location import LocationManager
from weather_app.repository import LocationRepository, SettingsRepository

from .forms import LocationSearchForm, UnitSelectionForm, UserInputLocationForm
from .utils import format_weather_data

# Initialize app and components
app = Flask(__name__)
app.config["SECRET_KEY"] = config("SECRET_KEY")
csrf = CSRFProtect(app)

init_db()
api = WeatherAPI()
display = WeatherDisplay()
location = LocationManager(api, display)
repo = LocationRepository()
forecast = ForecastManager(api, display)
current = CurrentWeatherManager(api, display)
settings = SettingsRepository()


@app.context_processor
def inject_year():
    return {"current_year": datetime.now().year}


@app.route("/")
def index():
    """Home page"""
    forms = {
        "search": LocationSearchForm(),
        "ui": UserInputLocationForm(),
        "unit": UnitSelectionForm(),
    }

    # Set default unit
    unit = settings.get_settings().temperature_unit
    forms["unit"].unit.default = "F" if unit.lower() == "fahrenheit" else "C"

    return render_template("index.html", forms=forms, favorites=repo.get_favorites())


@app.route("/search", methods=["POST"])
def search():
    """Search locations"""
    if not LocationSearchForm().validate_on_submit():
        return redirect(url_for("index"))

    query = request.form["query"]
    results = api.search_city(query)

    if not results:
        flash(f"No cities found matching '{query}'", "warning")
        return redirect(url_for("index"))

    return render_template("search_results.html", results=results, query=query)


@app.route("/weather/<float:lat>/<float:lon>")
def weather(lat, lon):
    """Show weather"""
    unit = request.args.get("unit", "C").upper()
    if unit not in ["C", "F"]:
        unit = "C"

    # Get location and weather
    loc = repo.find_or_create_by_coordinates("Custom Location", lat, lon, "", None)
    data = api.get_weather(f"{lat},{lon}")

    if not data:
        flash("Failed to get weather data", "error")
        return redirect(url_for("index"))

    # Update location if needed
    if loc.name == "Custom Location":
        api_loc = data["location"]
        loc = repo.update(
            loc.id,
            {
                "name": api_loc["name"],
                "country": api_loc["country"],
                "region": api_loc.get("region"),
            },
        )

    # Save and display
    current._save_weather_record(loc, data)
    return render_template(
        "weather.html",
        weather=format_weather_data(data, unit),
        location=loc,
        unit=unit,
        lat=lat,
        lon=lon,
    )


@app.route("/ui", methods=["POST"])
def ui_location():
    """Handle location entry"""
    if not UserInputLocationForm().validate_on_submit():
        return redirect(url_for("index"))

    location = request.form["location"]
    unit = request.form.get("unit", "C").upper()
    results = api.search_city(location)

    if not results:
        flash(f"No cities found matching '{location}'", "warning")
        return redirect(url_for("index"))

    if len(results) == 1:
        return redirect(
            url_for("weather", lat=results[0]["lat"], lon=results[0]["lon"], unit=unit)
        )

    return render_template("search_results.html", results=results, query=location)


@app.route("/favorite/<int:location_id>", methods=["POST"])
def toggle_favorite(location_id):
    """Toggle favorite"""
    success = location.toggle_favorite(location_id)
    flash(
        "Favorite updated" if success else "Update failed",
        "success" if success else "error",
    )
    return redirect(request.args.get("next") or url_for("index"))


@app.route("/unit", methods=["POST"])
def update_unit():
    """Update unit"""
    if UnitSelectionForm().validate_on_submit():
        unit = request.form["unit"].upper()
        if unit in ["C", "F"]:
            settings.update_temperature_unit("celsius" if unit == "C" else "fahrenheit")
            flash(f"Unit updated to {unit}", "success")
    return redirect(url_for("index"))


@app.route("/api/weather/<float:lat>/<float:lon>")
def api_weather(lat, lon):
    """API endpoint"""
    unit = request.args.get("unit", "C").upper()
    if unit not in ["C", "F"]:
        unit = "C"

    data = api.get_weather(f"{lat},{lon}")
    if not data:
        return jsonify({"error": "No data"}), 404

    return jsonify(format_weather_data(data, unit))


def run():
    """Run app"""
    app.run(debug=True)


if __name__ == "__main__":
    run()
