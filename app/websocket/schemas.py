"""WebSocket message schemas and protocols."""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class WSMessageType(str, Enum):
    """WebSocket message types."""
    # Client -> Server
    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"
    INGEST_REQUEST = "ingest_request"
    QUERY_REQUEST = "query_request"
    PING = "ping"

    # Server -> Client
    CONNECTED = "connected"
    PONG = "pong"
    ERROR = "error"
    SUBSCRIBED = "subscribed"
    UNSUBSCRIBED = "unsubscribed"

    # Ingestion events
    INGESTION_STARTED = "ingestion_started"
    INGESTION_PROGRESS = "ingestion_progress"
    INGESTION_COMPLETED = "ingestion_completed"
    INGESTION_FAILED = "ingestion_failed"

    # Query events
    QUERY_STARTED = "query_started"
    QUERY_CHUNK = "query_chunk"
    QUERY_COMPLETED = "query_completed"
    QUERY_FAILED = "query_failed"

    # Status events
    STATUS_UPDATE = "status_update"


class WSBaseMessage(BaseModel):
    """Base WebSocket message."""
    type: WSMessageType
    timestamp: Optional[str] = Field(default_factory=lambda: datetime.now().isoformat())
    request_id: Optional[str] = None


# Client -> Server Messages

class WSSubscribeMessage(WSBaseMessage):
    """Subscribe to a topic."""
    type: WSMessageType = WSMessageType.SUBSCRIBE
    topic: str = Field(..., description="Topic to subscribe to")


class WSUnsubscribeMessage(WSBaseMessage):
    """Unsubscribe from a topic."""
    type: WSMessageType = WSMessageType.UNSUBSCRIBE
    topic: str = Field(..., description="Topic to unsubscribe from")


class WSIngestRequest(WSBaseMessage):
    """Request document ingestion."""
    type: WSMessageType = WSMessageType.INGEST_REQUEST
    file_url: str = Field(..., description="URL to document")
    metadata: Dict[str, Any] = Field(default={}, description="Document metadata")
    stream_progress: bool = Field(default=True, description="Stream progress updates")


class WSQueryRequest(WSBaseMessage):
    """Request query execution."""
    type: WSMessageType = WSMessageType.QUERY_REQUEST
    query: str = Field(..., description="Query text")
    top_k: int = Field(default=10, description="Number of results")
    use_graph: bool = Field(default=True, description="Use graph enhancement")
    stream_results: bool = Field(default=True, description="Stream results as they arrive")


# Server -> Client Messages

class WSConnectedMessage(WSBaseMessage):
    """Connection established."""
    type: WSMessageType = WSMessageType.CONNECTED
    connection_id: str
    message: str = "Connected successfully"


class WSErrorMessage(WSBaseMessage):
    """Error message."""
    type: WSMessageType = WSMessageType.ERROR
    error: str
    details: Optional[Dict[str, Any]] = None


class WSSubscribedMessage(WSBaseMessage):
    """Subscription confirmed."""
    type: WSMessageType = WSMessageType.SUBSCRIBED
    topic: str
    message: str = "Subscribed successfully"


class WSUnsubscribedMessage(WSBaseMessage):
    """Unsubscription confirmed."""
    type: WSMessageType = WSMessageType.UNSUBSCRIBED
    topic: str
    message: str = "Unsubscribed successfully"


# Ingestion Messages

class WSIngestionStartedMessage(WSBaseMessage):
    """Ingestion started."""
    type: WSMessageType = WSMessageType.INGESTION_STARTED
    document_id: str
    file_name: str
    message: str = "Document ingestion started"


class WSIngestionProgressMessage(WSBaseModel):
    """Ingestion progress update."""
    type: WSMessageType = WSMessageType.INGESTION_PROGRESS
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    request_id: Optional[str] = None
    document_id: str
    stage: str = Field(..., description="Current processing stage")
    progress: float = Field(..., ge=0, le=100, description="Progress percentage")
    message: str
    details: Optional[Dict[str, Any]] = None


class WSIngestionCompletedMessage(WSBaseMessage):
    """Ingestion completed."""
    type: WSMessageType = WSMessageType.INGESTION_COMPLETED
    document_id: str
    file_name: str
    processing_time_seconds: float
    chunks_created: int
    images_extracted: int
    entities_extracted: int
    relationships_created: int
    vectors_stored: int
    message: str = "Document ingestion completed successfully"


class WSIngestionFailedMessage(WSBaseMessage):
    """Ingestion failed."""
    type: WSMessageType = WSMessageType.INGESTION_FAILED
    document_id: Optional[str] = None
    error: str
    details: Optional[Dict[str, Any]] = None


# Query Messages

class WSQueryStartedMessage(WSBaseMessage):
    """Query execution started."""
    type: WSMessageType = WSMessageType.QUERY_STARTED
    query: str
    message: str = "Query execution started"


class WSQueryChunkMessage(WSBaseMessage):
    """Query result chunk."""
    type: WSMessageType = WSMessageType.QUERY_CHUNK
    chunk_index: int
    result: Dict[str, Any]
    is_final: bool = False


class WSQueryCompletedMessage(WSBaseMessage):
    """Query completed."""
    type: WSMessageType = WSMessageType.QUERY_COMPLETED
    query: str
    total_results: int
    num_entities: int
    graph_enhanced: bool
    message: str = "Query completed successfully"
    summary: Optional[Dict[str, Any]] = None


class WSQueryFailedMessage(WSBaseMessage):
    """Query failed."""
    type: WSMessageType = WSMessageType.QUERY_FAILED
    query: str
    error: str
    details: Optional[Dict[str, Any]] = None


# Status Messages

class WSStatusUpdateMessage(WSBaseMessage):
    """System status update."""
    type: WSMessageType = WSMessageType.STATUS_UPDATE
    status: str
    message: str
    details: Optional[Dict[str, Any]] = None


# Helper functions

def parse_client_message(data: Dict[str, Any]) -> Optional[WSBaseMessage]:
    """
    Parse incoming client message.

    Args:
        data: Raw message data

    Returns:
        Parsed message or None if invalid
    """
    try:
        msg_type = data.get("type")

        if not msg_type:
            return None

        # Map message types to schemas
        type_map = {
            WSMessageType.SUBSCRIBE: WSSubscribeMessage,
            WSMessageType.UNSUBSCRIBE: WSUnsubscribeMessage,
            WSMessageType.INGEST_REQUEST: WSIngestRequest,
            WSMessageType.QUERY_REQUEST: WSQueryRequest,
            WSMessageType.PING: WSBaseMessage,
        }

        schema = type_map.get(msg_type)
        if not schema:
            return None

        return schema(**data)

    except Exception:
        return None


def create_error_message(
    error: str,
    details: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None
) -> Dict[str, Any]:
    """Create an error message."""
    msg = WSErrorMessage(
        error=error,
        details=details,
        request_id=request_id
    )
    return msg.model_dump()


def create_progress_message(
    document_id: str,
    stage: str,
    progress: float,
    message: str,
    details: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None
) -> Dict[str, Any]:
    """Create a progress update message."""
    msg = WSIngestionProgressMessage(
        document_id=document_id,
        stage=stage,
        progress=progress,
        message=message,
        details=details,
        request_id=request_id
    )
    return msg.model_dump()


def create_query_chunk_message(
    chunk_index: int,
    result: Dict[str, Any],
    is_final: bool = False,
    request_id: Optional[str] = None
) -> Dict[str, Any]:
    """Create a query result chunk message."""
    msg = WSQueryChunkMessage(
        chunk_index=chunk_index,
        result=result,
        is_final=is_final,
        request_id=request_id
    )
    return msg.model_dump()
