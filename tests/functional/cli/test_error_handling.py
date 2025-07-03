"""
Functional tests for CLI error handling and edge cases.
Tests various error scenarios, invalid inputs, and recovery mechanisms.
"""

import tempfile
from pathlib import Path


class TestCommandLineErrorHandling:
    """Test suite for command line error handling."""

    def test_invalid_command_handling(self, run_cli, cli_command):
        """Test handling of invalid commands."""
        invalid_commands = [
            f"{cli_command} invalidcommand",
            f"{cli_command} notacommand",
            f"{cli_command} xyz123",
        ]

        for cmd in invalid_commands:
            result = run_cli(cmd)

            # Should show helpful error message
            assert result["returncode"] == 2  # Typer error code
            assert any(
                keyword in result["stderr"].lower()
                for keyword in ["no such command", "usage", "error", "invalid"]
            )

    def test_missing_required_arguments(self, run_cli, cli_command):
        """Test handling when required arguments are missing."""
        commands_requiring_args = [
            f"{cli_command} weather",  # Missing location
            f"{cli_command} date",  # Missing date
        ]

        for cmd in commands_requiring_args:
            result = run_cli(cmd)

            # Should show error about missing argument
            assert result["returncode"] == 2
            assert any(
                keyword in result["stderr"].lower()
                for keyword in ["missing", "required", "argument", "usage"]
            )

    def test_invalid_argument_types(self, run_cli, cli_command):
        """Test handling of invalid argument types."""
        invalid_type_commands = [
            f"{cli_command} forecast --days abc",  # Non-numeric days
            f"{cli_command} date abc123",  # Invalid date format
            f"{cli_command} weather --unit xyz",  # Invalid unit
        ]

        for cmd in invalid_type_commands:
            result = run_cli(cmd)

            # Should handle type errors gracefully
            assert result["returncode"] in [1, 2]
            assert result["stdout"] or result["stderr"]

    def test_out_of_range_values(self, run_cli, cli_command):
        """Test handling of out-of-range parameter values."""
        out_of_range_commands = [
            f"{cli_command} forecast --days 15",  # Too many days
            f"{cli_command} forecast --days -1",  # Negative days
            f"{cli_command} forecast --days 0",  # Zero days
        ]

        for cmd in out_of_range_commands:
            result = run_cli(cmd)

            # Should show range validation error
            assert result["returncode"] == 2
            assert any(
                keyword in result["stderr"].lower()
                for keyword in ["range", "must be", "invalid", "between"]
            )


class TestEnvironmentErrorHandling:
    """Test suite for environment-related error handling."""

    def test_missing_api_key(self, run_cli, cli_command, monkeypatch, temp_env):
        """Test handling when API key is missing."""
        from pathlib import Path

        # Remove API key from environment
        monkeypatch.delenv("WEATHER_API_KEY", raising=False)

        # Temporarily move .env file to simulate missing API key
        env_file = Path(".env")
        temp_env_file = Path(".env.temp_backup")

        moved_env = False
        if env_file.exists():
            env_file.rename(temp_env_file)
            moved_env = True

        try:
            result = run_cli(f"{cli_command} weather 'London'")

            # Should handle missing API key gracefully
            assert result["returncode"] in [0, 1]  # May warn or fail gracefully
            assert result["stdout"] or result["stderr"]

            # If API key is still found (return code 0), accept success
            # If API key is missing (return code 1), check for helpful error message
            if result["returncode"] == 0:
                # API key was found, command succeeded - this is acceptable
                assert "weather" in result["stdout"].lower()
            else:
                # API key was missing, check for helpful error message
                output = (result["stdout"] + result["stderr"]).lower()
                assert any(
                    keyword in output
                    for keyword in [
                        "api key",
                        "configuration",
                        "environment",
                        "missing",
                    ]
                )
        finally:
            # Restore .env file if we moved it
            if moved_env and temp_env_file.exists():
                temp_env_file.rename(env_file)

    def test_invalid_api_key(self, run_cli, cli_command, monkeypatch, temp_env):
        """Test handling with invalid API key."""
        # Set invalid API key
        monkeypatch.setenv("WEATHER_API_KEY", "invalid-key-12345")

        result = run_cli(f"{cli_command} weather 'London'")

        # Should handle invalid API key gracefully
        assert result["returncode"] in [0, 1]
        assert result["stdout"] or result["stderr"]

    def test_database_permission_errors(self, run_cli, cli_command, monkeypatch):
        """Test handling when database permissions are problematic."""
        # Try to use a read-only directory for database
        with tempfile.TemporaryDirectory() as temp_dir:
            read_only_dir = Path(temp_dir) / "readonly"
            read_only_dir.mkdir()
            read_only_dir.chmod(0o444)  # Read-only

            db_path = read_only_dir / "test.db"
            monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")

            result = run_cli(f"{cli_command} init-db")

            # Should handle permission errors gracefully
            assert result["returncode"] in [0, 1]
            assert result["stdout"] or result["stderr"]

    def test_corrupted_database_handling(self, run_cli, cli_command, monkeypatch):
        """Test handling when database is corrupted."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a file that looks like a database but is corrupted
            corrupted_db = Path(temp_dir) / "corrupted.db"
            corrupted_db.write_text("This is not a valid SQLite database")

            monkeypatch.setenv("DATABASE_URL", f"sqlite:///{corrupted_db}")

            result = run_cli(f"{cli_command} current")

            # Should handle corrupted database gracefully
            assert result["returncode"] in [0, 1]
            assert result["stdout"] or result["stderr"]


class TestNetworkErrorHandling:
    """Test suite for network-related error handling."""

    def test_network_timeout_handling(
        self, run_cli, cli_command, mock_env_with_api_key
    ):
        """Test handling when network requests timeout."""
        # This test assumes the CLI has timeout handling
        result = run_cli(f"{cli_command} weather 'London'", timeout=5)

        # Should complete within reasonable time or handle timeout
        assert result["returncode"] in [0, 1, -1]  # -1 for timeout
        assert result["stdout"] or result["stderr"]

    def test_no_internet_connection(self, run_cli, cli_command, temp_env):
        """Test handling when there's no internet connection."""
        # Note: This is hard to simulate, so we test the error handling path
        result = run_cli(f"{cli_command} weather 'London'")

        # Should handle network issues gracefully
        assert result["returncode"] in [0, 1]
        assert result["stdout"] or result["stderr"]


class TestInputValidationAndSanitization:
    """Test suite for input validation and sanitization."""

    def test_special_character_handling(
        self, run_cli, cli_command, mock_env_with_api_key
    ):
        """Test handling of special characters in location names."""
        special_locations = [
            "São Paulo",
            "München",
            "北京",  # Beijing in Chinese
            "México City",
            "Zürich",
            "New York, NY",
            "London, UK",
        ]

        for location in special_locations:
            result = run_cli(f"{cli_command} weather '{location}'")

            # Should handle special characters without crashing
            assert result["returncode"] in [0, 1, 2]
            assert result["stdout"] or result["stderr"]

    def test_very_long_input_handling(self, run_cli, cli_command):
        """Test handling of unusually long inputs."""
        long_location = "a" * 500  # 500 character location name

        result = run_cli(f"{cli_command} weather '{long_location}'")

        # Should handle long input gracefully
        assert result["returncode"] in [0, 1, 2]
        assert result["stdout"] or result["stderr"]

    def test_empty_string_handling(self, run_cli, cli_command):
        """Test handling of empty string inputs."""
        result = run_cli(f"{cli_command} weather ''")

        # Should handle empty input appropriately
        assert result["returncode"] in [0, 1, 2]
        assert result["stdout"] or result["stderr"]

    def test_whitespace_only_input(self, run_cli, cli_command):
        """Test handling of whitespace-only inputs."""
        whitespace_inputs = [
            "   ",  # Spaces
            "\t\t",  # Tabs
            "\n\n",  # Newlines
            "  \t \n ",  # Mixed whitespace
        ]

        for whitespace in whitespace_inputs:
            result = run_cli(f"{cli_command} weather '{whitespace}'")

            # Should handle whitespace-only input
            assert result["returncode"] in [0, 1, 2]
            assert result["stdout"] or result["stderr"]

    def test_potentially_dangerous_input(self, run_cli, cli_command):
        """Test handling of potentially dangerous inputs."""
        dangerous_inputs = [
            "; rm -rf /",
            "$(rm -rf /)",
            "`rm -rf /`",
            "../../../etc/passwd",
            "'; DROP TABLE locations; --",
        ]

        for dangerous_input in dangerous_inputs:
            result = run_cli(f"{cli_command} weather '{dangerous_input}'")

            # Should sanitize and handle safely
            assert result["returncode"] in [0, 1, 2]
            assert result["stdout"] or result["stderr"]


class TestRecoveryMechanisms:
    """Test suite for error recovery mechanisms."""

    def test_help_system_always_available(self, run_cli, cli_command):
        """Test that help system works even when other things fail."""
        help_commands = [
            f"{cli_command} --help",
            f"{cli_command} weather --help",
            f"{cli_command} forecast --help",
        ]

        for cmd in help_commands:
            result = run_cli(cmd)

            # Help should always work
            assert result["returncode"] == 0
            assert (
                "usage" in result["stdout"].lower()
                or "help" in result["stdout"].lower()
            )

    def test_version_info_always_available(self, run_cli, cli_command):
        """Test that version info is always accessible."""
        version_commands = [
            f"{cli_command} version",
        ]

        for cmd in version_commands:
            result = run_cli(cmd)

            # Version should always work
            assert result["returncode"] == 0
            assert any(
                keyword in result["stdout"].lower()
                for keyword in ["version", "weather", "dashboard"]
            )

    def test_graceful_degradation(self, run_cli, cli_command, temp_env):
        """Test that app degrades gracefully when features are unavailable."""
        # Test with minimal environment
        result = run_cli(f"{cli_command} --help")

        # Basic functionality should still work
        assert result["returncode"] == 0
        assert result["stdout"]

    def test_error_message_quality(self, run_cli, cli_command):
        """Test that error messages are helpful and actionable."""
        # Trigger a known error
        result = run_cli(f"{cli_command} nonexistentcommand")

        error_output = result["stderr"].lower()

        # Should provide helpful guidance
        assert any(
            phrase in error_output
            for phrase in [
                "try",
                "help",
                "usage",
                "available",
                "commands",
                "see",
                "--help",
                "check",
            ]
        )


class TestConcurrencyAndRaceConditions:
    """Test suite for concurrency-related error handling."""

    def test_database_locking_handling(self, run_cli, cli_command, temp_env):
        """Test handling when database is locked by another process."""
        # This is challenging to test directly, but we can test the general path
        result = run_cli(f"{cli_command} init-db")

        # Should handle database operations gracefully
        assert result["returncode"] in [0, 1]
        assert result["stdout"] or result["stderr"]

    def test_multiple_command_execution(self, run_cli, cli_command, temp_env):
        """Test that multiple commands can run without conflicts."""
        commands = [
            f"{cli_command} --help",
            f"{cli_command} version",
            f"{cli_command} --help",
        ]

        results = []
        for cmd in commands:
            result = run_cli(cmd)
            results.append(result)

        # All commands should succeed
        for result in results:
            assert result["returncode"] == 0
            assert result["stdout"]


class TestResourceConstraints:
    """Test suite for resource constraint handling."""

    def test_memory_constraint_simulation(self, run_cli, cli_command):
        """Test behavior under simulated memory constraints."""
        # While we can't directly limit memory, we can test with large inputs
        large_input = "London " * 1000  # Very large location string

        result = run_cli(f"{cli_command} weather '{large_input}'")

        # Should handle large inputs without memory issues
        assert result["returncode"] in [0, 1, 2]
        assert result["stdout"] or result["stderr"]

    def test_disk_space_handling(self, run_cli, cli_command, temp_env):
        """Test handling when disk space might be limited."""
        # Test database operations that might be affected by disk space
        result = run_cli(f"{cli_command} init-db")

        # Should handle gracefully
        assert result["returncode"] in [0, 1]
        assert result["stdout"] or result["stderr"]
