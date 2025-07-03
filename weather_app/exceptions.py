"""Custom exceptions for the weather application."""


class WeatherAppError(Exception):
    """Base exception class for all weather app errors."""

    def __init__(
        self,
        message: str = "An error occurred in the Weather App",
        *args: object,
        **kwargs: object,
    ) -> None:
        self.message: str = message
        super().__init__(message, *args, **kwargs)


class APIError(WeatherAppError):
    """Exception raised for errors with the weather API."""

    def __init__(
        self,
        message: str = "Weather API error",
        status_code: int | None = None,
        *args: object,
        **kwargs: object,
    ) -> None:
        self.status_code: int | None = status_code
        super().__init__(message, *args, **kwargs)


class InputError(WeatherAppError):
    """Exception raised for invalid user input."""

    def __init__(
        self,
        message: str = "Invalid user input",
        field: str | None = None,
        *args: object,
        **kwargs: object,
    ) -> None:
        self.field: str | None = field
        error_message: str = (
            f"{message}" if not field else f"{message} (field: {field})"
        )
        super().__init__(error_message, *args, **kwargs)


class DatabaseError(WeatherAppError):
    """Exception raised for database-related errors."""

    def __init__(
        self, message: str = "Database error occurred", *args: object, **kwargs: object
    ) -> None:
        super().__init__(message, *args, **kwargs)


class ConfigurationError(WeatherAppError):
    """Exception raised for application configuration errors."""

    def __init__(
        self,
        message: str = "Configuration error",
        setting: str | None = None,
        *args: object,
        **kwargs: object,
    ) -> None:
        self.setting: str | None = setting
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
