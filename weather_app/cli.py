from typing import Optional

import typer

from . import logger
from .api import WeatherAPI
from .app import WeatherApp
from .display import WeatherDisplay
from .exceptions import APIError, InputError

app = typer.Typer(help="🌤️ A Totally Awesome Command-line Weather App")


@app.command(name="interactive")
def interactive():
    """Run the weather app in interactive mode with all features."""
    try:
        logger.info("===== Weather App Started in Interactive Mode =====")
        weather_app = WeatherApp()
        weather_app.run()
    except Exception as e:
        logger.critical("Fatal error", exc_info=True)
        typer.echo(f"❌ Fatal error occurred: {e}")
    finally:
        logger.info("===== Weather App Finished =====")


@app.command(name="weather")
def get_weather(
    location: str = typer.Argument(
        ..., help="Location to get weather for (city, region, country)"
    ),
    unit: Optional[str] = typer.Option(
        "C", "--unit", "-u", help="Temperature unit (C for Celsius, F for Fahrenheit)"
    ),
):
    """Get current weather and forecast for a specific location."""
    try:
        logger.info(f"Getting weather for {location} in unit {unit}")
        api = WeatherAPI()
        display = WeatherDisplay()

        data = api.get_weather(location)
        if data:
            unit_choice = "F" if unit and unit.upper() == "F" else "C"
            display.show_current_weather(data, unit_choice)
            display.show_forecast(data, unit_choice)
        else:
            typer.echo(
                "❌ Failed to retrieve weather information. Check your input or API key."
            )
    except APIError as e:
        typer.echo(f"❌ API Error: {e.message}")
    except InputError as e:
        typer.echo(f"❌ Input Error: {e.message}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        typer.echo(f"❌ An unexpected error occurred: {e}")


@app.command(name="version")
def version():
    """Display the current version of the weather app."""
    typer.echo("Weather Dashboard v0.1.0")


if __name__ == "__main__":
    app()
