"""Pinecone vector store service for similarity search."""
import logging
from typing import List, Dict, Any, Optional
import time
from pinecone import Pinecone, ServerlessSpec
from app.config import settings

logger = logging.getLogger(__name__)


class VectorStoreService:
    """Service for managing Pinecone vector store."""

    def __init__(self):
        """Initialize Pinecone vector store."""
        self.pc = None
        self.index = None
        self._initialize_pinecone()

    def _initialize_pinecone(self):
        """Initialize Pinecone client and index."""
        try:
            if not settings.PINECONE_API_KEY:
                logger.warning("Pinecone API key not provided")
                raise ValueError("Pinecone API key is required")

            # Initialize Pinecone
            self.pc = Pinecone(api_key=settings.PINECONE_API_KEY)

            # Check if index exists, create if not
            index_name = settings.PINECONE_INDEX_NAME

            if index_name not in self.pc.list_indexes().names():
                logger.info(f"Creating Pinecone index: {index_name}")
                self.pc.create_index(
                    name=index_name,
                    dimension=settings.PINECONE_DIMENSION,
                    metric=settings.PINECONE_METRIC,
                    spec=ServerlessSpec(
                        cloud="aws",
                        region=settings.PINECONE_ENVIRONMENT or "us-east-1"
                    )
                )
                # Wait for index to be ready
                time.sleep(1)

            # Connect to index
            self.index = self.pc.Index(index_name)
            logger.info(f"Connected to Pinecone index: {index_name}")

        except Exception as e:
            logger.error(f"Failed to initialize Pinecone: {e}")
            raise

    def upsert_vectors(
        self,
        vectors: List[Dict[str, Any]],
        namespace: str = ""
    ) -> Dict[str, Any]:
        """
        Upsert vectors to Pinecone.

        Args:
            vectors: List of vector dictionaries with 'id', 'values', and 'metadata'
            namespace: Optional namespace for organizing vectors

        Returns:
            Upsert response
        """
        try:
            if not vectors:
                logger.warning("No vectors to upsert")
                return {"upserted_count": 0}

            logger.info(f"Upserting {len(vectors)} vectors to namespace '{namespace}'")

            # Batch upsert
            batch_size = 100
            upserted_count = 0

            for i in range(0, len(vectors), batch_size):
                batch = vectors[i:i + batch_size]
                response = self.index.upsert(
                    vectors=batch,
                    namespace=namespace
                )
                upserted_count += response.get('upserted_count', len(batch))

                if (i + batch_size) % 500 == 0:
                    logger.info(f"Upserted {i + batch_size}/{len(vectors)} vectors")

            logger.info(f"Successfully upserted {upserted_count} vectors")

            return {"upserted_count": upserted_count}

        except Exception as e:
            logger.error(f"Error upserting vectors: {e}")
            raise

    def query_vectors(
        self,
        query_vector: List[float],
        top_k: int = 10,
        namespace: str = "",
        filter: Optional[Dict[str, Any]] = None,
        include_metadata: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Query similar vectors from Pinecone.

        Args:
            query_vector: Query embedding vector
            top_k: Number of results to return
            namespace: Optional namespace to query
            filter: Optional metadata filter
            include_metadata: Whether to include metadata in results

        Returns:
            List of matching results with scores
        """
        try:
            logger.info(f"Querying Pinecone for top {top_k} similar vectors")

            response = self.index.query(
                vector=query_vector,
                top_k=top_k,
                namespace=namespace,
                filter=filter,
                include_metadata=include_metadata
            )

            results = []
            for match in response.get('matches', []):
                results.append({
                    'id': match['id'],
                    'score': match['score'],
                    'metadata': match.get('metadata', {})
                })

            logger.info(f"Found {len(results)} similar vectors")
            return results

        except Exception as e:
            logger.error(f"Error querying vectors: {e}")
            raise

    def delete_vectors(
        self,
        ids: Optional[List[str]] = None,
        namespace: str = "",
        delete_all: bool = False
    ):
        """
        Delete vectors from Pinecone.

        Args:
            ids: List of vector IDs to delete
            namespace: Namespace to delete from
            delete_all: If True, delete all vectors in namespace
        """
        try:
            if delete_all:
                logger.warning(f"Deleting all vectors in namespace '{namespace}'")
                self.index.delete(delete_all=True, namespace=namespace)
            elif ids:
                logger.info(f"Deleting {len(ids)} vectors")
                self.index.delete(ids=ids, namespace=namespace)
            else:
                logger.warning("No IDs provided and delete_all is False")

        except Exception as e:
            logger.error(f"Error deleting vectors: {e}")
            raise

    def get_index_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the index.

        Returns:
            Index statistics
        """
        try:
            stats = self.index.describe_index_stats()
            logger.info(f"Index stats: {stats}")
            return stats
        except Exception as e:
            logger.error(f"Error getting index stats: {e}")
            raise

    def fetch_vectors(
        self,
        ids: List[str],
        namespace: str = ""
    ) -> Dict[str, Any]:
        """
        Fetch specific vectors by ID.

        Args:
            ids: List of vector IDs to fetch
            namespace: Namespace to fetch from

        Returns:
            Dictionary of vectors
        """
        try:
            logger.info(f"Fetching {len(ids)} vectors")
            response = self.index.fetch(ids=ids, namespace=namespace)
            return response.get('vectors', {})
        except Exception as e:
            logger.error(f"Error fetching vectors: {e}")
            raise


# Singleton instance
_vector_store_service: Optional[VectorStoreService] = None


def get_vector_store_service() -> VectorStoreService:
    """Get or create vector store service instance."""
    global _vector_store_service
    if _vector_store_service is None:
        _vector_store_service = VectorStoreService()
    return _vector_store_service
