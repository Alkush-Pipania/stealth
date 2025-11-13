"""Pydantic models for Graph RAG API."""
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, Dict, Any, List


# Ingestion Models
class DocumentIngestRequest(BaseModel):
    """Request model for document ingestion."""

    file_url: str = Field(
        ...,
        description="URL or path to the document in Azure Blob Storage",
        examples=["https://storage.azure.com/container/document.pdf"]
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default={},
        description="Optional metadata about the document"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "file_url": "https://mystorageaccount.blob.core.windows.net/documents/sample.pdf",
                "metadata": {
                    "author": "John Doe",
                    "category": "research",
                    "tags": ["AI", "ML"]
                }
            }
        }


class DocumentIngestResponse(BaseModel):
    """Response model for document ingestion."""

    status: str = Field(..., description="Ingestion status")
    document_id: str = Field(..., description="Unique document identifier")
    file_name: str = Field(..., description="Name of the file")
    processing_time_seconds: float = Field(..., description="Processing time in seconds")
    chunks_created: int = Field(..., description="Number of text chunks created")
    images_extracted: int = Field(..., description="Number of images extracted")
    entities_extracted: int = Field(..., description="Number of entities extracted")
    relationships_created: int = Field(..., description="Number of relationships created")
    vectors_stored: int = Field(..., description="Number of vectors stored in Pinecone")
    graph_stats: Dict[str, Any] = Field(..., description="Graph database statistics")


# Query Models
class QueryRequest(BaseModel):
    """Request model for querying the Graph RAG system."""

    query: str = Field(
        ...,
        description="User query text",
        min_length=1,
        examples=["What are the key findings about climate change?"]
    )
    top_k: int = Field(
        default=10,
        description="Number of similar chunks to retrieve",
        ge=1,
        le=100
    )
    namespace: str = Field(
        default="",
        description="Optional namespace to search in (e.g., specific document ID)"
    )
    use_graph: bool = Field(
        default=True,
        description="Whether to enhance results with graph context"
    )
    graph_depth: int = Field(
        default=2,
        description="Depth of graph traversal",
        ge=1,
        le=5
    )

    class Config:
        json_schema_extra = {
            "example": {
                "query": "What are the main conclusions about artificial intelligence?",
                "top_k": 10,
                "namespace": "",
                "use_graph": True,
                "graph_depth": 2
            }
        }


class ContextChunk(BaseModel):
    """Model for a context chunk in query results."""

    text: str = Field(..., description="Chunk text content")
    score: float = Field(..., description="Similarity score")
    doc_id: str = Field(..., description="Document ID")
    type: str = Field(..., description="Chunk type (text/image)")


class GraphContext(BaseModel):
    """Model for graph context data."""

    entities: List[Dict[str, Any]] = Field(default=[], description="Related entities")
    relationships: List[Dict[str, Any]] = Field(default=[], description="Relationships")
    num_entities: int = Field(default=0, description="Number of entities")
    num_relationships: int = Field(default=0, description="Number of relationships")


class QueryResult(BaseModel):
    """Model for individual query result."""

    id: str = Field(..., description="Result ID")
    score: float = Field(..., description="Relevance score")
    text: str = Field(..., description="Result text")
    doc_id: str = Field(..., description="Document ID")
    type: str = Field(..., description="Result type")
    graph_enhanced: bool = Field(..., description="Whether result is graph-enhanced")
    metadata: Dict[str, Any] = Field(default={}, description="Additional metadata")


class QueryResponse(BaseModel):
    """Response model for query."""

    query: str = Field(..., description="Original query")
    results: List[QueryResult] = Field(..., description="Query results")
    num_results: int = Field(..., description="Number of results returned")
    num_entities: int = Field(..., description="Number of entities involved")
    graph_enhanced: bool = Field(..., description="Whether graph enhancement was used")
    context_chunks: List[ContextChunk] = Field(..., description="Context chunks used")
    graph_context: Optional[Dict[str, Any]] = Field(None, description="Graph context data")


# Hybrid Search Models
class HybridSearchRequest(BaseModel):
    """Request model for hybrid search."""

    query: str = Field(
        ...,
        description="Search query",
        min_length=1
    )
    filters: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional metadata filters"
    )
    top_k: int = Field(
        default=10,
        description="Number of results to return",
        ge=1,
        le=100
    )

    class Config:
        json_schema_extra = {
            "example": {
                "query": "machine learning applications",
                "filters": {"category": "research"},
                "top_k": 10
            }
        }


class HybridSearchResponse(BaseModel):
    """Response model for hybrid search."""

    query: str = Field(..., description="Original query")
    results: List[Dict[str, Any]] = Field(..., description="Search results")
    num_vector_results: int = Field(..., description="Number of vector search results")
    num_entity_results: int = Field(..., description="Number of entity search results")
    search_type: str = Field(..., description="Type of search performed")


# Health Check Models
class HealthCheckResponse(BaseModel):
    """Response model for health check."""

    status: str = Field(..., description="Overall health status")
    services: Dict[str, str] = Field(..., description="Status of individual services")
    timestamp: str = Field(..., description="Timestamp of health check")


# Error Models
class ErrorResponse(BaseModel):
    """Error response model."""

    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
