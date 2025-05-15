#!/usr/bin/env python
"""
Flask runner module to launch the Flask app from an entry point.
This allows us to define a console script in pyproject.toml that effectively
runs 'flask run' but as a proper Python entry point.
"""

import os
import subprocess
import sys


def main():
    """
    Run Flask development server with the correct settings.
    Equivalent to 'flask run' but can be called from an entry point.
    """
    # Make sure FLASK_APP is set
    if "FLASK_APP" not in os.environ:
        os.environ["FLASK_APP"] = "web.app"

    # Default port
    port = os.environ.get("FLASK_RUN_PORT", "5001")

    # Get any additional arguments passed to the command
    args = sys.argv[1:]

    # Get the proper flask executable
    flask_cmd = subprocess.check_output(["which", "flask"]).decode().strip()

    # Build the command
    cmd = [flask_cmd, "run", "--port", port]

    # Add any additional arguments
    cmd.extend(args)

    # Print what we're about to run
    print(f"Running: {' '.join(cmd)}")

    # Execute flask run
    os.execvp(cmd[0], cmd)


if __name__ == "__main__":
    main()
