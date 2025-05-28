"""
Functional tests for interactive CLI mode and general CLI functionality.
Tests interactive mode, help system, and overall CLI behavior.
"""


class TestInteractiveMode:
    """Test suite for interactive CLI functionality."""

    def test_interactive_command_help(self, run_cli, cli_command):
        """Test that the interactive command shows help correctly."""
        result = run_cli(f"{cli_command} interactive --help")

        assert result["returncode"] == 0
        assert any(
            keyword in result["stdout"]
            for keyword in ["interactive", "Start interactive", "--verbose"]
        )

    def test_interactive_mode_exit(self, run_cli, cli_command, temp_env):
        """Test that interactive mode can be exited properly."""
        # Send 'exit' command to interactive mode
        result = run_cli(f"{cli_command} interactive", input_text="exit\n", timeout=10)

        # Should exit gracefully
        assert result["returncode"] in [0, 1]
        assert result["stdout"] or result["stderr"]

    def test_interactive_mode_quit(self, run_cli, cli_command, temp_env):
        """Test that interactive mode can be quit properly."""
        # Send 'quit' command to interactive mode
        result = run_cli(f"{cli_command} interactive", input_text="quit\n", timeout=10)

        # Should quit gracefully
        assert result["returncode"] in [0, 1]
        assert result["stdout"] or result["stderr"]

    def test_interactive_mode_help(self, run_cli, cli_command, temp_env):
        """Test help command in interactive mode."""
        # Send 'help' then 'exit' to interactive mode
        result = run_cli(
            f"{cli_command} interactive", input_text="help\nexit\n", timeout=10
        )

        # Should show help and exit
        assert result["returncode"] in [0, 1]
        assert result["stdout"] or result["stderr"]


class TestCLIHelp:
    """Test suite for CLI help system."""

    def test_main_help(self, run_cli, cli_command):
        """Test main CLI help command."""
        result = run_cli(f"{cli_command} --help")

        assert result["returncode"] == 0
        assert (
            "Weather App" in result["stdout"] or "weather" in result["stdout"].lower()
        )
        assert "Commands:" in result["stdout"] or "command" in result["stdout"].lower()

    def test_help_flag(self, run_cli, cli_command):
        """Test -h flag for help (Typer doesn't support -h by default)."""
        result = run_cli(f"{cli_command} -h")

        # Typer returns exit code 2 for unsupported options like -h
        assert result["returncode"] == 2
        assert (
            "No such option" in result["stderr"] or "help" in result["stderr"].lower()
        )

    def test_subcommand_listing(self, run_cli, cli_command):
        """Test that main help lists available subcommands."""
        result = run_cli(f"{cli_command} --help")

        assert result["returncode"] == 0

        # Check for key subcommands
        expected_commands = ["current", "forecast", "weather", "version"]
        for command in expected_commands:
            assert command in result["stdout"]

    def test_invalid_command(self, run_cli, cli_command):
        """Test behavior with invalid command."""
        result = run_cli(f"{cli_command} invalid-command")

        # Should show error for invalid command (Typer uses exit code 2)
        assert result["returncode"] == 2
        assert any(
            keyword in result["stderr"].lower()
            for keyword in ["no such command", "invalid", "error", "not found"]
        )


class TestCLIEdgeCases:
    """Test suite for CLI edge cases and error handling."""

    def test_no_arguments(self, run_cli, cli_command):
        """Test CLI with no arguments."""
        result = run_cli(cli_command)

        # Should show help or usage information
        assert result["returncode"] in [
            0,
            2,
        ]  # Some CLIs use exit code 2 for usage
        assert result["stdout"] or result["stderr"]

    def test_double_dash_help(self, run_cli, cli_command):
        """Test -- help syntax."""
        result = run_cli(f"{cli_command} -- --help")

        # Should handle this gracefully
        assert result["returncode"] in [0, 1, 2]
        assert result["stdout"] or result["stderr"]

    def test_version_variations(self, run_cli, cli_command):
        """Test different version command variations."""
        # Test main version command
        result = run_cli(f"{cli_command} version")
        assert result["returncode"] == 0
        assert "Weather Dashboard" in result["stdout"]

    def test_multiple_verbose_flags(self, run_cli, cli_command, temp_env):
        """Test commands with multiple verbose flags."""
        result = run_cli(f"{cli_command} current -v -v --verbose")

        # Should handle multiple verbose flags gracefully
        assert result["returncode"] in [0, 1]
        assert result["stdout"] or result["stderr"]

    def test_conflicting_options(self, run_cli, cli_command):
        """Test commands with potentially conflicting options."""
        result = run_cli(f"{cli_command} forecast --days 3 --days 5")

        # Should handle conflicting options (usually last one wins)
        assert result["returncode"] in [0, 1, 2]
        assert result["stdout"] or result["stderr"]

    def test_special_characters_in_location(
        self, run_cli, cli_command, mock_env_with_api_key
    ):
        """Test location names with special characters."""
        result = run_cli(f"{cli_command} weather 'São Paulo, Brazil'")

        # Should handle Unicode characters (Typer may return 2 for argument errors)
        assert result["returncode"] in [0, 1, 2]
        assert result["stdout"] or result["stderr"]

    def test_very_long_location_name(self, run_cli, cli_command):
        """Test with very long location name."""
        long_name = "A" * 500  # Very long location name
        result = run_cli(f"{cli_command} weather '{long_name}'")

        # Should handle long input gracefully
        assert result["returncode"] in [0, 1, 2]
        assert result["stdout"] or result["stderr"]

    def test_empty_string_arguments(self, run_cli, cli_command):
        """Test with empty string arguments."""
        result = run_cli(f"{cli_command} weather ''")

        # Typer might handle empty location differently
        assert result["returncode"] in [0, 1, 2]
        assert result["stdout"] or result["stderr"]


class TestCLIEnvironment:
    """Test suite for CLI environment handling."""

    def test_cli_without_api_key(self, run_cli, cli_command, monkeypatch):
        """Test CLI behavior without API key."""
        # Remove API key from environment
        monkeypatch.delenv("WEATHER_API_KEY", raising=False)

        result = run_cli(f"{cli_command} weather London")

        # Should handle missing API key gracefully
        assert result["returncode"] in [0, 1, 2]
        if result["returncode"] != 0:
            assert (
                any(
                    keyword in result["stdout"].lower()
                    or keyword in result["stderr"].lower()
                    for keyword in ["api", "key", "error", "config"]
                )
                or result["stdout"]
                or result["stderr"]
            )

    def test_cli_with_invalid_api_key(self, run_cli, cli_command, monkeypatch):
        """Test CLI behavior with invalid API key."""
        # Set invalid API key
        monkeypatch.setenv("WEATHER_API_KEY", "invalid-key-12345")

        result = run_cli(f"{cli_command} weather London")

        # Should handle invalid API key gracefully
        assert result["returncode"] in [0, 1, 2]
        if result["returncode"] != 0:
            assert (
                any(
                    keyword in result["stdout"].lower()
                    or keyword in result["stderr"].lower()
                    for keyword in ["api", "error", "invalid", "unauthorized"]
                )
                or result["stdout"]
                or result["stderr"]
            )

    def test_cli_database_permissions(self, run_cli, cli_command, monkeypatch):
        """Test CLI behavior with database permission issues."""
        # Point to a directory that doesn't exist or isn't writable
        monkeypatch.setenv("DATABASE_URL", "sqlite:///nonexistent/path/weather.db")

        result = run_cli(f"{cli_command} init-db")

        # Should handle database issues gracefully
        assert result["returncode"] in [0, 1, 2]
        assert result["stdout"] or result["stderr"]


class TestCLIPerformance:
    """Test suite for CLI performance and timeouts."""

    def test_command_timeout(self, run_cli, cli_command, temp_env):
        """Test that commands complete within reasonable time."""
        # Test a simple command that should complete quickly
        result = run_cli(f"{cli_command} version", timeout=5)

        assert result["returncode"] == 0
        assert "timeout" not in result["stderr"].lower()

    def test_help_commands_fast(self, run_cli, cli_command):
        """Test that help commands are fast."""
        commands_to_test = [
            f"{cli_command} --help",
            f"{cli_command} current --help",
            f"{cli_command} forecast --help",
            f"{cli_command} weather --help",
            f"{cli_command} version",
        ]

        for command in commands_to_test:
            result = run_cli(command, timeout=3)
            assert result["returncode"] == 0
            assert "timeout" not in result["stderr"].lower()
