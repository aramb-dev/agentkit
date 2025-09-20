# Namespace Management Documentation

## Overview

The namespace management system in AgentKit allows users to organize documents by project or topic using isolated collections. Each namespace maintains its own set of documents, embeddings, and RAG context, enabling clean separation between different projects or use cases.

## Features

### ✅ Namespace Management UI
- **Namespace Selector**: Dropdown component to switch between namespaces
- **Create New Namespaces**: Modal dialog with name validation
- **Rename Namespaces**: Inline editing with validation
- **Delete Namespaces**: Confirmation dialog for destructive operations
- **Document Count Display**: Visual indicators showing document count per namespace

### ✅ Backend API Endpoints
- `GET /namespaces` - List all namespaces with document counts
- `POST /namespaces` - Create a new namespace
- `PUT /namespaces/{old_name}/rename` - Rename an existing namespace
- `DELETE /namespaces/{namespace_name}` - Delete a namespace and all its documents
- `GET /namespaces/{namespace_name}/documents` - List documents in a specific namespace

### ✅ Integration Points
- **Chat Interface**: Namespace selector in chat header affects RAG retrieval
- **File Manager**: Shows documents grouped by selected namespace
- **Document Upload**: Respects selected namespace for new document ingestion
- **RAG System**: Queries are scoped to the selected namespace

## User Interface Components

### Namespace Selector
Located in both Chat and Files tabs, provides:
- Dropdown to select active namespace
- Document count badge for each namespace
- Visual indicator for default namespace
- Create and manage buttons for namespace operations

### Create Namespace Dialog
- Input field with real-time validation
- Name restrictions: letters, numbers, underscores, hyphens only
- Duplicate name prevention
- Auto-selection of newly created namespace

### Manage Namespaces Dialog
- List view of all namespaces
- Document count per namespace
- Rename functionality (inline editing)
- Delete functionality with confirmation
- Protection for default namespace

## API Reference

### List Namespaces
```http
GET /namespaces
```

**Response:**
```json
{
  "namespaces": [
    {
      "name": "default",
      "document_count": 5,
      "is_default": true
    },
    {
      "name": "my-project",
      "document_count": 3,
      "is_default": false
    }
  ],
  "total": 2
}
```

### Create Namespace
```http
POST /namespaces
Content-Type: application/x-www-form-urlencoded

name=my-new-project
```

**Response:**
```json
{
  "status": "success",
  "message": "Namespace 'my-new-project' created successfully",
  "namespace": "my-new-project"
}
```

### Rename Namespace
```http
PUT /namespaces/old-name/rename
Content-Type: application/x-www-form-urlencoded

new_name=new-project-name
```

### Delete Namespace
```http
DELETE /namespaces/my-project
```

**Response:**
```json
{
  "status": "success",
  "message": "Namespace 'my-project' deleted successfully"
}
```

### List Namespace Documents
```http
GET /namespaces/my-project/documents
```

**Response:**
```json
{
  "namespace": "my-project",
  "documents": [
    {
      "doc_id": "uuid-here",
      "filename": "document.pdf",
      "namespace": "my-project",
      "chunk_count": 15,
      "session_id": "session-uuid"
    }
  ],
  "total_documents": 1,
  "total_chunks": 15
}
```

## Usage Patterns

### Project-Based Organization
```
default/          # General documents
├── meeting-notes.pdf
└── general-research.pdf

project-alpha/    # Specific project documents
├── requirements.pdf
├── design-spec.pdf
└── api-docs.pdf

research-2024/    # Research documents
├── literature-review.pdf
├── data-analysis.pdf
└── findings.pdf
```

### Workflow Integration
1. **Select Namespace**: Choose or create appropriate namespace
2. **Upload Documents**: Documents are automatically assigned to selected namespace
3. **Chat with Context**: RAG queries retrieve only from selected namespace
4. **Switch Context**: Change namespace to work with different document sets
5. **Manage Organization**: Rename, delete, or reorganize namespaces as needed

## Validation and Constraints

### Namespace Name Rules
- Must contain only: letters (a-z, A-Z), numbers (0-9), underscores (_), hyphens (-)
- Cannot be empty or whitespace only
- Must be unique across all namespaces
- Case-sensitive

### Protected Operations
- **Default Namespace**: Cannot be renamed or deleted
- **Confirmation Required**: Destructive operations show confirmation dialogs
- **Data Validation**: All inputs validated on both frontend and backend

## Data Persistence

### Session Persistence
- Selected namespace persists across browser sessions
- Chat state maintains namespace context
- File uploads respect active namespace selection

### ChromaDB Collections
- Each namespace maps to a ChromaDB collection
- Documents are isolated by namespace
- Vector embeddings are scoped to namespace collections

## Error Handling

### Frontend Error States
- Network errors display user-friendly messages
- Validation errors show inline feedback
- Loading states prevent multiple operations
- Graceful fallbacks for API failures

### Backend Error Responses
- `400 Bad Request`: Invalid input or protected operation
- `404 Not Found`: Namespace doesn't exist
- `409 Conflict`: Duplicate namespace name
- `500 Internal Server Error`: System errors with details

## Testing

### API Tests
Comprehensive test suite covering:
- Namespace CRUD operations
- Validation scenarios
- Error conditions
- Edge cases
- Protected operation handling

### Frontend Integration
- Component rendering tests
- User interaction flows
- Error state handling
- Data persistence validation

## Architecture Notes

### LLM Router Integration
The namespace system integrates with AgentKit's LLM-powered tool routing:
- RAG tool receives namespace context
- Document retrieval scoped to active namespace
- Tool selection remains namespace-agnostic

### Backward Compatibility
- Existing documents remain in "default" namespace
- API endpoints maintain existing functionality
- Chat interface enhanced without breaking changes

## Future Enhancements

### Potential Improvements
- Namespace templates for common use cases
- Bulk document operations across namespaces
- Namespace sharing and collaboration features
- Advanced filtering and search within namespaces
- Import/export functionality for namespace data
- Namespace-level access controls and permissions