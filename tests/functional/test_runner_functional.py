"""
Comprehensive test runner for functional tests.
Handles setup, execution, and reporting for both CLI and web functional tests.
"""

import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, Optional


class FunctionalTestRunner:
    """Test runner for functional tests with environment setup."""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.web_server_process: Optional[subprocess.Popen] = None
        self.test_results: Dict[str, bool] = {}

    def setup_test_environment(self) -> bool:
        """Set up the test environment."""
        try:
            # Set up test database
            os.environ["DATABASE_URL"] = "sqlite:///test_weather.db"

            # Initialize test database
            init_script = self.project_root / "init_database.py"
            if init_script.exists():
                result = subprocess.run(
                    [sys.executable, str(init_script)],
                    cwd=self.project_root,
                    capture_output=True,
                    text=True,
                )
                if result.returncode != 0:
                    print(f"Warning: Database initialization failed: {result.stderr}")

            return True
        except Exception as e:
            print(f"Error setting up test environment: {e}")
            return False

    def start_web_server(self) -> bool:
        """Start the Flask web server for testing."""
        try:
            # Check if server is already running
            if self.is_server_running():
                print("Web server already running")
                return True

            # Start the web server using the web module
            web_module = self.project_root / "web" / "__main__.py"
            if not web_module.exists():
                web_module = self.project_root / "web" / "app.py"

            if web_module.exists():
                self.web_server_process = subprocess.Popen(
                    [sys.executable, "-m", "web"],
                    cwd=self.project_root,
                    env={
                        **os.environ,
                        "FLASK_PORT": "5001",
                        "PORT": "5001",
                        "APP_PORT": "5001",
                    },
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )

                # Wait for server to start
                max_attempts = 30
                for _attempt in range(max_attempts):
                    if self.is_server_running():
                        print("Web server started successfully")
                        return True
                    time.sleep(1)

                print("Web server failed to start within timeout")
                # Print server output for debugging
                if self.web_server_process.poll() is not None:
                    stdout, stderr = self.web_server_process.communicate()
                    print(f"Server stdout: {stdout.decode()}")
                    print(f"Server stderr: {stderr.decode()}")
                return False
            else:
                print("Web module not found, skipping web server start")
                return False

        except Exception as e:
            print(f"Error starting web server: {e}")
            return False

    def is_server_running(self) -> bool:
        """Check if the web server is running."""
        try:
            import urllib.request

            urllib.request.urlopen("http://localhost:5001", timeout=1)
            return True
        except (ConnectionError, OSError, TimeoutError):
            return False

    def stop_web_server(self) -> None:
        """Stop the Flask web server."""
        if self.web_server_process:
            try:
                self.web_server_process.terminate()
                self.web_server_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.web_server_process.kill()
            except Exception as e:
                print(f"Error stopping web server: {e}")
            finally:
                self.web_server_process = None

    def run_cli_tests(self) -> bool:
        """Run CLI functional tests."""
        print("\n" + "=" * 50)
        print("Running CLI Functional Tests")
        print("=" * 50)

        try:
            cli_test_dir = self.project_root / "tests" / "functional" / "cli"

            # Run CLI tests with pytest
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pytest",
                    str(cli_test_dir),
                    "-v",
                    "--tb=short",
                    f"--rootdir={self.project_root}",
                ],
                cwd=self.project_root,
                capture_output=True,
                text=True,
            )

            print(result.stdout)
            if result.stderr:
                print("STDERR:", result.stderr)

            success = result.returncode == 0
            self.test_results["cli"] = success

            if success:
                print("✅ CLI functional tests PASSED")
            else:
                print("❌ CLI functional tests FAILED")

            return success

        except Exception as e:
            print(f"Error running CLI tests: {e}")
            self.test_results["cli"] = False
            return False

    def run_web_tests(self) -> bool:
        """Run web functional tests."""
        print("\n" + "=" * 50)
        print("Running Web Functional Tests")
        print("=" * 50)

        # Start web server if needed
        if not self.start_web_server():
            print("❌ Failed to start web server for testing")
            self.test_results["web"] = False
            return False

        try:
            web_test_dir = self.project_root / "tests" / "functional" / "web"

            # Run web tests with pytest
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pytest",
                    str(web_test_dir),
                    "-v",
                    "--tb=short",
                    f"--rootdir={self.project_root}",
                ],
                cwd=self.project_root,
                capture_output=True,
                text=True,
            )

            print(result.stdout)
            if result.stderr:
                print("STDERR:", result.stderr)

            success = result.returncode == 0
            self.test_results["web"] = success

            if success:
                print("✅ Web functional tests PASSED")
            else:
                print("❌ Web functional tests FAILED")

            return success

        except Exception as e:
            print(f"Error running web tests: {e}")
            self.test_results["web"] = False
            return False
        finally:
            # Always stop the web server
            self.stop_web_server()

    def run_all_functional_tests(self) -> bool:
        """Run all functional tests."""
        print("Starting Functional Test Suite")
        print("=" * 50)

        # Setup environment
        if not self.setup_test_environment():
            print("❌ Failed to set up test environment")
            return False

        # Run tests
        cli_success = self.run_cli_tests()
        web_success = self.run_web_tests()

        # Print summary
        self.print_test_summary()

        return cli_success and web_success

    def print_test_summary(self) -> None:
        """Print test results summary."""
        print("\n" + "=" * 50)
        print("FUNCTIONAL TEST SUMMARY")
        print("=" * 50)

        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result)

        for test_type, result in self.test_results.items():
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"{test_type.upper()} Tests: {status}")

        print(f"\nOverall: {passed_tests}/{total_tests} test suites passed")

        if passed_tests == total_tests:
            print("🎉 All functional tests PASSED!")
        else:
            print("⚠️  Some functional tests FAILED")

    def cleanup(self) -> None:
        """Clean up test environment."""
        # Stop web server
        self.stop_web_server()

        # Clean up test database
        test_db_path = Path("test_weather.db")
        if test_db_path.exists():
            try:
                test_db_path.unlink()
            except Exception as e:
                print(f"Warning: Could not remove test database: {e}")


def run_specific_test_suite(suite: str) -> bool:
    """Run a specific test suite."""
    runner = FunctionalTestRunner()

    try:
        if not runner.setup_test_environment():
            return False

        if suite.lower() == "cli":
            return runner.run_cli_tests()
        elif suite.lower() == "web":
            return runner.run_web_tests()
        else:
            print(f"Unknown test suite: {suite}")
            print("Available suites: cli, web")
            return False
    finally:
        runner.cleanup()


def run_quick_smoke_tests() -> bool:
    """Run quick smoke tests for both CLI and web."""
    print("Running Quick Smoke Tests")
    print("=" * 30)

    runner = FunctionalTestRunner()

    try:
        if not runner.setup_test_environment():
            return False

        # Quick CLI test
        print("Testing CLI help command...")
        result = subprocess.run(
            [sys.executable, "-m", "weather_app.cli", "--help"],
            cwd=runner.project_root,
            capture_output=True,
            text=True,
            timeout=10,
        )
        cli_ok = result.returncode == 0 and "weather" in result.stdout.lower()
        print(f"CLI: {'✅ OK' if cli_ok else '❌ FAILED'}")

        # Quick web test
        print("Testing web server startup...")
        web_ok = runner.start_web_server()
        if web_ok:
            time.sleep(2)  # Give server time to fully start
            web_ok = runner.is_server_running()
        print(f"Web: {'✅ OK' if web_ok else '❌ FAILED'}")

        overall_ok = cli_ok and web_ok
        print(f"\nSmoke tests: {'✅ PASSED' if overall_ok else '❌ FAILED'}")

        return overall_ok

    except Exception as e:
        print(f"Error in smoke tests: {e}")
        return False
    finally:
        runner.cleanup()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run functional tests")
    parser.add_argument(
        "suite",
        nargs="?",
        choices=["all", "cli", "web", "smoke"],
        default="all",
        help="Test suite to run",
    )
    parser.add_argument(
        "--quick", action="store_true", help="Run quick smoke tests only"
    )

    args = parser.parse_args()

    if args.quick or args.suite == "smoke":
        success = run_quick_smoke_tests()
    elif args.suite == "all":
        runner = FunctionalTestRunner()
        try:
            success = runner.run_all_functional_tests()
        finally:
            runner.cleanup()
    else:
        success = run_specific_test_suite(args.suite)

    sys.exit(0 if success else 1)
