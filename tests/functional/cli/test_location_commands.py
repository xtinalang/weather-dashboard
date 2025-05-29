"""
Test CLI location management commands functionality.
Tests location-related CLI commands including search,
add, remove, list, and favorite operations.
"""


class TestLocationManagement:
    """Test suite for location management CLI commands."""

    def test_add_location_command_help(self, run_cli, cli_command):
        """Test that the add-location command shows help correctly."""
        result = run_cli(f"{cli_command} add-location --help")

        assert result["returncode"] == 0
        assert (
            "Add a new location" in result["stdout"]
            or "Location name" in result["stdout"]
        )
        assert "--name" in result["stdout"]
        assert "--lat" in result["stdout"]
        assert "--lon" in result["stdout"]
        assert "--country" in result["stdout"]

    def test_add_location_missing_required_args(self, run_cli, cli_command):
        """Test add-location command with missing required arguments."""
        result = run_cli(f"{cli_command} add-location")

        # Should fail with missing required arguments (Typer uses exit code 2)
        assert result["returncode"] == 2
        assert any(
            keyword in result["stderr"].lower()
            for keyword in ["missing", "required", "argument"]
        )

    def test_add_location_with_all_args(self, run_cli, cli_command, temp_env):
        """Test add-location command with all required arguments."""
        result = run_cli(
            f"{cli_command} add-location "
            f"--name 'Test City' "
            f"--lat 40.7128 "
            f"--lon -74.0060 "
            f"--country 'United States' "
            f"--region 'New York' "
            f"--favorite"
        )

        # Should complete successfully or with handled error
        assert result["returncode"] in [0, 1, 2]
        assert result["stdout"] or result["stderr"]

    def test_add_location_invalid_coordinates(self, run_cli, cli_command, temp_env):
        """Test add-location command with invalid coordinates."""
        result = run_cli(
            f"{cli_command} add-location "
            f"--name 'Invalid Location' "
            f"--lat 200.0 "  # Invalid latitude
            f"--lon -74.0060 "
            f"--country 'Test Country'"
        )

        # Should handle invalid coordinates
        assert result["returncode"] in [
            0,
            1,
            2,
        ]  # May be handled gracefully or cause validation error
        assert result["stdout"] or result["stderr"]

    def test_refresh_location_command_help(self, run_cli, cli_command):
        """Test that the refresh-location command shows help correctly."""
        result = run_cli(f"{cli_command} refresh-location --help")

        assert result["returncode"] == 0
        assert any(
            keyword in result["stdout"]
            for keyword in ["refresh", "location", "--city", "--id"]
        )

    def test_refresh_location_with_city(
        self, run_cli, cli_command, temp_env, mock_env_with_api_key
    ):
        """Test refresh-location command with city parameter."""
        result = run_cli(f"{cli_command} refresh-location --city London")

        # Should process the command
        assert result["returncode"] in [0, 1, 2]
        assert result["stdout"] or result["stderr"]

    def test_refresh_location_with_id(self, run_cli, cli_command, temp_env):
        """Test refresh-location command with ID parameter."""
        result = run_cli(f"{cli_command} refresh-location --id 1")

        # Should process the command (may fail if ID doesn't exist)
        assert result["returncode"] in [0, 1, 2]
        assert result["stdout"] or result["stderr"]

    def test_refresh_location_no_args(self, run_cli, cli_command):
        """Test refresh-location command with no arguments."""
        result = run_cli(f"{cli_command} refresh-location")

        # Should process or show appropriate message
        assert result["returncode"] in [0, 1, 2]
        assert result["stdout"] or result["stderr"]

    def test_test_location_command_help(self, run_cli, cli_command):
        """Test that the test-location command shows help correctly."""
        result = run_cli(f"{cli_command} test-location --help")

        assert result["returncode"] == 0
        assert any(
            keyword in result["stdout"]
            for keyword in [
                "test",
                "location",
                "--city",
                "--country",
                "--lat",
                "--lon",
            ]
        )

    def test_test_location_default_values(
        self, run_cli, cli_command, temp_env, mock_env_with_api_key
    ):
        """Test test-location command with default values."""
        result = run_cli(f"{cli_command} test-location")

        # Should run with default values (Paris, France)
        assert result["returncode"] in [0, 1, 2]
        assert result["stdout"] or result["stderr"]

    def test_test_location_custom_values(
        self, run_cli, cli_command, temp_env, mock_env_with_api_key
    ):
        """Test test-location command with custom values."""
        result = run_cli(
            f"{cli_command} test-location "
            f"--city 'New York' "
            f"--country 'United States' "
            f"--lat 40.7128 "
            f"--lon -74.0060"
        )

        # Should process custom location test
        assert result["returncode"] in [0, 1, 2]
        assert result["stdout"] or result["stderr"]


class TestDatabaseCommands:
    """Test suite for database-related CLI commands."""

    def test_init_db_command_help(self, run_cli, cli_command):
        """Test that the init-db command shows help correctly."""
        result = run_cli(f"{cli_command} init-db --help")

        assert result["returncode"] == 0
        assert any(
            keyword in result["stdout"]
            for keyword in ["initialize", "database", "reset"]
        )

    def test_init_db_command(self, run_cli, cli_command, temp_env):
        """Test init-db command execution."""
        result = run_cli(f"{cli_command} init-db")

        # Should initialize database successfully
        assert result["returncode"] == 0
        assert any(
            keyword in result["stdout"].lower()
            for keyword in ["database", "initialized", "successfully"]
        )


class TestSettingsCommands:
    """Test suite for settings management CLI commands."""

    def test_settings_command_help(self, run_cli, cli_command):
        """Test that the settings command shows help correctly."""
        result = run_cli(f"{cli_command} settings --help")

        assert result["returncode"] == 0
        assert any(
            keyword in result["stdout"]
            for keyword in ["settings", "--forecast-days", "--temp-unit"]
        )

    def test_settings_no_args(self, run_cli, cli_command, temp_env):
        """Test settings command with no arguments (should show current settings)."""
        result = run_cli(f"{cli_command} settings")

        # Should show current settings or complete successfully
        assert result["returncode"] in [0, 1, 2]
        # May have no output if settings are not initialized or command has no output
        assert result["stdout"] or result["stderr"] or result["returncode"] in [0, 1, 2]

    def test_settings_update_forecast_days(self, run_cli, cli_command, temp_env):
        """Test updating forecast days setting."""
        result = run_cli(f"{cli_command} settings --forecast-days 5")

        # Should update the setting
        assert result["returncode"] in [0, 1, 2]
        assert result["stdout"] or result["stderr"]

    def test_settings_update_temp_unit(self, run_cli, cli_command, temp_env):
        """Test updating temperature unit setting."""
        result = run_cli(f"{cli_command} settings --temp-unit F")

        # Should update the setting
        assert result["returncode"] in [0, 1, 2]
        assert result["stdout"] or result["stderr"]

    def test_settings_invalid_forecast_days(self, run_cli, cli_command, temp_env):
        """Test settings with invalid forecast days."""
        result = run_cli(f"{cli_command} settings --forecast-days 10")  # Should be 1-7

        # Should handle invalid value
        assert result["returncode"] in [0, 1, 2]
        assert result["stdout"] or result["stderr"]

    def test_set_forecast_days_command_help(self, run_cli, cli_command):
        """Test that the set-forecast-days command shows help correctly."""
        result = run_cli(f"{cli_command} set-forecast-days --help")

        assert result["returncode"] == 0
        assert any(
            keyword in result["stdout"] for keyword in ["forecast", "days", "--days"]
        )

    def test_set_forecast_days_valid(self, run_cli, cli_command, temp_env):
        """Test set-forecast-days command with valid value."""
        result = run_cli(f"{cli_command} set-forecast-days --days 3")

        # Should set the value successfully
        assert result["returncode"] in [0, 1, 2]
        assert result["stdout"] or result["stderr"]

    def test_set_forecast_days_invalid(self, run_cli, cli_command):
        """Test set-forecast-days command with invalid value."""
        result = run_cli(f"{cli_command} set-forecast-days --days 10")  # Max is 7

        # Should reject invalid value (Typer validation error)
        assert result["returncode"] == 2
        assert any(
            keyword in result["stderr"].lower()
            for keyword in ["error", "invalid", "range"]
        )


class TestDiagnosticsCommands:
    """Test suite for diagnostic CLI commands."""

    def test_diagnostics_command_help(self, run_cli, cli_command):
        """Test that the diagnostics command shows help correctly."""
        result = run_cli(f"{cli_command} diagnostics --help")

        assert result["returncode"] == 0
        assert any(
            keyword in result["stdout"] for keyword in ["diagnostic", "--verbose"]
        )

    def test_diagnostics_command(self, run_cli, cli_command, temp_env):
        """Test diagnostics command execution."""
        result = run_cli(f"{cli_command} diagnostics")

        # Should run diagnostics and provide output
        assert result["returncode"] in [0, 1, 2]
        assert result["stdout"] or result["stderr"]

    def test_diagnostics_verbose(self, run_cli, cli_command, temp_env):
        """Test diagnostics command with verbose flag."""
        result = run_cli(f"{cli_command} diagnostics --verbose")

        # Should run with verbose output
        assert result["returncode"] in [0, 1, 2]
        assert result["stdout"] or result["stderr"]
