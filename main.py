from app import WeatherApp
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("weather_app.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("weather_app")

if __name__ == "__main__":
    try:
        app = WeatherApp()
        app.run()
    except Exception as e:
        logger.critical("Fatal error", exc_info=True)
