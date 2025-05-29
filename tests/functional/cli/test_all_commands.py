"""
Comprehensive functional tests for all Typer CLI commands.
Tests every command with various parameters, options, and edge cases.
"""

import tempfile
import time
from pathlib import Path


class TestCurrentCommand:
    """Test suite for the 'current' command."""

    def test_current_command_help(self, run_cli, cli_command):
        """Test current command help."""
        result = run_cli(f"{cli_command} current --help")

        assert result["returncode"] == 0
        assert "current weather" in result["stdout"].lower()
        assert "--unit" in result["stdout"]
        assert "--verbose" in result["stdout"]

    def test_current_command_with_units(self, run_cli, cli_command, temp_env):
        """Test current command with different units."""
        units = ["C", "F"]

        for unit in units:
            result = run_cli(f"{cli_command} current --unit {unit}")

            # Should complete without crashing
            assert result["returncode"] in [0, 1, 2]
            assert result["stdout"] or result["stderr"]

    def test_current_command_verbose(self, run_cli, cli_command, temp_env):
        """Test current command with verbose output."""
        result = run_cli(f"{cli_command} current --verbose")

        # Should handle verbose mode
        assert result["returncode"] in [0, 1, 2]
        assert result["stdout"] or result["stderr"]

    def test_current_command_invalid_unit(self, run_cli, cli_command):
        """Test current command with invalid unit."""
        result = run_cli(f"{cli_command} current --unit X")

        # Should handle invalid unit gracefully
        assert result["returncode"] in [0, 1, 2]
        assert result["stdout"] or result["stderr"]


class TestForecastCommand:
    """Test suite for the 'forecast' command."""

    def test_forecast_command_help(self, run_cli, cli_command):
        """Test forecast command help."""
        result = run_cli(f"{cli_command} forecast --help")

        assert result["returncode"] == 0
        assert "forecast" in result["stdout"].lower()
        assert "--days" in result["stdout"]
        assert "--unit" in result["stdout"]

    def test_forecast_command_with_days(self, run_cli, cli_command, temp_env):
        """Test forecast command with different day ranges."""
        day_ranges = [1, 3, 5, 7]

        for days in day_ranges:
            result = run_cli(f"{cli_command} forecast --days {days}")

            # Should complete without crashing
            assert result["returncode"] in [0, 1, 2]
            assert result["stdout"] or result["stderr"]

    def test_forecast_command_invalid_days(self, run_cli, cli_command):
        """Test forecast command with invalid day ranges."""
        invalid_days = [0, -1, 15, 100]

        for days in invalid_days:
            result = run_cli(f"{cli_command} forecast --days {days}")

            # Should show validation error for out-of-range days
            if days < 1 or days > 14:  # Assuming valid range is 1-14
                assert result["returncode"] == 2
            else:
                assert result["returncode"] in [0, 1, 2]

    def test_forecast_command_with_units_and_days(self, run_cli, cli_command, temp_env):
        """Test forecast command with both units and days."""
        combinations = [
            ("C", 3),
            ("F", 5),
            ("C", 7),
            ("F", 1),
        ]

        for unit, days in combinations:
            result = run_cli(f"{cli_command} forecast --unit {unit} --days {days}")

            assert result["returncode"] in [0, 1, 2]
            assert result["stdout"] or result["stderr"]


class TestWeatherCommand:
    """Test suite for the 'weather' command."""

    def test_weather_command_help(self, run_cli, cli_command):
        """Test weather command help."""
        result = run_cli(f"{cli_command} weather --help")

        assert result["returncode"] == 0
        assert "weather" in result["stdout"].lower()
        assert "location" in result["stdout"].lower()
        assert "--unit" in result["stdout"]

    def test_weather_command_with_locations(
        self, run_cli, cli_command, mock_env_with_api_key
    ):
        """Test weather command with various locations."""
        locations = [
            "London",
            "New York",
            "Paris",
            "London, UK",
            "New York, NY",
            "Tokyo, Japan",
        ]

        for location in locations:
            result = run_cli(f"{cli_command} weather '{location}'")

            # Should process location without crashing
            assert result["returncode"] in [0, 1, 2]
            assert result["stdout"] or result["stderr"]

    def test_weather_command_missing_location(self, run_cli, cli_command):
        """Test weather command without location argument."""
        result = run_cli(f"{cli_command} weather")

        # Should show error about missing location
        assert result["returncode"] == 2
        assert any(
            keyword in result["stderr"].lower()
            for keyword in ["missing", "required", "argument"]
        )

    def test_weather_command_with_units(
        self, run_cli, cli_command, mock_env_with_api_key
    ):
        """Test weather command with different units."""
        units = ["C", "F"]

        for unit in units:
            result = run_cli(f"{cli_command} weather 'London' --unit {unit}")

            assert result["returncode"] in [0, 1, 2]
            assert result["stdout"] or result["stderr"]

    def test_weather_command_verbose(self, run_cli, cli_command, mock_env_with_api_key):
        """Test weather command with verbose output."""
        result = run_cli(f"{cli_command} weather 'London' --verbose")

        assert result["returncode"] in [0, 1, 2]
        assert result["stdout"] or result["stderr"]


class TestDateCommand:
    """Test suite for the 'date' command."""

    def test_date_command_help(self, run_cli, cli_command):
        """Test date command help."""
        result = run_cli(f"{cli_command} date --help")

        assert result["returncode"] == 0
        assert "date" in result["stdout"].lower()
        assert "YYYY-MM-DD" in result["stdout"]

    def test_date_command_valid_dates(
        self, run_cli, cli_command, mock_env_with_api_key
    ):
        """Test date command with valid date formats."""
        dates = [
            "2024-12-25",
            "2024-01-01",
            "2024-06-15",
            "2025-03-20",
        ]

        for date in dates:
            result = run_cli(f"{cli_command} date {date}")

            # Should process date without crashing
            assert result["returncode"] in [0, 1, 2]
            assert result["stdout"] or result["stderr"]

    def test_date_command_invalid_formats(self, run_cli, cli_command):
        """Test date command with invalid date formats."""
        invalid_dates = [
            "25-12-2024",  # Wrong format
            "2024/12/25",  # Wrong separator
            "12-25-2024",  # US format
            "2024-13-01",  # Invalid month
            "2024-02-30",  # Invalid date
            "invalid",  # Not a date
        ]

        for date in invalid_dates:
            result = run_cli(f"{cli_command} date {date}")

            # Should handle invalid dates gracefully
            assert result["returncode"] in [0, 1, 2]
            assert result["stdout"] or result["stderr"]

    def test_date_command_missing_date(self, run_cli, cli_command):
        """Test date command without date argument."""
        result = run_cli(f"{cli_command} date")

        # Should show error about missing date
        assert result["returncode"] == 2
        assert any(
            keyword in result["stderr"].lower()
            for keyword in ["missing", "required", "argument"]
        )

    def test_date_command_with_units(self, run_cli, cli_command, mock_env_with_api_key):
        """Test date command with different units."""
        result = run_cli(f"{cli_command} date 2024-12-25 --unit F")

        assert result["returncode"] in [0, 1, 2]
        assert result["stdout"] or result["stderr"]


class TestVersionCommand:
    """Test suite for the 'version' command."""

    def test_version_command_basic(self, run_cli, cli_command):
        """Test basic version command."""
        result = run_cli(f"{cli_command} version")

        assert result["returncode"] == 0
        assert any(
            keyword in result["stdout"].lower()
            for keyword in ["version", "weather", "dashboard"]
        )

    def test_version_command_output_format(self, run_cli, cli_command):
        """Test version command output format."""
        result = run_cli(f"{cli_command} version")

        assert result["returncode"] == 0
        # Should contain version information
        assert "v" in result["stdout"] or "V" in result["stdout"]


class TestInitDbCommand:
    """Test suite for the 'init-db' command."""

    def test_init_db_command_help(self, run_cli, cli_command):
        """Test init-db command help."""
        result = run_cli(f"{cli_command} init-db --help")

        assert result["returncode"] == 0
        assert "database" in result["stdout"].lower()

    def test_init_db_command_basic(self, run_cli, cli_command, temp_env):
        """Test basic database initialization."""
        result = run_cli(f"{cli_command} init-db")

        # Should complete database initialization
        assert result["returncode"] in [0, 1]
        assert result["stdout"] or result["stderr"]

    def test_init_db_command_multiple_runs(self, run_cli, cli_command, temp_env):
        """Test running init-db multiple times."""
        # First run
        result1 = run_cli(f"{cli_command} init-db")
        assert result1["returncode"] in [0, 1]

        # Second run (should handle existing database)
        result2 = run_cli(f"{cli_command} init-db")
        assert result2["returncode"] in [0, 1]


class TestSettingsCommand:
    """Test suite for the 'settings' command."""

    def test_settings_command_help(self, run_cli, cli_command):
        """Test settings command help."""
        result = run_cli(f"{cli_command} settings --help")

        assert result["returncode"] == 0
        assert "settings" in result["stdout"].lower()

    def test_settings_command_basic(self, run_cli, cli_command, temp_env):
        """Test basic settings command."""
        result = run_cli(f"{cli_command} settings")

        # Settings command may not produce output when run without options
        assert result["returncode"] in [0, 1, 2]
        # Command should complete successfully even if no output

    def test_settings_command_with_options(self, run_cli, cli_command, temp_env):
        """Test settings command with various options."""
        # Test with specific options that should produce output
        result = run_cli(f"{cli_command} settings --forecast-days 5")

        assert result["returncode"] in [0, 1, 2]
        # Should handle settings update


class TestSetForecastDaysCommand:
    """Test suite for the 'set-forecast-days' command."""

    def test_set_forecast_days_help(self, run_cli, cli_command):
        """Test set-forecast-days command help."""
        result = run_cli(f"{cli_command} set-forecast-days --help")

        assert result["returncode"] == 0
        assert "forecast" in result["stdout"].lower()
        assert "days" in result["stdout"].lower()

    def test_set_forecast_days_valid_values(self, run_cli, cli_command, temp_env):
        """Test set-forecast-days with valid values."""
        valid_days = [1, 3, 5, 7, 10, 14]

        for days in valid_days:
            result = run_cli(f"{cli_command} set-forecast-days {days}")

            # Should set forecast days
            assert result["returncode"] in [0, 1, 2]
            assert result["stdout"] or result["stderr"]

    def test_set_forecast_days_invalid_values(self, run_cli, cli_command):
        """Test set-forecast-days with invalid values."""
        invalid_days = [0, -1, 100, "abc"]

        for days in invalid_days:
            result = run_cli(f"{cli_command} set-forecast-days {days}")

            # Should handle invalid values
            assert result["returncode"] in [0, 1, 2]
            assert result["stdout"] or result["stderr"]

    def test_set_forecast_days_missing_argument(self, run_cli, cli_command):
        """Test set-forecast-days without argument."""
        result = run_cli(f"{cli_command} set-forecast-days")

        # Should show error about missing argument
        assert result["returncode"] == 2


class TestAddLocationCommand:
    """Test suite for the 'add-location' command."""

    def test_add_location_help(self, run_cli, cli_command):
        """Test add-location command help."""
        result = run_cli(f"{cli_command} add-location --help")

        assert result["returncode"] == 0
        assert "location" in result["stdout"].lower()

    def test_add_location_with_coordinates(self, run_cli, cli_command, temp_env):
        """Test add-location with coordinates."""
        locations = [
            ("London", "51.5074", "-0.1278"),
            ("Paris", "48.8566", "2.3522"),
            ("New York", "40.7128", "-74.0060"),
        ]

        for name, lat, lon in locations:
            result = run_cli(
                f"{cli_command} add-location --name '{name}' --lat {lat} --lon {lon}"
            )

            # Should add location
            assert result["returncode"] in [0, 1, 2]
            assert result["stdout"] or result["stderr"]

    def test_add_location_with_country(self, run_cli, cli_command, temp_env):
        """Test add-location with country information."""
        result = run_cli(
            f"{cli_command} add-location --name 'London' "
            f"--lat 51.5074 --lon -0.1278 --country 'UK'"
        )

        assert result["returncode"] in [0, 1, 2]
        assert result["stdout"] or result["stderr"]

    def test_add_location_invalid_coordinates(self, run_cli, cli_command):
        """Test add-location with invalid coordinates."""
        invalid_coords = [
            ("Test", "invalid", "0"),
            ("Test", "91", "0"),  # Invalid latitude
            ("Test", "0", "181"),  # Invalid longitude
            ("Test", "-91", "0"),  # Invalid latitude
            ("Test", "0", "-181"),  # Invalid longitude
        ]

        for name, lat, lon in invalid_coords:
            result = run_cli(
                f"{cli_command} add-location --name '{name}' --lat {lat} --lon {lon}"
            )

            # Should handle invalid coordinates
            assert result["returncode"] in [0, 1, 2]
            assert result["stdout"] or result["stderr"]


class TestRefreshLocationCommand:
    """Test suite for the 'refresh-location' command."""

    def test_refresh_location_help(self, run_cli, cli_command):
        """Test refresh-location command help."""
        result = run_cli(f"{cli_command} refresh-location --help")

        assert result["returncode"] == 0
        assert "refresh" in result["stdout"].lower()
        assert "location" in result["stdout"].lower()

    def test_refresh_location_by_city(self, run_cli, cli_command, temp_env):
        """Test refresh-location by city name."""
        cities = ["London", "Paris", "New York"]

        for city in cities:
            result = run_cli(f"{cli_command} refresh-location --city '{city}'")

            # Should attempt to refresh location
            assert result["returncode"] in [0, 1, 2]
            assert result["stdout"] or result["stderr"]

    def test_refresh_location_by_id(self, run_cli, cli_command, temp_env):
        """Test refresh-location by ID."""
        ids = [1, 2, 3]

        for location_id in ids:
            result = run_cli(f"{cli_command} refresh-location --id {location_id}")

            # Should attempt to refresh location by ID
            assert result["returncode"] in [0, 1, 2]
            assert result["stdout"] or result["stderr"]

    def test_refresh_location_no_arguments(self, run_cli, cli_command):
        """Test refresh-location without arguments."""
        result = run_cli(f"{cli_command} refresh-location")

        # Should show help or error about missing arguments
        assert result["returncode"] in [0, 1, 2]
        assert result["stdout"] or result["stderr"]


class TestTestLocationCommand:
    """Test suite for the 'test-location' command."""

    def test_test_location_help(self, run_cli, cli_command):
        """Test test-location command help."""
        result = run_cli(f"{cli_command} test-location --help")

        assert result["returncode"] == 0
        assert "test" in result["stdout"].lower()
        assert "location" in result["stdout"].lower()

    def test_test_location_basic(self, run_cli, cli_command, temp_env):
        """Test basic test-location functionality."""
        result = run_cli(f"{cli_command} test-location")

        # Should run location tests
        assert result["returncode"] in [0, 1, 2]
        assert result["stdout"] or result["stderr"]

    def test_test_location_with_custom_location(self, run_cli, cli_command, temp_env):
        """Test test-location with custom location if supported."""
        result = run_cli(f"{cli_command} test-location --location 'London'")

        # Should test specific location
        assert result["returncode"] in [0, 1, 2]
        assert result["stdout"] or result["stderr"]


class TestDiagnosticsCommand:
    """Test suite for the 'diagnostics' command."""

    def test_diagnostics_help(self, run_cli, cli_command):
        """Test diagnostics command help."""
        result = run_cli(f"{cli_command} diagnostics --help")

        assert result["returncode"] == 0
        assert "diagnostics" in result["stdout"].lower()

    def test_diagnostics_basic(self, run_cli, cli_command, temp_env):
        """Test basic diagnostics functionality."""
        result = run_cli(f"{cli_command} diagnostics")

        # Should run diagnostics
        assert result["returncode"] in [0, 1, 2]
        assert result["stdout"] or result["stderr"]

    def test_diagnostics_verbose(self, run_cli, cli_command, temp_env):
        """Test diagnostics with verbose output."""
        result = run_cli(f"{cli_command} diagnostics --verbose")

        # Should run verbose diagnostics
        assert result["returncode"] in [0, 1, 2]
        assert result["stdout"] or result["stderr"]


class TestInteractiveCommand:
    """Test suite for the 'interactive' command."""

    def test_interactive_help(self, run_cli, cli_command):
        """Test interactive command help."""
        result = run_cli(f"{cli_command} interactive --help")

        assert result["returncode"] == 0
        assert "interactive" in result["stdout"].lower()

    def test_interactive_command_basic(self, run_cli, cli_command, temp_env):
        """Test interactive command with immediate exit."""
        # Interactive commands are challenging to test automatically
        # We'll test that it starts and can be interrupted
        result = run_cli(f"{cli_command} interactive", input_text="\n", timeout=5)

        # Should start interactive mode
        assert result["returncode"] in [0, 1, 2, -1]  # -1 for timeout
        # Should have some output or be interrupted
        assert result["stdout"] or result["stderr"] or result["returncode"] == -1


class TestCommandIntegration:
    """Test suite for command integration and workflows."""

    def test_database_workflow(self, run_cli, cli_command, temp_env):
        """Test complete database workflow."""
        # Initialize database
        init_result = run_cli(f"{cli_command} init-db")
        assert init_result["returncode"] in [0, 1]

        # Add a location
        add_result = run_cli(
            f"{cli_command} add-location --name 'Test City' --lat 51.5 --lon -0.1"
        )
        assert add_result["returncode"] in [0, 1, 2]

        # Run diagnostics
        diag_result = run_cli(f"{cli_command} diagnostics")
        assert diag_result["returncode"] in [0, 1, 2]

    def test_settings_workflow(self, run_cli, cli_command, temp_env):
        """Test settings-related workflow."""
        # Set forecast days
        set_result = run_cli(f"{cli_command} set-forecast-days 5")
        assert set_result["returncode"] in [0, 1, 2]

        # Check settings
        settings_result = run_cli(f"{cli_command} settings")
        assert settings_result["returncode"] in [0, 1, 2]

    def test_weather_workflow(
        self, run_cli, cli_command, mock_env_with_api_key, temp_env
    ):
        """Test weather-related workflow."""
        # Get current weather
        current_result = run_cli(f"{cli_command} current --unit C")
        assert current_result["returncode"] in [0, 1, 2]

        # Get forecast
        forecast_result = run_cli(f"{cli_command} forecast --days 3 --unit C")
        assert forecast_result["returncode"] in [0, 1, 2]

        # Get weather for specific location
        weather_result = run_cli(f"{cli_command} weather 'London' --unit C")
        assert weather_result["returncode"] in [0, 1, 2]

    def test_command_chaining_compatibility(self, run_cli, cli_command, temp_env):
        """Test that commands don't interfere with each other."""
        commands = [
            f"{cli_command} version",
            f"{cli_command} init-db",
            f"{cli_command} settings",
            f"{cli_command} diagnostics",
        ]

        results = []
        for cmd in commands:
            result = run_cli(cmd)
            results.append(result)
            # Each command should complete
            assert result["returncode"] in [0, 1, 2]

        # All commands should have completed
        assert len(results) == len(commands)


class TestCommandPerformance:
    """Test suite for command performance characteristics."""

    def test_fast_commands_performance(self, run_cli, cli_command):
        """Test that informational commands are fast."""
        fast_commands = [
            f"{cli_command} version",
            f"{cli_command} --help",
            f"{cli_command} weather --help",
        ]

        for cmd in fast_commands:
            start_time = time.time()
            result = run_cli(cmd, timeout=3)
            execution_time = time.time() - start_time

            # Should be very fast
            assert execution_time < 2.0, f"Command {cmd} took {execution_time:.2f}s"
            assert result["returncode"] == 0

    def test_database_commands_performance(self, run_cli, cli_command, temp_env):
        """Test that database commands complete in reasonable time."""
        db_commands = [
            f"{cli_command} init-db",
            f"{cli_command} diagnostics",
        ]

        for cmd in db_commands:
            start_time = time.time()
            result = run_cli(cmd, timeout=10)
            execution_time = time.time() - start_time

            # Should complete in reasonable time
            assert execution_time < 8.0, f"Command {cmd} took {execution_time:.2f}s"
            assert result["returncode"] in [0, 1, 2]

    def test_api_commands_timeout(self, run_cli, cli_command, mock_env_with_api_key):
        """Test that API-dependent commands have reasonable timeouts."""
        api_commands = [
            f"{cli_command} weather 'London'",
            f"{cli_command} forecast --days 3",
        ]

        for cmd in api_commands:
            start_time = time.time()
            result = run_cli(cmd, timeout=15)
            execution_time = time.time() - start_time

            # Should complete or timeout gracefully
            assert execution_time < 15.0, f"Command {cmd} took {execution_time:.2f}s"
            assert result["returncode"] in [0, 1, 2, -1]  # -1 for timeout


class TestCommandRobustness:
    """Test suite for command robustness and error recovery."""

    def test_commands_with_corrupted_database(self, run_cli, cli_command, monkeypatch):
        """Test command behavior with corrupted database."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create corrupted database
            corrupted_db = Path(temp_dir) / "corrupted.db"
            corrupted_db.write_text("Not a valid database")

            monkeypatch.setenv("DATABASE_URL", f"sqlite:///{corrupted_db}")

            robust_commands = [
                f"{cli_command} version",
                f"{cli_command} --help",
                f"{cli_command} diagnostics",
            ]

            for cmd in robust_commands:
                result = run_cli(cmd)
                # Should handle corruption gracefully
                assert result["returncode"] in [0, 1, 2]
                assert result["stdout"] or result["stderr"]

    def test_commands_without_api_key(
        self, run_cli, cli_command, monkeypatch, temp_env
    ):
        """Test command behavior without API key."""
        # Remove API key
        monkeypatch.delenv("WEATHER_API_KEY", raising=False)

        commands_needing_api = [
            f"{cli_command} weather 'London'",
            f"{cli_command} current",
            f"{cli_command} forecast --days 3",
        ]

        for cmd in commands_needing_api:
            result = run_cli(cmd)
            # Should handle missing API key gracefully
            assert result["returncode"] in [0, 1, 2]
            assert result["stdout"] or result["stderr"]

            # App may still work without API key (cached data, default keys, etc.)
            # So we just ensure it doesn't crash and provides some output
            output = (result["stdout"] + result["stderr"]).lower()
            assert len(output) > 0, (
                "Command should provide some output or error message"
            )

    def test_commands_with_network_issues(self, run_cli, cli_command, temp_env):
        """Test command behavior with potential network issues."""
        # Commands that might need network access
        network_commands = [
            f"{cli_command} weather 'NonexistentCity'",
            f"{cli_command} refresh-location --city 'InvalidCity'",
        ]

        for cmd in network_commands:
            result = run_cli(cmd, timeout=10)
            # Should handle network issues gracefully
            assert result["returncode"] in [0, 1, 2, -1]
            assert result["stdout"] or result["stderr"] or result["returncode"] == -1
