# Quick Start Guide

Get the Graph RAG API up and running in 5 minutes!

## Prerequisites

- Docker and Docker Compose installed
- API keys for:
  - LlamaParse
  - Google Gemini
  - Pinecone
  - Azure Storage

## Step 1: Configure Environment

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your API keys:
   ```env
   # Required - Add your keys here
   AZURE_STORAGE_CONNECTION_STRING=your_connection_string_here
   LLAMA_CLOUD_API_KEY=your_llama_api_key_here
   GOOGLE_API_KEY=your_google_api_key_here
   PINECONE_API_KEY=your_pinecone_api_key_here
   PINECONE_ENVIRONMENT=your_pinecone_environment
   NEO4J_PASSWORD=choose_a_secure_password
   ```

## Step 2: Start Services

Using Docker Compose (recommended):
```bash
docker-compose up -d
```

This will start:
- Graph RAG API on port 8000
- Neo4j on ports 7474 (HTTP) and 7687 (Bolt)

Check status:
```bash
docker-compose ps
```

View logs:
```bash
docker-compose logs -f api
```

## Step 3: Verify Installation

Check API health:
```bash
curl http://localhost:8000/health
```

Check Graph RAG health:
```bash
curl http://localhost:8000/api/v1/graph-rag/health
```

Access API documentation:
- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

Access Neo4j Browser:
- URL: http://localhost:7474
- Username: `neo4j`
- Password: (the one you set in `.env`)

## Step 4: Ingest Your First Document

Upload a document to Azure Blob Storage, then ingest it:

```bash
curl -X POST "http://localhost:8000/api/v1/graph-rag/ingest" \
  -H "Content-Type: application/json" \
  -d '{
    "file_url": "https://yourstorage.blob.core.windows.net/documents/sample.pdf",
    "metadata": {
      "title": "My First Document",
      "category": "test"
    }
  }'
```

Expected response:
```json
{
  "status": "success",
  "document_id": "abc123...",
  "file_name": "sample.pdf",
  "processing_time_seconds": 45.2,
  "chunks_created": 150,
  "images_extracted": 5,
  "entities_extracted": 87,
  "relationships_created": 234,
  "vectors_stored": 155
}
```

## Step 5: Query Your Documents

Query the system:

```bash
curl -X POST "http://localhost:8000/api/v1/graph-rag/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the main topics in the document?",
    "top_k": 5,
    "use_graph": true,
    "graph_depth": 2
  }'
```

## Example Python Client

```python
import requests

# Configuration
API_URL = "http://localhost:8000/api/v1/graph-rag"

# Ingest a document
def ingest_document(file_url, metadata=None):
    response = requests.post(
        f"{API_URL}/ingest",
        json={
            "file_url": file_url,
            "metadata": metadata or {}
        }
    )
    return response.json()

# Query the system
def query(query_text, top_k=10):
    response = requests.post(
        f"{API_URL}/query",
        json={
            "query": query_text,
            "top_k": top_k,
            "use_graph": True,
            "graph_depth": 2
        }
    )
    return response.json()

# Example usage
if __name__ == "__main__":
    # Ingest
    result = ingest_document(
        "https://yourstorage.blob.core.windows.net/documents/sample.pdf",
        {"category": "research", "author": "John Doe"}
    )
    print(f"Ingested: {result['document_id']}")

    # Query
    results = query("What are the main conclusions?")
    print(f"Found {results['num_results']} results")
    for r in results['results'][:3]:
        print(f"- Score: {r['score']:.3f}")
        print(f"  Text: {r['text'][:100]}...")
```

## Monitoring

### Check System Stats

```bash
curl http://localhost:8000/api/v1/graph-rag/stats
```

### View Neo4j Graph

1. Open http://localhost:7474
2. Login with your credentials
3. Run queries:
   ```cypher
   // View all documents
   MATCH (d:Document) RETURN d LIMIT 10

   // View entities
   MATCH (e:Entity) RETURN e LIMIT 20

   // View relationships
   MATCH (e1:Entity)-[r]->(e2:Entity)
   RETURN e1, r, e2 LIMIT 50
   ```

### View Pinecone Stats

```bash
curl http://localhost:8000/api/v1/graph-rag/stats | jq '.vector_store'
```

## Stopping Services

```bash
docker-compose down
```

To also remove volumes (warning: deletes all data):
```bash
docker-compose down -v
```

## Troubleshooting

### API not responding
```bash
# Check if container is running
docker-compose ps

# View logs
docker-compose logs api

# Restart services
docker-compose restart
```

### Neo4j connection error
```bash
# Check Neo4j status
docker-compose logs neo4j

# Verify credentials in .env
# Wait for Neo4j to fully start (can take 30-60 seconds)
```

### Out of memory
```bash
# Increase Neo4j memory in docker-compose.yml
NEO4J_dbms_memory_heap_max__size=4G
NEO4J_dbms_memory_pagecache_size=2G
```

## Next Steps

- Read the full [README.md](README.md)
- Explore the API docs at http://localhost:8000/api/docs
- Check out example use cases
- Integrate with your application

## Getting Help

- Check logs: `docker-compose logs -f`
- View API docs: http://localhost:8000/api/docs
- Open an issue on GitHub

## Production Deployment

For production:
1. Use environment-specific `.env` files
2. Set up proper secrets management
3. Configure SSL/TLS
4. Set up monitoring and logging
5. Use production-grade databases
6. Implement authentication and authorization
7. Set up backups for Neo4j data

Happy Graph RAG-ing! 🚀
