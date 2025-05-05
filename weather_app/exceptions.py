"""Custom exceptions for the weather application"""

from typing import Optional


class WeatherAppError(Exception):
    """Base exception class for all weather app errors"""

    def __init__(
        self, message: str = "An error occurred in the Weather App", *args, **kwargs
    ):
        self.message = message
        super().__init__(message, *args, **kwargs)


class APIError(WeatherAppError):
    """Exception raised for errors with the weather API"""

    def __init__(
        self,
        message: str = "Weather API error",
        status_code: Optional[int] = None,
        *args,
        **kwargs,
    ):
        self.status_code = status_code
        super().__init__(message, *args, **kwargs)


class InputError(WeatherAppError):
    """Exception raised for invalid user input"""

    def __init__(
        self,
        message: str = "Invalid user input",
        field: Optional[str] = None,
        *args,
        **kwargs,
    ):
        self.field = field
        error_message = f"{message}" if not field else f"{message} (field: {field})"
        super().__init__(error_message, *args, **kwargs)


class DatabaseError(WeatherAppError):
    """Exception raised for database-related errors"""

    def __init__(self, message: str = "Database error occurred", *args, **kwargs):
        super().__init__(message, *args, **kwargs)


class ConfigurationError(WeatherAppError):
    """Exception raised for application configuration errors"""

    def __init__(
        self,
        message: str = "Configuration error",
        setting: Optional[str] = None,
        *args,
        **kwargs,
    ):
        self.setting = setting
        error_message = (
            f"{message}" if not setting else f"{message} (setting: {setting})"
        )
        super().__init__(error_message, *args, **kwargs)
