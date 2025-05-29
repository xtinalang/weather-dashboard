# Unit Tests Organization

This directory contains unit tests for the Weather Dashboard application, organized by component type.

## Directory Structure

```
tests/unit/
├── cli/                    # Unit tests for Typer CLI components
│   ├── test_cli_commands.py    # Tests for CLI commands using typer.testing.CliRunner
│   ├── test_app.py            # Tests for WeatherApp class
│   ├── test_api.py            # Tests for WeatherAPI class
│   ├── test_current.py        # Tests for current weather functionality
│   ├── test_database.py       # Tests for database operations
│   ├── test_location_manager.py # Tests for LocationManager class
│   ├── test_repository.py     # Tests for repository classes
│   ├── tests_emoji.py         # Tests for emoji functionality
│   └── conftest.py            # Test fixtures for CLI tests
├── web/                    # Unit tests for Flask web components
│   ├── test_flask_routes.py   # Tests for Flask routes using test_client
│   ├── test_web_forms.py      # Tests for Flask-WTF forms
│   ├── test_web_helpers.py    # Tests for web helper functions
│   └── conftest.py            # Test fixtures for web tests
└── README.md              # This file
```

## Test Types

### CLI Unit Tests (`tests/unit/cli/`)

These tests focus on the Typer CLI application components:

- **test_cli_commands.py**: Tests actual CLI commands using `typer.testing.CliRunner`
  - Tests command invocation, argument parsing, and output
  - Mocks external dependencies (API, database)
  - Validates command behavior and error handling

- **test_app.py**: Tests the main `WeatherApp` class
  - Tests business logic and application flow
  - Mocks dependencies and external services

- **test_api.py**: Tests the `WeatherAPI` class
  - Tests API interactions and data parsing
  - Mocks HTTP requests and responses

- **Other test files**: Test specific components like database, location management, etc.

### Web Unit Tests (`tests/unit/web/`)

These tests focus on the Flask web application components:

- **test_flask_routes.py**: Tests Flask routes using `app.test_client()`
  - Tests HTTP request/response handling
  - Tests route logic and redirects
  - Tests error handling and edge cases
  - Mocks external dependencies

- **test_web_forms.py**: Tests Flask-WTF forms
  - Tests form validation and data processing
  - Tests form field behavior

- **test_web_helpers.py**: Tests web utility functions
  - Tests helper functions and utilities
  - Tests data formatting and processing

## Running Tests

### Run all unit tests:
```bash
pytest tests/unit/ -v
```

### Run CLI unit tests only:
```bash
pytest tests/unit/cli/ -v
```

### Run web unit tests only:
```bash
pytest tests/unit/web/ -v
```

### Run specific test file:
```bash
pytest tests/unit/cli/test_cli_commands.py -v
pytest tests/unit/web/test_flask_routes.py -v
```

### Run specific test class or method:
```bash
pytest tests/unit/cli/test_cli_commands.py::TestVersionCommand -v
pytest tests/unit/web/test_flask_routes.py::TestIndexRoute::test_index_page_loads -v
```

## Test Coverage

The unit tests cover:

### CLI Components:
- ✅ CLI command invocation and argument parsing
- ✅ Weather data retrieval and display
- ✅ Location management and search
- ✅ Database operations and repositories
- ✅ User input handling and validation
- ✅ Error handling and edge cases

### Web Components:
- ✅ HTTP route handling and responses
- ✅ Form processing and validation
- ✅ Template rendering (basic structure)
- ✅ API endpoints (JSON responses)
- ✅ Error handling and redirects
- ✅ Helper functions and utilities

## Notes

- Tests use mocking extensively to isolate units under test
- External dependencies (API calls, database) are mocked
- Tests focus on behavior rather than implementation details
- Both positive and negative test cases are included
- Error conditions and edge cases are tested

## Functional vs Unit Tests

- **Unit tests** (this directory): Test individual components in isolation
- **Functional tests** (`tests/web_tests/functional/`): Test end-to-end user workflows using Playwright
- **Integration tests** (`tests/web_tests/integration/`): Test component interactions
