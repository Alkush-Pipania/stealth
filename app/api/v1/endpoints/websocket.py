"""WebSocket API endpoints for real-time communication."""
import logging
import uuid
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from typing import Optional

from app.websocket.connection_manager import get_connection_manager
from app.websocket.schemas import (
    WSMessageType,
    parse_client_message,
    WSQueryRequest,
    WSSubscribeMessage,
    WSUnsubscribeMessage,
    create_error_message
)
from app.websocket.handlers import (
    handle_query_request,
    handle_subscribe,
    handle_unsubscribe,
    handle_ping
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    client_id: Optional[str] = Query(None, description="Optional client identifier"),
    client_name: Optional[str] = Query(None, description="Optional client name")
):
    """
    Main WebSocket endpoint for real-time communication.

    Supports:
    - Query execution with result streaming
    - Topic subscriptions
    - Bidirectional messaging

    Example connection:
        ws://localhost:8000/api/v1/ws?client_id=my-client&client_name=MyApp
    """
    # Generate unique connection ID
    connection_id = client_id or str(uuid.uuid4())

    # Client metadata
    client_info = {
        "client_id": client_id,
        "client_name": client_name,
        "user_agent": websocket.headers.get("user-agent"),
    }

    manager = get_connection_manager()
    connection = None

    try:
        # Accept connection
        connection = await manager.connect(
            websocket=websocket,
            connection_id=connection_id,
            client_info=client_info
        )

        logger.info(
            f"WebSocket connected: {connection_id} "
            f"(name: {client_name or 'unknown'})"
        )

        # Message handling loop
        while True:
            try:
                # Receive message from client
                data = await websocket.receive_json()

                # Update activity timestamp
                connection.messages_received += 1

                # Parse message
                message = parse_client_message(data)

                if not message:
                    await manager.send_message(
                        connection_id,
                        create_error_message(
                            error="Invalid message format",
                            details={"received": data}
                        )
                    )
                    continue

                # Extract request ID if present
                request_id = getattr(message, 'request_id', None)

                # Route message to appropriate handler
                if message.type == WSMessageType.QUERY_REQUEST:
                    # Handle query request
                    query_msg: WSQueryRequest = message
                    import asyncio
                    asyncio.create_task(
                        handle_query_request(
                            connection_id=connection_id,
                            query=query_msg.query,
                            top_k=query_msg.top_k,
                            use_graph=query_msg.use_graph,
                            stream_results=query_msg.stream_results,
                            request_id=request_id
                        )
                    )

                elif message.type == WSMessageType.SUBSCRIBE:
                    # Handle subscription
                    sub_msg: WSSubscribeMessage = message
                    await handle_subscribe(
                        connection_id=connection_id,
                        topic=sub_msg.topic,
                        request_id=request_id
                    )

                elif message.type == WSMessageType.UNSUBSCRIBE:
                    # Handle unsubscription
                    unsub_msg: WSUnsubscribeMessage = message
                    await handle_unsubscribe(
                        connection_id=connection_id,
                        topic=unsub_msg.topic,
                        request_id=request_id
                    )

                elif message.type == WSMessageType.PING:
                    # Handle ping
                    await handle_ping(
                        connection_id=connection_id,
                        request_id=request_id
                    )

                else:
                    await manager.send_message(
                        connection_id,
                        create_error_message(
                            error=f"Unsupported message type: {message.type}",
                            request_id=request_id
                        )
                    )

            except WebSocketDisconnect:
                logger.info(f"Client disconnected: {connection_id}")
                break

            except Exception as e:
                logger.error(f"Error processing message: {e}")
                await manager.send_message(
                    connection_id,
                    create_error_message(
                        error="Internal server error",
                        details={"error": str(e)}
                    )
                )

    except Exception as e:
        logger.error(f"WebSocket error for {connection_id}: {e}")

    finally:
        # Clean up connection
        if connection_id:
            await manager.disconnect(connection_id)
            logger.info(f"Connection cleaned up: {connection_id}")


@router.get("/ws/connections")
async def get_connections():
    """
    Get information about active WebSocket connections.

    Returns:
        Connection statistics and list of active connections
    """
    manager = get_connection_manager()
    return manager.get_stats()


@router.get("/ws/connections/{connection_id}")
async def get_connection_info(connection_id: str):
    """
    Get information about a specific connection.

    Args:
        connection_id: Connection identifier

    Returns:
        Connection details
    """
    manager = get_connection_manager()
    connection = manager.get_connection(connection_id)

    if not connection:
        return {
            "error": "Connection not found",
            "connection_id": connection_id
        }

    return connection.to_dict()


@router.post("/ws/broadcast")
async def broadcast_message(message: dict):
    """
    Broadcast a message to all connected clients.

    Args:
        message: Message to broadcast

    Returns:
        Broadcast status
    """
    manager = get_connection_manager()
    await manager.broadcast(message)

    return {
        "status": "broadcasted",
        "recipients": manager.get_connection_count(),
        "message": message
    }


@router.post("/ws/topics/{topic}/broadcast")
async def broadcast_to_topic(topic: str, message: dict):
    """
    Broadcast a message to all subscribers of a topic.

    Args:
        topic: Topic name
        message: Message to broadcast

    Returns:
        Broadcast status
    """
    manager = get_connection_manager()
    subscribers = manager.get_topic_subscribers(topic)

    await manager.broadcast_to_topic(topic, message)

    return {
        "status": "broadcasted",
        "topic": topic,
        "recipients": len(subscribers),
        "message": message
    }


@router.get("/ws/topics")
async def get_topics():
    """
    Get list of active topics and their subscribers.

    Returns:
        Topics information
    """
    manager = get_connection_manager()
    stats = manager.get_stats()

    topics_info = {}
    for topic in stats.get('connections', []):
        for subscription in topic.get('subscriptions', []):
            if subscription not in topics_info:
                topics_info[subscription] = {
                    'topic': subscription,
                    'subscribers': []
                }
            topics_info[subscription]['subscribers'].append(
                topic.get('connection_id')
            )

    return {
        "topics": list(topics_info.values()),
        "total_topics": len(topics_info)
    }


@router.get("/ws/health")
async def websocket_health():
    """
    Check WebSocket service health.

    Returns:
        Health status
    """
    manager = get_connection_manager()
    stats = manager.get_stats()

    return {
        "status": "healthy",
        "active_connections": stats['active_connections'],
        "total_messages_sent": stats['total_messages_sent'],
        "total_messages_received": stats['total_messages_received']
    }
