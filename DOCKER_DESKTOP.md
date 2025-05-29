# Weather Dashboard - Docker Desktop Setup

Run the Weather Dashboard locally using Docker Desktop with uv for fast builds.

## Quick Start

1. **Install Docker Desktop** (if not already installed)
2. **Set up your environment:**
   ```bash
   cp .env-template .env
   # Edit .env and add your WEATHER_API_KEY
   ```

3. **Run with docker-compose:**
   ```bash
   docker-compose up --build
   ```

4. **Access the application:**
   Open http://localhost:5000 in your browser

That's it! 🚀

## Simple Docker Commands

### Option 1: Using docker-compose (Recommended)

```bash
# Start the application
docker-compose up --build

# Run in background
docker-compose up -d --build

# Stop the application
docker-compose down

# View logs
docker-compose logs -f weather-dashboard

# Rebuild and restart
docker-compose up --build --force-recreate
```

### Option 2: Using Docker directly

```bash
# Build the image
docker build -f Dockerfile.web -t weather-dashboard:local .

# Run the container
docker run -d \
  --name weather-dashboard \
  -p 5000:5000 \
  --env-file .env \
  weather-dashboard:local

# View logs
docker logs -f weather-dashboard

# Stop and remove
docker stop weather-dashboard
docker rm weather-dashboard
```

## Environment Setup

Create your `.env` file with your API key:

```bash
# .env
WEATHER_API_KEY=your_weatherapi_key_here
FLASK_ENV=development
LOG_LEVEL=DEBUG
```

## Development Features

The setup includes:
- ✅ **Persistent data** - Database survives container restarts
- ✅ **Live logs** - Real-time application logs
- ✅ **Health checks** - Automatic container health monitoring
- ✅ **Hot reload** - Restart container to pick up changes

## Optional Services

Add PostgreSQL for production-like testing:
```bash
# Start with PostgreSQL
docker-compose --profile postgres up --build

# The app will still use SQLite by default
# To use PostgreSQL, update DATABASE_URL in .env:
# DATABASE_URL=postgresql://weather_user:weather_password@postgres:5432/weather_dashboard
```

Add Redis for caching (future enhancement):
```bash
# Start with Redis
docker-compose --profile redis up --build
```

## Useful Commands

```bash
# View running containers
docker ps

# Execute commands inside the container
docker exec -it weather-dashboard /bin/sh

# View container resource usage
docker stats weather-dashboard

# Clean up everything
docker-compose down -v  # Removes volumes too
docker system prune     # Clean up unused images/containers
```

## Development Workflow

1. **Make code changes** in your editor
2. **Restart the container:**
   ```bash
   docker-compose restart weather-dashboard
   ```
   Or for full rebuild:
   ```bash
   docker-compose up --build --force-recreate
   ```

3. **Test your changes** at http://localhost:5000

## Troubleshooting

### Common Issues

**Port already in use:**
```bash
# Find what's using port 5000
lsof -i :5000

# Use a different port
docker-compose up --build
# Edit docker-compose.yml: "5001:5000"
```

**Container won't start:**
```bash
# Check logs
docker-compose logs weather-dashboard

# Check if API key is set
docker exec weather-dashboard env | grep WEATHER_API_KEY
```

**Database issues:**
```bash
# Reset the database
docker-compose down -v
docker-compose up --build
```

**Out of disk space:**
```bash
# Clean up Docker
docker system prune -a
docker volume prune
```

## Production Testing

To test production-like settings locally:

```bash
# Set production environment
echo "FLASK_ENV=production" >> .env

# Rebuild with production settings
docker-compose up --build --force-recreate

# Test with PostgreSQL
docker-compose --profile postgres up --build
```

## Building for Different Platforms

If you need to build for deployment elsewhere:

```bash
# Build for Linux (common for cloud deployment)
docker build -f Dockerfile.web --platform linux/amd64 -t weather-dashboard:linux .

# Build for Apple Silicon
docker build -f Dockerfile.web --platform linux/arm64 -t weather-dashboard:arm64 .
```

## Performance Tips

- **Use BuildKit** for faster builds:
  ```bash
  export DOCKER_BUILDKIT=1
  docker-compose build
  ```

- **Cache dependencies** - The Dockerfile is optimized for layer caching

- **Limit resources** if needed:
  ```yaml
  # Add to docker-compose.yml under weather-dashboard:
  deploy:
    resources:
      limits:
        memory: 512M
        cpus: '0.5'
  ```

## Next Steps

- For **production deployment**, see `KUBERNETES_DEPLOYMENT.md`
- For **cloud deployment**, consider Docker Swarm or managed container services
- For **CI/CD**, integrate the docker build commands into your pipeline
