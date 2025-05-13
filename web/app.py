# It initializes the Flask app, the database, and the API.
# It also defines the routes for the web app.


from datetime import datetime

from flask import Flask, render_template, request

# Create Flask app
app = Flask(__name__, template_folder="web/templates")


# Home page
@app.route("/")
def index():
    return render_template("index.html", current_year=datetime.now().year)


# Weather page
@app.route("/weather")
def weather():
    city = request.args.get("city", "Unknown")
    unit = request.args.get("unit", "C")

    # Simple weather data
    weather_data = {
        "city": city,
        "temperature": 22 if unit == "C" else 72,
        "unit": unit,
        "condition": "Sunny",
        "date": datetime.now().strftime("%B %d, %Y"),
    }

    return render_template(
        "weather.html", weather=weather_data, current_year=datetime.now().year
    )


# @app.route("/weather/forecast")
# def forecast():
#     try:
#         city = request.args.get("city", "Unknown")
#         unit = request.args.get("unit", "C")

#         # Get forecast data from API
#         forecast_data = get_forecast_data(city, unit)


#     return render_template("forecast.html")


# Run the app
if __name__ == "__main__":
    # Use a different port since 8008 is in use
    port = 5001
    print(f"Starting Weather Dashboard on http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=True)
