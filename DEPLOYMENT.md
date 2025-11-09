# Production Deployment Guide

This guide provides comprehensive instructions for deploying AgentKit in production environments using Docker.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Production Deployment Options](#production-deployment-options)
  - [Option 1: Docker Compose (Recommended)](#option-1-docker-compose-recommended)
  - [Option 2: Docker Swarm](#option-2-docker-swarm)
  - [Option 3: Kubernetes](#option-3-kubernetes)
- [Configuration](#configuration)
- [Health Checks and Monitoring](#health-checks-and-monitoring)
- [Security Best Practices](#security-best-practices)
- [Scaling](#scaling)
- [Backup and Recovery](#backup-and-recovery)
- [Troubleshooting](#troubleshooting)
- [Maintenance](#maintenance)

---

## Prerequisites

### System Requirements

- **Operating System**: Linux (Ubuntu 20.04+, Debian 11+, CentOS 8+) or macOS
- **CPU**: Minimum 2 cores (4+ recommended for production)
- **RAM**: Minimum 4GB (8GB+ recommended for production)
- **Storage**: 20GB+ available disk space
- **Docker**: Version 20.10.0 or higher
- **Docker Compose**: Version 2.0.0 or higher

### Required API Keys

Before deployment, obtain the following API keys:

1. **Google Gemini API Key**
   - Sign up at: https://makersuite.google.com/app/apikey
   - Free tier available with generous limits

2. **Tavily API Key**
   - Sign up at: https://tavily.com
   - Required for web search functionality

---

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/aramb-dev/agentkit.git
cd agentkit
```

### 2. Configure Environment Variables

```bash
# Copy the example environment file
cp .env.example .env

# Edit the file with your API keys and settings
nano .env
```

**Required changes in `.env`:**
```bash
GOOGLE_API_KEY=your_actual_gemini_api_key
TAVILY_API_KEY=your_actual_tavily_api_key
ENVIRONMENT=production
VITE_API_URL=http://your-domain.com:8000  # Update with your domain
```

### 3. Deploy with Docker Compose

```bash
# Production deployment
docker-compose -f docker-compose.prod.yml up -d

# Check status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f
```

### 4. Verify Deployment

```bash
# Check backend health
curl http://localhost:8000/healthz

# Check frontend
curl http://localhost:80

# Check readiness
curl http://localhost:8000/readyz
```

---

## Production Deployment Options

### Option 1: Docker Compose (Recommended)

Docker Compose is the simplest way to deploy AgentKit for small to medium-scale production environments.

#### Step-by-Step Deployment

**1. Prepare the Environment**

```bash
# Create data directories
mkdir -p data uploads chroma_db

# Set proper permissions
chmod 755 data uploads chroma_db
```

**2. Configure Production Environment**

Edit `.env` file with production settings:

```bash
# Required API Keys
GOOGLE_API_KEY=your_key_here
TAVILY_API_KEY=your_key_here

# Production Settings
ENVIRONMENT=production
LOG_LEVEL=INFO

# Port Configuration
BACKEND_PORT=8000
FRONTEND_PORT=80

# API URL (update with your domain)
VITE_API_URL=https://api.yourdomain.com

# Data Paths
DATA_PATH=/var/lib/agentkit/data
UPLOADS_PATH=/var/lib/agentkit/uploads
CHROMA_PATH=/var/lib/agentkit/chroma_db

# File Size (50MB default)
MAX_FILE_SIZE=52428800

# Conversation Settings
CONVERSATION_HISTORY_LIMIT=50

# Retry Logic
ENABLE_RETRY_LOGIC=true
MAX_RETRY_ATTEMPTS=3
RETRY_DELAY_SECONDS=1
```

**3. Build and Deploy**

```bash
# Build the images
docker-compose -f docker-compose.prod.yml build

# Start services
docker-compose -f docker-compose.prod.yml up -d

# Verify health
docker-compose -f docker-compose.prod.yml exec backend curl http://localhost:8000/healthz
```

**4. Monitor Logs**

```bash
# All services
docker-compose -f docker-compose.prod.yml logs -f

# Backend only
docker-compose -f docker-compose.prod.yml logs -f backend

# Frontend only
docker-compose -f docker-compose.prod.yml logs -f frontend
```

**5. Updates and Maintenance**

```bash
# Pull latest changes
git pull

# Rebuild and restart
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d

# Or use rolling update
docker-compose -f docker-compose.prod.yml up -d --no-deps --build backend
```

---

### Option 2: Docker Swarm

For high-availability deployments with multiple nodes.

**Initialize Swarm**

```bash
# On manager node
docker swarm init

# On worker nodes (use token from init output)
docker swarm join --token <token> <manager-ip>:2377
```

**Deploy Stack**

```bash
# Create overlay network
docker network create --driver overlay agentkit-network

# Deploy the stack
docker stack deploy -c docker-compose.prod.yml agentkit

# Check services
docker stack services agentkit

# View logs
docker service logs -f agentkit_backend
```

**Scale Services**

```bash
# Scale backend to 3 replicas
docker service scale agentkit_backend=3

# Scale frontend to 2 replicas
docker service scale agentkit_frontend=2
```

---

### Option 3: Kubernetes

For large-scale, enterprise deployments.

**1. Create Namespace**

```bash
kubectl create namespace agentkit
```

**2. Create Secrets**

```bash
kubectl create secret generic agentkit-secrets \
  --from-literal=GOOGLE_API_KEY=your_key_here \
  --from-literal=TAVILY_API_KEY=your_key_here \
  -n agentkit
```

**3. Deploy Application**

Create `k8s-deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: agentkit-backend
  namespace: agentkit
spec:
  replicas: 3
  selector:
    matchLabels:
      app: agentkit-backend
  template:
    metadata:
      labels:
        app: agentkit-backend
    spec:
      containers:
      - name: backend
        image: agentkit-backend:latest
        ports:
        - containerPort: 8000
        envFrom:
        - secretRef:
            name: agentkit-secrets
        livenessProbe:
          httpGet:
            path: /healthz
            port: 8000
          initialDelaySeconds: 40
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /readyz
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 10
        resources:
          requests:
            memory: "1Gi"
            cpu: "1"
          limits:
            memory: "2Gi"
            cpu: "2"
---
apiVersion: v1
kind: Service
metadata:
  name: agentkit-backend
  namespace: agentkit
spec:
  selector:
    app: agentkit-backend
  ports:
  - port: 8000
    targetPort: 8000
  type: ClusterIP
```

Apply the configuration:

```bash
kubectl apply -f k8s-deployment.yaml
```

---

## Configuration

### Reverse Proxy Setup (Nginx)

For production with SSL/TLS support.

**Create `nginx/nginx.conf`:**

```nginx
upstream backend {
    server backend:8000;
}

upstream frontend {
    server frontend:8080;
}

# HTTP redirect to HTTPS
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

# HTTPS server
server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    # SSL configuration
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Backend API
    location /api/ {
        proxy_pass http://backend/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Frontend
    location / {
        proxy_pass http://frontend/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

**Deploy with Nginx:**

```bash
# Update docker-compose.prod.yml to use nginx profile
docker-compose -f docker-compose.prod.yml --profile with-nginx up -d
```

---

## Health Checks and Monitoring

### Built-in Health Endpoints

AgentKit provides three health check endpoints:

1. **Liveness Probe** - `/healthz`
   ```bash
   curl http://localhost:8000/healthz
   # Response: {"status": "ok", "version": "1.0.0", "timestamp": "..."}
   ```

2. **Readiness Probe** - `/readyz`
   ```bash
   curl http://localhost:8000/readyz
   # Response: {"ready": true, "checks": {...}, "timestamp": "..."}
   ```

3. **System Status** - `/status`
   ```bash
   curl http://localhost:8000/status
   # Detailed system information including configuration and capabilities
   ```

### Monitoring with Prometheus

**Add to `docker-compose.prod.yml`:**

```yaml
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    ports:
      - "9090:9090"
    networks:
      - agentkit-network
```

**Create `prometheus.yml`:**

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'agentkit'
    static_configs:
      - targets: ['backend:8000']
```

### Log Aggregation

**Using Docker logging driver:**

```yaml
services:
  backend:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

**Using external logging (e.g., Loki):**

```yaml
  loki:
    image: grafana/loki:latest
    ports:
      - "3100:3100"
    volumes:
      - loki-data:/loki
    networks:
      - agentkit-network
```

---

## Security Best Practices

### 1. API Key Security

- **Never commit API keys to version control**
- Use environment variables or secret management systems
- Rotate keys regularly
- Use different keys for dev/staging/prod

### 2. Network Security

```bash
# Restrict external access to backend (use reverse proxy)
# Update docker-compose.prod.yml:
services:
  backend:
    ports:
      - "127.0.0.1:8000:8000"  # Only localhost access
```

### 3. Container Security

- Run containers as non-root users (already configured)
- Use minimal base images (alpine)
- Scan images for vulnerabilities:

```bash
docker scan agentkit-backend:latest
```

### 4. File Upload Security

- Set appropriate `MAX_FILE_SIZE` limits
- Validate file types server-side
- Scan uploaded files for malware
- Use separate storage volumes

### 5. Database Security

- Regular backups
- Encrypted volumes for sensitive data
- Access controls and authentication

---

## Scaling

### Horizontal Scaling

**Docker Compose:**

```bash
docker-compose -f docker-compose.prod.yml up -d --scale backend=3
```

**Kubernetes:**

```bash
kubectl scale deployment agentkit-backend --replicas=5 -n agentkit
```

### Vertical Scaling

Update resource limits in `docker-compose.prod.yml`:

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 4G
        reservations:
          cpus: '2'
          memory: 2G
```

### Load Balancing

Use Nginx or HAProxy for load balancing:

```nginx
upstream backend_servers {
    least_conn;
    server backend-1:8000;
    server backend-2:8000;
    server backend-3:8000;
}
```

---

## Backup and Recovery

### Automated Backup Script

Create `backup.sh`:

```bash
#!/bin/bash

BACKUP_DIR="/var/backups/agentkit"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup database
docker exec agentkit-backend-prod tar -czf - /app/data > \
  $BACKUP_DIR/database_$DATE.tar.gz

# Backup uploads
docker exec agentkit-backend-prod tar -czf - /app/uploads > \
  $BACKUP_DIR/uploads_$DATE.tar.gz

# Backup vector store
docker exec agentkit-backend-prod tar -czf - /app/chroma_db > \
  $BACKUP_DIR/chroma_$DATE.tar.gz

# Remove backups older than 30 days
find $BACKUP_DIR -type f -mtime +30 -delete

echo "Backup completed: $DATE"
```

**Schedule with cron:**

```bash
# Run daily at 2 AM
0 2 * * * /path/to/backup.sh >> /var/log/agentkit-backup.log 2>&1
```

### Recovery

```bash
# Stop services
docker-compose -f docker-compose.prod.yml down

# Restore data
docker run --rm -v agentkit-data:/app/data -v /path/to/backup:/backup \
  alpine tar -xzf /backup/database_YYYYMMDD_HHMMSS.tar.gz -C /

# Restart services
docker-compose -f docker-compose.prod.yml up -d
```

---

## Troubleshooting

### Common Issues

**1. Services won't start**

```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs

# Check disk space
df -h

# Check Docker resources
docker system df
```

**2. API errors (503)**

```bash
# Check readiness
curl http://localhost:8000/readyz

# Verify API keys
docker-compose -f docker-compose.prod.yml exec backend env | grep API_KEY
```

**3. Out of memory**

```bash
# Check container memory usage
docker stats

# Increase memory limits in docker-compose.prod.yml
# Or increase host RAM
```

**4. File upload failures**

```bash
# Check file size limits
curl http://localhost:8000/status

# Verify upload directory permissions
docker-compose exec backend ls -la /app/uploads

# Check reverse proxy limits (nginx)
```

### Debug Mode

Enable detailed logging:

```bash
# Update .env
LOG_LEVEL=DEBUG

# Restart services
docker-compose -f docker-compose.prod.yml restart
```

---

## Maintenance

### Regular Tasks

**Weekly:**
- Review logs for errors
- Check disk space usage
- Verify backups are running

**Monthly:**
- Update Docker images
- Review and rotate API keys
- Check for security updates
- Analyze performance metrics

**Quarterly:**
- Review and optimize resource allocation
- Update documentation
- Test disaster recovery procedures

### Updates

```bash
# Pull latest code
git pull

# Rebuild images
docker-compose -f docker-compose.prod.yml build

# Rolling update (zero downtime)
docker-compose -f docker-compose.prod.yml up -d --no-deps --build backend
docker-compose -f docker-compose.prod.yml up -d --no-deps --build frontend
```

### Cleanup

```bash
# Remove unused images
docker image prune -a

# Remove unused volumes (careful!)
docker volume prune

# Complete system cleanup
docker system prune -a --volumes
```

---

## Support and Resources

- **Documentation**: See `README.md` and other markdown files
- **Environment Variables**: See `ENVIRONMENT_VARIABLES.md`
- **Issues**: Report bugs on GitHub
- **Health Monitoring**: Use `/healthz`, `/readyz`, and `/status` endpoints

---

## Production Checklist

Before going live, ensure:

- [ ] API keys are configured and valid
- [ ] `.env` file has production settings
- [ ] `ENVIRONMENT=production`
- [ ] Appropriate `LOG_LEVEL` is set
- [ ] Data directories exist and have correct permissions
- [ ] SSL/TLS certificates are configured (if using HTTPS)
- [ ] Firewall rules are properly configured
- [ ] Backups are scheduled and tested
- [ ] Monitoring is set up
- [ ] Health checks are working
- [ ] Resource limits are appropriate
- [ ] Security best practices are followed
- [ ] Documentation is up to date

---

**Congratulations!** Your AgentKit deployment is ready for production. 🚀
