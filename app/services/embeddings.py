"""Embeddings service using Google Gemini (768 dimensions, cosine similarity)."""
import logging
from typing import List, Optional
import google.generativeai as genai
from app.config import settings

logger = logging.getLogger(__name__)


class EmbeddingsService:
    """Service for generating embeddings using Google Gemini."""

    def __init__(self):
        """Initialize Gemini embeddings service."""
        self._initialize_gemini()

    def _initialize_gemini(self):
        """Initialize Gemini client."""
        try:
            if not settings.GOOGLE_API_KEY:
                logger.warning("Google API key not provided")
                raise ValueError("Google API key is required for embeddings")

            genai.configure(api_key=settings.GOOGLE_API_KEY)
            logger.info(f"Gemini embeddings service initialized with model: {settings.GEMINI_EMBEDDING_MODEL}")

        except Exception as e:
            logger.error(f"Failed to initialize Gemini: {e}")
            raise

    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Text to embed

        Returns:
            768-dimensional embedding vector

        Raises:
            Exception: If embedding generation fails
        """
        try:
            if not text or not text.strip():
                logger.warning("Empty text provided for embedding")
                return [0.0] * settings.GEMINI_EMBEDDING_DIMENSION

            # Generate embedding using Gemini
            result = genai.embed_content(
                model=settings.GEMINI_EMBEDDING_MODEL,
                content=text,
                task_type="retrieval_document"
            )

            embedding = result['embedding']

            # Verify dimension
            if len(embedding) != settings.GEMINI_EMBEDDING_DIMENSION:
                logger.warning(
                    f"Unexpected embedding dimension: {len(embedding)}, "
                    f"expected {settings.GEMINI_EMBEDDING_DIMENSION}"
                )

            return embedding

        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of 768-dimensional embedding vectors
        """
        embeddings = []

        for i, text in enumerate(texts):
            try:
                embedding = self.embed_text(text)
                embeddings.append(embedding)

                if (i + 1) % 10 == 0:
                    logger.info(f"Generated embeddings for {i + 1}/{len(texts)} texts")

            except Exception as e:
                logger.error(f"Error embedding text {i}: {e}")
                # Add zero vector as fallback
                embeddings.append([0.0] * settings.GEMINI_EMBEDDING_DIMENSION)

        logger.info(f"Generated {len(embeddings)} embeddings")
        return embeddings

    def embed_query(self, query: str) -> List[float]:
        """
        Generate embedding for a query.

        Args:
            query: Query text to embed

        Returns:
            768-dimensional embedding vector
        """
        try:
            if not query or not query.strip():
                logger.warning("Empty query provided for embedding")
                return [0.0] * settings.GEMINI_EMBEDDING_DIMENSION

            # Generate embedding with query task type
            result = genai.embed_content(
                model=settings.GEMINI_EMBEDDING_MODEL,
                content=query,
                task_type="retrieval_query"
            )

            embedding = result['embedding']

            # Verify dimension
            if len(embedding) != settings.GEMINI_EMBEDDING_DIMENSION:
                logger.warning(
                    f"Unexpected embedding dimension: {len(embedding)}, "
                    f"expected {settings.GEMINI_EMBEDDING_DIMENSION}"
                )

            return embedding

        except Exception as e:
            logger.error(f"Error generating query embedding: {e}")
            raise

    def get_dimension(self) -> int:
        """Get embedding dimension."""
        return settings.GEMINI_EMBEDDING_DIMENSION


# Singleton instance
_embeddings_service: Optional[EmbeddingsService] = None


def get_embeddings_service() -> EmbeddingsService:
    """Get or create embeddings service instance."""
    global _embeddings_service
    if _embeddings_service is None:
        _embeddings_service = EmbeddingsService()
    return _embeddings_service
