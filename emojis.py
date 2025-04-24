# Version 1: Using match/case (Python 3.10+)
def get_weather_emoji(condition):
    """Return an emoji matching the weather condition"""
    condition = condition.lower()
    
    match condition:
        case condition if "sunny" in condition:
            return "☀️"
        case condition if "cloud" in condition:
            return "☁️"
        case condition if "rain" in condition or "drizzle" in condition:
            return "🌧️"
        case condition if "thunder" in condition:
            return "⛈️"
        case condition if "snow" in condition:
            return "❄️"
        case condition if "fog" in condition or "mist" in condition:
            return "🌫️"
        case condition if "clear" in condition:
            return "🌕"
        case condition if "wind" in condition:
            return "🌬️"
        case _:
            return "🌈"  # Default cute fallback


# Version 2: Using a dictionary with key functions
def get_weather_emoji_dict(condition):
    """Return an emoji matching the weather condition using dictionary lookup"""
    condition = condition.lower()
    
    # Define mapping of condition checks to emojis
    condition_map = {
        lambda c: "sunny" in c: "☀️",
        lambda c: "cloud" in c: "☁️",
        lambda c: "rain" in c or "drizzle" in c: "🌧️",
        lambda c: "thunder" in c: "⛈️",
        lambda c: "snow" in c: "❄️",
        lambda c: "fog" in c or "mist" in c: "🌫️",
        lambda c: "clear" in c: "🌕",
        lambda c: "wind" in c: "🌬️",
    }
    
    # Find the first matching condition
    for check_func, emoji in condition_map.items():
        if check_func(condition):
            return emoji
            
    return "🌈"  # Default cute fallback


# Version 3: Using a simpler dictionary approach with substring checks
def get_weather_emoji_simple_dict(condition):
    """Return an emoji matching the weather condition using simple dictionary lookup"""
    condition = condition.lower()
    
    # Map of substrings to check for
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
        "wind": "🌬️"
    }
    
    # Check each key in the dictionary
    for key, emoji in emoji_map.items():
        if key in condition:
            return emoji
            
    return "🌈"  # Default cute fallback


# Example usage
if __name__ == "__main__":
    test_conditions = [
        "Sunny with clear skies",
        "Cloudy with a chance of rain",
        "Light drizzle expected",
        "Thunderstorms in the evening",
        "Heavy snow",
        "Morning fog",
        "Clear night",
        "Windy conditions",
        "Hazy"
    ]
    
    print("Testing match/case version:")
    for condition in test_conditions:
        print(f"{condition}: {get_weather_emoji(condition)}")
    
    print("\nTesting dictionary with lambdas version:")
    for condition in test_conditions:
        print(f"{condition}: {get_weather_emoji_dict(condition)}")
        
    print("\nTesting simple dictionary version:")
    for condition in test_conditions:
        print(f"{condition}: {get_weather_emoji_simple_dict(condition)}")