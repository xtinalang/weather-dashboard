#!/bin/bash

set -euo pipefail

# Configuration
REGISTRY="${REGISTRY:-your-registry.com}"
IMAGE_NAME="${IMAGE_NAME:-weather-dashboard}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
NAMESPACE="${NAMESPACE:-weather-dashboard}"
KUBECONFIG="${KUBECONFIG:-~/.kube/config}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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

# Check requirements
check_requirements() {
    log_info "Checking requirements..."

    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed or not in PATH"
        exit 1
    fi

    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed or not in PATH"
        exit 1
    fi

    if ! command -v uv &> /dev/null; then
        log_warn "uv is not installed. Building without uv optimizations."
    fi

    log_info "Requirements check passed"
}

# Build Docker image
build_image() {
    log_info "Building Docker image..."

    FULL_IMAGE_NAME="${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"

    docker build \
        -f Dockerfile.web \
        -t "${FULL_IMAGE_NAME}" \
        --platform linux/amd64 \
        .

    log_info "Image built successfully: ${FULL_IMAGE_NAME}"

    # Push to registry if not local
    if [[ "${REGISTRY}" != "localhost" && "${REGISTRY}" != "local" ]]; then
        log_info "Pushing image to registry..."
        docker push "${FULL_IMAGE_NAME}"
        log_info "Image pushed successfully"
    fi
}

# Update Kubernetes manifests
update_manifests() {
    log_info "Updating Kubernetes manifests..."

    # Update image in kustomization.yaml
    sed -i.bak "s|newTag: .*|newTag: ${IMAGE_TAG}|g" k8s/kustomization.yaml

    # Update image in deployment.yaml
    sed -i.bak "s|image: .*|image: ${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}|g" k8s/deployment.yaml

    log_info "Manifests updated"
}

# Create secrets
create_secrets() {
    log_info "Creating/updating secrets..."

    # Check if .env file exists
    if [[ -f ".env" ]]; then
        source .env

        # Encode API key
        if [[ -n "${WEATHER_API_KEY:-}" ]]; then
            ENCODED_API_KEY=$(echo -n "${WEATHER_API_KEY}" | base64)
            sed -i.bak "s|WEATHER_API_KEY: .*|WEATHER_API_KEY: ${ENCODED_API_KEY}|g" k8s/secret.yaml
            log_info "API key updated in secret"
        else
            log_warn "WEATHER_API_KEY not found in .env file"
        fi
    else
        log_warn ".env file not found. Please update k8s/secret.yaml manually"
    fi
}

# Deploy to Kubernetes
deploy() {
    log_info "Deploying to Kubernetes..."

    # Apply namespace first
    kubectl apply -f k8s/namespace.yaml

    # Apply all resources using kustomize
    kubectl apply -k k8s/

    # Wait for deployment
    log_info "Waiting for deployment to be ready..."
    kubectl wait --for=condition=available --timeout=300s deployment/weather-dashboard -n "${NAMESPACE}"

    log_info "Deployment completed successfully"
}

# Show deployment status
show_status() {
    log_info "Deployment status:"

    echo
    echo "Pods:"
    kubectl get pods -n "${NAMESPACE}" -l app=weather-dashboard

    echo
    echo "Services:"
    kubectl get services -n "${NAMESPACE}" -l app=weather-dashboard

    echo
    echo "Ingress:"
    kubectl get ingress -n "${NAMESPACE}" -l app=weather-dashboard

    echo
    echo "HPA:"
    kubectl get hpa -n "${NAMESPACE}" -l app=weather-dashboard
}

# Show logs
show_logs() {
    log_info "Recent logs:"
    kubectl logs -n "${NAMESPACE}" -l app=weather-dashboard --tail=50
}

# Cleanup function
cleanup() {
    log_info "Cleaning up temporary files..."
    find k8s/ -name "*.bak" -delete 2>/dev/null || true
}

# Main function
main() {
    case "${1:-deploy}" in
        "build")
            check_requirements
            build_image
            ;;
        "deploy")
            check_requirements
            build_image
            update_manifests
            create_secrets
            deploy
            show_status
            cleanup
            ;;
        "status")
            show_status
            ;;
        "logs")
            show_logs
            ;;
        "clean")
            log_info "Removing deployment..."
            kubectl delete -k k8s/ || true
            cleanup
            ;;
        *)
            echo "Usage: $0 {build|deploy|status|logs|clean}"
            echo
            echo "Commands:"
            echo "  build   - Build and push Docker image"
            echo "  deploy  - Build, push, and deploy to Kubernetes"
            echo "  status  - Show deployment status"
            echo "  logs    - Show recent application logs"
            echo "  clean   - Remove deployment from Kubernetes"
            echo
            echo "Environment variables:"
            echo "  REGISTRY    - Docker registry (default: your-registry.com)"
            echo "  IMAGE_NAME  - Image name (default: weather-dashboard)"
            echo "  IMAGE_TAG   - Image tag (default: latest)"
            echo "  NAMESPACE   - Kubernetes namespace (default: weather-dashboard)"
            exit 1
            ;;
    esac
}

# Trap cleanup on exit
trap cleanup EXIT

# Run main function
main "$@"
