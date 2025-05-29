# Database Architecture in Weather Dashboard

This document explains the database architecture of the Weather Dashboard application, how data is stored, retrieved, and managed across the application.

## Overview

The Weather Dashboard application uses SQLModel (a library that combines SQLAlchemy and Pydantic) to manage database operations. The architecture follows a clean separation of concerns with three main components:

1. **Models** (`models.py`): Data structures that represent database tables
2. **Database** (`database.py`): Database connection and session management
3. **Repositories** (`repository.py`): Classes that handle data access operations

This architecture provides several benefits:

- Separation of data model, database connection, and business logic
- Type safety through Python type hints
- Session management to prevent common SQL-related errors
- Error handling with custom exceptions

## Models (models.py)

The `models.py` file defines the data structures used throughout the application, both for database storage and in-memory manipulation.

### Key Features

- Uses SQLModel to define database tables and relationships
- Each model corresponds to a database table
- Models include validation rules and default values
- Relationships between models are explicitly defined
- Includes helper methods for common operations (like `to_dict()`)

### Main Models

1. **Location**: Stores geographical locations (cities, regions)
   - Has a one-to-many relationship with WeatherRecord
   - Tracked attributes include coordinates, country, region, favorite status

2. **WeatherRecord**: Stores historical weather data
   - Each record is associated with a specific location
   - Contains temperature, humidity, wind speed, etc.
   - Timestamped for historical tracking

3. **UserSettings**: Stores application preferences
   - Only one record exists (ID=1)
   - Includes temperature unit, theme, forecast days, etc.

### Code Example

```python
class Location(SQLModel, table=True):
    """Represents a geographical location for weather data"""

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    latitude: float
    longitude: float
    country: str = Field(index=True)
    region: Optional[str] = Field(default=None, index=True)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    is_favorite: bool = Field(default=False, index=True)

    # Relationships
    weather_records: List["WeatherRecord"] = Relationship(back_populates="location")
```

## Database Connection (database.py)

The `database.py` file manages database connections, sessions, and table creation/migrations.

### Key Features

- Singleton pattern to ensure a single database connection
- SQLite database stored in user's home directory
- Context managers for safe session handling
- Automatic table creation based on model definitions
- Support for initializing the database with default data

### Core Components

1. **Database Class**: Manages the database connection and provides session access
   - Implements a singleton pattern to ensure only one connection exists
   - Provides session management through context managers
   - Handles table creation and schema updates

2. **Initialization Functions**: Functions to initialize the database
   - `init_db()`: Creates all tables and initializes the database
   - `get_session()`: Provides a database session for operations

### Code Example

```python
class Database:
    """Database connection manager for the weather application"""

    _instance: Optional["Database"] = None
    _engine: Optional[Engine] = None

    def __new__(cls) -> "Database":
        """Singleton pattern to ensure only one database instance exists"""
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
            cls._initialize_db()
        return cls._instance

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """Get a database session"""
        session = Session(self.get_engine())
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
```

## Repositories (repository.py)

Repositories handle all database operations for a specific model, providing a clean interface for the rest of the application.

### Key Features

- Generic base repository with common CRUD operations
- Type-safe operations through generics
- Specific repositories for each model with custom operations
- Comprehensive error handling and logging
- Solutions for common SQLAlchemy issues like detached instances

### Repository Design

1. **BaseRepository**: Generic repository with common CRUD operations
   - Create, read, update, delete operations for any model
   - Error handling and consistent interface
   - Type-safe through Python generics

2. **Model-Specific Repositories**: Extend the base repository with specialized operations
   - **LocationRepository**: Location-specific operations
   - **WeatherRepository**: Weather record operations
   - **SettingsRepository**: User settings operations

3. **Session Management**: Each repository handles sessions properly
   - Sessions are opened when needed and closed afterward
   - Transactions are committed or rolled back appropriately
   - Detached objects are properly handled

### Code Example

```python
class BaseRepository(Generic[T]):
    """Base repository class with common CRUD operations"""

    model_class: Type[T]

    def __init__(self) -> None:
        self.db = Database()

    def create(self, obj: T) -> T:
        """Create a new database record"""
        try:
            with self.db.get_session() as session:
                session.add(obj)
                session.commit()
                session.refresh(obj)
                return obj
        except SQLAlchemyError as e:
            error_msg = f"Failed to create {self.model_class.__name__}: {e}"
            raise DatabaseError(error_msg) from e
```

## Session Management Across Components

The Weather Dashboard application manages database sessions across various components to ensure data consistency while preventing common issues like detached instances. This section explains how sessions are handled in different parts of the application.

### Session Lifecycle in the Application Flow

The application follows a specific pattern for session management:

1. **Session Creation**: Sessions are created when needed by repositories
2. **Data Retrieval**: Data is fetched from the database within a session
3. **Detached Copy Creation**: Detached copies are created before the session closes
4. **Session Closure**: The session is closed after database operations
5. **Working with Detached Objects**: The application works with detached objects

This approach helps prevent issues related to accessing session-bound objects after the session has closed.

### WeatherApp Class and Session Management

The `WeatherApp` class serves as the central orchestrator and implements several session-related patterns:

1. **Refreshing Locations**: The `refresh_location` method ensures a location object is attached to an active session:

   ```python
   def refresh_location(self, location: Location) -> Optional[Location]:
       """Refresh a location from the database to ensure it's attached to an active session"""
       try:
           # Use find_or_create method to get a fresh location object
           return self.location_repo.find_or_create_by_coordinates(
               name=location.name,
               latitude=location.latitude,
               longitude=location.longitude,
               country=location.country,
               region=location.region
           )
       except Exception as e:
           logger.error(f"Error refreshing location: {e}")
           return None
   ```

2. **Creating Detached Copies**: The `_return_fresh_location` method creates detached copies to avoid session issues:

   ```python
   def _return_fresh_location(self, location: Location) -> Location:
       """Create a fresh Location object detached from any session"""
       return Location(
           id=location.id,
           name=location.name,
           latitude=location.latitude,
           # ... other attributes
       )
   ```

### API Component and Sessions

The API component (`WeatherAPI` class) interacts with external services and does not directly use database sessions. However, it plays a crucial role in the application's session architecture:

1. **Data Retrieval**: The API retrieves data from external sources
2. **Session-Independent Data**: API responses are session-independent
3. **Data Transformation**: API data is transformed into model objects before saving to the database

This separation ensures that API operations don't interfere with database sessions.

### Location Management and Sessions

The `LocationManager` class manages locations and implements several session-related patterns:

1. **Finding Locations**: When finding locations, it uses repository methods that handle sessions internally:

   ```python
   def _use_saved_location(self) -> Optional[str]:
       """Use a previously saved location"""
       favorites = self.location_repo.get_favorites()  # Repository handles session
       # ...
   ```

2. **Saving Locations**: When saving locations from API data, it creates detached copies:

   ```python
   def _save_location_to_db(self, location_data: Dict) -> Dict:
       """Save a location to the database"""
       # Use repository method that creates detached copies
       location = self.location_repo.find_or_create_by_coordinates(
           name=location_data.get('name', 'Unknown'),
           latitude=float(location_data.get('lat', 0)),
           longitude=float(location_data.get('lon', 0)),
           # ...
       )

       # Return a dictionary rather than a session-bound object
       return {
           'id': location.id,
           'name': location.name,
           # ...
       }
   ```

### Display Component and Sessions

The `WeatherDisplay` class is responsible for displaying data to the user and is designed to be session-independent:

1. **Session-Independent Data**: The display class accepts plain data rather than database objects:

   ```python
   def show_current_weather(self, weather_data: Dict[str, Any], unit: str = "C") -> None:
       """Display current weather data"""
       # Works with data dictionary, not database objects
       # ...
   ```

2. **No Session Interaction**: The display component never interacts directly with database sessions

This design ensures that UI components don't need to worry about session management.

### Manager Classes and Sessions

Manager classes (like `CurrentWeatherManager` and `ForecastManager`) bridge the gap between API data and database persistence:

1. **Repository Composition**: Managers contain repository instances for database operations:

   ```python
   def __init__(self, api: WeatherAPI, display: WeatherDisplay):
       self.api = api
       self.display = display
       self.location_repo = LocationRepository()
       self.weather_repo = WeatherRepository()
       self.settings_repo = SettingsRepository()
   ```

2. **Session Handling**: Managers use repositories to handle sessions internally:

   ```python
   def get_current_weather(self, location: Location) -> None:
       """Get and display current weather for a location"""
       # Get settings using repository (handles session internally)
       settings = self.settings_repo.get_settings()

       # Get weather data from API (no session involved)
       weather_data = self.api.get_weather(f"{location.latitude},{location.longitude}")

       # Save to database using repository (handles session internally)
       self._save_weather_record(location, weather_data)

       # Display the data (no session involved)
       self.display.show_current_weather(weather_data, unit)
   ```

### Key Session Management Strategies

The application employs several strategies to manage sessions effectively:

1. **Session Scoping**: Sessions are kept to the smallest possible scope
2. **Detached Object Creation**: Detached copies are created when objects need to outlive sessions
3. **Dictionary Returns**: Functions often return dictionaries rather than database objects
4. **Error Recovery**: Repositories include fallback mechanisms when sessions fail
5. **Session Refresh**: Objects are refreshed when they might be detached

These strategies together create a robust system that handles database sessions properly while providing a clean interface to the rest of the application.

## Common Database Issues and Solutions

### Session Management Issues

One of the most common issues in SQLAlchemy applications is session management. Objects retrieved in one session may become "detached" when the session is closed, leading to errors when trying to access relationships or update the objects.

#### Solutions implemented in the Weather Dashboard:

1. **Detached Object Copies**:
   ```python
   def _create_detached_location_copy(self, location: Location) -> Location:
       """Create a detached copy of a location to avoid session issues"""
       detached_copy = Location(
           id=location.id,
           name=location.name,
           # ...other attributes...
       )
       return detached_copy
   ```

2. **Session Context Managers**:
   ```python
   with self.db.get_session() as session:
       # Operations using the session
       # Session is automatically closed when the block exits
   ```

3. **Custom Exception Handling**:
   ```python
   class DetachedInstanceError(SessionError):
       """Error occurred when trying to access a detached database instance."""
       pass
   ```

### Schema Changes

When the database schema changes (e.g., adding a column), existing databases need to be updated.

#### Solutions implemented:

1. **Database Migration Script**:
   - `migrate_database.py` in the Experimental folder
   - Adds missing columns to existing tables
   - Creates backups before migrations

2. **Default Values for New Columns**:
   - New columns have default values
   - Migration scripts set default values for existing records

3. **Error Recovery**:
   - Repositories handle missing columns gracefully
   - Default values are provided when errors occur

## Usage Patterns

### Creating a New Record

```python
# Create a new location
location_repo = LocationRepository()
new_location = Location(
    name="New York",
    latitude=40.7128,
    longitude=-74.0060,
    country="USA",
    region="New York"
)
created_location = location_repo.create(new_location)
```

### Finding Records

```python
# Find location by coordinates
location = location_repo.find_by_coordinates(latitude, longitude)

# Get all weather records for a location
weather_repo = WeatherRepository()
records = weather_repo.get_by_location(location.id)
```

### Updating Settings

```python
# Update temperature unit preference
settings_repo = SettingsRepository()
settings = settings_repo.update_temperature_unit("fahrenheit")
```

## Conclusion

The Weather Dashboard's database architecture follows modern best practices for Python applications:

1. **Clean Separation**: Models, database connection, and data access logic are separated
2. **Type Safety**: Strong typing through Python type hints
3. **Error Handling**: Comprehensive error handling and custom exceptions
4. **Session Management**: Proper session management to prevent common issues
5. **Migration Support**: Tools to handle schema changes

This architecture makes the application maintainable, testable, and scalable, while preventing common database-related issues.
