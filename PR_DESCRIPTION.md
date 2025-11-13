# Graph RAG Query API with Real-Time WebSocket Streaming

## 🎯 Overview

This PR introduces a production-ready **Graph RAG Query API** that combines semantic search with knowledge graph capabilities for enhanced document querying and retrieval. The API focuses on querying pre-ingested documents (ingestion handled by separate CRUD backend) with powerful real-time streaming capabilities.

## ✨ Key Features

### Core Query Capabilities
- **Semantic Search**: 768-dimensional embeddings using Google Gemini with cosine similarity
- **Knowledge Graph Integration**: Neo4j graph traversal for contextual understanding
- **Vector Store**: Fast similarity search using Pinecone
- **Hybrid Search**: Combines vector similarity with graph relationships for superior results

### Real-Time Communication
- **WebSocket API**: Streaming query execution with live results
- **Connection Management**: Industrial-grade concurrent connection handling
- **Topic Subscriptions**: Event-driven pub/sub architecture
- **Heartbeat Monitoring**: Automatic connection health tracking

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Graph RAG Query API                       │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐   │
│  │    Gemini    │   │   Pinecone   │   │    Neo4j     │   │
│  │  Embeddings  │   │   Vector     │   │  Knowledge   │   │
│  │  (768-dim)   │   │   Database   │   │    Graph     │   │
│  └──────────────┘   └──────────────┘   └──────────────┘   │
│         │                    │                    │          │
│         └────────────────────┼────────────────────┘          │
│                              ▼                                │
│                    ┌──────────────────┐                      │
│                    │   Query Engine   │                      │
│                    │  (Graph RAG)     │                      │
│                    └──────────────────┘                      │
│                              │                                │
│         ┌────────────────────┼────────────────────┐          │
│         ▼                    ▼                    ▼          │
│   ┌──────────┐      ┌──────────────┐      ┌──────────┐     │
│   │   HTTP   │      │   WebSocket  │      │  Hybrid  │     │
│   │   Query  │      │   Streaming  │      │  Search  │     │
│   └──────────┘      └──────────────┘      └──────────┘     │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## 📂 Project Structure

```
stealth/
├── app/
│   ├── api/v1/endpoints/
│   │   ├── graph_rag.py        # HTTP REST endpoints
│   │   ├── websocket.py        # WebSocket endpoints
│   │   └── user.py             # User endpoints
│   ├── services/
│   │   ├── azure_storage.py    # Azure Blob Storage client
│   │   ├── document_parser.py  # LlamaParse integration
│   │   ├── embeddings.py       # Gemini embeddings service
│   │   ├── vector_store.py     # Pinecone integration
│   │   ├── graph_store.py      # Neo4j integration
│   │   ├── graph_rag_query.py  # Query engine
│   │   └── graph_rag_ingestion.py # (For CRUD backend reference)
│   ├── websocket/
│   │   ├── connection_manager.py # Connection lifecycle management
│   │   ├── schemas.py           # Message protocols
│   │   └── handlers.py          # Message processing
│   ├── models/
│   │   └── graph_rag.py        # Pydantic schemas
│   └── config.py               # Configuration management
├── examples/
│   ├── websocket_client.py     # Python WebSocket client
│   ├── websocket_client.html   # Interactive web client
│   ├── query_system.py         # Query examples
│   └── complete_workflow.py    # Full workflow demo
├── WEBSOCKET.md               # WebSocket documentation
├── README.md                   # Complete documentation
└── docker-compose.yml          # Docker deployment
```

## 🔌 API Endpoints

### HTTP REST API

#### Query Documents
```http
POST /api/v1/graph-rag/query
```
Execute semantic search with graph enhancement.

**Request:**
```json
{
  "query": "What are the main conclusions?",
  "top_k": 10,
  "use_graph": true,
  "graph_depth": 2
}
```

**Response:**
```json
{
  "query": "What are the main conclusions?",
  "results": [...],
  "num_results": 10,
  "num_entities": 15,
  "graph_enhanced": true,
  "context_chunks": [...],
  "graph_context": {...}
}
```

#### Hybrid Search
```http
POST /api/v1/graph-rag/hybrid-search
```
Combine vector similarity with entity-based search.

#### Health Check
```http
GET /api/v1/graph-rag/health
```

#### System Statistics
```http
GET /api/v1/graph-rag/stats
```

### WebSocket API

#### Connection
```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/ws?client_id=my-client');
```

#### Streaming Query Execution
```javascript
// Send query
ws.send(JSON.stringify({
    type: 'query_request',
    request_id: 'req-123',
    query: 'What are the findings?',
    top_k: 10,
    stream_results: true
}));

// Receive results as they arrive
ws.onmessage = (event) => {
    const msg = JSON.parse(event.data);
    if (msg.type === 'query_chunk') {
        console.log('Result:', msg.result);
    }
};
```

#### WebSocket Management Endpoints
- `GET /api/v1/ws/connections` - View active connections
- `GET /api/v1/ws/health` - WebSocket health check
- `POST /api/v1/ws/broadcast` - Broadcast to all clients
- `POST /api/v1/ws/topics/{topic}/broadcast` - Topic broadcasts

## 🚀 Key Components

### 1. Query Engine (`graph_rag_query.py`)
- Semantic similarity search using Gemini embeddings
- Graph traversal for contextual enhancement
- Hybrid search combining multiple approaches
- Entity extraction and relationship mapping
- Result ranking and reranking

### 2. WebSocket Infrastructure
- **Connection Manager**: Thread-safe multi-client support
- **Message Protocols**: Type-safe Pydantic schemas
- **Handlers**: Async message processing
- **Broadcasting**: All clients or topic-specific
- **Health Monitoring**: Automatic heartbeats

### 3. Vector Store Service (`vector_store.py`)
- Pinecone integration with 768-dimensional vectors
- Cosine similarity search
- Namespace management
- Batch operations
- Connection pooling

### 4. Graph Store Service (`graph_store.py`)
- Neo4j knowledge graph queries
- Entity and relationship traversal
- Subgraph extraction
- Cypher query execution
- Connection management

### 5. Embeddings Service (`embeddings.py`)
- Google Gemini text-embedding-004 model
- 768-dimensional embeddings
- Batch processing
- Query vs document embeddings
- Error handling and retries

## 📊 Tech Stack

- **FastAPI**: Modern async web framework
- **WebSocket**: Real-time bidirectional communication
- **Google Gemini**: State-of-the-art embeddings (768-dim)
- **Pinecone**: Managed vector database (cosine similarity)
- **Neo4j**: Graph database for knowledge representation
- **LangChain**: LLM orchestration framework
- **Pydantic**: Data validation and settings management
- **Docker**: Containerization and deployment

## 🎨 Industrial Features

### Connection Management
- ✅ Multi-client concurrent support
- ✅ Connection lifecycle tracking
- ✅ Automatic reconnection support
- ✅ Graceful shutdown handling
- ✅ Resource cleanup

### Error Handling
- ✅ Comprehensive exception catching
- ✅ Detailed error messages
- ✅ Fallback mechanisms
- ✅ Retry logic with exponential backoff
- ✅ Circuit breaker patterns

### Performance
- ✅ Async/await throughout
- ✅ Connection pooling
- ✅ Batch operations
- ✅ Streaming responses
- ✅ Query result caching

### Monitoring
- ✅ Health checks for all services
- ✅ Connection statistics
- ✅ Message tracking
- ✅ Performance metrics
- ✅ Comprehensive logging

### Security
- ✅ Input validation
- ✅ Type safety with Pydantic
- ✅ Error message sanitization
- ✅ Connection limits
- ✅ Rate limiting ready

## 📚 Documentation

### Included Documentation
- **README.md**: Complete API documentation with examples
- **WEBSOCKET.md**: Comprehensive WebSocket API reference
- **QUICKSTART.md**: 5-minute setup guide
- **examples/**: Working code examples for all features

### Code Examples
- **Python WebSocket Client**: Full-featured async client
- **Web Client**: Interactive HTML/JavaScript client with UI
- **Query Examples**: Various query patterns and use cases
- **Complete Workflow**: End-to-end usage demonstration

## 🧪 Examples Provided

### Python WebSocket Client (`examples/websocket_client.py`)
```python
from websocket_client import GraphRAGWebSocketClient

client = GraphRAGWebSocketClient()
await client.connect()

# Stream query results
await client.query("What are the key findings?", top_k=10)
```

### Web Client (`examples/websocket_client.html`)
Beautiful, responsive web interface with:
- Real-time connection status
- Interactive query interface
- Live result streaming
- Progress visualization
- Message history

### Query Examples (`examples/query_system.py`)
```python
# Standard query
result = client.query("What are the conclusions?", top_k=10)

# Hybrid search
result = client.hybrid_search("machine learning", filters={"category": "research"})
```

## 🐳 Deployment

### Docker Compose
```bash
docker-compose up -d
```

Includes:
- FastAPI application (port 8000)
- Neo4j database (ports 7474, 7687)
- Health checks
- Auto-restart
- Volume persistence

### Environment Configuration
```env
# Google Gemini
GOOGLE_API_KEY=your_api_key

# Pinecone
PINECONE_API_KEY=your_api_key
PINECONE_INDEX_NAME=graph-rag-embeddings

# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_PASSWORD=your_password
```

## 🔄 Workflow Integration

This API is designed to work with a separate CRUD backend:

```
CRUD Backend (Ingestion)
      ↓
Documents → Pinecone + Neo4j
      ↓
Graph RAG Query API (This PR)
      ↓
Query Results → Users
```

## ✅ Testing

### Quick Start
1. Start services: `docker-compose up -d`
2. Run examples: `python examples/query_system.py`
3. Try web client: Open `examples/websocket_client.html`
4. Check health: `curl http://localhost:8000/api/v1/graph-rag/health`

### API Documentation
- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

## 📈 Performance Characteristics

- **Query Latency**: Sub-second for most queries
- **Concurrent Connections**: Hundreds of WebSocket connections
- **Throughput**: Async processing with connection pooling
- **Scalability**: Horizontal scaling ready
- **Memory**: Efficient streaming for large result sets

## 🔐 Security Considerations

- Input validation using Pydantic schemas
- Type safety throughout
- Error message sanitization
- Connection limits configurable
- Ready for authentication/authorization layer
- WSS (WebSocket Secure) support for production

## 🎯 Use Cases

- **Document Q&A Systems**: Semantic search with context
- **Research Assistants**: Graph-enhanced retrieval
- **Knowledge Base Querying**: Combined vector + graph search
- **Real-Time Dashboards**: Streaming results via WebSocket
- **Multi-User Applications**: Concurrent query support
- **Analytics Platforms**: Hybrid search capabilities

## 📝 Design Decisions

### Why Separate Ingestion?
- **Separation of Concerns**: Ingestion is a different workflow
- **Scalability**: Different scaling requirements
- **Reliability**: Query API remains stable during ingestion
- **Simplicity**: Focused API with clear responsibility

### Why WebSocket?
- **Real-Time Updates**: Stream results as they arrive
- **Better UX**: Progressive result loading
- **Efficient**: Single connection for multiple operations
- **Flexible**: Supports various messaging patterns

### Why Graph + Vector?
- **Best of Both Worlds**: Semantic + structural understanding
- **Context**: Graph provides relationship context
- **Accuracy**: Hybrid approach improves relevance
- **Flexibility**: Can use either or both

## 🚦 Migration Path

If upgrading from a previous version:
1. Documents must be pre-ingested via CRUD backend
2. Update client code to use query-only endpoints
3. WebSocket clients need to remove ingestion message types
4. Environment variables remain the same

## 📞 Support

- **API Docs**: http://localhost:8000/api/docs
- **WebSocket Docs**: See WEBSOCKET.md
- **Examples**: Check examples/ directory
- **Issues**: Open GitHub issue for bugs/features

## 🎉 Summary

This PR delivers a **production-ready Graph RAG Query API** with:
- ✅ Powerful semantic + graph search
- ✅ Real-time WebSocket streaming
- ✅ Industrial-grade architecture
- ✅ Comprehensive documentation
- ✅ Working examples
- ✅ Docker deployment
- ✅ Health monitoring
- ✅ Scalable design

The API is ready for integration with your CRUD backend and can handle production workloads with proper configuration.

---

## 🔍 Review Checklist

- [ ] Code follows Python best practices
- [ ] All endpoints documented
- [ ] WebSocket protocol tested
- [ ] Error handling comprehensive
- [ ] Examples work correctly
- [ ] Docker setup functional
- [ ] Documentation complete
- [ ] Type hints throughout
- [ ] Logging appropriate
- [ ] Security considerations addressed

## 📎 Related

- Ingestion handled by separate CRUD backend
- Complements existing document management system
- Ready for horizontal scaling with load balancer
