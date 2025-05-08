# Weather App Tests

This directory contains tests for the Weather App modules and components. The tests are written using pytest and focus on unit testing the application's core functionality.

## Test Structure

- `conftest.py`: Common test fixtures and configuration used across test modules
- `test_api.py`: Tests for the WeatherAPI class and weather data retrieval
- `test_app.py`: Tests for the WeatherApp class and application flow
- `test_database.py`: Tests for the Database class and database operations
- `test_location_manager.py`: Tests for the LocationManager class and location handling
- `test_repository.py`: Tests for repository classes (LocationRepository, SettingsRepository, WeatherRepository)

## Running Tests

### Running All Tests

To run all tests, execute the following command from the project root:

```bash
python -m pytest
```

### Running Specific Test Modules

To run tests from a specific file:

```bash
python -m pytest tests/test_api.py
```

### Running Individual Tests

To run a specific test function:

```bash
python -m pytest tests/test_api.py::test_get_weather_success
```

### Common Pytest Options

- `-v`: Verbose output, shows individual test results
- `-xvs`: Verbose output, stops at first failure, shows prints
- `--pdb`: Drop into debugger on failures
- `--cov=weather_app`: Generate coverage report (requires pytest-cov)

## Test Coverage

The tests cover the following components:

1. **API Module**:
   - WeatherAPI initialization and configuration
   - Weather data retrieval
   - City search functionality
   - Error handling

2. **Database Module**:
   - Database initialization
   - Session management
   - Connection handling
   - SQLite and PostgreSQL support

3. **Repository Layer**:
   - CRUD operations for all models
   - Query functionality
   - Error handling
   - Data validation

4. **Location Management**:
   - Location search and selection
   - Favorite locations
   - Coordinates handling
   - Database integration

5. **Application Core**:
   - Application initialization
   - Main workflow (run method)
   - Interactive mode
   - Forecast handling
   - Command-line interface

## Mocking

The tests use extensive mocking to isolate components and avoid external dependencies:

- External API calls are mocked to avoid network requests
- Database connections use in-memory SQLite for testing
- User input is simulated
- Weather data responses are predefined

## Adding New Tests

When adding new functionality to the app, please follow these guidelines for writing tests:

1. Place tests in the appropriate module based on what's being tested
2. Use descriptive test names that indicate what's being tested
3. Consider creating reusable fixtures in conftest.py
4. Mock external dependencies
5. Test both success and failure paths

## Running Tests with Coverage

To run tests with coverage reporting:

1. Install pytest-cov:
   ```bash
   pip install pytest-cov
   ```

2. Run tests with coverage:
   ```bash
   python -m pytest --cov=weather_app --cov-report=term-missing
   ```

3. For a HTML coverage report:
   ```bash
   python -m pytest --cov=weather_app --cov-report=html
   ```
