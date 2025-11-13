# WebSocket API Documentation

Real-time communication interface for Graph RAG API with streaming support for document ingestion and query execution.

## Overview

The WebSocket API provides bidirectional, real-time communication for:
- **Streaming document ingestion** with live progress updates
- **Streaming query execution** with results delivered as they arrive
- **Topic-based subscriptions** for event notifications
- **Connection management** with automatic heartbeats
- **Concurrent operations** support

## Connection

### WebSocket URL

```
ws://localhost:8000/api/v1/ws
```

### Connection Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `client_id` | string | No | Unique client identifier (auto-generated if not provided) |
| `client_name` | string | No | Human-readable client name |

### Example Connection

**JavaScript:**
```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/ws?client_id=my-client&client_name=MyApp');

ws.onopen = () => {
    console.log('Connected!');
};

ws.onmessage = (event) => {
    const message = JSON.parse(event.data);
    console.log('Received:', message);
};
```

**Python:**
```python
import asyncio
import websockets
import json

async def connect():
    uri = "ws://localhost:8000/api/v1/ws?client_id=my-client"
    async with websockets.connect(uri) as websocket:
        # Receive welcome message
        welcome = await websocket.recv()
        print(f"Connected: {welcome}")

        # Send message
        await websocket.send(json.dumps({
            "type": "ping"
        }))

        # Receive response
        response = await websocket.recv()
        print(f"Response: {response}")

asyncio.run(connect())
```

## Message Protocol

All messages are JSON-formatted with a standard structure:

```json
{
    "type": "message_type",
    "timestamp": "2025-11-13T10:30:00.000Z",
    "request_id": "optional-request-id",
    "...additional fields..."
}
```

### Message Types

#### Client → Server

| Type | Description |
|------|-------------|
| `subscribe` | Subscribe to a topic |
| `unsubscribe` | Unsubscribe from a topic |
| `ingest_request` | Request document ingestion |
| `query_request` | Execute a query |
| `ping` | Heartbeat ping |

#### Server → Client

| Type | Description |
|------|-------------|
| `connected` | Connection established |
| `pong` | Heartbeat response |
| `error` | Error occurred |
| `subscribed` | Subscription confirmed |
| `unsubscribed` | Unsubscription confirmed |
| `ingestion_started` | Document ingestion started |
| `ingestion_progress` | Progress update |
| `ingestion_completed` | Ingestion completed |
| `ingestion_failed` | Ingestion failed |
| `query_started` | Query execution started |
| `query_chunk` | Query result chunk |
| `query_completed` | Query completed |
| `query_failed` | Query failed |
| `status_update` | General status update |

## Operations

### 1. Document Ingestion with Streaming Progress

Request document ingestion and receive real-time progress updates.

**Request:**
```json
{
    "type": "ingest_request",
    "request_id": "req-123",
    "file_url": "https://storage.blob.core.windows.net/docs/sample.pdf",
    "metadata": {
        "title": "Sample Document",
        "author": "John Doe",
        "category": "research"
    },
    "stream_progress": true
}
```

**Response Flow:**

1. **Started:**
```json
{
    "type": "ingestion_started",
    "request_id": "req-123",
    "document_id": "abc123...",
    "file_name": "sample.pdf",
    "message": "Document ingestion started",
    "timestamp": "2025-11-13T10:30:00.000Z"
}
```

2. **Progress Updates:**
```json
{
    "type": "ingestion_progress",
    "request_id": "req-123",
    "document_id": "abc123...",
    "stage": "parsing",
    "progress": 30.0,
    "message": "Parsing document with LlamaParse",
    "details": {},
    "timestamp": "2025-11-13T10:30:05.000Z"
}
```

Stages:
- `downloading` (10%) - Downloading from Azure Blob Storage
- `parsing` (30%) - Parsing with LlamaParse
- `entities` (50%) - Extracting entities and relationships
- `embeddings` (70%) - Generating embeddings
- `storing` (85%) - Storing vectors in Pinecone
- `graph` (95%) - Building knowledge graph in Neo4j

3. **Completed:**
```json
{
    "type": "ingestion_completed",
    "request_id": "req-123",
    "document_id": "abc123...",
    "file_name": "sample.pdf",
    "processing_time_seconds": 45.2,
    "chunks_created": 150,
    "images_extracted": 5,
    "entities_extracted": 87,
    "relationships_created": 234,
    "vectors_stored": 155,
    "message": "Document ingestion completed successfully",
    "timestamp": "2025-11-13T10:31:00.000Z"
}
```

4. **Error (if occurs):**
```json
{
    "type": "ingestion_failed",
    "request_id": "req-123",
    "document_id": "abc123...",
    "error": "Failed to download document",
    "details": {
        "file_url": "https://..."
    },
    "timestamp": "2025-11-13T10:30:30.000Z"
}
```

### 2. Query Execution with Streaming Results

Execute queries and receive results as they arrive.

**Request:**
```json
{
    "type": "query_request",
    "request_id": "req-456",
    "query": "What are the main conclusions?",
    "top_k": 10,
    "use_graph": true,
    "stream_results": true
}
```

**Response Flow:**

1. **Started:**
```json
{
    "type": "query_started",
    "request_id": "req-456",
    "query": "What are the main conclusions?",
    "message": "Query execution started",
    "timestamp": "2025-11-13T10:32:00.000Z"
}
```

2. **Result Chunks:**
```json
{
    "type": "query_chunk",
    "request_id": "req-456",
    "chunk_index": 0,
    "result": {
        "id": "doc1_chunk_5",
        "score": 0.9234,
        "text": "The main conclusions indicate that...",
        "doc_id": "doc1",
        "type": "text",
        "graph_enhanced": true,
        "metadata": {}
    },
    "is_final": false,
    "timestamp": "2025-11-13T10:32:01.000Z"
}
```

3. **Completed:**
```json
{
    "type": "query_completed",
    "request_id": "req-456",
    "query": "What are the main conclusions?",
    "total_results": 10,
    "num_entities": 15,
    "graph_enhanced": true,
    "message": "Query completed successfully",
    "summary": {
        "context_chunks": 10,
        "graph_context_available": true
    },
    "timestamp": "2025-11-13T10:32:05.000Z"
}
```

### 3. Topic Subscriptions

Subscribe to topics for event notifications.

**Subscribe:**
```json
{
    "type": "subscribe",
    "topic": "system_updates"
}
```

**Response:**
```json
{
    "type": "status_update",
    "status": "subscribed",
    "message": "Subscribed to topic: system_updates",
    "topic": "system_updates",
    "timestamp": "2025-11-13T10:33:00.000Z"
}
```

**Unsubscribe:**
```json
{
    "type": "unsubscribe",
    "topic": "system_updates"
}
```

### 4. Heartbeat

Keep connection alive with ping/pong.

**Request:**
```json
{
    "type": "ping",
    "timestamp": "2025-11-13T10:34:00.000Z"
}
```

**Response:**
```json
{
    "type": "pong",
    "timestamp": "2025-11-13T10:34:00.001Z"
}
```

## Error Handling

Errors are sent with detailed information:

```json
{
    "type": "error",
    "error": "Invalid message format",
    "details": {
        "received": {...}
    },
    "timestamp": "2025-11-13T10:35:00.000Z",
    "request_id": "req-789"
}
```

Common error types:
- `Invalid message format` - Malformed JSON or missing required fields
- `Unsupported message type` - Unknown message type
- `Connection error` - WebSocket connection issues
- `Internal server error` - Server-side processing errors

## Management Endpoints

REST endpoints for WebSocket management (requires HTTP connection):

### Get Active Connections

```http
GET /api/v1/ws/connections
```

**Response:**
```json
{
    "active_connections": 5,
    "topics": 3,
    "total_messages_sent": 1250,
    "total_messages_received": 450,
    "connections": [
        {
            "connection_id": "client-123",
            "state": "connected",
            "connected_at": "2025-11-13T10:00:00.000Z",
            "last_activity": "2025-11-13T10:35:00.000Z",
            "messages_sent": 50,
            "messages_received": 10,
            "subscriptions": ["system_updates"],
            "client_info": {
                "client_name": "MyApp",
                "user_agent": "..."
            }
        }
    ]
}
```

### Get Connection Info

```http
GET /api/v1/ws/connections/{connection_id}
```

### Broadcast Message

```http
POST /api/v1/ws/broadcast
Content-Type: application/json

{
    "type": "status_update",
    "message": "System maintenance in 5 minutes"
}
```

### Broadcast to Topic

```http
POST /api/v1/ws/topics/{topic}/broadcast
Content-Type: application/json

{
    "type": "status_update",
    "message": "New document available"
}
```

### Get Topics

```http
GET /api/v1/ws/topics
```

### Health Check

```http
GET /api/v1/ws/health
```

## Client Examples

### Python Client

See `examples/websocket_client.py` for a complete Python client implementation.

```bash
python examples/websocket_client.py
```

### Web Browser Client

See `examples/websocket_client.html` for an interactive web-based client.

```bash
# Open in browser
open examples/websocket_client.html
```

### JavaScript/TypeScript

```typescript
class GraphRAGClient {
    private ws: WebSocket;

    constructor(url: string) {
        this.ws = new WebSocket(url);
        this.setupHandlers();
    }

    private setupHandlers() {
        this.ws.onopen = () => {
            console.log('Connected');
        };

        this.ws.onmessage = (event) => {
            const message = JSON.parse(event.data);
            this.handleMessage(message);
        };
    }

    async ingestDocument(fileUrl: string, metadata: any) {
        const requestId = this.generateRequestId();

        this.ws.send(JSON.stringify({
            type: 'ingest_request',
            request_id: requestId,
            file_url: fileUrl,
            metadata: metadata,
            stream_progress: true
        }));

        return requestId;
    }

    async query(query: string, topK: number = 10) {
        const requestId = this.generateRequestId();

        this.ws.send(JSON.stringify({
            type: 'query_request',
            request_id: requestId,
            query: query,
            top_k: topK,
            use_graph: true,
            stream_results: true
        }));

        return requestId;
    }

    private generateRequestId(): string {
        return `req-${Date.now()}-${Math.random()}`;
    }

    private handleMessage(message: any) {
        switch (message.type) {
            case 'ingestion_progress':
                console.log(`Progress: ${message.progress}%`);
                break;
            case 'query_chunk':
                console.log('Result:', message.result);
                break;
            // ... handle other message types
        }
    }
}
```

## Best Practices

### 1. Connection Management

- Implement automatic reconnection on disconnect
- Handle connection timeouts gracefully
- Use unique `request_id` for tracking requests
- Close connections properly when done

### 2. Message Handling

- Validate all incoming messages
- Handle all message types appropriately
- Log errors for debugging
- Implement message queuing for high throughput

### 3. Error Recovery

- Retry failed operations with exponential backoff
- Handle partial failures in streaming operations
- Provide user feedback on errors
- Implement circuit breakers for repeated failures

### 4. Performance

- Process messages asynchronously
- Use connection pooling for multiple clients
- Batch operations when possible
- Monitor connection health

### 5. Security

- Validate all user inputs
- Implement authentication/authorization
- Use WSS (WebSocket Secure) in production
- Rate limit connections and messages

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Client Application                    │
└────────────────────┬────────────────────────────────────┘
                     │ WebSocket
                     ▼
┌─────────────────────────────────────────────────────────┐
│              WebSocket Endpoint (/ws)                    │
│                                                           │
│  ┌────────────────────────────────────────────────────┐ │
│  │          Connection Manager                         │ │
│  │  • Connection lifecycle                             │ │
│  │  • Message routing                                  │ │
│  │  • Topic subscriptions                              │ │
│  │  • Heartbeat monitoring                             │ │
│  └────────────────────────────────────────────────────┘ │
│                        │                                  │
│  ┌────────────────────┼────────────────────────┐        │
│  │                    │                         │        │
│  ▼                    ▼                         ▼        │
│ ┌──────────┐   ┌──────────┐           ┌──────────┐     │
│ │Ingestion │   │  Query   │           │  Topic   │     │
│ │ Handler  │   │ Handler  │           │ Manager  │     │
│ └──────────┘   └──────────┘           └──────────┘     │
└─────────────────────────────────────────────────────────┘
                     │         │                │
        ┌────────────┘         │                └──────────┐
        ▼                      ▼                            ▼
┌──────────────┐    ┌──────────────┐           ┌──────────────┐
│  Ingestion   │    │    Query     │           │  Broadcast   │
│   Pipeline   │    │   Engine     │           │   Service    │
└──────────────┘    └──────────────┘           └──────────────┘
```

## Monitoring

Monitor WebSocket health and performance:

### Metrics

- Active connections count
- Messages sent/received per second
- Average message processing time
- Error rate
- Connection duration

### Health Check

```http
GET /api/v1/ws/health
```

Returns:
- Connection count
- Total messages processed
- Service status

## Troubleshooting

### Connection Issues

**Problem:** Cannot connect to WebSocket

**Solutions:**
- Verify server is running
- Check WebSocket URL and port
- Ensure firewall allows WebSocket connections
- Check for proxy/load balancer WebSocket support

### Message Not Received

**Problem:** Sent message but no response

**Solutions:**
- Check message format (must be valid JSON)
- Verify message type is supported
- Check server logs for errors
- Ensure connection is still active

### Progress Updates Stop

**Problem:** Ingestion progress stops updating

**Solutions:**
- Check for errors in ingestion
- Verify connection is still alive
- Check server resources (CPU, memory)
- Review server logs for issues

### High Latency

**Problem:** Slow message delivery

**Solutions:**
- Check network latency
- Monitor server load
- Review concurrent operations
- Consider connection pooling

## Production Considerations

### Security

- Use `wss://` (WebSocket Secure) in production
- Implement authentication (tokens, API keys)
- Validate and sanitize all inputs
- Implement rate limiting
- Use CORS appropriately

### Scalability

- Implement horizontal scaling with load balancers
- Use Redis for shared state across instances
- Implement connection limits per client
- Monitor and auto-scale based on connections

### Reliability

- Implement automatic reconnection
- Handle network failures gracefully
- Use message acknowledgments
- Implement idempotency for operations
- Log all errors and anomalies

## Support

- API Documentation: http://localhost:8000/api/docs
- WebSocket Health: http://localhost:8000/api/v1/ws/health
- Main README: [README.md](README.md)
- Examples: [examples/](examples/)
