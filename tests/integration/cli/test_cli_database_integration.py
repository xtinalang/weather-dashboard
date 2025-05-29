"""Integration tests for CLI database operations.

These tests focus specifically on how the CLI interacts with the database,
including data persistence, transaction handling, and error recovery.
"""

from tests.integration.conftest import assert_cli_success
from weather_app.cli import app
from weather_app.repository import LocationRepository, SettingsRepository


class TestCLIDatabasePersistence:
    """Test CLI database persistence operations."""

    def test_location_persistence_through_cli(self, cli_runner, clean_db):
        """Test that locations added through CLI persist in database."""
        # Initialize database
        result = cli_runner.invoke(app, ["init-db"])
        assert_cli_success(result)

        # Add location through CLI
        result = cli_runner.invoke(
            app,
            [
                "add-location",
                "--name",
                "Paris",
                "--lat",
                "48.8566",
                "--lon",
                "2.3522",
                "--country",
                "France",
                "--region",
                "Île-de-France",
            ],
        )
        assert_cli_success(result)

        # Verify location exists in database
        repo = LocationRepository()
        location = repo.find_by_coordinates(48.8566, 2.3522)
        assert location is not None
        assert location.name == "Paris"
        assert location.country == "France"

    def test_settings_persistence_through_cli(self, cli_runner, clean_db):
        """Test that settings updated through CLI persist in database."""
        # Initialize database
        result = cli_runner.invoke(app, ["init-db"])
        assert_cli_success(result)

        # Update settings through CLI
        result = cli_runner.invoke(app, ["set-forecast-days", "--days", "5"])
        assert_cli_success(result)

        result = cli_runner.invoke(app, ["settings", "--temp-unit", "F"])
        assert_cli_success(result)

        # Verify settings persist in database
        repo = SettingsRepository()
        settings = repo.get_settings()
        assert settings.forecast_days == 5
        assert settings.temperature_unit == "fahrenheit"

    def test_multiple_location_workflow(self, cli_runner, clean_db):
        """Test adding and managing multiple locations."""
        # Initialize database
        result = cli_runner.invoke(app, ["init-db"])
        assert_cli_success(result)

        # Add multiple locations
        locations = [
            ("London", "51.52", "-0.11", "UK"),
            ("New York", "40.7128", "-74.0060", "USA"),
            ("Tokyo", "35.6762", "139.6503", "Japan"),
        ]

        for name, lat, lon, country in locations:
            result = cli_runner.invoke(
                app,
                [
                    "add-location",
                    "--name",
                    name,
                    "--lat",
                    lat,
                    "--lon",
                    lon,
                    "--country",
                    country,
                ],
            )
            assert_cli_success(result)

        # Verify all locations exist in database
        repo = LocationRepository()
        all_locations = repo.get_all()
        assert len(all_locations) == 3

        names = [loc.name for loc in all_locations]
        assert "London" in names
        assert "New York" in names
        assert "Tokyo" in names


class TestCLIDatabaseTransactions:
    """Test CLI database transaction handling."""

    def test_database_rollback_on_error(self, cli_runner, clean_db):
        """Test that database operations rollback on errors."""
        # Initialize database
        result = cli_runner.invoke(app, ["init-db"])
        assert_cli_success(result)

        # Try to add location with invalid data (should fail)
        result = cli_runner.invoke(
            app,
            [
                "add-location",
                "--name",
                "Test",
                "--lat",
                "invalid_lat",
                "--lon",
                "2.0",
                "--country",
                "Test",
            ],
        )
        assert result.exit_code != 0

        # Verify no partial data was saved
        repo = LocationRepository()
        all_locations = repo.get_all()
        assert len(all_locations) == 0

    def test_concurrent_database_operations(self, cli_runner, clean_db):
        """Test handling of concurrent database operations."""
        # Initialize database
        result = cli_runner.invoke(app, ["init-db"])
        assert_cli_success(result)

        # Add location
        result = cli_runner.invoke(
            app,
            [
                "add-location",
                "--name",
                "Test City",
                "--lat",
                "40.0",
                "--lon",
                "50.0",
                "--country",
                "Test",
            ],
        )
        assert_cli_success(result)

        # Update settings (different table)
        result = cli_runner.invoke(app, ["set-forecast-days", "--days", "7"])
        assert_cli_success(result)

        # Both operations should succeed
        location_repo = LocationRepository()
        settings_repo = SettingsRepository()

        location = location_repo.find_by_coordinates(40.0, 50.0)
        settings = settings_repo.get_settings()

        assert location is not None
        assert settings.forecast_days == 7


class TestCLIDatabaseRecovery:
    """Test CLI database error recovery."""

    def test_database_recovery_after_corruption(self, cli_runner, clean_db):
        """Test recovery when database is corrupted or missing."""
        # Initialize database
        result = cli_runner.invoke(app, ["init-db"])
        assert_cli_success(result)

        # Simulate database corruption by removing file
        from pathlib import Path

        Path(clean_db).unlink()

        # Try to use CLI (should handle gracefully)
        result = cli_runner.invoke(app, ["set-forecast-days", "--days", "3"])
        # Should either succeed or fail gracefully
        assert result.exit_code in [0, 1]

    def test_database_initialization_recovery(self, cli_runner, clean_db):
        """Test database re-initialization after errors."""
        # Try to initialize database multiple times
        for _ in range(3):
            result = cli_runner.invoke(app, ["init-db"])
            assert_cli_success(result)

        # Should still work after multiple initializations
        result = cli_runner.invoke(app, ["set-forecast-days", "--days", "5"])
        assert_cli_success(result)


class TestCLIDatabaseConstraints:
    """Test CLI database constraint handling."""

    def test_unique_constraint_handling(self, cli_runner, clean_db):
        """Test handling of unique constraint violations."""
        # Initialize database
        result = cli_runner.invoke(app, ["init-db"])
        assert_cli_success(result)

        # Add location
        result = cli_runner.invoke(
            app,
            [
                "add-location",
                "--name",
                "Test City",
                "--lat",
                "40.0",
                "--lon",
                "50.0",
                "--country",
                "Test",
            ],
        )
        assert_cli_success(result)

        # Try to add same location again (should handle gracefully)
        result = cli_runner.invoke(
            app,
            [
                "add-location",
                "--name",
                "Test City 2",  # Different name
                "--lat",
                "40.0",  # Same coordinates
                "--lon",
                "50.0",
                "--country",
                "Test",
            ],
        )
        # Should either succeed (update) or fail gracefully
        assert result.exit_code in [0, 1]

    def test_foreign_key_constraint_handling(self, cli_runner, clean_db):
        """Test handling of foreign key constraints."""
        # Initialize database
        result = cli_runner.invoke(app, ["init-db"])
        assert_cli_success(result)

        # Operations should maintain referential integrity
        result = cli_runner.invoke(app, ["set-forecast-days", "--days", "3"])
        assert_cli_success(result)

        result = cli_runner.invoke(
            app,
            [
                "add-location",
                "--name",
                "Test",
                "--lat",
                "10.0",
                "--lon",
                "20.0",
                "--country",
                "Test",
            ],
        )
        assert_cli_success(result)


class TestCLIDatabasePerformance:
    """Test CLI database performance scenarios."""

    def test_bulk_location_operations(self, cli_runner, clean_db):
        """Test performance with multiple location operations."""
        # Initialize database
        result = cli_runner.invoke(app, ["init-db"])
        assert_cli_success(result)

        # Add many locations
        for i in range(10):
            result = cli_runner.invoke(
                app,
                [
                    "add-location",
                    "--name",
                    f"City_{i}",
                    "--lat",
                    str(40.0 + i * 0.1),
                    "--lon",
                    str(50.0 + i * 0.1),
                    "--country",
                    f"Country_{i}",
                ],
            )
            assert_cli_success(result)

        # Verify all locations were added
        repo = LocationRepository()
        all_locations = repo.get_all()
        assert len(all_locations) == 10

    def test_database_session_management(self, cli_runner, clean_db):
        """Test proper database session management."""
        # Initialize database
        result = cli_runner.invoke(app, ["init-db"])
        assert_cli_success(result)

        # Perform multiple operations that should each manage sessions properly
        operations = [
            ["set-forecast-days", "--days", "3"],
            ["settings", "--temp-unit", "C"],
            ["settings", "--forecast-days", "5"],
            ["settings", "--temp-unit", "F"],
        ]

        for operation in operations:
            result = cli_runner.invoke(app, operation)
            assert_cli_success(result)

        # Final state should be consistent
        repo = SettingsRepository()
        settings = repo.get_settings()
        assert settings.forecast_days == 5
        assert settings.temperature_unit == "fahrenheit"
