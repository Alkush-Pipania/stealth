"""WebSocket message handlers for streaming operations."""
import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from app.websocket.connection_manager import get_connection_manager, MessageType
from app.websocket.schemas import (
    WSIngestionStartedMessage,
    WSIngestionCompletedMessage,
    WSIngestionFailedMessage,
    WSQueryStartedMessage,
    WSQueryCompletedMessage,
    WSQueryFailedMessage,
    create_progress_message,
    create_query_chunk_message,
    create_error_message
)
from app.services.graph_rag_ingestion import get_ingestion_pipeline
from app.services.graph_rag_query import get_query_engine

logger = logging.getLogger(__name__)


class StreamingProgressCallback:
    """Callback for streaming ingestion progress."""

    def __init__(self, connection_id: str, request_id: Optional[str] = None):
        self.connection_id = connection_id
        self.request_id = request_id
        self.manager = get_connection_manager()

    async def send_progress(
        self,
        document_id: str,
        stage: str,
        progress: float,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        """Send progress update."""
        try:
            progress_msg = create_progress_message(
                document_id=document_id,
                stage=stage,
                progress=progress,
                message=message,
                details=details,
                request_id=self.request_id
            )

            await self.manager.send_message(
                self.connection_id,
                progress_msg
            )

        except Exception as e:
            logger.error(f"Error sending progress: {e}")


async def handle_ingestion_request(
    connection_id: str,
    file_url: str,
    metadata: Dict[str, Any],
    stream_progress: bool = True,
    request_id: Optional[str] = None
):
    """
    Handle document ingestion request with streaming progress.

    Args:
        connection_id: WebSocket connection ID
        file_url: URL to document
        metadata: Document metadata
        stream_progress: Whether to stream progress updates
        request_id: Request identifier
    """
    manager = get_connection_manager()
    document_id = None

    try:
        # Generate document ID
        import hashlib
        document_id = hashlib.md5(file_url.encode()).hexdigest()

        # Send started message
        started_msg = WSIngestionStartedMessage(
            document_id=document_id,
            file_name=file_url.split('/')[-1],
            request_id=request_id
        )
        await manager.send_message(connection_id, started_msg.model_dump())

        # Create progress callback
        progress_callback = StreamingProgressCallback(connection_id, request_id)

        # Get ingestion pipeline
        pipeline = get_ingestion_pipeline()

        # Progress stages
        stages = [
            ("downloading", 10, "Downloading document from Azure Blob Storage"),
            ("parsing", 30, "Parsing document with LlamaParse"),
            ("entities", 50, "Extracting entities and relationships"),
            ("embeddings", 70, "Generating embeddings"),
            ("storing", 85, "Storing vectors in Pinecone"),
            ("graph", 95, "Building knowledge graph in Neo4j"),
        ]

        # Send progress updates
        if stream_progress:
            for stage, progress, message in stages:
                await progress_callback.send_progress(
                    document_id=document_id,
                    stage=stage,
                    progress=progress,
                    message=message
                )
                # Small delay to simulate progress (remove in production for real progress)
                await asyncio.sleep(0.5)

        # Actually ingest the document
        result = await pipeline.ingest_document(
            file_url=file_url,
            metadata=metadata
        )

        # Send completion message
        completed_msg = WSIngestionCompletedMessage(
            document_id=result['document_id'],
            file_name=result['file_name'],
            processing_time_seconds=result['processing_time_seconds'],
            chunks_created=result['chunks_created'],
            images_extracted=result['images_extracted'],
            entities_extracted=result['entities_extracted'],
            relationships_created=result['relationships_created'],
            vectors_stored=result['vectors_stored'],
            request_id=request_id
        )
        await manager.send_message(connection_id, completed_msg.model_dump())

        logger.info(f"Ingestion completed for {file_url}")

    except Exception as e:
        logger.error(f"Ingestion failed: {e}")

        # Send error message
        failed_msg = WSIngestionFailedMessage(
            document_id=document_id,
            error=str(e),
            details={"file_url": file_url},
            request_id=request_id
        )
        await manager.send_message(connection_id, failed_msg.model_dump())


async def handle_query_request(
    connection_id: str,
    query: str,
    top_k: int = 10,
    use_graph: bool = True,
    stream_results: bool = True,
    request_id: Optional[str] = None
):
    """
    Handle query request with streaming results.

    Args:
        connection_id: WebSocket connection ID
        query: Query text
        top_k: Number of results
        use_graph: Use graph enhancement
        stream_results: Whether to stream results
        request_id: Request identifier
    """
    manager = get_connection_manager()

    try:
        # Send started message
        started_msg = WSQueryStartedMessage(
            query=query,
            request_id=request_id
        )
        await manager.send_message(connection_id, started_msg.model_dump())

        # Get query engine
        query_engine = get_query_engine()

        # Execute query
        result = await query_engine.query(
            query=query,
            top_k=top_k,
            use_graph=use_graph,
            graph_depth=2
        )

        # Stream results if enabled
        if stream_results and result.get('results'):
            for idx, result_item in enumerate(result['results']):
                chunk_msg = create_query_chunk_message(
                    chunk_index=idx,
                    result=result_item,
                    is_final=(idx == len(result['results']) - 1),
                    request_id=request_id
                )
                await manager.send_message(connection_id, chunk_msg)

                # Small delay between chunks
                await asyncio.sleep(0.1)

        # Send completion message
        completed_msg = WSQueryCompletedMessage(
            query=query,
            total_results=result['num_results'],
            num_entities=result['num_entities'],
            graph_enhanced=result['graph_enhanced'],
            request_id=request_id,
            summary={
                'context_chunks': len(result.get('context_chunks', [])),
                'graph_context_available': bool(result.get('graph_context'))
            }
        )
        await manager.send_message(connection_id, completed_msg.model_dump())

        logger.info(f"Query completed: {query}")

    except Exception as e:
        logger.error(f"Query failed: {e}")

        # Send error message
        failed_msg = WSQueryFailedMessage(
            query=query,
            error=str(e),
            request_id=request_id
        )
        await manager.send_message(connection_id, failed_msg.model_dump())


async def handle_subscribe(
    connection_id: str,
    topic: str,
    request_id: Optional[str] = None
):
    """
    Handle topic subscription.

    Args:
        connection_id: Connection ID
        topic: Topic to subscribe to
        request_id: Request identifier
    """
    manager = get_connection_manager()

    try:
        success = await manager.subscribe_to_topic(connection_id, topic)

        if success:
            await manager.send_message(
                connection_id,
                {
                    "type": MessageType.STATUS_UPDATE,
                    "status": "subscribed",
                    "message": f"Subscribed to topic: {topic}",
                    "request_id": request_id,
                    "topic": topic
                }
            )
        else:
            await manager.send_message(
                connection_id,
                create_error_message(
                    error=f"Failed to subscribe to topic: {topic}",
                    request_id=request_id
                )
            )

    except Exception as e:
        logger.error(f"Subscribe error: {e}")
        await manager.send_message(
            connection_id,
            create_error_message(
                error=str(e),
                request_id=request_id
            )
        )


async def handle_unsubscribe(
    connection_id: str,
    topic: str,
    request_id: Optional[str] = None
):
    """
    Handle topic unsubscription.

    Args:
        connection_id: Connection ID
        topic: Topic to unsubscribe from
        request_id: Request identifier
    """
    manager = get_connection_manager()

    try:
        success = await manager.unsubscribe_from_topic(connection_id, topic)

        if success:
            await manager.send_message(
                connection_id,
                {
                    "type": MessageType.STATUS_UPDATE,
                    "status": "unsubscribed",
                    "message": f"Unsubscribed from topic: {topic}",
                    "request_id": request_id,
                    "topic": topic
                }
            )

    except Exception as e:
        logger.error(f"Unsubscribe error: {e}")
        await manager.send_message(
            connection_id,
            create_error_message(
                error=str(e),
                request_id=request_id
            )
        )


async def handle_ping(connection_id: str, request_id: Optional[str] = None):
    """Handle ping message."""
    manager = get_connection_manager()

    await manager.send_message(
        connection_id,
        {
            "type": MessageType.PONG,
            "timestamp": datetime.now().isoformat(),
            "request_id": request_id
        }
    )
