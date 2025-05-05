import logging

logger = logging.getLogger("weather_app")


def get_weather_emoji(condition: str) -> str:
    condition = condition.lower()
    emoji_map = {
        "sunny": "☀️",
        "cloud": "☁️",
        "rain": "🌧️",
        "drizzle": "🌧️",
        "thunder": "⛈️",
        "snow": "❄️",
        "fog": "🌫️",
        "mist": "🌫️",
        "clear": "🌕",
        "wind": "🌬️",
    }
    for key, emoji in emoji_map.items():
        if key in condition:
            return emoji
    return "🌈"
