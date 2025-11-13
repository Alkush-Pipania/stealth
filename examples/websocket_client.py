"""
WebSocket client example for Graph RAG API.

Demonstrates real-time document ingestion and query streaming.
"""
import asyncio
import json
import uuid
from typing import Optional, Callable, Dict, Any
import websockets
from datetime import datetime


class GraphRAGWebSocketClient:
    """WebSocket client for Graph RAG API."""

    def __init__(
        self,
        url: str = "ws://localhost:8000/api/v1/ws",
        client_id: Optional[str] = None,
        client_name: Optional[str] = None
    ):
        """
        Initialize WebSocket client.

        Args:
            url: WebSocket URL
            client_id: Optional client identifier
            client_name: Optional client name
        """
        self.url = url
        self.client_id = client_id or str(uuid.uuid4())
        self.client_name = client_name or "PythonClient"
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.is_connected = False

        # Add client info to URL
        self.full_url = f"{url}?client_id={self.client_id}&client_name={self.client_name}"

        # Message handlers
        self.message_handlers: Dict[str, Callable] = {}

    async def connect(self):
        """Connect to WebSocket server."""
        try:
            self.websocket = await websockets.connect(self.full_url)
            self.is_connected = True
            print(f"Connected to {self.url}")
            print(f"Client ID: {self.client_id}")

            # Wait for connection confirmation
            welcome_msg = await self.websocket.recv()
            print(f"Server: {welcome_msg}")

        except Exception as e:
            print(f"Connection error: {e}")
            raise

    async def disconnect(self):
        """Disconnect from server."""
        if self.websocket and self.is_connected:
            await self.websocket.close()
            self.is_connected = False
            print("Disconnected from server")

    async def send_message(self, message: Dict[str, Any]):
        """Send a message to the server."""
        if not self.websocket or not self.is_connected:
            raise Exception("Not connected to server")

        await self.websocket.send(json.dumps(message))

    async def receive_messages(self):
        """Receive and handle messages from server."""
        try:
            while self.is_connected:
                message_str = await self.websocket.recv()
                message = json.loads(message_str)

                # Get message type
                msg_type = message.get("type")

                # Call registered handler if available
                handler = self.message_handlers.get(msg_type)
                if handler:
                    await handler(message)
                else:
                    # Default handler
                    await self.default_handler(message)

        except websockets.exceptions.ConnectionClosed:
            print("Connection closed by server")
            self.is_connected = False
        except Exception as e:
            print(f"Error receiving messages: {e}")
            self.is_connected = False

    def register_handler(self, message_type: str, handler: Callable):
        """Register a message handler."""
        self.message_handlers[message_type] = handler

    async def default_handler(self, message: Dict[str, Any]):
        """Default message handler."""
        msg_type = message.get("type")
        timestamp = message.get("timestamp", "")
        print(f"[{timestamp}] {msg_type}: {message}")

    async def ingest_document(
        self,
        file_url: str,
        metadata: Optional[Dict[str, Any]] = None,
        stream_progress: bool = True
    ) -> str:
        """
        Request document ingestion with streaming progress.

        Args:
            file_url: URL to document
            metadata: Optional metadata
            stream_progress: Stream progress updates

        Returns:
            Request ID
        """
        request_id = str(uuid.uuid4())

        message = {
            "type": "ingest_request",
            "request_id": request_id,
            "file_url": file_url,
            "metadata": metadata or {},
            "stream_progress": stream_progress
        }

        await self.send_message(message)
        print(f"Ingestion requested: {file_url}")
        print(f"Request ID: {request_id}")

        return request_id

    async def query(
        self,
        query: str,
        top_k: int = 10,
        use_graph: bool = True,
        stream_results: bool = True
    ) -> str:
        """
        Execute a query with streaming results.

        Args:
            query: Query text
            top_k: Number of results
            use_graph: Use graph enhancement
            stream_results: Stream results

        Returns:
            Request ID
        """
        request_id = str(uuid.uuid4())

        message = {
            "type": "query_request",
            "request_id": request_id,
            "query": query,
            "top_k": top_k,
            "use_graph": use_graph,
            "stream_results": stream_results
        }

        await self.send_message(message)
        print(f"Query sent: {query}")
        print(f"Request ID: {request_id}")

        return request_id

    async def subscribe(self, topic: str):
        """Subscribe to a topic."""
        message = {
            "type": "subscribe",
            "topic": topic
        }

        await self.send_message(message)
        print(f"Subscribed to topic: {topic}")

    async def unsubscribe(self, topic: str):
        """Unsubscribe from a topic."""
        message = {
            "type": "unsubscribe",
            "topic": topic
        }

        await self.send_message(message)
        print(f"Unsubscribed from topic: {topic}")

    async def ping(self):
        """Send ping to server."""
        message = {
            "type": "ping",
            "timestamp": datetime.now().isoformat()
        }

        await self.send_message(message)


async def main():
    """Example usage of WebSocket client."""
    # Create client
    client = GraphRAGWebSocketClient(
        url="ws://localhost:8000/api/v1/ws",
        client_name="ExampleClient"
    )

    # Register custom handlers
    async def handle_progress(message):
        """Handle ingestion progress updates."""
        stage = message.get("stage")
        progress = message.get("progress", 0)
        msg = message.get("message", "")
        print(f"Progress [{stage}]: {progress:.1f}% - {msg}")

    async def handle_ingestion_complete(message):
        """Handle ingestion completion."""
        print("\n" + "=" * 60)
        print("INGESTION COMPLETED")
        print("=" * 60)
        print(f"Document ID: {message.get('document_id')}")
        print(f"File: {message.get('file_name')}")
        print(f"Time: {message.get('processing_time_seconds')}s")
        print(f"Chunks: {message.get('chunks_created')}")
        print(f"Images: {message.get('images_extracted')}")
        print(f"Entities: {message.get('entities_extracted')}")
        print("=" * 60 + "\n")

    async def handle_query_chunk(message):
        """Handle query result chunk."""
        chunk_idx = message.get("chunk_index")
        result = message.get("result", {})
        is_final = message.get("is_final", False)

        print(f"\nResult {chunk_idx + 1}:")
        print(f"  Score: {result.get('score', 0):.4f}")
        print(f"  Text: {result.get('text', '')[:150]}...")

        if is_final:
            print("\n--- All results received ---\n")

    async def handle_query_complete(message):
        """Handle query completion."""
        print("\n" + "=" * 60)
        print("QUERY COMPLETED")
        print("=" * 60)
        print(f"Query: {message.get('query')}")
        print(f"Total Results: {message.get('total_results')}")
        print(f"Entities: {message.get('num_entities')}")
        print(f"Graph Enhanced: {message.get('graph_enhanced')}")
        print("=" * 60 + "\n")

    async def handle_error(message):
        """Handle error messages."""
        print(f"\nERROR: {message.get('error')}")
        if message.get('details'):
            print(f"Details: {message.get('details')}")
        print()

    # Register handlers
    client.register_handler("ingestion_progress", handle_progress)
    client.register_handler("ingestion_completed", handle_ingestion_complete)
    client.register_handler("query_chunk", handle_query_chunk)
    client.register_handler("query_completed", handle_query_complete)
    client.register_handler("error", handle_error)

    try:
        # Connect
        await client.connect()

        # Start message receiver in background
        receive_task = asyncio.create_task(client.receive_messages())

        print("\n" + "=" * 60)
        print("WebSocket Client Connected")
        print("=" * 60 + "\n")

        # Example 1: Ingest a document
        print("Example 1: Document Ingestion with Progress Streaming")
        print("-" * 60)

        await client.ingest_document(
            file_url="https://yourstorage.blob.core.windows.net/documents/sample.pdf",
            metadata={
                "title": "Sample Document",
                "author": "Test Author",
                "category": "test"
            },
            stream_progress=True
        )

        # Wait for ingestion to complete
        await asyncio.sleep(15)

        # Example 2: Query with streaming results
        print("\n\nExample 2: Query with Streaming Results")
        print("-" * 60)

        await client.query(
            query="What are the main conclusions?",
            top_k=5,
            use_graph=True,
            stream_results=True
        )

        # Wait for query to complete
        await asyncio.sleep(5)

        # Example 3: Topic subscription
        print("\n\nExample 3: Topic Subscription")
        print("-" * 60)

        await client.subscribe("system_updates")
        await asyncio.sleep(2)

        # Example 4: Ping
        print("\n\nExample 4: Ping/Pong")
        print("-" * 60)

        await client.ping()
        await asyncio.sleep(1)

        # Keep connection alive for a bit
        print("\nKeeping connection alive for 5 seconds...")
        await asyncio.sleep(5)

        # Clean up
        receive_task.cancel()
        await client.disconnect()

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        await client.disconnect()
    except Exception as e:
        print(f"\nError: {e}")
        await client.disconnect()


if __name__ == "__main__":
    print("""
╔════════════════════════════════════════════════════════════╗
║        Graph RAG WebSocket Client Example                  ║
╚════════════════════════════════════════════════════════════╝

This example demonstrates:
  1. Real-time document ingestion with progress updates
  2. Streaming query results
  3. Topic subscriptions
  4. Bidirectional communication

Make sure the API server is running:
  docker-compose up -d
  OR
  uvicorn app.main:app --reload

""")

    asyncio.run(main())
