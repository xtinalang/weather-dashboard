# Weather Dashboard CLI Reference

## Command Line Interface

The Weather Dashboard application provides a command-line interface using Typer. This document provides a quick reference for all available commands and options.

## Basic Usage

After installation:
```bash
# Run in interactive mode
weather-dashboard interactive

# Get weather for a specific location
weather-dashboard weather "London" --unit F

# Show version information
weather-dashboard version

# Show help
weather-dashboard --help
```

If running from the source code:
```bash
# Run in interactive mode
python -m weather_app

# Or explicitly call the interactive command
python -m weather_app interactive

# Get weather for a specific location
python -m weather_app weather "New York" --unit C

# Show help
python -m weather_app --help
```

## Available Commands

### Interactive Mode

```bash
weather-dashboard interactive
```

Runs the application in interactive mode, allowing you to:
- Choose temperature units (Celsius or Fahrenheit)
- Search for locations
- View current weather and forecasts
- Navigate through the application menu

### Weather Command

```bash
weather-dashboard weather LOCATION [--unit UNIT]
```

Arguments:
- `LOCATION`: The location to get weather for (city, region, country)

Options:
- `--unit`, `-u`: Temperature unit (C for Celsius, F for Fahrenheit), default is C

Examples:
```bash
weather-dashboard weather "London"
weather-dashboard weather "Tokyo, Japan" --unit F
weather-dashboard weather "New York" -u F
```

### Version Command

```bash
weather-dashboard version
```

Displays the current version of the weather application.

## Implementation Details

The CLI is implemented in `weather_app/cli.py` using the Typer library. The main components are:

1. `app = typer.Typer()` - Creates the Typer application
2. Command functions decorated with `@app.command()`
3. Type annotations and Typer-specific parameter definitions

Entry points are configured in `pyproject.toml` to allow the application to be run as `weather-dashboard` after installation.

## Customization

To add new commands to the CLI:

1. Add new command functions to `weather_app/cli.py`
2. Decorate with `@app.command(name="command_name")`
3. Add proper type annotations and docstrings
4. Implement the command functionality

Example:
```python
@app.command(name="forecast")
def get_forecast(
    location: str = typer.Argument(..., help="Location to get forecast for"),
    days: int = typer.Option(7, "--days", "-d", help="Number of days to forecast")
):
    """Get weather forecast for a specific location."""
    # Implementation here
```
