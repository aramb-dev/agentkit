# AgentKit - Intelligent AI Assistant with Modern Web Interface 🚀

[![Test Suite](https://github.com/aramb-dev/agentkit/actions/workflows/test.yml/badge.svg)](https://github.com/aramb-dev/agentkit/actions/workflows/test.yml)

**Enhanced RAG Frontend Integration Complete** ✨

AgentKit is a powerful AI assistant that combines intelligent conversation with advanced document processing capabilities. The system features a modern React frontend with comprehensive RAG (Retrieval-Augmented Generation) document ingestion and multi-stage progress tracking.

## ✨ Latest Enhancements - RAG Frontend Integration

### 🎯 Complete Visual Progress Tracking
- **Multi-stage progress indicators**: Real-time feedback through upload → processing → embedding → completion
- **Stage-specific animations**: Blue spinners, orange pulsing icons, purple database indicators, green success checkmarks
- **Real-time progress bars**: Smooth animations with percentage indicators
- **Comprehensive error handling**: Categorized errors with actionable recovery guidance

### 📁 Enhanced File Upload Experience  
- **Drag-and-drop interface**: Intuitive file upload with visual feedback
- **Multi-format support**: PDF, TXT, DOCX, MD, JSON files (up to 50MB each)
- **Visual file management**: Clear indicators for upload status, processing stages, and completion
- **Comprehensive validation**: Client-side and server-side file validation with clear error messages
- **Error recovery**: Detailed error messages with specific resolution steps and retry logic

### 🎨 Modern UI Components
- **Progress components**: Built with @radix-ui/react-progress for smooth animations
- **Visual design system**: Consistent color coding and iconography throughout
- **Responsive design**: Optimized for all screen sizes and devices
- **Accessibility**: Full keyboard navigation and screen reader support

AgentKit is a comprehensive AI-powered assistant built with Google's Gemini models, featuring intelligent tool routing, real-time web search, persistent conversation history, and advanced file processing capabilities.

## ✨ Key Features

### 🧠 **Advanced AI Integration**

- **Google Gen AI SDK**: 43+ Gemini models (1.5, 2.0, 2.5 variants)
- **Intelligent Routing**: LLM-powered tool selection for optimal responses
- **Dynamic Model Discovery**: Auto-detects available models with 4000 token responses
- **Conversation Memory**: Maintains context across entire chat sessions

### 🔍 **Advanced RAG Features** ✅

- **Full Vector Store Integration**: Connected to ChromaDB for persistent document storage
- **Semantic Search**: Enhanced relevance scoring for better document retrieval
- **Citation Support**: Automatic source attribution with document references
- **Hybrid Search**: Combines web search and document retrieval for comprehensive answers
- **Search Modes**: Configurable search preferences (Auto, Web, Documents, Hybrid)
- **Query Understanding**: Advanced query preprocessing for improved semantic matching
- **Source Attribution**: Clear tracking of information sources in responses
- **End-to-End Workflow**: Complete PDF upload → embedding → query → citation pipeline

### ⚡ **Performance Optimizations (Phase 2.3 - NEW!)** 🚀

- **99% Faster Cached Queries**: <1ms response time for repeated queries (was 100-500ms)
- **54% Faster Embeddings**: 23ms generation time (was 50ms)
- **Query Result Caching**: LRU cache with 100 query capacity
- **Configurable Models**: 3 embedding models (fast/balanced/accurate)
- **Optimized Parameters**: Fine-tuned chunk sizes and retrieval settings
- **Real-time Monitoring**: Performance metrics via `/monitoring/rag` endpoint
- **Benchmarking Tools**: `benchmark_rag.py` for performance profiling
- **Parameter Tuning**: `tune_rag_params.py` for custom optimization

📚 **See [OPTIMIZATION_QUICKSTART.md](OPTIMIZATION_QUICKSTART.md) for quick start**  
📖 **See [VECTOR_SEARCH_OPTIMIZATION.md](VECTOR_SEARCH_OPTIMIZATION.md) for complete optimization guide**  
📋 **See [RAG_INTEGRATION.md](RAG_INTEGRATION.md) for RAG setup guide**

### 🌐 **Real-Time Web Search**

- **Tavily API Integration**: Current, accurate web information
- **Smart Search Triggers**: Automatically searches when queries need current data
- **Contextual Results**: Seamlessly integrates search results into responses

### 🖥️ **Modern React Frontend**

- **Professional UI**: Built with React, TypeScript, Vite, and Shadcn/ui
- **Markdown & Math Rendering**: Full support for formatted content with KaTeX
- **Real-time Chat**: Responsive interface with conversation persistence
- **File Management**: Integrated file upload and management system
- **Model Selection**: Dynamic picker for available AI models

### 📁 **Advanced File Processing & Document Management**

- **Multi-format Support**: PDF, DOCX, TXT, MD, CSV, JSON
- **Persistent Storage**: Unique file IDs with deduplication and metadata
- **Smart Processing**: RAG integration for document question-answering
- **File Management API**: Upload, list, delete, and cleanup operations
- **Document Management UI**: Search, filter, select, and delete documents with ease
- **Bulk Operations**: Select multiple documents for batch deletion
- **Confirmation Dialogs**: Safety prompts for destructive operations

### ⚡ **Production-Ready Backend**

- **FastAPI Server**: Async API with CORS support and comprehensive error handling
- **Conversation History**: Maintains chat context across requests
- **Environment Configuration**: Secure API key management
- **Health Monitoring**: Comprehensive logging and error tracking

### 🛡️ **Error Handling & Validation (Phase 2.2 - Complete)** ✅

- **Comprehensive File Validation**: Size (50MB), type, format, and path traversal checks
- **Standardized Error Responses**: Consistent JSON format with error codes and details
- **Retry Logic**: Automatic retry with exponential backoff for transient failures
- **Client-Side Validation**: Pre-upload validation with instant feedback
- **Request Tracking**: Unique request IDs for debugging and monitoring
- **Security Features**: Path traversal protection, extension whitelisting, DoS prevention
- **Clear Error Messages**: User-friendly messages with actionable recovery steps
- **Extensive Testing**: 15+ automated tests covering validation scenarios

📚 **See [ERROR_HANDLING.md](ERROR_HANDLING.md) for complete error handling guide**

## 🏗️ Project Structure

```
agentkit/
├── agent/                    # Core AI logic
│   ├── agent.py             # Orchestration with conversation history
│   ├── llm_client.py        # Google Gen AI integration
│   ├── router.py            # Intelligent LLM-based tool selection
│   ├── tools.py             # Web search, RAG, memory tools
│   ├── document_processor.py # Multi-format file processing
│   └── file_manager.py      # Persistent storage system
├── app/
│   └── main.py              # Enhanced FastAPI server
├── frontend/                # Modern React application
│   ├── src/components/      # Chat, FileUpload, FileManager
│   ├── src/types/          # TypeScript definitions
│   └── package.json        # Vite + React + Shadcn/ui
├── uploads/                 # File storage directory
│   ├── files/              # Uploaded files
│   └── metadata/           # File metadata
├── .env.example            # Environment template
└── requirements.txt        # Python dependencies
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Google AI API key ([Get one here](https://makersuite.google.com/app/apikey))
- Tavily API key ([Get one here](https://tavily.com/))

### 1. Environment Setup

```bash
# Clone the repository
git clone https://github.com/aramb-dev/agentkit.git
cd agentkit

# Copy environment template
cp .env.example .env

# Add your API keys to .env
GOOGLE_API_KEY=your_google_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here
```

### 2. Backend Setup

```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt

# Start the FastAPI server
uvicorn app.main:app --reload
```

The backend will be available at `http://localhost:8000`

### 3. Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install Node.js dependencies
npm install

# Start development server
npm run dev
```

The frontend will be available at `http://localhost:5173`

## 🎯 Usage Examples

### Chat Interface

- **Natural Conversations**: Ask questions, get intelligent responses
- **Web Search**: "What's the latest news about AI?" (automatically searches)
- **File Processing**: Upload documents and ask questions about their content
- **Math & Code**: Full markdown rendering with LaTeX math support

### API Endpoints

- `POST /chat` - Send messages with conversation history
- `POST /upload` - Upload files for processing
- `GET /models` - List available AI models
- `GET /files` - List uploaded files
- `DELETE /files/{file_id}` - Delete specific files

## 🔧 Advanced Configuration

### Advanced RAG Features 🆕

AgentKit now includes powerful search capabilities:

#### Search Modes

- **🔍 Auto Mode**: Intelligent LLM-powered routing (default)
- **🌐 Web Mode**: Search current web information only
- **📄 Documents Mode**: Search uploaded documents only
- **⚡ Hybrid Mode**: Combine web and document search

#### Citation Features

- Automatic source attribution in responses
- Document name and chunk references
- Relevance scores for each source
- Clear distinction between web and document sources

#### Query Understanding

- LLM-powered query preprocessing
- Intelligent semantic enhancement
- Context-aware filler word removal
- Automatic concept extraction

**See [ADVANCED_RAG_FEATURES.md](ADVANCED_RAG_FEATURES.md) for detailed documentation.**

### Model Selection

AgentKit automatically discovers available Gemini models:

- **Gemini 1.5**: Fast, efficient for most tasks
- **Gemini 2.0**: Enhanced reasoning and code generation
- **Gemini 2.5**: Latest model with advanced capabilities

### File Processing

Supported formats and use cases:

- **PDFs**: Extract text, answer questions about content
- **Documents**: DOCX, TXT, MD files for RAG processing
- **Data**: CSV, JSON for analysis and querying

### Environment Variables

```bash
GOOGLE_API_KEY=your_google_api_key
TAVILY_API_KEY=your_tavily_api_key
MAX_FILE_SIZE=10485760  # 10MB default
CONVERSATION_HISTORY_LIMIT=50  # Messages to keep in memory
```

## 🧪 Testing

AgentKit has comprehensive test coverage for both backend and frontend components.

### Running All Tests

```bash
# Run the complete test suite
./run_tests.sh
```

This will run:
- Backend unit and integration tests with coverage
- Frontend component tests with coverage
- Generate HTML coverage reports

### Running Tests Individually

```bash
# Backend tests
python -m pytest test_*.py -v

# Backend tests with coverage
python -m pytest test_*.py --cov=agent --cov=app --cov=rag --cov-report=html

# Frontend tests
cd frontend && npm test

# Frontend tests with coverage
cd frontend && npm run test:coverage

# End-to-end tests
npx playwright test
```

### Test Coverage

Coverage reports are generated in:
- Backend: `htmlcov/index.html`
- Frontend: `frontend/coverage/index.html`

For detailed testing documentation, see [TESTING.md](TESTING.md)

### Building for Production

```bash
# Build frontend
cd frontend && npm run build

# The built files will be in frontend/dist/
```

## 📚 API Documentation

Once the backend is running, visit:

- **Interactive API Docs**: `http://localhost:8000/docs`
- **OpenAPI Spec**: `http://localhost:8000/openapi.json`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Commit your changes (`git commit -m 'Add amazing feature'`)
5. Push to the branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Google AI**: For the powerful Gemini models
- **Tavily**: For real-time web search capabilities
- **Shadcn/ui**: For the beautiful UI components
- **React & Vite**: For the modern frontend framework

---

**AgentKit** - Where AI meets intuitive design for powerful, conversational intelligence. 🎉
