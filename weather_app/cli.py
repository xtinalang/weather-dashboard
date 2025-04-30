"""This is for Typer"""

import typer

app = typer.Typer(help="🌤️ A Totally Awesome Command-line Weather App")

# function to run application interactively
# @app_cli.command()
# def typer_interactive_cli()
#   WeatherApp().run() '''Verify syntax'''


@app.command()
def run():
    print("Running the WeatherApp...")


# function to grab weather location from user
# app_cli.command()
# def get_weather(location:str)
#     api = WeatherAPI()
#     display = WeatherDisplay()

#     data = api.get_weather(location)
#     if data:
#         display.show_current_weather(data)
#         display.show_forecast(data)
#     else:
#         typer.echo("❌ Failed to retrieve weather information. Check your input or API key.")
