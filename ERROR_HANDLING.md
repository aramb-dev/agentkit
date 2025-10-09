# Error Handling & Validation Guide

## Overview

AgentKit implements comprehensive error handling and validation to ensure reliability, security, and a great user experience. This document describes the error handling mechanisms, validation rules, and best practices.

## File Upload Validation

### File Size Limits

- **Maximum file size:** 50MB (52,428,800 bytes)
- **Configurable via:** `MAX_FILE_SIZE` environment variable
- **Error code:** `FILE_TOO_LARGE`
- **HTTP status:** 413 Payload Too Large

### Supported File Types

AgentKit supports the following file formats for document ingestion and chat attachments:

- **PDF** (`.pdf`) - Portable Document Format
- **Word Documents** (`.docx`) - Microsoft Word
- **Text Files** (`.txt`) - Plain text
- **Markdown** (`.md`, `.markdown`) - Markdown documents
- **JSON** (`.json`) - JSON data files

### File Validation Rules

1. **Filename Required:** All uploaded files must have a valid filename
2. **Non-empty Files:** Files with 0 bytes are rejected
3. **Extension Validation:** File extension must match supported types
4. **MIME Type Check:** Content-Type header is validated (with warnings for mismatches)
5. **Path Traversal Protection:** Filenames containing `..`, `/`, or `\` are rejected

## Error Response Format

All API errors follow a standardized JSON response format:

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {
      "key": "Additional context"
    },
    "timestamp": "2024-01-01T12:00:00.000000",
    "retry_after": 60
  },
  "request_id": "uuid-v4-request-id"
}
```

### Error Codes

| Code | Description | HTTP Status | Retryable |
|------|-------------|-------------|-----------|
| `FILE_TOO_LARGE` | File exceeds size limit | 413 | No |
| `UNSUPPORTED_FORMAT` | File type not supported | 400 | No |
| `VALIDATION_ERROR` | Request validation failed | 400 | No |
| `PROCESSING_ERROR` | Document processing failed | 500 | Yes |
| `NETWORK_ERROR` | Network/connection issue | 503 | Yes |
| `RATE_LIMIT_EXCEEDED` | Too many requests | 429 | Yes |
| `INTERNAL_ERROR` | Unexpected server error | 500 | Yes |
| `NOT_FOUND` | Resource not found | 404 | No |
| `CONFLICT` | Resource conflict (e.g., duplicate namespace) | 409 | No |

## Retry Logic

### Backend Configuration

Retry behavior can be configured via environment variables:

```bash
ENABLE_RETRY_LOGIC=true          # Enable/disable retry logic
MAX_RETRY_ATTEMPTS=3             # Maximum retry attempts
RETRY_DELAY_SECONDS=1            # Initial delay (exponential backoff)
```

### Frontend Retry Logic

The frontend automatically retries failed requests for certain error types:

- **Network errors** (connection failures, timeouts)
- **5xx server errors** (500, 502, 503, 504)
- **429 rate limit errors**

Retry strategy uses **exponential backoff**:
- Attempt 1: Wait 1 second
- Attempt 2: Wait 2 seconds
- Attempt 3: Wait 4 seconds

### Determining Retryability

An error is considered retryable if:
1. It's a network/connection error (`ECONNABORTED`, `NETWORK_ERROR`)
2. HTTP status is 5xx (server error)
3. HTTP status is 429 (rate limit exceeded)

Client errors (4xx) are generally **not retryable** as they indicate invalid requests.

## Error Handling Best Practices

### For API Users

1. **Always check the error response structure** before parsing error details
2. **Implement retry logic** for retryable errors with exponential backoff
3. **Log request IDs** (`X-Request-ID` header) for debugging
4. **Respect `retry_after`** field for rate limit errors
5. **Validate files client-side** before uploading to reduce failed requests

### For Developers

1. **Use standardized error responses** via `HTTPException` or error handlers
2. **Log errors with context** including request path, user ID, file details
3. **Include error codes** for programmatic error handling
4. **Provide clear error messages** that guide users to resolution
5. **Test error scenarios** in integration tests

## Client-Side Validation

The frontend implements client-side validation before upload:

### FileUpload Component

```tsx
// Automatic validation via react-dropzone
const { getRootProps, getInputProps, fileRejections } = useDropzone({
  maxSize: 50 * 1024 * 1024,  // 50MB
  maxFiles: 5,
  accept: {
    'application/pdf': ['.pdf'],
    'text/plain': ['.txt'],
    // ... other supported types
  }
});
```

### Validation Errors Displayed

- File too large (> 50MB)
- Unsupported file type
- Too many files (> 5)
- Duplicate files

## Error Logging

All errors are logged with structured information:

```python
logger.error(f"HTTP {status_code}: {detail} - Path: {path}")
logger.warning(f"File validation failed: {filename} - {reason}")
```

### Log Levels

- **ERROR:** Request failures, validation errors, processing errors
- **WARNING:** Unexpected MIME types, suspicious filenames
- **INFO:** Successful requests, file uploads, processing completion

## Security Considerations

### Path Traversal Protection

Files with path traversal patterns are automatically rejected:
- `../../../etc/passwd` ❌
- `..\\..\\windows\\system32` ❌
- `subdir/../../../sensitive` ❌

### File Size Limits

Enforced to prevent:
- Denial of Service (DoS) attacks
- Memory exhaustion
- Storage abuse

### Extension Validation

Only whitelisted extensions accepted to prevent:
- Executable file uploads
- Script injection
- Malware distribution

## Monitoring & Debugging

### Request Tracing

Every request gets a unique ID accessible via:
- Response header: `X-Request-ID`
- Error response: `request_id` field
- Server logs: Correlated with request ID

### Error Metrics

Monitor these metrics for system health:
- Error rate by endpoint
- Error rate by error code
- Retry success rate
- Average file size (for capacity planning)

## Examples

### Handling File Too Large Error

```typescript
try {
  await uploadFile(file);
} catch (error) {
  if (axios.isAxiosError(error) && error.response?.status === 413) {
    const errorData = error.response.data.error;
    console.error(`File too large: ${errorData.message}`);
    // Show user-friendly message
    alert(`File exceeds 50MB limit. Please choose a smaller file.`);
  }
}
```

### Retry with Exponential Backoff

```typescript
async function retryWithBackoff(fn, maxAttempts = 3) {
  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      return await fn();
    } catch (error) {
      if (!isRetryableError(error) || attempt === maxAttempts) {
        throw error;
      }
      const delay = 1000 * Math.pow(2, attempt - 1);
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }
}
```

### Validation Before Upload

```typescript
function validateFile(file: File): { valid: boolean; error?: string } {
  // Check size
  if (file.size > 50 * 1024 * 1024) {
    return { valid: false, error: 'File size exceeds 50MB limit' };
  }
  
  // Check extension
  const validExtensions = ['.pdf', '.txt', '.docx', '.md', '.json'];
  const ext = file.name.split('.').pop()?.toLowerCase();
  if (!ext || !validExtensions.includes(`.${ext}`)) {
    return { valid: false, error: 'Unsupported file type' };
  }
  
  return { valid: true };
}
```

## Configuration Reference

### Environment Variables

```bash
# File Upload
MAX_FILE_SIZE=52428800  # 50MB in bytes

# Error Handling
ENABLE_RETRY_LOGIC=true
MAX_RETRY_ATTEMPTS=3
RETRY_DELAY_SECONDS=1

# Debugging
DEBUG=false  # Set true to include error details in responses
```

### Frontend Configuration

Update in `ChatContainer.tsx`:

```typescript
const MAX_FILE_SIZE = 50 * 1024 * 1024;  // 50MB
const MAX_FILES = 5;
const MAX_RETRY_ATTEMPTS = 3;
```

## Testing Error Handling

Run the error handling test suite:

```bash
python -m pytest test_error_handling.py -v
```

Tests cover:
- File size validation
- File type validation
- Path traversal protection
- Error response format
- Request validation
- Error logging
- Retry logic

## Support & Troubleshooting

### Common Issues

**Issue:** "File too large" error
- **Solution:** Compress or split file, or increase `MAX_FILE_SIZE` limit

**Issue:** "Unsupported format" error
- **Solution:** Convert file to supported format (PDF, DOCX, TXT, MD, JSON)

**Issue:** Uploads timing out
- **Solution:** Check network connection, increase timeout, reduce file size

**Issue:** Retry exhausted
- **Solution:** Check server logs with request ID, verify server health

### Getting Help

1. Check server logs for detailed error messages
2. Include request ID when reporting issues
3. Verify file meets validation requirements
4. Test with smaller files to isolate issues
