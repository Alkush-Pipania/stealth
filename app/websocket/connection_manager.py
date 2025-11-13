"""WebSocket connection manager for handling multiple concurrent connections."""
import logging
import json
from typing import Dict, List, Optional, Any, Set
from datetime import datetime
import asyncio
from fastapi import WebSocket, WebSocketDisconnect
from enum import Enum

logger = logging.getLogger(__name__)


class ConnectionState(str, Enum):
    """WebSocket connection states."""
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTING = "disconnecting"
    DISCONNECTED = "disconnected"


class MessageType(str, Enum):
    """WebSocket message types."""
    # System messages
    CONNECT = "connect"
    DISCONNECT = "disconnect"
    ERROR = "error"
    PING = "ping"
    PONG = "pong"

    # Ingestion messages
    INGESTION_START = "ingestion_start"
    INGESTION_PROGRESS = "ingestion_progress"
    INGESTION_COMPLETE = "ingestion_complete"
    INGESTION_ERROR = "ingestion_error"

    # Query messages
    QUERY_START = "query_start"
    QUERY_CHUNK = "query_chunk"
    QUERY_COMPLETE = "query_complete"
    QUERY_ERROR = "query_error"

    # Status messages
    STATUS_UPDATE = "status_update"
    HEALTH_CHECK = "health_check"


class WebSocketConnection:
    """Represents a single WebSocket connection with metadata."""

    def __init__(
        self,
        websocket: WebSocket,
        connection_id: str,
        client_info: Optional[Dict[str, Any]] = None
    ):
        self.websocket = websocket
        self.connection_id = connection_id
        self.client_info = client_info or {}
        self.state = ConnectionState.CONNECTING
        self.connected_at = datetime.now()
        self.last_activity = datetime.now()
        self.messages_sent = 0
        self.messages_received = 0
        self.subscriptions: Set[str] = set()

    def to_dict(self) -> Dict[str, Any]:
        """Convert connection to dictionary."""
        return {
            "connection_id": self.connection_id,
            "state": self.state.value,
            "connected_at": self.connected_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "messages_sent": self.messages_sent,
            "messages_received": self.messages_received,
            "subscriptions": list(self.subscriptions),
            "client_info": self.client_info
        }


class ConnectionManager:
    """
    WebSocket connection manager with support for:
    - Multiple concurrent connections
    - Broadcasting to all/specific connections
    - Connection lifecycle management
    - Topic-based subscriptions
    - Connection health monitoring
    """

    def __init__(self):
        """Initialize the connection manager."""
        self.active_connections: Dict[str, WebSocketConnection] = {}
        self.topic_subscribers: Dict[str, Set[str]] = {}
        self._lock = asyncio.Lock()
        self._heartbeat_task: Optional[asyncio.Task] = None
        logger.info("ConnectionManager initialized")

    async def connect(
        self,
        websocket: WebSocket,
        connection_id: str,
        client_info: Optional[Dict[str, Any]] = None
    ) -> WebSocketConnection:
        """
        Accept and register a new WebSocket connection.

        Args:
            websocket: FastAPI WebSocket instance
            connection_id: Unique identifier for this connection
            client_info: Optional client metadata

        Returns:
            WebSocketConnection instance
        """
        try:
            await websocket.accept()

            connection = WebSocketConnection(
                websocket=websocket,
                connection_id=connection_id,
                client_info=client_info
            )
            connection.state = ConnectionState.CONNECTED

            async with self._lock:
                self.active_connections[connection_id] = connection

            logger.info(
                f"Connection established: {connection_id} "
                f"(total: {len(self.active_connections)})"
            )

            # Send welcome message
            await self.send_message(
                connection_id,
                {
                    "type": MessageType.CONNECT,
                    "connection_id": connection_id,
                    "timestamp": datetime.now().isoformat(),
                    "message": "Connected successfully"
                }
            )

            # Start heartbeat if not already running
            if not self._heartbeat_task or self._heartbeat_task.done():
                self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

            return connection

        except Exception as e:
            logger.error(f"Error connecting {connection_id}: {e}")
            raise

    async def disconnect(self, connection_id: str):
        """
        Disconnect and remove a WebSocket connection.

        Args:
            connection_id: Connection identifier to disconnect
        """
        async with self._lock:
            connection = self.active_connections.get(connection_id)

            if not connection:
                logger.warning(f"Connection not found: {connection_id}")
                return

            connection.state = ConnectionState.DISCONNECTING

            # Remove from topic subscriptions
            for topic in connection.subscriptions.copy():
                await self._unsubscribe_from_topic(connection_id, topic)

            # Close the WebSocket
            try:
                await connection.websocket.close()
            except Exception as e:
                logger.error(f"Error closing websocket {connection_id}: {e}")

            # Remove from active connections
            del self.active_connections[connection_id]
            connection.state = ConnectionState.DISCONNECTED

            logger.info(
                f"Connection closed: {connection_id} "
                f"(total: {len(self.active_connections)})"
            )

    async def send_message(
        self,
        connection_id: str,
        message: Dict[str, Any]
    ) -> bool:
        """
        Send a message to a specific connection.

        Args:
            connection_id: Target connection ID
            message: Message dictionary to send

        Returns:
            True if sent successfully, False otherwise
        """
        connection = self.active_connections.get(connection_id)

        if not connection:
            logger.warning(f"Connection not found: {connection_id}")
            return False

        try:
            # Ensure message has timestamp
            if "timestamp" not in message:
                message["timestamp"] = datetime.now().isoformat()

            await connection.websocket.send_json(message)
            connection.messages_sent += 1
            connection.last_activity = datetime.now()
            return True

        except WebSocketDisconnect:
            logger.warning(f"Client disconnected: {connection_id}")
            await self.disconnect(connection_id)
            return False
        except Exception as e:
            logger.error(f"Error sending message to {connection_id}: {e}")
            await self.disconnect(connection_id)
            return False

    async def send_text(
        self,
        connection_id: str,
        text: str
    ) -> bool:
        """
        Send raw text message to a connection.

        Args:
            connection_id: Target connection ID
            text: Text to send

        Returns:
            True if sent successfully
        """
        connection = self.active_connections.get(connection_id)

        if not connection:
            return False

        try:
            await connection.websocket.send_text(text)
            connection.messages_sent += 1
            connection.last_activity = datetime.now()
            return True
        except Exception as e:
            logger.error(f"Error sending text to {connection_id}: {e}")
            await self.disconnect(connection_id)
            return False

    async def broadcast(
        self,
        message: Dict[str, Any],
        exclude: Optional[List[str]] = None
    ):
        """
        Broadcast a message to all connected clients.

        Args:
            message: Message to broadcast
            exclude: Optional list of connection IDs to exclude
        """
        exclude = exclude or []

        tasks = []
        for connection_id in list(self.active_connections.keys()):
            if connection_id not in exclude:
                tasks.append(self.send_message(connection_id, message))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def broadcast_to_topic(
        self,
        topic: str,
        message: Dict[str, Any]
    ):
        """
        Broadcast message to all subscribers of a topic.

        Args:
            topic: Topic name
            message: Message to send
        """
        subscribers = self.topic_subscribers.get(topic, set())

        if not subscribers:
            logger.debug(f"No subscribers for topic: {topic}")
            return

        tasks = []
        for connection_id in list(subscribers):
            tasks.append(self.send_message(connection_id, message))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def subscribe_to_topic(
        self,
        connection_id: str,
        topic: str
    ) -> bool:
        """
        Subscribe a connection to a topic.

        Args:
            connection_id: Connection ID
            topic: Topic name

        Returns:
            True if subscribed successfully
        """
        connection = self.active_connections.get(connection_id)

        if not connection:
            logger.warning(f"Connection not found: {connection_id}")
            return False

        async with self._lock:
            if topic not in self.topic_subscribers:
                self.topic_subscribers[topic] = set()

            self.topic_subscribers[topic].add(connection_id)
            connection.subscriptions.add(topic)

        logger.info(f"Connection {connection_id} subscribed to topic: {topic}")
        return True

    async def _unsubscribe_from_topic(
        self,
        connection_id: str,
        topic: str
    ):
        """Internal method to unsubscribe from a topic."""
        if topic in self.topic_subscribers:
            self.topic_subscribers[topic].discard(connection_id)

            # Clean up empty topic
            if not self.topic_subscribers[topic]:
                del self.topic_subscribers[topic]

        connection = self.active_connections.get(connection_id)
        if connection:
            connection.subscriptions.discard(topic)

    async def unsubscribe_from_topic(
        self,
        connection_id: str,
        topic: str
    ) -> bool:
        """
        Unsubscribe a connection from a topic.

        Args:
            connection_id: Connection ID
            topic: Topic name

        Returns:
            True if unsubscribed successfully
        """
        async with self._lock:
            await self._unsubscribe_from_topic(connection_id, topic)

        logger.info(f"Connection {connection_id} unsubscribed from topic: {topic}")
        return True

    async def _heartbeat_loop(self):
        """Background task to send periodic heartbeats."""
        while self.active_connections:
            try:
                await asyncio.sleep(30)  # Send heartbeat every 30 seconds

                for connection_id in list(self.active_connections.keys()):
                    await self.send_message(
                        connection_id,
                        {
                            "type": MessageType.PING,
                            "timestamp": datetime.now().isoformat()
                        }
                    )

            except Exception as e:
                logger.error(f"Error in heartbeat loop: {e}")

    def get_connection(self, connection_id: str) -> Optional[WebSocketConnection]:
        """Get a connection by ID."""
        return self.active_connections.get(connection_id)

    def get_all_connections(self) -> List[WebSocketConnection]:
        """Get all active connections."""
        return list(self.active_connections.values())

    def get_connection_count(self) -> int:
        """Get the number of active connections."""
        return len(self.active_connections)

    def get_topic_subscribers(self, topic: str) -> List[str]:
        """Get all subscribers for a topic."""
        return list(self.topic_subscribers.get(topic, set()))

    def get_stats(self) -> Dict[str, Any]:
        """Get connection manager statistics."""
        total_messages_sent = sum(
            conn.messages_sent for conn in self.active_connections.values()
        )
        total_messages_received = sum(
            conn.messages_received for conn in self.active_connections.values()
        )

        return {
            "active_connections": len(self.active_connections),
            "topics": len(self.topic_subscribers),
            "total_messages_sent": total_messages_sent,
            "total_messages_received": total_messages_received,
            "connections": [
                conn.to_dict() for conn in self.active_connections.values()
            ]
        }


# Singleton instance
_connection_manager: Optional[ConnectionManager] = None


def get_connection_manager() -> ConnectionManager:
    """Get or create the connection manager singleton."""
    global _connection_manager
    if _connection_manager is None:
        _connection_manager = ConnectionManager()
    return _connection_manager
