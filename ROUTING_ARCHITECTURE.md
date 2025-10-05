# Enhanced Tool Routing Architecture

AgentKit's enhanced routing system provides intelligent, context-aware tool selection with advanced capabilities including tool chaining, performance monitoring, and sophisticated fallback mechanisms.

## Architecture Overview

### Core Components

1. **Intelligent Router** (`agent/router.py`)
   - LLM-powered tool selection with contextual analysis
   - Enhanced fallback mechanisms
   - Performance monitoring and metrics collection

2. **Tool Chain Manager** (`agent/tool_chain.py`)
   - Automatic detection of complex workflows
   - Sequential and parallel tool execution
   - Dependency management and error handling

3. **Enhanced Agent Orchestrator** (`agent/agent.py`)
   - Integration of routing and chaining capabilities
   - Context-aware response generation
   - Comprehensive error handling and recovery

4. **Performance Monitoring** (Across all components)
   - Real-time metrics collection
   - Tool execution statistics
   - Routing decision tracking

## Key Features

### 1. Context-Aware Tool Selection

The routing system analyzes both the user's message and conversation context to make intelligent tool selection decisions:

```python
analysis = _analyze_message_context(message, conversation_context)
# Returns: {
#   "complexity": "simple|complex",
#   "needs_facts": True|False,
#   "about_agentkit": True|False,
#   "memory_intent": True|False,
#   "conversational": True|False,
#   "has_context": True|False,
#   "word_count": int
# }
```

### 2. Enhanced Prompt Engineering

The router uses sophisticated prompts that consider:
- Message complexity analysis
- Conversation context
- Tool capabilities and strengths
- Previous tool usage patterns

**Routing Prompt Structure:**
- **Context Analysis**: Semantic understanding of query intent
- **Tool Descriptions**: Clear capability definitions
- **Enhanced Rules**: Contextual decision guidelines
- **Conversation Awareness**: Reference to previous interactions

### 3. Tool Chaining for Complex Workflows

Automatically detects and executes multi-step workflows:

**Chain Types:**
- **Research + Memory**: Find information and store it
- **Context + Search**: Use previous context for new searches
- **Document + Web**: Combine internal and external information
- **Multi-Step Research**: Complex fact-finding missions

**Example Chain:**
```python
steps = [
    ChainStep(tool_name="web", query="Tesla stock price"),
    ChainStep(tool_name="memory", query="Remember Tesla info", depends_on=["web"])
]
```

### 4. Performance Monitoring

Comprehensive tracking of system performance:

**Routing Metrics:**
- Total routing decisions
- Tool usage distribution  
- Routing method success rates (LLM vs fallback)
- Context analysis statistics

**Tool Performance:**
- Execution times and success rates
- Error tracking and patterns
- Usage frequency and efficiency
- Average response times

### 5. Advanced Fallback Mechanisms

Multi-layer fallback system ensures reliability:

1. **Primary**: LLM-based intelligent routing
2. **Secondary**: Enhanced keyword-based routing with context
3. **Tertiary**: Traditional keyword matching
4. **Recovery**: Error handling and tool retry logic

## API Endpoints

### Monitoring Endpoints

- `GET /monitoring/routing` - Routing system metrics
- `GET /monitoring/tools` - Tool performance statistics  
- `GET /monitoring/system` - Comprehensive system metrics
- `POST /monitoring/reset` - Reset metrics (testing)

### Enhanced Chat Endpoint

The main chat endpoint now returns additional information:

```json
{
  "answer": "Response text",
  "tool_used": "web" | "chain(web → memory)",
  "tool_output": "Tool results",
  "execution_time": 1.23,
  "chain_execution": true|false,
  "chain_details": {
    "steps": 2,
    "tools": ["web", "memory"], 
    "success": true
  },
  "tool_error": null|"error message"
}
```

## Configuration

### Environment Variables

Standard AgentKit environment variables apply:
- `GOOGLE_API_KEY` - Required for LLM routing
- `TAVILY_API_KEY` - Optional for web search
- `MAX_FILE_SIZE` - File upload limits
- `CONVERSATION_HISTORY_LIMIT` - Context window size

### Routing Parameters

The enhanced router accepts additional parameters:

```python
await select_tool(
    message="User query",
    conversation_context="Previous conversation"
)
```

## Usage Patterns

### Simple Queries
Single tool execution with intelligent routing:
```
User: "What's the weather like?"
System: Routes to 'web' → Searches current weather
```

### Complex Workflows  
Automatic chain detection and execution:
```
User: "Find Tesla's latest news and remember the key points"
System: Detects chain → web(Tesla news) → memory(store results)
```

### Contextual Routing
Considers conversation history:
```
Previous: "I'm working on a Python project"
User: "Find the latest updates"
System: Routes to 'web' with Python context → Python-focused results
```

## Performance Characteristics

### Routing Speed
- **LLM Routing**: ~0.5-2.0 seconds (depends on model)
- **Fallback Routing**: ~0.001-0.01 seconds
- **Context Analysis**: ~0.001 seconds

### Tool Execution
- **Web Search**: 1-3 seconds (API dependent)
- **RAG Retrieval**: 0.1-0.5 seconds (local)
- **Memory Operations**: 0.01-0.1 seconds
- **Idle Responses**: ~0.5-1.5 seconds (LLM generation)

### Chain Execution
- **Detection**: ~0.5-2.0 seconds (LLM analysis)
- **Sequential Execution**: Sum of individual tool times
- **Parallel Execution**: Max of concurrent tool times

## Testing

Comprehensive test suite includes:

### Unit Tests
- Context analysis functionality
- Enhanced fallback routing
- Performance monitoring
- Tool chain detection

### Integration Tests
- End-to-end routing workflows
- Chain execution scenarios
- Error handling and recovery
- Performance metric collection

### Load Tests
- Concurrent routing requests
- Tool performance under load
- Memory usage optimization
- Response time consistency

## Error Handling

### Routing Failures
1. LLM routing timeout → Enhanced fallback
2. Enhanced fallback error → Traditional keywords
3. All routing fails → Default to 'idle'

### Tool Execution Failures
1. Primary tool fails → Error logged, graceful response
2. Chain step fails → Partial results returned
3. Critical failure → User-friendly error message

### Recovery Mechanisms
- Automatic retry for transient failures
- Fallback tool selection for unavailable tools
- Partial result presentation for chain failures
- Comprehensive error logging for debugging

## Future Enhancements

### Planned Features
- Machine learning-based routing optimization
- Dynamic tool priority adjustment
- Advanced parallel execution strategies
- Custom chain templates and workflows
- Real-time performance dashboards

### Extensibility Points
- Custom tool development hooks
- Plugin architecture for specialized routing
- External monitoring system integration
- Custom chain detection patterns

## Debugging and Troubleshooting

### Common Issues

**Poor Routing Decisions:**
- Check LLM availability and API keys
- Review routing prompt effectiveness
- Analyze context analysis results
- Monitor fallback usage patterns

**Slow Performance:**
- Monitor tool execution times
- Check LLM response latency
- Analyze chain complexity
- Review context processing overhead

**Chain Detection Issues:**
- Verify chain detection prompts
- Test with various query patterns  
- Monitor chain success rates
- Adjust detection sensitivity

### Monitoring and Alerts

Use the monitoring endpoints to track:
- Routing decision accuracy
- Tool performance trends
- Error rate increases
- Context analysis effectiveness

The enhanced routing architecture provides AgentKit with sophisticated intelligence for handling complex user queries while maintaining reliability, performance, and extensibility.