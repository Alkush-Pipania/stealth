from fastapi import FastAPI
import logging

logger = logging.getLogger(__name__)

async def startup_handler(app: FastAPI):
    """Initialize services on startup"""
    logger.info("🚀 Application starting...")
    # app.state.db_connected = True

async def shutdown_handler(app: FastAPI):
    """Cleanup on shutdown"""
    logger.info("🛑 Application shutting down...")
    # app.state.db_connected = False