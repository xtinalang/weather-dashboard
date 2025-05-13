#!/usr/bin/env python3
"""
Minimal Weather Dashboard
"""

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


# Run the app
if __name__ == "__main__":
    # Use a different port since 8008 is in use
    port = 8009
    print(f"Starting Weather Dashboard on http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=True)
