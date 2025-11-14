from typing import List, Dict, Any
import asyncio
from pathlib import Path
import os

from app.services.embed.entity_extractor import EntityExtractor
from app.services.embed.multimodal_parser import MultimodalParser
from app.services.embed.neo4j_manager import Neo4jManager
from app.services.embed.pinecone_manager import PineconeManager
from app.utils.azure_downloader import AzureBlobDownloader
from app.models.embed import Entity, Relationship, DocumentChunk


class EmbedService:
    def __init__(self):
        self.pinecone_manager = PineconeManager()
        # COMMENTED OUT: Graph RAG components (for now, using only Pinecone RAG)
        # self.neo4j_manager = Neo4jManager()
        # self.entity_extractor = EntityExtractor()
        self.multimodal_parser = MultimodalParser()
        self.azure_downloader = AzureBlobDownloader()

    async def process_embed(self, user_id: str, azure_url: str) -> Dict[str, Any]:
        """
        Simplified RAG pipeline (Graph RAG components commented out):
        1. Download document from Azure
        2. Parse document (text, tables, images)
        3. Generate embeddings and store in Pinecone with user namespace
        """
        local_file_path = None
        
        try:
            print("="*80)
            print(f"🚀 STARTING RAG PIPELINE (Pinecone only)")
            print(f"👤 User: {user_id}")
            print(f"📄 Document: {azure_url}")
            print("="*80)
            
            # Step 1: Download document from Azure
            print("")
            print("STEP 1: Downloading document from Azure")
            print("-"*80)
            local_file_path = await self.azure_downloader.download_from_url(azure_url)
            print(f"✅ Document downloaded to: {local_file_path}")
            
            # Step 2: Parse document into chunks (text, tables, images)
            print("")
            print("STEP 2: Parsing document with multimodal parser")
            print("-"*80)
            chunks: List[DocumentChunk] = await self.multimodal_parser.parse_document(local_file_path)
            print(f"✅ Parsed {len(chunks)} chunks from document")
            
            # COMMENTED OUT: Entity extraction and graph building (using only Pinecone RAG for now)
            # # Step 3: Extract entities and relationships from each chunk
            # print("")
            # print("STEP 3: Extracting entities and relationships")
            # print("-"*80)
            # print(f"📊 Total chunks to process: {len(chunks)}")
            # all_entities: List[Entity] = []
            # all_relationships: List[Relationship] = []
            # 
            # # Process all chunks in parallel
            # print(f"🔄 Processing {len(chunks)} chunks in parallel...")
            # 
            # extraction_tasks = [
            #     self.entity_extractor.extract(chunk) 
            #     for chunk in chunks
            # ]
            # extraction_results = await asyncio.gather(*extraction_tasks)
            # 
            # # Collect results
            # for entities, relationships in extraction_results:
            #     all_entities.extend(entities)
            #     all_relationships.extend(relationships)
            # 
            # print(f"🎉 Extraction complete! Total: {len(all_entities)} entities and {len(all_relationships)} relationships")
            
            # Step 3: Generate embeddings for chunks (BATCHED to prevent thread exhaustion)
            print("")
            print("STEP 3: Generating embeddings for chunks")
            print("-"*80)
            print(f"📊 Embedding {len(chunks)} chunks")
            
            embedding_tasks = []
            
            # Add chunk embedding tasks
            for chunk in chunks:
                if not chunk.embedding:
                    embedding_tasks.append((chunk, chunk.content, "chunk"))
            
            print(f"   Processing {len(embedding_tasks)} embeddings in batches...")
            
            # Process embeddings in batches with semaphore to limit concurrent operations
            # This prevents thread exhaustion when processing thousands of embeddings
            if embedding_tasks:
                # Semaphore limits concurrent embedding operations (50 at a time)
                semaphore = asyncio.Semaphore(50)
                batch_size = 100  # Process 100 embeddings per batch
                
                async def get_embedding_wrapper(item, text):
                    async with semaphore:  # Limit concurrent operations
                        return item, await self.pinecone_manager.get_embedding(text)
                
                # Process in batches to avoid overwhelming the system
                total_batches = (len(embedding_tasks) + batch_size - 1) // batch_size
                all_results = []
                
                for batch_idx in range(0, len(embedding_tasks), batch_size):
                    batch = embedding_tasks[batch_idx:batch_idx + batch_size]
                    current_batch_num = (batch_idx // batch_size) + 1
                    
                    print(f"   Processing batch {current_batch_num}/{total_batches} ({len(batch)} embeddings)...")
                    
                    batch_results = await asyncio.gather(*[
                        get_embedding_wrapper(item, text) 
                        for item, text, _ in batch
                    ])
                    
                    all_results.extend(batch_results)
                
                # Assign embeddings back
                for item, embedding in all_results:
                    item.embedding = embedding
            
            print(f"✅ All embeddings generated! ({len([c for c in chunks if c.embedding])} chunks)")
            
            # COMMENTED OUT: Neo4j graph storage (using only Pinecone RAG for now)
            # # Step 5: Store in Neo4j (graph database)
            # print("")
            # print("STEP 5: Storing in Neo4j graph database")
            # print("-"*80)
            # print("🔧 Creating Neo4j indexes...")
            # await self.neo4j_manager.create_indexes()
            # print(f"📤 Upserting {len(all_entities)} entities and {len(all_relationships)} relationships...")
            # print(f"📤 User namespace: {user_id}")
            # await self.neo4j_manager.batch_insert(all_entities, all_relationships, user_id=user_id)
            # print("✅ Graph data stored in Neo4j with user isolation")
            
            # Step 4: Store embeddings in Pinecone with user namespace
            print("")
            print("STEP 4: Storing embeddings in Pinecone vector database")
            print("-"*80)
            print(f"📤 Namespace: {user_id}")
            print(f"📤 Upserting {len(chunks)} chunks to Pinecone...")
            await self.pinecone_manager.upsert_chunks(chunks, namespace=user_id)
            print("✅ Embeddings stored in Pinecone")
            
            # Prepare response
            result = {
                "user_id": user_id,
                "azure_url": azure_url,
                "status": "success",
                "embeddings": {
                    "total_chunks": len(chunks),
                    # "total_entities": len(all_entities),  # Commented out - no graph for now
                    # "total_relationships": len(all_relationships),  # Commented out - no graph for now
                    "chunks_by_type": {
                        "text": sum(1 for c in chunks if c.content_type == "text"),
                        "image": sum(1 for c in chunks if c.content_type == "image"),
                        "table": sum(1 for c in chunks if c.content_type == "table"),
                        "chart": sum(1 for c in chunks if c.content_type == "chart")
                    }
                }
            }
            
            print("")
            print("="*80)
            print("✅ PIPELINE COMPLETED SUCCESSFULLY!")
            print("="*80)
            print(f"📊 Summary:")
            print(f"   - User: {user_id}")
            print(f"   - Chunks: {len(chunks)}")
            # print(f"   - Entities: {len(all_entities)}")  # Commented out - no graph for now
            # print(f"   - Relationships: {len(all_relationships)}")  # Commented out - no graph for now
            print("="*80)
            return result
            
        except Exception as e:
            print("")
            print("="*80)
            print("❌ PIPELINE FAILED!")
            print("="*80)
            print(f"Error: {str(e)}")
            print("="*80)
            import traceback
            traceback.print_exc()
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
                    print(f"Cleaned up temporary file: {local_file_path}")
                except Exception as e:
                    print(f"Could not delete temporary file {local_file_path}: {str(e)}")


def get_embed_service() -> EmbedService:
    return EmbedService()