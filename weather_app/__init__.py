import logging

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(module)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("weather_app.log")],
)

logger = logging.getLogger("weather_app")

# # Example logs
# # logger.debug("Debug message")
# # logger.info("Info message")
# # logger.warning("Warning message")
# # logger.error("Error message")
# # logger.critical("Critical message")
