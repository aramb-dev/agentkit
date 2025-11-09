# Environment Variables Documentation

This document describes all environment variables used in the AgentKit application. These variables control application behavior, API integrations, and deployment configurations.

## Table of Contents

- [Required Variables](#required-variables)
- [Application Settings](#application-settings)
- [File Upload Configuration](#file-upload-configuration)
- [Conversation Settings](#conversation-settings)
- [Error Handling](#error-handling)
- [Docker Deployment](#docker-deployment)
- [RAG Configuration](#rag-configuration)
- [Security Considerations](#security-considerations)

---

## Required Variables

These variables **must** be set for the application to function properly.

### `GOOGLE_API_KEY`

- **Description**: API key for Google Gemini AI models
- **Required**: Yes
- **Default**: None
- **Example**: `GOOGLE_API_KEY=AIzaSyABC123...`
- **How to obtain**: Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
- **Used by**: AI model inference, conversation generation
- **Notes**: Without this key, the AI chat functionality will not work

### `TAVILY_API_KEY`

- **Description**: API key for Tavily web search service
- **Required**: Yes (for web search features)
- **Default**: None
- **Example**: `TAVILY_API_KEY=tvly-ABC123...`
- **How to obtain**: Sign up at [Tavily](https://tavily.com)
- **Used by**: Real-time web search, hybrid RAG search
- **Notes**: Web search features will be disabled if not configured

---

## Application Settings

### `ENVIRONMENT`

- **Description**: Application environment mode
- **Required**: No
- **Default**: `development`
- **Allowed values**: `development`, `staging`, `production`
- **Example**: `ENVIRONMENT=production`
- **Impact**:
  - Affects logging verbosity
  - Controls debug mode features
  - Influences error message detail

### `LOG_LEVEL`

- **Description**: Logging verbosity level
- **Required**: No
- **Default**: `INFO`
- **Allowed values**: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`
- **Example**: `LOG_LEVEL=WARNING`
- **Impact**:
  - `DEBUG`: Very detailed logs (use in development)
  - `INFO`: Standard operational logs (recommended for production)
  - `WARNING`: Only warnings and errors
  - `ERROR`: Only error messages
  - `CRITICAL`: Only critical failures

---

## File Upload Configuration

### `MAX_FILE_SIZE`

- **Description**: Maximum allowed file upload size in bytes
- **Required**: No
- **Default**: `52428800` (50 MB)
- **Example**: `MAX_FILE_SIZE=104857600` (100 MB)
- **Impact**: Limits the size of documents that can be uploaded for RAG processing
- **Notes**:
  - Larger files require more memory for processing
  - Consider server resources when increasing this value
  - Nginx/reverse proxy may have separate upload limits

---

## Conversation Settings

### `CONVERSATION_HISTORY_LIMIT`

- **Description**: Maximum number of messages to retain in conversation memory
- **Required**: No
- **Default**: `50`
- **Example**: `CONVERSATION_HISTORY_LIMIT=100`
- **Impact**:
  - Higher values provide more context to the AI but use more memory
  - Lower values reduce memory usage but may lose conversation context
- **Notes**: Conversations are persisted to database regardless of this limit

---

## Error Handling

### `ENABLE_RETRY_LOGIC`

- **Description**: Enable automatic retry for transient API failures
- **Required**: No
- **Default**: `true`
- **Allowed values**: `true`, `false`
- **Example**: `ENABLE_RETRY_LOGIC=true`
- **Impact**: Automatically retries failed API calls (e.g., network timeouts)

### `MAX_RETRY_ATTEMPTS`

- **Description**: Maximum number of retry attempts for failed requests
- **Required**: No
- **Default**: `3`
- **Example**: `MAX_RETRY_ATTEMPTS=5`
- **Impact**: More retries increase resilience but may delay error reporting
- **Notes**: Only applies when `ENABLE_RETRY_LOGIC=true`

### `RETRY_DELAY_SECONDS`

- **Description**: Initial delay between retry attempts (uses exponential backoff)
- **Required**: No
- **Default**: `1` (second)
- **Example**: `RETRY_DELAY_SECONDS=2`
- **Impact**: Actual delays: 1s, 2s, 4s, 8s... (exponential)
- **Notes**: Only applies when `ENABLE_RETRY_LOGIC=true`

---

## Docker Deployment

These variables are used specifically for Docker Compose deployments.

### `BACKEND_PORT`

- **Description**: Host port to expose the backend API
- **Required**: No
- **Default**: `8000`
- **Example**: `BACKEND_PORT=8080`
- **Used by**: `docker-compose.prod.yml`

### `FRONTEND_PORT`

- **Description**: Host port to expose the frontend application
- **Required**: No
- **Default**: `80`
- **Example**: `FRONTEND_PORT=3000`
- **Used by**: `docker-compose.prod.yml`

### `VITE_API_URL`

- **Description**: Backend API URL for the frontend to connect to
- **Required**: No (for production)
- **Default**: `http://localhost:8000`
- **Example**: `VITE_API_URL=https://api.yourdomain.com`
- **Used by**: Frontend build process and runtime
- **Notes**: Must match your production backend URL

### `DATA_PATH`

- **Description**: Host directory path for data persistence
- **Required**: No
- **Default**: `./data`
- **Example**: `DATA_PATH=/var/lib/agentkit/data`
- **Used by**: Production Docker volumes

### `UPLOADS_PATH`

- **Description**: Host directory path for uploaded files
- **Required**: No
- **Default**: `./uploads`
- **Example**: `UPLOADS_PATH=/var/lib/agentkit/uploads`
- **Used by**: Production Docker volumes

### `CHROMA_PATH`

- **Description**: Host directory path for ChromaDB vector store
- **Required**: No
- **Default**: `./chroma_db`
- **Example**: `CHROMA_PATH=/var/lib/agentkit/chroma_db`
- **Used by**: Production Docker volumes

---

## RAG Configuration

These optional variables override default RAG (Retrieval-Augmented Generation) settings.

### `EMBEDDING_MODEL`

- **Description**: Sentence transformer model for document embeddings
- **Required**: No
- **Default**: `all-MiniLM-L6-v2`
- **Example**: `EMBEDDING_MODEL=all-mpnet-base-v2`
- **Options**:
  - `all-MiniLM-L6-v2`: Fast, balanced (recommended)
  - `all-mpnet-base-v2`: Better quality, slower
  - `paraphrase-MiniLM-L6-v2`: Good for semantic similarity
- **Impact**: Affects embedding quality and speed

### `RAG_DEFAULT_K`

- **Description**: Default number of documents to retrieve for RAG queries
- **Required**: No
- **Default**: `5`
- **Example**: `RAG_DEFAULT_K=10`
- **Impact**: More results provide more context but may include less relevant documents

### `RAG_CACHE_ENABLED`

- **Description**: Enable query result caching for performance
- **Required**: No
- **Default**: `true`
- **Allowed values**: `true`, `false`
- **Example**: `RAG_CACHE_ENABLED=false`
- **Impact**: Caching improves performance for repeated queries

---

## Security Considerations

### Best Practices

1. **Never commit `.env` files to version control**
   - Add `.env` to `.gitignore`
   - Use `.env.example` as a template

2. **Use strong, unique API keys**
   - Rotate keys periodically
   - Use different keys for development and production

3. **Restrict file upload sizes**
   - Set `MAX_FILE_SIZE` based on your server capacity
   - Consider implementing rate limiting

4. **Use environment-specific configurations**
   - Development: Verbose logging, smaller limits
   - Production: Limited logging, appropriate resource limits

5. **Secure API key storage**
   - Use secret management services (AWS Secrets Manager, HashiCorp Vault)
   - For Docker: Use Docker secrets or environment variable encryption

### Production Checklist

- [ ] All required API keys are set
- [ ] `ENVIRONMENT=production`
- [ ] `LOG_LEVEL=INFO` or higher
- [ ] File size limits are appropriate for your infrastructure
- [ ] API URLs point to production endpoints
- [ ] Data paths have proper permissions
- [ ] API keys are stored securely (not in plain text files)

---

## Setting Environment Variables

### Local Development

```bash
# Copy the example file
cp .env.example .env

# Edit with your values
nano .env
```

### Docker Compose

```bash
# Docker Compose automatically reads .env file
docker-compose up
```

### Production Server

```bash
# Set in system environment
export GOOGLE_API_KEY="your-key-here"
export TAVILY_API_KEY="your-key-here"

# Or use a .env file with docker-compose
docker-compose -f docker-compose.prod.yml up -d
```

### Kubernetes

```yaml
# Use ConfigMaps and Secrets
apiVersion: v1
kind: Secret
metadata:
  name: agentkit-secrets
type: Opaque
stringData:
  GOOGLE_API_KEY: "your-key-here"
  TAVILY_API_KEY: "your-key-here"
```

---

## Troubleshooting

### Application won't start

- Check that required API keys are set
- Verify `.env` file is in the correct location
- Check logs for specific error messages

### File uploads failing

- Increase `MAX_FILE_SIZE` if needed
- Check reverse proxy upload limits (nginx, etc.)
- Verify upload directory permissions

### API errors

- Verify API keys are valid and not expired
- Check `ENABLE_RETRY_LOGIC` is enabled
- Review logs for specific error codes

---

## Additional Resources

- [Production Deployment Guide](./DEPLOYMENT.md)
- [Docker Setup Guide](./README.md#docker-deployment)
- [RAG Configuration](./RAG_INTEGRATION.md)
- [Error Handling Documentation](./ERROR_HANDLING.md)
