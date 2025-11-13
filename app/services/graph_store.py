"""Neo4j graph store service for knowledge graph management."""
import logging
from typing import List, Dict, Any, Optional
from neo4j import GraphDatabase, Driver
from app.config import settings

logger = logging.getLogger(__name__)


class GraphStoreService:
    """Service for managing Neo4j knowledge graph."""

    def __init__(self):
        """Initialize Neo4j graph store."""
        self.driver: Optional[Driver] = None
        self._initialize_neo4j()

    def _initialize_neo4j(self):
        """Initialize Neo4j driver and create constraints."""
        try:
            if not settings.NEO4J_PASSWORD:
                logger.warning("Neo4j password not provided")
                raise ValueError("Neo4j credentials are required")

            self.driver = GraphDatabase.driver(
                settings.NEO4J_URI,
                auth=(settings.NEO4J_USERNAME, settings.NEO4J_PASSWORD)
            )

            # Verify connectivity
            self.driver.verify_connectivity()
            logger.info("Connected to Neo4j successfully")

            # Create indexes and constraints
            self._create_schema()

        except Exception as e:
            logger.error(f"Failed to initialize Neo4j: {e}")
            raise

    def _create_schema(self):
        """Create indexes and constraints for the graph."""
        try:
            with self.driver.session(database=settings.NEO4J_DATABASE) as session:
                # Create constraint for Document nodes
                session.run("""
                    CREATE CONSTRAINT document_id IF NOT EXISTS
                    FOR (d:Document) REQUIRE d.id IS UNIQUE
                """)

                # Create constraint for Entity nodes
                session.run("""
                    CREATE CONSTRAINT entity_id IF NOT EXISTS
                    FOR (e:Entity) REQUIRE e.id IS UNIQUE
                """)

                # Create constraint for Chunk nodes
                session.run("""
                    CREATE CONSTRAINT chunk_id IF NOT EXISTS
                    FOR (c:Chunk) REQUIRE c.id IS UNIQUE
                """)

                # Create index for entity names
                session.run("""
                    CREATE INDEX entity_name IF NOT EXISTS
                    FOR (e:Entity) ON (e.name)
                """)

                logger.info("Graph schema created successfully")

        except Exception as e:
            logger.error(f"Error creating schema: {e}")

    def create_document_node(
        self,
        doc_id: str,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a document node in the graph.

        Args:
            doc_id: Unique document identifier
            metadata: Document metadata

        Returns:
            Created node data
        """
        try:
            with self.driver.session(database=settings.NEO4J_DATABASE) as session:
                result = session.run("""
                    MERGE (d:Document {id: $doc_id})
                    SET d += $metadata
                    SET d.created_at = datetime()
                    RETURN d
                """, doc_id=doc_id, metadata=metadata)

                node = result.single()
                logger.info(f"Created document node: {doc_id}")
                return dict(node['d'])

        except Exception as e:
            logger.error(f"Error creating document node: {e}")
            raise

    def create_chunk_nodes(
        self,
        doc_id: str,
        chunks: List[Dict[str, Any]]
    ) -> int:
        """
        Create chunk nodes and link them to document.

        Args:
            doc_id: Parent document ID
            chunks: List of chunk data

        Returns:
            Number of chunks created
        """
        try:
            with self.driver.session(database=settings.NEO4J_DATABASE) as session:
                result = session.run("""
                    MATCH (d:Document {id: $doc_id})
                    UNWIND $chunks AS chunk
                    CREATE (c:Chunk {
                        id: chunk.id,
                        text: chunk.text,
                        index: chunk.index
                    })
                    SET c += chunk.metadata
                    CREATE (d)-[:HAS_CHUNK]->(c)
                    RETURN count(c) as count
                """, doc_id=doc_id, chunks=chunks)

                count = result.single()['count']
                logger.info(f"Created {count} chunk nodes for document {doc_id}")
                return count

        except Exception as e:
            logger.error(f"Error creating chunk nodes: {e}")
            raise

    def create_entity_nodes(
        self,
        entities: List[Dict[str, Any]]
    ) -> int:
        """
        Create or merge entity nodes.

        Args:
            entities: List of entity data

        Returns:
            Number of entities processed
        """
        try:
            with self.driver.session(database=settings.NEO4J_DATABASE) as session:
                result = session.run("""
                    UNWIND $entities AS entity
                    MERGE (e:Entity {id: entity.id})
                    SET e.name = entity.name,
                        e.type = entity.type,
                        e.description = entity.description
                    SET e += entity.metadata
                    RETURN count(e) as count
                """, entities=entities)

                count = result.single()['count']
                logger.info(f"Processed {count} entity nodes")
                return count

        except Exception as e:
            logger.error(f"Error creating entity nodes: {e}")
            raise

    def create_relationships(
        self,
        relationships: List[Dict[str, Any]]
    ) -> int:
        """
        Create relationships between entities.

        Args:
            relationships: List of relationship data with source, target, and type

        Returns:
            Number of relationships created
        """
        try:
            with self.driver.session(database=settings.NEO4J_DATABASE) as session:
                result = session.run("""
                    UNWIND $relationships AS rel
                    MATCH (source:Entity {id: rel.source_id})
                    MATCH (target:Entity {id: rel.target_id})
                    CALL apoc.create.relationship(
                        source, rel.type, rel.properties, target
                    ) YIELD rel as relationship
                    RETURN count(relationship) as count
                """, relationships=relationships)

                count = result.single()['count']
                logger.info(f"Created {count} relationships")
                return count

        except Exception as e:
            # Fallback without APOC
            logger.warning("APOC not available, using simple relationships")
            return self._create_simple_relationships(relationships)

    def _create_simple_relationships(
        self,
        relationships: List[Dict[str, Any]]
    ) -> int:
        """Create relationships without APOC."""
        try:
            count = 0
            with self.driver.session(database=settings.NEO4J_DATABASE) as session:
                for rel in relationships:
                    session.run("""
                        MATCH (source:Entity {id: $source_id})
                        MATCH (target:Entity {id: $target_id})
                        MERGE (source)-[r:RELATES_TO]->(target)
                        SET r.type = $rel_type
                        SET r += $properties
                    """,
                        source_id=rel['source_id'],
                        target_id=rel['target_id'],
                        rel_type=rel['type'],
                        properties=rel.get('properties', {})
                    )
                    count += 1

            logger.info(f"Created {count} simple relationships")
            return count

        except Exception as e:
            logger.error(f"Error creating simple relationships: {e}")
            raise

    def link_chunk_to_entities(
        self,
        chunk_id: str,
        entity_ids: List[str]
    ):
        """
        Link a chunk to entities it mentions.

        Args:
            chunk_id: Chunk identifier
            entity_ids: List of entity identifiers
        """
        try:
            with self.driver.session(database=settings.NEO4J_DATABASE) as session:
                session.run("""
                    MATCH (c:Chunk {id: $chunk_id})
                    UNWIND $entity_ids AS entity_id
                    MATCH (e:Entity {id: entity_id})
                    MERGE (c)-[:MENTIONS]->(e)
                """, chunk_id=chunk_id, entity_ids=entity_ids)

                logger.debug(f"Linked chunk {chunk_id} to {len(entity_ids)} entities")

        except Exception as e:
            logger.error(f"Error linking chunk to entities: {e}")

    def query_subgraph(
        self,
        entity_ids: List[str],
        max_depth: int = 2
    ) -> Dict[str, Any]:
        """
        Query subgraph around given entities.

        Args:
            entity_ids: List of entity IDs to start from
            max_depth: Maximum depth of relationships to traverse

        Returns:
            Subgraph data with nodes and relationships
        """
        try:
            with self.driver.session(database=settings.NEO4J_DATABASE) as session:
                result = session.run("""
                    MATCH (e:Entity)
                    WHERE e.id IN $entity_ids
                    CALL apoc.path.subgraphAll(e, {
                        maxLevel: $max_depth,
                        relationshipFilter: "RELATES_TO|MENTIONS"
                    })
                    YIELD nodes, relationships
                    RETURN nodes, relationships
                """, entity_ids=entity_ids, max_depth=max_depth)

                record = result.single()
                if record:
                    return {
                        'nodes': [dict(node) for node in record['nodes']],
                        'relationships': [dict(rel) for rel in record['relationships']]
                    }
                return {'nodes': [], 'relationships': []}

        except Exception as e:
            logger.warning(f"APOC subgraph query failed, using simple query: {e}")
            return self._simple_subgraph_query(entity_ids, max_depth)

    def _simple_subgraph_query(
        self,
        entity_ids: List[str],
        max_depth: int
    ) -> Dict[str, Any]:
        """Simple subgraph query without APOC."""
        try:
            with self.driver.session(database=settings.NEO4J_DATABASE) as session:
                result = session.run("""
                    MATCH path = (e:Entity)-[*1..%d]-(related)
                    WHERE e.id IN $entity_ids
                    RETURN nodes(path) as nodes, relationships(path) as rels
                """ % max_depth, entity_ids=entity_ids)

                all_nodes = []
                all_rels = []

                for record in result:
                    all_nodes.extend([dict(node) for node in record['nodes']])
                    all_rels.extend([dict(rel) for rel in record['rels']])

                # Deduplicate
                unique_nodes = {node['id']: node for node in all_nodes if 'id' in node}
                unique_rels = list({str(rel): rel for rel in all_rels}.values())

                return {
                    'nodes': list(unique_nodes.values()),
                    'relationships': unique_rels
                }

        except Exception as e:
            logger.error(f"Error in simple subgraph query: {e}")
            return {'nodes': [], 'relationships': []}

    def get_entity_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Find entity by name.

        Args:
            name: Entity name

        Returns:
            Entity data or None
        """
        try:
            with self.driver.session(database=settings.NEO4J_DATABASE) as session:
                result = session.run("""
                    MATCH (e:Entity)
                    WHERE toLower(e.name) CONTAINS toLower($name)
                    RETURN e
                    LIMIT 1
                """, name=name)

                record = result.single()
                if record:
                    return dict(record['e'])
                return None

        except Exception as e:
            logger.error(f"Error finding entity: {e}")
            return None

    def close(self):
        """Close Neo4j driver connection."""
        if self.driver:
            self.driver.close()
            logger.info("Neo4j connection closed")


# Singleton instance
_graph_store_service: Optional[GraphStoreService] = None


def get_graph_store_service() -> GraphStoreService:
    """Get or create graph store service instance."""
    global _graph_store_service
    if _graph_store_service is None:
        _graph_store_service = GraphStoreService()
    return _graph_store_service
