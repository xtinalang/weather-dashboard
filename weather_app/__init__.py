import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("weather_app.log"), logging.StreamHandler()],
)

logger = logging.getLogger("weather_app")
