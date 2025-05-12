#!/usr/bin/env python3
"""
Run script for the Weather Dashboard web application.

This script initializes and runs the Flask web application
with appropriate configuration based on environment.
"""

import os

from dotenv import load_dotenv

# Import after setting environment variables
from web.app import app

# Load environment variables from .env file
load_dotenv()

# Set Flask environment variables
if os.environ.get("FLASK_ENV") != "production":
    os.environ["FLASK_ENV"] = "development"
    os.environ["FLASK_DEBUG"] = "1"


if __name__ == "__main__":
    # Get port from environment or use default
    port = int(os.environ.get("PORT", 5000))

    # Run the application
    app.run(
        host="0.0.0.0", port=port, debug=(os.environ.get("FLASK_ENV") == "development")
    )
