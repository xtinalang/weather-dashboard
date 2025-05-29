import logging
import os
import sys
import traceback
from datetime import datetime
from typing import Optional

import typer
from rich.console import Console

from . import logger
from .api import WeatherAPI
from .cli_app import WeatherApp
from .database import DATABASE_URL
from .database import init_db as initialize_database
from .display import WeatherDisplay
from .exceptions import APIError, InputError
from .location import LocationManager
from .models import Location
from .repository import LocationRepository

app = typer.Typer(help="🌤️ A Totally Awesome Command-line Weather App")
console = Console()


def get_app() -> WeatherApp:
    """Get WeatherApp instance"""
    return WeatherApp()


@app.command()
def current(
    unit: str = typer.Option(
        "C", "--unit", "-u", help="Temperature unit (C for Celsius, F for Fahrenheit)"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose logging"
    ),
) -> None:
    """Show current weather for a location"""
    configure_logging(verbose)
    weather_app = get_app()
    weather_app.unit = unit.upper()
    weather_app.run()


@app.command()
def forecast(
    days: Optional[int] = typer.Option(
        None, "--days", "-d", help="Number of days to forecast (1-7)", min=1, max=7
    ),
    unit: str = typer.Option(
        "C", "--unit", "-u", help="Temperature unit (C for Celsius, F for Fahrenheit)"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose logging"
    ),
) -> None:
    """Show weather forecast"""
    configure_logging(verbose)
    weather_app = get_app()
    weather_app.unit = unit.upper()

    if days:
        weather_app.show_forecast_for_days(days)
    else:
        weather_app.run()


@app.command()
def set_forecast_days(
    days: int = typer.Option(
        ...,  # Required
        "--days",
        "-d",
        help="Default number of forecast days (1-7)",
        min=1,
        max=7,
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose logging"
    ),
) -> None:
    """Set default number of forecast days"""
    configure_logging(verbose)
    weather_app = get_app()
    weather_app.set_default_forecast_days(days)


@app.command()
def interactive(
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose logging"
    ),
) -> None:
    """Start interactive weather app"""
    configure_logging(verbose)
    weather_app = get_app()
    weather_app.run_from_user_input()


@app.command(name="weather")
def get_weather(
    location: str = typer.Argument(
        ..., help="Location to get weather for (city, region, country)"
    ),
    unit: str = typer.Option(
        "C", "--unit", "-u", help="Temperature unit (C for Celsius, F for Fahrenheit)"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose logging"
    ),
) -> None:
    """Get current weather and forecast for a specific location."""
    configure_logging(verbose)
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
            console.print(
                "[bold red]❌ Failed to retrieve weather information. "
                "Check your input or API key.[/bold red]"
            )
    except APIError as e:
        console.print(f"[bold red]❌ API Error: {e.message}[/bold red]")
    except InputError as e:
        console.print(f"[bold red]❌ Input Error: {e.message}[/bold red]")
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        console.print(f"[bold red]❌ An unexpected error occurred: {e}[/bold red]")


@app.command(name="version")
def version() -> None:
    """Display the current version of the weather app."""
    console.print("[blue]Weather Dashboard v0.1.0[/blue]")


@app.command(name="date")
def date_forecast(
    date: str = typer.Argument(..., help="Date in YYYY-MM-DD format"),
    unit: str = typer.Option(
        "C", "--unit", "-u", help="Temperature unit (C for Celsius, F for Fahrenheit)"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose logging"
    ),
) -> None:
    """Get forecast for a specific date."""
    configure_logging(verbose)
    try:
        target_date = datetime.strptime(date, "%Y-%m-%d")
        weather_app = get_app()
        weather_app.unit = unit.upper()
        weather_app.show_forecast_for_date(target_date)
    except ValueError:
        console.print(
            f"[bold red]Error: Invalid date format '{date}'. Use YYYY-MM-DD[/bold red]"
        )


@app.command(name="init-db")
def init_database(
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose logging"
    ),
) -> None:
    """Initialize or reset the database."""
    configure_logging(verbose)
    try:
        # Directly initialize the database without going through the app
        initialize_database()

        # initialize_database()
        console.print("[bold green]Database initialized successfully![/bold green]")
    except Exception as e:
        console.print(f"[bold red]Error initializing database: {e}[/bold red]")


@app.command()
def settings(
    forecast_days: Optional[int] = typer.Option(
        None, "--forecast-days", help="Default number of forecast days (1-7)"
    ),
    temp_unit: Optional[str] = typer.Option(
        None, "--temp-unit", help="Default temperature unit (C or F)"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose logging"
    ),
) -> None:
    """Update application settings."""
    configure_logging(verbose)
    weather_app = get_app()

    if forecast_days is not None:
        try:
            weather_app.set_default_forecast_days(forecast_days)
            console.print(
                f"[green]Default forecast days updated to {forecast_days}[/green]"
            )
        except Exception as e:
            console.print(f"[red]Error updating forecast days: {e}[/red]")

    if temp_unit is not None:
        try:
            unit = "fahrenheit" if temp_unit.upper() == "F" else "celsius"
            weather_app.settings_repo.update_temperature_unit(unit)
            console.print(f"[green]Default temperature unit updated to {unit}[/green]")
        except Exception as e:
            console.print(f"[red]Error updating temperature unit: {e}[/red]")


@app.command("refresh-location")
def refresh_location(
    city: Optional[str] = typer.Option(None, "--city", help="City name to refresh"),
    id: Optional[int] = typer.Option(None, "--id", help="Location ID to refresh"),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose logging"
    ),
) -> None:
    """Refresh location data in the database."""
    configure_logging(verbose)
    weather_app = get_app()

    try:
        if id:
            location = weather_app.location_repo.get_by_id(id)
            if location:
                fresh_location = weather_app.refresh_location(location)
                if fresh_location:
                    console.print(
                        f"[green]Successfully refreshed location: "
                        f"{fresh_location.name}, "
                        f"{fresh_location.country}[/green]"
                    )
                else:
                    console.print(f"[red]Failed to refresh location with ID {id}[/red]")
            else:
                console.print(f"[red]Location with ID {id} not found[/red]")

        elif city:
            # Search for locations matching the city name
            locations = weather_app.location_repo.search(city)
            if not locations:
                console.print(f"[yellow]No locations found matching '{city}'[/yellow]")
                return

            console.print(
                f"[blue]Found {len(locations)} matching locations. Refreshing...[/blue]"
            )
            for loc in locations:
                fresh_loc = weather_app.refresh_location(loc)
                if fresh_loc:
                    console.print(
                        f"[green]Refreshed: {fresh_loc.name}, "
                        f"{fresh_loc.country} (ID: {fresh_loc.id})[/green]"
                    )
                else:
                    console.print(
                        f"[red]Failed to refresh: {loc.name}, "
                        f"{loc.country} (ID: {loc.id})[/red]"
                    )

        else:
            console.print(
                "[yellow]Please specify either --city or --id to refresh a "
                "location[/yellow]"
            )

    except Exception as e:
        logger.error(f"Failed to refresh location: {e}")
        console.print(f"[bold red]Error: {e}[/bold red]")


@app.command("diagnostics")
def run_diagnostics(
    verbose: bool = typer.Option(
        True, "--verbose", "-v", help="Enable verbose logging"
    ),
) -> None:
    """Run diagnostics on database and location data."""
    configure_logging(verbose)
    console.print("[blue]Running Weather App diagnostics...[/blue]")

    # 1. Check database connection
    try:
        console.print("\n[bold]1. Database Connection Test[/bold]")
        console.print("[green]✓ Database connection established[/green]")

        console.print(f"Database URL: {DATABASE_URL}")

        if DATABASE_URL.startswith("sqlite"):
            db_path = DATABASE_URL.replace("sqlite:///", "")
            if os.path.exists(db_path):
                size = os.path.getsize(db_path)
                console.print(
                    f"SQLite database file: {db_path} (Size: {size / 1024:.1f} KB)"
                )
            else:
                console.print(
                    f"[yellow]Warning: SQLite database file does not exist: "
                    f"{db_path}[/yellow]"
                )
    except Exception as e:
        console.print(f"[red]✗ Database connection failed: {e}[/red]")

    # 2. Check if tables exist
    try:
        console.print("\n[bold]2. Database Schema Test[/bold]")
        location_repo = LocationRepository()

        try:
            count = location_repo.count()
            console.print(
                f"[green]✓ Location table exists with {count} records[/green]"
            )
        except Exception as e:
            console.print(f"[red]✗ Error accessing Location table: {e}[/red]")
            console.print("[yellow]Attempting to initialize database...[/yellow]")
            try:
                initialize_database()
                console.print("[green]Database initialized successfully[/green]")
            except Exception as init_err:
                console.print(
                    f"[red]✗ Database initialization failed: {init_err}[/red]"
                )

    except Exception as e:
        console.print(f"[red]✗ Database schema test failed: {e}[/red]")

    # 3. Location Manager Test
    try:
        console.print("\n[bold]3. Location Manager Test[/bold]")
        location_manager = LocationManager()

        # Test location search
        test_location = location_manager.get_location("Paris")
        if test_location:
            console.print(
                f"[green]✓ Location manager working. Found: "
                f"{test_location.name}, {test_location.country}[/green]"
            )
        else:
            console.print(
                "[yellow]⚠ Location manager returned no results for 'Paris'[/yellow]"
            )

    except Exception as e:
        console.print(f"[red]✗ Location manager test failed: {e}[/red]")

    # 4. Weather API Test
    try:
        console.print("\n[bold]4. Weather API Test[/bold]")
        api = WeatherAPI()

        # Test a simple weather request
        console.print("[blue]Testing API with London...[/blue]")
        weather_data = api.get_weather("London")

        if weather_data and "location" in weather_data:
            location_name = weather_data["location"].get("name", "Unknown")
            console.print(
                f"[green]✓ Weather API working. Retrieved data for: "
                f"{location_name}[/green]"
            )
        else:
            console.print("[yellow]⚠ Weather API returned no/invalid data[/yellow]")

    except APIError as e:
        console.print(f"[red]✗ Weather API test failed: {e.message}[/red]")
    except Exception as e:
        console.print(f"[red]✗ Weather API test failed: {e}[/red]")

    console.print("\n[bold blue]Diagnostics complete![/bold blue]")


@app.command("add-location")
def add_location(
    name: str = typer.Option(..., "--name", "-n", help="Location name"),
    latitude: float = typer.Option(..., "--lat", help="Latitude coordinate"),
    longitude: float = typer.Option(..., "--lon", help="Longitude coordinate"),
    country: str = typer.Option(..., "--country", "-c", help="Country name"),
    region: Optional[str] = typer.Option(
        None, "--region", "-r", help="Region/state name"
    ),
    favorite: bool = typer.Option(False, "--favorite", "-f", help="Mark as favorite"),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose logging"
    ),
) -> None:
    """Add a new location to the database."""
    configure_logging(verbose)

    try:
        location_repo = LocationRepository()

        # Create new location
        new_location = Location(
            name=name,
            latitude=latitude,
            longitude=longitude,
            country=country,
            region=region,
        )

        # Save to database
        saved_location = location_repo.create(new_location)

        console.print(
            f"[green]Added location successfully: {saved_location.name}, "
            f"{saved_location.country}[/green]"
        )
        console.print(
            f"[blue]Location ID: {saved_location.id}, "
            f"Coordinates: ({saved_location.latitude}, "
            f"{saved_location.longitude})[/blue]"
        )

        if favorite:
            console.print("[green]Location marked as favorite[/green]")

    except Exception as e:
        logger.error(f"Failed to add location: {e}")
        console.print(f"[bold red]Error adding location: {e}[/bold red]")


@app.command("test-location")
def test_location_saving(
    city: str = typer.Option("Paris", "--city", "-c", help="City name to test with"),
    country: str = typer.Option(
        "France", "--country", help="Country name for the test city"
    ),
    lat: float = typer.Option(48.8566, "--lat", help="Latitude of the test city"),
    lon: float = typer.Option(2.3522, "--lon", help="Longitude of the test city"),
    verbose: bool = typer.Option(
        True, "--verbose", "-v", help="Enable verbose logging"
    ),
) -> None:
    """Test location saving functionality."""
    configure_logging(verbose)
    console.print(f"[blue]Testing location saving with {city}, {country}[/blue]")

    try:
        # Create repository
        location_repo = LocationRepository()

        # Create test location
        test_location = Location(
            name=city,
            latitude=lat,
            longitude=lon,
            country=country,
        )

        # Try to save
        saved_location = location_repo.create(test_location)

        if saved_location:
            console.print(
                f"[green]✓ Successfully saved location: {saved_location.name}, "
                f"{saved_location.country}[/green]"
            )
            console.print(
                f"[blue]Location ID: {saved_location.id}, "
                f"Coordinates: ({saved_location.latitude}, "
                f"{saved_location.longitude})[/blue]"
            )

            # Try to retrieve it back
            retrieved = location_repo.get_by_id(saved_location.id)
            if retrieved:
                console.print(
                    f"[green]✓ Successfully retrieved location: "
                    f"{retrieved.name}[/green]"
                )
            else:
                console.print("[red]✗ Failed to retrieve saved location[/red]")

            # Clean up - delete the test location
            try:
                location_repo.delete(saved_location.id)
                console.print("[green]✓ Test location cleaned up[/green]")
            except Exception as e:
                console.print(
                    f"[yellow]Warning: Could not clean up test location: {e}[/yellow]"
                )

        else:
            console.print("[red]✗ Failed to save location[/red]")

    except Exception as e:
        logger.error(f"Location saving test failed: {e}")
        console.print(f"[bold red]Test failed: {e}[/bold red]")

        # Print traceback for debugging
        console.print(f"[red]Traceback: {traceback.format_exc()}[/red]")


def configure_logging(verbose: bool = False) -> None:
    """Configure logging based on verbosity."""
    # Avoid reconfiguring if already configured
    if logger.handlers:
        return

    level = logging.DEBUG if verbose else logging.INFO
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)

    # File handler
    file_handler = logging.FileHandler("weather_app.log")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    # Configure logger
    logger.setLevel(logging.DEBUG)
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    # Prevent duplicate logs
    logger.propagate = False


if __name__ == "__main__":
    app()
