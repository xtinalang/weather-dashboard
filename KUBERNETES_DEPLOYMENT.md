# Weather Dashboard - Kubernetes Deployment Guide

This guide explains how to deploy the Weather Dashboard application on Kubernetes using uv for dependency management.

## Prerequisites

- **Docker** - For building container images
- **kubectl** - Kubernetes command-line tool
- **uv** - Python package manager (recommended)
- **Kubernetes cluster** - Local (minikube, kind) or cloud-based
- **Container registry** - Docker Hub, GitHub Container Registry, or private registry

## Quick Start

1. **Clone and prepare the application:**
   ```bash
   git clone <your-repo>
   cd weather-dashboard
   ```

2. **Set up environment variables:**
   ```bash
   cp .env-template .env
   # Edit .env and add your WEATHER_API_KEY
   ```

3. **Configure deployment:**
   ```bash
   export REGISTRY="your-registry.com"  # or docker.io/your-username
   export IMAGE_TAG="v1.0.0"
   ```

4. **Deploy:**
   ```bash
   ./scripts/build-and-deploy.sh deploy
   ```

## Detailed Deployment Steps

### 1. Prepare Environment

Create your `.env` file with required configuration:
```bash
WEATHER_API_KEY=your_weatherapi_key_here
FLASK_SECRET_KEY=your_secret_key_here
```

### 2. Build Docker Image

The deployment uses a multi-stage Docker build optimized for uv:

```bash
# Build locally for testing
docker build -f Dockerfile.web -t weather-dashboard:latest .

# Build and push to registry
REGISTRY=your-registry.com ./scripts/build-and-deploy.sh build
```

### 3. Configure Kubernetes Manifests

Update the following files with your specific configuration:

**k8s/secret.yaml:**
```bash
# Encode your API key
echo -n "your-api-key" | base64
# Update the WEATHER_API_KEY value in secret.yaml
```

**k8s/ingress.yaml:**
```yaml
# Update the host field
host: weather-dashboard.yourdomain.com
```

**k8s/deployment.yaml:**
```yaml
# Update the image field
image: your-registry.com/weather-dashboard:latest
```

### 4. Deploy to Kubernetes

#### Option A: Using the deployment script (recommended)
```bash
# Full deployment
./scripts/build-and-deploy.sh deploy

# Check status
./scripts/build-and-deploy.sh status

# View logs
./scripts/build-and-deploy.sh logs
```

#### Option B: Manual deployment with kubectl
```bash
# Apply all manifests
kubectl apply -k k8s/

# Check deployment status
kubectl get pods -n weather-dashboard
kubectl get services -n weather-dashboard
kubectl get ingress -n weather-dashboard
```

#### Option C: Using kustomize directly
```bash
# Build and preview
kubectl kustomize k8s/

# Apply
kubectl apply -k k8s/
```

## Configuration Options

### Environment Variables

The application supports the following environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `WEATHER_API_KEY` | WeatherAPI.com API key | Required |
| `FLASK_ENV` | Flask environment | `production` |
| `DATABASE_URL` | Database connection string | `sqlite:///app/data/weather.db` |
| `LOG_LEVEL` | Logging level | `INFO` |

### Resource Configuration

Default resource limits and requests:

```yaml
resources:
  requests:
    memory: "128Mi"
    cpu: "100m"
  limits:
    memory: "512Mi"
    cpu: "500m"
```

Adjust these values in `k8s/deployment.yaml` based on your needs.

### Scaling Configuration

The deployment includes Horizontal Pod Autoscaler (HPA):

- **Min replicas:** 2
- **Max replicas:** 10
- **CPU target:** 70%
- **Memory target:** 80%

Modify `k8s/hpa.yaml` to adjust scaling behavior.

## Storage

The application uses a PersistentVolumeClaim for SQLite database storage:

- **Size:** 1Gi
- **Access mode:** ReadWriteOnce
- **Mount path:** `/app/data`

For production, consider using a cloud-native database instead of SQLite.

## Networking

### Internal Communication
- **Service:** `weather-dashboard-service`
- **Port:** 80 (maps to container port 5000)
- **Type:** ClusterIP

### External Access
- **Ingress:** `weather-dashboard-ingress`
- **Host:** Configure in `k8s/ingress.yaml`
- **TLS:** Optional, configure with cert-manager

## Security

The deployment includes several security best practices:

- **Non-root user:** Containers run as user ID 1001
- **Read-only filesystem:** Mostly read-only with specific writable volumes
- **Security context:** Drops all capabilities
- **Network policies:** Consider adding for production
- **Secrets management:** API keys stored in Kubernetes secrets

## Monitoring and Health Checks

### Health Checks
- **Liveness probe:** HTTP GET on `/` (port 5000)
- **Readiness probe:** HTTP GET on `/` (port 5000)

### Monitoring
Consider adding:
- Prometheus metrics endpoint
- Grafana dashboards
- Alerting rules

## Production Considerations

### High Availability
- Deploy across multiple availability zones
- Use pod anti-affinity rules
- Configure node selectors and tolerations

### Database
For production, consider migrating from SQLite to:
- PostgreSQL (cloud-managed)
- MySQL/MariaDB
- Cloud-native solutions (AWS RDS, Google Cloud SQL)

### Security Enhancements
- Enable network policies
- Use Pod Security Standards
- Implement RBAC
- Use external secrets management (AWS Secrets Manager, HashiCorp Vault)

### Observability
```yaml
# Add to deployment.yaml
env:
- name: ENABLE_METRICS
  value: "true"
- name: METRICS_PORT
  value: "9090"
```

## Troubleshooting

### Common Issues

1. **Pods not starting:**
   ```bash
   kubectl describe pod -n weather-dashboard
   kubectl logs -n weather-dashboard -l app=weather-dashboard
   ```

2. **Image pull errors:**
   - Check registry credentials
   - Verify image name and tag
   - Ensure registry is accessible from cluster

3. **Database connection issues:**
   - Check volume mounts
   - Verify database initialization
   - Review file permissions

4. **External access issues:**
   - Verify ingress controller is installed
   - Check DNS configuration
   - Validate TLS certificates

### Useful Commands

```bash
# View all resources
kubectl get all -n weather-dashboard

# Describe a specific pod
kubectl describe pod <pod-name> -n weather-dashboard

# Get logs from all pods
kubectl logs -n weather-dashboard -l app=weather-dashboard --tail=100

# Port forward for local testing
kubectl port-forward service/weather-dashboard-service 8080:80 -n weather-dashboard

# Execute commands in a pod
kubectl exec -it <pod-name> -n weather-dashboard -- /bin/sh

# Check HPA status
kubectl get hpa -n weather-dashboard -w
```

## Cleanup

To remove the deployment:

```bash
# Using the script
./scripts/build-and-deploy.sh clean

# Manual cleanup
kubectl delete -k k8s/
```

## Example Production Deployment

For a production deployment with custom domain and TLS:

1. **Update ingress with your domain:**
   ```yaml
   # k8s/ingress.yaml
   spec:
     tls:
     - hosts:
       - weather.yourdomain.com
       secretName: weather-dashboard-tls
     rules:
     - host: weather.yourdomain.com
   ```

2. **Deploy with production settings:**
   ```bash
   export REGISTRY="your-registry.com"
   export IMAGE_TAG="v1.0.0"
   export NAMESPACE="weather-dashboard"

   ./scripts/build-and-deploy.sh deploy
   ```

3. **Verify deployment:**
   ```bash
   # Check all components
   kubectl get all,ing,pvc,secrets,cm -n weather-dashboard

   # Test external access
   curl -I https://weather.yourdomain.com
   ```

## Support

For issues and questions:
- Check logs: `kubectl logs -n weather-dashboard -l app=weather-dashboard`
- Review pod status: `kubectl get pods -n weather-dashboard -o wide`
- Check events: `kubectl get events -n weather-dashboard --sort-by='.lastTimestamp'`
