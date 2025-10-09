"""
Database module for conversation persistence using SQLite.
Provides schema and CRUD operations for conversations and messages.
"""

import sqlite3
import json
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# Database file location
DB_PATH = Path(__file__).parent.parent / "uploads" / "conversations.db"


def get_db_connection():
    """Get a database connection with row factory."""
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    """Initialize database schema."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create conversations table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            namespace TEXT NOT NULL DEFAULT 'default',
            session_id TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP NOT NULL,
            updated_at TIMESTAMP NOT NULL,
            message_count INTEGER DEFAULT 0,
            metadata TEXT
        )
    """)
    
    # Create messages table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
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
    """)
    
    # Create indexes for efficient queries
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_conversations_created_at 
        ON conversations(created_at DESC)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_conversations_updated_at 
        ON conversations(updated_at DESC)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_conversations_session_id 
        ON conversations(session_id)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_messages_conversation_id 
        ON messages(conversation_id)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_messages_timestamp 
        ON messages(timestamp)
    """)
    
    conn.commit()
    conn.close()
    logger.info(f"Database initialized at {DB_PATH}")


def create_conversation(
    conversation_id: str,
    session_id: str,
    title: str = "New Conversation",
    namespace: str = "default",
    metadata: Optional[Dict] = None
) -> Dict[str, Any]:
    """Create a new conversation."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    now = datetime.now(timezone.utc).isoformat()
    metadata_json = json.dumps(metadata or {})
    
    try:
        cursor.execute("""
            INSERT INTO conversations (id, session_id, title, namespace, created_at, updated_at, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (conversation_id, session_id, title, namespace, now, now, metadata_json))
        
        conn.commit()
        
        return {
            "id": conversation_id,
            "session_id": session_id,
            "title": title,
            "namespace": namespace,
            "created_at": now,
            "updated_at": now,
            "message_count": 0,
            "metadata": metadata or {}
        }
    except sqlite3.IntegrityError as e:
        logger.error(f"Failed to create conversation: {e}")
        raise ValueError(f"Conversation with session_id {session_id} already exists")
    finally:
        conn.close()


def get_conversation(conversation_id: str) -> Optional[Dict[str, Any]]:
    """Get a conversation by ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM conversations WHERE id = ?
    """, (conversation_id,))
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            "id": row["id"],
            "session_id": row["session_id"],
            "title": row["title"],
            "namespace": row["namespace"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "message_count": row["message_count"],
            "metadata": json.loads(row["metadata"]) if row["metadata"] else {}
        }
    return None


def get_conversation_by_session(session_id: str) -> Optional[Dict[str, Any]]:
    """Get a conversation by session ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM conversations WHERE session_id = ?
    """, (session_id,))
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            "id": row["id"],
            "session_id": row["session_id"],
            "title": row["title"],
            "namespace": row["namespace"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "message_count": row["message_count"],
            "metadata": json.loads(row["metadata"]) if row["metadata"] else {}
        }
    return None


def list_conversations(
    limit: int = 50,
    offset: int = 0,
    namespace: Optional[str] = None,
    search_query: Optional[str] = None
) -> List[Dict[str, Any]]:
    """List conversations with pagination and optional filtering."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = "SELECT * FROM conversations"
    params = []
    conditions = []
    
    if namespace:
        conditions.append("namespace = ?")
        params.append(namespace)
    
    if search_query:
        conditions.append("(title LIKE ? OR id LIKE ?)")
        search_pattern = f"%{search_query}%"
        params.extend([search_pattern, search_pattern])
    
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    
    query += " ORDER BY updated_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    return [{
        "id": row["id"],
        "session_id": row["session_id"],
        "title": row["title"],
        "namespace": row["namespace"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "message_count": row["message_count"],
        "metadata": json.loads(row["metadata"]) if row["metadata"] else {}
    } for row in rows]


def update_conversation(
    conversation_id: str,
    title: Optional[str] = None,
    metadata: Optional[Dict] = None
) -> bool:
    """Update a conversation."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    updates = ["updated_at = ?"]
    params = [datetime.now(timezone.utc).isoformat()]
    
    if title is not None:
        updates.append("title = ?")
        params.append(title)
    
    if metadata is not None:
        updates.append("metadata = ?")
        params.append(json.dumps(metadata))
    
    params.append(conversation_id)
    
    cursor.execute(f"""
        UPDATE conversations 
        SET {', '.join(updates)}
        WHERE id = ?
    """, params)
    
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    
    return success


def delete_conversation(conversation_id: str) -> bool:
    """Delete a conversation and all its messages."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
    success = cursor.rowcount > 0
    
    conn.commit()
    conn.close()
    
    return success


def add_message(
    message_id: str,
    conversation_id: str,
    role: str,
    content: str,
    model: Optional[str] = None,
    tool_used: Optional[str] = None,
    attachments: Optional[List[Dict]] = None,
    citations: Optional[List[Dict]] = None,
    timestamp: Optional[str] = None
) -> Dict[str, Any]:
    """Add a message to a conversation."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if timestamp is None:
        timestamp = datetime.now(timezone.utc).isoformat()
    
    attachments_json = json.dumps(attachments or [])
    citations_json = json.dumps(citations or [])
    
    try:
        cursor.execute("""
            INSERT INTO messages (id, conversation_id, role, content, model, tool_used, attachments, citations, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (message_id, conversation_id, role, content, model, tool_used, attachments_json, citations_json, timestamp))
        
        # Update conversation message count and updated_at
        cursor.execute("""
            UPDATE conversations 
            SET message_count = message_count + 1,
                updated_at = ?
            WHERE id = ?
        """, (timestamp, conversation_id))
        
        conn.commit()
        
        return {
            "id": message_id,
            "conversation_id": conversation_id,
            "role": role,
            "content": content,
            "model": model,
            "tool_used": tool_used,
            "attachments": attachments or [],
            "citations": citations or [],
            "timestamp": timestamp
        }
    finally:
        conn.close()


def get_messages(
    conversation_id: str,
    limit: Optional[int] = None,
    offset: int = 0
) -> List[Dict[str, Any]]:
    """Get messages for a conversation."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = """
        SELECT * FROM messages 
        WHERE conversation_id = ? 
        ORDER BY timestamp ASC
    """
    params = [conversation_id]
    
    if limit is not None:
        query += " LIMIT ? OFFSET ?"
        params.extend([limit, offset])
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    return [{
        "id": row["id"],
        "conversation_id": row["conversation_id"],
        "role": row["role"],
        "content": row["content"],
        "model": row["model"],
        "tool_used": row["tool_used"],
        "attachments": json.loads(row["attachments"]) if row["attachments"] else [],
        "citations": json.loads(row["citations"]) if row["citations"] else [],
        "timestamp": row["timestamp"]
    } for row in rows]


def search_messages(
    query: str,
    conversation_id: Optional[str] = None,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """Search messages by content."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    sql_query = "SELECT * FROM messages WHERE content LIKE ?"
    params = [f"%{query}%"]
    
    if conversation_id:
        sql_query += " AND conversation_id = ?"
        params.append(conversation_id)
    
    sql_query += " ORDER BY timestamp DESC LIMIT ?"
    params.append(limit)
    
    cursor.execute(sql_query, params)
    rows = cursor.fetchall()
    conn.close()
    
    return [{
        "id": row["id"],
        "conversation_id": row["conversation_id"],
        "role": row["role"],
        "content": row["content"],
        "model": row["model"],
        "tool_used": row["tool_used"],
        "attachments": json.loads(row["attachments"]) if row["attachments"] else [],
        "citations": json.loads(row["citations"]) if row["citations"] else [],
        "timestamp": row["timestamp"]
    } for row in rows]


# Initialize database on module import
init_database()
