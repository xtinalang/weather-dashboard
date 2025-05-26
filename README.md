# 🌤️ Weather Dashboard

A comprehensive weather application that provides both a command-line interface (CLI) and a web interface for checking weather conditions and forecasts. Built with Python, featuring Typer for CLI functionality and Flask for the web interface.

## ✨ Features

### 🖥️ Command Line Interface (CLI)
- **Interactive mode** for guided weather queries
- **Direct weather lookups** for specific locations
- **Forecast management** with customizable days (1-7 days)
- **Location management** with favorites and search history
- **Unit preferences** (Celsius/Fahrenheit)
- **Database operations** for storing locations and settings
- **Rich terminal output** with emojis and formatting

### 🌐 Web Interface
- **Modern responsive UI** for weather queries
- **Real-time weather data** with current conditions
- **Multi-day forecasts** with detailed information
- **Interactive location search** with autocomplete
- **Favorite locations** for quick access
- **Natural language date queries** (e.g., "weather next Monday")
- **Unit conversion** between Celsius and Fahrenheit
- **Mobile-friendly** responsive design

### 📊 Data Features
- **SQLite database** for persistent storage (Can also use Posgresql)
- **Location caching** for faster repeated queries
- **Weather history** tracking
- **User preferences** storage
- **API integration** with WeatherAPI.com

## 🚀 Installation

### Prerequisites
- Python 3.9 or higher
- WeatherAPI.com API key (free tier available)

### Setup

1. **Clone the repository:**
```bash
git clone <repository-url>
cd weather-dashboard
```

2. **Create and activate virtual environment:**
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -e .
```

4. **Set up environment variables:**
```bash
cp .env-template .env
# Edit .env and add your WeatherAPI.com API key
```

5. **Initialize the database:**
```bash
weather-dashboard init-db
```

## 🛠️ Usage

### Command Line Interface (Typer CLI)

The CLI is built with [Typer](https://typer.tiangolo.com/) and provides multiple commands for weather operations.

#### Basic Commands

```bash
# Interactive mode - guided experience
weather-dashboard interactive

# Get weather for a specific location
weather-dashboard weather "London, UK" --unit F

# Show 7-day forecast
weather-dashboard forecast --days 7 --unit C

# Get weather for a specific date
weather-dashboard date 2024-12-25 --unit F

# Show version
weather-dashboard version

# Initialize/reset database
weather-dashboard init-db
```

#### Advanced Commands

```bash
# Location management
weather-dashboard add-location --name "Paris" --lat 48.8566 --lon 2.3522 --country "France" --favorite

# Refresh location data
weather-dashboard refresh-location --city "London"

# Update settings
weather-dashboard settings --forecast-days 5 --temp-unit C

# Run diagnostics
weather-dashboard diagnostics

# Test location saving
weather-dashboard test-location --city "Tokyo" --country "Japan"
```

#### CLI Options

Most commands support these common options:
- `--unit, -u`: Temperature unit (C for Celsius, F for Fahrenheit)
- `--verbose, -v`: Enable verbose logging
- `--days, -d`: Number of forecast days (1-7, where applicable)

### Web Interface (Flask)

The web interface provides a user-friendly way to access weather data through your browser.

#### Starting the Web Server

```bash
# Method 1: Direct module execution
python -m web

# Method 2: Using the run function
python -c "from web.app import run; run()"
```

The web server will start on `http://localhost:5050` by default.

#### Web Features

1. **Home Page** (`/`):
   - Location search form
   - Favorite locations quick access
   - Unit preference settings
   - Forecast days configuration

2. **Weather Display** (`/weather/{lat}/{lon}`):
   - Current weather conditions
   - Detailed metrics (temperature, humidity, wind, pressure)
   - Weather icons and descriptions

3. **Forecast View** (`/forecast/{lat}/{lon}`):
   - Multi-day weather forecast
   - Daily highs and lows
   - Precipitation chances
   - Wind and humidity information

4. **API Endpoints** (`/api/weather/{lat}/{lon}`):
   - JSON weather data for API consumers
   - Programmatic access to weather information

5. **Natural Language Queries** (`/nl-date-weather`):
   - Human-friendly date expressions
   - Examples: "tomorrow", "next Monday", "in 3 days"

## 🗂️ Project Structure

```
weather-dashboard/
├── weather_app/          # Core application logic
│   ├── cli.py           # Typer CLI commands and routing
│   ├── cli_app.py       # Main WeatherApp orchestration class
│   ├── api.py           # WeatherAPI.com integration
│   ├── models.py        # SQLModel database models
│   ├── repository.py    # Database operations and queries
│   ├── location.py      # Location management and geocoding
│   ├── forecast.py      # Forecast data processing
│   ├── current.py       # Current weather processing
│   ├── display.py       # CLI output formatting and display
│   ├── database.py      # Database initialization and connection
│   ├── exceptions.py    # Custom exception classes
│   └── weather_types.py # Type definitions and constants
├── web/                 # Flask web interface
│   ├── app.py          # Flask application and routes
│   ├── forms.py        # WTForms form definitions
│   ├── helpers.py      # Web-specific helper functions
│   ├── utils.py        # Web utilities and constants
│   ├── templates/      # Jinja2 HTML templates
│   └── static/         # CSS, JavaScript, and images
├── database/           # Database files and migrations
├── tests/             # Test suites for CLI and web
├── logs/              # Application log files
└── pyproject.toml     # Project configuration and dependencies
```

## 🏗️ Architecture

### CLI Architecture (Typer)

The CLI is built using **Typer**, which provides:
- **Type annotations** for automatic argument validation
- **Rich help** generation with beautiful formatting
- **Command grouping** for organized functionality
- **Option parsing** with short and long flags
- **Interactive prompts** when needed

Key CLI components:
- `cli.py`: Main Typer app with command definitions
- `cli_app.py`: Business logic orchestration
- `display.py`: Rich terminal output formatting
- `user_input.py`: Interactive input handling

### Web Architecture (Flask)

The web interface uses **Flask** with:
- **Jinja2 templates** for dynamic HTML generation
- **WTForms** for form handling and validation
- **Flask-WTF** for CSRF protection
- **Responsive CSS** for mobile compatibility

Key web components:
- `app.py`: Flask app with route definitions
- `forms.py`: Form classes for user input
- `templates/`: HTML templates with Jinja2
- `static/`: Frontend assets (CSS, JS, images)

### Shared Components

Both interfaces share:
- **WeatherAPI integration** (`api.py`)
- **Database models** (`models.py`)
- **Data repositories** (`repository.py`)
- **Location management** (`location.py`)
- **Weather processing** (`forecast.py`, `current.py`)

## 🔧 Configuration

### Environment Variables

Create a `.env` file based on `.env-template`:

```bash
# Required
WEATHER_API_KEY=your_weatherapi_com_key_here

# Optional - Web Interface
FLASK_PORT=5050
SECRET_KEY=your-secret-key-for-flask

# Optional - Database
DATABASE_URL=sqlite:///./weather_app.db

# Optional - Logging
LOG_LEVEL=INFO
```

### API Key Setup

1. Sign up at [WeatherAPI.com](https://www.weatherapi.com/)
2. Get your free API key
3. Add it to your `.env` file

## 📝 Development

### Running Tests

```bash
# Run all tests
pytest

# Run CLI tests only
pytest tests/cli_tests/

# Run web tests only
pytest tests/web_tests/

# Run with verbose output
pytest -v
```

### Code Quality

The project uses several tools for code quality:

```bash
# Format code
black .

# Sort imports
isort .

# Lint code
ruff check .

# Type checking
mypy weather_app/ web/
```

### Pre-commit Hooks

Install pre-commit hooks for automatic code quality checks:

```bash
pre-commit install
```

## 🐳 Docker

Run the application in Docker:

```bash
# Build the image
docker build -t weather-dashboard .

# Run the container
docker run -p 5050:5050 -e WEATHER_API_KEY=your_api_key weather-dashboard
```

## 📚 API Reference

### CLI Commands

For detailed CLI command reference, see [CLI_REFERENCE.md](CLI_REFERENCE.md).

### Web Routes

- `GET /` - Home page with search forms
- `POST /search` - Location search
- `GET /weather/{lat}/{lon}` - Weather display
- `GET /forecast/{lat}/{lon}` - Forecast display
- `POST /favorite/{location_id}` - Toggle favorite status
- `GET /api/weather/{lat}/{lon}` - JSON weather API

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [WeatherAPI.com](https://www.weatherapi.com/) for weather data
- [Typer](https://typer.tiangolo.com/) for the excellent CLI framework
- [Flask](https://flask.palletsprojects.com/) for the web framework
- [Rich](https://rich.readthedocs.io/) for beautiful terminal output

## 📞 Support

If you encounter any issues:

1. Check the logs in the `logs/` directory
2. Run diagnostics: `weather-dashboard diagnostics`
3. Check the [Issues](https://github.com/your-repo/weather-dashboard/issues) page
4. Create a new issue with detailed information

---

*Happy weather checking! 🌤️*
