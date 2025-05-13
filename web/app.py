"""
Weather Dashboard Flask application.

A web interface for the weather_app package that provides
temperature unit selection and current/forecast toggle.
"""

from datetime import datetime

from decouple import config
from flask import Flask, flash, render_template, request
from flask_wtf.csrf import CSRFProtect

# Import weather_app components
from weather_app.api import WeatherAPI
from weather_app.current import CurrentWeatherManager
from weather_app.database import init_db
from weather_app.display import WeatherDisplay
from weather_app.forecast import ForecastManager
from weather_app.location import LocationManager
from weather_app.repository import LocationRepository, SettingsRepository

# Initialize Flask app
app = Flask(__name__)
app.config["SECRET_KEY"] = config("SECRET_KEY")
csrf = CSRFProtect(app)

# Initialize database
try:
    init_db()
except Exception as e:
    print(f"Warning: Failed to initialize database: {e}")

# Initialize weather components
weather_api = WeatherAPI()
display = WeatherDisplay()
location_manager = LocationManager(weather_api, display)
location_repo = LocationRepository()
forecast_manager = ForecastManager(weather_api, display)
current_manager = CurrentWeatherManager(weather_api, display)
settings_repo = SettingsRepository()


# Context processor for all templates
@app.context_processor
def inject_globals():
    return {
        "current_year": datetime.now().year,
    }


# Routes for home page this will go for the index html page
@app.route("/")
def index():
    """Home page with location search form."""
    # Get favorite locations for quick access
    favorites = []
    try:
        favorites = location_repo.get_favorites()
    except Exception as e:
        flash(f"Error loading favorite locations: {e}", "error")

    # Get user's temperature unit preference
    temp_unit = request.args.get("unit", "C").upper()
    if temp_unit not in ["C", "F"]:
        temp_unit = "C"

    # Get display type preference (current or forecast)
    display_type = request.args.get("display", "current")
    if display_type not in ["current", "forecast"]:
        display_type = "current"

    return render_template(
        "index.html",
        favorites=favorites,
        temp_unit=temp_unit,
        display_type=display_type,
    )


# @app.route("/search", methods=["POST"])
# def search():
#     """Search for locations by name."""
#     query = request.form.get("location", "")
#     if not query:
#         flash("Please enter a location", "warning")
#         return redirect(url_for("index"))

#     try:
#         results = weather_api.search_city(query)
#         if not results:
#             flash(f"No cities found matching '{query}'", "warning")
#             return redirect(url_for("index"))

#         # Get user preferences from query
#         temp_unit = request.args.get("unit", "C").upper()
#         display_type = request.args.get("display", "current")

#         return render_template(
#             "search_results.html",
#             results=results,
#             query=query,
#             temp_unit=temp_unit,
#             display_type=display_type,
#         )
#     except Exception as e:
#         flash(f"Error searching for location: {e}", "error")
#         return redirect(url_for("index"))


# @app.route("/weather/<float:lat>/<float:lon>")
# def weather(lat, lon):
#     """Show weather for a location by coordinates."""
#     # Get user preferences from query parameters
#     temp_unit = request.args.get("unit", "C").upper()
#     if temp_unit not in ["C", "F"]:
#         temp_unit = "C"

#     display_type = request.args.get("display", "current")
#     if display_type not in ["current", "forecast"]:
#         display_type = "current"

#     try:
#         # Find or create location
#         location = location_repo.find_or_create_by_coordinates(
#             name="Custom Location",
#             latitude=lat,
#             longitude=lon,
#             country="",
#             region=None,
#         )

#         # Get weather data
#         coords = f"{lat},{lon}"
#         weather_data = weather_api.get_weather(coords)

#         if not weather_data:
#             flash("Failed to get weather data", "error")
#             return redirect(url_for("index"))

#         # Update location name from API data if it was auto-created
#         if location.name == "Custom Location":
#             api_location = weather_data["location"]
#             location = location_repo.update(
#                 location.id,
#                 {
#                     "name": api_location["name"],
#                     "country": api_location["country"],
#                     "region": api_location.get("region"),
#                 },
#             )

#         # Format data for display
#         formatted_data = format_weather_data(weather_data, temp_unit)

#         # Save record to database
#         try:
#             current_manager._save_weather_record(location, weather_data)
#         except Exception as e:
#             flash(f"Note: Failed to save weather data: {e}", "warning")

#         return render_template(
#             "weather.html",
#             weather=formatted_data,
#             location=location,
#             temp_unit=temp_unit,
#             display_type=display_type,
#             lat=lat,
#             lon=lon,
#         )

#     except Exception as e:
#         flash(f"Error getting weather: {e}", "error")
#         return redirect(url_for("index"))


# @app.route("/toggle/unit")
# def toggle_unit():
#     """Toggle temperature unit and redirect back."""
#     # Get current unit and toggle it
#     current_unit = request.args.get("unit", "C").upper()
#     new_unit = "F" if current_unit == "C" else "C"

#     # Get other parameters to preserve them
#     display_type = request.args.get("display", "current")
#     lat = request.args.get("lat")
#     lon = request.args.get("lon")

#     # If we have coordinates, redirect to weather page
#     if lat and lon:
#         return redirect(
#             url_for(
#                 "weather",
#                 lat=float(lat),
#                 lon=float(lon),
#                 unit=new_unit,
#                 display=display_type,
#             )
#         )

#     # Otherwise redirect to index
#     return redirect(url_for("index", unit=new_unit, display=display_type))


# @app.route("/toggle/display")
# def toggle_display():
#     """Toggle display type and redirect back."""
#     # Get current display type and toggle it
#     current_display = request.args.get("display", "current")
#     new_display = "forecast" if current_display == "current" else "current"

#     # Get other parameters to preserve them
#     temp_unit = request.args.get("unit", "C").upper()
#     lat = request.args.get("lat")
#     lon = request.args.get("lon")

#     # If we have coordinates, redirect to weather page
#     if lat and lon:
#         return redirect(
#             url_for(
#                 "weather",
#                 lat=float(lat),
#                 lon=float(lon),
#                 unit=temp_unit,
#                 display=new_display,
#             )
#         )

#     # Otherwise redirect to index
#     return redirect(url_for("index", unit=temp_unit, display=new_display))


# @app.route("/favorite/<int:location_id>", methods=["POST"])
# def toggle_favorite(location_id):
#     """Toggle favorite status for a location."""
#     try:
#         success = location_manager.toggle_favorite(location_id)
#         if success:
#             flash("Favorite status updated", "success")
#         else:
#             flash("Failed to update favorite status", "error")
#     except Exception as e:
#         flash(f"Error updating favorite status: {e}", "error")

#     # Return to previous page or index
#     next_page = request.args.get("next") or url_for("index")
#     return redirect(next_page)


# def format_weather_data_unit(weather_data, unit="C"):
#     """Format weather data for display in templates."""
#     if not weather_data:
#         return {}

#     result = {
#         "location": {
#             "name": weather_data["location"]["name"],
#             "region": weather_data["location"]["region"],
#             "country": weather_data["location"]["country"],
#         },
#         "current": {
#             "condition": weather_data["current"]["condition"]["text"],
#             "icon": weather_data["current"]["condition"]["icon"],
#             "humidity": weather_data["current"]["humidity"],
#             "wind_kph": weather_data["current"]["wind_kph"],
#             "wind_mph": weather_data["current"]["wind_mph"],
#             "wind_dir": weather_data["current"]["wind_dir"],
#             "pressure_mb": weather_data["current"]["pressure_mb"],
#             "pressure_in": weather_data["current"]["pressure_in"],
#             "precip_mm": weather_data["current"]["precip_mm"],
#             "precip_in": weather_data["current"]["precip_in"],
#             "last_updated": weather_data["current"]["last_updated"],
#         },
#         "unit": unit,
#     }

#     # Add temperature based on unit
#     if unit == "F":
#         result["current"]["temp"] = weather_data["current"]["temp_f"]
#         result["current"]["feelslike"] = weather_data["current"]["feelslike_f"]
#     else:
#         result["current"]["temp"] = weather_data["current"]["temp_c"]
#         result["current"]["feelslike"] = weather_data["current"]["feelslike_c"]

#     # Add forecast if available
#     if "forecast" in weather_data:
#         result["forecast"] = []
#         for day in weather_data["forecast"].get("forecastday", []):
#             forecast_day = {
#                 "date": day["date"],
#                 "condition": day["day"]["condition"]["text"],
#                 "icon": day["day"]["condition"]["icon"],
#                 "humidity": day["day"].get("avghumidity", "N/A"),
#                 "chance_of_rain": day["day"].get("daily_chance_of_rain", "N/A"),
#                 "chance_of_snow": day["day"].get("daily_chance_of_snow", "N/A"),
#             }

#             # Add temperature based on unit
#             if unit == "F":
#                 forecast_day["max_temp"] = day["day"]["maxtemp_f"]
#                 forecast_day["min_temp"] = day["day"]["mintemp_f"]
#             else:
#                 forecast_day["max_temp"] = day["day"]["maxtemp_c"]
#                 forecast_day["min_temp"] = day["day"]["mintemp_c"]

#             # Add sunrise/sunset if available
#             if "astro" in day:
#                 forecast_day["sunrise"] = day["astro"].get("sunrise", "N/A")
#                 forecast_day["sunset"] = day["astro"].get("sunset", "N/A")

#             result["forecast"].append(forecast_day)

#     return result


# Run the app
def run():
    """Run the Flask application."""
    app.run(debug=True, host="0.0.0.0")


if __name__ == "__main__":
    run()
