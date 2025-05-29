#!/bin/bash

set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        log_error "Docker is not running. Please start Docker Desktop."
        exit 1
    fi
    log_info "Docker is running"
}

# Check if .env file exists
check_env() {
    if [[ ! -f ".env" ]]; then
        log_warn ".env file not found. Creating from template..."
        if [[ -f ".env-template" ]]; then
            cp .env-template .env
            log_warn "Please edit .env and add your WEATHER_API_KEY"
            echo "Opening .env file..."
            ${EDITOR:-nano} .env || true
        else
            log_error ".env-template not found. Please create .env manually with WEATHER_API_KEY"
            exit 1
        fi
    fi

    # Check if API key is set
    if ! grep -q "WEATHER_API_KEY=.*[^[:space:]]" .env; then
        log_warn "WEATHER_API_KEY appears to be empty in .env file"
        log_warn "The application may not work properly without a valid API key"
    fi
}

# Start the application
start_app() {
    log_info "Starting Weather Dashboard..."
    docker-compose up --build
}

# Start in background
start_background() {
    log_info "Starting Weather Dashboard in background..."
    docker-compose up -d --build
    log_info "Application started! Access it at: http://localhost:5000"
    log_info "View logs with: docker-compose logs -f weather-dashboard"
    log_info "Stop with: docker-compose down"
}

# Stop the application
stop_app() {
    log_info "Stopping Weather Dashboard..."
    docker-compose down
    log_info "Application stopped"
}

# Show logs
show_logs() {
    log_info "Showing application logs (Press Ctrl+C to exit)..."
    docker-compose logs -f weather-dashboard
}

# Show status
show_status() {
    log_info "Application status:"
    docker-compose ps

    if docker-compose ps | grep -q "weather-dashboard.*Up"; then
        echo
        log_info "Weather Dashboard is running at: http://localhost:5000"
    fi
}

# Clean up
cleanup() {
    log_info "Cleaning up Docker resources..."
    docker-compose down -v
    docker system prune -f
    log_info "Cleanup complete"
}

# Rebuild and restart
rebuild() {
    log_info "Rebuilding and restarting application..."
    docker-compose down
    docker-compose up --build --force-recreate -d
    log_info "Application rebuilt and restarted!"
    log_info "Access at: http://localhost:5000"
}

# Main function
main() {
    case "${1:-start}" in
        "start")
            check_docker
            check_env
            start_app
            ;;
        "background"|"bg")
            check_docker
            check_env
            start_background
            ;;
        "stop")
            stop_app
            ;;
        "restart")
            check_docker
            stop_app
            start_background
            ;;
        "rebuild")
            check_docker
            check_env
            rebuild
            ;;
        "logs")
            show_logs
            ;;
        "status")
            show_status
            ;;
        "clean")
            cleanup
            ;;
        "setup")
            check_docker
            check_env
            log_info "Setup complete! Run './run-local.sh start' to begin"
            ;;
        *)
            echo "Weather Dashboard - Local Docker Runner"
            echo
            echo "Usage: $0 {start|background|stop|restart|rebuild|logs|status|clean|setup}"
            echo
            echo "Commands:"
            echo "  start      - Start the application (foreground with logs)"
            echo "  background - Start the application in background"
            echo "  stop       - Stop the application"
            echo "  restart    - Stop and start the application"
            echo "  rebuild    - Rebuild and restart the application"
            echo "  logs       - Show application logs"
            echo "  status     - Show application status"
            echo "  clean      - Clean up Docker resources"
            echo "  setup      - Initial setup (check requirements, create .env)"
            echo
            echo "Quick start:"
            echo "  1. ./run-local.sh setup"
            echo "  2. ./run-local.sh start"
            echo "  3. Open http://localhost:5000"
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
