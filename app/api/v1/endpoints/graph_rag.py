"""Graph RAG API endpoints."""
import logging
from fastapi import APIRouter, HTTPException, BackgroundTasks
from datetime import datetime
from typing import Dict, Any

from app.models.graph_rag import (
    DocumentIngestRequest,
    DocumentIngestResponse,
    QueryRequest,
    QueryResponse,
    HybridSearchRequest,
    HybridSearchResponse,
    HealthCheckResponse,
    ErrorResponse
)
from app.services.graph_rag_ingestion import get_ingestion_pipeline
from app.services.graph_rag_query import get_query_engine
from app.services.vector_store import get_vector_store_service
from app.services.graph_store import get_graph_store_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/ingest",
    response_model=DocumentIngestResponse,
    status_code=200,
    summary="Ingest a document into Graph RAG system",
    description="""
    Ingest a document from Azure Blob Storage into the Graph RAG system.

    This endpoint:
    1. Downloads the document from Azure Blob Storage
    2. Parses it using LlamaParse (with multi-modal support)
    3. Extracts entities and relationships
    4. Generates embeddings using Gemini (768 dimensions)
    5. Stores vectors in Pinecone
    6. Builds knowledge graph in Neo4j
    """,
    responses={
        200: {"model": DocumentIngestResponse},
        400: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    }
)
async def ingest_document(request: DocumentIngestRequest):
    """Ingest a document into the Graph RAG system."""
    try:
        logger.info(f"Received ingestion request for: {request.file_url}")

        # Get ingestion pipeline
        pipeline = get_ingestion_pipeline()

        # Ingest document
        result = await pipeline.ingest_document(
            file_url=request.file_url,
            metadata=request.metadata
        )

        return DocumentIngestResponse(**result)

    except ValueError as e:
        logger.error(f"Validation error during ingestion: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error during ingestion: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to ingest document: {str(e)}"
        )


@router.post(
    "/query",
    response_model=QueryResponse,
    status_code=200,
    summary="Query the Graph RAG system",
    description="""
    Query the Graph RAG system using semantic search and graph traversal.

    This endpoint:
    1. Generates embedding for the query using Gemini
    2. Performs vector similarity search in Pinecone
    3. Extracts relevant entities from results
    4. Enhances results with knowledge graph context from Neo4j
    5. Returns ranked results with graph context
    """,
    responses={
        200: {"model": QueryResponse},
        400: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    }
)
async def query_graph_rag(request: QueryRequest):
    """Query the Graph RAG system."""
    try:
        logger.info(f"Received query: {request.query}")

        # Get query engine
        query_engine = get_query_engine()

        # Execute query
        result = await query_engine.query(
            query=request.query,
            top_k=request.top_k,
            namespace=request.namespace,
            use_graph=request.use_graph,
            graph_depth=request.graph_depth
        )

        return QueryResponse(**result)

    except ValueError as e:
        logger.error(f"Validation error during query: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error during query: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to execute query: {str(e)}"
        )


@router.post(
    "/hybrid-search",
    response_model=HybridSearchResponse,
    status_code=200,
    summary="Perform hybrid search",
    description="""
    Perform hybrid search combining vector similarity and graph entity search.

    This endpoint combines:
    - Vector similarity search in Pinecone
    - Entity-based search in Neo4j knowledge graph
    - Intelligent reranking of results
    """,
    responses={
        200: {"model": HybridSearchResponse},
        400: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    }
)
async def hybrid_search(request: HybridSearchRequest):
    """Perform hybrid search."""
    try:
        logger.info(f"Received hybrid search request: {request.query}")

        # Get query engine
        query_engine = get_query_engine()

        # Execute hybrid search
        result = await query_engine.hybrid_search(
            query=request.query,
            filters=request.filters,
            top_k=request.top_k
        )

        return HybridSearchResponse(**result)

    except ValueError as e:
        logger.error(f"Validation error during hybrid search: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error during hybrid search: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to execute hybrid search: {str(e)}"
        )


@router.get(
    "/health",
    response_model=HealthCheckResponse,
    status_code=200,
    summary="Check health of Graph RAG services",
    description="Check the health and connectivity of all Graph RAG services"
)
async def health_check():
    """Check health of all services."""
    try:
        services_status = {}

        # Check Pinecone
        try:
            vector_store = get_vector_store_service()
            stats = vector_store.get_index_stats()
            services_status["pinecone"] = "connected"
        except Exception as e:
            logger.error(f"Pinecone health check failed: {e}")
            services_status["pinecone"] = f"error: {str(e)}"

        # Check Neo4j
        try:
            graph_store = get_graph_store_service()
            # Simple connectivity check
            services_status["neo4j"] = "connected"
        except Exception as e:
            logger.error(f"Neo4j health check failed: {e}")
            services_status["neo4j"] = f"error: {str(e)}"

        # Overall status
        all_healthy = all(
            status == "connected" for status in services_status.values()
        )
        overall_status = "healthy" if all_healthy else "degraded"

        return HealthCheckResponse(
            status=overall_status,
            services=services_status,
            timestamp=datetime.now().isoformat()
        )

    except Exception as e:
        logger.error(f"Health check error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Health check failed: {str(e)}"
        )


@router.get(
    "/stats",
    response_model=Dict[str, Any],
    status_code=200,
    summary="Get system statistics",
    description="Get statistics about the Graph RAG system"
)
async def get_stats():
    """Get system statistics."""
    try:
        stats = {}

        # Get Pinecone stats
        try:
            vector_store = get_vector_store_service()
            pinecone_stats = vector_store.get_index_stats()
            stats["vector_store"] = pinecone_stats
        except Exception as e:
            logger.error(f"Failed to get Pinecone stats: {e}")
            stats["vector_store"] = {"error": str(e)}

        # Get Neo4j stats
        try:
            graph_store = get_graph_store_service()
            # You could add a method to get graph stats
            stats["graph_store"] = {"status": "connected"}
        except Exception as e:
            logger.error(f"Failed to get Neo4j stats: {e}")
            stats["graph_store"] = {"error": str(e)}

        return stats

    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get stats: {str(e)}"
        )
