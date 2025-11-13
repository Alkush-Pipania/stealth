# Graph RAG API

A powerful Graph-based Retrieval Augmented Generation (RAG) API that combines semantic search with knowledge graph capabilities for enhanced document understanding and querying.

## Features

- **Multi-Modal Document Processing**: Extract text and images from PDFs using LlamaParse
- **Semantic Search**: 768-dimensional embeddings using Google Gemini with cosine similarity
- **Knowledge Graph**: Build and query knowledge graphs with Neo4j
- **Vector Store**: Fast similarity search using Pinecone
- **Azure Blob Storage**: Seamless document retrieval from Azure cloud storage
- **Hybrid Search**: Combine vector similarity with graph traversal for superior results

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Graph RAG System                        │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐   │
│  │ Azure Blob   │   │  LlamaParse  │   │    Gemini    │   │
│  │   Storage    │──▶│  Multi-Modal │──▶│  Embeddings  │   │
│  │              │   │    Parser    │   │  (768-dim)   │   │
│  └──────────────┘   └──────────────┘   └──────────────┘   │
│                            │                     │           │
│                            ▼                     ▼           │
│                     ┌──────────────┐    ┌──────────────┐   │
│                     │    Neo4j     │    │   Pinecone   │   │
│                     │ Knowledge    │    │   Vector     │   │
│                     │    Graph     │    │   Database   │   │
│                     └──────────────┘    └──────────────┘   │
│                            │                     │           │
│                            └──────────┬──────────┘           │
│                                       ▼                       │
│                            ┌──────────────────┐              │
│                            │   Query Engine   │              │
│                            │  (Graph RAG)     │              │
│                            └──────────────────┘              │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## Tech Stack

- **FastAPI**: Modern, fast web framework for building APIs
- **LlamaParse**: Advanced document parsing with multi-modal support
- **LangChain**: Framework for LLM-powered applications
- **Google Gemini**: State-of-the-art embeddings (768 dimensions)
- **Pinecone**: Managed vector database with cosine similarity
- **Neo4j**: Graph database for knowledge representation
- **Azure Blob Storage**: Cloud storage for documents

## Installation

### Prerequisites

- Python 3.10+
- Neo4j database (local or cloud)
- API keys for:
  - LlamaParse
  - Google Gemini
  - Pinecone
  - Azure Storage

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd stealth
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and configuration
   ```

5. **Start Neo4j**
   ```bash
   # Using Docker
   docker run -d \
     --name neo4j \
     -p 7474:7474 -p 7687:7687 \
     -e NEO4J_AUTH=neo4j/your_password \
     neo4j:latest
   ```

6. **Run the application**
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

## Configuration

Edit `.env` file with your credentials:

```env
# Azure Blob Storage
AZURE_STORAGE_CONNECTION_STRING=your_connection_string
AZURE_STORAGE_ACCOUNT_NAME=your_account_name
AZURE_STORAGE_ACCOUNT_KEY=your_account_key
AZURE_STORAGE_CONTAINER_NAME=documents

# LlamaParse
LLAMA_CLOUD_API_KEY=your_llama_api_key

# Google Gemini
GOOGLE_API_KEY=your_google_api_key

# Pinecone
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_ENVIRONMENT=your_environment
PINECONE_INDEX_NAME=graph-rag-embeddings

# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_neo4j_password
```

## API Endpoints

### Document Ingestion

**POST** `/api/v1/graph-rag/ingest`

Ingest a document from Azure Blob Storage into the Graph RAG system.

```bash
curl -X POST "http://localhost:8000/api/v1/graph-rag/ingest" \
  -H "Content-Type: application/json" \
  -d '{
    "file_url": "https://mystorageaccount.blob.core.windows.net/documents/sample.pdf",
    "metadata": {
      "author": "John Doe",
      "category": "research"
    }
  }'
```

**Response:**
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
  "vectors_stored": 155,
  "graph_stats": {
    "document_nodes": 1,
    "chunk_nodes": 150,
    "entity_nodes": 87,
    "relationships": 234
  }
}
```

### Query

**POST** `/api/v1/graph-rag/query`

Query the Graph RAG system using semantic search and graph traversal.

```bash
curl -X POST "http://localhost:8000/api/v1/graph-rag/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the main conclusions about artificial intelligence?",
    "top_k": 10,
    "use_graph": true,
    "graph_depth": 2
  }'
```

**Response:**
```json
{
  "query": "What are the main conclusions about artificial intelligence?",
  "results": [...],
  "num_results": 10,
  "num_entities": 15,
  "graph_enhanced": true,
  "context_chunks": [...],
  "graph_context": {
    "entities": [...],
    "relationships": [...]
  }
}
```

### Hybrid Search

**POST** `/api/v1/graph-rag/hybrid-search`

Perform hybrid search combining vector similarity and entity search.

```bash
curl -X POST "http://localhost:8000/api/v1/graph-rag/hybrid-search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "machine learning applications",
    "filters": {"category": "research"},
    "top_k": 10
  }'
```

### Health Check

**GET** `/api/v1/graph-rag/health`

Check the health status of all services.

```bash
curl -X GET "http://localhost:8000/api/v1/graph-rag/health"
```

### System Statistics

**GET** `/api/v1/graph-rag/stats`

Get statistics about the Graph RAG system.

```bash
curl -X GET "http://localhost:8000/api/v1/graph-rag/stats"
```

### Delete Document

**DELETE** `/api/v1/graph-rag/documents/{document_id}`

Delete a document and all its associated data.

```bash
curl -X DELETE "http://localhost:8000/api/v1/graph-rag/documents/abc123..."
```

## API Documentation

Once the application is running, visit:

- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc

## Project Structure

```
stealth/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/
│   │       │   ├── graph_rag.py    # Graph RAG endpoints
│   │       │   └── user.py         # User endpoints
│   │       └── router.py           # API router
│   ├── core/
│   │   └── events.py               # Startup/shutdown events
│   ├── models/
│   │   └── graph_rag.py            # Pydantic models
│   ├── services/
│   │   ├── azure_storage.py        # Azure Blob Storage client
│   │   ├── document_parser.py      # LlamaParse integration
│   │   ├── embeddings.py           # Gemini embeddings
│   │   ├── vector_store.py         # Pinecone integration
│   │   ├── graph_store.py          # Neo4j integration
│   │   ├── graph_rag_ingestion.py  # Ingestion pipeline
│   │   └── graph_rag_query.py      # Query engine
│   ├── config.py                   # Configuration management
│   └── main.py                     # FastAPI application
├── requirements.txt                # Python dependencies
├── .env.example                    # Environment variables template
├── Dockerfile                      # Docker configuration
├── docker-compose.yml              # Docker Compose setup
└── README.md                       # This file
```

## How It Works

### Ingestion Pipeline

1. **Document Retrieval**: Download PDF from Azure Blob Storage
2. **Multi-Modal Parsing**: Extract text and images using LlamaParse
3. **Entity Extraction**: Identify entities and relationships from text
4. **Embedding Generation**: Create 768-dimensional vectors using Gemini
5. **Vector Storage**: Store embeddings in Pinecone with cosine similarity
6. **Graph Building**: Create knowledge graph in Neo4j with entities, relationships, and chunks

### Query Pipeline

1. **Query Embedding**: Generate embedding for user query using Gemini
2. **Vector Search**: Find similar chunks in Pinecone using cosine similarity
3. **Entity Extraction**: Extract entities from top results
4. **Graph Traversal**: Enhance results with related entities from Neo4j
5. **Result Ranking**: Combine and rank results using hybrid scoring
6. **Context Assembly**: Return results with graph context

## Advanced Features

### Multi-Modal Support

The system automatically extracts and processes images from PDFs:
- Images are extracted from PDF pages
- Gemini generates descriptions of images
- Image descriptions are embedded and searchable
- Visual content enhances retrieval quality

### Graph Enhancement

Knowledge graph provides:
- Entity relationship mapping
- Concept clustering
- Cross-document connections
- Semantic navigation

### Hybrid Search

Combines:
- Semantic similarity (vector search)
- Entity matching (graph search)
- Intelligent reranking
- Context-aware results

## Performance

- **Embedding Dimension**: 768 (Gemini text-embedding-004)
- **Similarity Metric**: Cosine similarity
- **Vector Database**: Pinecone (managed, scalable)
- **Graph Database**: Neo4j (optimized for graph queries)

## Development

### Running Tests

```bash
pytest tests/ -v
```

### Code Formatting

```bash
black app/
isort app/
```

### Type Checking

```bash
mypy app/
```

## Docker Deployment

### Build and run with Docker Compose

```bash
docker-compose up -d
```

This will start:
- FastAPI application
- Neo4j database
- (Optional) Additional services

### Build Docker image

```bash
docker build -t graph-rag-api .
```

### Run Docker container

```bash
docker run -p 8000:8000 --env-file .env graph-rag-api
```

## Troubleshooting

### Common Issues

1. **Neo4j Connection Error**
   - Ensure Neo4j is running
   - Check credentials in `.env`
   - Verify port 7687 is accessible

2. **Pinecone Index Not Found**
   - Index is created automatically on first use
   - Verify API key and environment

3. **Azure Storage Error**
   - Check connection string
   - Verify container exists
   - Ensure blob URLs are accessible

4. **LlamaParse Error**
   - Verify API key is valid
   - Check rate limits
   - Ensure document format is supported

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

[Add your license here]

## Support

For issues and questions:
- Open an issue on GitHub
- Contact: [Your contact information]

## Acknowledgments

- LlamaParse for document parsing
- Google Gemini for embeddings
- Pinecone for vector storage
- Neo4j for graph database
- FastAPI for the web framework
