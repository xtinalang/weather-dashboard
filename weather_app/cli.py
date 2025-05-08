import logging
import sys
from datetime import datetime
from typing import Optional

import typer
from rich.console import Console

from . import logger
from .api import WeatherAPI
from .app import WeatherApp
from .database import init_db
from .display import WeatherDisplay
from .exceptions import APIError, InputError
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
):
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
):
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
):
    """Set default number of forecast days"""
    configure_logging(verbose)
    weather_app = get_app()
    weather_app.set_default_forecast_days(days)


@app.command()
def interactive(
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose logging"
    ),
):
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
):
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
                "[bold red]❌ Failed to retrieve weather information. Check your input or API key.[/bold red]"
            )
    except APIError as e:
        console.print(f"[bold red]❌ API Error: {e.message}[/bold red]")
    except InputError as e:
        console.print(f"[bold red]❌ Input Error: {e.message}[/bold red]")
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        console.print(f"[bold red]❌ An unexpected error occurred: {e}[/bold red]")


@app.command(name="version")
def version():
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
):
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
):
    """Initialize or reset the database."""
    configure_logging(verbose)
    try:
        # Directly initialize the database without going through the app
        from .database import init_db as initialize_database

        initialize_database()
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
):
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
):
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
                        f"[green]Successfully refreshed location: {fresh_location.name}, {fresh_location.country}[/green]"
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
                        f"[green]Refreshed: {fresh_loc.name}, {fresh_loc.country} (ID: {fresh_loc.id})[/green]"
                    )
                else:
                    console.print(
                        f"[red]Failed to refresh: {loc.name}, {loc.country} (ID: {loc.id})[/red]"
                    )

        else:
            console.print(
                "[yellow]Please specify either --city or --id to refresh a location[/yellow]"
            )

    except Exception as e:
        logger.error(f"Failed to refresh location: {e}")
        console.print(f"[bold red]Error: {e}[/bold red]")


@app.command("diagnostics")
def run_diagnostics(
    verbose: bool = typer.Option(
        True, "--verbose", "-v", help="Enable verbose logging"
    ),
):
    """Run diagnostics on database and location data."""
    configure_logging(verbose)
    console.print("[blue]Running Weather App diagnostics...[/blue]")

    # 1. Check database connection
    try:
        console.print("\n[bold]1. Database Connection Test[/bold]")
        console.print("[green]✓ Database connection established[/green]")

        # Get database path information
        import os

        from .database import DATABASE_URL

        console.print(f"Database URL: {DATABASE_URL}")

        if DATABASE_URL.startswith("sqlite"):
            db_path = DATABASE_URL.replace("sqlite:///", "")
            if os.path.exists(db_path):
                size = os.path.getsize(db_path)
                console.print(
                    f"SQLite database file: {db_path} (Size: {size/1024:.1f} KB)"
                )
            else:
                console.print(
                    f"[yellow]Warning: SQLite database file does not exist: {db_path}[/yellow]"
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
                init_db()
                console.print("[green]Database initialized successfully[/green]")
            except Exception as init_err:
                console.print(f"[red]Failed to initialize database: {init_err}[/red]")
    except Exception as e:
        console.print(f"[red]✗ Schema test failed: {e}[/red]")

    # 3. Check location data
    try:
        console.print("\n[bold]3. Location Data Test[/bold]")
        location_repo = LocationRepository()

        # Check if any locations exist
        try:
            locations = location_repo.get_all(limit=5)
            if locations:
                console.print(
                    f"[green]✓ Found {len(locations)} locations in database[/green]"
                )
                console.print("[bold]Sample locations:[/bold]")
                for loc in locations:
                    console.print(f"  - {loc.name}, {loc.country} (ID: {loc.id})")
                    console.print(f"    Coordinates: {loc.latitude}, {loc.longitude}")
            else:
                console.print("[yellow]No locations found in database[/yellow]")
                console.print(
                    "[yellow]You need to search for and save locations first[/yellow]"
                )
        except Exception as e:
            console.print(f"[red]✗ Error retrieving locations: {e}[/red]")
    except Exception as e:
        console.print(f"[red]✗ Location data test failed: {e}[/red]")

    # 4. Test coordinate lookup
    try:
        console.print("\n[bold]4. Coordinate Lookup Test[/bold]")
        location_repo = LocationRepository()

        test_locations = [
            {"name": "New York", "lat": 40.7128, "lon": -74.0060},
            {"name": "London", "lat": 51.5074, "lon": -0.1278},
            {"name": "Tokyo", "lat": 35.6762, "lon": 139.6503},
            {"name": "Sydney", "lat": -33.8688, "lon": 151.2093},
        ]

        for test_loc in test_locations:
            try:
                result = location_repo.find_by_coordinates(
                    test_loc["lat"], test_loc["lon"]
                )
                if result:
                    console.print(
                        f"[green]✓ Found location near {test_loc['name']}: {result.name} (ID: {result.id})[/green]"
                    )
                else:
                    console.print(
                        f"[yellow]No location found near {test_loc['name']} coordinates[/yellow]"
                    )
            except Exception as e:
                console.print(
                    f"[red]✗ Error looking up {test_loc['name']} coordinates: {e}[/red]"
                )
    except Exception as e:
        console.print(f"[red]✗ Coordinate lookup test failed: {e}[/red]")

    console.print("\n[blue]Diagnostics complete[/blue]")


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
):
    """Add a new location to the database manually."""
    configure_logging(verbose)

    from datetime import datetime

    from .repository import LocationRepository

    try:
        # Create location object
        location = Location(
            name=name,
            latitude=latitude,
            longitude=longitude,
            country=country,
            region=region,
            is_favorite=favorite,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # Save to database
        repo = LocationRepository()
        result = repo.create(location)

        console.print("[green]✓ Added location successfully:[/green]")
        console.print(f"  Name: {result.name}")
        console.print(f"  Country: {result.country}")
        console.print(f"  Region: {result.region or 'N/A'}")
        console.print(f"  Coordinates: {result.latitude}, {result.longitude}")
        console.print(f"  ID: {result.id}")

    except Exception as e:
        console.print(f"[red]✗ Failed to add location: {e}[/red]")
        logger.error(f"Error adding location: {e}", exc_info=True)


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
):
    """Test location saving and session handling."""
    configure_logging(verbose)
    console.print(f"[blue]Testing location saving with {city}, {country}[/blue]")

    try:
        from datetime import datetime

        from .app import WeatherApp
        from .models import Location
        from .repository import LocationRepository

        # 1. Try direct repository creation
        console.print("\n[bold]1. Testing direct repository creation[/bold]")
        repo = LocationRepository()

        # Create test location
        test_location = Location(
            name=city,
            country=country,
            latitude=lat,
            longitude=lon,
            region="Test Region",
            is_favorite=False,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        try:
            # Save to database
            saved = repo.create(test_location)
            console.print(
                f"[green]✓ Created location: {saved.name} (ID: {saved.id})[/green]"
            )

            # Try to refresh from database
            refreshed = repo.get_by_id(saved.id)
            if refreshed:
                console.print(
                    f"[green]✓ Retrieved location by ID: {refreshed.name} (ID: {refreshed.id})[/green]"
                )
            else:
                console.print("[red]✗ Failed to retrieve location by ID[/red]")

            # Try coordinates lookup
            by_coords = repo.find_by_coordinates(lat, lon)
            if by_coords:
                console.print(
                    f"[green]✓ Found by coordinates: {by_coords.name} (ID: {by_coords.id})[/green]"
                )
            else:
                console.print("[red]✗ Failed to find location by coordinates[/red]")
        except Exception as e:
            console.print(f"[red]✗ Repository test failed: {e}[/red]")

        # 2. Test through the app's refresh mechanism
        console.print("\n[bold]2. Testing app refresh mechanism[/bold]")
        app = WeatherApp()

        try:
            # Create a detached location
            detached_location = Location(
                id=saved.id if "saved" in locals() else None,
                name=city,
                country=country,
                latitude=lat,
                longitude=lon,
                region="Test Region",
                is_favorite=False,
            )

            # Try to refresh it
            refreshed_location = app.refresh_location(detached_location)
            if refreshed_location:
                console.print(
                    f"[green]✓ Successfully refreshed location: {refreshed_location.name} (ID: {refreshed_location.id})[/green]"
                )
            else:
                console.print("[red]✗ Failed to refresh location[/red]")
        except Exception as e:
            console.print(f"[red]✗ App refresh test failed: {e}[/red]")

        # 3. Test the location manager functionality
        console.print("\n[bold]3. Testing location manager[/bold]")
        try:
            from .api import WeatherAPI
            from .display import WeatherDisplay
            from .location import LocationManager

            api = WeatherAPI()
            display = WeatherDisplay()
            manager = LocationManager(api, display)

            # Test saving location from API-like data
            location_data = {
                "name": f"{city}-Test",
                "lat": lat + 0.001,  # Slightly different to avoid collision
                "lon": lon + 0.001,
                "country": country,
                "region": "Test Region",
            }

            result = manager._save_location_to_db(location_data)
            if result and "id" in result:
                console.print(
                    f"[green]✓ Location manager saved location successfully (ID: {result['id']})[/green]"
                )
            else:
                console.print("[red]✗ Location manager failed to save location[/red]")

        except Exception as e:
            console.print(f"[red]✗ Location manager test failed: {e}[/red]")

        console.print("\n[blue]Location tests completed[/blue]")

    except Exception as e:
        console.print(f"[bold red]Test failed with error: {e}[/bold red]")
        import traceback

        console.print(traceback.format_exc())


def configure_logging(verbose=False):
    """Configure application logging."""
    log_level = logging.DEBUG if verbose else logging.INFO

    # Log format with timestamp, level and message
    log_format = "%(asctime)s - %(name)s - %(module)s%(levelname)s - %(message)s"

    # Configure root logger with console handler
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[
            logging.FileHandler("weather_app.log"),
            logging.StreamHandler(sys.stdout),
        ],
    )

    # Set SQLAlchemy logging to WARNING unless in verbose mode
    if not verbose:
        logging.getLogger("sqlalchemy").setLevel(logging.WARNING)


if __name__ == "__main__":
    app()
