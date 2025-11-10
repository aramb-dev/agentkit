# Multi-stage Dockerfile for AgentKit Backend
# Optimized for production deployment with minimal image size

# Stage 1: Base Python image with dependencies
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Stage 2: Dependencies installation
FROM base as dependencies

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Stage 3: Production image
FROM base as production

# Copy installed dependencies from dependencies stage
COPY --from=dependencies /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=dependencies /usr/local/bin /usr/local/bin

# Create non-root user for security
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

# Copy application code
COPY --chown=appuser:appuser ./app ./app
COPY --chown=appuser:appuser ./agent ./agent
COPY --chown=appuser:appuser ./rag ./rag
COPY --chown=appuser:appuser ./.env.example ./.env.example

# Create directories for data persistence
RUN mkdir -p /app/data /app/uploads /app/chroma_db && \
    chown -R appuser:appuser /app/data /app/uploads /app/chroma_db

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Default number of workers (can be overridden via environment variable)
ENV UVICORN_WORKERS=4

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/healthz')" || exit 1

# Run the application with uvicorn
# Use shell form to allow environment variable substitution
CMD /bin/sh -c "exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers ${UVICORN_WORKERS}"
