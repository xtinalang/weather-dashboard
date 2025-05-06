# Use the latest Alpine image with Python 3
FROM python:3.12-alpine

# Set the working directory inside the container
WORKDIR /weather_app

# Copy the application files into the container
COPY . /weather_app

# Install SQLite and build tools
RUN apk update && apk add --no-cache \
    sqlite \
    sqlite-dev \
    build-base  # Needed if you're building packages with C extensions

# Install any dependencies
#RUN pip install --no-cache-dir -r requirements.txt

#

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
CMD ["python"]
