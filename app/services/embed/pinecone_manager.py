from pinecone import Pinecone, ServerlessSpec
from typing import List, Dict, Any
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from app.models.embed import DocumentChunk
from app.utils.logger import setup_logger
from app.config import get_settings

logger = setup_logger(__name__)
settings = get_settings()

class PineconeManager:
    def __init__(self):
        self.pc = Pinecone(api_key=settings.PINECONE_API_KEY)
        self.index_name = settings.INDEX
        
        # Initialize Gemini embeddings using LangChain
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model=settings.EMBEDDING_MODEL,
            google_api_key=settings.GOOGLE_API_KEY
        )
        
        # Create index if not exists
        self._ensure_index()
        self.index = self.pc.Index(self.index_name)
    
    def _ensure_index(self):
        """Create Pinecone index if it doesn't exist"""
        if self.index_name not in self.pc.list_indexes().names():
            logger.info(f"Creating Pinecone index: {self.index_name}")
            self.pc.create_index(
                name=self.index_name,
                dimension=str(settings.EMBEDDING_DIM),
                metric="cosine",
                spec=ServerlessSpec(
                    cloud="aws",
                    region=settings.pinecone_environment
                )
            )
    
    def get_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using Gemini"""
        return self.embeddings.embed_query(text)
    
    async def upsert_chunks(self, chunks: List[DocumentChunk], namespace: str = ""):
        """Upsert document chunks with embeddings to a specific namespace"""
        try:
            vectors = []
            for chunk in chunks:
                # Generate embedding if not exists
                if not chunk.embedding:
                    chunk.embedding = self.get_embedding(chunk.content)
                
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
            
            logger.info(f"Upserted {len(vectors)} vectors to Pinecone namespace: {namespace}")
            
        except Exception as e:
            logger.error(f"Error upserting to Pinecone: {str(e)}")
            raise
    
    async def search(
        self, 
        query: str, 
        top_k: int = 10,
        filter_dict: Dict[str, Any] = None,
        namespace: str = ""
    ) -> List[Dict]:
        """Search for similar chunks in a specific namespace"""
        query_embedding = self.get_embedding(query)
        
        results = self.index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True,
            filter=filter_dict,
            namespace=namespace
        )
        
        return [
            {
                "id": match["id"],
                "score": match["score"],
                "metadata": match["metadata"]
            }
            for match in results["matches"]
        ]