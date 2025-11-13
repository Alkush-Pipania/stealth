"""Graph RAG ingestion pipeline."""
import logging
import hashlib
import re
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.services.azure_storage import get_azure_storage_service
from app.services.document_parser import get_document_parser_service
from app.services.embeddings import get_embeddings_service
from app.services.vector_store import get_vector_store_service
from app.services.graph_store import get_graph_store_service

logger = logging.getLogger(__name__)


class GraphRAGIngestionPipeline:
    """Pipeline for ingesting documents into Graph RAG system."""

    def __init__(self):
        """Initialize the ingestion pipeline."""
        self.storage_service = get_azure_storage_service()
        self.parser_service = get_document_parser_service()
        self.embeddings_service = get_embeddings_service()
        self.vector_store = get_vector_store_service()
        self.graph_store = get_graph_store_service()

    async def ingest_document(
        self,
        file_url: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Ingest a document into the Graph RAG system.

        Args:
            file_url: URL or path to the document in Azure Blob Storage
            metadata: Optional metadata about the document

        Returns:
            Ingestion results
        """
        try:
            logger.info(f"Starting ingestion for: {file_url}")
            start_time = datetime.now()

            # Step 1: Download document from Azure Blob Storage
            logger.info("Step 1: Downloading document from Azure Blob Storage")
            file_content = self.storage_service.download_blob_from_url(file_url)

            # Extract filename
            file_name = file_url.split('/')[-1].split('?')[0]
            doc_id = self._generate_doc_id(file_url)

            # Step 2: Parse document with LlamaParse (multi-modal)
            logger.info("Step 2: Parsing document with LlamaParse")
            parsed_data = await self.parser_service.parse_document(
                file_content=file_content,
                file_name=file_name,
                extract_images=True
            )

            # Step 3: Extract entities and relationships
            logger.info("Step 3: Extracting entities and relationships")
            entities, relationships = await self._extract_entities_and_relationships(
                parsed_data
            )

            # Step 4: Generate embeddings
            logger.info("Step 4: Generating embeddings for text chunks")
            embeddings_data = await self._generate_embeddings(
                doc_id=doc_id,
                text_nodes=parsed_data['text_nodes'],
                image_nodes=parsed_data['image_nodes']
            )

            # Step 5: Store in Pinecone
            logger.info("Step 5: Storing embeddings in Pinecone")
            self.vector_store.upsert_vectors(
                vectors=embeddings_data['vectors'],
                namespace=doc_id
            )

            # Step 6: Build knowledge graph in Neo4j
            logger.info("Step 6: Building knowledge graph in Neo4j")
            graph_stats = await self._build_knowledge_graph(
                doc_id=doc_id,
                file_name=file_name,
                metadata=metadata or {},
                chunks=embeddings_data['chunks'],
                entities=entities,
                relationships=relationships
            )

            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()

            result = {
                "status": "success",
                "document_id": doc_id,
                "file_name": file_name,
                "processing_time_seconds": processing_time,
                "chunks_created": len(parsed_data['text_nodes']),
                "images_extracted": len(parsed_data['image_nodes']),
                "entities_extracted": len(entities),
                "relationships_created": len(relationships),
                "vectors_stored": embeddings_data['vectors_count'],
                "graph_stats": graph_stats
            }

            logger.info(f"Ingestion completed successfully for {file_name}")
            return result

        except Exception as e:
            logger.error(f"Error during ingestion: {e}")
            raise

    async def _extract_entities_and_relationships(
        self,
        parsed_data: Dict[str, Any]
    ) -> tuple[List[Dict], List[Dict]]:
        """
        Extract entities and relationships from parsed text.

        Args:
            parsed_data: Parsed document data

        Returns:
            Tuple of (entities, relationships)
        """
        entities = []
        relationships = []

        try:
            # Simple entity extraction using regex patterns
            # In production, you'd use NER models or LLMs
            text = parsed_data['raw_text']

            # Extract capitalized phrases as potential entities
            entity_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b'
            potential_entities = re.findall(entity_pattern, text)

            # Deduplicate and create entity nodes
            unique_entities = list(set(potential_entities))

            for entity_name in unique_entities[:100]:  # Limit to 100 entities
                entity_id = self._generate_entity_id(entity_name)
                entities.append({
                    'id': entity_id,
                    'name': entity_name,
                    'type': 'NAMED_ENTITY',
                    'description': f'Entity extracted from document',
                    'metadata': {}
                })

            # Extract simple co-occurrence relationships
            # In production, use more sophisticated relationship extraction
            for i in range(len(entities)):
                for j in range(i + 1, min(i + 5, len(entities))):
                    relationships.append({
                        'source_id': entities[i]['id'],
                        'target_id': entities[j]['id'],
                        'type': 'CO_OCCURS',
                        'properties': {'strength': 1.0}
                    })

            logger.info(f"Extracted {len(entities)} entities and {len(relationships)} relationships")

        except Exception as e:
            logger.error(f"Error extracting entities: {e}")

        return entities, relationships

    async def _generate_embeddings(
        self,
        doc_id: str,
        text_nodes: List[Any],
        image_nodes: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate embeddings for text and image descriptions.

        Args:
            doc_id: Document identifier
            text_nodes: List of text nodes
            image_nodes: List of image metadata

        Returns:
            Embeddings data
        """
        vectors = []
        chunks = []

        try:
            # Generate embeddings for text chunks
            for idx, node in enumerate(text_nodes):
                chunk_id = f"{doc_id}_chunk_{idx}"
                text = node.text if hasattr(node, 'text') else str(node)

                # Generate embedding
                embedding = self.embeddings_service.embed_text(text)

                vectors.append({
                    'id': chunk_id,
                    'values': embedding,
                    'metadata': {
                        'doc_id': doc_id,
                        'chunk_index': idx,
                        'text': text[:500],  # Store truncated text
                        'type': 'text',
                        'node_metadata': node.metadata if hasattr(node, 'metadata') else {}
                    }
                })

                chunks.append({
                    'id': chunk_id,
                    'text': text,
                    'index': idx,
                    'metadata': node.metadata if hasattr(node, 'metadata') else {}
                })

            # Generate embeddings for image descriptions
            for idx, image_node in enumerate(image_nodes):
                chunk_id = f"{doc_id}_image_{idx}"
                description = image_node.get('description', '')

                if description:
                    embedding = self.embeddings_service.embed_text(description)

                    vectors.append({
                        'id': chunk_id,
                        'values': embedding,
                        'metadata': {
                            'doc_id': doc_id,
                            'chunk_index': idx,
                            'text': description[:500],
                            'type': 'image',
                            'image_metadata': image_node
                        }
                    })

            logger.info(f"Generated {len(vectors)} embeddings")

        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise

        return {
            'vectors': vectors,
            'chunks': chunks,
            'vectors_count': len(vectors)
        }

    async def _build_knowledge_graph(
        self,
        doc_id: str,
        file_name: str,
        metadata: Dict[str, Any],
        chunks: List[Dict[str, Any]],
        entities: List[Dict[str, Any]],
        relationships: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Build knowledge graph in Neo4j.

        Args:
            doc_id: Document identifier
            file_name: Name of the file
            metadata: Document metadata
            chunks: Text chunks
            entities: Extracted entities
            relationships: Extracted relationships

        Returns:
            Graph statistics
        """
        try:
            # Create document node
            doc_metadata = {
                'file_name': file_name,
                'ingested_at': datetime.now().isoformat(),
                **metadata
            }
            self.graph_store.create_document_node(doc_id, doc_metadata)

            # Create chunk nodes
            chunks_created = self.graph_store.create_chunk_nodes(doc_id, chunks)

            # Create entity nodes
            entities_created = 0
            if entities:
                entities_created = self.graph_store.create_entity_nodes(entities)

            # Create relationships
            relationships_created = 0
            if relationships:
                try:
                    relationships_created = self.graph_store.create_relationships(relationships)
                except Exception as e:
                    logger.warning(f"Some relationships could not be created: {e}")

            # Link chunks to entities (simple matching)
            for chunk in chunks:
                chunk_text = chunk['text'].lower()
                mentioned_entities = [
                    e['id'] for e in entities
                    if e['name'].lower() in chunk_text
                ]
                if mentioned_entities:
                    self.graph_store.link_chunk_to_entities(
                        chunk['id'],
                        mentioned_entities[:10]  # Limit to 10
                    )

            return {
                'document_nodes': 1,
                'chunk_nodes': chunks_created,
                'entity_nodes': entities_created,
                'relationships': relationships_created
            }

        except Exception as e:
            logger.error(f"Error building knowledge graph: {e}")
            raise

    def _generate_doc_id(self, file_url: str) -> str:
        """Generate unique document ID from URL."""
        return hashlib.md5(file_url.encode()).hexdigest()

    def _generate_entity_id(self, entity_name: str) -> str:
        """Generate unique entity ID from name."""
        return hashlib.md5(entity_name.lower().encode()).hexdigest()


# Singleton instance
_ingestion_pipeline: Optional[GraphRAGIngestionPipeline] = None


def get_ingestion_pipeline() -> GraphRAGIngestionPipeline:
    """Get or create ingestion pipeline instance."""
    global _ingestion_pipeline
    if _ingestion_pipeline is None:
        _ingestion_pipeline = GraphRAGIngestionPipeline()
    return _ingestion_pipeline
