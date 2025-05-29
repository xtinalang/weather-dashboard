# Functional Tests

This directory contains functional tests for the Weather Dashboard application, covering both the CLI (Typer) and web UI (Flask) components.

## Overview

The functional tests are organized into two main categories:

### CLI Tests (`cli/`)
- **`test_weather_commands.py`** - Tests for weather-related CLI commands (current, forecast, weather, date)
- **`test_location_commands.py`** - Tests for location management commands (add-location, refresh-location, settings)
- **`test_interactive_mode.py`** - Tests for interactive mode, help system, and general CLI functionality

### Web Tests (`web/`)
- **`test_api_endpoints.py`** - Tests for Flask API endpoints and AJAX functionality
- **`test_form_interactions.py`** - Tests for form interactions and user workflows
- **Existing tests** - `test_index.py`, `test_search.py`, `test_weather.py`, `test_forecast.py`

## Requirements

### CLI Tests
- Python 3.8+
- All project dependencies installed
- Optional: Valid `WEATHER_API_KEY` environment variable for full API testing

### Web Tests
- All CLI requirements
- Playwright for browser automation
- Web server running on localhost:5001

### Installation
```bash
# Install test dependencies
pip install pytest playwright

# Install Playwright browsers
playwright install chromium
```

## Running Tests

### Quick Smoke Tests
Run basic functionality checks:
```bash
python tests/functional/test_runner_functional.py smoke
```

### All Functional Tests
Run the complete functional test suite:
```bash
python tests/functional/test_runner_functional.py all
```

### CLI Tests Only
```bash
python tests/functional/test_runner_functional.py cli
```

### Web Tests Only
```bash
python tests/functional/test_runner_functional.py web
```

### Individual Test Files
Run specific test files with pytest:
```bash
# CLI tests
pytest tests/functional/cli/test_weather_commands.py -v
pytest tests/functional/cli/test_location_commands.py -v
pytest tests/functional/cli/test_interactive_mode.py -v

# Web tests
pytest tests/functional/web/test_api_endpoints.py -v
pytest tests/functional/web/test_form_interactions.py -v
```

## Test Categories

### CLI Functional Tests

#### Weather Commands (`test_weather_commands.py`)
- **Current weather**: `current` command with various units and options
- **Forecasts**: `forecast` command with different day ranges
- **Location-specific weather**: `weather <location>` command
- **Date-specific forecasts**: `date YYYY-MM-DD` command
- **Version info**: `version` command
- **Error handling**: Invalid inputs, missing API keys

#### Location Management (`test_location_commands.py`)
- **Add locations**: `add-location` with coordinates and metadata
- **Refresh locations**: `refresh-location` by city or ID
- **Test locations**: `test-location` with custom or default values
- **Database operations**: `init-db` command
- **Settings management**: `settings` and `set-forecast-days` commands
- **Diagnostics**: `diagnostics` command

#### Interactive & General (`test_interactive_mode.py`)
- **Interactive mode**: Starting, navigation, exiting
- **Help system**: Main help, subcommand help, invalid commands
- **Edge cases**: Empty inputs, special characters, long inputs
- **Environment handling**: Missing API keys, database issues
- **Performance**: Command timeouts, response times

### Web Functional Tests

#### API Endpoints (`test_api_endpoints.py`)
- **Weather API**: `/api/weather/{lat}/{lon}` endpoint testing
- **Response formats**: JSON structure validation
- **Error handling**: Invalid coordinates, API failures
- **AJAX functionality**: Dynamic content updates
- **Security**: CSRF token validation
- **Performance**: Response times, browser compatibility

#### Form Interactions (`test_form_interactions.py`)
- **Form validation**: Empty inputs, special characters
- **User workflows**: Search → location selection → weather display
- **Natural language queries**: Processing various query formats
- **Settings updates**: Unit preferences, forecast days
- **Dynamic content**: Flash messages, loading states
- **Accessibility**: Keyboard navigation, screen reader support
- **Multi-step workflows**: Complex user interactions

## Test Data and Mocking

### Environment Variables
Tests use the following environment variables:
- `WEATHER_API_KEY` - For API testing (optional, tests handle missing keys gracefully)
- `DATABASE_URL` - Automatically set to test database for CLI tests
- `FLASK_PORT` - Set to 5001 for web testing

### Test Data
- **London coordinates**: 51.5074, -0.1278
- **Paris coordinates**: 48.8566, 2.3522
- **Test cities**: London, Paris, New York (used in various tests)
- **Date formats**: YYYY-MM-DD for date command testing

### Mocking Strategy
- **Database**: Uses temporary SQLite database for isolation
- **API calls**: Tests handle both successful responses and API failures
- **Web server**: Starts isolated instance on port 5001
- **Environment**: Temporary environment variables for each test

## Configuration

### Test Configuration (`conftest.py` files)
- **CLI**: Provides fixtures for command execution and environment setup
- **Web**: Provides Playwright browser automation and server configuration

### Pytest Configuration (`pytest.ini`)
- Test discovery patterns
- Output formatting
- Warning filters
- Logging configuration

## Expected Behavior

### Successful Test Run
- CLI tests validate command functionality and error handling
- Web tests verify UI interactions and API responses
- All tests handle missing dependencies gracefully
- Test runner provides clear success/failure reporting

### Handling Failures
- **API failures**: Tests expect graceful error handling, not crashes
- **Missing dependencies**: Tests skip or show appropriate warnings
- **Database issues**: Tests use temporary databases and clean up
- **Network issues**: Tests have reasonable timeouts and retry logic

## Troubleshooting

### Common Issues

1. **Web server fails to start**
   - Check if port 5001 is available
   - Verify Flask dependencies are installed
   - Check for firewall restrictions

2. **CLI tests fail with import errors**
   - Ensure you're in the project root directory
   - Verify all dependencies are installed
   - Check Python path configuration

3. **Playwright browser issues**
   - Run `playwright install chromium`
   - Check for system dependencies on Linux
   - Verify browser permissions

4. **API key related failures**
   - Tests should handle missing API keys gracefully
   - Set `WEATHER_API_KEY` environment variable for full testing
   - Check API key validity and rate limits

### Debug Mode
Run tests with increased verbosity:
```bash
pytest tests/functional/ -v -s --tb=long
```

### Test Coverage
The functional tests cover:
- ✅ All major CLI commands and options
- ✅ Web UI forms and user interactions
- ✅ API endpoints and responses
- ✅ Error handling and edge cases
- ✅ Environment and configuration handling
- ✅ Performance and accessibility basics

## Contributing

When adding new functional tests:

1. **Follow the existing structure** - Use appropriate test classes and naming
2. **Handle failures gracefully** - Don't assume external dependencies work
3. **Use proper fixtures** - Leverage existing setup/teardown code
4. **Document test purpose** - Clear docstrings explaining what's being tested
5. **Test both success and failure** - Cover happy path and error cases
6. **Consider performance** - Use reasonable timeouts and avoid slow operations

## Integration with CI/CD

These functional tests are designed to work in CI/CD environments:
- Minimal external dependencies
- Graceful handling of missing services
- Clear exit codes for automation
- Comprehensive reporting output
- Reasonable execution times
