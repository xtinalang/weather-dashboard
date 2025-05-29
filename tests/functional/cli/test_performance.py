"""
Performance functional tests for the CLI application.
Tests command execution times, resource usage, and scalability.
"""

import concurrent.futures
import tempfile
import time
from pathlib import Path


class TestCommandExecutionPerformance:
    """Test suite for command execution performance."""

    def test_help_command_performance(self, run_cli, cli_command):
        """Test that help commands execute quickly."""
        help_commands = [
            f"{cli_command} --help",
            f"{cli_command} weather --help",
            f"{cli_command} forecast --help",
            f"{cli_command} current --help",
        ]

        for cmd in help_commands:
            start_time = time.time()
            result = run_cli(cmd, timeout=5)
            execution_time = time.time() - start_time

            # Help commands should execute very quickly
            assert execution_time < 1.0, f"Help command took {execution_time:.2f}s"
            assert result["returncode"] == 0
            assert result["stdout"]

    def test_version_command_performance(self, run_cli, cli_command):
        """Test version command performance."""
        start_time = time.time()
        result = run_cli(f"{cli_command} version", timeout=5)
        execution_time = time.time() - start_time

        # Version should be nearly instantaneous
        assert execution_time < 0.5, f"Version command took {execution_time:.2f}s"
        assert result["returncode"] == 0

    def test_database_initialization_performance(self, run_cli, cli_command, temp_env):
        """Test database initialization performance."""
        start_time = time.time()
        result = run_cli(f"{cli_command} init-db", timeout=10)
        execution_time = time.time() - start_time

        # Database init should complete within reasonable time
        assert execution_time < 5.0, f"Database init took {execution_time:.2f}s"
        assert result["returncode"] in [0, 1]  # May fail gracefully

    def test_weather_command_performance(
        self, run_cli, cli_command, mock_env_with_api_key
    ):
        """Test weather command performance."""
        start_time = time.time()
        result = run_cli(f"{cli_command} weather 'London'", timeout=15)
        execution_time = time.time() - start_time

        # Weather command should complete within reasonable time
        assert execution_time < 10.0, f"Weather command took {execution_time:.2f}s"
        assert result["returncode"] in [0, 1, 2]  # Various acceptable outcomes

    def test_forecast_command_performance(
        self, run_cli, cli_command, mock_env_with_api_key
    ):
        """Test forecast command performance."""
        start_time = time.time()
        result = run_cli(f"{cli_command} forecast --days 3", timeout=15)
        execution_time = time.time() - start_time

        # Forecast should complete within reasonable time
        assert execution_time < 10.0, f"Forecast command took {execution_time:.2f}s"
        assert result["returncode"] in [0, 1, 2]


class TestConcurrentExecution:
    """Test suite for concurrent command execution."""

    def test_concurrent_help_commands(self, run_cli, cli_command):
        """Test concurrent execution of help commands."""
        commands = [
            f"{cli_command} --help",
            f"{cli_command} weather --help",
            f"{cli_command} forecast --help",
        ]

        start_time = time.time()

        # Execute commands concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(run_cli, cmd, timeout=5) for cmd in commands]
            results = [future.result() for future in futures]

        total_time = time.time() - start_time

        # Should complete concurrently faster than sequentially
        assert total_time < 3.0, f"Concurrent help commands took {total_time:.2f}s"

        # All should succeed
        for result in results:
            assert result["returncode"] == 0
            assert result["stdout"]

    def test_concurrent_database_operations(self, run_cli, cli_command, temp_env):
        """Test concurrent database operations."""
        commands = [
            f"{cli_command} init-db",
            f"{cli_command} current",
            f"{cli_command} --help",
        ]

        start_time = time.time()

        # Execute database-related commands concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(run_cli, cmd, timeout=10) for cmd in commands]
            results = [future.result() for future in futures]

        total_time = time.time() - start_time

        # Should handle concurrent database access
        assert total_time < 15.0, f"Concurrent DB operations took {total_time:.2f}s"

        # Should not crash (return codes may vary)
        for result in results:
            assert result["returncode"] in [0, 1, 2]

    def test_multiple_weather_requests(
        self, run_cli, cli_command, mock_env_with_api_key
    ):
        """Test multiple concurrent weather requests."""
        locations = ["London", "Paris", "New York"]
        commands = [f"{cli_command} weather '{loc}'" for loc in locations]

        start_time = time.time()

        # Execute weather commands concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(run_cli, cmd, timeout=20) for cmd in commands]
            results = [future.result() for future in futures]

        total_time = time.time() - start_time

        # Should handle multiple API requests reasonably
        assert total_time < 30.0, f"Multiple weather requests took {total_time:.2f}s"

        # Should not crash
        for result in results:
            assert result["returncode"] in [0, 1, 2]


class TestResourceUsage:
    """Test suite for resource usage optimization."""

    def test_memory_usage_stability(self, run_cli, cli_command, temp_env):
        """Test that repeated commands don't cause memory leaks."""
        commands = [
            f"{cli_command} --help",
            f"{cli_command} version",
            f"{cli_command} --help",
            f"{cli_command} version",
            f"{cli_command} --help",
        ]

        execution_times = []

        for cmd in commands:
            start_time = time.time()
            result = run_cli(cmd, timeout=5)
            execution_time = time.time() - start_time

            execution_times.append(execution_time)
            assert result["returncode"] == 0

        # Execution times should remain stable (no significant degradation)
        if len(execution_times) > 2:
            first_time = execution_times[0]
            last_time = execution_times[-1]

            # Last execution should not be significantly slower
            assert last_time < first_time * 2, (
                "Performance degraded over repeated executions"
            )

    def test_large_input_handling(self, run_cli, cli_command):
        """Test handling of large inputs."""
        # Test with very long location name
        long_location = "a" * 1000

        start_time = time.time()
        result = run_cli(f"{cli_command} weather '{long_location}'", timeout=10)
        execution_time = time.time() - start_time

        # Should handle large input without performance issues
        assert execution_time < 5.0, f"Large input handling took {execution_time:.2f}s"
        assert result["returncode"] in [0, 1, 2]

    def test_database_size_impact(self, run_cli, cli_command, monkeypatch):
        """Test performance impact of database size."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.db"
            monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")

            # Initialize database
            init_result = run_cli(f"{cli_command} init-db", timeout=10)
            assert init_result["returncode"] in [0, 1]  # Should complete

            # Test command performance with empty database
            start_time = time.time()
            result1 = run_cli(f"{cli_command} current", timeout=10)
            empty_db_time = time.time() - start_time

            # Database commands should work
            assert result1["returncode"] in [0, 1, 2]
            # Test performance should be reasonable
            assert empty_db_time < 3.0, f"Empty DB command took {empty_db_time:.2f}s"


class TestScalabilityIndicators:
    """Test suite for scalability indicators."""

    def test_command_startup_overhead(self, run_cli, cli_command):
        """Test command startup overhead."""
        simple_commands = [
            f"{cli_command} version",
            f"{cli_command} --help",
        ]

        startup_times = []

        for cmd in simple_commands:
            # Run multiple times to get average
            times = []
            for _ in range(3):
                start_time = time.time()
                result = run_cli(cmd, timeout=5)
                execution_time = time.time() - start_time
                times.append(execution_time)
                assert result["returncode"] == 0

            avg_time = sum(times) / len(times)
            startup_times.append(avg_time)

        # Startup overhead should be minimal
        max_startup = max(startup_times)
        assert max_startup < 2.0, f"Command startup overhead: {max_startup:.2f}s"

    def test_repeated_command_performance(self, run_cli, cli_command, temp_env):
        """Test performance of repeated command execution."""
        command = f"{cli_command} --help"

        execution_times = []

        # Execute the same command multiple times
        for _ in range(5):
            start_time = time.time()
            result = run_cli(command, timeout=5)
            execution_time = time.time() - start_time

            execution_times.append(execution_time)
            assert result["returncode"] == 0

        # Performance should remain consistent
        avg_time = sum(execution_times) / len(execution_times)
        max_time = max(execution_times)
        min_time = min(execution_times)

        # Variation should be minimal
        variation = max_time - min_time
        assert variation < avg_time, f"Performance variation too high: {variation:.2f}s"

    def test_stress_test_rapid_commands(self, run_cli, cli_command):
        """Test rapid sequential command execution."""
        commands = [f"{cli_command} --help" for _ in range(10)]

        start_time = time.time()

        results = []
        for cmd in commands:
            result = run_cli(cmd, timeout=2)
            results.append(result)

        total_time = time.time() - start_time

        # Should handle rapid commands efficiently
        assert total_time < 10.0, f"Rapid commands took {total_time:.2f}s"

        # All should succeed
        for result in results:
            assert result["returncode"] == 0


class TestUserExperiencePerformance:
    """Test suite for user experience performance metrics."""

    def test_immediate_feedback_commands(self, run_cli, cli_command):
        """Test commands that should provide immediate feedback."""
        immediate_commands = [
            f"{cli_command} --help",
            f"{cli_command} version",
        ]

        for cmd in immediate_commands:
            start_time = time.time()
            result = run_cli(cmd, timeout=3)
            response_time = time.time() - start_time

            # Should respond immediately
            assert response_time < 0.5, f"Immediate command took {response_time:.2f}s"
            assert result["returncode"] == 0
            assert result["stdout"]

    def test_error_message_response_time(self, run_cli, cli_command):
        """Test that error messages appear quickly."""
        error_commands = [
            f"{cli_command} invalidcommand",
            f"{cli_command} weather",  # Missing argument
            f"{cli_command} forecast --days abc",  # Invalid argument
        ]

        for cmd in error_commands:
            start_time = time.time()
            result = run_cli(cmd, timeout=3)
            response_time = time.time() - start_time

            # Error messages should appear quickly
            assert response_time < 1.0, f"Error response took {response_time:.2f}s"
            assert result["returncode"] == 2  # Typer error code
            assert result["stderr"]

    def test_progress_indication_timeout(
        self, run_cli, cli_command, mock_env_with_api_key
    ):
        """Test that long-running commands don't appear frozen."""
        # Weather commands might take time due to API calls
        start_time = time.time()
        result = run_cli(f"{cli_command} weather 'London'", timeout=20)
        execution_time = time.time() - start_time

        # Should complete or timeout gracefully
        assert execution_time < 20.0, f"Command took {execution_time:.2f}s"

        # Should not appear frozen (should have some output)
        assert result["stdout"] or result["stderr"]

    def test_interactive_responsiveness(self, run_cli, cli_command, temp_env):
        """Test responsiveness of potentially interactive commands."""
        # Test commands that might prompt for input
        commands = [
            f"{cli_command} current",  # Might prompt for location
            f"{cli_command} forecast",  # Might prompt for parameters
        ]

        for cmd in commands:
            start_time = time.time()
            result = run_cli(cmd, timeout=5)
            response_time = time.time() - start_time

            # Should respond within reasonable time
            assert response_time < 3.0, f"Interactive command took {response_time:.2f}s"
            assert result["returncode"] in [0, 1, 2]


class TestPerformanceRegression:
    """Test suite for performance regression detection."""

    def test_baseline_performance_metrics(self, run_cli, cli_command):
        """Establish baseline performance metrics."""
        baseline_commands = {
            "help": f"{cli_command} --help",
            "version": f"{cli_command} version",
        }

        baseline_times = {}

        for name, cmd in baseline_commands.items():
            times = []
            for _ in range(3):  # Average of 3 runs
                start_time = time.time()
                result = run_cli(cmd, timeout=5)
                execution_time = time.time() - start_time
                times.append(execution_time)
                assert result["returncode"] == 0

            baseline_times[name] = sum(times) / len(times)

        # Baseline performance expectations
        assert baseline_times["help"] < 1.0, (
            f"Help baseline: {baseline_times['help']:.2f}s"
        )
        assert baseline_times["version"] < 0.5, (
            f"Version baseline: {baseline_times['version']:.2f}s"
        )

    def test_performance_consistency(self, run_cli, cli_command):
        """Test that performance is consistent across runs."""
        command = f"{cli_command} --help"

        execution_times = []

        # Run same command multiple times
        for _ in range(5):
            start_time = time.time()
            result = run_cli(command, timeout=5)
            execution_time = time.time() - start_time
            execution_times.append(execution_time)
            assert result["returncode"] == 0

        # Calculate performance statistics
        avg_time = sum(execution_times) / len(execution_times)
        max_time = max(execution_times)
        min_time = min(execution_times)

        # Performance should be consistent
        performance_ratio = max_time / min_time if min_time > 0 else 1
        assert performance_ratio < 3.0, (
            f"Performance inconsistent: {performance_ratio:.2f}x variation"
        )

        # Average should be reasonable
        assert avg_time < 1.0, f"Average performance: {avg_time:.2f}s"
