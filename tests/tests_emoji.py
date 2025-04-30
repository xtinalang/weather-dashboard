from src.emoji import get_weather_emoji


def test_get_weather_emoji():
    assert get_weather_emoji("Sunny") == "☀️"
    assert get_weather_emoji("Cloudy") == "☁️"
    assert get_weather_emoji("Thunderstorm") == "⛈️"
    assert get_weather_emoji("Fog") == "🌫️"
    assert get_weather_emoji("Unknown") == "🌈"
