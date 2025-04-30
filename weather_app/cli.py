import typer
from . import logger
from .app import WeatherApp


app = typer.Typer(help="🌤️ A Totally Awesome Command-line Weather App")

# function to run application interactively
@app.command()
def typer_interactive_cli():
  try:
    logger.info("===== Weather App Started =====")
    app = WeatherApp()
    app.run()
  except Exception as e:
    logger.critical("Fatal error", exc_info=True)
    print(f"Fatal error occurred: {e}")
  finally:
    logger.info("===== Weather App Finished =====")

# function to grab weather location from user --maybe fixes bug
# @app.command()
# def get_weather(location:str):
#     api = WeatherAPI()
#     display = WeatherDisplay()

#     data = api.get_weather(location)
#     if data:
#         display.show_current_weather(data)
#         display.show_forecast(data)
#     else:
#         typer.echo("❌ Failed to retrieve weather information. Check your input or API key.")
