# Weather Dashboard

A comprehensive weather application with both a command-line interface (CLI) and web interface. Get current weather conditions and forecasts for any location worldwide.

## Features

### Command Line Interface (CLI)
- Get current weather conditions for any location
- View weather forecasts (1-7 days)
- Support for both Celsius and Fahrenheit
- Rich terminal output with color formatting
- Verbose logging option for debugging

### Web Interface
- User-friendly web dashboard
- Natural language query support (e.g., "What's the weather like in London?")
- Location disambiguation for cities with the same name
- Multiple location selection options
- Favorite locations management
- Support for both current weather and forecasts

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/weather-dashboard.git
cd weather-dashboard
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
uv pip install -e .
```

4. Set up your environment variables:
```bash
export WEATHER_API_KEY=your_api_key_here  # Get from weatherapi.com
```

## Usage

### Command Line Interface

```bash
# Get current weather
weather current "London, UK" --unit C

# Get forecast
weather forecast "New York" --days 5 --unit F

# Show version
weather version

# Show help
weather --help
```

### Web Interface

1. Start the Flask development server:
```bash
flask run
```

2. Open your browser and navigate to `http://localhost:5000`

3. Use the web interface to:
   - Search for locations
   - View current weather
   - Check forecasts
   - Save favorite locations
   - Use natural language queries

## Project Structure

```
weather-dashboard/
├── weather_app/                  # Main package directory
│   ├── __init__.py              # Package initialization
│   ├── cli.py                   # Typer CLI implementation
│   ├── cli_app.py               # CLI application logic
│   ├── api.py                   # Weather API client
│   ├── display.py               # Terminal display formatting
│   ├── current.py               # Current weather handling
│   ├── forecast.py              # Forecast processing
│   ├── location.py              # Location management
│   ├── models.py                # Database models
│   ├── repository.py            # Data access layer
│   ├── database.py              # Database configuration
│   ├── exceptions.py            # Custom exceptions
│   ├── user_input.py            # User input handling
│   ├── weather_types.py         # Type definitions
│   ├── emoji.py                 # Emoji support
│   └── migrate_database.py      # Database migrations
├── web/                         # Web interface
│   ├── __init__.py             # Web package initialization
│   ├── app.py                  # Flask application
│   ├── forms.py                # Form definitions
│   ├── helpers.py              # Helper functions
│   ├── error_handlers.py       # Error handling
│   ├── templates/              # HTML templates
│   │   ├── base.html          # Base template
│   │   ├── index.html         # Home page
│   │   ├── weather.html       # Weather display
│   │   ├── forecast.html      # Forecast display
│   │   ├── search_results.html # Search results
│   │   ├── location_selection.html # Location selection
│   │   └── disambiguate_location.html # Location disambiguation
│   └── static/                 # Static assets
│       ├── css/               # Stylesheets
│       ├── js/                # JavaScript files
│       └── images/            # Image assets
├── tests/                      # Test suite
│   ├── __init__.py            # Test initialization
│   ├── conftest.py            # Test configuration
│   └── unit/                  # Unit tests
│       ├── web/               # Web tests
│       │   ├── test_app.py    # App tests
│       │   ├── test_forms.py  # Form tests
│       │   └── test_helpers.py # Helper tests
│       └── weather_app/       # Core functionality tests
│           ├── test_api.py    # API tests
│           ├── test_cli.py    # CLI tests
│           └── test_location.py # Location tests
├── .env                        # Environment variables
├── .gitignore                 # Git ignore rules
├── pyproject.toml             # Project configuration
├── requirements.txt           # Production dependencies
├── requirements-dev.txt       # Development dependencies
├── README.md                  # This file
└── LICENSE                    # License information
```

## Development

### Running Tests
```bash
pytest
```

### Code Style
This project uses `ruff` for linting and formatting:
```bash
ruff check .
ruff format .
```

## Dependencies

- Python ≥ 3.9
- Typer: CLI interface
- Flask: Web framework
- SQLAlchemy: Database ORM
- Rich: Terminal formatting
- Requests: HTTP client
- WeatherAPI.com account (free tier available)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Weather data provided by [Weather API Provider]
- Geocoding services by [Geocoding Provider]
- Built with Flask and Python

## Support

For support:
- Check the [FAQ](docs/faq.md)
- Submit an issue
- Contact the maintainers

## Roadmap

Future plans include:
- [ ] Additional language support
- [ ] More weather data providers
- [ ] Mobile app version
- [ ] Weather alerts
- [ ] Historical data analysis
