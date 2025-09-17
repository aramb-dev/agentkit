# AgentKit Setup Instructions

## Overview

AgentKit has been updated to use the official Google Gen AI SDK for intelligent responses instead of hardcoded messages. The agent now provides contextual, AI-generated responses while maintaining its modular tool architecture.

## Quick Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set up API Keys

1. **Gemini API Key**: Go to [Google AI Studio](https://aistudio.google.com/app/apikey) and create an API key
2. **Tavily API Key** (optional but recommended): Go to [Tavily](https://tavily.com) and get a free API key for enhanced web search
3. Create a `.env` file in the project root:

```bash
# .env file
GOOGLE_API_KEY=your_gemini_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here  # Optional for real web search
```

**Note**: Without Tavily API key, the web search will use simulated results. With Tavily, you get real, current web search results.

### 3. Test the Agent

```bash
python3 test_agent_llm.py
```

### 4. Run the Web Interface

```bash
# Start the FastAPI backend
python3 -m uvicorn app.main:app --reload --port 8000

# In another terminal, start the Streamlit UI
streamlit run ui/streamlit_app.py
```

## What Was Fixed

### Problem

The original AgentKit was sending generic "I hope this helps!" responses instead of using AI to generate contextual answers.

### Solution

1. **Added Modern LLM Integration**: Created `agent/llm_client.py` using the official Google Gen AI SDK
2. **Updated Response Generation**: Modified `agent/agent.py` to use LLM for all responses
3. **Enhanced Tools**: Improved tool outputs to provide better context for the LLM
4. **Better Routing**: Enhanced keyword matching for more accurate tool selection

### Key Changes

#### Before

```python
# Hardcoded generic response
return "Final answer: I hope this helps!"
```

#### After

```python
# AI-generated contextual response using Google Gen AI SDK
response = await self.genai_client.aio.models.generate_content(
    model='gemini-2.0-flash-001',
    contents=prompt,
    config=types.GenerateContentConfig(temperature=0.7)
)
return response.text
```

## Features

### 🔧 Tool Selection

- **Web Search**: Real-time web search using Tavily API (with fallback simulation)
- **Documentation**: Comprehensive AgentKit architecture and setup documentation
- **Memory**: Conversation memory with timestamps and context
- **General**: Intelligent conversation for greetings and general questions

### 🤖 AI Integration

- **Google Gemini 2.0 Flash**: Latest model for fast, intelligent responses
- **Tavily Web Search**: Real-time web search with current results
- **Contextual Processing**: Combines search results with AI analysis
- **Graceful Fallbacks**: Works even when APIs are unavailable

### 🛠️ Architecture

- **Router**: Intelligent query analysis and tool selection
- **Tools**: Modular functions with real API integrations
- **LLM Client**: Official Google Gen AI SDK integration
- **Agent**: Orchestrates tools + AI for comprehensive responses

## Example Interactions

### Greeting

**User**: "hey!!"
**Agent**: "Hello! I'm AgentKit, a modular AI agent. I can help you with web searches, document explanations, and memory functions. What would you like me to help you with?"

### Search

**User**: "search for AI news"
**Agent**: "Here are the latest AI developments I found: [AI-generated response with search results]"

### Documentation

**User**: "explain the architecture"
**Agent**: "AgentKit's architecture consists of several key components: [detailed explanation]"

## Troubleshooting

### No API Key

If you see fallback responses, ensure your `GOOGLE_API_KEY` is set correctly:

```bash
echo $GOOGLE_API_KEY
```

### Import Errors

Make sure all dependencies are installed:

```bash
pip install -r requirements.txt
```

### API Errors

Check that your Gemini API key is valid and has sufficient quota.

## Development

### Adding New Tools

1. Add the tool function to `agent/tools.py`
2. Update the `TOOLS` dictionary
3. Add keywords to `_TOOL_KEYWORDS` in `agent/router.py`

### Customizing Responses

Modify the prompts in the `_format_response` function in `agent/agent.py` to change how the LLM generates responses.
