# Docker Quick Start Guide

Get AgentKit up and running with Docker in minutes!

## Prerequisites

- Docker 20.10.0+ installed ([Get Docker](https://docs.docker.com/get-docker/))
- Docker Compose 2.0.0+ installed ([Get Docker Compose](https://docs.docker.com/compose/install/))
- API keys for Google Gemini and Tavily

## Quick Start (Development)

### 1. Clone and Configure

```bash
# Clone the repository
git clone https://github.com/aramb-dev/agentkit.git
cd agentkit

# Copy environment template
cp .env.example .env

# Edit .env with your API keys
nano .env  # or use your preferred editor
```

**Required in `.env`:**
```bash
GOOGLE_API_KEY=your_actual_gemini_api_key_here
TAVILY_API_KEY=your_actual_tavily_api_key_here
```

### 2. Launch the Application

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f
```

### 3. Access the Application

- **Frontend**: http://localhost:8080
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/healthz

### 4. Stop the Application

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (clean slate)
docker-compose down -v
```

---

## Production Deployment

### 1. Configure for Production

```bash
# Copy and edit environment file
cp .env.example .env

# Update .env with production settings
nano .env
```

**Production `.env` example:**
```bash
# API Keys
GOOGLE_API_KEY=your_production_gemini_key
TAVILY_API_KEY=your_production_tavily_key

# Environment
ENVIRONMENT=production
LOG_LEVEL=INFO

# Ports
BACKEND_PORT=8000
FRONTEND_PORT=80

# API URL (update with your domain)
VITE_API_URL=https://api.yourdomain.com

# Data paths (create these directories first!)
DATA_PATH=/var/lib/agentkit/data
UPLOADS_PATH=/var/lib/agentkit/uploads
CHROMA_PATH=/var/lib/agentkit/chroma_db
```

### 2. Create Data Directories

```bash
# Create directories
sudo mkdir -p /var/lib/agentkit/{data,uploads,chroma_db}

# Set permissions
sudo chown -R $USER:$USER /var/lib/agentkit
chmod 755 /var/lib/agentkit/*
```

### 3. Deploy with Production Config

```bash
# Build images
docker-compose -f docker-compose.prod.yml build

# Start services
docker-compose -f docker-compose.prod.yml up -d

# Check status
docker-compose -f docker-compose.prod.yml ps
```

### 4. Verify Deployment

```bash
# Check backend health
curl http://localhost:8000/healthz

# Check readiness
curl http://localhost:8000/readyz

# View logs
docker-compose -f docker-compose.prod.yml logs -f
```

---

## Common Commands

### Service Management

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# Restart a specific service
docker-compose restart backend

# View service status
docker-compose ps

# Scale backend (multiple instances)
docker-compose up -d --scale backend=3
```

### Logs and Debugging

```bash
# View all logs
docker-compose logs -f

# View backend logs only
docker-compose logs -f backend

# View last 100 lines
docker-compose logs --tail=100

# Follow logs for a specific service
docker-compose logs -f frontend
```

### Updates and Rebuilds

```bash
# Pull latest code
git pull

# Rebuild and restart
docker-compose up -d --build

# Rebuild specific service
docker-compose up -d --build backend

# Force recreate containers
docker-compose up -d --force-recreate
```

### Maintenance

```bash
# Execute command in running container
docker-compose exec backend bash

# Check container resource usage
docker stats

# Clean up unused resources
docker system prune -a

# View container details
docker-compose exec backend env
```

---

## Health Checks

AgentKit provides multiple health check endpoints:

### Liveness Check

```bash
curl http://localhost:8000/healthz
```

**Response:**
```json
{
  "status": "ok",
  "version": "1.0.0",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Readiness Check

```bash
curl http://localhost:8000/readyz
```

**Response:**
```json
{
  "ready": true,
  "checks": {
    "api": true,
    "google_api_key": true,
    "database": true,
    "vector_store": true
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### System Status

```bash
curl http://localhost:8000/status
```

Returns comprehensive system information including configuration, capabilities, and endpoints.

---

## Architecture

```
┌─────────────────────────────────────────────┐
│                  Frontend                    │
│           (React + Vite + Nginx)            │
│              Port: 8080 / 80                │
└────────────────┬────────────────────────────┘
                 │
                 │ HTTP/HTTPS
                 │
┌────────────────▼────────────────────────────┐
│                 Backend API                  │
│            (FastAPI + Python)               │
│                Port: 8000                    │
└────────┬──────────────┬──────────────┬──────┘
         │              │              │
         │              │              │
    ┌────▼─────┐   ┌───▼────┐   ┌────▼──────┐
    │ SQLite   │   │ChromaDB│   │  Uploads  │
    │(Database)│   │(Vector)│   │   (Files) │
    └──────────┘   └────────┘   └───────────┘
```

---

## Troubleshooting

### Services Won't Start

**Problem:** Containers fail to start

**Solutions:**
```bash
# Check logs for errors
docker-compose logs

# Verify .env file exists and has API keys
cat .env | grep API_KEY

# Check port conflicts
sudo lsof -i :8000
sudo lsof -i :8080

# Restart Docker daemon
sudo systemctl restart docker
```

### API Key Errors

**Problem:** "API key not configured" errors

**Solutions:**
```bash
# Verify environment variables in container
docker-compose exec backend env | grep API_KEY

# Ensure .env file is in project root
ls -la .env

# Restart services after updating .env
docker-compose down && docker-compose up -d
```

### File Upload Failures

**Problem:** Cannot upload files

**Solutions:**
```bash
# Check upload directory permissions
docker-compose exec backend ls -la /app/uploads

# Verify MAX_FILE_SIZE setting
curl http://localhost:8000/status | jq '.configuration.max_file_size_mb'

# Check available disk space
df -h
```

### Out of Memory

**Problem:** Containers killed due to OOM

**Solutions:**
```bash
# Check container memory usage
docker stats

# Increase Docker memory limits
# Edit docker-compose.yml or docker-compose.prod.yml:
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 4G

# Restart with new limits
docker-compose up -d
```

### Connection Refused

**Problem:** Frontend can't connect to backend

**Solutions:**
```bash
# Verify backend is running
curl http://localhost:8000/healthz

# Check VITE_API_URL in .env
grep VITE_API_URL .env

# For production, ensure it matches your domain
VITE_API_URL=https://api.yourdomain.com

# Rebuild frontend with new URL
docker-compose build frontend
docker-compose up -d frontend
```

---

## Performance Optimization

### Resource Limits

Set appropriate limits in `docker-compose.prod.yml`:

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
```

### Caching

Docker builds use layer caching. To speed up builds:

```bash
# Use BuildKit for better caching
DOCKER_BUILDKIT=1 docker-compose build

# Pull cache from registry (if using)
docker-compose build --pull
```

### Scaling

Run multiple backend instances:

```bash
# Scale to 3 backend workers
docker-compose up -d --scale backend=3

# With load balancer, all handle requests
```

---

## Security Best Practices

1. **Never expose backend directly to internet**
   - Use reverse proxy (Nginx, Traefik)
   - See `DEPLOYMENT.md` for Nginx configuration

2. **Use secrets for API keys**
   - Never commit `.env` to git
   - Use Docker secrets or vault in production

3. **Run as non-root user** (already configured)
   - Containers run as `appuser` (UID 1000)

4. **Keep images updated**
   ```bash
   # Pull latest base images
   docker-compose build --pull

   # Update regularly
   docker-compose pull && docker-compose up -d
   ```

5. **Scan for vulnerabilities**
   ```bash
   # Install Trivy
   # Scan images
   docker scan agentkit-backend:latest
   ```

---

## Next Steps

- **Production Setup**: See [DEPLOYMENT.md](./DEPLOYMENT.md)
- **Environment Variables**: See [ENVIRONMENT_VARIABLES.md](./ENVIRONMENT_VARIABLES.md)
- **CI/CD Setup**: See `.github/workflows/` for GitHub Actions
- **RAG Configuration**: See [RAG_INTEGRATION.md](./RAG_INTEGRATION.md)

---

## Support

- **Issues**: [GitHub Issues](https://github.com/aramb-dev/agentkit/issues)
- **Documentation**: See all `*.md` files in repository
- **Health Monitoring**: Use `/healthz`, `/readyz`, `/status` endpoints

---

**Happy Deploying! 🚀**
