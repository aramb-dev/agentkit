# AgentKit - Intelligent AI Assistant with Modern Web Interface 🚀

AgentKit is a comprehensive AI-powered assistant built with Google's Gemini models, featuring intelligent tool routing, real-time web search, persistent conversation history, and advanced file processing capabilities.

## ✨ Key Features

### 🧠 **Advanced AI Integration**

- **Google Gen AI SDK**: 43+ Gemini models (1.5, 2.0, 2.5 variants)
- **Intelligent Routing**: LLM-powered tool selection for optimal responses
- **Dynamic Model Discovery**: Auto-detects available models with 4000 token responses
- **Conversation Memory**: Maintains context across entire chat sessions

### 🔍 **Real-Time Web Search**

- **Tavily API Integration**: Current, accurate web information
- **Smart Search Triggers**: Automatically searches when queries need current data
- **Contextual Results**: Seamlessly integrates search results into responses

### 🖥️ **Modern React Frontend**

- **Professional UI**: Built with React, TypeScript, Vite, and Shadcn/ui
- **Markdown & Math Rendering**: Full support for formatted content with KaTeX
- **Real-time Chat**: Responsive interface with conversation persistence
- **File Management**: Integrated file upload and management system
- **Model Selection**: Dynamic picker for available AI models

### 📁 **Advanced File Processing**

- **Multi-format Support**: PDF, DOCX, TXT, MD, CSV, JSON
- **Persistent Storage**: Unique file IDs with deduplication and metadata
- **Smart Processing**: RAG integration for document question-answering
- **File Management API**: Upload, list, delete, and cleanup operations

### ⚡ **Production-Ready Backend**

- **FastAPI Server**: Async API with CORS support and error handling
- **Conversation History**: Maintains chat context across requests
- **Environment Configuration**: Secure API key management
- **Health Monitoring**: Comprehensive logging and error tracking

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

## 🧪 Development

### Running Tests

```bash
# Backend tests
python -m pytest

# Frontend tests
cd frontend && npm test
```

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
