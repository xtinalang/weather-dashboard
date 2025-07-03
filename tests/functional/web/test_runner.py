#!/usr/bin/env python3
"""
Playwright Test Runner for Weather Dashboard
Runs Playwright tests organized by template with flexible options.
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path


def get_test_files():
    """Get available test files organized by template."""
    return {
        "index": "test_index.py",
        "weather": "test_weather.py",
        "forecast": "test_forecast.py",
        "search": "test_search.py",
        "integration": "test_integration.py",
    }


def run_pytest_command(test_files, args):
    """Execute pytest with specified files and arguments."""
    cmd = ["python", "-m", "pytest"]

    # Add test files
    cmd.extend(test_files)

    # Add pytest arguments based on user options
    if args.verbose:
        cmd.append("-v")
    else:
        cmd.append("-q")

    if args.headed:
        cmd.extend(["--headed"])

    if args.browser:
        cmd.extend(["--browser", args.browser])

    if args.workers:
        cmd.extend(["--numprocesses", str(args.workers)])

    if args.timeout:
        cmd.extend(["--timeout", str(args.timeout)])

    if args.retry:
        cmd.extend(["--maxfail", "3"])  # Stop after 3 failures for retry mode

    # Additional pytest options for async tests
    cmd.extend(["--tb=short"])  # Shorter traceback format
    cmd.extend(["--asyncio-mode=auto"])  # Enable async test mode

    print(f"🚀 Running command: {' '.join(cmd)}")
    print("-" * 60)

    try:
        result = subprocess.run(cmd, cwd=Path(__file__).parent)
        return result.returncode
    except KeyboardInterrupt:
        print("\n⚠️  Test execution interrupted by user")
        return 1
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return 1


def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(
        description="Run Playwright tests for Weather Dashboard",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python test_runner.py                    # Run all tests
  python test_runner.py --template weather # Run weather page tests only
  python test_runner.py --template index weather # Run multiple templates
  python test_runner.py --headed --verbose # Run with browser visible and verbose output
  python test_runner.py --browser firefox  # Run with Firefox browser
  python test_runner.py --workers 4        # Run with 4 parallel workers
        """,
    )

    available_tests = get_test_files()

    parser.add_argument(
        "--template",
        "-t",
        choices=list(available_tests.keys()) + ["all"],
        nargs="*",
        default=["all"],
        help="Template(s) to test (default: all)",
    )

    parser.add_argument(
        "--headed",
        action="store_true",
        help="Run tests with browser visible (default: headless)",
    )

    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose output"
    )

    parser.add_argument(
        "--browser",
        "-b",
        choices=["chromium", "firefox", "webkit"],
        default="chromium",
        help="Browser to use (default: chromium)",
    )

    parser.add_argument(
        "--workers",
        "-w",
        type=int,
        help="Number of parallel workers (pytest-xdist required)",
    )

    parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="Test timeout in seconds (default: 300)",
    )

    parser.add_argument("--retry", action="store_true", help="Enable retry on failures")

    args = parser.parse_args()

    # Determine which test files to run
    if "all" in args.template:
        test_files = list(available_tests.values())
        template_names = "all templates"
    else:
        test_files = [available_tests[template] for template in args.template]
        template_names = ", ".join(args.template)

    # Check if test files exist
    missing_files = []
    for test_file in test_files:
        if not Path(test_file).exists():
            missing_files.append(test_file)

    if missing_files:
        print(f"❌ Missing test files: {', '.join(missing_files)}")
        return 1

    # Display test run information
    print("🧪 Weather Dashboard Playwright Tests")
    print("=" * 60)
    print(f"📁 Templates: {template_names}")
    print(f"🌐 Browser: {args.browser}")
    print(f"👁️  Mode: {'headed' if args.headed else 'headless'}")
    print(f"📝 Verbosity: {'verbose' if args.verbose else 'quiet'}")

    if args.workers:
        print(f"⚡ Workers: {args.workers}")

    print(f"⏱️  Timeout: {args.timeout}s")
    print("=" * 60)

    # Run the tests
    start_time = time.time()
    exit_code = run_pytest_command(test_files, args)
    end_time = time.time()

    # Display results
    print("-" * 60)
    duration = end_time - start_time
    print(f"⏱️  Total duration: {duration:.2f} seconds")

    if exit_code == 0:
        print("✅ All tests passed!")
    else:
        print(f"❌ Tests failed with exit code: {exit_code}")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
