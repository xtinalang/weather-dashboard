# Weather Dashboard

A sophisticated weather application that combines natural language processing with weather data to provide an intuitive way to check weather conditions and forecasts.

## Features

- 🗣 Natural Language Queries: Ask about weather in plain English
- 🌍 Smart Location Handling: Automatic disambiguation of location names
- 🌡 Flexible Units: Support for both Celsius and Fahrenheit
- 📅 Date Intelligence: Understanding of relative dates ("tomorrow", "next weekend", etc.)
- 📊 Comprehensive Data: Detailed weather metrics including temperature, humidity, wind, and more
- 🔍 Location Memory: Save and manage favorite locations
- 📱 Responsive Design: Works on desktop and mobile devices

## Quick Start

1. Clone the repository:
```bash
git clone https://github.com/yourusername/weather-dashboard.git
cd weather-dashboard
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
export FLASK_DEBUG=1  # For development
export FLASK_PORT=5001
export SECRET_KEY="your-secret-key"
```

4. Run the application:
```bash
python -m web.app
```

5. Visit `http://localhost:5001` in your browser

## Project Structure

```
weather-dashboard/
├── web/                    # Web application package
│   ├── app.py             # Flask application
│   ├── forms.py           # Form definitions
│   ├── helpers.py         # Helper functions
│   ├── error_handlers.py  # Error management
│   └── templates/         # HTML templates
├── weather_app/           # Core weather functionality
│   ├── api.py            # Weather API integration
│   ├── current.py        # Current weather handling
│   ├── forecast.py       # Forecast processing
│   └── location.py       # Location management
├── tests/                 # Test suite
│   ├── unit/             # Unit tests
│   ├── functional/       # Functional tests
│   └── integration/      # Integration tests
├── experiments/          # Experimental features
├── docs/                 # Documentation
└── logs/                 # Application logs
```

## Usage Examples

### Natural Language Queries
```python
# Ask about weather naturally
"What's the weather like in Portland tomorrow?"
"Will it rain in London next weekend?"
"Show me the forecast for Paris this week"
```

### Location Disambiguation
```python
# Handles ambiguous locations
"Weather in Cambridge"  # Prompts: UK or MA?
"Portland weather"      # Prompts: OR or ME?
```

### Date Processing
```python
# Understands various date formats
"tomorrow"
"this weekend"
"next Monday"
"next week"
```

## Development

### Setting Up Development Environment

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

2. Install development dependencies:
```bash
pip install -r requirements-dev.txt
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test category
pytest tests/unit/ #still working these
pytest tests/functional/ #still working these
pytest tests/integration/ #still working these

# Run with coverage
pytest --cov=web --cov=weather_app tests/
```

### Code Style

```bash
# Check style
flake8 web/ weather_app/

# Format code
black web/ weather_app/
```

## API Documentation

The application integrates with:
- Weather API for current conditions and forecasts
- Geocoding API for location resolution
- Reverse geocoding for coordinate validation

Detailed API documentation can be found in `docs/api.md`

## Configuration

Key configuration options:
- `FLASK_DEBUG`: Enable/disable debug mode
- `FLASK_PORT`: Application port (default: 5001)
- `SECRET_KEY`: Flask secret key
- `WEATHER_API_KEY`: Weather service API key
- `LOG_LEVEL`: Logging level (default: INFO)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

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
