"""Custom exceptions for the weather application."""

from typing import Optional


class WeatherAppError(Exception):
    """Base exception class for all weather app errors."""

    def __init__(
        self, message: str = "An error occurred in the Weather App", *args, **kwargs
    ) -> None:
        self.message: str = message
        super().__init__(message, *args, **kwargs)


class APIError(WeatherAppError):
    """Exception raised for errors with the weather API."""

    def __init__(
        self,
        message: str = "Weather API error",
        status_code: Optional[int] = None,
        *args,
        **kwargs,
    ) -> None:
        self.status_code: Optional[int] = status_code
        super().__init__(message, *args, **kwargs)


class InputError(WeatherAppError):
    """Exception raised for invalid user input."""

    def __init__(
        self,
        message: str = "Invalid user input",
        field: Optional[str] = None,
        *args,
        **kwargs,
    ) -> None:
        self.field: Optional[str] = field
        error_message: str = (
            f"{message}" if not field else f"{message} (field: {field})"
        )
        super().__init__(error_message, *args, **kwargs)


class DatabaseError(WeatherAppError):
    """Exception raised for database-related errors."""

    def __init__(
        self, message: str = "Database error occurred", *args, **kwargs
    ) -> None:
        super().__init__(message, *args, **kwargs)


class ConfigurationError(WeatherAppError):
    """Exception raised for application configuration errors."""

    def __init__(
        self,
        message: str = "Configuration error",
        setting: Optional[str] = None,
        *args,
        **kwargs,
    ) -> None:
        self.setting: Optional[str] = setting
        error_message: str = (
            f"{message}" if not setting else f"{message} (setting: {setting})"
        )
        super().__init__(error_message, *args, **kwargs)


class SessionError(DatabaseError):
    """Error related to database session handling."""

    pass


class DetachedInstanceError(SessionError):
    """Error occurred when trying to access a detached database instance."""

    pass


class StaleDataError(SessionError):
    """Error occurred when data is stale or has been modified elsewhere."""

    pass
