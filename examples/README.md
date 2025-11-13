# Graph RAG API Examples

This directory contains example scripts demonstrating how to use the Graph RAG API.

## Prerequisites

1. API server running at `http://localhost:8000`
2. Python 3.10+ with `requests` library installed:
   ```bash
   pip install requests
   ```

## Examples

### 1. Ingest Document (`ingest_document.py`)

Demonstrates how to ingest a document from Azure Blob Storage into the Graph RAG system.

**Usage:**
```bash
# Default example
python examples/ingest_document.py

# With custom URL
python examples/ingest_document.py "https://yourstorage.blob.core.windows.net/documents/your-file.pdf"
```

**Features:**
- Document ingestion from Azure Blob Storage
- Custom metadata attachment
- Processing statistics display

### 2. Query System (`query_system.py`)

Shows how to query the Graph RAG system with different approaches.

**Usage:**
```bash
# Default queries
python examples/query_system.py

# Custom query
python examples/query_system.py "What are the main conclusions?"
```

**Features:**
- Standard semantic search
- Graph-enhanced queries
- Hybrid search
- Result formatting and display

### 3. Complete Workflow (`complete_workflow.py`)

Full end-to-end demonstration of the Graph RAG system.

**Usage:**
```bash
python examples/complete_workflow.py
```

**Workflow:**
1. Health check
2. Get system statistics
3. Ingest multiple documents
4. Perform various queries
5. Hybrid search
6. Final statistics

## GraphRAGClient Class

All examples use a simple `GraphRAGClient` class that wraps the API calls:

```python
from complete_workflow import GraphRAGClient

# Initialize client
client = GraphRAGClient()

# Health check
health = client.health_check()

# Ingest document
result = client.ingest_document(
    file_url="https://...",
    metadata={"title": "My Doc"}
)

# Query
results = client.query(
    query="What are the findings?",
    top_k=10,
    use_graph=True
)

# Hybrid search
search_results = client.hybrid_search(
    query="machine learning",
    filters={"category": "research"}
)
```

## Customization

### Changing API URL

Edit the `API_BASE_URL` in each script:

```python
API_BASE_URL = "http://your-server:8000/api/v1"
```

### Adding Authentication

If your API requires authentication, modify the requests:

```python
headers = {
    "Authorization": "Bearer your-token-here"
}

response = requests.post(endpoint, json=payload, headers=headers)
```

## Sample Output

### Ingestion
```
Document ID: abc123...
File Name: sample.pdf
Processing Time: 45.2s
Text Chunks: 150
Images Extracted: 5
Entities Found: 87
Relationships: 234
Vectors Stored: 155
```

### Query
```
Query: What are the main conclusions?
Results Found: 10
Entities Involved: 15
Graph Enhanced: True

Top Results:
1. Score: 0.9234 | Type: text
   The main conclusions indicate that...
```

## Error Handling

All examples include error handling:

```python
try:
    result = client.ingest_document(file_url, metadata)
except requests.exceptions.RequestException as e:
    print(f"Error: {e}")
    if hasattr(e.response, 'text'):
        print(f"Details: {e.response.text}")
```

## Integration Example

```python
import requests

class MyApplication:
    def __init__(self):
        self.api_url = "http://localhost:8000/api/v1/graph-rag"

    def process_document(self, file_url, metadata):
        """Process a new document."""
        response = requests.post(
            f"{self.api_url}/ingest",
            json={"file_url": file_url, "metadata": metadata},
            timeout=300
        )
        return response.json()

    def search(self, query):
        """Search documents."""
        response = requests.post(
            f"{self.api_url}/query",
            json={"query": query, "top_k": 10},
            timeout=60
        )
        return response.json()

# Usage
app = MyApplication()
result = app.search("What is AI?")
```

## Troubleshooting

### Connection Error
```
Error: Connection refused
```
**Solution:** Make sure the API server is running:
```bash
docker-compose ps
# or
uvicorn app.main:app --reload
```

### Timeout Error
```
Error: Request timeout
```
**Solution:** Increase timeout in the scripts or wait for long-running operations.

### Authentication Error
```
Error: 401 Unauthorized
```
**Solution:** Add authentication headers if required.

## Next Steps

1. Modify examples for your use case
2. Create custom workflows
3. Integrate with your application
4. Explore the API docs: http://localhost:8000/api/docs

## Support

- API Documentation: http://localhost:8000/api/docs
- Main README: [../README.md](../README.md)
- Quick Start: [../QUICKSTART.md](../QUICKSTART.md)
