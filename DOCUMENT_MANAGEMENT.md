# Document Management Documentation

## Overview

The document management system in AgentKit provides comprehensive tools for organizing, searching, and managing RAG documents within namespaces. Users can easily view, filter, select, and delete documents through an intuitive interface.

## Features

### 📋 Document Listing
- **Namespace-based Organization**: Documents are grouped by namespace
- **Metadata Display**: View filename, chunk count, and session ID
- **Document Count**: Real-time counter showing total documents in namespace
- **Visual Icons**: File type indicators for easy identification

### 🔍 Search and Filter
- **Real-time Search**: Filter documents as you type
- **Search by Filename**: Find documents by their file name
- **Search by Session**: Locate documents by session ID
- **Search Counter**: Shows filtered results vs total (e.g., "1/3 documents")

### ✅ Selection and Bulk Operations
- **Individual Selection**: Click checkboxes to select specific documents
- **Select All**: Quickly select all visible documents
- **Multi-Select**: Select multiple documents at once
- **Selection Counter**: Visual feedback showing number of selected items
- **Bulk Delete**: Remove multiple documents in one operation

### 🗑️ Document Deletion
- **Individual Delete**: Delete single documents with trash icon
- **Bulk Delete**: Remove multiple selected documents
- **Confirmation Dialogs**: Safety prompts before deletion
- **Detailed Warnings**: Shows chunk count and confirms action cannot be undone
- **Real-time Updates**: Document list refreshes automatically after deletion

## User Interface Components

### Document List View
Each document card displays:
- **Checkbox**: For selection (left side)
- **File Icon**: Visual indicator of document type
- **Filename**: Document name (clickable/truncated if too long)
- **Chunk Count**: Number of RAG chunks in the document
- **Session ID**: Associated session identifier
- **Delete Button**: Individual delete action (right side)

### Search Bar
- **Icon**: Magnifying glass for visual clarity
- **Placeholder**: "Search documents by name or session..."
- **Instant Filtering**: Results update as you type
- **Counter Update**: Shows matching results count

### Selection Controls
- **Select All Checkbox**: Located above document list
- **Bulk Delete Button**: Appears when documents are selected
- **Selection Count**: Shows in bulk delete button (e.g., "Delete Selected (3)")

### Confirmation Dialogs

#### Individual Delete Dialog
```
Delete Document
Are you sure you want to delete "[filename]"?
This will remove [N] chunks from the namespace.
This action cannot be undone.

[Cancel] [Delete]
```

#### Bulk Delete Dialog
```
Delete Multiple Documents
Are you sure you want to delete [N] selected document(s)?
This action cannot be undone.

[Cancel] [Delete N Document(s)]
```

## API Endpoints

### List Documents in Namespace
```
GET /namespaces/{namespace_name}/documents

Response:
{
  "namespace": "default",
  "documents": [
    {
      "doc_id": "uuid",
      "filename": "document.pdf",
      "namespace": "default",
      "chunk_count": 5,
      "session_id": "session-123"
    }
  ],
  "total_documents": 1,
  "total_chunks": 5
}
```

### Delete Individual Document
```
DELETE /namespaces/{namespace_name}/documents/{doc_id}

Response:
{
  "status": "success",
  "message": "Document deleted successfully",
  "namespace": "default",
  "doc_id": "uuid",
  "deleted_chunks": 5
}
```

## Usage Examples

### Example 1: Search for Documents
1. Navigate to the Files tab
2. Type in the search bar (e.g., "report")
3. View filtered results showing only matching documents
4. Counter updates to show "2/10" if 2 out of 10 documents match

### Example 2: Delete a Single Document
1. Locate the document in the list
2. Click the red trash icon on the right side
3. Review the confirmation dialog
4. Click "Delete" to confirm or "Cancel" to abort
5. Document is removed and list refreshes automatically

### Example 3: Bulk Delete Documents
1. Select documents by clicking their checkboxes
2. "Delete Selected (N)" button appears
3. Click the bulk delete button
4. Confirm the operation in the dialog
5. All selected documents are removed
6. Selection is cleared and list refreshes

### Example 4: Select All and Delete
1. Click "Select All" checkbox above the document list
2. All visible documents are selected
3. Click "Delete Selected (N)" button
4. Confirm bulk deletion
5. All documents in current view are removed

## Error Handling

### Common Errors
- **Document Not Found**: Occurs if document was already deleted
- **Namespace Not Found**: Namespace doesn't exist or was deleted
- **Network Error**: API connection issues
- **Permission Error**: Insufficient rights to delete documents

### Error Messages
All errors are displayed in a red alert box at the top of the file manager with clear, actionable messages.

## Best Practices

### Document Organization
- Use meaningful session IDs for easier searching
- Upload related documents to the same namespace
- Regularly review and clean up unused documents

### Before Deleting
- Double-check document selection before bulk delete
- Use search to verify you're deleting the right documents
- Consider the impact on active RAG queries

### Performance
- Large document lists load with scrolling
- Search filtering is client-side for instant results
- Bulk operations are processed in parallel for speed

## Technical Implementation

### Frontend Components
- **FileManager.tsx**: Main component with document management
- **Checkbox.tsx**: Radix UI checkbox component
- **Dialog.tsx**: Confirmation dialog component
- **Real-time Filtering**: Client-side search using Array.filter()

### Backend API
- **rag/store.py**: `delete_document()` function removes chunks by doc_id
- **app/main.py**: DELETE endpoint at `/namespaces/{namespace}/documents/{doc_id}`
- **Error Handling**: HTTP exceptions with descriptive messages

### State Management
- Selected documents stored in Set for efficient lookup
- Search query triggers filtered document list
- Document list refetches after successful deletion

## Keyboard Shortcuts

Future enhancement: Add keyboard shortcuts for common operations
- `Ctrl+A` / `Cmd+A`: Select all documents
- `Delete`: Delete selected documents (with confirmation)
- `Escape`: Cancel selection or close dialogs

## Accessibility

- Checkboxes are keyboard navigable
- Dialog close buttons have screen reader text
- Focus management in confirmation dialogs
- Clear visual feedback for all interactions

## Future Enhancements

### Planned Features
- Document preview/download capability
- Sort documents by name, date, or size
- Filter by date range or session pattern
- Export document list to CSV
- Undo delete operation (trash/recycle bin)
- Document tagging and categories
- Advanced search with operators (AND, OR, NOT)
