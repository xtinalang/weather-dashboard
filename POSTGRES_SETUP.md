# PostgreSQL Setup for Weather Dashboard

This guide will help you set up PostgreSQL for use with the Weather Dashboard application.

## Prerequisites

1. PostgreSQL server (version 12 or higher recommended)
2. Python 3.9+
3. psycopg2-binary package

## Installation

### Install PostgreSQL

#### On Ubuntu/Debian:
```bash
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib
```

#### On macOS with Homebrew:
```bash
brew install postgresql
brew services start postgresql
```

#### On Windows:
Download and install from [PostgreSQL official website](https://www.postgresql.org/download/windows/)

### Install Required Python Packages

```bash
pip install sqlmodel psycopg2-binary
```

## Setup Database

### Create PostgreSQL Database

1. Log in to PostgreSQL as the postgres user:
   ```bash
   sudo -u postgres psql
   ```

2. Create a database and user for the application:
   ```sql
   CREATE DATABASE weather_app;
   CREATE USER weather_user WITH ENCRYPTED PASSWORD 'your_secure_password';
   GRANT ALL PRIVILEGES ON DATABASE weather_app TO weather_user;
   ```

3. Exit PostgreSQL:
   ```
   \q
   ```

## Configuration

### Set Environment Variables

Create a `.env` file in your project root with your PostgreSQL connection details:

```
WEATHER_APP_DATABASE_URL=postgresql://weather_user:your_secure_password@localhost:5432/weather_app
WEATHER_API_KEY=your_weather_api_key
```

## Database Initialization

The app will automatically create the necessary tables when it starts for the first time. No additional steps are required.

## Verifying the Setup

You can verify your PostgreSQL connection by running:

```bash
python -c "from weather_app.database import Database; db = Database(); print('Database connection successful!')"
```

## PostgreSQL-Specific Features

The ORM implementation includes several PostgreSQL-specific optimizations:

1. **Connection Pooling**: Configured for optimal concurrent access
2. **GiST Index for Locations**: Optimized for geographical queries
3. **Table Partitioning**: Weather records use time-based partitioning for efficient queries
4. **Prepared Statements**: Used automatically for improved performance

## Troubleshooting

### Common Issues

1. **Connection Refused**: Ensure PostgreSQL is running with `pg_ctl status` or `sudo service postgresql status`

2. **Authentication Failed**: Verify your username and password in the connection string

3. **Database Doesn't Exist**: Ensure you've created the weather_app database

4. **Permission Denied**: Ensure the user has proper privileges on the database

### PostgreSQL Logs

Check PostgreSQL logs for more detailed error information:

```bash
sudo tail -f /var/log/postgresql/postgresql-*.log
```

Or on macOS:
```bash
tail -f /usr/local/var/log/postgresql@*.log
```
