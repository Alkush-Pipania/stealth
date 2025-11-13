from fastapi import FastAPI
import logging
from app.config import settings
from app.services.graph_store import GraphStore
from pinecone import Pinecone

logger = logging.getLogger(__name__)

async def startup_handler(app: FastAPI):
    """Initialize services on startup"""
    logger.info("🚀 Application starting...")

    # Validate required environment variables
    try:
        settings.validate_required_settings()
    except ValueError as e:
        logger.error(f"Configuration validation failed: {e}")
        raise

    # Initialize service health tracking
    app.state.services_health = {
        "neo4j": False,
        "pinecone": False,
    }

    # Test Neo4j connection
    try:
        graph_store = GraphStore()
        graph_store.verify_connection()
        app.state.services_health["neo4j"] = True
        logger.info("✓ Neo4j connection verified")
    except Exception as e:
        logger.error(f"✗ Neo4j connection failed: {e}")
        app.state.services_health["neo4j"] = False

    # Test Pinecone connection
    try:
        pc = Pinecone(api_key=settings.PINECONE_API_KEY)
        pc.list_indexes()
        app.state.services_health["pinecone"] = True
        logger.info("✓ Pinecone connection verified")
    except Exception as e:
        logger.error(f"✗ Pinecone connection failed: {e}")
        app.state.services_health["pinecone"] = False

    logger.info("🎉 Application startup complete")

async def shutdown_handler(app: FastAPI):
    """Cleanup on shutdown"""
    logger.info("🛑 Application shutting down...")

    # Mark all services as disconnected
    if hasattr(app.state, "services_health"):
        app.state.services_health = {
            "neo4j": False,
            "pinecone": False,
        }

    logger.info("👋 Application shutdown complete")