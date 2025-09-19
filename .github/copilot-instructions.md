# AgentKit Development Guide

## 🏗️ Architecture Overview

AgentKit is a modular AI agent framework with **LLM-powered tool routing** and a modern React frontend. The system uses **Google Gemini models** for intelligent conversation and tool selection, not keyword matching.

### Core Components

- **`agent/router.py`**: LLM-based intelligent tool selection (not keyword matching)
- **`agent/agent.py`**: Main orchestration with conversation history support
- **`agent/tools.py`**: Four core tools: `web` (Tavily API), `rag` (documentation), `memory`, `idle`
- **`app/main.py`**: FastAPI server with file upload, chat history, and RAG document ingestion
- **`frontend/`**: React TypeScript with Shadcn/ui components and namespace-based chat

### Key Architectural Decisions

**LLM Router vs Keywords**: Uses `await llm_client.generate_response()` to analyze user intent and select tools, with keyword fallback only on LLM failure. The router prompt in `agent/router.py` is critical for tool selection accuracy.

**Conversation Context**: `run_agent_with_history()` maintains last 10 messages for context, passes last 5 to response generation. This enables contextual tool selection and coherent responses.

**Namespace Isolation**: RAG system uses ChromaDB collections per namespace (`chatState.namespace`) for document isolation between sessions.

## 🔧 Development Workflows

### Environment Setup

```bash
# Backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Frontend
cd frontend && npm install && npm run dev
```

### Testing Agent Logic

```bash
python test_agent_llm.py  # Tests all tools with real LLM responses
python test_main.py       # Tests FastAPI endpoints
```

### Adding New Tools

1. Add function to `agent/tools.py` following `async def _tool_name(query: str) -> str:` pattern
2. Add to `TOOLS` dict with name, description, and function reference
3. Update router prompt in `agent/router.py` with tool selection rules
4. Tool descriptions are auto-discovered for LLM routing - no manual keyword mapping needed

## 🎯 Project-Specific Patterns

### Tool Implementation Pattern

```python
async def _web_search(query: str) -> str:
    """Always include docstring - used by router for tool descriptions."""
    # Real API integration with graceful fallback
    if tavily_client:
        return await real_api_call()
    return _fallback_simulation(query)
```

### Response Generation Pattern

The agent uses **contextual prompts** in `_format_response_with_context()` that vary by tool. Each tool gets a different system prompt - `idle` tool gets conversational prompt, others get task-specific prompts.

### Frontend State Management

```typescript
// ChatState includes namespace for RAG document isolation
const [chatState, setChatState] = useState<ChatState>({
  namespace: "default", // ChromaDB collection name
  sessionId: crypto.randomUUID(), // For session tracking
  // ... other state
});
```

## 🔗 Integration Points

### RAG Pipeline Flow

1. **PDF Upload**: `frontend/ChatContainer.tsx` → `ingestDocument()` → `/docs/ingest` endpoint
2. **Text Extraction**: `rag/ingest.py` chunks PDFs with 900-char chunks, 150-char overlap
3. **Vector Storage**: `rag/store.py` uses sentence-transformers + ChromaDB with namespace isolation
4. **Retrieval**: RAG tool in `agent/tools.py` queries vectors for relevant context

### Chat API Integration

```typescript
// Frontend sends conversation history for context
const historyForContext = chatState.messages.slice(-10).map((msg) => ({
  role: msg.role,
  content: msg.content,
  timestamp: msg.timestamp.toISOString(),
}));
formData.append("history", JSON.stringify(historyForContext));
```

### LLM Client Pattern

```python
# agent/llm_client.py provides unified interface
await llm_client.generate_response(prompt, model)
# Handles API retries, model availability, graceful degradation
```

## 📁 Key File Locations

- **Tool Logic**: `agent/tools.py` - All tool implementations and TOOLS registry
- **Router Logic**: `agent/router.py` - LLM-powered tool selection with fallback
- **API Endpoints**: `app/main.py` - FastAPI routes for chat, file upload, RAG ingestion
- **Frontend Chat**: `frontend/src/components/ChatContainer.tsx` - Main chat interface with RAG integration
- **Type Definitions**: `frontend/src/types/chat.ts` - TypeScript interfaces for API communication
- **RAG Implementation**: `rag/ingest.py` and `rag/store.py` - Document processing and vector storage

## 🚀 Critical Commands

```bash
# Start development environment
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
cd frontend && npm run dev

# Test RAG document ingestion
curl -X POST "http://localhost:8000/docs/ingest" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@document.pdf" \
  -F "namespace=test"

# Run agent tests with real LLM
python test_agent_llm.py
```

## 🔍 Debugging Tips

- **Tool Selection Issues**: Check router prompt in `agent/router.py` and LLM response logs
- **RAG Not Working**: Verify namespace consistency between ingestion and chat requests
- **Frontend API Errors**: Check CORS configuration in `app/main.py` and API_BASE_URL in ChatContainer
- **LLM Response Issues**: Check API keys in `.env` and model availability via `/models` endpoint

Remember: This system prioritizes **intelligent LLM-based routing** over rule-based approaches. When debugging tool selection, focus on the router's LLM prompt rather than keyword matching logic.
