# Advanced RAG Features Documentation

## Overview

AgentKit now includes advanced RAG (Retrieval-Augmented Generation) capabilities that enhance search quality, provide source attribution, and enable hybrid search combining multiple information sources.

## Key Features

### 1. Semantic Search with Relevance Scoring

**What it is:** Enhanced vector search that calculates relevance scores for retrieved documents.

**How it works:**
- Converts distance metrics to relevance scores (0-1 scale)
- Higher scores indicate better semantic matches
- Helps prioritize the most relevant information

**Technical Implementation:**
```python
# In rag/store.py
relevance_score = 1.0 / (1.0 + distance)
```

**Benefits:**
- More accurate document retrieval
- Better ranking of search results
- Improved context for LLM responses

### 2. Citation Support and Source Attribution

**What it is:** Automatic citation generation showing the source of retrieved information.

**Features:**
- Document name and chunk number
- Relevance percentage for each source
- Structured citation format
- Clear source attribution in responses

**Example Output:**
```
**Source [1]: technical_manual.pdf** (chunk #5, relevance: 87.3%)
[Document content...]

---
**Citations:**
[1] technical_manual.pdf, chunk 5 (relevance: 87.30%)
[2] user_guide.pdf, chunk 12 (relevance: 79.45%)
```

**Benefits:**
- Transparency in information sources
- Easy verification of facts
- Better trust in AI responses
- Academic-style referencing

### 3. Hybrid Search

**What it is:** Advanced search mode that combines web search and document retrieval for comprehensive answers.

**How it works:**
- Executes web and document searches in parallel
- Combines results from both sources
- Provides clear attribution for each source type
- Optimized for efficiency with async operations

**Example Use Cases:**
- "What's the latest on AI regulations and how does it affect our policy document?"
- "Compare current market trends with our internal projections"
- "Find recent news about Python and check our coding standards"

**Output Format:**
```
═══════════════════════════════════════
📚 FROM YOUR DOCUMENTS:
═══════════════════════════════════════
[Document search results with citations]

═══════════════════════════════════════
🌐 FROM WEB SEARCH:
═══════════════════════════════════════
[Web search results with URLs]

═══════════════════════════════════════
💡 HYBRID SEARCH SUMMARY:
═══════════════════════════════════════
[Summary of combined approach]
```

**Benefits:**
- Most comprehensive answers
- Combines internal knowledge with current information
- Clear source separation
- Efficient parallel execution

### 4. Advanced Query Understanding

**What it is:** Query preprocessing that enhances semantic matching.

**Features:**
- Filler word removal (please, could, would, etc.)
- Query optimization for better embeddings
- Context preservation for important terms
- Intelligent enhancement that preserves intent

**Example:**
```
Original: "Could you please tell me about the architecture?"
Enhanced: "architecture"
```

**Benefits:**
- Better semantic matches
- More relevant results
- Reduced noise in queries
- Improved retrieval accuracy

### 5. Configurable Search Modes

**What it is:** User-selectable search preferences that control how information is retrieved.

**Available Modes:**

#### Auto Mode (Default)
- **Icon:** 🔍 Search
- **Description:** Automatically selects the best search method based on query
- **When to use:** General queries, letting AI decide
- **How it works:** LLM-powered routing analyzes query and selects optimal tool

#### Web Mode
- **Icon:** 🌐 Globe
- **Description:** Search current web information only
- **When to use:** Current events, latest news, real-time data
- **Example queries:** "What's the weather today?", "Latest AI news"

#### Documents Mode
- **Icon:** 📄 FileText
- **Description:** Search uploaded documents only
- **When to use:** Internal documentation, uploaded knowledge base
- **Example queries:** "What's in our policy document?", "Explain the architecture from the manual"

#### Hybrid Mode
- **Icon:** ⚡ Zap
- **Description:** Combine web and document search
- **When to use:** Comprehensive research, comparing internal and external information
- **Example queries:** "How do current AI trends align with our strategy?", "Latest Python features vs our coding standards"

**UI Implementation:**
- Dropdown selector in chat header
- Tooltip with mode descriptions
- Persistent preference per session
- Visual indicators for active mode

## Technical Architecture

### Backend Components

#### 1. Enhanced RAG Store (`rag/store.py`)
```python
def query(namespace: str, query_text: str, k: int = 5) -> List[Dict]:
    """
    Query with relevance scoring:
    - Calculates semantic similarity
    - Returns scored results
    - Enables better ranking
    """
```

#### 2. Advanced Tools (`agent/tools.py`)
```python
# Query enhancement
def _enhance_query(query: str) -> str:
    """Preprocesses queries for better matching"""

# Enhanced RAG with citations
def _retrieve_context(query: str, namespace: str, k: int) -> str:
    """Retrieves with citations and relevance scores"""

# Hybrid search
async def _hybrid_search(query: str, namespace: str) -> str:
    """Combines web and document search"""
```

#### 3. Agent Integration (`agent/agent.py`)
```python
async def run_agent_with_history(..., search_mode: str = "auto"):
    """
    Supports search mode override:
    - 'auto': LLM routing
    - 'web': Force web search
    - 'documents': Force RAG search
    - 'hybrid': Force hybrid search
    """
```

### Frontend Components

#### 1. Search Mode Selector (`SearchModeSelector.tsx`)
- Visual mode selector
- Tooltips with descriptions
- Icon-based UI
- Responsive design

#### 2. Enhanced Chat State (`chat.ts`)
```typescript
interface ChatState {
    searchMode: 'auto' | 'web' | 'documents' | 'hybrid';
    // ... other properties
}

interface Citation {
    source: string;
    chunk?: number;
    relevance?: number;
    type: 'document' | 'web';
}
```

## Usage Examples

### Example 1: Document Search with Citations

**User Query:** "What is the authentication process?"

**Response:**
```
Based on your documents, the authentication process involves:

**Source [1]: security_guide.pdf** (chunk #3, relevance: 92.1%)
The authentication process uses OAuth 2.0 with JWT tokens...

**Source [2]: api_documentation.pdf** (chunk #7, relevance: 85.4%)
All API requests must include the Authorization header...

---
**Citations:**
[1] security_guide.pdf, chunk 3 (relevance: 92.10%)
[2] api_documentation.pdf, chunk 7 (relevance: 85.40%)
```

### Example 2: Hybrid Search

**User Query:** "Latest Python features and our coding standards"

**Response:**
```
═══════════════════════════════════════
📚 FROM YOUR DOCUMENTS:
═══════════════════════════════════════
**Source [1]: coding_standards.pdf** (chunk #2, relevance: 88.7%)
Our Python coding standards require...

═══════════════════════════════════════
🌐 FROM WEB SEARCH:
═══════════════════════════════════════
1. **Python 3.12 Released with New Features**
   Python 3.12 introduces improved performance...
   Source: https://python.org/news

═══════════════════════════════════════
💡 HYBRID SEARCH SUMMARY:
═══════════════════════════════════════
This response combines information from both your uploaded 
documents and current web sources to provide comprehensive, 
up-to-date answers with full source attribution.
```

### Example 3: Web-Only Search

**User Query (Web Mode):** "Current weather in San Francisco"

**Response:**
```
Web search results for 'Current weather in San Francisco':

1. **San Francisco Weather - Current Conditions**
   Currently 65°F with partly cloudy skies...
   Source: https://weather.com/weather/today/l/SF
```

### Example 4: Auto Mode (LLM Routing)

**User Query:** "Tell me about our company policy"

**Agent Behavior:**
- Analyzes query semantically
- Detects "our company policy" indicates internal document
- Automatically routes to RAG tool
- Returns document-based response with citations

## Configuration

### Environment Variables

No additional environment variables needed. The features work with existing configuration:

```bash
GOOGLE_API_KEY=your_google_api_key  # For LLM routing
TAVILY_API_KEY=your_tavily_api_key  # For web search (optional)
```

### Frontend Configuration

Search mode preference is stored in session state:

```typescript
const [chatState, setChatState] = useState<ChatState>({
    searchMode: 'auto',  // Default to auto mode
    // ... other state
});
```

### Backend Configuration

Configurable parameters in `agent/tools.py`:

```python
# Number of results to retrieve
k = 5  # Default, can be adjusted per query

# Query enhancement
_enhance_query(query)  # Automatically applied
```

## Performance Characteristics

### Semantic Search
- **Speed:** ~0.1-0.5 seconds (local ChromaDB)
- **Accuracy:** Improved with relevance scoring
- **Scalability:** Handles thousands of documents

### Hybrid Search
- **Speed:** ~1-3 seconds (parallel execution)
- **Combines:** Web (1-3s) + Documents (0.1-0.5s)
- **Optimization:** Async/await for efficiency

### Query Understanding
- **Speed:** ~0.001 seconds (preprocessing)
- **Impact:** Minimal overhead
- **Benefit:** Significant accuracy improvement

## Best Practices

### When to Use Each Mode

1. **Auto Mode**
   - Default for most queries
   - Trust LLM to route correctly
   - Best for mixed conversations

2. **Web Mode**
   - Time-sensitive queries
   - Current events
   - Latest information needs

3. **Documents Mode**
   - Internal knowledge
   - Uploaded documentation
   - Company-specific information

4. **Hybrid Mode**
   - Research tasks
   - Comprehensive analysis
   - Comparing internal/external info

### Citation Best Practices

- Always verify citations when accuracy is critical
- Use chunk numbers to locate exact source locations
- Check relevance scores for confidence levels
- Higher relevance (>80%) indicates strong matches

### Query Optimization Tips

- Be specific in queries for better results
- Use natural language
- Include context when helpful
- Hybrid mode for comprehensive needs

## Troubleshooting

### Issue: Low Relevance Scores

**Symptoms:** All results show relevance < 50%

**Solutions:**
1. Rephrase query with more specific terms
2. Ensure documents are properly ingested
3. Try query expansion (add related terms)
4. Check if information exists in documents

### Issue: Missing Citations

**Symptoms:** Response doesn't include citation section

**Solutions:**
1. Verify RAG tool is being used
2. Check if documents exist in namespace
3. Ensure embeddings were created successfully
4. Try increasing k parameter for more results

### Issue: Hybrid Search Takes Too Long

**Symptoms:** Response time > 5 seconds

**Solutions:**
1. Check network connectivity for web search
2. Verify Tavily API is responding
3. Consider using Documents mode instead
4. Check server logs for bottlenecks

## Future Enhancements

Potential improvements for future versions:

1. **Multi-Modal RAG**
   - Image and diagram search
   - Table extraction and search
   - Code snippet retrieval

2. **Advanced Ranking**
   - BM25 + semantic hybrid ranking
   - Learning-to-rank algorithms
   - User feedback integration

3. **Citation Management**
   - Export citations in BibTeX format
   - Bibliography generation
   - Citation graphs and relationships

4. **Query Intelligence**
   - Query suggestion
   - Spelling correction
   - Synonym expansion with thesaurus

5. **Performance Optimization**
   - Result caching
   - Incremental indexing
   - Distributed vector search

## API Reference

### RAG Query Endpoint

```python
POST /chat
Form Data:
  - message: str (query text)
  - model: str (LLM model)
  - namespace: str (document namespace)
  - search_mode: str ('auto' | 'web' | 'documents' | 'hybrid')
  
Response:
  - answer: str (formatted response)
  - tool_used: str (selected tool)
  - citations: List[Citation] (source references)
```

### Tools API

```python
# Direct tool access (internal use)
from agent.tools import _retrieve_context, _hybrid_search

# RAG with citations
result = _retrieve_context(query, namespace, k=5)

# Hybrid search
result = await _hybrid_search(query, namespace)
```

## Conclusion

These advanced RAG features provide:
- ✅ Better search accuracy with semantic understanding
- ✅ Full source attribution and citations
- ✅ Flexible search modes for different needs
- ✅ Hybrid approach combining multiple sources
- ✅ Enhanced user control and transparency

For more information, see the main README.md and ROUTING_ARCHITECTURE.md documentation.
