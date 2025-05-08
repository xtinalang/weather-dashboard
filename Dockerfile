# Use the latest Alpine image with Python 3
FROM python:3.12-alpine

# Set the working directory inside the container
WORKDIR /app

# Install SQLite and build tools needed for SQLModel
RUN apk update && apk add --no-cache \
    sqlite \
    build-base

# Copy just the requirements first (for better caching)
COPY pyproject.toml ./

# Install the package
RUN pip install --no-cache-dir -e .

# Copy the application files
COPY . .

# Create data directory for SQLite
RUN mkdir -p /root/.weather_app

# Expose the port for potential future web interface
EXPOSE 8000

# Command to run the application in interactive mode
CMD ["python", "-m", "weather_app", "interactive"]
