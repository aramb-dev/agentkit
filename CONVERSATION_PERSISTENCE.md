# Conversation Persistence Documentation

## Overview

AgentKit now includes full conversation persistence capabilities, allowing users to save, retrieve, search, and export their chat history. All conversations are automatically saved to a local SQLite database with support for namespaces, search, and multiple export formats.

## Features

### ✅ Automatic Conversation Saving
- Every chat interaction is automatically saved to the database
- Conversations are organized by session ID for easy retrieval
- Messages include metadata: role, content, model used, tool used, timestamps

### ✅ Conversation History Sidebar
- Visual sidebar showing all past conversations
- Shows conversation title, timestamp, and message count
- Real-time updates as new conversations are created
- Collapsible interface to maximize chat space

### ✅ Search and Filter
- **Search by content**: Find conversations by title or ID
- **Filter by namespace**: Isolate conversations by namespace
- **Real-time filtering**: Results update as you type

### ✅ Conversation Management
- **Load conversation**: Click any conversation to load its full history
- **Delete conversation**: Remove conversations you no longer need
- **Export conversation**: Download in JSON, TXT, or Markdown format
- **Update title**: Rename conversations via API

### ✅ Namespace Isolation
- Conversations are tied to namespaces for organization
- Filter history by namespace to see related conversations
- Perfect for separating work contexts or projects

## Database Schema

### Conversations Table
```sql
CREATE TABLE conversations (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    namespace TEXT NOT NULL DEFAULT 'default',
    session_id TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    message_count INTEGER DEFAULT 0,
    metadata TEXT
)
```

### Messages Table
```sql
CREATE TABLE messages (
    id TEXT PRIMARY KEY,
    conversation_id TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    model TEXT,
    tool_used TEXT,
    attachments TEXT,
    citations TEXT,
    timestamp TIMESTAMP NOT NULL,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
)
```

## API Endpoints

### List Conversations
```http
GET /conversations?limit=50&offset=0&namespace=default&search=query
```

**Query Parameters:**
- `limit` (optional): Number of conversations to return (default: 50)
- `offset` (optional): Pagination offset (default: 0)
- `namespace` (optional): Filter by namespace
- `search` (optional): Search by title or ID

**Response:**
```json
{
  "conversations": [
    {
      "id": "uuid",
      "session_id": "session-uuid",
      "title": "Conversation title",
      "namespace": "default",
      "created_at": "2025-10-09T19:37:47.783681+00:00",
      "updated_at": "2025-10-09T19:37:47.783681+00:00",
      "message_count": 5,
      "metadata": {}
    }
  ],
  "total": 1,
  "limit": 50,
  "offset": 0
}
```

### Get Conversation Details
```http
GET /conversations/{conversation_id}
```

**Response:**
```json
{
  "id": "uuid",
  "session_id": "session-uuid",
  "title": "Conversation title",
  "namespace": "default",
  "created_at": "2025-10-09T19:37:47.783681+00:00",
  "updated_at": "2025-10-09T19:37:47.783681+00:00",
  "message_count": 2,
  "metadata": {},
  "messages": [
    {
      "id": "msg-uuid",
      "conversation_id": "uuid",
      "role": "user",
      "content": "Hello",
      "model": null,
      "tool_used": null,
      "attachments": [],
      "citations": [],
      "timestamp": "2025-10-09T19:37:47.783681+00:00"
    },
    {
      "id": "msg-uuid-2",
      "conversation_id": "uuid",
      "role": "assistant",
      "content": "Hi there!",
      "model": "gemini-2.0-flash-001",
      "tool_used": "idle",
      "attachments": [],
      "citations": [],
      "timestamp": "2025-10-09T19:37:48.123456+00:00"
    }
  ]
}
```

### Update Conversation
```http
PUT /conversations/{conversation_id}?title=New+Title
```

**Query Parameters:**
- `title` (optional): New title for the conversation

**Response:**
```json
{
  "success": true,
  "conversation_id": "uuid"
}
```

### Delete Conversation
```http
DELETE /conversations/{conversation_id}
```

**Response:**
```json
{
  "success": true,
  "conversation_id": "uuid"
}
```

### Search Messages
```http
GET /conversations/search/messages?query=python&limit=50
```

**Query Parameters:**
- `query` (required): Search term
- `conversation_id` (optional): Limit search to specific conversation
- `limit` (optional): Maximum results to return (default: 50)

**Response:**
```json
{
  "messages": [
    {
      "id": "msg-uuid",
      "conversation_id": "uuid",
      "role": "user",
      "content": "Tell me about Python",
      "model": null,
      "tool_used": null,
      "attachments": [],
      "citations": [],
      "timestamp": "2025-10-09T19:37:47.783681+00:00"
    }
  ],
  "total": 1
}
```

### Export Conversation
```http
POST /conversations/{conversation_id}/export?format=json
```

**Query Parameters:**
- `format` (required): Export format - `json`, `txt`, or `md`

**Response (JSON format):**
```json
{
  "id": "uuid",
  "title": "Conversation title",
  "messages": [...],
  ...
}
```

**Response (TXT/MD format):**
```json
{
  "content": "Formatted conversation text...",
  "format": "txt"
}
```

## Usage Examples

### Frontend Usage

#### Loading Conversations
The conversation history sidebar automatically loads and displays conversations:

```typescript
// Conversations are loaded from the API
const response = await axios.get<ConversationListResponse>(
    `${API_BASE_URL}/conversations?namespace=${namespace}`
);
```

#### Loading a Specific Conversation
Click on any conversation in the sidebar to load its full history:

```typescript
const handleLoadConversation = async (conversation: Conversation) => {
    const response = await axios.get<Conversation>(
        `${API_BASE_URL}/conversations/${conversation.id}`
    );
    
    // Convert messages to chat format
    const chatMessages = response.data.messages.map(msg => ({
        id: msg.id,
        content: msg.content,
        role: msg.role,
        timestamp: new Date(msg.timestamp),
        model: msg.model,
        toolUsed: msg.tool_used
    }));
    
    // Update chat state
    setChatState({ ...prev, messages: chatMessages });
};
```

#### Searching Conversations
Use the search box in the sidebar:

```typescript
const [searchQuery, setSearchQuery] = useState('');

// Search is debounced (300ms) and automatically triggers
useEffect(() => {
    const timer = setTimeout(() => {
        loadConversations(); // Reloads with search query
    }, 300);
    return () => clearTimeout(timer);
}, [searchQuery]);
```

#### Exporting Conversations
Click the export button (download icon) on any conversation:

```typescript
const handleExportConversation = async (
    conversationId: string, 
    format: 'json' | 'txt' | 'md'
) => {
    const response = await axios.post(
        `${API_BASE_URL}/conversations/${conversationId}/export?format=${format}`
    );
    
    // Create download
    const blob = new Blob([content], { type: mimeType });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `conversation-${conversationId}.${format}`;
    a.click();
};
```

### Backend Usage

#### Automatic Saving
Conversations are automatically saved on every chat interaction:

```python
# In app/main.py chat endpoint
conversation = db.get_conversation_by_session(session_id)
if not conversation:
    # Create new conversation
    conversation = db.create_conversation(
        conversation_id=str(uuid.uuid4()),
        session_id=session_id,
        title=message[:50] + "..." if len(message) > 50 else message,
        namespace=namespace
    )

# Save user message
db.add_message(
    message_id=str(uuid.uuid4()),
    conversation_id=conversation["id"],
    role="user",
    content=message
)

# Save assistant response
db.add_message(
    message_id=str(uuid.uuid4()),
    conversation_id=conversation["id"],
    role="assistant",
    content=response.get("answer", ""),
    model=model,
    tool_used=response.get("tool_used")
)
```

#### Direct Database Access
You can also interact directly with the database module:

```python
from app import database as db

# Create a conversation
conversation = db.create_conversation(
    conversation_id="my-conv-id",
    session_id="my-session-id",
    title="My Conversation",
    namespace="my-namespace"
)

# Add messages
db.add_message(
    message_id="msg-1",
    conversation_id="my-conv-id",
    role="user",
    content="Hello"
)

# Get messages
messages = db.get_messages("my-conv-id")

# Search messages
results = db.search_messages("python", limit=10)

# Update conversation
db.update_conversation("my-conv-id", title="Updated Title")

# Delete conversation
db.delete_conversation("my-conv-id")
```

## Database Location

The SQLite database is stored at:
```
uploads/conversations.db
```

This file is created automatically on first use and persists across server restarts.

## Performance Considerations

### Indexes
The database includes indexes on:
- `conversations.created_at` (DESC)
- `conversations.updated_at` (DESC)
- `conversations.session_id`
- `messages.conversation_id`
- `messages.timestamp`

These indexes ensure fast queries even with thousands of conversations.

### Pagination
Use the `limit` and `offset` parameters when listing conversations to avoid loading too much data at once:

```http
GET /conversations?limit=20&offset=0  # First page
GET /conversations?limit=20&offset=20 # Second page
```

### Search Performance
- Searches use LIKE queries with wildcards
- For better performance with large datasets, consider implementing full-text search (FTS5)
- Current implementation is suitable for up to ~10,000 conversations

## Export Formats

### JSON Format
Complete conversation data with all metadata:
```json
{
  "id": "uuid",
  "title": "Conversation",
  "messages": [...],
  "namespace": "default",
  "created_at": "...",
  "updated_at": "..."
}
```

### Text Format
Human-readable plain text:
```
Conversation: My Conversation
Created: 2025-10-09T19:37:47.783681+00:00
Namespace: default
==================================================

USER: Hello

ASSISTANT: Hi there!
  (Model: gemini-2.0-flash-001)
```

### Markdown Format
Formatted markdown suitable for documentation:
```markdown
# My Conversation

**Created:** 2025-10-09T19:37:47.783681+00:00
**Namespace:** default
**Messages:** 2

---

### 👤 User

Hello

### 🤖 Assistant
*Model: gemini-2.0-flash-001*

Hi there!
```

## Testing

Run the conversation persistence tests:

```bash
python -m pytest test_conversations.py -v
```

This will test:
- Conversation creation via chat
- Listing conversations with pagination
- Getting conversation details
- Updating conversation titles
- Deleting conversations
- Searching messages
- Exporting conversations in all formats
- Namespace filtering
- Direct database operations

## Troubleshooting

### Database locked error
If you get "database is locked" errors:
- Ensure only one instance of the server is running
- Check that no other processes are accessing the database
- Consider increasing the SQLite timeout (contact support)

### Missing conversations
If conversations don't appear:
- Check that the `uploads/` directory has write permissions
- Verify the database file exists at `uploads/conversations.db`
- Check server logs for errors during conversation creation

### Export not working
If export downloads are empty:
- Check browser console for errors
- Verify the conversation ID is correct
- Ensure the format parameter is valid (json, txt, or md)

## Future Enhancements

Potential improvements for conversation persistence:
- Full-text search using SQLite FTS5
- Conversation tags and categories
- Shared conversations between users
- Conversation templates
- Bulk export of multiple conversations
- Conversation analytics (most used tools, response times, etc.)
- Archive old conversations to separate storage
- Conversation import from external sources

## Related Documentation

- [RAG Integration](RAG_INTEGRATION.md) - Document storage and retrieval
- [Namespace Management](NAMESPACE_MANAGEMENT.md) - Organizing conversations
- [API Documentation](http://localhost:8000/docs) - Complete API reference
