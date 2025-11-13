from typing import List, Dict, Any
import asyncio
from pathlib import Path
import os

from app.services.embed.entity_extractor import EntityExtractor
from app.services.embed.multimodal_parser import MultimodalParser
from app.services.embed.neo4j_manager import Neo4jManager
from app.services.embed.pinecone_manager import PineconeManager
from app.utils.azure_downloader import AzureBlobDownloader
from app.utils.logger import setup_logger
from app.models.embed import Entity, Relationship, DocumentChunk

logger = setup_logger(__name__)


class EmbedService:
    def __init__(self):
        self.pinecone_manager = PineconeManager()
        self.neo4j_manager = Neo4jManager()
        self.multimodal_parser = MultimodalParser()
        self.entity_extractor = EntityExtractor()
        self.azure_downloader = AzureBlobDownloader()

    async def process_embed(self, user_id: str, azure_url: str) -> Dict[str, Any]:
        """
        Complete Graph RAG pipeline:
        1. Download document from Azure
        2. Parse document (text, tables, images)
        3. Extract entities and relationships
        4. Store in Neo4j graph database
        5. Generate embeddings and store in Pinecone with user namespace
        """
        local_file_path = None
        
        try:
            logger.info(f"Starting embed pipeline for user: {user_id}, URL: {azure_url}")
            
            # Step 1: Download document from Azure
            logger.info("Step 1: Downloading document from Azure...")
            local_file_path = await self.azure_downloader.download_from_url(azure_url)
            logger.info(f"Document downloaded to: {local_file_path}")
            
            # Step 2: Parse document into chunks (text, tables, images)
            logger.info("Step 2: Parsing document with multimodal parser...")
            chunks: List[DocumentChunk] = await self.multimodal_parser.parse_document(local_file_path)
            logger.info(f"Parsed {len(chunks)} chunks from document")
            
            # Step 3: Extract entities and relationships from each chunk
            logger.info("Step 3: Extracting entities and relationships...")
            all_entities: List[Entity] = []
            all_relationships: List[Relationship] = []
            
            # Process chunks in parallel for better performance
            extraction_tasks = [
                self.entity_extractor.extract(chunk) 
                for chunk in chunks
            ]
            extraction_results = await asyncio.gather(*extraction_tasks)
            
            for entities, relationships in extraction_results:
                all_entities.extend(entities)
                all_relationships.extend(relationships)
            
            logger.info(f"Extracted {len(all_entities)} entities and {len(all_relationships)} relationships")
            
            # Step 4: Generate embeddings for chunks
            logger.info("Step 4: Generating embeddings for chunks...")
            for chunk in chunks:
                if not chunk.embedding:
                    chunk.embedding = self.pinecone_manager.get_embedding(chunk.content)
            
            # Generate embeddings for entities
            for entity in all_entities:
                if not entity.embedding:
                    entity_text = f"{entity.name} ({entity.type}): {entity.properties}"
                    entity.embedding = self.pinecone_manager.get_embedding(entity_text)
            
            logger.info("Embeddings generated for all chunks and entities")
            
            # Step 5: Store in Neo4j (graph database)
            logger.info("Step 5: Storing entities and relationships in Neo4j...")
            await self.neo4j_manager.create_indexes()
            await self.neo4j_manager.batch_insert(all_entities, all_relationships)
            logger.info("Successfully stored graph data in Neo4j")
            
            # Step 6: Store embeddings in Pinecone with user namespace
            logger.info(f"Step 6: Storing embeddings in Pinecone (namespace: {user_id})...")
            await self.pinecone_manager.upsert_chunks(chunks, namespace=user_id)
            logger.info("Successfully stored embeddings in Pinecone")
            
            # Prepare response
            result = {
                "user_id": user_id,
                "azure_url": azure_url,
                "status": "success",
                "embeddings": {
                    "total_chunks": len(chunks),
                    "total_entities": len(all_entities),
                    "total_relationships": len(all_relationships),
                    "chunks_by_type": {
                        "text": sum(1 for c in chunks if c.content_type == "text"),
                        "image": sum(1 for c in chunks if c.content_type == "image"),
                        "table": sum(1 for c in chunks if c.content_type == "table"),
                        "chart": sum(1 for c in chunks if c.content_type == "chart")
                    }
                }
            }
            
            logger.info(f"Pipeline completed successfully for user: {user_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error in embed pipeline: {str(e)}", exc_info=True)
            return {
                "user_id": user_id,
                "azure_url": azure_url,
                "status": "failed",
                "error": str(e),
                "embeddings": None
            }
        
        finally:
            # Cleanup: Remove temporary downloaded file
            if local_file_path and os.path.exists(local_file_path):
                try:
                    os.remove(local_file_path)
                    logger.info(f"Cleaned up temporary file: {local_file_path}")
                except Exception as e:
                    logger.warning(f"Could not delete temporary file {local_file_path}: {str(e)}")


def get_embed_service() -> EmbedService:
    return EmbedService()