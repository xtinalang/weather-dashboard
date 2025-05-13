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

# Load environment variables from .env file if it exists
load_dotenv()

# # Set a default SECRET_KEY if not provided
# if not os.environ.get("SECRET_KEY"):
#     os.environ["SECRET_KEY"] = "dev-weather-dashboard-key"

# # Set Flask environment variables
# if os.environ.get("FLASK_ENV") != "production":
#     os.environ["FLASK_ENV"] = "development"
#     os.environ["FLASK_DEBUG"] = "1"

# Import after setting environment variables

if __name__ == "__main__":
    # Get port from environment or use default
    port = int(os.environ.get("PORT", 8008))

    print(f"Starting Weather Dashboard on http://localhost:{port}")
    print("Press Ctrl+C to stop the server")

    # Run the application
    app.run(
        host="0.0.0.0", port=port, debug=(os.environ.get("FLASK_ENV") == "development")
    )
