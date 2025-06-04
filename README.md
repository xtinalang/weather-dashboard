# 🌤️ Weather Dashboard CLI

A powerful command-line weather application built with Typer that provides current weather, forecasts, and location management with local database storage.

## 📦 Installation

### From PyPI (Recommended)
```bash
pip install weather-dashboard
```

### From Source
```bash
git clone <repository-url>
cd weather-dashboard
pip install -e .
```

## 🚀 Quick Start

1. **Get your API key** from [WeatherAPI.com](https://www.weatherapi.com/)

2. **Set your API key** (optional - can be set via environment variable):
```bash
export WEATHER_API_KEY="your-api-key-here"
```

3. **Initialize the database**:
```bash
weather-dashboard init-db
```

4. **Get current weather**:
```bash
weather-dashboard current
```

## 🛠️ Commands

### Weather Information

#### `current`
Show current weather for a location (interactive mode if no location set)
```bash
weather-dashboard current [OPTIONS]
```
**Options:**
- `--unit, -u`: Temperature unit (C for Celsius, F for Fahrenheit) [default: C]
- `--verbose, -v`: Enable verbose logging

#### `weather <location>`
Get current weather and forecast for a specific location
```bash
weather-dashboard weather "London, UK" --unit F
weather-dashboard weather "New York" --unit C
```

#### `forecast`
Show weather forecast (interactive mode or with options)
```bash
weather-dashboard forecast [OPTIONS]
```
**Options:**
- `--days, -d`: Number of days to forecast (1-7)
- `--unit, -u`: Temperature unit (C/F)
- `--verbose, -v`: Enable verbose logging

#### `date <date>`
Get forecast for a specific date
```bash
weather-dashboard date 2024-12-25 --unit F
weather-dashboard date 2024-01-15
```

### Interactive Mode

#### `interactive`
Start the interactive weather application
```bash
weather-dashboard interactive
```

### Database Management

#### `init-db`
Initialize or reset the database
```bash
weather-dashboard init-db
```

#### `database-info`
Show database location and configuration information
```bash
weather-dashboard database-info
```

### Location Management

#### `add-location`
Add a new location to the database
```bash
weather-dashboard add-location \
  --name "Paris" \
  --lat 48.8566 \
  --lon 2.3522 \
  --country "France" \
  --region "Île-de-France"
```

#### `refresh-location`
Refresh location data in the database
```bash
# Refresh by city name
weather-dashboard refresh-location --city "London"

# Refresh by location ID
weather-dashboard refresh-location --id 1
```

### Settings

#### `settings`
Update application settings
```bash
# Set default forecast days
weather-dashboard settings --forecast-days 5

# Set default temperature unit
weather-dashboard settings --temp-unit F

# Set both
weather-dashboard settings --forecast-days 3 --temp-unit C
```

#### `set-forecast-days`
Set default number of forecast days
```bash
weather-dashboard set-forecast-days --days 7
```

### Utilities

#### `version`
Display the current version
```bash
weather-dashboard version
```

#### `diagnostics`
Run comprehensive diagnostics on database and API connectivity
```bash
weather-dashboard diagnostics
```

#### `test-location`
Test location saving functionality (for debugging)
```bash
weather-dashboard test-location --city "Tokyo" --country "Japan"
```

## ⚙️ Configuration

### Environment Variables

The CLI app supports the following environment variables:

- `WEATHER_API_KEY`: Your WeatherAPI.com API key (required)
- `DATABASE_URL`: Database connection URL (optional, defaults to local SQLite)

### Database Location

By default, the app stores data in:
- **Linux/macOS**: `~/.local/share/weather-dashboard/weather_app.db`
- **Windows**: `%APPDATA%/weather-dashboard/weather_app.db`

Use `weather-dashboard database-info` to see your exact database location.

### Custom Database

You can override the default database location:
```bash
export DATABASE_URL="sqlite:///path/to/your/database.db"
# Or use PostgreSQL
export DATABASE_URL="postgresql://user:password@localhost:5432/weather_db"
```

## 📋 Examples

### Basic Usage
```bash
# Get current weather (interactive mode)
weather-dashboard current

# Get weather for specific location
weather-dashboard weather "Tokyo, Japan"

# Get 5-day forecast in Fahrenheit
weather-dashboard forecast --days 5 --unit F

# Check weather for a future date
weather-dashboard date 2024-02-14 --unit C
```

### Database Management
```bash
# Initialize database
weather-dashboard init-db

# Check database status
weather-dashboard database-info

# Add favorite location
weather-dashboard add-location \
  --name "Home" \
  --lat 40.7128 \
  --lon -74.0060 \
  --country "USA" \
  --region "New York"
```

### Settings Configuration
```bash
# Set preferences
weather-dashboard settings --forecast-days 7 --temp-unit F

# Run diagnostics
weather-dashboard diagnostics
```

## 🐛 Troubleshooting

### Common Issues

**"No API key found"**
- Set your API key: `export WEATHER_API_KEY="your-key"`
- Or create a `.env` file with `WEATHER_API_KEY=your-key`

**"Database connection failed"**
- Run: `weather-dashboard init-db`
- Check database location: `weather-dashboard database-info`

**"Location not found"**
- Try more specific location names: "London, UK" instead of "London"
- Use interactive mode for location search

### Debug Mode
Enable verbose logging for troubleshooting:
```bash
weather-dashboard current --verbose
weather-dashboard diagnostics --verbose
```

### Reset Everything
```bash
# Reset database
weather-dashboard init-db

# Check if everything works
weather-dashboard diagnostics
```

## 🔗 Related

- **Web Interface**: See main README.md for the Flask web application
- **API Documentation**: Check the WeatherAPI.com documentation
- **Source Code**: View the full source code repository

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

**Made with ❤️ using Typer and Rich**
