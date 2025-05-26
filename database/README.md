# Experimental Tools and Scripts

This directory contains experimental tools, scripts, and utilities for the Weather Dashboard application.

## Database Migration

### migrate_database.py

This script updates the database schema to add any missing columns required by the latest version of the application.

#### What it does:

1. Creates a backup of your existing database before making any changes
2. Adds the `forecast_days` column to the UserSettings table if it doesn't exist
3. Sets a default value (5) for the column if it's NULL

#### When to use:

Run this script when you:
- Update to a new version of the application that includes schema changes
- See errors like `no such column: usersettings.forecast_days` in the logs
- Want to ensure your database schema is up-to-date

#### How to run:

```bash
# Navigate to the project root
cd /path/to/weather-dashboard

# Run the migration script
python Experimental/migrate_database.py
```

#### What to expect:

The script will:
1. Create a backup of your database (with timestamp in the filename)
2. Check for missing columns and add them
3. Provide feedback on the changes made

If the script completes successfully, you'll see:
```
✅ Migration completed successfully!
```

If there are issues, check the `migration.log` file for details.

## Other Experimental Tools

The other scripts in this directory are experimental and may not be fully supported. Use them at your own risk.

- `emoji.py`: Experimental emoji support for the display
- `display.py`: Alternative display implementation
- `api.py`: Extended API functionality
- `main.py`: Alternative entry point
- `locations.py`: Location management utilities
- `app1.py`: Original application implementation
