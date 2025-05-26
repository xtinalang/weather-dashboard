# Weather Dashboard - Playwright Tests

Comprehensive Playwright test suite for the Weather Dashboard Flask application, organized by template for easy navigation and testing.

## 📁 Test Organization

### Test Files Structure
```
web_tests/
├── test_index.py          # Homepage tests (index.html)
├── test_weather.py        # Weather page tests (weather.html)
├── test_forecast.py       # Forecast page tests (forecast.html)
├── test_search.py         # Search functionality tests
├── test_integration.py    # End-to-end integration tests
├── test_runner.py         # CLI test runner
├── conftest.py           # Pytest configuration & fixtures
└── README.md             # This file
```

### Test Coverage by Template

#### 🏠 **test_index.py** - Homepage Tests
- Page loading and title verification
- Natural language query form testing
- Location search form functionality
- Forecast form with day selection
- Quick links for popular cities
- Favorites section display
- Responsive layout testing
- CSRF token validation
- Form placeholder verification

#### 🌤️ **test_weather.py** - Weather Page Tests
- Weather data display and formatting
- Location information presentation
- Temperature and condition display
- Weather details (humidity, wind, pressure, UV)
- Navigation links functionality
- Unit conversion (°C ↔ °F)
- Favorites button interaction
- Weather icons and timestamps
- Error handling for invalid coordinates
- Mobile responsive design

#### 📅 **test_forecast.py** - Forecast Page Tests
- Forecast days selection (1, 3, 5, 7 days)
- Multi-day weather display
- Forecast day structure validation
- Temperature format verification
- Weather details for each day
- Navigation between forecast periods
- Unit conversion persistence
- Forecast form interactions
- Date formatting verification
- Responsive forecast layout

#### 🔍 **test_search.py** - Search & Natural Language Tests
- Location search functionality
- Multiple search result handling
- Invalid location error handling
- Natural language query processing
- Date-specific weather requests ("today", "tomorrow")
- International character support
- Case-insensitive search testing
- Coordinate-based search
- Search result navigation flows

#### 🔗 **test_integration.py** - End-to-End Tests
- Complete user workflow testing
- Cross-template navigation
- Unit preference persistence
- Favorites functionality across pages
- Error handling and recovery
- Responsive behavior validation
- Form validation across templates
- Data persistence testing

## 🚀 Quick Start

### Prerequisites
```bash
# Install dependencies (from project root)
pip install -r requirements.txt

# Install Playwright browsers
python -m playwright install chromium
```

### Running Tests

#### Using the Test Runner (Recommended)
```bash
# Run all tests
python test_runner.py

# Run specific template tests
python test_runner.py --template weather
python test_runner.py --template forecast
python test_runner.py --template index weather  # Multiple templates

# Run with browser visible for debugging
python test_runner.py --headed --verbose

# Run with different browser
python test_runner.py --browser firefox

# Run with parallel workers (requires pytest-xdist)
python test_runner.py --workers 4
```

#### Direct Pytest Execution
```bash
# Run all tests
python -m pytest

# Run specific test file
python -m pytest test_weather.py -v

# Run with browser visible
python -m pytest --headed

# Run specific test
python -m pytest test_weather.py::TestWeatherPage::test_weather_page_loads_with_valid_coordinates
```

## 🎯 Test Features

### Real Weather Data Testing
- Tests use actual coordinates (London: 51.5074, -0.1278)
- Validates real API responses and data formatting
- Tests handle live weather service interactions

### Responsive Design Testing
- **Desktop**: 1200x800 viewport
- **Tablet**: 768x1024 viewport
- **Mobile**: 375x667 viewport
- Validates layout adaptation across screen sizes

### Unit Conversion Testing
- Celsius to Fahrenheit conversion
- Fahrenheit to Celsius conversion
- Unit preference persistence across pages
- Temperature format validation

### Error Handling
- Invalid coordinate handling
- Non-existent location testing
- API timeout scenarios
- Network error simulation
- Graceful error recovery validation

### Form Testing
- CSRF token validation
- Input field validation
- Form submission workflows
- Empty form handling
- International character support

## 🛠️ Test Configuration

### Browser Configuration (conftest.py)
```python
# Default browser: Chromium
# Headless mode: True (unless --headed)
# Timeout: 30 seconds
# Viewport: 1280x720
```

### Test Data
- **London**: 51.5074, -0.1278 (primary test location)
- **Weather API**: Live WeatherAPI.com integration
- **Test queries**: "London weather today", "Paris tomorrow"

## 📊 Running Specific Test Scenarios

### Template-Specific Testing
```bash
# Homepage functionality
python test_runner.py --template index

# Weather page features
python test_runner.py --template weather

# Forecast functionality
python test_runner.py --template forecast

# Search and NL queries
python test_runner.py --template search

# End-to-end workflows
python test_runner.py --template integration
```

### Development Testing
```bash
# Quick smoke test
python test_runner.py --template index weather --verbose

# Debug mode with browser visible
python test_runner.py --template weather --headed --verbose

# Fast parallel execution
python test_runner.py --workers 3 --timeout 120
```

### CI/CD Testing
```bash
# Headless with retries
python test_runner.py --retry --timeout 300

# Specific browser testing
python test_runner.py --browser firefox --verbose
```

## 🔧 Debugging Tests

### Visual Debugging
```bash
# Run with browser visible
python test_runner.py --headed

# Slow down execution for observation
python -m pytest --headed --slowmo 1000 test_weather.py
```

### Verbose Output
```bash
# Detailed test output
python test_runner.py --verbose

# Pytest verbose mode
python -m pytest -v -s test_weather.py
```

### Screenshot on Failure
```python
# Add to test for debugging
page.screenshot(path="debug_screenshot.png")
```

## 📈 Test Results & Reporting

### Exit Codes
- `0`: All tests passed
- `1`: Test failures or errors
- `2`: User interruption

### Test Output Format
```
🧪 Weather Dashboard Playwright Tests
============================================================
📁 Templates: weather, forecast
🌐 Browser: chromium
👁️  Mode: headless
📝 Verbosity: verbose
⏱️  Timeout: 300s
============================================================
🚀 Running command: python -m pytest test_weather.py test_forecast.py -v
```

## 🔍 Troubleshooting

### Common Issues

#### Browser Installation
```bash
# If browsers not found
python -m playwright install chromium
```

#### Port Conflicts
```bash
# If Flask app not running on 5001
# Update base URL in tests or start Flask on correct port
python app.py  # Should run on localhost:5001
```

#### Timeout Issues
```bash
# Increase timeout for slow systems
python test_runner.py --timeout 600
```

#### Test File Not Found
```bash
# Verify test files exist
ls test_*.py

# Run from correct directory
cd web_tests/
python test_runner.py
```

### Test Environment
- **OS**: Compatible with Windows, macOS, Linux
- **Python**: 3.8+ required
- **Flask App**: Must be running on localhost:5001
- **Network**: Internet required for weather API calls

## 📚 Additional Resources

- [Playwright Documentation](https://playwright.dev/python/)
- [Pytest Documentation](https://docs.pytest.org/)
- [Weather API Documentation](https://www.weatherapi.com/docs/)

---

**Happy Testing! 🎭✨**
