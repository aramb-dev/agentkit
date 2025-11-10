"""
Security middleware and utilities for AgentKit.

This module provides comprehensive security features including:
- Rate limiting
- Security headers
- Input validation
- Request sanitization
"""

import os
import re
import secrets
from typing import Optional, List
from functools import wraps
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from pydantic import BaseModel, Field, validator
import logging

logger = logging.getLogger(__name__)

# Initialize rate limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100/minute", "1000/hour"],
    storage_uri="memory://",
    strategy="fixed-window"
)


# Pydantic models for input validation
class ChatRequest(BaseModel):
    """Validated chat request model."""
    message: str = Field(..., min_length=1, max_length=10000, description="User message")
    model: str = Field(..., min_length=1, max_length=100, description="AI model name")
    history: str = Field(default="[]", max_length=500000, description="Conversation history as JSON")
    namespace: str = Field(default="default", min_length=1, max_length=64, description="Document namespace")
    session_id: str = Field(default="default", min_length=1, max_length=128, description="Session identifier")
    search_mode: str = Field(default="auto", description="Search mode selection")

    @validator('namespace')
    def validate_namespace(cls, v):
        """Ensure namespace contains only safe characters."""
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Namespace can only contain letters, numbers, underscores, and hyphens')
        return v

    @validator('search_mode')
    def validate_search_mode(cls, v):
        """Ensure search mode is valid."""
        valid_modes = ['auto', 'web', 'documents', 'hybrid']
        if v not in valid_modes:
            raise ValueError(f'Search mode must be one of: {", ".join(valid_modes)}')
        return v


class NamespaceRequest(BaseModel):
    """Validated namespace creation request."""
    name: str = Field(..., min_length=1, max_length=64, description="Namespace name")

    @validator('name')
    def validate_name(cls, v):
        """Ensure namespace name is safe."""
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Namespace name can only contain letters, numbers, underscores, and hyphens')
        if v.startswith('-') or v.startswith('_'):
            raise ValueError('Namespace name cannot start with hyphen or underscore')
        return v


class ConversationUpdateRequest(BaseModel):
    """Validated conversation update request."""
    title: Optional[str] = Field(None, max_length=200, description="Conversation title")
    namespace: Optional[str] = Field(None, max_length=64, description="Namespace")

    @validator('namespace')
    def validate_namespace(cls, v):
        """Ensure namespace contains only safe characters."""
        if v and not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Namespace can only contain letters, numbers, underscores, and hyphens')
        return v


# Security headers middleware
async def add_security_headers(request: Request, call_next):
    """
    Add security headers to all responses.

    Headers added:
    - X-Frame-Options: Prevent clickjacking
    - X-Content-Type-Options: Prevent MIME sniffing
    - X-XSS-Protection: Enable XSS filter
    - Strict-Transport-Security: Enforce HTTPS
    - Content-Security-Policy: Restrict resource loading
    - Referrer-Policy: Control referrer information
    """
    response = await call_next(request)

    # Prevent clickjacking
    response.headers["X-Frame-Options"] = "DENY"

    # Prevent MIME type sniffing
    response.headers["X-Content-Type-Options"] = "nosniff"

    # Enable XSS protection (legacy browsers)
    response.headers["X-XSS-Protection"] = "1; mode=block"

    # Enforce HTTPS in production
    if os.getenv("ENVIRONMENT") == "production":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"

    # Content Security Policy
    csp_directives = [
        "default-src 'self'",
        "script-src 'self' 'unsafe-inline'",  # unsafe-inline needed for some frameworks
        "style-src 'self' 'unsafe-inline'",
        "img-src 'self' data: https:",
        "font-src 'self' data:",
        "connect-src 'self'",
        "frame-ancestors 'none'",
    ]
    response.headers["Content-Security-Policy"] = "; ".join(csp_directives)

    # Control referrer information
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

    # Prevent caching of sensitive data
    if request.url.path.startswith("/conversations") or request.url.path.startswith("/files"):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
        response.headers["Pragma"] = "no-cache"

    return response


# Rate limit error handler
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """
    Custom handler for rate limit exceeded errors.
    Returns a standardized error response.
    """
    logger.warning(f"Rate limit exceeded for {get_remote_address(request)} on {request.url.path}")

    return JSONResponse(
        status_code=429,
        content={
            "error": {
                "code": "RATE_LIMIT_EXCEEDED",
                "message": "Too many requests. Please slow down and try again later.",
                "retry_after": 60
            }
        },
        headers={
            "Retry-After": "60"
        }
    )


def sanitize_error_message(error: Exception, request: Request) -> str:
    """
    Sanitize error messages to prevent information disclosure.

    Args:
        error: The exception that occurred
        request: The FastAPI request object

    Returns:
        A safe, generic error message for the client
    """
    # Log detailed error for debugging (server-side only)
    logger.error(
        f"Error processing request: {request.url.path}",
        exc_info=True,
        extra={
            "method": request.method,
            "path": request.url.path,
            "client": get_remote_address(request)
        }
    )

    # Never expose internal details in production
    if os.getenv("ENVIRONMENT") == "production":
        return "An error occurred while processing your request. Please try again later."

    # In development, provide slightly more detail (but still sanitized)
    error_type = type(error).__name__
    safe_messages = {
        "ValidationError": "Invalid input data provided",
        "JSONDecodeError": "Invalid JSON format",
        "FileNotFoundError": "Requested resource not found",
        "PermissionError": "Insufficient permissions",
        "TimeoutError": "Request timed out",
        "ConnectionError": "Service temporarily unavailable"
    }

    return safe_messages.get(error_type, "An unexpected error occurred")


def validate_file_upload(filename: str, content: bytes, max_size: int = 52428800) -> tuple[str, str]:
    """
    Validate file uploads for security.

    Args:
        filename: Original filename
        content: File content bytes
        max_size: Maximum allowed file size

    Returns:
        Tuple of (sanitized_filename, error_message)

    Raises:
        HTTPException: If validation fails
    """
    # Check file size
    if len(content) > max_size:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {max_size / (1024 * 1024):.1f}MB"
        )

    # Validate filename
    if not filename:
        raise HTTPException(status_code=400, detail="Filename is required")

    # Extract just the filename (no path)
    from pathlib import Path
    try:
        safe_filename = Path(filename).name
    except (ValueError, RuntimeError):
        raise HTTPException(status_code=400, detail="Invalid filename")

    # Check for path traversal attempts
    if '..' in filename or '/' in filename or '\\' in filename:
        raise HTTPException(status_code=400, detail="Invalid filename: path components not allowed")

    # Check for dangerous extensions
    dangerous_extensions = [
        '.exe', '.bat', '.cmd', '.sh', '.ps1', '.scr', '.vbs', '.jar',
        '.msi', '.app', '.deb', '.rpm', '.dmg', '.iso', '.dll', '.so'
    ]
    if any(safe_filename.lower().endswith(ext) for ext in dangerous_extensions):
        raise HTTPException(status_code=400, detail="File type not allowed for security reasons")

    # Validate against allowed extensions
    allowed_extensions = ['.pdf', '.txt', '.docx', '.md', '.json', '.csv', '.xml']
    if not any(safe_filename.lower().endswith(ext) for ext in allowed_extensions):
        raise HTTPException(
            status_code=400,
            detail=f"File type not supported. Allowed types: {', '.join(allowed_extensions)}"
        )

    return safe_filename, ""


def generate_secure_token(length: int = 32) -> str:
    """
    Generate a cryptographically secure random token.

    Args:
        length: Token length in bytes

    Returns:
        URL-safe base64 encoded token
    """
    return secrets.token_urlsafe(length)


def validate_uuid_format(uuid_str: str) -> bool:
    """
    Validate that a string is a properly formatted UUID.

    Args:
        uuid_str: String to validate

    Returns:
        True if valid UUID format, False otherwise
    """
    uuid_pattern = re.compile(
        r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
        re.IGNORECASE
    )
    return bool(uuid_pattern.match(uuid_str))


def get_allowed_origins() -> List[str]:
    """
    Get allowed CORS origins from environment.

    Returns:
        List of allowed origin URLs
    """
    origins_env = os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173,http://localhost:8080,http://127.0.0.1:8080"
    )
    origins = [origin.strip() for origin in origins_env.split(",")]

    # Log origins in development for debugging
    if os.getenv("ENVIRONMENT") != "production":
        logger.info(f"Allowed CORS origins: {origins}")

    return origins


def is_safe_redirect_url(url: str, allowed_domains: List[str]) -> bool:
    """
    Check if a redirect URL is safe (prevents open redirect vulnerabilities).

    Args:
        url: URL to validate
        allowed_domains: List of allowed domain names

    Returns:
        True if URL is safe, False otherwise
    """
    from urllib.parse import urlparse

    if not url:
        return False

    # Relative URLs are safe
    if url.startswith('/'):
        return True

    try:
        parsed = urlparse(url)
        # Check if domain is in allowed list
        return parsed.netloc in allowed_domains
    except Exception:
        return False


# Logging utilities
def setup_security_logging():
    """
    Configure security-focused logging.
    Sets up structured logging with appropriate filters.
    """
    # Create security logger
    security_logger = logging.getLogger("security")
    security_logger.setLevel(logging.INFO)

    # Create handler
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - SECURITY - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    security_logger.addHandler(handler)

    return security_logger


def audit_log(action: str, details: dict, level: str = "INFO"):
    """
    Create an audit log entry for security-relevant actions.

    Args:
        action: The action being performed
        details: Dictionary of relevant details
        level: Log level (INFO, WARNING, ERROR)
    """
    security_logger = logging.getLogger("security")

    log_entry = {
        "action": action,
        **details
    }

    log_method = getattr(security_logger, level.lower(), security_logger.info)
    log_method(f"AUDIT: {action}", extra=log_entry)


# Rate limit decorators for specific endpoints
def rate_limit_chat(func):
    """Rate limit decorator for chat endpoints (10 requests/minute)."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        return await func(*args, **kwargs)
    return limiter.limit("10/minute")(wrapper)


def rate_limit_upload(func):
    """Rate limit decorator for upload endpoints (5 requests/minute)."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        return await func(*args, **kwargs)
    return limiter.limit("5/minute")(wrapper)


def rate_limit_delete(func):
    """Rate limit decorator for delete endpoints (20 requests/minute)."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        return await func(*args, **kwargs)
    return limiter.limit("20/minute")(wrapper)
