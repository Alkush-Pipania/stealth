from pinecone import Pinecone, ServerlessSpec
from typing import List, Dict, Any
from google import genai
from google.genai import types
import asyncio
from concurrent.futures import ThreadPoolExecutor

from app.models.embed import DocumentChunk
from app.config import get_settings

settings = get_settings()

class PineconeManager:
    def __init__(self):
        self.pc = Pinecone(api_key=settings.PINECONE_API_KEY)
        self.index_name = settings.INDEX
        
        # Initialize native Google GenAI client for embeddings with full control
        self.genai_client = genai.Client(api_key=settings.GOOGLE_API_KEY)
        
        # Shared thread pool executor with limited workers to prevent thread exhaustion
        # Max 50 concurrent threads for embeddings (adjust based on your system)
        self.executor = ThreadPoolExecutor(max_workers=50, thread_name_prefix="embedding")
        
        # Create index if not exists
        self._ensure_index()
        self.index = self.pc.Index(self.index_name)
    
    def close(self):
        """Cleanup: shutdown the thread pool executor"""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=True)
    
    def _ensure_index(self):
        """Create Pinecone index if it doesn't exist"""
        if self.index_name not in self.pc.list_indexes().names():
            print(f"Creating Pinecone index: {self.index_name}")
            self.pc.create_index(
                name=self.index_name,
                dimension=settings.EMBEDDING_DIM,  # Should be integer, not string
                metric="cosine",
                spec=ServerlessSpec(
                    cloud="aws",
                    region=settings.pinecone_environment
                )
            )
    
    async def get_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using Gemini with specified dimensions"""
        loop = asyncio.get_event_loop()
        
        # Use native Google GenAI SDK with output_dimensionality control
        def embed_with_dimensions():
            result = self.genai_client.models.embed_content(
                model=settings.EMBEDDING_MODEL,
                contents=text,
                config=types.EmbedContentConfig(
                    output_dimensionality=settings.EMBEDDING_DIM,
                    task_type="retrieval_document"
                )
            )
            return result.embeddings[0].values
        
        return await loop.run_in_executor(self.executor, embed_with_dimensions)
    
    async def upsert_chunks(self, chunks: List[DocumentChunk], namespace: str = ""):
        """Upsert document chunks with embeddings to a specific namespace"""
        try:
            vectors = []
            for chunk in chunks:
                # Embedding should already be generated before calling upsert_chunks
                if not chunk.embedding:
                    chunk.embedding = await self.get_embedding(chunk.content)
                
                vectors.append({
                    "id": chunk.id,
                    "values": chunk.embedding,
                    "metadata": {
                        "content": chunk.content[:1000],  # Truncate for metadata
                        "content_type": chunk.content_type,
                        "source": chunk.metadata.get("source", ""),
                        "page": chunk.metadata.get("page", 0),
                        **chunk.metadata
                    }
                })
            
            # Upsert in batches
            batch_size = 100
            for i in range(0, len(vectors), batch_size):
                batch = vectors[i:i+batch_size]
                self.index.upsert(vectors=batch, namespace=namespace)
            
            print(f"Upserted {len(vectors)} vectors to Pinecone namespace: {namespace}")
            
        except Exception as e:
            print(f"Error upserting to Pinecone: {str(e)}")
            raise
    